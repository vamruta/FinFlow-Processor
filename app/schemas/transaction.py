from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    transaction_id: str = Field(
        ..., description="Unique transaction ID (e.g. TXN100234)"
    )
    account_number: str = Field(..., description="Account number")
    amount: float = Field(..., description="Monetary transaction amount")
    currency: str = Field(default="USD", description="Currency code, defaults to USD")
    merchant: str = Field(..., description="Merchant name")
    status: str = Field(
        default="SUCCESS", description="Transaction status: SUCCESS or FAILED"
    )
    timestamp: Optional[datetime] = Field(
        default=None, description="Transaction timestamp"
    )


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class TransactionSummary(BaseModel):
    total_volume: float
    transaction_count: int
    average_amount: float
    by_merchant: Dict[str, float]


class ErrorLogBase(BaseModel):
    raw_payload: str = Field(..., description="Stores the raw bad data line")
    error_message: str = Field(..., description="Why processing failed")
    logged_at: Optional[datetime] = Field(default=None, description="Log timestamp")


class ErrorLogCreate(ErrorLogBase):
    pass


class ErrorLogRead(ErrorLogBase):
    id: int
    logged_at: datetime

    class Config:
        from_attributes = True
