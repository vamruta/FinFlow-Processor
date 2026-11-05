from app.core.database import SessionLocal
from app.models.transaction import ErrorLog, Transaction

if __name__ == "__main__":
    print("Testing database connection and counts...")
    db = SessionLocal()
    try:
        tx_count = db.query(Transaction).count()
        err_count = db.query(ErrorLog).count()
        print(f"Transactions in DB: {tx_count}")
        print(f"Error logs in DB  : {err_count}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
