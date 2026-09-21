"""
Database repository for AgriNexus-AI backend.
Handles data access operations for market observations and forecasts.
"""

from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from . import models
from ..core.logging import logger


class MarketObservationRepository:
    """Repository for market observation data operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_observation(self, observation_data: dict) -> models.MarketObservation:
        """
        Create a new market observation record.
        Uses merge-like behavior to avoid duplicates based on unique constraints.

        Args:
            observation_data: Dictionary containing observation data

        Returns:
            MarketObservation: Created or existing observation record
        """
        try:
            # Check if observation already exists
            existing = self.get_observation_by_details(
                state=observation_data["state"],
                district=observation_data["district"],
                market=observation_data["market"],
                commodity=observation_data["commodity"],
                variety=observation_data.get("variety"),
                grade=observation_data.get("grade"),
                observation_date=observation_data["observation_date"]
            )

            if existing:
                # Update existing record with new data
                for key, value in observation_data.items():
                    if hasattr(existing, key) and key != "id":
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                self.db.commit()
                self.db.refresh(existing)
                logger.debug(f"Updated existing observation: {existing}")
                return existing
            else:
                # Create new observation
                observation = models.MarketObservation(**observation_data)
                self.db.add(observation)
                self.db.commit()
                self.db.refresh(observation)
                logger.debug(f"Created new observation: {observation}")
                return observation

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating/updating market observation: {e}")
            raise

    def get_observation_by_details(
        self,
        state: str,
        district: str,
        market: str,
        commodity: str,
        variety: Optional[str] = None,
        grade: Optional[str] = None,
        observation_date: Optional[date] = None
    ) -> Optional[models.MarketObservation]:
        """
        Get a market observation by its unique details.

        Args:
            state: State name
            district: District name
            market: Market name
            commodity: Commodity name
            variety: Variety name (optional)
            grade: Grade (optional)
            observation_date: Date of observation (optional)

        Returns:
            MarketObservation if found, None otherwise
        """
        query = self.db.query(models.MarketObservation).filter(
            and_(
                models.MarketObservation.state == state,
                models.MarketObservation.district == district,
                models.MarketObservation.market == market,
                models.MarketObservation.commodity == commodity,
                models.MarketObservation.observation_date == observation_date
            )
        )

        # Add optional filters
        if variety is not None:
            query = query.filter(models.MarketObservation.variety == variety)
        else:
            query = query.filter(models.MarketObservation.variety == None)

        if grade is not None:
            query = query.filter(models.MarketObservation.grade == grade)
        else:
            query = query.filter(models.MarketObservation.grade == None)

        return query.first()

    def get_latest_observation(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None
    ) -> Optional[models.MarketObservation]:
        """
        Get the most recent observation for a commodity (and optionally location).

        Args:
            commodity: Commodity name
            state: State name (optional)
            district: District name (optional)
            market: Market name (optional)

        Returns:
            Most recent MarketObservation or None
        """
        query = self.db.query(models.MarketObservation).filter(
            models.MarketObservation.commodity == commodity
        )

        if state:
            query = query.filter(models.MarketObservation.state == state)
        if district:
            query = query.filter(models.MarketObservation.district == district)
        if market:
            query = query.filter(models.MarketObservation.market == market)

        return query.order_by(desc(models.MarketObservation.observation_date)).first()

    def get_observations_for_commodity(
        self,
        commodity: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[models.MarketObservation]:
        """
        Get observations for a specific commodity with optional filtering.

        Args:
            commodity: Commodity name
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            state: State name (optional)
            district: District name (optional)
            market: Market name (optional)
            limit: Maximum number of records to return

        Returns:
            List of MarketObservation objects
        """
        query = self.db.query(models.MarketObservation).filter(
            models.MarketObservation.commodity == commodity
        )

        if start_date:
            query = query.filter(models.MarketObservation.observation_date >= start_date)
        if end_date:
            query = query.filter(models.MarketObservation.observation_date <= end_date)
        if state:
            query = query.filter(models.MarketObservation.state == state)
        if district:
            query = query.filter(models.MarketObservation.district == district)
        if market:
            query = query.filter(models.MarketObservation.market == market)

        query = query.order_by(models.MarketObservation.observation_date)

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_date_range_for_commodity(
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
        query = self.db.query(
            func.min(models.MarketObservation.observation_date),
            func.max(models.MarketObservation.observation_date)
        ).filter(models.MarketObservation.commodity == commodity)

        if state:
            query = query.filter(models.MarketObservation.state == state)
        if district:
            query = query.filter(models.MarketObservation.district == district)
        if market:
            query = query.filter(models.MarketObservation.market == market)

        result = query.first()
        return result if result else (None, None)

    def count_observations(
        self,
        commodity: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        """
        Count observations matching criteria.

        Args:
            commodity: Commodity name (optional)
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)

        Returns:
            Number of matching observations
        """
        query = self.db.query(func.count(models.MarketObservation.id))

        if commodity:
            query = query.filter(models.MarketObservation.commodity == commodity)
        if start_date:
            query = query.filter(models.MarketObservation.observation_date >= start_date)
        if end_date:
            query = query.filter(models.MarketObservation.observation_date <= end_date)

        return query.scalar()


class ForecastResultRepository:
    """Repository for forecast result data operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_forecast(self, forecast_data: dict) -> models.ForecastResult:
        """
        Create a new forecast result record.

        Args:
            forecast_data: Dictionary containing forecast data

        Returns:
            ForecastResult: Created forecast record
        """
        try:
            forecast = models.ForecastResult(**forecast_data)
            self.db.add(forecast)
            self.db.commit()
            self.db.refresh(forecast)
            logger.debug(f"Created forecast result: {forecast}")
            return forecast
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating forecast result: {e}")
            raise

    def get_latest_forecast(
        self,
        commodity: str,
        target_date: date,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Optional[models.ForecastResult]:
        """
        Get the most recent forecast for a commodity and target date.

        Args:
            commodity: Commodity name
            target_date: Date being forecasted
            state: State name (optional)
            district: District name (optional)
            market: Market name (optional)
            model_name: Model name (optional)

        Returns:
            Most recent ForecastResult or None
        """
        query = self.db.query(models.ForecastResult).filter(
            and_(
                models.ForecastResult.commodity == commodity,
                models.ForecastResult.target_date == target_date
            )
        )

        if state:
            query = query.filter(models.ForecastResult.state == state)
        if district:
            query = query.filter(models.ForecastResult.district == district)
        if market:
            query = query.filter(models.ForecastResult.market == market)
        if model_name:
            query = query.filter(models.ForecastResult.model_name == model_name)

        return query.order_by(desc(models.ForecastResult.created_at)).first()

    def get_forecasts_for_commodity(
        self,
        commodity: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[models.ForecastResult]:
        """
        Get forecast results for a commodity.

        Args:
            commodity: Commodity name
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            limit: Maximum number of records to return

        Returns:
            List of ForecastResult objects
        """
        query = self.db.query(models.ForecastResult).filter(
            models.ForecastResult.commodity == commodity
        )

        if start_date:
            query = query.filter(models.ForecastResult.forecast_date >= start_date)
        if end_date:
            query = query.filter(models.ForecastResult.forecast_date <= end_date)

        query = query.order_by(desc(models.ForecastResult.created_at))

        if limit:
            query = query.limit(limit)

        return query.all()