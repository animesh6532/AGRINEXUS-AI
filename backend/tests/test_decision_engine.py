"""
Unit tests for the deterministic Decision Engine
(app/intelligence/decision_engine.py).

These tests exercise the pure decision logic with NO external API calls,
NO HTTP transport and NO ML model implementations. FarmContext inputs are
constructed directly from the normalized schemas. No secrets or API keys
are used anywhere in this file.
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.intelligence.decision_engine import (
    EXPECTED_SOURCE_COUNT,
    ENGINE_VERSION,
    KNOWN_ML_MODELS,
    RULESET_VERSION,
    evaluate_farm_context,
)
from app.schemas.decision import (
    CropCalendarContext,
    DecisionStatus,
    DecisionType,
    FarmContext,
    MarketContext,
    MLPrediction,
    MLPredictionStatus,
    Priority,
    WeatherContext,
)

AS_OF = date(2026, 9, 19)


# =============================================================================
# Fixtures / builders (deterministic test data)
# =============================================================================


def make_ml(model_name, *, prediction=None, probability=None,
            confidence=None, unit=None, status="available", metadata=None):
    """Build a standardized MLPrediction (values echoed, never invented)."""
    return MLPrediction(
        model_name=model_name,
        prediction=prediction,
        probability=probability,
        confidence=confidence,
        unit=unit,
        status=MLPredictionStatus(status),
        metadata=metadata,
    )


def make_weather(**overrides):
    """Calm-weather WeatherContext; overrides activate signals."""
    values = dict(
        is_weather_data_available=True,
        precipitation_probability=10.0,
        forecast_precipitation_sum=0.0,
        temperature_max_forecast=30.0,
        temperature_min_forecast=20.0,
        wind_speed_max_forecast=10.0,
        current_humidity=60.0,
    )
    values.update(overrides)
    return WeatherContext(**values)


def make_market(**overrides):
    values = dict(
        is_market_data_available=True,
        commodity="Paddy (Common)",
        current_price=2800.0,
        recent_trend="stable",
        forecast_trend="stable",
    )
    values.update(overrides)
    return MarketContext(**values)


def make_calendar(**overrides):
    values = dict(is_crop_calendar_available=True, crop="rice")
    values.update(overrides)
    return CropCalendarContext(**values)


def make_context(**kwargs):
    """FarmContext with stable identity fields; sources passed via kwargs."""
    kwargs.setdefault("crop", "rice")
    kwargs.setdefault("location", "West Bengal")
    kwargs.setdefault("sowing_date", date(2026, 6, 15))
    kwargs.setdefault("as_of_date", AS_OF)
    return FarmContext(**kwargs)


def decision_types(response):
    return [d.decision_type for d in response.decisions]


def irrigation_advisory_ml(**overrides):
    values = dict(
        prediction="sufficient_soil_moisture",
        probability=0.9,
        metadata={"soil_moisture_level": "high"},
    )
    values.update(overrides)
    return make_ml("smart_irrigation", **values)


# =============================================================================
# Minimal / empty context and engine metadata
# =============================================================================


class TestMinimalContext:
    def test_empty_context_is_insufficient(self):
        response = evaluate_farm_context(make_context())
        assert response.status == DecisionStatus.insufficient_context
        assert response.total_decisions == 0
        assert response.decisions == []

    def test_empty_context_data_quality(self):
        response = evaluate_farm_context(make_context())
        dq = response.data_quality
        assert dq.status == "insufficient_context"
        assert dq.completeness_percent == 0.0
        assert dq.missing_sources == [
            "crop_calendar", "market", "weather",
        ]
        assert dq.unavailable_ml_models == []
        assert dq.missing_critical_fields == []

    def test_empty_context_warnings_report_missing_sources(self):
        response = evaluate_farm_context(make_context())
        warned = {w.source for w in response.warnings}
        assert {"weather", "market", "crop_calendar"} <= warned

    def test_engine_metadata_present(self):
        response = evaluate_farm_context(make_context())
        assert response.engine_version == ENGINE_VERSION == "1.0.0"
        assert response.ruleset_version == RULESET_VERSION == "1.0.0"
        assert response.evaluation_timestamp.endswith("+00:00")
        assert response.total_decisions == len(response.decisions)

    def test_known_ml_model_contracts(self):
        assert KNOWN_ML_MODELS == [
            "crop_recommendation",
            "soil_analysis",
            "disease_detection",
            "pest_prediction",
            "fertilizer_recommendation",
            "smart_irrigation",
            "crop_yield_prediction",
        ]
        # 3 data sources + 7 ML contracts drive the completeness formula.
        assert EXPECTED_SOURCE_COUNT == 10

# === PART_2 ===
