# FinFlow Processor

A modern, high-performance financial transaction processing service built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

---

## 📁 Directory Structure

```text
finflow-processor/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py           # API v1 route aggregator
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py       # Health check & database probe
│   │           └── transactions.py # Transaction CRUD & analytics
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Application settings & environment loader
│   │   └── database.py             # SQLAlchemy engine & session management
│   ├── models/
│   │   ├── __init__.py
│   │   └── transaction.py          # SQLAlchemy ORM models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── health.py               # Pydantic schemas for health checks
│   │   └── transaction.py          # Pydantic schemas for transactions
│   └── services/
│       ├── __init__.py
│       └── processor.py            # Analytics and calculation engine using pandas
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures and in-memory test database
│   └── test_main.py                # Test cases for endpoints and services
├── .env.example                    # Environment variable template with DATABASE_URL
├── .gitignore                      # Git ignore rules
├── Dockerfile                      # Application container definition
├── docker-compose.yml              # Multi-container orchestration (FastAPI + PostgreSQL)
├── requirements.txt                # Python project dependencies
└── README.md                       # Project documentation
```

---

## 📦 Requirements

The project uses the following dependencies specified in `requirements.txt`:

- **fastapi**: High-performance web framework for APIs.
- **uvicorn**: ASGI server for running FastAPI.
- **sqlalchemy**: Database toolkit and Object-Relational Mapper (ORM).
- **psycopg2-binary**: PostgreSQL database adapter for Python.
- **pydantic**: Data validation and parsing using Python type hints.
- **pandas**: Financial data transformation and aggregation library.
- **pytest**: Automated testing framework.
- **requests**: HTTP client library (useful for integration testing and external calls).

---

## ⚙️ Environment Configuration

Copy `.env.example` to create your local `.env` configuration:

```bash
cp .env.example .env
```

### PostgreSQL Connection String (`DATABASE_URL`)

The `.env.example` file contains the placeholder variable for PostgreSQL:

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/finflow_db
```

When running locally outside Docker, update the host to `localhost`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/finflow_db
```

---

## 🐳 Running with Docker Compose

To build and spin up both the PostgreSQL database and the FastAPI application container in one command:

```bash
docker compose up --build
```

The services will be available at:
- **FastAPI API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **PostgreSQL Database**: `localhost:5432`

To shut down the containers and volumes:

```bash
docker compose down -v
```

---

## 💻 Running Locally

### 1. Create and Activate a Virtual Environment

```bash
# macOS/Linux
python -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Application

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 Running Tests

Execute the automated test suite with pytest:

```bash
pytest
```
