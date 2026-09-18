"""
Test market service with mocked API calls.

The MarketAPIClient uses urllib (not httpx) for data.gov.in requests,
so these tests mock urllib.request.urlopen.
"""

import asyncio
import json
import urllib.error
from unittest.mock import MagicMock, patch
from datetime import date
import pytest

from app.services.market_service import MarketService, MarketAPIClient
from app.database import connection, models, repository
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def market_service(db_session):
    """Create a market service instance for testing."""
    return MarketService(db_session)


def test_market_service_initialization(market_service):
    """Test market service initialization."""
    assert market_service.db is not None
    assert market_service.api_client is not None
    assert market_service.observation_repo is not None
    assert market_service.forecast_repo is not None


def test_get_latest_price_no_data(market_service):
    """Test getting latest price when no data exists."""
    result = market_service.get_latest_price("NonExistentCommodity")
    assert result is None


def test_get_historical_prices_no_data(market_service):
    """Test getting historical prices when no data exists."""
    result = market_service.get_historical_prices("NonExistentCommodity")
    assert result == []


def test_get_available_date_range_no_data(market_service):
    """Test getting date range when no data exists."""
    result = market_service.get_available_date_range("NonExistentCommodity")
    assert result == (None, None)


class TestMarketAPIClient:
    """Test the MarketAPIClient class."""

    @pytest.fixture
    def api_client(self):
        """Create an API client for testing."""
        client = MarketAPIClient()
        client.api_key = "test_key"  # Set a test key
        return client

    @patch('urllib.request.urlopen')
    def test_fetch_latest_market_data_success(self, mock_urlopen, api_client):
        """Test successful API data fetch via the urllib client."""
        # Mock response (urlopen is used as a context manager)
        mock_response = MagicMock()
        mock_response.read.return_value.decode.return_value = json.dumps({
            "status": "ok",
            "records": [
                {
                    "state": "Andhra Pradesh",
                    "district": "Prakasam",
                    "market": "Maddipadu APMC",
                    "commodity": "Paddy(Common)",
                    "variety": "B P T",
                    "grade": "FAQ",
                    "arrival_date": "17/09/2026",
                    "min_price": 2800,
                    "max_price": 2800,
                    "modal_price": 2800
                }
            ]
        })
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Call the method
        records = asyncio.run(api_client.fetch_latest_market_data(
            commodity="Paddy(Common)",
            limit=10
        ))

        # Verify
        assert len(records) == 1
        record = records[0]
        assert record["state"] == "Andhra Pradesh"
        assert record["commodity"] == "Paddy(Common)"
        assert record["modal_price"] == 2800.0
        assert record["observation_date"] == date(2026, 9, 17)

    @patch('urllib.request.urlopen')
    def test_fetch_latest_market_data_api_error(self, mock_urlopen, api_client):
        """Test API error handling."""
        # Mock response with error status
        mock_response = MagicMock()
        mock_response.read.return_value.decode.return_value = json.dumps({
            "status": "error",
            "error": "Invalid API key"
        })
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Call the method
        records = asyncio.run(api_client.fetch_latest_market_data(
            commodity="Paddy(Common)",
            limit=10
        ))

        # Verify
        assert len(records) == 0  # Should return empty list on error

    @patch('urllib.request.urlopen')
    def test_fetch_latest_market_data_http_error(self, mock_urlopen, api_client):
        """Test HTTP error handling (e.g. invalid API key)."""
        # Mock HTTP 401 error raised by urllib
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.data.gov.in/resource/test",
            401,
            "Unauthorized",
            None,
            None
        )

        # Call the method
        records = asyncio.run(api_client.fetch_latest_market_data(
            commodity="Paddy(Common)",
            limit=10
        ))

        # Verify
        assert len(records) == 0  # Should return empty list on error

    def test_transform_api_records(self, api_client):
        """Test transformation of API records."""
        raw_records = [
            {
                "state": "Andhra Pradesh",
                "district": "Prakasam",
                "market": "Maddipadu APMC",
                "commodity": "Paddy(Common)",
                "variety": "B P T",
                "grade": "FAQ",
                "arrival_date": "17/09/2026",
                "min_price": 2800,
                "max_price": 2800,
                "modal_price": 2800
            },
            {
                "state": "",  # Invalid record - empty state
                "district": "Prakasam",
                "market": "Maddipadu APMC",
                "commodity": "Paddy(Common)",
                "variety": "B P T",
                "grade": "FAQ",
                "arrival_date": "17/09/2026",
                "min_price": 2800,
                "max_price": 2800,
                "modal_price": 2800
            },
            {
                "state": "Andhra Pradesh",
                "district": "Prakasam",
                "market": "Maddipadu APMC",
                "commodity": "Paddy(Common)",
                "variety": "B P T",
                "grade": "FAQ",
                "arrival_date": "invalid_date",  # Invalid date
                "min_price": 2800,
                "max_price": 2800,
                "modal_price": 2800
            }
        ]

        transformed = api_client._transform_api_records(raw_records)

        # Should only have one valid record
        assert len(transformed) == 1
        record = transformed[0]
        assert record["state"] == "Andhra Pradesh"
        assert record["commodity"] == "Paddy(Common)"
        assert record["modal_price"] == 2800.0
        assert record["observation_date"] == date(2026, 9, 17)