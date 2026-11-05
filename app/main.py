from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionRead
from etl_pipeline import run_etl


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist on startup
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        print(f"[Warning] Could not initialize database tables automatically: {exc}")
    yield


app = FastAPI(
    title="FinFlow Processor",
    description="High-performance financial transaction processing engine built with FastAPI and PostgreSQL.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check endpoint",
)
def health():
    """Returns application health status."""
    return {"status": "healthy"}


@app.get(
    "/transactions",
    response_model=List[TransactionRead],
    tags=["Transactions"],
    summary="List paginated transactions with optional filters",
)
def get_transactions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    page: Optional[int] = Query(None, ge=1, description="Page number (1-indexed)"),
    status: Optional[str] = Query(None, description="Filter by status (SUCCESS / FAILED)"),
    merchant: Optional[str] = Query(None, description="Filter by merchant name"),
    db: Session = Depends(get_db),
):
    """Returns a paginated list of processed transactions with optional filtering by status and merchant."""
    if page is not None:
        skip = (page - 1) * limit

    query = db.query(Transaction)

    if status:
        query = query.filter(func.lower(Transaction.status) == status.strip().lower())

    if merchant:
        query = query.filter(func.lower(Transaction.merchant) == merchant.strip().lower())

    return query.order_by(Transaction.id.asc()).offset(skip).limit(limit).all()


@app.post(
    "/transactions/run-etl",
    status_code=status.HTTP_200_OK,
    tags=["ETL"],
    summary="Trigger the ETL pipeline on demand",
)
def trigger_etl():
    """Triggers the etl_pipeline.py ingestion script via an API call."""
    result = run_etl()
    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "ETL pipeline execution failed"),
        )
    return {
        "status": "success",
        "message": "ETL pipeline executed successfully",
        "total_processed": result.get("total_processed", 0),
        "total_successful": result.get("total_successful", 0),
        "total_failed": result.get("total_failed", 0),
    }


# Include modular v1 API router for endpoints such as error logs and transaction summaries
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root():
    """Root endpoint providing service metadata."""
    return {
        "service": settings.APP_NAME,
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }
