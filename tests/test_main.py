from datetime import datetime
from models import ErrorLog, Transaction


def test_models_direct_instantiation(db_session):
    """Test direct SQLAlchemy ORM instantiation and persistence for Transaction and ErrorLog."""
    # Test Transaction model
    tx = Transaction(
        transaction_id="TXN100234",
        account_number="ACC-987654",
        amount=150.75,
        currency="USD",
        merchant="Target",
        status="SUCCESS",
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)

    assert tx.id is not None
    assert tx.transaction_id == "TXN100234"
    assert tx.account_number == "ACC-987654"
    assert tx.amount == 150.75
    assert tx.currency == "USD"
    assert tx.merchant == "Target"
    assert tx.status == "SUCCESS"
    assert isinstance(tx.timestamp, datetime)
    assert "TXN100234" in repr(tx)

    # Test ErrorLog model
    err = ErrorLog(
        raw_payload="INVALID,DATA,,LINE",
        error_message="Invalid transaction format or missing account number",
    )
    db_session.add(err)
    db_session.commit()
    db_session.refresh(err)

    assert err.id is not None
    assert err.raw_payload == "INVALID,DATA,,LINE"
    assert err.error_message == "Invalid transaction format or missing account number"
    assert isinstance(err.logged_at, datetime)
    assert "Invalid transaction format" in repr(err)


def test_root_endpoint(client):
    """Test root endpoint returns service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "finflow-processor"
    assert data["status"] == "online"


def test_health_endpoint(client):
    """Test health check endpoint reports status and database connectivity."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_create_and_read_transaction(client):
    """Test transaction creation and retrieval flow."""
    payload = {
        "transaction_id": "TXN100234",
        "account_number": "ACC-554433",
        "amount": 250.50,
        "currency": "USD",
        "merchant": "Amazon",
        "status": "SUCCESS",
    }
    create_res = client.post("/api/v1/transactions", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["transaction_id"] == "TXN100234"
    assert created_data["account_number"] == "ACC-554433"
    assert created_data["amount"] == 250.50
    assert created_data["merchant"] == "Amazon"
    assert created_data["status"] == "SUCCESS"

    list_res = client.get("/api/v1/transactions")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["transaction_id"] == "TXN100234"


def test_log_error_endpoint(client):
    """Test logging an error payload and retrieval."""
    error_payload = {
        "raw_payload": "TXN999999,BAD_ACC,-500,UNKNOWN",
        "error_message": "Negative amount not allowed",
    }
    create_err = client.post("/api/v1/errors", json=error_payload)
    assert create_err.status_code == 201
    err_data = create_err.json()
    assert err_data["raw_payload"] == "TXN999999,BAD_ACC,-500,UNKNOWN"
    assert err_data["error_message"] == "Negative amount not allowed"

    errors_list = client.get("/api/v1/errors")
    assert errors_list.status_code == 200
    assert len(errors_list.json()) == 1


def test_transactions_summary_calculation(client):
    """Test pandas-based calculation endpoint."""
    transactions = [
        {
            "transaction_id": "TXN-20001",
            "account_number": "ACC-01",
            "amount": 100.0,
            "currency": "USD",
            "merchant": "Walmart",
            "status": "SUCCESS",
        },
        {
            "transaction_id": "TXN-20002",
            "account_number": "ACC-02",
            "amount": 200.0,
            "currency": "USD",
            "merchant": "Apple",
            "status": "SUCCESS",
        },
    ]
    for tx in transactions:
        client.post("/api/v1/transactions", json=tx)

    summary_res = client.get("/api/v1/transactions/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["transaction_count"] == 2
    assert summary["total_volume"] == 300.0
    assert summary["average_amount"] == 150.0
    assert summary["by_merchant"]["Walmart"] == 100.0
    assert summary["by_merchant"]["Apple"] == 200.0
