from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

try:
    from app.core.database import Base, SessionLocal
except (ImportError, ModuleNotFoundError):
    Base = declarative_base()
    SessionLocal = None


class Transaction(Base):
    """SQLAlchemy model representing a financial transaction."""
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    account_number = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    merchant = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'SUCCESS' or 'FAILED'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, **kwargs):
        kwargs.setdefault("currency", "USD")
        kwargs.setdefault("timestamp", datetime.utcnow())
        super().__init__(**kwargs)

    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, transaction_id='{self.transaction_id}', "
            f"account_number='{self.account_number}', amount={self.amount}, "
            f"currency='{self.currency}', merchant='{self.merchant}', "
            f"status='{self.status}', timestamp={self.timestamp})>"
        )


class ErrorLog(Base):
    """SQLAlchemy model representing logged processing failures and invalid payloads."""
    __tablename__ = "error_logs"
    id = Column(Integer, primary_key=True, index=True)
    raw_payload = Column(Text, nullable=False)
    error_message = Column(String, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, **kwargs):
        kwargs.setdefault("logged_at", datetime.utcnow())
        super().__init__(**kwargs)

    def __repr__(self):
        return (
            f"<ErrorLog(id={self.id}, error_message='{self.error_message}', "
            f"logged_at={self.logged_at})>"
        )


# --- Execution logic to test database integration ---
if __name__ == "__main__":
    print("Testing database write using models...")
    db = SessionLocal()
    try:
        tx = Transaction(
            transaction_id="TXN-TEST-123",
            account_number="ACC-999",
            amount=500.00,
            currency="USD",
            merchant="Script Test Vendor",
            status="SUCCESS"
        )
        db.add(tx)
        db.commit()
        print(f"Success! Inserted transaction with ID: {tx.id}")
    except Exception as e:
        db.rollback()
        print(f"Error during test: {e}")
    finally:
        db.close()