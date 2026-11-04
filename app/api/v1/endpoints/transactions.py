from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import (
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
        .filter(Transaction.reference_id == payload.reference_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction with reference {payload.reference_id} already exists.",
        )

    transaction = Transaction(**payload.model_dump())
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
            "category": t.category,
            "currency": t.currency,
            "status": t.status,
        }
        for t in transactions
    ]
    return FinancialProcessorService.calculate_summary(records)
