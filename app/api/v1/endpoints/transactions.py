from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models import ErrorLog, Transaction
from app.schemas.transaction import (
    ErrorLogCreate,
    ErrorLogRead,
    TransactionCreate,
    TransactionRead,
    TransactionSummary,
)
from app.services.processor import FinancialProcessorService

router = APIRouter()


@router.post(
    "/transactions",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Transactions"],
)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
):
    """Record a new financial transaction."""
    existing = (
        db.query(Transaction)
        .filter(Transaction.transaction_id == payload.transaction_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction with ID {payload.transaction_id} already exists.",
        )

    data = payload.model_dump(exclude_unset=True)
    transaction = Transaction(**data)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get(
    "/transactions",
    response_model=List[TransactionRead],
    tags=["Transactions"],
)
def list_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Retrieve financial transactions with pagination."""
    return db.query(Transaction).offset(skip).limit(limit).all()


@router.get(
    "/transactions/summary",
    response_model=TransactionSummary,
    tags=["Transactions"],
)
def get_transactions_summary(
    db: Session = Depends(get_db),
):
    """Calculate aggregated transaction metrics using pandas."""
    transactions = db.query(Transaction).all()
    records = [
        {
            "amount": t.amount,
            "merchant": t.merchant,
            "currency": t.currency,
            "status": t.status,
        }
        for t in transactions
    ]
    return FinancialProcessorService.calculate_summary(records)


@router.post(
    "/errors",
    response_model=ErrorLogRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Error Logs"],
)
def log_error(
    payload: ErrorLogCreate,
    db: Session = Depends(get_db),
):
    """Record an invalid payload and processing error message."""
    data = payload.model_dump(exclude_unset=True)
    error_entry = ErrorLog(**data)
    db.add(error_entry)
    db.commit()
    db.refresh(error_entry)
    return error_entry


@router.get(
    "/errors",
    response_model=List[ErrorLogRead],
    tags=["Error Logs"],
)
def list_errors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Retrieve logged errors with pagination."""
    return db.query(ErrorLog).offset(skip).limit(limit).all()
