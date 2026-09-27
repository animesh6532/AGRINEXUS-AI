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
from .market_commodity_canonicalizer import (
    canonicalize_commodity,
    get_supported_commodities_catalogue,
)


class MarketAPIClient:
    """
    Client for fetching agricultural market data from government APIs.
    Currently implements data.gov.in API for AGMARKNET data.
    """

    def __init__(self):
        self.base_url = (settings.DATA_GOV_IN_BASE_URL or "https://api.data.gov.in").rstrip("/")
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
        limit: int = 1000,
        max_pages: int = 10,
        page_size: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch market data, paging ``offset`` until ``limit`` reached.

        Uses Python urllib because httpx times out on the
        data.gov.in API in the current Windows environment.

        Args:
            commodity: Filter by commodity name (optional)
            state: Filter by state name (optional)
            market: Filter by market name (optional)
            limit: Maximum total records (paged via offset)
            max_pages: safety cap on API pages fetched
            page_size: records per request (default min(limit, 500))

        Returns:
            List of dictionaries containing market data records
        """
        if not self.api_key:
            logger.error("API key not configured")
            return []

        eff_page = page_size or min(limit, 500)
        eff_page = max(1, min(eff_page, 1000))
        all_raw: List[Dict[str, Any]] = []
        total_available: Optional[int] = None
        offset = 0
        for page in range(max_pages):
            if len(all_raw) >= limit:
                break
            cur_size = min(eff_page, limit - len(all_raw))
            params = {
                "api-key": self.api_key,
                "format": "json",
                "limit": cur_size,
                "offset": offset,
                "filters[state]": state if state else "",
                "filters[market]": market if market else "",
                "filters[commodity]": commodity if commodity else "",
            }
            params = {k: v for k, v in params.items() if v != ""}
            url = f"{self.base_url}/resource/{self.resource_id}"
            request_url = f"{url}?{urllib.parse.urlencode(params)}"
            page_records: Optional[List[Dict[str, Any]]] = None
            for attempt in range(self.max_retries):
                try:
                    def make_request(url=request_url):
                        request = urllib.request.Request(
                            url,
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
                    response_text = await asyncio.to_thread(make_request)
                    data = json.loads(response_text)
                    if data.get("status") != "ok":
                        logger.error(
                            f"API error status: {data.get('message', '?')}"
                        )
                        break
                    if total_available is None and data.get("total") is not None:
                        try:
                            total_available = int(data["total"])
                            logger.info(
                                f"data.gov.in total={total_available} "
                                f"state={state} commodity={commodity}"
                            )
                        except (TypeError, ValueError):
                            pass
                    page_records = data.get("records", [])
                    break
                except urllib.error.HTTPError as e:
                    logger.error(f"HTTP {e.code} page={page + 1} off={offset}")
                    if 400 <= e.code < 500:
                        return self._transform_api_records(all_raw)
                    if attempt == self.max_retries - 1:
                        logger.error("Max retries reached")
                except urllib.error.URLError as e:
                    logger.warning(f"URL err page={page + 1}: {e}")
                    if attempt == self.max_retries - 1:
                        logger.error("Max retries reached")
                except (json.JSONDecodeError, TimeoutError, OSError) as e:
                    logger.warning(f"Fetch err page={page + 1}: {e}")
                    if attempt == self.max_retries - 1:
                        logger.error("Max retries reached")
                except Exception as e:
                    logger.error(f"Unexpected fetch error: {e}")
                    break
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            if not page_records:
                if page == 0 and not all_raw:
                    logger.warning(
                        f"No records page 1; state={state} commodity={commodity}"
                    )
                break
            all_raw.extend(page_records)
            logger.info(f"Page {page + 1}: +{len(page_records)} tot={len(all_raw)}")
            if len(page_records) < cur_size:
                break
            offset += len(page_records)
            if total_available is not None and offset >= total_available:
                break
        return self._transform_api_records(all_raw[:limit])

    @staticmethod
    def _get_field(record: Dict[str, Any], *names: str) -> Any:
        """First matching field value, case-insensitive (state/State ...)."""
        lowered = {str(k).lower(): v for k, v in record.items()}
        for name in names:
            if name.lower() in lowered:
                return lowered[name.lower()]
        return None

    def _parse_date(self, value: Any):
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        try:
            return parse(text).date()
        except (ValueError, TypeError, OverflowError):
            return None

    def _num(self, value: Any) -> float:
        try:
            if value is None or str(value).strip() == "":
                return 0.0
            return float(str(value).replace(",", "").strip())
        except (ValueError, TypeError, AttributeError):
            return 0.0

    def _str(self, value: Any) -> str:
        return str(value).strip() if value is not None else ""

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
                state = self._str(self._get_field(record, "state", "State"))
                district = self._str(
                    self._get_field(record, "district", "District")
                )
                market = self._str(self._get_field(record, "market", "Market"))
                commodity_raw = self._str(
                    self._get_field(record, "commodity", "Commodity")
                )
                commodity = canonicalize_commodity(commodity_raw)
                variety_raw = self._get_field(record, "variety", "Variety")
                grade_raw = self._get_field(record, "grade", "Grade")

                arrival_raw = self._get_field(
                    record,
                    "arrival_date",
                    "Arrival_Date",
                    "arrival_date_1",
                )
                observation_date = self._parse_date(arrival_raw)

                transformed_record = {
                    "state": state,
                    "district": district,
                    "market": market,
                    "commodity": commodity,
                    "variety": self._str(variety_raw) or None,
                    "grade": self._str(grade_raw) or None,
                    "observation_date": observation_date,
                    "min_price": self._num(
                        self._get_field(record, "min_price", "Min_Price")
                    ),
                    "max_price": self._num(
                        self._get_field(record, "max_price", "Max_Price")
                    ),
                    "modal_price": self._num(
                        self._get_field(record, "modal_price", "Modal_Price")
                    ),
                    "source": "data.gov.in",
                }

                # Only add records with valid data
                if (
                    transformed_record["observation_date"]
                    and transformed_record["state"]
                    and transformed_record["commodity"]
                    and transformed_record["district"]
                    and transformed_record["market"]
                    and transformed_record["modal_price"] > 0
                ):
                    transformed.append(transformed_record)

            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(
                    f"Skipping invalid record due to parsing error: {e}"
                )
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
        limit: int = 1000,
        max_pages: int = 20,
        page_size: Optional[int] = None
    ) -> int:
        """
        Fetch latest market data from API and store in database.
        Handles deduplication automatically.

        Args:
            commodity: Filter by commodity name (optional)
            state: Filter by state name (optional)
            market: Filter by market name (optional)
            limit: Maximum number of records to fetch (total, paged)
            max_pages: Maximum API pages to walk with ``offset``
            page_size: Records requested per API page

        Returns:
            Number of new/updated records stored
        """
        logger.info(
            f"Fetching market data for commodity={commodity}, "
            f"state={state}, market={market}, limit={limit}, "
            f"max_pages={max_pages}, page_size={page_size}"
        )

        # Fetch data from API
        records = await self.api_client.fetch_latest_market_data(
            commodity=commodity,
            state=state,
            market=market,
            limit=limit,
            max_pages=max_pages,
            page_size=page_size
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
        canonical_commodity = canonicalize_commodity(commodity)
        observation = self.observation_repo.get_latest_observation(
            commodity=canonical_commodity,
            state=state,
            district=district,
            market=market
        )

        return observation.to_dict() if observation else None

    def get_latest_market_data(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None
    ) -> Optional[dict]:
        """Alias for get_latest_price for service compatibility."""
        return self.get_latest_price(commodity=commodity, state=state, district=district, market=market)

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
        canonical_commodity = canonicalize_commodity(commodity)
        observations = self.observation_repo.get_observations_for_commodity(
            commodity=canonical_commodity,
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
        canonical_commodity = canonicalize_commodity(commodity)
        return self.observation_repo.get_date_range_for_commodity(
            commodity=canonical_commodity,
            state=state,
            district=district,
            market=market
        )

    def get_commodity_catalogue(
        self,
        state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get supported commodity catalogue indicating availability in the selected state.

        Args:
            state: State filter (optional)

        Returns:
            List of commodity catalogue items
        """
        return get_supported_commodities_catalogue(self.db, state=state)
