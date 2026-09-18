"""
Market data service for fetching and managing agricultural market data.
Handles API requests to government data sources and data storage.
"""

import asyncio
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple

from dateutil.parser import parse

from ..core.config import settings
from ..core.logging import logger
from ..database import connection, repository


class MarketAPIClient:
    """
    Client for fetching agricultural market data from government APIs.
    Currently implements data.gov.in API for AGMARKNET data.
    """

    def __init__(self):
        self.base_url = settings.DATA_GOV_IN_BASE_URL
        self.api_key = settings.DATA_GOV_API_KEY
        self.timeout = 30.0
        self.max_retries = 3

        # Resource ID for AGMARKNET daily price data
        # This is the resource ID we discovered earlier:
        # "9ef84268-d588-465a-a308-a864a43d0070"
        self.resource_id = "9ef84268-d588-465a-a308-a864a43d0070"

        if not self.api_key:
            logger.warning(
                "DATA_GOV_API_KEY not set. API requests will fail or use demo data."
            )

    async def fetch_latest_market_data(
        self,
        commodity: Optional[str] = None,
        state: Optional[str] = None,
        market: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetch latest market data from data.gov.in API.

        Uses Python urllib because httpx times out on the
        data.gov.in API in the current Windows environment.

        Args:
            commodity: Filter by commodity name (optional)
            state: Filter by state name (optional)
            market: Filter by market name (optional)
            limit: Maximum number of records to fetch

        Returns:
            List of dictionaries containing market data records
        """
        if not self.api_key:
            logger.error("API key not configured")
            return []

        # Build query parameters
        params = {
            "api-key": self.api_key,
            "format": "json",
            "limit": limit,
            "filters[state]": state if state else "",
            "filters[market]": market if market else "",
            "filters[commodity]": commodity if commodity else "",
            "offset": 0
        }

        # Remove empty filters
        params = {k: v for k, v in params.items() if v != ""}

        url = f"{self.base_url}/resource/{self.resource_id}"
        query_string = urllib.parse.urlencode(params)
        request_url = f"{url}?{query_string}"

        for attempt in range(self.max_retries):
            try:
                def make_request():
                    request = urllib.request.Request(
                        request_url,
                        headers={
                            "User-Agent": "AgriNexus-AI/1.0",
                            "Accept": "application/json",
                        },
                        method="GET",
                    )

                    with urllib.request.urlopen(
                        request,
                        timeout=self.timeout
                    ) as response:
                        return response.read().decode("utf-8")

                # Run blocking urllib request without blocking
                # the FastAPI/async event loop.
                response_text = await asyncio.to_thread(make_request)

                data = json.loads(response_text)

                if data.get("status") == "ok":
                    records = data.get("records", [])

                    logger.info(
                        f"Fetched {len(records)} market records from API"
                    )

                    return self._transform_api_records(records)

                else:
                    logger.error(
                        f"API returned error status: {data.get('status')}"
                    )
                    return []

            except urllib.error.HTTPError as e:
                logger.error(
                    f"HTTP error fetching market data: {e.code}"
                )

                if e.code == 401:
                    logger.error("Invalid API key")
                    return []

                if e.code == 429:
                    logger.warning("Rate limit exceeded")

                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue

                return []

            except urllib.error.URLError as e:
                logger.warning(
                    f"API connection error "
                    f"(attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt == self.max_retries - 1:
                    logger.error("Max retries exceeded for API request")
                    return []

                await asyncio.sleep(2 ** attempt)

            except TimeoutError:
                logger.warning(
                    f"API request timeout "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

                if attempt == self.max_retries - 1:
                    logger.error("Max retries exceeded for API request")
                    return []

                await asyncio.sleep(2 ** attempt)

            except json.JSONDecodeError as e:
                logger.error(
                    f"Invalid JSON response from API: {e}"
                )
                return []

            except Exception as e:
                logger.error(
                    f"Unexpected error fetching market data: {e}"
                )

                if attempt == self.max_retries - 1:
                    return []

                await asyncio.sleep(2 ** attempt)

        return []

    def _transform_api_records(
        self,
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform API records to internal format.

        Args:
            records: Raw records from API

        Returns:
            List of transformed records
        """
        transformed = []

        for record in records:
            try:
                # Parse the arrival_date (format: DD/MM/YYYY)
                observation_date = None
                if "arrival_date" in record and record["arrival_date"]:
                    try:
                        # Handle DD/MM/YYYY format
                        day, month, year = record["arrival_date"].split("/")
                        observation_date = datetime(
                            int(year), int(month), int(day)
                        ).date()
                    except ValueError:
                        # Try alternative parsing
                        observation_date = parse(record["arrival_date"]).date()

                transformed_record = {
                    "state": record.get("state", "").strip(),
                    "district": record.get("district", "").strip(),
                    "market": record.get("market", "").strip(),
                    "commodity": record.get("commodity", "").strip(),
                    "variety": record.get("variety", "").strip() if record.get("variety") else None,
                    "grade": record.get("grade", "").strip() if record.get("grade") else None,
                    "observation_date": observation_date,
                    "min_price": float(record.get("min_price", 0)) if record.get("min_price") else 0.0,
                    "max_price": float(record.get("max_price", 0)) if record.get("max_price") else 0.0,
                    "modal_price": float(record.get("modal_price", 0)) if record.get("modal_price") else 0.0,
                    "source": "data.gov.in"
                }

                # Only add records with valid data
                if (
                    transformed_record["observation_date"] and
                    transformed_record["state"] and
                    transformed_record["commodity"] and
                    transformed_record["district"] and
                    transformed_record["market"] and
                    transformed_record["modal_price"] > 0
                ):
                    transformed.append(transformed_record)

            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid record due to parsing error: {e}")
                continue

        return transformed


class MarketService:
    """
    Service for managing market data operations.
    Coordinates between API client, database repository, and business logic.
    """

    def __init__(self, db: connection.Session):
        self.db = db
        self.api_client = MarketAPIClient()
        self.observation_repo = repository.MarketObservationRepository(db)
        self.forecast_repo = repository.ForecastResultRepository(db)

    async def fetch_and_store_latest_data(
        self,
        commodity: Optional[str] = None,
        state: Optional[str] = None,
        market: Optional[str] = None,
        limit: int = 1000
    ) -> int:
        """
        Fetch latest market data from API and store in database.
        Handles deduplication automatically.

        Args:
            commodity: Filter by commodity name (optional)
            state: Filter by state name (optional)
            market: Filter by market name (optional)
            limit: Maximum number of records to fetch

        Returns:
            Number of new/updated records stored
        """
        logger.info(
            f"Fetching market data for commodity={commodity}, "
            f"state={state}, market={market}, limit={limit}"
        )

        # Fetch data from API
        records = await self.api_client.fetch_latest_market_data(
            commodity=commodity,
            state=state,
            market=market,
            limit=limit
        )

        if not records:
            logger.warning("No market data fetched from API")
            return 0

        # Store each record in database
        stored_count = 0
        for record in records:
            try:
                observation = self.observation_repo.create_observation(record)
                if observation:
                    stored_count += 1
            except Exception as e:
                logger.error(f"Error storing market observation: {e}")
                continue

        logger.info(
            f"Stored {stored_count} market observations "
            f"(out of {len(records)} fetched)"
        )
        return stored_count

    def get_latest_price(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None
    ) -> Optional[dict]:
        """
        Get the latest price observation for a commodity.

        Args:
            commodity: Commodity name
            state: State name (optional)
            district: District name (optional)
            market: Market name (optional)

        Returns:
            Dictionary with latest price data or None
        """
        observation = self.observation_repo.get_latest_observation(
            commodity=commodity,
            state=state,
            district=district,
            market=market
        )

        return observation.to_dict() if observation else None

    def get_historical_prices(
        self,
        commodity: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[dict]:
        """
        Get historical price observations for a commodity.

        Args:
            commodity: Commodity name
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            state: State name (optional)
            district: District name (optional)
            market: Market name (optional)
            limit: Maximum number of records to return

        Returns:
            List of dictionaries containing price observations
        """
        observations = self.observation_repo.get_observations_for_commodity(
            commodity=commodity,
            start_date=start_date,
            end_date=end_date,
            state=state,
            district=district,
            market=market,
            limit=limit
        )

        return [obs.to_dict() for obs in observations]

    def get_available_date_range(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None
    ) -> Tuple[Optional[date], Optional[date]]:
        """
        Get the date range of available observations for a commodity.

        Args:
            commodity: Commodity name
            state: State name (optional)
            district: District name (optional)
            market: Market name (optional)

        Returns:
            Tuple of (min_date, max_date) or (None, None) if no data
        """
        return self.observation_repo.get_date_range_for_commodity(
            commodity=commodity,
            state=state,
            district=district,
            market=market
        )