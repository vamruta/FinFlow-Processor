from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup if available
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root():
    """Root entry point providing service metadata and documentation links."""
    return {
        "service": settings.APP_NAME,
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }
