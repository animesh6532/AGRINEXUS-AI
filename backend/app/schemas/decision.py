"""
Pydantic schemas for the Context/Decision Engine API.

Defines the normalized farm context, the standardized ML prediction
contract, and the structured/explainable decision responses produced by
the deterministic decision engine.

Conventions follow the existing weather/market/crop_calendar schemas
(Pydantic v2, Field with examples, Response style).

IMPORTANT SCOPE NOTE:
The Decision Engine is NOT an ML model. It consumes normalized outputs
from the existing modules (Weather Intelligence, Market Forecast, Crop
Calendar) plus standardized ML prediction contracts, and produces
explainable farming decisions using deterministic rule-based logic.
It does not train, replace, or reimplement any of the project's ML models.
"""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enumerations
# =============================================================================


class DecisionStatus(str, Enum):
    """
    Overall context status of a decision evaluation (documented meaning):

    - complete_context:     all major data sources available
    - partial_context:      some sources missing; decisions still produced
                            from what IS available (no substitution)
    - insufficient_context: too few sources available to responsibly decide
    - conflicting_signals:  sources disagree; conflict surfaced explicitly
                            instead of being silently resolved
    """
    complete_context = "complete_context"
    partial_context = "partial_context"
    insufficient_context = "insufficient_context"
    conflicting_signals = "conflicting_signals"


class Priority(str, Enum):
    """
    Decision priority levels. Deterministic rules are documented in
    backend/app/intelligence/decision_engine.py and backend/README.md:

    - low:      informational (e.g. data-quality notes)
    - medium:   advisory worth noting (e.g. review irrigation plan)
    - high:     significant condition requiring attention (e.g. adverse
                weather during a sensitive growth stage, conflicting
                signals between sources)
    - critical: immediate threat to the crop (e.g. severe weather in a
                sensitive stage, high-probability disease/pest risk with
                favourable conditions)

    Priority is about the agricultural situation, NOT about model
    confidence. Confidence and priority are different concepts.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionType(str, Enum):
    """Types of contextual decisions the engine can produce."""
    weather_irrigation_interaction = "weather_irrigation_interaction"
    weather_crop_stage_interaction = "weather_crop_stage_interaction"
    disease_weather_risk = "disease_weather_risk"
    pest_crop_stage_risk = "pest_crop_stage_risk"
    market_crop_context = "market_crop_context"
    fertilizer_contextualization = "fertilizer_contextualization"
    yield_market_context = "yield_market_context"
    conflicting_signals = "conflicting_signals"
    data_quality_alert = "data_quality_alert"
    general_advisory = "general_advisory"


class MLPredictionStatus(str, Enum):
    """Status of an ML prediction supplied to the engine."""
    available = "available"
    unavailable = "unavailable"
    error = "error"


# =============================================================================
# Standardized ML prediction contract
# =============================================================================


class MLPrediction(BaseModel):
    """
    Standardized ML prediction consumed by the Decision Engine.

    This is a CONTRACT, not a model implementation. The engine never
    fabricates predictions:
    - an unavailable model is passed with status="unavailable" and
      prediction=None;
    - a model that does not report confidence leaves confidence=None
      (confidence is never manufactured).
    """
    model_name: str = Field(
        ...,
        example="disease_detection",
        description="Standardized model name, e.g. crop_recommendation, "
                    "soil_analysis, disease_detection, pest_prediction, "
                    "fertilizer_recommendation, smart_irrigation, "
                    "crop_yield_prediction",
    )
    prediction: Optional[str] = Field(
        None,
        description="Model prediction as a string; None when unavailable",
        example="Leaf blight",
    )
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Model-reported confidence; None when not provided",
        example=0.82,
    )
    top_predictions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional ranked alternatives as provided by the model",
    )
    probability: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Model-reported probability of the predicted outcome; "
                    "None when not provided",
        example=0.74,
    )
    unit: Optional[str] = Field(
        None,
        description="Unit for numeric predictions where applicable",
        example="mm",
    )
    timestamp: Optional[str] = Field(
        None,
        description="Prediction timestamp as provided by the model",
        example="2026-09-19T10:30:00+00:00",
    )
    model_version: Optional[str] = Field(
        None, description="Model version if the model reports one",
        example="1.3.0",
    )
    status: MLPredictionStatus = Field(
        default=MLPredictionStatus.available,
        description="available | unavailable | error",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional structured hints from the model (e.g. "
                    "irrigation_required, soil_moisture_level, risk_level)",
    )


# =============================================================================
# Normalized context objects (consumed from existing module outputs)
# =============================================================================


class WeatherContext(BaseModel):
    """
    Normalized weather signals consumed from Weather Intelligence outputs.

    Values are never invented: when a signal is not available from the
    weather module, the corresponding field stays None.
    """
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    current_temperature: Optional[float] = Field(
        None, description="Current temperature (deg C)", example=28.5,
    )
    current_humidity: Optional[float] = Field(
        None, ge=0, le=100,
        description="Current relative humidity (%)", example=75.0,
    )
    current_precipitation: Optional[float] = Field(
        None, ge=0, description="Current precipitation (mm)", example=0.0,
    )
    precipitation_probability: Optional[float] = Field(
        None, ge=0, le=100,
        description="Maximum forecast precipitation probability (%)",
        example=80.0,
    )
    forecast_precipitation_sum: Optional[float] = Field(
        None, ge=0,
        description="Sum of forecast precipitation over the horizon (mm)",
        example=25.0,
    )
    temperature_max_forecast: Optional[float] = Field(
        None, description="Maximum forecast temperature (deg C)",
        example=32.0,
    )
    temperature_min_forecast: Optional[float] = Field(
        None, description="Minimum forecast temperature (deg C)",
        example=23.5,
    )
    wind_speed_max_forecast: Optional[float] = Field(
        None, ge=0, description="Maximum forecast wind speed (km/h)",
        example=25.0,
    )
    severe_weather_indicators: List[str] = Field(
        default_factory=list,
        description="Severe-weather indicators reported by the weather module",
    )
    forecast_horizon_days: Optional[int] = Field(
        None, ge=1, le=16,
        description="Forecast horizon available (days)", example=7,
    )
    weather_data_freshness: Optional[str] = Field(
        None,
        description="Observation/forecast timestamp from the weather module "
                    "(freshness as reported; never fabricated)",
        example="2026-09-18T10:30",
    )
    is_weather_data_available: bool = Field(
        False,
        description="Whether weather data was supplied in this context",
    )


class MarketContext(BaseModel):
    """
    Normalized market signals consumed from Market Forecast outputs.

    Trend values reuse the existing Market Forecast contract
    (increasing | decreasing | stable | insufficient_data).
    """
    commodity: Optional[str] = Field(
        None, description="Commodity analysed", example="Paddy(Common)",
    )
    current_price: Optional[float] = Field(
        None, ge=0, description="Latest/current modal price", example=2800.0,
    )
    recent_trend: Optional[str] = Field(
        None,
        pattern="^(increasing|decreasing|stable|insufficient_data)$",
        description="Trend over the recent analysis period",
        example="increasing",
    )
    forecast_trend: Optional[str] = Field(
        None,
        pattern="^(increasing|decreasing|stable|insufficient_data)$",
        description="Trend expected over the forecast horizon",
        example="increasing",
    )
    recent_change_percent: Optional[float] = Field(
        None, description="Recent price change (%)", example=4.2,
    )
    forecast_change_percent: Optional[float] = Field(
        None, description="Forecast price change (%)", example=6.1,
    )
    volatility: Optional[float] = Field(
        None, ge=0, description="Recent price volatility (%)", example=3.5,
    )
    signal_strength: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Market signal strength as reported by the Market "
                    "Forecast module", example=0.8,
    )
    analysis_period_days: Optional[int] = Field(
        None, ge=1, description="Analysis period (days)", example=30,
    )
    market_data_freshness: Optional[str] = Field(
        None,
        description="Latest observation date/timestamp as reported",
        example="2026-09-17",
    )
    is_market_data_available: bool = Field(
        False,
        description="Whether market data was supplied in this context",
    )


class CropCalendarContext(BaseModel):
    """
    Normalized crop-calendar signals consumed from Crop Calendar outputs.

    Growth stage information comes from the Crop Calendar module; the
    engine never assumes a stage that the calendar did not provide.
    """
    crop: Optional[str] = Field(None, example="rice")
    season: Optional[str] = Field(None, example="kharif")
    sowing_date: Optional[date] = Field(None, example="2026-06-15")
    current_growth_stage: Optional[str] = Field(
        None,
        description="Current growth stage as provided by the Crop Calendar",
        example="tillering",
    )
    stage_progress_percent: Optional[float] = Field(
        None, ge=0, le=100,
        description="Progress through the current stage (percent)",
        example=40.0,
    )
    next_stage: Optional[str] = Field(None, example="panicle_initiation")
    expected_harvest_window_start: Optional[date] = Field(
        None, description="Harvest window start date from the calendar",
        example="2026-10-17",
    )
    expected_harvest_window_end: Optional[date] = Field(
        None, description="Harvest window end date from the calendar",
        example="2026-11-06",
    )
    days_to_next_stage: Optional[int] = Field(
        None, description="Days until the next stage (when provided)",
        example=12,
    )
    calendar_confidence: Optional[str] = Field(
        None,
        description="Calendar provenance/confidence as reported by the "
                    "Crop Calendar module (e.g. reference dataset label)",
        example="reference_dataset",
    )
    is_crop_calendar_available: bool = Field(
        False,
        description="Whether crop calendar data was supplied in this context",
    )


# =============================================================================
# Central context object
# =============================================================================


class FarmContext(BaseModel):
    """
    Central normalized context consumed by the Decision Engine.

    All fields are optional where existing modules may not reliably
    provide them. The engine degrades gracefully: missing data leads to
    partial/insufficient context status - never to fabricated values.
    """
    location: Optional[str] = Field(
        None, description="Farmer-supplied location label",
        example="West Bengal",
    )
    latitude: Optional[float] = Field(None, ge=-90, le=90, example=22.9868)
    longitude: Optional[float] = Field(None, ge=-180, le=180, example=87.8550)
    crop: Optional[str] = Field(
        None, description="Crop of interest", example="rice",
    )
    variety: Optional[str] = Field(None, example="MTU 7029")
    season: Optional[str] = Field(None, example="kharif")
    sowing_date: Optional[date] = Field(None, example="2026-06-15")
    current_growth_stage: Optional[str] = Field(
        None,
        description="Optional farmer-supplied growth stage. Used only when "
                    "crop_calendar_context does not provide a stage "
                    "(calendar data takes precedence).",
        example="tillering",
    )
    weather_context: Optional[WeatherContext] = Field(
        None, description="Normalized weather signals (Weather Intelligence)",
    )
    market_context: Optional[MarketContext] = Field(
        None, description="Normalized market signals (Market Forecast)",
    )
    crop_calendar_context: Optional[CropCalendarContext] = Field(
        None, description="Normalized calendar signals (Crop Calendar)",
    )
    ml_predictions: List[MLPrediction] = Field(
        default_factory=list,
        description="Standardized ML predictions (friend's ML layer). "
                    "Unavailable models are passed with "
                    "status='unavailable' and are never fabricated.",
    )
    farmer_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional farmer/context metadata (irrigation plans, "
                    "field notes, etc.). Free-form; never required.",
    )
    data_freshness: Optional[Dict[str, str]] = Field(
        None,
        description="Optional source-freshness map "
                    "({source: ISO-8601 timestamp}) as reported by callers",
    )
    as_of_date: Optional[date] = Field(
        None,
        description="Evaluation 'as of' date (defaults to engine evaluation "
                    "date where needed; never fabricated backwards)",
        example="2026-09-19",
    )


# =============================================================================
# Decision building blocks
# =============================================================================


class SupportingSignal(BaseModel):
    """A single piece of evidence supporting a decision (traceable)."""
    signal: str = Field(
        ...,
        description="Machine-readable signal name, e.g. "
                    "high_precipitation_probability",
        example="high_precipitation_probability",
    )
    source: str = Field(
        ...,
        description="Contributing source, e.g. weather | market | "
                    "crop_calendar | <ml model name>",
        example="weather",
    )
    description: Optional[str] = Field(
        None,
        description="Human-readable explanation of the signal",
        example="Precipitation probability: 80%",
    )
    value: Optional[Any] = Field(
        None,
        description="Raw supporting value where available (e.g. 80.0)",
        example=80.0,
    )


class ContributingSource(BaseModel):
    """A data source that contributed to a decision."""
    source: str = Field(
        ..., description="Source identifier", example="weather",
    )
    source_type: str = Field(
        ...,
        pattern="^(external_data|ml_model|farmer_context)$",
        description="external_data | ml_model | farmer_context",
        example="external_data",
    )
    detail: Optional[str] = Field(
        None,
        description="What this source contributed",
        example="Forecast precipitation and probability signals",
    )


class DecisionWarning(BaseModel):
    """A warning attached to a decision (e.g. data limitations)."""
    warning: str = Field(
        ...,
        description="Warning text",
        example="Market data was unavailable; market context not evaluated",
    )
    source: Optional[str] = Field(
        None, description="Source/module the warning relates to",
        example="market",
    )


class DataQuality(BaseModel):
    """
    Lightweight deterministic data-quality assessment.

    - status: one of the DecisionStatus values
    - completeness_percent: share of expected sources present (documented:
      3 data sources + 7 known ML model contracts = 10 expected inputs)
    - missing_sources / stale_sources / conflicts /
      unavailable_ml_models / missing_critical_fields: explicit lists,
      never fabricated
    """
    status: str = Field(
        ...,
        pattern="^(complete_context|partial_context|insufficient_context|"
                "conflicting_signals)$",
        description="Overall data-quality status",
        example="partial_context",
    )
    completeness_percent: Optional[float] = Field(
        None, ge=0, le=100,
        description="Share of expected sources present (%)",
        example=40.0,
    )
    missing_sources: List[str] = Field(default_factory=list)
    stale_sources: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    unavailable_ml_models: List[str] = Field(default_factory=list)
    missing_critical_fields: List[str] = Field(default_factory=list)


# =============================================================================
# Decision responses
# =============================================================================


class Decision(BaseModel):
    """
    A single structured, explainable decision.

    Every decision is traceable: `reason` explains WHY, `supporting_signals`
    lists the evidence, and `contributing_sources` identifies where each
    piece of evidence came from.
    """
    id: str = Field(
        ...,
        description="Deterministic unique identifier for this decision",
    )
    decision_type: DecisionType = Field(
        ..., description="Type of contextual decision",
        example="weather_irrigation_interaction",
    )
    status: DecisionStatus = Field(
        ..., description="Context status of the evaluation",
        example="partial_context",
    )
    priority: Priority = Field(
        ..., description="Deterministic priority (documented rules)",
        example="medium",
    )
    severity: Optional[str] = Field(
        None,
        description="Optional severity label where applicable "
                    "(e.g. adverse-weather severity)",
        example="moderate",
    )
    title: str = Field(
        ..., description="Short decision title", example="Review Planned "
        "Irrigation Due to Expected Rainfall",
    )
    summary: str = Field(
        ..., description="Farmer-readable summary of the decision",
    )
    reason: str = Field(
        ...,
        description="Explainable reason: which signals, which sources, "
                    "and why the conclusion was reached",
    )
    crop: Optional[str] = Field(None, example="rice")
    growth_stage: Optional[str] = Field(
        None,
        description="Growth stage used in this decision (only when "
                    "crop calendar or farmer context provided one)",
        example="tillering",
    )
    location: Optional[str] = Field(None, example="West Bengal")
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Decision confidence (NOT model confidence). "
                    "Methodology documented in the engine: based on number "
                    "and agreement of contributing sources. Null when it "
                    "cannot be responsibly calculated.",
        example=0.75,
    )
    confidence_rationale: Optional[str] = Field(
        None,
        description="How confidence was derived (when present)",
        example="Two independent sources agree (weather + irrigation model)",
    )
    contributing_sources: List[ContributingSource] = Field(
        default_factory=list,
        description="All sources that contributed to this decision",
    )
    supporting_signals: List[SupportingSignal] = Field(
        default_factory=list,
        description="Evidence signals supporting this decision",
    )
    warnings: List[DecisionWarning] = Field(
        default_factory=list,
        description="Data limitations/warnings attached to this decision",
    )
    created_at: str = Field(
        ..., description="Decision creation timestamp (ISO-8601, UTC)",
        example="2026-09-19T10:30:00+00:00",
    )


class DecisionResponse(BaseModel):
    """Full evaluation response: context status, data quality, decisions."""
    status: DecisionStatus = Field(
        ..., description="Overall context status of the evaluation",
        example="partial_context",
    )
    data_quality: DataQuality = Field(
        ..., description="Deterministic data-quality assessment",
    )
    decisions: List[Decision] = Field(
        default_factory=list,
        description="Structured decisions produced from the available "
                    "signals (empty list when context is insufficient)",
    )
    warnings: List[DecisionWarning] = Field(
        default_factory=list,
        description="Evaluation-level warnings (e.g. unavailable sources)",
    )
    engine_version: str = Field(
        ..., description="Decision engine version", example="1.0.0",
    )
    ruleset_version: str = Field(
        ..., description="Deterministic ruleset version", example="1.0.0",
    )
    evaluation_timestamp: str = Field(
        ..., description="Evaluation timestamp (ISO-8601, UTC)",
        example="2026-09-19T10:30:00+00:00",
    )
    total_decisions: int = Field(
        ..., ge=0, description="Number of decisions produced", example=2,
    )


class DecisionHealthResponse(BaseModel):
    """
    Health check response for the Decision Engine.

    Reports engine/ruleset availability only. Never exposes secrets,
    API keys, or credentials of any kind.
    """
    status: str = Field(
        ..., description="Service status (healthy)", example="healthy",
    )
    service: str = Field(
        ..., description="Service name",
        example="agrinexus-decision-engine",
    )
    version: str = Field(..., example="1.0.0")
    timestamp: str = Field(
        ..., example="2026-09-19T10:30:00+00:00",
    )
    engine_available: bool = Field(
        ..., description="Whether the decision engine is operational",
        example=True,
    )
    ruleset_version: str = Field(
        ..., description="Active deterministic ruleset version",
        example="1.0.0",
    )
    ml_model_contracts_available: List[str] = Field(
        default_factory=list,
        description="Known standardized ML prediction contracts the engine "
                    "can consume (contract names only; no model secrets)",
        example=[
            "crop_recommendation", "soil_analysis", "disease_detection",
            "pest_prediction", "fertilizer_recommendation",
            "smart_irrigation", "crop_yield_prediction",
        ],
    )
