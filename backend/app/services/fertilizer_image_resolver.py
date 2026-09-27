"""
Fertilizer Image Resolver Service (Pexels Provider Only).

Resolves representative agricultural imagery for fertilizer formulation recommendations
using Pexels API with strict attribution, caching, and candidate scoring.
"""

import time
import requests
from typing import Dict, Any, List, Optional
from ..core.config import settings
from ..core.logging import logger

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


def generate_fertilizer_queries(fertilizer_name: str) -> List[str]:
    """Generate specific, non-generic search queries for a fertilizer formulation."""
    if not fertilizer_name:
        return ["fertilizer granules"]

    name = fertilizer_name.strip()
    name_lower = name.lower()

    if name_lower == "urea":
        return ["urea fertilizer", "urea fertilizer bag", "urea fertilizer granules"]
    elif name_lower in ("dap", "18:46:00 npk", "18:46:0"):
        return ["DAP fertilizer", "diammonium phosphate fertilizer", "DAP fertilizer bag"]
    elif name_lower in ("mop", "white potash"):
        return ["potash fertilizer", "muriate of potash fertilizer", "potash granules"]
    elif name_lower == "ssp":
        return ["single superphosphate fertilizer", "phosphate fertilizer bag", "SSP fertilizer"]
    elif "npk" in name_lower or any(char.isdigit() for char in name):
        clean_npk = name.replace(":", "-")
        return [f"{clean_npk} NPK fertilizer", f"{clean_npk} fertilizer", "NPK fertilizer bag", "NPK fertilizer granules"]
    else:
        return [f"{name} fertilizer", f"{name} agricultural fertilizer", "fertilizer bag granules"]


def score_pexels_candidate(photo: Dict[str, Any], fertilizer_name: str) -> int:
    """Score a Pexels photo candidate based on fertilizer relevance signals."""
    score = 50
    alt_text = (photo.get("alt") or "").lower()
    url_str = (photo.get("url") or "").lower()
    combined_text = f"{alt_text} {url_str}"

    name_clean = fertilizer_name.lower().replace(":", "-").strip()
    name_parts = [p for p in name_clean.split() if len(p) >= 2]

    # Positive signals
    positives = ["fertilizer", "fertilizers", "granules", "pellets", "bag", "sack", "plant food", "plant nutrition", "agriculture", "soil nutrient"]
    for pos in positives:
        if pos in combined_text:
            score += 12

    for part in name_parts:
        if part in combined_text:
            score += 20

    # Negative signals
    negatives = ["pesticide", "insecticide", "herbicide", "fungicide", "tractor", "combine harvester", "diseased leaf", "plant disease"]
    for neg in negatives:
        if neg in combined_text:
            score -= 25

    # Resolution and orientation
    w = photo.get("width") or 0
    h = photo.get("height") or 0
    if w >= getattr(settings, "IMAGE_MIN_WIDTH", 640) and h >= getattr(settings, "IMAGE_MIN_HEIGHT", 360):
        score += 10
    if w >= h:
        score += 5

    return max(0, min(100, score))


class FertilizerImageResolver:
    """
    Pexels-only image resolver for fertilizer recommendations.
    Provides cache-first resolution with fallback handling.
    """

    _cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _normalize_cache_key(cls, fertilizer_name: str) -> str:
        """Normalize query to canonical cache key (e.g., 'fertilizer_image:urea')."""
        clean = fertilizer_name.strip().lower().replace(":", "-").replace(" ", "_")
        return f"fertilizer_image:{clean}"

    @classmethod
    def resolve_fertilizer_image(cls, fertilizer_name: str) -> Dict[str, Any]:
        """
        Resolve a representative Pexels image for a fertilizer prediction.
        Cache-first lookup with TTL expiration.
        """
        if not fertilizer_name or not fertilizer_name.strip():
            return cls._empty_fallback("Product image unavailable")

        cache_key = cls._normalize_cache_key(fertilizer_name)
        now = time.time()
        ttl = getattr(settings, "IMAGE_CACHE_TTL", 86400)

        # Cache hit check
        if cache_key in cls._cache:
            entry = cls._cache[cache_key]
            if now - entry.get("_timestamp", 0) < ttl:
                return entry["result"]

        # If search is disabled or PEXELS_API_KEY missing
        api_key = getattr(settings, "PEXELS_API_KEY", None) or ""
        search_enabled = getattr(settings, "IMAGE_SEARCH_ENABLED", True)

        if not search_enabled or not api_key or api_key.strip() in ("", "your_pexels_api_key_here"):
            fallback = cls._empty_fallback("Pexels provider unconfigured")
            cls._cache[cache_key] = {"result": fallback, "_timestamp": now}
            return fallback

        # Search Pexels API
        try:
            result = cls._fetch_pexels_image(fertilizer_name, api_key.strip())
            cls._cache[cache_key] = {"result": result, "_timestamp": now}
            return result
        except Exception as e:
            logger.warning(f"Pexels image search error for '{fertilizer_name}': {e}")
            fallback = cls._empty_fallback(f"Pexels search error: {str(e)}")
            cls._cache[cache_key] = {"result": fallback, "_timestamp": now}
            return fallback

    @classmethod
    def _fetch_pexels_image(cls, fertilizer_name: str, api_key: str) -> Dict[str, Any]:
        """Fetch candidates from Pexels API using Authorization: <API_KEY> header."""
        queries = generate_fertilizer_queries(fertilizer_name)
        candidates: List[Dict[str, Any]] = []

        headers = {"Authorization": api_key}
        timeout = getattr(settings, "IMAGE_REQUEST_TIMEOUT", 8.0)
        max_cand = getattr(settings, "IMAGE_MAX_CANDIDATES", 10)
        min_score = getattr(settings, "IMAGE_MIN_RELEVANCE_SCORE", 60)

        for query in queries:
            try:
                params = {
                    "query": query,
                    "per_page": min(max_cand, 15),
                    "orientation": "landscape"
                }
                res = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=timeout)
                if res.status_code == 200:
                    data = res.json()
                    photos = data.get("photos", [])
                    for photo in photos:
                        match_score = score_pexels_candidate(photo, fertilizer_name)
                        if match_score >= min_score:
                            src = photo.get("src", {})
                            img_url = src.get("large2x") or src.get("large") or src.get("medium")
                            photographer = photo.get("photographer", "Pexels Contributor")
                            photographer_url = photo.get("photographer_url") or "https://www.pexels.com"
                            src_url = photo.get("url") or "https://www.pexels.com"

                            candidates.append({
                                "image_url": img_url,
                                "source": "pexels",
                                "source_url": src_url,
                                "photographer": photographer,
                                "photographer_url": photographer_url,
                                "image_type": "representative",
                                "verified_product": False,
                                "match_score": match_score
                            })

                    if candidates:
                        # Pick highest scoring candidate
                        candidates.sort(key=lambda x: x["match_score"], reverse=True)
                        return candidates[0]
            except Exception as query_err:
                logger.warning(f"Pexels query '{query}' failed: {query_err}")
                continue

        return cls._empty_fallback("No relevant Pexels fertilizer image found")

    @classmethod
    def _empty_fallback(cls, reason: str = "Fertilizer image unavailable") -> Dict[str, Any]:
        """Return standardized empty fallback schema per Phase 16."""
        return {
            "image_url": None,
            "source": None,
            "source_url": None,
            "photographer": None,
            "photographer_url": None,
            "image_type": None,
            "verified_product": False,
            "match_score": 0
        }
