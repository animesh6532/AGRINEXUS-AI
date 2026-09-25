"""
API v1 Router Aggregator.
Combines all domain-specific routers into a unified /api/v1 router.
"""

from fastapi import APIRouter
from .health import router as health_router
from .crop import router as crop_router
from .disease import router as disease_router
from .fertilizer import router as fertilizer_router
from .irrigation import router as irrigation_router
from .pest import router as pest_router
from .soil import router as soil_router
from .yield_api import router as yield_router
from .live import router as live_router
from .images import router as images_router

api_v1_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(crop_router)
api_v1_router.include_router(images_router)
api_v1_router.include_router(disease_router)
api_v1_router.include_router(fertilizer_router)
api_v1_router.include_router(irrigation_router)
api_v1_router.include_router(pest_router)
api_v1_router.include_router(soil_router)
api_v1_router.include_router(yield_router)
api_v1_router.include_router(live_router)

