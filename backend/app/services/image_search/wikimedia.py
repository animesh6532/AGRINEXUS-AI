"""
Wikimedia Commons Image Provider.
Searches Wikimedia Commons API for open-access biological and agricultural reference photos.
"""

from typing import List, Optional
import httpx
from .base import ImageProvider, ImageCandidate
from ...data.crop_catalogue import CropEntity
from ...core.config import settings
from ...core.logging import logger

WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"


class WikimediaImageProvider(ImageProvider):
    """Wikimedia Commons MediaWiki API provider."""

    def __init__(self):
        super().__init__("Wikimedia Commons")

    def is_configured(self) -> bool:
        return True

    async def search(
        self,
        query: str,
        entity: CropEntity,
        max_candidates: int = 10
    ) -> List[ImageCandidate]:
        candidates: List[ImageCandidate] = []
        if not settings.IMAGE_SEARCH_ENABLED:
            return candidates

        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"file:{query}",
            "gsrnamespace": "6",  # File namespace
            "gsrlimit": min(max_candidates, 15),
            "prop": "imageinfo|info",
            "iiprop": "url|size|extmetadata|user",
            "inprop": "url",
            "format": "json"
        }

        headers = {
            "User-Agent": "AgriNexusAI/2.0 (Agricultural Intelligence Support Platform; contact@agrinexus.ai)"
        }

        try:
            async with httpx.AsyncClient(timeout=settings.IMAGE_REQUEST_TIMEOUT) as client:
                res = await client.get(WIKIMEDIA_API_URL, params=params, headers=headers)
                if res.status_code != 200:
                    logger.warning(f"Wikimedia API returned HTTP {res.status_code}")
                    return candidates

                data = res.json()
                pages = data.get("query", {}).get("pages", {})

                for page_id, page_data in pages.items():
                    image_info_list = page_data.get("imageinfo", [])
                    if not image_info_list:
                        continue

                    info = image_info_list[0]
                    img_url = info.get("url")
                    if not img_url or not (img_url.endswith(".jpg") or img_url.endswith(".jpeg") or img_url.endswith(".png") or img_url.endswith(".webp")):
                        continue

                    thumb_url = info.get("thumburl") or img_url
                    width = info.get("width")
                    height = info.get("height")
                    extmeta = info.get("extmetadata", {})

                    title = page_data.get("title", "").replace("File:", "")
                    source_url = page_data.get("fullurl") or f"https://commons.wikimedia.org/wiki/File:{title}"

                    # Author extraction
                    artist_html = extmeta.get("Artist", {}).get("value", "")
                    author = extmeta.get("Artist", {}).get("value") or info.get("user") or "Wikimedia Commons Contributor"
                    # Clean simple HTML from artist field
                    if "<" in author:
                        import re
                        author = re.sub(r"<[^>]+>", "", author).strip()

                    license_name = extmeta.get("LicenseShortName", {}).get("value") or "CC BY-SA"
                    license_url = extmeta.get("LicenseUrl", {}).get("value") or "https://creativecommons.org/licenses/"

                    description = extmeta.get("ImageDescription", {}).get("value") or title
                    if "<" in str(description):
                        import re
                        description = re.sub(r"<[^>]+>", "", str(description)).strip()

                    candidates.append(ImageCandidate(
                        url=img_url,
                        thumbnail_url=thumb_url,
                        title=title,
                        description=str(description)[:250],
                        provider="Wikimedia Commons",
                        source_url=source_url,
                        author=author,
                        license=license_name,
                        license_url=license_url,
                        width=width,
                        height=height,
                        tags=[entity.name.lower(), entity.crop_id]
                    ))

        except Exception as e:
            logger.warning(f"Wikimedia search failed for query '{query}': {e}")

        return candidates
