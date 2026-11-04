from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    reference_id: str = Field(..., description="Unique transaction reference ID")
    account_id: str = Field(..., description="Account identifier")
    amount: float = Field(..., description="Monetary amount of transaction")
    currency: str = Field(default="USD", max_length=3, description="ISO currency code")
    category: str = Field(..., description="Category (e.g. transfer, deposit, expense)")
    status: str = Field(default="PENDING", description="Transaction status")


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionSummary(BaseModel):
    total_volume: float
    transaction_count: int
    average_amount: float
    by_category: Dict[str, float]
