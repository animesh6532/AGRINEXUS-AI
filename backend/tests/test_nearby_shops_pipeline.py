"""
Unit tests for Nearby Fertilizer & Agro-Input Supplier Discovery Pipeline.
Tests OpenStreetMap + Overpass API supplier provider, relevance scoring, address building,
progressive radius expansion, distance calculation, caching, rate limiting, and provider factory.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.osm_supplier_service import (
    OSMSupplierProvider,
    haversine_distance,
    score_osm_element,
    build_osm_address,
    _SUPPLIER_CACHE,
)
from app.services.supplier_provider_factory import SupplierProviderFactory
from app.schemas.fertilizer import SupplierResponse, NearbyShopsResponse


def test_haversine_distance_calculation():
    """Verify Haversine distance formula accuracy."""
    # Distance between Champadali Barasat (22.7321, 88.4996) and Kolkata Airport (22.6547, 88.4467) ~ 10.3 km
    dist = haversine_distance(22.7321, 88.4996, 22.6547, 88.4467)
    assert 9.0 <= dist <= 12.0


def test_score_osm_element_relevance_scoring():
    """Verify OSM element relevance scoring logic."""
    # Agrarian shop -> high score
    el1 = {"type": "node", "id": 1, "tags": {"shop": "agrarian", "name": "Barasat Krishi Kendra"}}
    assert score_osm_element(el1) >= 20

    # Fertilizer store with name match -> high score
    el2 = {"type": "node", "id": 2, "tags": {"shop": "store", "name": "Bengal Agro Inputs & Fertilizers"}}
    assert score_osm_element(el2) >= 10

    # Unrelated clothing store -> score 0 (rejected)
    el3 = {"type": "node", "id": 3, "tags": {"shop": "clothes", "name": "Style Fashion Garments"}}
    assert score_osm_element(el3) == 0


def test_build_osm_address_formats_tags_correctly():
    """Verify address construction from OSM addr:* tags."""
    tags = {
        "addr:housenumber": "42",
        "addr:street": "Station Road",
        "addr:suburb": "Champadali",
        "addr:city": "Barasat",
        "addr:postcode": "700124"
    }
    address = build_osm_address(tags)
    assert "42, Station Road, Champadali, Barasat, 700124" in address


@patch("requests.post")
def test_osm_supplier_provider_success(mock_post):
    """Verify OSMSupplierProvider fetches elements, normalizes them, and calculates distances."""
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "elements": [
            {
                "type": "node",
                "id": 101,
                "lat": 22.7350,
                "lon": 88.5020,
                "tags": {
                    "name": "Barasat Krishi Bipani",
                    "shop": "agrarian",
                    "addr:street": "Jessore Road",
                    "addr:city": "Barasat",
                    "phone": "+91 33 2552 1111",
                    "opening_hours": "09:00-20:00"
                }
            },
            {
                "type": "way",
                "id": 202,
                "center": {"lat": 22.7400, "lon": 88.5100},
                "tags": {
                    "name": "Kisan Agro Supplies",
                    "shop": "farm",
                    "addr:street": "Station Road"
                }
            }
        ]
    }
    mock_post.return_value = mock_res

    # Clear cache before test
    _SUPPLIER_CACHE.clear()

    res = OSMSupplierProvider.find_suppliers(
        latitude=22.7321,
        longitude=88.4996,
        radius_km=5.0
    )

    assert res["success"] is True
    assert res["provider"] == "osm"
    assert res["count"] == 2
    assert len(res["suppliers"]) == 2
    assert len(res["shops"]) == 2

    # Check canonical supplier structure
    s0 = res["suppliers"][0]
    assert s0["name"] == "Barasat Krishi Bipani"
    assert s0["provider"] == "osm"
    assert s0["osm_type"] == "node"
    assert s0["osm_id"] == "101"
    assert s0["rating"] is None  # OSM does not have ratings
    assert s0["review_count"] is None
    assert s0["distance_km"] > 0
    assert "https://www.openstreetmap.org/node/101" in s0["osm_uri"]

    # Verify Pydantic schema compliance
    validated = SupplierResponse(**res)
    assert validated.count == 2
    assert validated.location.latitude == 22.7321


@patch("requests.post")
def test_osm_supplier_provider_rate_limited_429(mock_post):
    """Verify HTTP 429 rate limit produces controlled provider_limited response without crashing."""
    mock_res = MagicMock()
    mock_res.status_code = 429
    mock_post.return_value = mock_res

    _SUPPLIER_CACHE.clear()

    res = OSMSupplierProvider.find_suppliers(
        latitude=22.7321,
        longitude=88.4996,
        radius_km=5.0
    )

    assert res["status"] in ["provider_limited", "error", "empty"]
    assert res["count"] == 0
    assert "rate-limited" in (res["error_diagnostic"] or "").lower() or "unavailable" in (res["error_diagnostic"] or "").lower()


def test_supplier_provider_factory_selects_provider():
    """Verify SupplierProviderFactory switches based on settings.SUPPLIER_PROVIDER."""
    with patch("app.services.supplier_provider_factory.settings") as mock_settings:
        mock_settings.SUPPLIER_PROVIDER = "osm"
        provider_cls = SupplierProviderFactory.get_provider()
        assert provider_cls == OSMSupplierProvider

        mock_settings.SUPPLIER_PROVIDER = "google"
        provider_cls2 = SupplierProviderFactory.get_provider()
        assert provider_cls2.__name__ == "GooglePlacesSupplierProvider"
