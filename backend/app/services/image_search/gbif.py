"""
GBIF Image Provider.
Searches Global Biodiversity Information Facility (GBIF) occurrence API for verified botanical species imagery.
"""

from typing import List
import httpx
from .base import ImageProvider, ImageCandidate
from ...data.crop_catalogue import CropEntity
from ...core.config import settings
from ...core.logging import logger

GBIF_OCCURRENCE_URL = "https://api.gbif.org/v1/occurrence/search"


class GBIFImageProvider(ImageProvider):
    """GBIF Species Occurrence Image Provider."""

    def __init__(self):
        super().__init__("GBIF")

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
            "scientificName": entity.scientific_name,
            "mediaType": "StillImage",
            "limit": min(max_candidates, 10)
        }

        headers = {
            "User-Agent": "AgriNexusAI/2.0 (Agricultural Intelligence Support Platform; contact@agrinexus.ai)"
        }

        try:
            async with httpx.AsyncClient(timeout=settings.IMAGE_REQUEST_TIMEOUT) as client:
                res = await client.get(GBIF_OCCURRENCE_URL, params=params, headers=headers)
                if res.status_code != 200:
                    logger.warning(f"GBIF API returned HTTP {res.status_code}")
                    return candidates

                data = res.json()
                results = data.get("results", [])

                for item in results:
                    media_list = item.get("media", [])
                    if not media_list:
                        continue

                    for media in media_list:
                        if media.get("type") != "StillImage":
                            continue

                        img_url = media.get("identifier")
                        if not img_url:
                            continue

                        gbif_key = item.get("key")
                        source_url = f"https://www.gbif.org/occurrence/{gbif_key}" if gbif_key else "https://www.gbif.org"
                        author = media.get("rightsHolder") or item.get("recordedBy") or "GBIF Contributor"
                        license_name = media.get("license") or "CC BY 4.0"
                        title = f"{entity.scientific_name} ({entity.name})"

                        candidates.append(ImageCandidate(
                            url=img_url,
                            thumbnail_url=img_url,
                            title=title,
                            description=f"GBIF Occurrence specimen of {entity.scientific_name}",
                            provider="GBIF",
                            source_url=source_url,
                            author=author,
                            license=license_name,
                            license_url="https://creativecommons.org/licenses/",
                            tags=[entity.crop_id, entity.scientific_name.lower()]
                        ))
                        if len(candidates) >= max_candidates:
                            break

        except Exception as e:
            logger.warning(f"GBIF search failed for entity '{entity.crop_id}': {e}")

        return candidates
