"""Root models module for backward compatibility and direct imports."""
try:
    from app.models.transaction import Base, ErrorLog, Transaction
except (ImportError, ModuleNotFoundError):
    from datetime import datetime
    from sqlalchemy import Column, DateTime, Float, Integer, String, Text
    from sqlalchemy.orm import declarative_base

    try:
        from app.core.database import Base
    except (ImportError, ModuleNotFoundError):
        Base = declarative_base()

    class Transaction(Base):
        __tablename__ = "transactions"
        id = Column(Integer, primary_key=True, index=True)
        transaction_id = Column(String, unique=True, index=True, nullable=False)
        account_number = Column(String, nullable=False)
        amount = Column(Float, nullable=False)
        currency = Column(String, default="USD", nullable=False)
        merchant = Column(String, nullable=False)
        status = Column(String, nullable=False)
        timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    class ErrorLog(Base):
        __tablename__ = "error_logs"
        id = Column(Integer, primary_key=True, index=True)
        raw_payload = Column(Text, nullable=False)
        error_message = Column(String, nullable=False)
        logged_at = Column(DateTime, default=datetime.utcnow, nullable=False)

__all__ = ["Base", "Transaction", "ErrorLog"]
