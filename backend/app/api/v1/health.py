"""
Health check endpoints for models and overall application readiness.
"""

from fastapi import APIRouter
from ...schemas.health import ModelsHealthResponse
from ...services.model_registry import ModelRegistry

router = APIRouter(tags=["health"])


@router.get(
    "/models/health",
    response_model=ModelsHealthResponse,
    summary="Get ML models loading and health status",
    description="Check the readiness status of all 7 frozen ML model artifacts."
)
async def get_models_health():
    """Retrieve readiness status for all 7 ML model artifacts."""
    registry = ModelRegistry()
    return registry.get_health_status()
