"""
Decision Engine service layer.

Responsibilities:
- Provide a reusable, dependency-injectable DecisionEngineService
- Normalize outputs from the EXISTING modules (Weather Intelligence,
  Market Forecast, Crop Calendar) into the Decision Engine input
  contract via optional adapters
- Delegate all decision logic to the deterministic engine in
  app.intelligence.decision_engine

This service does NOT call external APIs itself and does NOT duplicate
existing module logic: adapters only reshape data the caller already
fetched (e.g. service outputs from Weather, Market or Crop Calendar).
When adapters are not used, the caller supplies a FarmContext directly.
"""

from typing import Any, Dict, List, Optional

from app.intelligence.decision_engine import (
    ENGINE_VERSION,
    KNOWN_ML_MODELS,
    RULESET_VERSION,
    evaluate_farm_context,
)
from app.schemas.decision import (
    CropCalendarContext,
    DecisionResponse,
    FarmContext,
    MarketContext,
    MLPrediction,
    MLPredictionStatus,
    WeatherContext,
)


class DecisionEngineService:
    """
    Application service for the Context/Decision Engine.

    Usage:
        service = DecisionEngineService()
        response = service.evaluate(farm_context)
    """

    def __init__(self) -> None:
        self.engine_version = ENGINE_VERSION
        self.ruleset_version = RULESET_VERSION

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self) -> Dict[str, Any]:
        """Health snapshot (no secrets, no API keys)."""
        return {
            "status": "healthy",
            "service": "agrinexus-decision-engine",
            "version": self.engine_version,
            "engine_available": True,
            "ruleset_version": self.ruleset_version,
            "ml_model_contracts_available": list(KNOWN_ML_MODELS),
        }

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(self, context: FarmContext) -> DecisionResponse:
        """Evaluate a normalized FarmContext (deterministic)."""
        return evaluate_farm_context(context)

    # ------------------------------------------------------------------
    # Normalization adapters (reshape EXISTING module outputs)
    # ------------------------------------------------------------------

    def build_weather_context(
        self,
        *,
        current: Optional[Dict[str, Any]] = None,
        forecast: Optional[Dict[str, Any]] = None,
        insights: Optional[Dict[str, Any]] = None,
    ) -> Optional[WeatherContext]:
        """
        Build a WeatherContext from existing Weather Intelligence
        outputs (payload shapes of /api/weather/current,
        /api/weather/forecast and /api/weather/insights).

        Accepts plain dicts so callers can pass model_dump() results.
        Missing fields stay None; values are never invented. Returns
        None when no usable weather payload is supplied.
        """
        if not current and not forecast and not insights:
            return None

        def _num(value: Any) -> Optional[float]:
            try:
                return float(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        current = current or {}
        forecast = forecast or {}
        insights = insights or {}
        daily = (
            forecast.get("daily")
            or forecast.get("daily_forecast")
            or forecast.get("days")
            or []
        )
        horizon = len(daily) if isinstance(daily, list) else None

        def _agg(key: str, aggregate: str) -> Optional[float]:
            values = [
                _num(item.get(key))
                for item in daily
                if isinstance(item, dict) and _num(item.get(key)) is not None
            ]
            if not values:
                return None
            if aggregate == "sum":
                return sum(values)
            if aggregate == "min":
                return min(values)
            return max(values)

        severe = list(insights.get("severe_weather_indicators") or [])
        freshness = (
            current.get("observation_time")
            or current.get("timestamp")
            or current.get("data_timestamp")
            or forecast.get("data_timestamp")
            or insights.get("timestamp")
            or insights.get("data_timestamp")
        )

        return WeatherContext(
            latitude=_num(current.get("latitude")),
            longitude=_num(current.get("longitude")),
            current_temperature=_num(
                current.get("temperature") or current.get("temperature_c")
            ),
            current_humidity=_num(
                current.get("relative_humidity") or current.get("humidity")
            ),
            current_precipitation=_num(current.get("precipitation")),
            precipitation_probability=(
                _agg("precipitation_probability_max", "max")
                or _agg("precipitation_probability", "max")
                or _num(forecast.get("precipitation_probability"))
            ),
            forecast_precipitation_sum=(
                _agg("precipitation_sum", "sum")
                or _agg("precipitation", "sum")
            ),
            temperature_max_forecast=(
                _agg("temperature_max", "max")
                or _num(forecast.get("temperature_max"))
            ),
            temperature_min_forecast=(
                _agg("temperature_min", "min")
                or _num(forecast.get("temperature_min"))
            ),
            wind_speed_max_forecast=(
                _agg("wind_speed_max", "max")
                or _agg("wind_speed", "max")
                or _num(forecast.get("wind_speed_max"))
            ),
            severe_weather_indicators=severe,
            forecast_horizon_days=(
                _num(forecast.get("forecast_days"))
                if _num(forecast.get("forecast_days")) is not None
                else horizon
            ),
            weather_data_freshness=freshness,
            is_weather_data_available=True,
        )

    def build_market_context(
        self,
        *,
        signals: Optional[Dict[str, Any]] = None,
        forecast: Optional[Dict[str, Any]] = None,
    ) -> Optional[MarketContext]:
        """
        Build a MarketContext from existing Market Forecast outputs
        (payload shapes of /api/market/signals and /api/market/forecast).

        Accepts plain dicts so callers can pass model_dump() results.
        Missing fields stay None; values are never invented. Returns
        None when no usable market payload is supplied.
        """
        if not signals and not forecast:
            return None
        signals = signals or {}
        forecast = forecast or {}

        def _num(value: Any) -> Optional[float]:
            try:
                return float(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        trend = signals.get("trend_analysis") or {}
        forecast_analysis = signals.get("forecast_analysis") or {}
        latest = signals.get("latest_price") or {}
        freshness = (
            signals.get("timestamp")
            or latest.get("observation_date")
            or latest.get("observation_time")
        )

        return MarketContext(
            commodity=(
                signals.get("commodity") or forecast.get("commodity")
            ),
            current_price=(
                _num(latest.get("modal_price"))
                or _num(forecast_analysis.get("current_price"))
                or _num(forecast.get("current_price"))
            ),
            recent_trend=trend.get("recent_trend"),
            forecast_trend=(
                forecast_analysis.get("trend") or forecast.get("trend")
            ),
            recent_change_percent=_num(trend.get("recent_change_percent")),
            forecast_change_percent=_num(
                trend.get("forecast_change_percent")
            ),
            volatility=_num(trend.get("volatility")),
            signal_strength=_num(trend.get("signal_strength")),
            analysis_period_days=(
                int(_num(trend.get("analysis_period_days")))
                if _num(trend.get("analysis_period_days")) is not None
                else None
            ),
            market_data_freshness=freshness,
            is_market_data_available=True,
        )

    def build_crop_calendar_context(
        self,
        *,
        schedule: Optional[Dict[str, Any]] = None,
        static_calendar: Optional[Dict[str, Any]] = None,
    ) -> Optional[CropCalendarContext]:
        """
        Build a CropCalendarContext from existing Crop Calendar outputs
        (payload shapes of the /api/crop-calendar schedule and static
        endpoints).

        Accepts plain dicts so callers can pass model_dump() results.
        Missing fields stay None; values are never invented (in
        particular, no growth stage is assumed when the calendar did
        not provide one). Returns None when no usable payload is given.
        """
        if not schedule and not static_calendar:
            return None
        schedule = schedule or {}
        static_calendar = static_calendar or {}
        harvest = schedule.get("harvest_window") or {}

        return CropCalendarContext(
            crop=(
                schedule.get("crop") or static_calendar.get("crop")
            ),
            season=(
                schedule.get("season") or static_calendar.get("season")
            ),
            sowing_date=schedule.get("sowing_date"),
            current_growth_stage=schedule.get("current_stage"),
            stage_progress_percent=schedule.get(
                "current_stage_progress_percent"
            ),
            next_stage=schedule.get("next_stage"),
            expected_harvest_window_start=harvest.get("start_date"),
            expected_harvest_window_end=harvest.get("end_date"),
            days_to_next_stage=schedule.get("days_to_next_stage"),
            calendar_confidence=(
                schedule.get("data_source")
                or static_calendar.get("data_source")
            ),
            is_crop_calendar_available=True,
        )

    def build_ml_prediction(
        self,
        model_name: str,
        *,
        prediction: Optional[str] = None,
        confidence: Optional[float] = None,
        top_predictions: Optional[List[Dict[str, Any]]] = None,
        probability: Optional[float] = None,
        unit: Optional[str] = None,
        timestamp: Optional[str] = None,
        model_version: Optional[str] = None,
        status: str = "available",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MLPrediction:
        """
        Build the standardized MLPrediction contract.

        This is an adapter only: values are echoed as provided by the
        ML layer. Unavailable models are represented with
        status='unavailable' and prediction=None - never fabricated.
        """
        return MLPrediction(
            model_name=model_name,
            prediction=prediction,
            confidence=confidence,
            top_predictions=top_predictions,
            probability=probability,
            unit=unit,
            timestamp=timestamp,
            model_version=model_version,
            status=MLPredictionStatus(status),
            metadata=metadata,
        )