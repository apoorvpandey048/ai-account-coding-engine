"""Main FastAPI application for AI Account Coding Service."""

from fastapi import FastAPI, HTTPException, Depends, Security, status, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional

from ..core.engine import AccountCodingEngine
from ..utils.config import get_settings
from ..utils.logger import setup_logging
from .models import (
    SuggestRequest,
    SuggestResponse,
    BatchSuggestRequest,
    FeedbackRequest,
    FeedbackResponse,
    ErrorResponse,
    HealthResponse
)
from .routes import router
import os

# Azure SDK imports for debug endpoint
try:
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobClient
except Exception:
    DefaultAzureCredential = None
    BlobClient = None

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global engine instance
engine: Optional[AccountCodingEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global engine
    
    # Startup
    logger.info("Starting AI Account Coding Service...")
    settings = get_settings()
    
    try:
        from openai import AzureOpenAI
        
        azure_client = None
        if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY:
            azure_client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            logger.info("Azure OpenAI client initialized")
        else:
            logger.warning("Azure OpenAI not configured - using rule-based classification only")
        
        engine = AccountCodingEngine(azure_openai_client=azure_client)
        logger.info("Account Coding Engine initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize engine: {e}")
        # Continue without Azure OpenAI - will use rule-based only
        engine = AccountCodingEngine()
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Account Coding Service...")


# Create FastAPI app
app = FastAPI(
    title="AI Account Coding Service",
    description="AI-based GL account coding suggestions for invoice line items",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(request: Request, api_key: str = Security(api_key_header)):
    """Verify API key from request header.

    Allow CORS preflight (OPTIONS) requests to pass without an API key so
    the browser can perform the preflight handshake. This avoids the
    common `TypeError: Failed to fetch` client-side error caused when
    the OPTIONS request is rejected by authentication.
    """
    # Allow CORS preflight without API key
    if request.method == "OPTIONS":
        return None

    settings = get_settings()

    if not settings.API_KEY_REQUIRED:
        return None

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required"
        )

    # Check against configured API keys
    if api_key not in settings.VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )

    return api_key


def get_engine() -> AccountCodingEngine:
    """Dependency to get the engine instance."""
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    return engine


# Include routes
app.include_router(router, dependencies=[Depends(verify_api_key)])


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "service": "AI Account Coding Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        azure_openai_available=bool(
            settings.AZURE_OPENAI_ENDPOINT and 
            settings.AZURE_OPENAI_API_KEY
        )
    )


@app.get("/debug/fetch-dataset")
async def debug_fetch_dataset():
    """Debug endpoint: attempt to read DATASET_BLOB_URL using managed identity.

    Returns basic blob metadata if successful, otherwise an error message.
    """
    dataset_url = os.getenv("DATASET_BLOB_URL")
    if not dataset_url:
        return {"ok": False, "error": "DATASET_BLOB_URL not configured"}

    if DefaultAzureCredential is None or BlobClient is None:
        return {"ok": False, "error": "Azure SDK not available in environment"}

    try:
        cred = DefaultAzureCredential()
        blob = BlobClient.from_blob_url(dataset_url, credential=cred)
        props = blob.get_blob_properties()
        return {
            "ok": True,
            "length": props.size,
            "content_type": props.content_settings.content_type,
            "last_modified": props.last_modified.isoformat()
        }
    except Exception as e:
        logger.exception("Failed to fetch dataset blob")
        return {"ok": False, "error": str(e)}


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return ErrorResponse(
        error=exc.__class__.__name__,
        message=exc.detail,
        details={"status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return ErrorResponse(
        error=exc.__class__.__name__,
        message="Internal server error",
        details={"error": str(exc)}
    )
