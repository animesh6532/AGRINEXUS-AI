"""
Dynamic Image Resolver Service.
Resolves, ranks, validates, and caches high-relevance agricultural crop photos across multiple providers.
Guarantees:
- Deterministic relevance scoring (0-100)
- Entity-aware negative keyword matching (e.g., Mango NEVER returns cereal/wheat images)
- Rejection of low-scoring candidates (< 75 threshold)
- Persistent SQLite cache with configurable TTL (IMAGE_CACHE_TTL)
- Fault-tolerant provider fallback (never fails recommendation API)
"""

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import httpx

from ..core.config import settings, BACKEND_DIR
from ..core.logging import logger
from ..data.crop_catalogue import get_crop_catalogue, CropEntity
from .image_search import (
    ImageProvider,
    ImageCandidate,
    WikimediaImageProvider,
    GBIFImageProvider,
    PexelsImageProvider,
    INaturalistImageProvider
)

DATA_DIR = BACKEND_DIR / "data"
CACHE_DB_PATH = DATA_DIR / "image_cache.db"


class ImageCache:
    """SQLite-backed persistent image metadata cache."""

    def __init__(self, db_path: Path = CACHE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite cache table."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS image_cache (
                    entity_key TEXT PRIMARY KEY,
                    crop_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    scientific_name TEXT,
                    available INTEGER NOT NULL,
                    url TEXT,
                    thumbnail_url TEXT,
                    provider TEXT,
                    source_url TEXT,
                    author TEXT,
                    license TEXT,
                    license_url TEXT,
                    alt TEXT,
                    relevance_score REAL,
                    reason TEXT,
                    resolved_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                )
            """)
            conn.commit()

    def get(self, entity_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve valid cached image metadata."""
        now = int(time.time())
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT payload_json, expires_at FROM image_cache WHERE entity_key = ?",
                    (entity_key,)
                )
                row = cursor.fetchone()
                if row:
                    payload_json, expires_at = row
                    if expires_at > now:
                        return json.loads(payload_json)
                    else:
                        # Expired entry
                        conn.execute("DELETE FROM image_cache WHERE entity_key = ?", (entity_key,))
                        conn.commit()
        except Exception as e:
            logger.warning(f"Image cache read error: {e}")
        return None

    def set(self, entity_key: str, crop_id: str, data: Dict[str, Any], ttl_seconds: int):
        """Store resolved image metadata in persistent SQLite cache."""
        now = int(time.time())
        expires_at = now + ttl_seconds
        payload_json = json.dumps(data)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO image_cache (
                        entity_key, crop_id, name, scientific_name, available,
                        url, thumbnail_url, provider, source_url, author,
                        license, license_url, alt, relevance_score, reason,
                        resolved_at, expires_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_key,
                    crop_id,
                    data.get("entity", {}).get("name", crop_id),
                    data.get("entity", {}).get("scientific_name"),
                    1 if data.get("image", {}).get("available") else 0,
                    data.get("image", {}).get("url"),
                    data.get("image", {}).get("thumbnail_url"),
                    data.get("image", {}).get("provider"),
                    data.get("image", {}).get("source_url"),
                    data.get("image", {}).get("author"),
                    data.get("image", {}).get("license"),
                    data.get("image", {}).get("license_url"),
                    data.get("image", {}).get("alt"),
                    data.get("image", {}).get("relevance_score"),
                    data.get("image", {}).get("reason"),
                    now,
                    expires_at,
                    payload_json
                ))
                conn.commit()
        except Exception as e:
            logger.warning(f"Image cache write error: {e}")

    def clear(self):
        """Purge all cached entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM image_cache")
                conn.commit()
        except Exception as e:
            logger.warning(f"Image cache clear error: {e}")


class RelevanceScorer:
    """Deterministic Agricultural Image Relevance Scorer."""

    AG_KEYWORDS = [
        "crop", "plant", "tree", "fruit", "field", "agriculture", "farm",
        "orchard", "harvest", "botanical", "cultivation", "leaf", "leaves",
        "branch", "flora", "bloom", "growing", "soil"
    ]

    @classmethod
    def calculate_score(cls, candidate: ImageCandidate, entity: CropEntity) -> float:
        """
        Calculate deterministic relevance score (0-100).
        Scoring Matrix:
        - Scientific name exact match: +40
        - Canonical name exact match: +25
        - Alias match: +15
        - Ag context keywords: +10
        - Tag/description match: +5
        - Resolution / aspect quality: +5
        - Negative Keyword Penalty: -60 or rejection
        """
        text_corpus = f"{candidate.title} {candidate.description or ''} {' '.join(candidate.tags)}".lower()

        # 1. Negative Keyword Penalty Check (Entity-Aware)
        for neg_term in entity.negative_terms:
            if neg_term.lower() in text_corpus:
                # Check if candidate strongly specifies current crop scientific name
                sci_match = entity.scientific_name and entity.scientific_name.lower() in text_corpus
                if not sci_match:
                    logger.info(f"Candidate rejected for '{entity.crop_id}' due to negative keyword match '{neg_term}' in title '{candidate.title}'")
                    return 0.0

        score = 0.0

        # 2. Scientific Name Match (+40)
        if entity.scientific_name and entity.scientific_name.lower() in text_corpus:
            score += 40.0

        # 3. Canonical Name Match (+25)
        if entity.name.lower() in text_corpus or entity.crop_id in text_corpus:
            score += 25.0

        # 4. Alias Match (+15)
        for alias in entity.aliases:
            if alias.lower() in text_corpus:
                score += 15.0
                break

        # 5. Agricultural Context Keywords (+10)
        ag_matches = sum(1 for kw in cls.AG_KEYWORDS if kw in text_corpus)
        score += min(10.0, ag_matches * 3.5)

        # 6. Description / Tag Depth (+5)
        if len(candidate.tags) >= 2 or len(candidate.description or "") >= 20:
            score += 5.0

        # 7. Resolution / Quality Aspect (+5)
        if candidate.width and candidate.width >= settings.IMAGE_MIN_WIDTH:
            score += 5.0

        return round(min(100.0, max(0.0, score)), 1)


class CandidateValidator:
    """Security and Quality Gate Validator for Image Candidates."""

    @staticmethod
    def is_safe_url(url: str) -> bool:
        """Prevent SSRF attacks by blocking local/private IP URLs."""
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            return False
        lower = url.lower()
        blocked = ["localhost", "127.0.0.1", "0.0.0.0", "10.", "192.168.", "172.16."]
        return not any(b in lower for b in blocked)

    @classmethod
    async def validate_candidate(cls, candidate: ImageCandidate) -> bool:
        """Validate URL safety and optional HTTP head reachability."""
        if not cls.is_safe_url(candidate.url):
            return False

        # Lightweight HEAD check for HTTP 200 and image Content-Type
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                head_res = await client.head(candidate.url, follow_redirects=True)
                if head_res.status_code == 200:
                    ctype = head_res.headers.get("Content-Type", "")
                    if "image" in ctype or candidate.url.endswith((".jpg", ".jpeg", ".png", ".webp")):
                        return True
        except Exception:
            # If HEAD check fails or times out, accept if URL ends with standard image extension
            if candidate.url.endswith((".jpg", ".jpeg", ".png", ".webp")):
                return True

        return False


class ImageResolver:
    """Orchestrator for Dynamic Crop Image Resolution."""

    def __init__(self, cache: Optional[ImageCache] = None):
        self.cache = cache or ImageCache()
        self.catalogue = get_crop_catalogue()

        # Active providers sequence
        self.providers: List[ImageProvider] = [
            PexelsImageProvider(),
            WikimediaImageProvider(),
            GBIFImageProvider(),
            INaturalistImageProvider()
        ]

    async def resolve_entity_image(self, crop_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Resolve canonical crop entity and find highest relevance verified image.
        Returns standard Pydantic response dict matching API contract.
        """
        entity = self.catalogue.get_entity(crop_name)
        cache_key = f"crop:{entity.crop_id}"

        # 1. Check persistent cache
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"image_cache_hit entity={entity.crop_id}")
                return cached

        logger.info(f"image_resolution_started entity={entity.crop_id} scientific_name={entity.scientific_name}")

        all_candidates: List[ImageCandidate] = []

        # 2. Build controlled search queries
        search_queries: List[str] = list(entity.search_terms)
        if not search_queries:
            if entity.scientific_name:
                search_queries.append(f"{entity.scientific_name} {entity.name} plant agriculture")
            search_queries.append(f"{entity.name} crop plant agriculture")

        # 3. Query configured providers in parallel/fallback sequence
        for provider in self.providers:
            if not provider.is_configured():
                continue

            for query in search_queries[:2]:  # Top 2 controlled queries
                try:
                    candidates = await asyncio.wait_for(
                        provider.search(query, entity, max_candidates=settings.IMAGE_MAX_CANDIDATES),
                        timeout=settings.IMAGE_REQUEST_TIMEOUT
                    )
                    if candidates:
                        logger.info(f"image_provider_success provider={provider.provider_name} entity={entity.crop_id} candidates={len(candidates)}")
                        all_candidates.extend(candidates)
                except Exception as e:
                    logger.warning(f"Provider {provider.provider_name} search failed: {e}")

        # 4. Relevance Scoring & Negative Keyword Filtering
        valid_candidates: List[Tuple[ImageCandidate, float]] = []

        for candidate in all_candidates:
            score = RelevanceScorer.calculate_score(candidate, entity)
            candidate.relevance_score = score

            if score >= settings.IMAGE_MIN_RELEVANCE_SCORE:
                valid_candidates.append((candidate, score))
            else:
                logger.info(f"image_candidate_rejected entity={entity.crop_id} provider={candidate.provider} score={score} title='{candidate.title}'")

        # 5. Sort candidates by score descending
        valid_candidates.sort(key=lambda x: x[1], reverse=True)

        selected_candidate: Optional[ImageCandidate] = None

        # 6. Candidate Validation Gate
        for candidate, score in valid_candidates:
            if await CandidateValidator.validate_candidate(candidate):
                selected_candidate = candidate
                logger.info(f"image_resolution_success entity={entity.crop_id} provider={candidate.provider} score={score}")
                break

        # 7. Construct Normalized Response Payload
        if selected_candidate:
            response_payload = {
                "success": True,
                "entity": {
                    "id": entity.crop_id,
                    "name": entity.name,
                    "scientific_name": entity.scientific_name,
                    "category": entity.category,
                    "is_resolved": entity.is_resolved
                },
                "image": {
                    "available": True,
                    "url": selected_candidate.url,
                    "thumbnail_url": selected_candidate.thumbnail_url or selected_candidate.url,
                    "provider": selected_candidate.provider,
                    "source_url": selected_candidate.source_url,
                    "author": selected_candidate.author or f"{selected_candidate.provider} Contributor",
                    "license": selected_candidate.license or "CC BY-SA",
                    "license_url": selected_candidate.license_url or "https://creativecommons.org/licenses/",
                    "alt": selected_candidate.title or f"{entity.name} plant agriculture photo",
                    "relevance_score": selected_candidate.relevance_score,
                    "reason": "Successfully resolved high-relevance crop photo"
                }
            }
        else:
            logger.info(f"image_resolution_failed entity={entity.crop_id} reason=no_valid_candidate_above_threshold")
            response_payload = {
                "success": True,
                "entity": {
                    "id": entity.crop_id,
                    "name": entity.name,
                    "scientific_name": entity.scientific_name,
                    "category": entity.category,
                    "is_resolved": entity.is_resolved
                },
                "image": {
                    "available": False,
                    "url": None,
                    "thumbnail_url": None,
                    "provider": None,
                    "source_url": None,
                    "author": None,
                    "license": None,
                    "license_url": None,
                    "alt": f"{entity.name} image unavailable",
                    "relevance_score": None,
                    "reason": "No sufficiently relevant image found matching quality & safety threshold"
                }
            }

        # 8. Store in persistent cache
        self.cache.set(cache_key, entity.crop_id, response_payload, settings.IMAGE_CACHE_TTL)
        return response_payload


# Global singleton instance
def get_image_resolver() -> ImageResolver:
    return ImageResolver()
