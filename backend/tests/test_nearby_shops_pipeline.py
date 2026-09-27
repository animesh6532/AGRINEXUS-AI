"""
Unit tests for Nearby Fertilizer & Agro-Input Shops Search Pipeline.
Tests Google Places API (New) integration, progressive radius expansion, text search fallback,
haversine distance calculation, sorting, deduplication, and error diagnostics.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.nearby_shops_service import (
    NearbyShopsService,
    haversine_distance,
    is_relevant_supplier,
)
from app.schemas.fertilizer import NearbyShopsRequest, NearbyShopsResponse


def test_haversine_distance_calculation():
    """Verify Haversine distance formula accuracy."""
    # Distance between Champadali Barasat (22.7321, 88.4996) and Kolkata Airport (22.6547, 88.4467) ~ 10.3 km
    dist = haversine_distance(22.7321, 88.4996, 22.6547, 88.4467)
    assert 9.0 <= dist <= 12.0


def test_is_relevant_supplier_accepts_various_types_and_names():
    """Verify non-restrictive relevance filter accepts legitimate suppliers regardless of primaryType."""
    # Fertilizer shop with primaryType = 'store'
    place1 = {
        "id": "p1",
        "displayName": {"text": "Barasat Krishi Bipani"},
        "primaryType": "store",
        "types": ["store", "point_of_interest"]
    }
    assert is_relevant_supplier(place1) is True

    # Agro input dealer with primaryType = 'wholesaler'
    place2 = {
        "id": "p2",
        "displayName": {"text": "Bengal Agro Inputs & Seeds"},
        "primaryType": "wholesaler",
        "types": ["wholesaler", "establishment"]
    }
    assert is_relevant_supplier(place2) is True

    # Place returned via text search
    place3 = {
        "id": "p3",
        "displayName": {"text": "North 24 Parganas Enterprise"},
        "primaryType": "establishment",
        "types": ["establishment"]
    }
    assert is_relevant_supplier(place3, query_used="fertilizer shop") is True

    # Completely unrelated place (e.g. shoe store) should be rejected
    place4 = {
        "id": "p4",
        "displayName": {"text": "Fancy Footwear"},
        "primaryType": "shoe_store",
        "types": ["shoe_store", "store"]
    }
    assert is_relevant_supplier(place4) is False


def test_unconfigured_api_key_returns_diagnostic():
    """Verify service returns clear diagnostic when API key is missing."""
    with patch("app.services.nearby_shops_service.settings") as mock_settings, \
         patch("os.getenv", return_value=None):
        mock_settings.GOOGLE_MAPS_API_KEY = None
        mock_settings.GOOGLE_PLACES_API_KEY = None

        res = NearbyShopsService.find_nearby_shops(
            latitude=22.7321,
            longitude=88.4996,
            radius_km=25.0
        )

        assert res["count"] == 0
        assert res["error_diagnostic"] == "Google Places API key is unconfigured on backend."


@patch("requests.post")
def test_nearby_search_with_progressive_radius(mock_post):
    """Verify searchNearby fetches places and calculates distance correctly."""
    # Mock Google Places API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "places": [
            {
                "id": "place_barasat_01",
                "displayName": {"text": "Barasat Krishi Rasayan Store"},
                "formattedAddress": "Champadali More, Barasat, West Bengal",
                "location": {"latitude": 22.7350, "longitude": 88.5020},
                "rating": 4.7,
                "userRatingCount": 85,
                "regularOpeningHours": {"openNow": True},
                "nationalPhoneNumber": "+91 33 2552 1234",
                "websiteUri": "https://barasatkrishi.example.com",
                "googleMapsUri": "https://maps.google.com/?cid=123",
                "primaryTypeDisplayName": {"text": "Fertilizer Supplier"},
                "types": ["store", "wholesaler"]
            },
            {
                "id": "place_barasat_02",
                "displayName": {"text": "Maa Tara Agro Input Center"},
                "formattedAddress": "Station Road, Barasat, West Bengal",
                "location": {"latitude": 22.7400, "longitude": 88.5100},
                "rating": 4.5,
                "userRatingCount": 42,
                "regularOpeningHours": {"openNow": False},
                "types": ["establishment"]
            },
            {
                "id": "place_barasat_03",
                "displayName": {"text": "IFFCO Kisan Sewa Kendra Barasat"},
                "formattedAddress": "NH12, Barasat, West Bengal",
                "location": {"latitude": 22.7450, "longitude": 88.5150},
                "rating": 4.8,
                "userRatingCount": 110,
                "types": ["wholesaler"]
            }
        ]
    }
    mock_post.return_value = mock_response

    with patch("os.getenv", return_value="fake_test_google_key"):
        res = NearbyShopsService.find_nearby_shops(
            latitude=22.7321,
            longitude=88.4996,
            radius_km=25.0,
            sort_by="nearest"
        )

        assert res["count"] == 3
        assert len(res["providers"]) == 3
        assert len(res["shops"]) == 3

        # Verify distance_km is calculated and sorted nearest first
        p0 = res["providers"][0]
        assert p0["name"] == "Barasat Krishi Rasayan Store"
        assert p0["distance_km"] > 0
        assert p0["open_now"] is True

        # Verify response model compatibility
        response_model = NearbyShopsResponse(**res)
        assert response_model.count == 3
        assert response_model.location.latitude == 22.7321


@patch("requests.post")
def test_text_search_fallback_when_nearby_search_returns_few_results(mock_post):
    """Verify Text Search fallback is triggered when searchNearby returns fewer than 3 results."""
    # First call (searchNearby) returns 1 place
    nearby_res = MagicMock()
    nearby_res.status_code = 200
    nearby_res.json.return_value = {
        "places": [
            {
                "id": "place_nearby_01",
                "displayName": {"text": "Barasat Fertilizer Depot"},
                "location": {"latitude": 22.7330, "longitude": 88.5000},
                "types": ["store"]
            }
        ]
    }

    # Second call (searchText) returns 2 additional places
    text_res = MagicMock()
    text_res.status_code = 200
    text_res.json.return_value = {
        "places": [
            {
                "id": "place_text_01",
                "displayName": {"text": "Champadali Agro Seeds"},
                "location": {"latitude": 22.7340, "longitude": 88.5010},
                "types": ["store"]
            },
            {
                "id": "place_nearby_01",  # Duplicate ID to test deduplication
                "displayName": {"text": "Barasat Fertilizer Depot"},
                "location": {"latitude": 22.7330, "longitude": 88.5000},
                "types": ["store"]
            },
            {
                "id": "place_text_02",
                "displayName": {"text": "Kisan Bio Fertilizers Store"},
                "location": {"latitude": 22.7360, "longitude": 88.5050},
                "types": ["store"]
            }
        ]
    }

    mock_post.side_effect = [nearby_res, text_res, text_res, text_res, text_res]

    with patch("os.getenv", return_value="fake_test_google_key"):
        res = NearbyShopsService.find_nearby_shops(
            latitude=22.7321,
            longitude=88.4996,
            radius_km=10.0
        )

        # Should deduplicate place_nearby_01 and return 3 total unique places
        assert res["count"] == 3
        place_ids = {p["place_id"] for p in res["providers"]}
        assert place_ids == {"place_nearby_01", "place_text_01", "place_text_02"}


@patch("requests.post")
def test_google_places_api_error_handling(mock_post):
    """Verify backend logs API error diagnostic when Google API returns HTTP 403 or 400."""
    err_res = MagicMock()
    err_res.status_code = 403
    err_res.text = '{"error": {"code": 403, "message": "The provided API key is invalid."}}'
    mock_post.return_value = err_res

    with patch("os.getenv", return_value="invalid_key"):
        res = NearbyShopsService.find_nearby_shops(
            latitude=22.7321,
            longitude=88.4996,
            radius_km=5.0
        )

        assert res["count"] == 0
        assert "Google Places API Nearby HTTP 403" in res["error_diagnostic"]
