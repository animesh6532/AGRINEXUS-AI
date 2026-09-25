"""
iNaturalist Image Provider.
Searches iNaturalist research-grade observation photos for verified biological species imagery.
"""

from typing import List
import httpx
from .base import ImageProvider, ImageCandidate
from ...data.crop_catalogue import CropEntity
from ...core.config import settings
from ...core.logging import logger

INATURALIST_OBSERVATIONS_URL = "https://api.inaturalist.org/v1/observations"


class INaturalistImageProvider(ImageProvider):
    """iNaturalist Species Observation Photo Provider."""

    def __init__(self):
        super().__init__("iNaturalist")

    def is_configured(self) -> bool:
        return True

    async def search(
        self,
        query: str,
        entity: CropEntity,
        max_candidates: int = 10
    ) -> List[ImageCandidate]:
        candidates: List[ImageCandidate] = []
        if not settings.IMAGE_SEARCH_ENABLED or not entity.scientific_name:
            return candidates

        params = {
            "taxon_name": entity.scientific_name,
            "quality_grade": "research",
            "has[]": "photos",
            "per_page": min(max_candidates, 10),
            "order": "desc",
            "order_by": "votes"
        }

        headers = {
            "User-Agent": "AgriNexusAI/2.0 (Agricultural Intelligence Support Platform; contact@agrinexus.ai)"
        }

        try:
            async with httpx.AsyncClient(timeout=settings.IMAGE_REQUEST_TIMEOUT) as client:
                res = await client.get(INATURALIST_OBSERVATIONS_URL, params=params, headers=headers)
                if res.status_code != 200:
                    logger.warning(f"iNaturalist API returned HTTP {res.status_code}")
                    return candidates

                data = res.json()
                results = data.get("results", [])

                for item in results:
                    photos = item.get("photos", [])
                    if not photos:
                        continue

                    photo = photos[0]
                    img_url = photo.get("url")
                    if not img_url:
                        continue

                    # Replace square thumbnail with medium or original URL
                    img_url = img_url.replace("square.", "medium.").replace("square.jpg", "large.jpg")
                    thumb_url = img_url.replace("medium.", "square.")

                    attribution = photo.get("attribution") or f"Photo by {item.get('user', {}).get('login', 'iNaturalist User')}"
                    license_code = photo.get("license_code") or "cc-by"

                    obs_id = item.get("id")
                    source_url = f"https://www.inaturalist.org/observations/{obs_id}" if obs_id else "https://www.inaturalist.org"

                    candidates.append(ImageCandidate(
                        url=img_url,
                        thumbnail_url=thumb_url,
                        title=f"{entity.scientific_name} observation",
                        description=f"Research-grade iNaturalist observation photo of {entity.name}",
                        provider="iNaturalist",
                        source_url=source_url,
                        author=attribution,
                        license=license_code.upper(),
                        license_url="https://creativecommons.org/licenses/",
                        tags=[entity.crop_id, entity.scientific_name.lower()]
                    ))

        except Exception as e:
            logger.warning(f"iNaturalist search failed for entity '{entity.crop_id}': {e}")

        return candidates
