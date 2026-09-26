"""
Forecasting service for the AgriNexus-AI backend.
Handles forecasting agricultural market prices using time-series models.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
import logging

import numpy as np
import pandas as pd

from ..core.config import settings
from ..core.logging import logger
from ..database import connection, models, repository
from .model import (
    BaseForecastModel,
    ForecastPoint,
    ForecastResult,
    create_forecast_model,
    NaiveForecastModel,
    MovingAverageForecastModel,
    ExponentialSmoothingForecastModel,
    ARIMAForecastModel
)


class ForecastService:
    """
    Service for generating market price forecasts.
    Coordinates data retrieval, model selection, forecasting, and result storage.
    """

    def __init__(self, db: connection.Session):
        self.db = db
        self.market_repo = repository.MarketObservationRepository(db)
        self.forecast_repo = repository.ForecastResultRepository(db)

        # Available forecasting models
        self.available_models = {
            "naive": NaiveForecastModel,
            "moving_average": lambda: MovingAverageForecastModel(window_size=7),
            "ets": lambda: ExponentialSmoothingForecastModel(trend="add"),
            "arima": lambda: ARIMAForecastModel(order=(1, 1, 1))
        }

    async def generate_forecast(
        self,
        commodity: str,
        horizon_days: int = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        model_type: str = "ets",
        use_cache: bool = True
    ) -> ForecastResult:
        """
        Generate price forecast for a commodity.

        Args:
            commodity: Commodity name to forecast
            horizon_days: Number of days to forecast ahead (default from settings)
            state: State name filter (optional)
            district: District name filter (optional)
            market: Market name filter (optional)
            model_type: Type of forecasting model to use
            use_cache: Whether to use cached forecast if available and recent

        Returns:
            ForecastResult containing the forecast and metadata
        """
        # Set default horizon
        if horizon_days is None:
            horizon_days = settings.DEFAULT_FORECAST_HORIZON_DAYS

        forecast_date = date.today()
        logger.info(
            f"Generating {horizon_days}-day forecast for {commodity} "
            f"using {model_type} model"
        )

        # Check for cached forecast if requested
        if use_cache:
            cached_forecast = self._get_cached_forecast(
                commodity=commodity,
                horizon_days=horizon_days,
                state=state,
                district=district,
                market=market,
                model_type=model_type,
                forecast_date=forecast_date
            )
            if cached_forecast:
                logger.info("Using cached forecast")
                return cached_forecast

        # Get historical data
        historical_data = self._get_historical_data_for_forecasting(
            commodity=commodity,
            state=state,
            district=district,
            market=market
        )

        # If location filters returned insufficient data, try widening to commodity level
        if len(historical_data) < settings.MIN_HISTORICAL_DAYS_REQUIRED:
            historical_data = self._get_historical_data_for_forecasting(
                commodity=commodity,
                state=None,
                district=None,
                market=None
            )

        if len(historical_data) < settings.MIN_HISTORICAL_DAYS_REQUIRED:
            raise ValueError(
                f"Insufficient historical data for forecasting. "
                f"Need at least {settings.MIN_HISTORICAL_DAYS_REQUIRED} days, "
                f"got {len(historical_data)}."
            )

        unique_dates = {
            obs["observation_date"]
            if isinstance(obs["observation_date"], date)
            else date.fromisoformat(obs["observation_date"])
            for obs in historical_data
        } if historical_data else set()

        if len(unique_dates) < settings.MIN_HISTORICAL_DAYS_REQUIRED:
            raise ValueError(
                "Insufficient historical data for forecasting. "
                f"Need at least {settings.MIN_HISTORICAL_DAYS_REQUIRED} unique "
                f"observation dates, got {len(unique_dates)} unique date(s) "
                f"across {len(historical_data)} record(s) for the selected "
                "commodity/location. Collect more daily market data first."
            )

        # Prepare time-series data
        ts_data = self._prepare_time_series_data(historical_data)

        # Select and fit model
        model = self._select_and_fit_model(ts_data, model_type)

        # Generate forecast
        forecast_values, lower_bounds, upper_bounds = model.predict_with_confidence(
            horizon_days
        )

        # Create forecast points
        forecast_points = []
        for i in range(horizon_days):
            forecast_date_point = forecast_date + timedelta(days=i + 1)
            forecast_points.append(ForecastPoint(
                date=forecast_date_point,
                predicted_price=forecast_values[i],
                confidence_lower=lower_bounds[i] if i < len(lower_bounds) else None,
                confidence_upper=upper_bounds[i] if i < len(upper_bounds) else None
            ))

        # Calculate trend
        trend = self._calculate_trend(forecast_values)

        # Calculate metrics using temporal train/test split
        metrics = self._calculate_forecast_metrics(
            ts_data, model_type, horizon_days
        )

        # Create forecast result
        result = ForecastResult(
            commodity=commodity,
            market=market,
            state=state,
            forecast_date=forecast_date,
            horizon_days=horizon_days,
            model_name=model.name,
            forecast=forecast_points,
            metrics=metrics,
            trend=trend
        )

        # Store forecast result in database
        try:
            self._store_forecast_result(result)
            logger.info(
                f"Forecast generated and stored for {commodity} "
                f"(model: {model.name}, trend: {trend})"
            )
        except Exception as e:
            logger.error(f"Error storing forecast result: {e}")
            # Don't fail the forecast generation if storage fails

        return result

    def _get_historical_data_for_forecasting(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical observations for forecasting purposes.

        Args:
            commodity: Commodity name
            state: State name filter (optional)
            district: District name filter (optional)
            market: Market name filter (optional)

        Returns:
            List of observation dictionaries sorted by date
        """
        # Get more data than minimum required to allow for train/test splitting
        limit = max(
            settings.MIN_HISTORICAL_DAYS_REQUIRED * 2,
            100  # Ensure we get reasonable amount of data
        )

        # Get observations as model objects and convert to dictionaries
        observation_models = self.market_repo.get_observations_for_commodity(
            commodity=commodity,
            start_date=None,  # Get all available data
            end_date=None,
            state=state,
            district=district,
            market=market,
            limit=limit
        )
        observations = [obs.to_dict() for obs in observation_models]

        # Sort by date (oldest first)
        observations.sort(
            key=lambda x: x["observation_date"]
            if isinstance(x["observation_date"], date)
            else date.fromisoformat(x["observation_date"])
        )

        return observations

    def _prepare_time_series_data(
        self,
        observations: List[Dict[str, Any]]
    ) -> pd.Series:
        """
        Convert observations to pandas Series for time-series forecasting.

        Args:
            observations: List of observation dictionaries

        Returns:
            pandas Series with dates as index and modal prices as values
        """
        if not observations:
            raise ValueError("No observations provided for time-series preparation")

        # Extract dates and prices
        dates = []
        prices = []

        for obs in observations:
            obs_date = obs["observation_date"]
            if isinstance(obs_date, str):
                obs_date = date.fromisoformat(obs_date)

            dates.append(obs_date)
            prices.append(obs["modal_price"])

        # Create pandas Series
        ts_data = pd.Series(
            data=prices,
            index=pd.to_datetime(dates),
            name="modal_price"
        )

        # Remove duplicates (keep last)
        ts_data = ts_data[~ts_data.index.duplicated(keep='last')]

        # Sort by date
        ts_data = ts_data.sort_index()

        return ts_data

    def _select_and_fit_model(
        self,
        data: pd.Series,
        model_type: str
    ) -> BaseForecastModel:
        """
        Select and fit a forecasting model.

        Args:
            data: Time-series data as pandas Series
            model_type: Type of model to use

        Returns:
            Fitted forecasting model
        """
        # Create model instance
        if model_type in self.available_models:
            model_factory = self.available_models[model_type]
            if callable(model_factory):
                model = model_factory()
            else:
                model = model_factory
        else:
            logger.warning(
                f"Unknown model type '{model_type}'. Defaulting to ETS."
                f" Available models: {list(self.available_models.keys())}"
            )
            model = ExponentialSmoothingForecastModel(trend="add")

        # Fit the model
        try:
            model.fit(data)
            logger.info(f"Fitted {model.name} model")
            return model
        except Exception as e:
            logger.error(f"Error fitting {model_type} model: {e}")
            # Fall back to naive model
            logger.info("Falling back to naive forecast model")
            naive_model = NaiveForecastModel()
            naive_model.fit(data)
            return naive_model

    def _calculate_trend(self, forecast_values: List[float]) -> str:
        """
        Calculate the overall trend from forecast values.

        Args:
            forecast_values: List of forecasted prices

        Returns:
            Trend string: "increasing", "decreasing", or "stable"
        """
        if len(forecast_values) < 2:
            return "stable"

        # Calculate linear regression slope
        x = np.arange(len(forecast_values))
        y = np.array(forecast_values)

        if len(y) < 2:
            return "stable"

        # Simple trend calculation: compare first and last values
        first_val = forecast_values[0]
        last_val = forecast_values[-1]
        change_pct = ((last_val - first_val) / first_val) * 100 if first_val != 0 else 0

        # Define thresholds for trend classification
        if change_pct > 2.0:  # More than 2% increase
            return "increasing"
        elif change_pct < -2.0:  # More than 2% decrease
            return "decreasing"
        else:
            return "stable"

    def _calculate_forecast_metrics(
        self,
        data: pd.Series,
        model_type: str,
        horizon_days: int
    ) -> Dict[str, float]:
        """
        Calculate forecast accuracy metrics using temporal train/test split.

        Args:
            data: Time-series data
            model_type: Type of model used
            horizon_days: Forecast horizon used

        Returns:
            Dictionary of metric values
        """
        if len(data) < horizon_days + 10:  # Need enough data for meaningful split
            logger.warning(
                f"Not enough data ({len(data)} points) for reliable metrics calculation. "
                f"Returning zero metrics."
            )
            return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

        # Use temporal split: train on earlier data, test on recent data
        # We'll simulate forecasting the last horizon_days points
        test_size = min(horizon_days, len(data) // 4)  # Use up to 25% of data for testing
        test_size = max(test_size, 5)  # At least 5 points for testing

        if len(data) <= test_size:
            logger.warning("Not enough data for train/test split")
            return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

        train_data = data.iloc[:-test_size]
        test_data = data.iloc[-test_size:]

        try:
            # Create and fit model on training data
            model = self._select_and_fit_model(train_data, model_type)

            # Generate forecasts for test period
            predictions = model.predict(len(test_data))
            actual_values = test_data.tolist()

            # Calculate metrics
            metrics = model.calculate_metrics(actual_values, predictions)
            logger.debug(
                f"Forecast metrics for {model.name}: "
                f"MAE={metrics['mae']:.2f}, RMSE={metrics['rmse']:.2f}, MAPE={metrics['mape']:.2f}"
            )
            return metrics

        except Exception as e:
            logger.error(f"Error calculating forecast metrics: {e}")
            return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

    def _get_cached_forecast(
        self,
        commodity: str,
        horizon_days: int,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        model_type: str = "ets",
        forecast_date: Optional[date] = None
    ) -> Optional[ForecastResult]:
        """
        Check for a recent cached forecast.

        Args:
            commodity: Commodity name
            horizon_days: Forecast horizon
            state: State filter (optional)
            district: District filter (optional)
            market: Market filter (optional)
            model_type: Model type
            forecast_date: Date forecast was generated (defaults to today)

        Returns:
            Cached ForecastResult if found and recent, None otherwise
        """
        if forecast_date is None:
            forecast_date = date.today()

        # Only use cache if forecast is from today (or very recent)
        # In a production system, you might want a longer cache TTL
        cutoff_date = forecast_date  # Only today's forecasts

        # Get recent forecasts
        recent_forecasts = self.forecast_repo.get_forecasts_for_commodity(
            commodity=commodity,
            start_date=cutoff_date,
            end_date=forecast_date,
            limit=10
        )

        # Look for matching forecast
        for forecast in recent_forecasts:
            if (
                forecast.commodity == commodity and
                forecast.state == state and
                forecast.district == district and
                forecast.market == market and
                forecast.horizon_days == horizon_days and
                forecast.model_name == self._get_model_name(model_type) and
                forecast.forecast_date == forecast_date
            ):
                # Convert database model to ForecastResult
                return self._db_forecast_to_result(forecast)

        return None

    def _get_model_name(self, model_type: str) -> str:
        """Get the display name for a model type."""
        model_names = {
            "naive": "Naive",
            "moving_average": "MovingAverage_7",
            "ets": "ETS_add_none_no",
            "arima": "ARIMA_111_none"
        }
        return model_names.get(model_type, "ETS_add_none_no")

    def _store_forecast_result(self, result: ForecastResult) -> None:
        """
        Store forecast result in database.

        Args:
            result: ForecastResult to store
        """
        # Convert ForecastPoint list to individual forecast records
        # Store one record per forecast day
        for i, forecast_point in enumerate(result.forecast):
            target_date = forecast_point.date
            horizon_days = i + 1  # 1-indexed horizon

            forecast_data = {
                "commodity": result.commodity,
                "state": result.state,
                "district": result.district,
                "market": result.market,
                "forecast_date": result.forecast_date,
                "target_date": target_date,
                "horizon_days": horizon_days,
                "predicted_min_price": None,  # We're only forecasting modal price for now
                "predicted_max_price": None,
                "predicted_modal_price": forecast_point.predicted_price,
                "model_name": result.model_name,
                "model_version": "1.0",
                "mae": result.metrics.get("mae"),
                "rmse": result.metrics.get("rmse"),
                "mape": result.metrics.get("mape")
            }

            try:
                self.forecast_repo.create_forecast(forecast_data)
            except Exception as e:
                logger.error(f"Error storing forecast for {target_date}: {e}")
                # Continue with other forecast days

    def _db_forecast_to_result(
        self,
        db_forecast: models.ForecastResult
    ) -> ForecastResult:
        """
        Convert database ForecastResult model to ForecastResult dataclass.

        Args:
            db_forecast: Database forecast model instance

        Returns:
            ForecastResult dataclass instance
        """
        # This is a simplified conversion - in reality, we'd need to
        # retrieve all forecast points for this forecast series
        # For now, we'll return a basic result
        forecast_points = [
            ForecastPoint(
                date=db_forecast.target_date,
                predicted_price=db_forecast.predicted_modal_price or 0.0
            )
        ]

        return ForecastResult(
            commodity=db_forecast.commodity,
            market=db_forecast.market,
            state=db_forecast.state,
            forecast_date=db_forecast.forecast_date,
            horizon_days=db_forecast.horizon_days,
            model_name=db_forecast.model_name,
            forecast=forecast_points,
            metrics={
                "mae": db_forecast.mae or 0.0,
                "rmse": db_forecast.rmse or 0.0,
                "mape": db_forecast.mape or 0.0
            },
            trend="stable"  # Default trend - would need to recalculate
        )