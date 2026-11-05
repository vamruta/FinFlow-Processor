from datetime import datetime
from unittest.mock import patch
import pytest

from app.models.transaction import ErrorLog, Transaction
from etl_pipeline import validate_transaction_row


# ==============================================================================
# 1. Health Endpoint Tests
# ==============================================================================


def test_health_endpoint_returns_200(client):
    """Test that the /health endpoint returns a 200 OK status and expected payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_api_v1_health_endpoint_returns_200(client):
    """Test that the /api/v1/health endpoint also returns a 200 OK status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data


# ==============================================================================
# 2. Direct Validation Logic Tests (Negative amounts, missing IDs, duplicates)
# ==============================================================================


def test_validation_catches_negative_amount():
    """Test validation logic directly to ensure negative amounts are caught as errors."""
    row = {
        "transaction_id": "TXN-VALID-001",
        "account_number": "ACC-123456",
        "amount": -50.25,
        "currency": "USD",
        "merchant": "Amazon",
        "timestamp": "2026-11-05T12:00:00",
    }
    is_valid, error_reason, amount, timestamp = validate_transaction_row(row)
    assert is_valid is False
    assert error_reason is not None
    assert "greater than 0" in error_reason
    assert "-50.25" in error_reason


def test_validation_catches_zero_amount():
    """Test validation logic directly to ensure zero amounts are caught as errors."""
    row = {
        "transaction_id": "TXN-VALID-002",
        "account_number": "ACC-123456",
        "amount": 0.0,
        "currency": "USD",
        "merchant": "Target",
        "timestamp": "2026-11-05T12:00:00",
    }
    is_valid, error_reason, _, _ = validate_transaction_row(row)
    assert is_valid is False
    assert error_reason is not None
    assert "greater than 0" in error_reason


def test_validation_catches_missing_transaction_id():
    """Test validation logic directly to ensure missing or null IDs are caught as errors."""
    # Test empty string
    row_empty = {
        "transaction_id": "",
        "account_number": "ACC-123456",
        "amount": 100.0,
        "currency": "USD",
        "merchant": "Amazon",
        "timestamp": "2026-11-05T12:00:00",
    }
    is_valid, error_reason, _, _ = validate_transaction_row(row_empty)
    assert is_valid is False
    assert "transaction_id" in error_reason

    # Test None
    row_none = {
        "transaction_id": None,
        "account_number": "ACC-123456",
        "amount": 100.0,
        "currency": "USD",
        "merchant": "Amazon",
        "timestamp": "2026-11-05T12:00:00",
    }
    is_valid, error_reason, _, _ = validate_transaction_row(row_none)
    assert is_valid is False
    assert "transaction_id" in error_reason

    # Test "nan"
    row_nan = {
        "transaction_id": "nan",
        "account_number": "ACC-123456",
        "amount": 100.0,
        "currency": "USD",
        "merchant": "Amazon",
        "timestamp": "2026-11-05T12:00:00",
    }
    is_valid, error_reason, _, _ = validate_transaction_row(row_nan)
    assert is_valid is False
    assert "transaction_id" in error_reason


def test_validation_catches_missing_mandatory_fields():
    """Test validation logic directly for other mandatory fields (account_number, timestamp, merchant)."""
    # Missing account_number
    row_missing_acc = {
        "transaction_id": "TXN-VALID-003",
        "account_number": "",
        "amount": 100.0,
        "currency": "USD",
        "merchant": "Amazon",
        "timestamp": "2026-11-05T12:00:00",
    }
    is_valid, error_reason, _, _ = validate_transaction_row(row_missing_acc)
    assert is_valid is False
    assert "account_number" in error_reason

    # Missing timestamp
    row_missing_time = {
        "transaction_id": "TXN-VALID-004",
        "account_number": "ACC-123456",
        "amount": 100.0,
        "currency": "USD",
        "merchant": "Amazon",
        "timestamp": "",
    }
    is_valid, error_reason, _, _ = validate_transaction_row(row_missing_time)
    assert is_valid is False
    assert "timestamp" in error_reason

    # Missing merchant
    row_missing_merchant = {
        "transaction_id": "TXN-VALID-005",
        "account_number": "ACC-123456",
        "amount": 100.0,
        "currency": "USD",
        "merchant": "",
        "timestamp": "2026-11-05T12:00:00",
    }
    is_valid, error_reason, _, _ = validate_transaction_row(row_missing_merchant)
    assert is_valid is False
    assert "merchant" in error_reason


def test_validation_catches_duplicate_transaction_id():
    """Test validation logic catches duplicates within batch and existing DB records."""
    row = {
        "transaction_id": "TXN-DUP-001",
        "account_number": "ACC-123456",
        "amount": 100.0,
        "currency": "USD",
        "merchant": "Amazon",
        "timestamp": "2026-11-05T12:00:00",
    }
    # Duplicate in batch
    is_valid_batch, err_batch, _, _ = validate_transaction_row(
        row, seen_batch_ids={"TXN-DUP-001"}
    )
    assert is_valid_batch is False
    assert "batch" in err_batch

    # Duplicate in database
    is_valid_db, err_db, _, _ = validate_transaction_row(
        row, existing_db_ids={"TXN-DUP-001"}
    )
    assert is_valid_db is False
    assert "already exists in PostgreSQL" in err_db


def test_validation_accepts_clean_row():
    """Test validation logic accepts a valid transaction row."""
    row = {
        "transaction_id": "TXN-CLEAN-999",
        "account_number": "ACC-998877",
        "amount": "250.75",
        "currency": "USD",
        "merchant": "Starbucks",
        "timestamp": "2026-11-05T08:30:00",
    }
    is_valid, error_reason, amount, timestamp = validate_transaction_row(row)
    assert is_valid is True
    assert error_reason is None
    assert amount == 250.75
    assert isinstance(timestamp, datetime)


# ==============================================================================
# 3. Model & Schema Instantiation Tests
# ==============================================================================


def test_models_direct_instantiation(db_session):
    """Test direct SQLAlchemy ORM instantiation and persistence for Transaction and ErrorLog."""
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


# ==============================================================================
# 4. API Endpoint Integration Tests
# ==============================================================================


def test_root_endpoint(client):
    """Test root endpoint returns service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "finflow-processor"
    assert data["status"] == "online"


def test_get_transactions_pagination_and_filters(client):
    """Test GET /transactions with pagination and status/merchant filters."""
    tx_list = [
        {
            "transaction_id": "TXN-PAG-001",
            "account_number": "ACC-01",
            "amount": 100.0,
            "currency": "USD",
            "merchant": "Amazon",
            "status": "SUCCESS",
        },
        {
            "transaction_id": "TXN-PAG-002",
            "account_number": "ACC-02",
            "amount": 200.0,
            "currency": "USD",
            "merchant": "Apple",
            "status": "FAILED",
        },
        {
            "transaction_id": "TXN-PAG-003",
            "account_number": "ACC-03",
            "amount": 300.0,
            "currency": "USD",
            "merchant": "Amazon",
            "status": "SUCCESS",
        },
    ]
    for tx in tx_list:
        client.post("/api/v1/transactions", json=tx)

    # Test pagination: limit = 2
    res_page1 = client.get("/transactions?skip=0&limit=2")
    assert res_page1.status_code == 200
    items_page1 = res_page1.json()
    assert len(items_page1) == 2

    # Test status filter: SUCCESS
    res_success = client.get("/transactions?status=SUCCESS")
    assert res_success.status_code == 200
    items_success = res_success.json()
    assert len(items_success) == 2
    for it in items_success:
        assert it["status"] == "SUCCESS"

    # Test status filter: FAILED
    res_failed = client.get("/transactions?status=FAILED")
    assert res_failed.status_code == 200
    items_failed = res_failed.json()
    assert len(items_failed) == 1
    assert items_failed[0]["merchant"] == "Apple"

    # Test merchant filter: Amazon
    res_amazon = client.get("/transactions?merchant=Amazon")
    assert res_amazon.status_code == 200
    items_amazon = res_amazon.json()
    assert len(items_amazon) == 2
    for it in items_amazon:
        assert it["merchant"] == "Amazon"

    # Test combined filter: status=SUCCESS and merchant=Amazon
    res_comb = client.get("/transactions?status=SUCCESS&merchant=Amazon")
    assert res_comb.status_code == 200
    items_comb = res_comb.json()
    assert len(items_comb) == 2


def test_post_run_etl_endpoint(client):
    """Test POST /transactions/run-etl triggers ETL pipeline and returns statistics."""
    mock_result = {
        "status": "success",
        "total_processed": 500,
        "total_successful": 495,
        "total_failed": 5,
    }
    with patch("main.run_etl", return_value=mock_result), patch(
        "app.main.run_etl", return_value=mock_result
    ):
        response = client.post("/transactions/run-etl")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total_processed"] == 500
        assert data["total_successful"] == 495
        assert data["total_failed"] == 5


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

    list_res = client.get("/transactions")
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
