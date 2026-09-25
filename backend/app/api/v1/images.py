"""
Image Resolution & Verification API Router.
Exposes endpoints for dynamic crop image lookup, cache refresh, and provider health status.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ...core.config import settings
from ...services.image_resolver import get_image_resolver
from ...services.image_search import (
    WikimediaImageProvider,
    GBIFImageProvider,
    PexelsImageProvider,
    INaturalistImageProvider
)

router = APIRouter(prefix="/images", tags=["images"])


class ImageEntitySchema(BaseModel):
    id: str
    name: str
    scientific_name: Optional[str] = None
    category: str = "General"
    is_resolved: bool = True


class ImageDetailSchema(BaseModel):
    available: bool
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    provider: Optional[str] = None
    source_url: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    license_url: Optional[str] = None
    alt: Optional[str] = None
    relevance_score: Optional[float] = None
    reason: Optional[str] = None


class ImageResolutionResponseSchema(BaseModel):
    success: bool = True
    entity: ImageEntitySchema
    image: ImageDetailSchema


@router.get(
    "/crop/{crop_id}",
    response_model=ImageResolutionResponseSchema,
    summary="Resolve dynamic verified image for a canonical crop species",
    description="Resolves, ranks, validates, and returns cached/dynamic crop photo metadata."
)
async def get_crop_image(
    crop_id: str,
    refresh: bool = Query(False, description="Force cache refresh")
):
    """Retrieve verified image metadata for a crop species."""
    resolver = get_image_resolver()
    try:
        res = await resolver.resolve_entity_image(crop_id, force_refresh=refresh)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image resolution error: {str(e)}"
        )


@router.post(
    "/crop/{crop_id}/refresh",
    response_model=ImageResolutionResponseSchema,
    summary="Force refresh cached image metadata for a crop species"
)
async def refresh_crop_image(crop_id: str):
    """Purge cache and re-query providers for a crop image."""
    resolver = get_image_resolver()
    try:
        res = await resolver.resolve_entity_image(crop_id, force_refresh=True)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image refresh error: {str(e)}"
        )


@router.get(
    "/health",
    summary="Get image resolution system and provider health status"
)
async def get_images_health():
    """Return health status of image search providers and configuration."""
    pexels = PexelsImageProvider()
    wikimedia = WikimediaImageProvider()
    gbif = GBIFImageProvider()
    inat = INaturalistImageProvider()

    return {
        "status": "healthy" if settings.IMAGE_SEARCH_ENABLED else "disabled",
        "enabled": settings.IMAGE_SEARCH_ENABLED,
        "cache": "sqlite_active",
        "cache_ttl_seconds": settings.IMAGE_CACHE_TTL,
        "min_relevance_score": settings.IMAGE_MIN_RELEVANCE_SCORE,
        "providers": {
            "pexels": "configured" if pexels.is_configured() else "not_configured",
            "wikimedia": "available" if wikimedia.is_configured() else "disabled",
            "gbif": "available" if gbif.is_configured() else "disabled",
            "inaturalist": "available" if inat.is_configured() else "disabled"
        }
    }
