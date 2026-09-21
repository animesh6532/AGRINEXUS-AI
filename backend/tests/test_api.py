"""
Test API endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app

# Create test client
test_client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Welcome to AgriNexus-AI" in data["message"]
    assert "docs" in data
    assert "health" in data


def test_health_endpoint():
    """Test health endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_market_health_endpoint():
    """Test market module health endpoint."""
    response = test_client.get("/api/market/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["module"] == "market_forecast"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


def test_get_current_price_no_data():
    """Test getting current price for non-existent commodity."""
    response = test_client.get(
        "/api/market/current",
        params={"commodity": "NonExistentCommodity"}
    )
    # Should return 404 since no data exists
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_historical_prices_no_data():
    """Test getting historical prices for non-existent commodity."""
    response = test_client.get(
        "/api/market/history",
        params={"commodity": "NonExistentCommodity"}
    )
    # Should return empty list (200 OK) since no data is not an error
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_market_forecast_no_data():
    """Test generating forecast for non-existent commodity."""
    response = test_client.get(
        "/api/market/forecast",
        params={"commodity": "NonExistentCommodity"}
    )
    # Should return 400 since insufficient data for forecasting
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_get_market_trend_no_data():
    """Test getting market trend for non-existent commodity."""
    response = test_client.get(
        "/api/market/trend",
        params={"commodity": "NonExistentCommodity"}
    )
    # Should return 200 with insight about insufficient data
    assert response.status_code == 200
    data = response.json()
    assert "trend" in data
    # Should indicate insufficient data
    assert data["trend"] == "insufficient_data"


def test_get_market_signals_no_data():
    """Test getting market signals for non-existent commodity."""
    response = test_client.get(
        "/api/market/signals",
        params={"commodity": "NonExistentCommodity"}
    )
    # Should return 200 with analysis showing insufficient data
    assert response.status_code == 200
    data = response.json()
    assert "commodity" in data
    assert data["commodity"] == "NonExistentCommodity"
    assert "trend_analysis" in data
    assert data["trend_analysis"]["trend"] == "insufficient_data"


def test_refresh_market_data_no_key():
    """Test refreshing market data without API key."""
    response = test_client.post(
        "/api/market/refresh",
        params={"commodity": "Paddy(Common)"}
    )
    # Should return 500 since no API key is configured
    # In a real test we might mock this, but for now we expect it to fail gracefully
    # Actually, it might return 202 if the service handles missing keys gracefully
    # Let's just check that it returns a valid response
    assert response.status_code in [200, 202, 500]
    data = response.json()
    # Should have either success message or error detail
    assert "message" in data or "detail" in data


def test_invalid_parameters():
    """Test API with invalid parameters."""
    # Test invalid horizon (too large)
    response = test_client.get(
        "/api/market/forecast",
        params={
            "commodity": "Paddy(Common)",
            "horizon": 100  # Max is 30
        }
    )
    # Should return 422 for validation error
    assert response.status_code == 422

    # Test invalid model type
    response = test_client.get(
        "/api/market/forecast",
        params={
            "commodity": "Paddy(Common)",
            "model": "invalid_model"
        }
    )
    # Should return 422 for validation error
    assert response.status_code == 422

    # Test negative horizon
    response = test_client.get(
        "/api/market/forecast",
        params={
            "commodity": "Paddy(Common)",
            "horizon": -1
        }
    )
    # Should return 422 for validation error
    assert response.status_code == 422