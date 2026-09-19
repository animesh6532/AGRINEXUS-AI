"""
Main FastAPI application for AgriNexus-AI Master Backend.
Integrates Market Intelligence and Frozen ML Model Services with Live OpenCV Computer Vision.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .core import dependencies, config, logging
from .api import market
from .api.v1.router import api_v1_router
from .services.model_registry import ModelRegistry
from .database import connection


# Initialize logging
logger = logging.setup_logging()

# Create FastAPI application
app = FastAPI(
    title=config.settings.PROJECT_NAME,
    description="AgriNexus-AI Master Backend integrating 7 Frozen ML models, Live OpenCV Computer Vision, and Market Intelligence.",
    version=config.settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(market.router)
app.include_router(api_v1_router)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting AgriNexus-AI Master Backend...")

    # 1. Initialize Database Tables
    try:
        connection.create_tables()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # 2. Load Frozen ML Model Artifacts Once on Startup
    try:
        registry = ModelRegistry()
        registry.load_all_models()
    except Exception as e:
        logger.error(f"Critical error during Model Registry initialization: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down AgriNexus-AI Master Backend")


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to AgriNexus-AI Master Backend",
        "version": config.settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "models_health": "/api/v1/models/health"
    }


# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors cleanly."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Failure",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": str(exc) if config.settings.DEBUG else "An unexpected error occurred during processing."
        }
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Application health check endpoint combining app and ML readiness status."""
    registry = ModelRegistry()
    m_health = registry.get_health_status()

    return {
        "status": m_health["status"],
        "service": "agrinexus-ai-master-backend",
        "version": config.settings.VERSION,
        "models": m_health["models"]
    }