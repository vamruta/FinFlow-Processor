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
        "reference_id": "TX-10001",
        "account_id": "ACC-9988",
        "amount": 250.50,
        "currency": "USD",
        "category": "transfer",
        "status": "COMPLETED",
    }
    create_res = client.post("/api/v1/transactions", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["reference_id"] == "TX-10001"
    assert created_data["amount"] == 250.50

    list_res = client.get("/api/v1/transactions")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["reference_id"] == "TX-10001"


def test_transactions_summary_calculation(client):
    """Test pandas-based calculation endpoint."""
    transactions = [
        {
            "reference_id": "TX-20001",
            "account_id": "ACC-01",
            "amount": 100.0,
            "currency": "USD",
            "category": "deposit",
            "status": "COMPLETED",
        },
        {
            "reference_id": "TX-20002",
            "account_id": "ACC-02",
            "amount": 200.0,
            "currency": "USD",
            "category": "withdrawal",
            "status": "COMPLETED",
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
    assert summary["by_category"]["deposit"] == 100.0
    assert summary["by_category"]["withdrawal"] == 200.0
