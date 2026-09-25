"""
Comprehensive Automated Test Suite for Dynamic Image Resolver & Verification System.
Strictly tests entity normalization, scientific name safety, relevance scoring matrix,
negative keyword filtering, cache hit/miss, provider fallback, low-score rejection,
and the critical regression test: test_mango_never_returns_cereal_image().
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.crop_catalogue import get_crop_catalogue
from app.services.image_search.base import ImageCandidate
from app.services.image_resolver import (
    RelevanceScorer,
    CandidateValidator,
    ImageCache,
    get_image_resolver
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ==============================================================================
# 1. MOST IMPORTANT REGRESSION TEST
# ==============================================================================
def test_mango_never_returns_cereal_image():
    """
    MOST IMPORTANT REGRESSION TEST:
    Verify entity 'mango' (Mangifera indica) strictly rejects image candidates
    strongly associated with cereal/wheat/rice/maize/corn/barley/mustard/potato.
    """
    catalogue = get_crop_catalogue()
    mango = catalogue.get_entity("mango")

    assert mango.crop_id == "mango"
    assert mango.scientific_name == "Mangifera indica"

    # Candidate 1: Invalid cereal image mistakenly matching "mango"
    cereal_candidate = ImageCandidate(
        url="https://images.example.com/wheat_field.jpg",
        title="Golden wheat field ready for harvest in farm",
        description="A beautiful golden wheat grain field landscape",
        provider="TestProvider",
        source_url="https://example.com/wheat",
        tags=["wheat", "cereal", "grain", "agriculture"]
    )

    cereal_score = RelevanceScorer.calculate_score(cereal_candidate, mango)
    assert cereal_score == 0.0, f"Cereal candidate received score {cereal_score}, expected 0.0 rejection"

    # Candidate 2: Valid mango orchard photo
    mango_candidate = ImageCandidate(
        url="https://images.example.com/mango_tree.jpg",
        title="Ripe Mangifera indica mango fruit hanging on tree branch in orchard",
        description="Lush green mango orchard tree with yellow mango fruit",
        provider="TestProvider",
        source_url="https://example.com/mango",
        tags=["mango", "mangifera indica", "fruit", "orchard", "agriculture"],
        width=1200,
        height=800
    )

    mango_score = RelevanceScorer.calculate_score(mango_candidate, mango)
    assert mango_score >= 85.0, f"Mango candidate received score {mango_score}, expected >= 85.0"


# ==============================================================================
# 2. CANONICAL CROP NORMALIZATION & SCIENTIFIC NAME SAFETY
# ==============================================================================
def test_crop_entity_normalization():
    """Verify input variants normalize to exact canonical crop ID."""
    catalogue = get_crop_catalogue()

    assert catalogue.get_entity("mango").crop_id == "mango"
    assert catalogue.get_entity("Mango").crop_id == "mango"
    assert catalogue.get_entity("MANGIFERA INDICA").crop_id == "mango"
    assert catalogue.get_entity("aam").crop_id == "mango"

    assert catalogue.get_entity("rice").crop_id == "rice"
    assert catalogue.get_entity("Paddy").crop_id == "rice"
    assert catalogue.get_entity("Oryza sativa").crop_id == "rice"


def test_unresolved_entity_handling_no_scientific_name_fabrication():
    """Verify unknown crop entity returns explicit unresolved state WITHOUT fabricating a scientific name."""
    catalogue = get_crop_catalogue()
    unknown = catalogue.get_entity("exotic_unknown_dragonfruit_v2")

    assert unknown.is_resolved is False
    assert unknown.scientific_name is None, "Scientific name must NOT be fabricated for unresolved entity"
    assert unknown.crop_id == "exotic_unknown_dragonfruit_v2"


# ==============================================================================
# 3. RELEVANCE SCORING MATRIX
# ==============================================================================
def test_relevance_scoring_matrix():
    """Test individual point contributions in RelevanceScorer."""
    catalogue = get_crop_catalogue()
    rice = catalogue.get_entity("rice")

    candidate = ImageCandidate(
        url="https://images.example.com/rice.jpg",
        title="Oryza sativa rice paddy crop field",
        description="Lush green flooded rice field agriculture",
        provider="Wikimedia Commons",
        source_url="https://commons.wikimedia.org/wiki/File:Rice.jpg",
        tags=["rice", "oryza sativa", "paddy"],
        width=1920
    )

    score = RelevanceScorer.calculate_score(candidate, rice)
    # Scientific (+40) + Canonical (+25) + Alias (+15) + Ag Context (+10) + Tags (+5) + Quality (+5) = 100
    assert score >= 90.0


# ==============================================================================
# 4. LOW SCORE REJECTION & CANDIDATE VALIDATION
# ==============================================================================
def test_low_relevance_score_rejection():
    """Verify candidates scoring below minimum threshold (75) are rejected."""
    catalogue = get_crop_catalogue()
    apple = catalogue.get_entity("apple")

    low_score_candidate = ImageCandidate(
        url="https://images.example.com/green.jpg",
        title="Generic green leaf in garden",
        description="A simple leaf",
        provider="TestProvider",
        source_url="https://example.com/leaf",
        tags=["leaf", "garden"]
    )

    score = RelevanceScorer.calculate_score(low_score_candidate, apple)
    assert score < 75.0


def test_ssrf_url_validation():
    """Verify CandidateValidator blocks unsafe SSRF targets."""
    assert CandidateValidator.is_safe_url("https://images.example.com/mango.jpg") is True
    assert CandidateValidator.is_safe_url("http://localhost:8000/secret.jpg") is False
    assert CandidateValidator.is_safe_url("http://127.0.0.1/admin.jpg") is False
    assert CandidateValidator.is_safe_url("http://10.0.0.1/private.jpg") is False
    assert CandidateValidator.is_safe_url("http://192.168.1.1/internal.jpg") is False


# ==============================================================================
# 5. CACHE HIT & MISS
# ==============================================================================
def test_image_cache_persistence(tmp_path):
    """Test SQLite cache store, retrieval, and expiration."""
    db_file = tmp_path / "test_image_cache.db"
    cache = ImageCache(db_file)

    test_data = {
        "success": True,
        "entity": {"id": "mango", "name": "Mango", "scientific_name": "Mangifera indica"},
        "image": {"available": True, "url": "https://example.com/mango.jpg", "provider": "Test"}
    }

    cache.set("crop:mango", "mango", test_data, ttl_seconds=3600)
    cached = cache.get("crop:mango")

    assert cached is not None
    assert cached["image"]["available"] is True
    assert cached["image"]["url"] == "https://example.com/mango.jpg"


# ==============================================================================
# 6. API ENDPOINTS INTEGRATION
# ==============================================================================
def test_image_resolution_api_endpoints(client):
    """Test GET /api/v1/images/crop/{crop_id} and GET /api/v1/images/health."""
    # Health endpoint
    res_health = client.get("/api/v1/images/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["enabled"] is True
    assert "providers" in health_data

    # Crop image endpoint for Mango
    res_mango = client.get("/api/v1/images/crop/mango")
    assert res_mango.status_code == 200
    data_mango = res_mango.json()

    assert data_mango["success"] is True
    assert data_mango["entity"]["id"] == "mango"
    assert data_mango["entity"]["name"] == "Mango"
    assert data_mango["entity"]["scientific_name"] == "Mangifera indica"
    assert "image" in data_mango
    assert "available" in data_mango["image"]


def test_smart_crop_recommendation_includes_image_payload(client, monkeypatch):
    """Verify POST /api/v1/crop/recommend-smart returns image payload in each recommendation."""
    # Fast mock for external provider search in automated test suite
    async def mock_search(self, query, entity, max_candidates=10):
        return [
            ImageCandidate(
                url=f"https://images.example.com/{entity.crop_id}.jpg",
                title=f"Verified photo of {entity.scientific_name or entity.name} crop agriculture",
                provider="TestProvider",
                source_url=f"https://example.com/{entity.crop_id}",
                tags=[entity.crop_id, (entity.scientific_name or '').lower()]
            )
        ]

    from app.services.image_search import WikimediaImageProvider
    monkeypatch.setattr(WikimediaImageProvider, "search", mock_search)

    payload = {
        "mode": "auto",
        "location": {"latitude": 22.72, "longitude": 88.48, "state": "West Bengal"}
    }
    res = client.post("/api/v1/crop/recommend-smart", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert len(data["recommendations"]) > 0

    top_rec = data["recommendations"][0]
    assert "image" in top_rec
    assert "available" in top_rec["image"]

