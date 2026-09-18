"""
Main FastAPI application for the Market Forecast backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core import dependencies, config, logging
from .api import market
from .database import connection


# Initialize logging
logger = logging.setup_logging()

# Create FastAPI application
app = FastAPI(
    title=config.settings.PROJECT_NAME,
    description="Market Forecast backend for AgriNexus-AI university project",
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


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting AgriNexus-AI Market Forecast Backend")

    # Create database tables
    try:
        connection.create_tables()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Don't fail startup if database initialization fails
        # The application might still work with cached data


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down AgriNexus-AI Market Forecast Backend")


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Welcome to AgriNexus-AI Market Forecast Backend",
        "version": config.settings.VERSION,
        "docs": "/docs",
        "health": "/api/market/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Application health check endpoint."""
    return {
        "status": "healthy",
        "service": "agrinexus-market-forecast",
        "version": config.settings.VERSION,
        "timestamp": config.settings.API_V1_STR
    }