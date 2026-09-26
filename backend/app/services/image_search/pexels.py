"""
Pexels Image Provider.
Searches Pexels REST API for high-resolution agricultural photography when PEXELS_API_KEY is configured.
Strictly preserves Pexels photographer attribution and source URL.
"""

from typing import List
import httpx
from .base import ImageProvider, ImageCandidate
from ...data.crop_catalogue import CropEntity
from ...core.config import settings
from ...core.logging import logger

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


class PexelsImageProvider(ImageProvider):
    """Pexels Agricultural Photography API Provider."""

    def __init__(self):
        super().__init__("Pexels")

    def is_configured(self) -> bool:
        return bool(settings.PEXELS_API_KEY and settings.PEXELS_API_KEY.strip() != "" and settings.PEXELS_API_KEY != "your_pexels_api_key_here")

    async def search(
        self,
        query: str,
        entity: CropEntity,
        max_candidates: int = 10
    ) -> List[ImageCandidate]:
        candidates: List[ImageCandidate] = []
        if not self.is_configured() or not settings.IMAGE_SEARCH_ENABLED:
            return candidates

        headers = {
            "Authorization": settings.PEXELS_API_KEY.strip()
        }
        params = {
            "query": query,
            "per_page": min(max_candidates, 15),
            "orientation": "landscape"
        }

        try:
            async with httpx.AsyncClient(timeout=settings.IMAGE_REQUEST_TIMEOUT) as client:
                res = await client.get(PEXELS_SEARCH_URL, headers=headers, params=params)
                if res.status_code != 200:
                    logger.warning(f"Pexels API returned HTTP {res.status_code}")
                    return candidates

                data = res.json()
                photos = data.get("photos", [])

                for photo in photos:
                    src = photo.get("src", {})
                    img_url = src.get("large2x") or src.get("large") or src.get("original")
                    thumb_url = src.get("medium") or src.get("small") or img_url
                    if not img_url:
                        continue

                    photographer = photo.get("photographer", "Pexels Photographer")
                    source_url = photo.get("url") or "https://www.pexels.com"
                    alt_text = photo.get("alt") or f"{entity.name} plant agriculture"

                    candidates.append(ImageCandidate(
                        url=img_url,
                        thumbnail_url=thumb_url,
                        title=alt_text[:100],
                        description=alt_text,
                        provider="Pexels",
                        source_url=source_url,
                        author=f"Photo by {photographer} on Pexels",
                        license="Pexels License (Free for agricultural use)",
                        license_url="https://www.pexels.com/license/",
                        width=photo.get("width"),
                        height=photo.get("height"),
                        tags=[entity.crop_id, entity.name.lower()]
                    ))

        except Exception as e:
            logger.warning(f"Pexels search failed for query '{query}': {e}")

    async def check_health(self) -> dict:
        """Perform lightweight health and authentication verification check for Pexels API."""
        if not self.is_configured():
            return {
                "configured": False,
                "reachable": False,
                "authenticated": False,
                "last_status": None,
                "message": "PEXELS_API_KEY is missing or unconfigured"
            }

        headers = {"Authorization": settings.PEXELS_API_KEY.strip()}
        params = {"query": "nature", "per_page": 1}

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(PEXELS_SEARCH_URL, headers=headers, params=params)
                status_code = res.status_code
                if status_code == 200:
                    return {
                        "configured": True,
                        "reachable": True,
                        "authenticated": True,
                        "last_status": 200,
                        "message": "Pexels API authenticated and operational"
                    }
                elif status_code == 401:
                    return {
                        "configured": True,
                        "reachable": True,
                        "authenticated": False,
                        "last_status": 401,
                        "message": "Invalid Pexels API Key"
                    }
                elif status_code == 403:
                    return {
                        "configured": True,
                        "reachable": True,
                        "authenticated": False,
                        "last_status": 403,
                        "message": "Pexels API request forbidden"
                    }
                elif status_code == 429:
                    return {
                        "configured": True,
                        "reachable": True,
                        "authenticated": True,
                        "last_status": 429,
                        "message": "Pexels API rate limited"
                    }
                else:
                    return {
                        "configured": True,
                        "reachable": False,
                        "authenticated": False,
                        "last_status": status_code,
                        "message": f"Pexels API returned HTTP {status_code}"
                    }
        except Exception as e:
            return {
                "configured": True,
                "reachable": False,
                "authenticated": False,
                "last_status": None,
                "message": f"Pexels health check failed: {str(e)}"
            }

