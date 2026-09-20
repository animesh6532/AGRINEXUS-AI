"""
Decision Engine - Deterministic Rule-Based Decision Intelligence.

Consumes a normalized FarmContext (weather / market / crop-calendar
signals + standardized ML prediction contracts) and produces structured,
explainable farming decisions using deterministic rules.

DESIGN PRINCIPLES
-----------------
- Deterministic: the same input always produces the same output
  (except timestamps/IDs, which are documented).
- Explainable: every decision carries reason, supporting signals and
  contributing sources.
- No ML: this module is NOT a model. It never fabricates ML predictions,
  never manufactures model confidence, and never substitutes default
  agricultural values for missing data.
- Priority is about the agricultural situation, not model confidence.

PRIORITY RULES (documented, deterministic)
------------------------------------------
- CRITICAL: severe weather indicator in a sensitive growth stage.
- HIGH:     adverse weather (heavy rain/extreme temp/strong wind) during a
            sensitive growth stage, OR any conflicting signal between
            sources, OR high-probability disease/pest risk (disease with
            weather amplifiers is HIGH at probability >= 0.8, otherwise
            MEDIUM).
- MEDIUM:   advisory interactions (weather + irrigation, market + crop,
            fertilizer contextualization, yield + market) or a
            data-quality alert on a partial context.
- LOW:      data-quality-only advisories on insufficient context.

CONFIDENCE METHODOLOGY (decision confidence, NOT model confidence)
------------------------------------------------------------------
- confidence = base 0.5 (2 agreeing independent sources)
             + 0.1 per additional agreeing independent source
             + 0.1 when the interacting pair includes an ML model that
               reports its own confidence/probability
             capped at 0.9 (no false precision)
- When fewer than two independent sources contribute, confidence is
  returned as None (unknown) rather than invented.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.decision import (
    ContributingSource,
    CropCalendarContext,
    DataQuality,
    Decision,
    DecisionStatus,
    DecisionType,
    DecisionWarning,
    FarmContext,
    MarketContext,
    MLPrediction,
    Priority,
    SupportingSignal,
    WeatherContext,
)

# Engine / ruleset versions (bumped when decision rules change).
ENGINE_VERSION = "1.0.0"
RULESET_VERSION = "1.0.0"

# Known standardized ML model contracts (friend's ML layer).
KNOWN_ML_MODELS = [
    "crop_recommendation",
    "soil_analysis",
    "disease_detection",
    "pest_prediction",
    "fertilizer_recommendation",
    "smart_irrigation",
    "crop_yield_prediction",
]

# Growth stages considered sensitive/important (from the Crop Calendar's
# agronomic stage vocabulary). Sensitive stages amplify weather risks.
SENSITIVE_STAGES = {
    "transplanting",
    "seedling",
    "vegetative",
    "tillering",
    "panicle initiation",
    "panicle_initiation",
    "booting",
    "flowering",
    "grain filling",
    "grain_filling",
    "fruiting",
    "pod development",
    "pod_development",
    "boll formation",
    "tuber bulking",
    "silking",
    "heading",
}

# Crop/commodity synonym groups used for deterministic crop <-> market
# commodity matching. Market Forecast commodity names (Agmarknet style,
# e.g. "Paddy (Common)") differ from Crop Calendar crop names (e.g.
# "rice"); these groups are a fixed, documented lookup - no data is
# invented or inferred from any external service.
CROP_SYNONYM_GROUPS = (
    ("paddy", "rice"),
    ("maize", "corn"),
    ("groundnut", "peanut"),
    ("soybean", "soya", "soyabean"),
    ("gram", "chana", "chickpea", "bengal"),
    ("jute", "raw jute"),
    ("cotton", "kapas"),
    ("wheat", "gehun"),
    ("onion", "pyaz"),
    ("potato", "aloo"),
    ("tomato",),
    ("sugarcane", "cane"),
    ("mustard", "rapeseed"),
    ("sesame", "til"),
    ("bajra", "pearl millet"),
    ("jowar", "sorghum"),
    ("ragi", "finger millet"),
)

# Minimum word length used when matching crop words against commodity
# names (avoids noise from very short synonyms such as "raw").
MIN_MATCH_WORD_LENGTH = 3

# Number of expected inputs for completeness (3 data sources + 7 ML
# model contracts = 10). Used by the deterministic data-quality scorer.
EXPECTED_SOURCE_COUNT = 10

# Data older than this many days is considered stale when a freshness
# timestamp is provided.
STALENESS_DAYS_THRESHOLD = 3

# Deterministic decision thresholds (documented constants).
PRECIP_PROBABILITY_THRESHOLD = 70.0     # percent
PRECIPITATION_MM_THRESHOLD = 10.0       # mm over forecast horizon
HEAVY_RAINFALL_MM_THRESHOLD = 50.0      # mm over forecast horizon
EXTREME_HEAT_C_THRESHOLD = 38.0         # deg C max forecast
FROST_C_THRESHOLD = 5.0                 # deg C min forecast
STRONG_WIND_KMH_THRESHOLD = 30.0        # km/h max forecast
HIGH_HUMIDITY_PERCENT = 80.0            # percent current humidity
ML_PROBABILITY_THRESHOLD = 0.6          # elevated ML probability
MARKET_CHANGE_PERCENT_THRESHOLD = 3.0   # meaningful market change (%)


# =============================================================================
# Internal helpers (pure functions - deterministic)
# =============================================================================


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _normalize(name: Optional[str]) -> str:
    """Normalize a name (crop/stage/commodity) for comparisons."""
    if not name:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _stage_is_sensitive(stage: Optional[str]) -> bool:
    normalized = _normalize(stage)
    if not normalized:
        return False
    return any(
        normalized == _normalize(s) or _normalize(s) in normalized
        for s in SENSITIVE_STAGES
    )


def _decision_id(context: FarmContext, decision_type: str) -> str:
    """Deterministic ID from stable context attributes + decision type."""
    payload = "|".join([
        decision_type,
        _normalize(context.crop),
        _normalize(context.location),
        str(context.sowing_date or ""),
        str(context.as_of_date or ""),
    ])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"dec-{digest}"


def _get_ml(context: FarmContext, model_name: str) -> Optional[MLPrediction]:
    """Return an AVAILABLE prediction for a model, else None.

    Unavailable/errored models are never treated as data and never
    fabricated; they are reported in data quality instead.
    """
    for pred in context.ml_predictions:
        if pred.model_name == model_name and pred.status == "available":
            return pred
    return None


def _model_probability(pred: MLPrediction) -> Optional[float]:
    """Best available probability from a prediction, or None.

    Uses model-provided probability/confidence only - never manufactures
    a value.
    """
    if pred.probability is not None:
        return pred.probability
    if pred.confidence is not None:
        return pred.confidence
    return None


def _effective_growth_stage(context: FarmContext) -> Optional[str]:
    """Resolve the growth stage: crop calendar first, farmer fallback.

    The Crop Calendar module is authoritative for stage information.
    The farmer-supplied stage is used only when the calendar is absent.
    """
    if context.crop_calendar_context and \
            context.crop_calendar_context.current_growth_stage:
        return context.crop_calendar_context.current_growth_stage
    return context.current_growth_stage


def _available_source_names(context: FarmContext) -> List[str]:
    """Names of the data sources present in the context."""
    sources: List[str] = []
    if context.weather_context and context.weather_context.is_weather_data_available:
        sources.append("weather")
    if context.market_context and context.market_context.is_market_data_available:
        sources.append("market")
    if context.crop_calendar_context and \
            context.crop_calendar_context.is_crop_calendar_available:
        sources.append("crop_calendar")
    return sources


def _unavailable_ml_models(context: FarmContext) -> List[str]:
    """Known ML models explicitly reported as unavailable/error."""
    unavailable: List[str] = []
    for pred in context.ml_predictions:
        if pred.model_name in KNOWN_ML_MODELS and pred.status in (
            "unavailable", "error",
        ):
            unavailable.append(pred.model_name)
    return sorted(set(unavailable))


def _weather_signals(context: FarmContext) -> Dict[str, Any]:
    """
    Extract boolean weather signals from the Weather Intelligence context.

    Returns a dict of signal_name -> {"active": bool, "detail": str,
    "value": float|None}. A signal is marked inactive when the underlying
    value is absent (missing data never becomes a fabricated value).
    """
    signals: Dict[str, Any] = {}
    wx = context.weather_context
    if not wx or not wx.is_weather_data_available:
        return signals

    if wx.precipitation_probability is not None:
        active = wx.precipitation_probability >= PRECIP_PROBABILITY_THRESHOLD
        signals["high_precipitation_probability"] = {
            "active": active,
            "detail": (
                f"Forecast precipitation probability: "
                f"{wx.precipitation_probability}%"
            ),
            "value": wx.precipitation_probability,
        }
    if wx.forecast_precipitation_sum is not None:
        heavy = wx.forecast_precipitation_sum >= HEAVY_RAINFALL_MM_THRESHOLD
        notable = wx.forecast_precipitation_sum >= PRECIPITATION_MM_THRESHOLD
        signals["heavy_rainfall_expected"] = {
            "active": heavy,
            "detail": (
                f"Forecast rainfall total: "
                f"{wx.forecast_precipitation_sum} mm over horizon"
            ),
            "value": wx.forecast_precipitation_sum,
        }
        signals["notable_rainfall_expected"] = {
            "active": notable and not heavy,
            "detail": (
                f"Forecast rainfall total: "
                f"{wx.forecast_precipitation_sum} mm over horizon"
            ),
            "value": wx.forecast_precipitation_sum,
        }
    if wx.temperature_max_forecast is not None:
        active = wx.temperature_max_forecast >= EXTREME_HEAT_C_THRESHOLD
        signals["extreme_heat_expected"] = {
            "active": active,
            "detail": (
                f"Forecast maximum temperature: "
                f"{wx.temperature_max_forecast} deg C"
            ),
            "value": wx.temperature_max_forecast,
        }
    if wx.temperature_min_forecast is not None:
        active = wx.temperature_min_forecast <= FROST_C_THRESHOLD
        signals["frost_risk_expected"] = {
            "active": active,
            "detail": (
                f"Forecast minimum temperature: "
                f"{wx.temperature_min_forecast} deg C"
            ),
            "value": wx.temperature_min_forecast,
        }
    if wx.wind_speed_max_forecast is not None:
        active = wx.wind_speed_max_forecast >= STRONG_WIND_KMH_THRESHOLD
        signals["strong_wind_expected"] = {
            "active": active,
            "detail": (
                f"Forecast maximum wind speed: "
                f"{wx.wind_speed_max_forecast} km/h"
            ),
            "value": wx.wind_speed_max_forecast,
        }
    if wx.current_humidity is not None:
        active = wx.current_humidity >= HIGH_HUMIDITY_PERCENT
        signals["high_humidity"] = {
            "active": active,
            "detail": f"Current humidity: {wx.current_humidity}%",
            "value": wx.current_humidity,
        }
    if wx.severe_weather_indicators:
        signals["severe_weather_indicator"] = {
            "active": True,
            "detail": (
                "Severe weather indicators: "
                f"{', '.join(wx.severe_weather_indicators)}"
            ),
            "value": list(wx.severe_weather_indicators),
        }
    return signals


def _active_signal_names(signals: Dict[str, Any]) -> List[str]:
    return sorted(name for name, info in signals.items() if info["active"])


def _adverse_signals(signals: Dict[str, Any]) -> List[str]:
    """Active weather signals that are adverse for field operations."""
    adverse = [
        "heavy_rainfall_expected",
        "extreme_heat_expected",
        "frost_risk_expected",
        "strong_wind_expected",
        "severe_weather_indicator",
    ]
    return sorted(
        name for name in adverse
        if name in signals and signals[name]["active"]
    )


def _context_status(context: FarmContext, conflicts: List[str]) -> str:
    """
    Deterministic context status:
    - conflicting_signals when any conflicts were detected
    - insufficient_context when no data source at all is available
    - complete_context when weather+market+calendar all available
    - partial_context otherwise
    """
    if conflicts:
        return DecisionStatus.conflicting_signals.value
    available = _available_source_names(context)
    ml_available = any(
        p.status == "available" for p in context.ml_predictions
    )
    if not available and not ml_available:
        return DecisionStatus.insufficient_context.value
    if set(available) == {"weather", "market", "crop_calendar"}:
        return DecisionStatus.complete_context.value
    return DecisionStatus.partial_context.value


def _stale_sources(context: FarmContext) -> List[str]:
    """
    Deterministic staleness check on caller-provided freshness timestamps
    (context.data_freshness map). Sources without timestamps are NOT
    marked stale - freshness is only assessed when a timestamp exists.
    """
    stale: List[str] = []
    freshness = context.data_freshness or {}
    now = datetime.now(timezone.utc)
    for source, ts in freshness.items():
        parsed = None
        raw = (ts or "").strip()
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        age_days = (now - parsed).total_seconds() / 86400.0
        if age_days > STALENESS_DAYS_THRESHOLD:
            stale.append(source)
    return sorted(stale)


def _assess_data_quality(
    context: FarmContext, conflicts: List[str],
) -> DataQuality:
    """Deterministic data-quality assessment (documented methodology)."""
    available = _available_source_names(context)
    missing = sorted({"weather", "market", "crop_calendar"} - set(available))
    unavailable_ml = _unavailable_ml_models(context)
    stale = _stale_sources(context)

    available_ml = len(context.ml_predictions) - len(unavailable_ml)
    present = len(available) + max(0, available_ml)
    completeness = round(
        min(100.0, (present / EXPECTED_SOURCE_COUNT) * 100.0), 1,
    ) if present > 0 else 0.0

    if conflicts:
        status = DecisionStatus.conflicting_signals.value
    elif not available and not any(
        p.status == "available" for p in context.ml_predictions
    ):
        status = DecisionStatus.insufficient_context.value
    elif not missing and not unavailable_ml:
        status = DecisionStatus.complete_context.value
    else:
        status = DecisionStatus.partial_context.value

    return DataQuality(
        status=status,
        completeness_percent=completeness,
        missing_sources=missing,
        stale_sources=stale,
        conflicts=list(conflicts),
        unavailable_ml_models=unavailable_ml,
        missing_critical_fields=[],
    )


def _decision_confidence(
    independent_sources: List[str],
    ml_model: Optional[MLPrediction],
) -> tuple:
    """
    Decision confidence (methodology documented in the module docstring).

    Returns (confidence: float|None, rationale: str|None). None when
    fewer than two independent sources contribute - never invented.
    """
    unique_sources = sorted(set(independent_sources))
    if len(unique_sources) < 2:
        return None, None
    confidence = 0.5 + 0.1 * (len(unique_sources) - 2)
    ml_note = ""
    if ml_model is not None and _model_probability(ml_model) is not None:
        confidence += 0.1
        ml_note = (
            f" plus model-reported probability from {ml_model.model_name}"
        )
    confidence = min(0.9, round(confidence, 2))
    rationale = (
        f"{len(unique_sources)} independent sources agree "
        f"({', '.join(unique_sources)}){ml_note}"
    )
    return confidence, rationale


# =============================================================================
# Rule helpers
# =============================================================================


def _sig(name: str, source: str, detail: Optional[str] = None,
         value: Any = None) -> SupportingSignal:
    return SupportingSignal(
        signal=name, source=source, description=detail, value=value,
    )


def _src(source: str, source_type: str,
         detail: Optional[str] = None) -> ContributingSource:
    return ContributingSource(
        source=source, source_type=source_type, detail=detail,
    )


def _weather_signal_refs(
    signals: Dict[str, Any], names: List[str],
) -> List[SupportingSignal]:
    """Build SupportingSignal entries from active weather signals."""
    refs: List[SupportingSignal] = []
    for name in names:
        info = signals.get(name)
        if info and info["active"]:
            refs.append(_sig(name, "weather", info["detail"], info["value"]))
    return refs


def _weather_source() -> ContributingSource:
    return _src(
        "weather", "external_data",
        "Weather Intelligence forecast signals",
    )


def _ml_signal_name(model_name: str, kind: str) -> str:
    """
    Deterministic machine-readable signal name for an ML-derived signal,
    e.g. ("smart_irrigation", "soil_moisture") ->
    "smart_irrigation_high_soil_moisture" style names are built by the
    rules; this builds the base "<model>_<kind>" form.
    """
    return f"{model_name}_{kind}"


def _dec(
    context: FarmContext,
    decision_type: DecisionType,
    priority: Priority,
    title: str,
    summary: str,
    reason: str,
    stage: Optional[str],
    sources: List[ContributingSource],
    signals: List[SupportingSignal],
    confidence: Optional[float] = None,
    confidence_rationale: Optional[str] = None,
    severity: Optional[str] = None,
    warnings: Optional[List[DecisionWarning]] = None,
) -> Decision:
    """
    Deterministic Decision constructor (single creation point).

    Per-decision status starts as the context's base status computed
    without conflicts; evaluate_farm_context assigns the final overall
    status (including conflicting_signals) to every decision afterwards.
    """
    return Decision(
        id=_decision_id(context, decision_type.value),
        decision_type=decision_type,
        status=DecisionStatus(_context_status(context, [])),
        priority=priority,
        severity=severity,
        title=title,
        summary=summary,
        reason=reason,
        crop=context.crop,
        growth_stage=stage,
        location=context.location,
        confidence=confidence,
        confidence_rationale=confidence_rationale,
        contributing_sources=sources,
        supporting_signals=signals,
        warnings=warnings or [],
        created_at=_utc_now_iso(),
    )


# =============================================================================
# Case 1 - Weather + Irrigation interaction
# =============================================================================


def _rule_weather_irrigation(
    context: FarmContext, signals: Dict[str, Any], stage: Optional[str],
) -> Optional[Decision]:
    """
    Weather + irrigation interaction.

    - Rainfall expected AND irrigation model indicates sufficient/high
      soil moisture -> advisory to review planned irrigation.
    - Rainfall expected AND irrigation model indicates HIGH irrigation
      need -> conflicting_signals decision (never silently resolved).

    Does NOT claim exact irrigation quantities: quantities are only
    echoed when the irrigation model itself provides them (in metadata).
    """
    irrigation = _get_ml(context, "smart_irrigation")
    if irrigation is None:
        return None

    rain_active = any(
        signals.get(name, {}).get("active")
        for name in (
            "high_precipitation_probability",
            "notable_rainfall_expected",
            "heavy_rainfall_expected",
        )
    )
    if not rain_active:
        return None

    metadata = irrigation.metadata or {}
    moisture_level = _normalize(
        str(metadata.get("soil_moisture_level", "") or "")
    )
    irrigation_required = metadata.get("irrigation_required")
    probability = _model_probability(irrigation)

    high_need = (
        irrigation_required is True
        or moisture_level in {"low", "very low", "dry"}
    )
    sufficient_moisture = (
        irrigation_required is False
        or moisture_level in {"high", "sufficient", "adequate", "good"}
    )

    rain_refs = _weather_signal_refs(signals, [
        "high_precipitation_probability",
        "notable_rainfall_expected",
        "heavy_rainfall_expected",
    ])
    irrigation_signal = _ml_signal_name(
        "smart_irrigation", "soil_moisture",
    )
    ml_ref = _sig(
        irrigation_signal, "smart_irrigation",
        (
            f"Irrigation model prediction: {irrigation.prediction}"
            if irrigation.prediction
            else "Irrigation model prediction available"
        ),
        probability,
    )
    wx_source = _weather_source()
    ml_source = _src(
        "smart_irrigation", "ml_model",
        "Smart Irrigation ML prediction (friend's ML layer)",
    )

    if high_need:
        # CONFLICTING SIGNALS - surfaced explicitly, never resolved silently.
        reason = (
            "Weather forecast indicates significant rainfall while the "
            "smart irrigation prediction indicates elevated irrigation "
            "need. The two sources disagree for the same window."
        )
        return _dec(
            context, DecisionType.conflicting_signals, Priority.HIGH,
            "Conflicting Signals: Rainfall Expected vs High Irrigation Need",
            "Weather and the irrigation model disagree; both are reported "
            "for review instead of silently choosing one.",
            reason,
            stage,
            [wx_source, ml_source],
            rain_refs + [ml_ref],
            confidence=None,
            confidence_rationale=(
                "Sources conflict; decision confidence not calculated"
            ),
        )

    if sufficient_moisture:
        reason = (
            "Weather forecast signals rainfall "
            f"({', '.join(n for n in _active_signal_names(signals) if 'rain' in n) or 'expected precipitation'}) "
            "and the smart irrigation prediction indicates sufficient soil "
            "moisture. Review planned irrigation because upcoming rainfall "
            "and predicted soil moisture indicate reduced immediate "
            "irrigation need. Quantities are not stated because the "
            "irrigation model does not provide them in this context."
        )
        confidence, rationale = _decision_confidence(
            ["weather", "smart_irrigation"], irrigation,
        )
        return _dec(
            context, DecisionType.weather_irrigation_interaction,
            Priority.MEDIUM,
            "Review Planned Irrigation Due to Expected Rainfall",
            "Upcoming rainfall plus predicted sufficient soil moisture "
            "suggest reviewing the irrigation plan.",
            reason,
            stage,
            [wx_source, ml_source],
            rain_refs + [ml_ref],
            confidence=confidence,
            confidence_rationale=rationale,
        )
    return None


# =============================================================================
# Case 2 - Weather + Crop Stage interaction
# =============================================================================


def _rule_weather_stage(
    context: FarmContext, signals: Dict[str, Any], stage: Optional[str],
) -> Optional[Decision]:
    """
    Weather + crop stage interaction.

    Adverse weather during a sensitive/important growth stage elevates
    the condition. Priority ladder (documented):
    - CRITICAL: severe weather indicator active in a sensitive stage
    - HIGH:     other adverse weather (heavy rain/extreme heat/frost/
                strong wind) in a sensitive stage
    - MEDIUM:   adverse weather without stage information
    Requires BOTH weather adverse signals AND a stage; weather alone does
    not produce this decision (the weather module already reports it).
    """
    adverse = _adverse_signals(signals)
    if not adverse or not stage:
        return None

    sensitive = _stage_is_sensitive(stage)
    severe = bool(
        signals.get("severe_weather_indicator", {}).get("active")
    )
    if severe and sensitive:
        priority = Priority.CRITICAL
    elif sensitive:
        priority = Priority.HIGH
    else:
        priority = Priority.MEDIUM

    refs = _weather_signal_refs(signals, adverse)
    refs.append(_sig(
        "growth_stage", "crop_calendar",
        f"Current growth stage: {stage}",
        stage,
    ))
    sources = [
        _weather_source(),
        _src(
            "crop_calendar", "external_data",
            "Crop Calendar growth-stage context",
        ),
    ]
    stage_note = (
        "a sensitive growth stage"
        if sensitive
        else f"the {stage} stage"
    )
    reason = (
        f"Adverse weather is expected ({', '.join(adverse)}) while the "
        f"crop is in {stage_note}. The crop calendar identifies this "
        "stage as weather-sensitive, so the combination elevates the "
        "condition. Sources: weather forecast + crop calendar stage."
        if sensitive
        else
        f"Adverse weather is expected ({', '.join(adverse)}) while the "
        f"crop is in the {stage} stage. The calendar did not flag this "
        "stage as especially sensitive, so this is an elevated advisory, "
        "not a critical alert. Sources: weather forecast + crop calendar "
        "stage."
    )
    return _dec(
        context, DecisionType.weather_crop_stage_interaction, priority,
        "Adverse Weather During Sensitive Growth Stage"
        if sensitive
        else "Adverse Weather During Current Growth Stage",
        "Adverse weather coincides with the current crop stage; review "
        "protective measures.",
        reason,
        stage,
        sources,
        refs,
        severity="severe" if (severe and sensitive) else
        ("moderate" if sensitive else "elevated"),
    )


# =============================================================================
# Case 3 - Disease + Weather
# =============================================================================


def _rule_disease_weather(
    context: FarmContext, signals: Dict[str, Any], stage: Optional[str],
) -> Optional[Decision]:
    """
    Disease + weather interaction.

    The Disease Detection ML model remains the ONLY source of disease
    diagnosis. The engine only contextualizes an elevated model-reported
    probability with disease-relevant weather (high humidity / rain) and
    never diagnoses independently.
    """
    disease = _get_ml(context, "disease_detection")
    if disease is None:
        return None
    probability = _model_probability(disease)
    if probability is None or probability < ML_PROBABILITY_THRESHOLD:
        return None

    favourable = [
        name for name in ("high_humidity",
                          "high_precipitation_probability",
                          "notable_rainfall_expected",
                          "heavy_rainfall_expected")
        if signals.get(name, {}).get("active")
    ]

    ml_ref = _sig(
        _ml_signal_name("disease_detection", "elevated_probability"),
        "disease_detection",
        (
            f"Disease model reports elevated probability "
            f"({probability:.2f})"
            + (f" for {disease.prediction}" if disease.prediction else "")
        ),
        probability,
    )
    ml_source = _src(
        "disease_detection", "ml_model",
        "Disease Detection ML prediction (diagnosis source; friend's "
        "ML layer)",
    )

    if favourable:
        refs = [ml_ref] + _weather_signal_refs(signals, favourable)
        sources = [ml_source, _weather_source()]
        reason = (
            f"The disease detection model reports elevated probability "
            f"({probability:.2f})"
            + (f" for {disease.prediction}" if disease.prediction else "")
            + " and current weather conditions ("
            + ", ".join(favourable)
            + ") are favourable for disease development. The ML model "
              "remains the source of the diagnosis; the engine only "
              "combines it with weather context."
        )
        priority = Priority.HIGH if probability >= 0.8 else Priority.MEDIUM
        confidence, rationale = _decision_confidence(
            ["disease_detection", "weather"], disease,
        )
        return _dec(
            context, DecisionType.disease_weather_risk, priority,
            "Elevated Disease Risk Under Current Weather Conditions",
            "Model-reported disease probability combined with weather "
            "favourable for disease development.",
            reason,
            stage,
            sources,
            refs,
            confidence=confidence,
            confidence_rationale=rationale,
        )

    # Elevated disease probability without weather amplifiers.
    reason = (
        f"The disease detection model reports elevated probability "
        f"({probability:.2f})"
        + (f" for {disease.prediction}" if disease.prediction else "")
        + ". Weather conditions are not identified as especially "
          "favourable for disease development, but the model signal "
          "warrants monitoring. The ML model remains the source of the "
          "diagnosis."
    )
    return _dec(
        context, DecisionType.disease_weather_risk, Priority.HIGH,
        "Elevated Disease Probability Reported by Model",
        "Disease model probability is elevated; monitor the crop.",
        reason,
        stage,
        [ml_source],
        [ml_ref],
        confidence=None,
        confidence_rationale=(
            "Single ML source; decision confidence not calculated"
        ),
    )


# =============================================================================
# Case 4 - Pest + Crop Stage
# =============================================================================


def _rule_pest_stage(
    context: FarmContext, signals: Dict[str, Any], stage: Optional[str],
) -> Optional[Decision]:
    """
    Pest + crop stage interaction.

    The Pest Prediction ML model remains the only source of pest
    probability; the calendar provides stage relevance. The engine never
    predicts pests itself.
    """
    pest = _get_ml(context, "pest_prediction")
    if pest is None or not stage:
        return None
    probability = _model_probability(pest)
    if probability is None or probability < ML_PROBABILITY_THRESHOLD:
        return None

    ml_ref = _sig(
        _ml_signal_name("pest_prediction", "elevated_probability"),
        "pest_prediction",
        (
            f"Pest model reports elevated probability ({probability:.2f})"
            + (f" for {pest.prediction}" if pest.prediction else "")
        ),
        probability,
    )
    stage_ref = _sig(
        "growth_stage", "crop_calendar",
        f"Current growth stage: {stage}", stage,
    )
    sensitive = _stage_is_sensitive(stage)
    priority = Priority.HIGH if sensitive else Priority.MEDIUM
    reason = (
        f"The pest prediction model reports elevated probability "
        f"({probability:.2f})"
        + (f" for {pest.prediction}" if pest.prediction else "")
        + f" while the crop is in the {stage} stage"
        + (
            " (a sensitive stage for pest pressure)."
            if sensitive
            else "."
        )
        + " The ML model remains the source of the pest prediction."
    )
    confidence, rationale = _decision_confidence(
        ["pest_prediction", "crop_calendar"], pest,
    )
    return _dec(
        context, DecisionType.pest_crop_stage_risk, priority,
        "Elevated Pest Risk at Current Growth Stage",
        "Model-reported pest probability combined with crop stage "
        "context.",
        reason,
        stage,
        [
            _src(
                "pest_prediction", "ml_model",
                "Pest Prediction ML (prediction source; friend's ML layer)",
            ),
            _src(
                "crop_calendar", "external_data",
                "Crop Calendar growth-stage context",
            ),
        ],
        [ml_ref, stage_ref],
        confidence=confidence,
        confidence_rationale=rationale,
    )


# =============================================================================
# Case 5 - Market + Crop
# =============================================================================


def _rule_market_crop(
    context: FarmContext, signals: Dict[str, Any], stage: Optional[str],
) -> Optional[Decision]:
    """
    Market + crop context.

    Produces a market context decision when the Market Forecast reports a
    meaningful trend for a commodity corresponding to the farmer's crop.
    Does NOT advise buying/selling - that policy belongs to a later module.
    """
    market = context.market_context
    if not market or not market.is_market_data_available:
        return None
    if not context.crop:
        return None

    # Commodity must correspond to the crop (normalized substring match
    # handles forms like "Paddy (Common)" vs "paddy").
    crop_norm = _normalize(context.crop)
    commodity_norm = _normalize(market.commodity or "")
    if not crop_norm or not commodity_norm:
        return None
    crop_words = crop_norm.split()
    if not any(word in commodity_norm for word in crop_words):
        return None

    trend = market.forecast_trend or market.recent_trend
    change = (
        market.forecast_change_percent
        if market.forecast_change_percent is not None
        else market.recent_change_percent
    )
    meaningful = (
        trend in ("increasing", "decreasing")
        and change is not None
        and abs(change) >= MARKET_CHANGE_PERCENT_THRESHOLD
    )
    if not meaningful:
        return None

    direction = "rising" if trend == "increasing" else "falling"
    trend_signal = (
        f"market_forecast_{trend}"
        if market.forecast_trend == trend
        else f"market_recent_{trend}"
    )
    strength = (
        market.signal_strength
        if market.signal_strength is not None
        else "n/a"
    )
    refs = [
        _sig(
            trend_signal, "market",
            f"Market trend for {market.commodity}: {trend} "
            f"({change:+.1f}%); signal strength {strength}",
            change,
        ),
        _sig(
            "crop_market_match", "crop_calendar",
            f"Commodity {market.commodity} corresponds to crop "
            f"{context.crop}",
            context.crop,
        ),
    ]
    sources = [
        _src("market", "external_data", "Market Forecast trend signals"),
        _src(
            "crop_calendar", "external_data",
            "Crop identification for market matching",
        ),
    ]
    reason = (
        f"The Market Forecast reports a {direction} price trend for "
        f"{market.commodity} ({change:+.1f}% expected change), which "
        f"corresponds to the farmer's crop ({context.crop}). This is "
        "market context only: the engine does not advise buying or "
        "selling - pricing policy belongs to a later module."
    )
    return _dec(
        context, DecisionType.market_crop_context, Priority.MEDIUM,
        f"Market Trend Context for {context.crop}",
        f"Prices for {market.commodity} are {direction}; recorded as "
        "market context.",
        reason,
        stage,
        sources,
        refs,
    )


# =============================================================================
# Case 6 - Fertilizer contextualization
# =============================================================================


def _rule_fertilizer(
    context: FarmContext, signals: Dict[str, Any], stage: Optional[str],
) -> Optional[Decision]:
    """
    Fertilizer contextualization.

    The Fertilizer Recommendation ML output is passed through with
    crop/stage/weather/soil context attached. The engine does NOT replace
    or recompute the recommendation.
    """
    fertilizer = _get_ml(context, "fertilizer_recommendation")
    if fertilizer is None:
        return None

    refs = [
        _sig(
            _ml_signal_name("fertilizer_recommendation", "recommendation"),
            "fertilizer_recommendation",
            (
                f"Fertilizer model recommendation: {fertilizer.prediction}"
                if fertilizer.prediction
                else "Fertilizer model recommendation available"
            ),
            _model_probability(fertilizer),
        ),
    ]
    sources = [
        _src(
            "fertilizer_recommendation", "ml_model",
            "Fertilizer Recommendation ML (recommendation source; "
            "friend's ML layer)",
        ),
    ]
    if context.crop:
        refs.append(_sig(
            "crop", "crop_calendar", f"Crop: {context.crop}", context.crop,
        ))
    if stage:
        refs.append(_sig(
            "growth_stage", "crop_calendar",
            f"Current growth stage: {stage}", stage,
        ))
    adverse = _adverse_signals(signals)
    if adverse:
        refs += _weather_signal_refs(signals, adverse)
        sources.append(_weather_source())
    soil = _get_ml(context, "soil_analysis")
    if soil is not None:
        refs.append(_sig(
            _ml_signal_name("soil_analysis", "prediction"),
            "soil_analysis",
            (
                f"Soil analysis context: {soil.prediction}"
                if soil.prediction
                else "Soil analysis context available"
            ),
            _model_probability(soil),
        ))
        sources.append(_src(
            "soil_analysis", "ml_model",
            "Soil Analysis ML (context only; friend's ML layer)",
        ))

    context_parts = [
        context.crop or "crop not specified",
        f"growth stage {stage}" if stage else "growth stage not provided",
        "adverse weather expected" if adverse
        else "no adverse weather expected",
    ]
    rain_note = (
        " Heavy rainfall may affect fertilizer effectiveness; review "
        "application timing with the recommendation in mind."
        if "heavy_rainfall_expected" in adverse
        else ""
    )
    reason = (
        f"The fertilizer recommendation model suggests: "
        f"{fertilizer.prediction or 'a recommendation (see model output)'}."
        f" Contextual factors: {'; '.join(context_parts)}.{rain_note}"
        " The recommendation itself comes from the ML model; the engine "
        "only adds context."
    )
    return _dec(
        context, DecisionType.fertilizer_contextualization, Priority.MEDIUM,
        "Fertilizer Recommendation in Crop Context",
        "Model fertilizer recommendation contextualized with crop, "
        "stage, and weather information.",
        reason,
        stage,
        sources,
        refs,
    )


# =============================================================================
# Case 7 - Yield + Market
# =============================================================================


def _rule_yield_market(
    context: FarmContext, signals: Dict[str, Any], stage: Optional[str],
) -> Optional[Decision]:
    """
    Yield + market relationship identification.

    When a yield prediction and market context both exist, identifies
    their relationship for downstream decision-making. Performs NO
    economic calculations (insufficient inputs; out of scope).
    """
    yield_pred = _get_ml(context, "crop_yield_prediction")
    market = context.market_context
    if yield_pred is None or not market or not market.is_market_data_available:
        return None

    unit = f" {yield_pred.unit}" if yield_pred.unit else ""
    refs = [
        _sig(
            _ml_signal_name("crop_yield_prediction", "prediction"),
            "crop_yield_prediction",
            (
                f"Yield model prediction: {yield_pred.prediction}{unit}"
                if yield_pred.prediction
                else "Yield model prediction available"
            ),
            _model_probability(yield_pred),
        ),
    ]
    sources = [
        _src(
            "crop_yield_prediction", "ml_model",
            "Crop Yield Prediction ML (friend's ML layer)",
        ),
        _src("market", "external_data", "Market Forecast price context"),
    ]
    if market.current_price is not None:
        refs.append(_sig(
            "market_price_available", "market",
            f"Current market price: {market.current_price}",
            market.current_price,
        ))

    trend = market.forecast_trend or market.recent_trend
    trend_note = (
        f" Market trend is {trend}."
        if trend in ("increasing", "decreasing", "stable")
        else ""
    )
    reason = (
        "A yield prediction and market context are both available; the "
        "engine records their relationship for downstream decision-making "
        f"(yield: {yield_pred.prediction or 'available'}{unit}; "
        f"commodity: {market.commodity or 'n/a'}.{trend_note}) No "
        "economic calculations are performed because not all required "
        "inputs are provided by existing modules."
    )
    return _dec(
        context, DecisionType.yield_market_context, Priority.MEDIUM,
        "Yield and Market Context Available",
        "Yield prediction and market context recorded together for "
        "downstream analysis.",
        reason,
        stage,
        sources,
        refs,
    )


# =============================================================================
# Engine entry point
# =============================================================================


def evaluate_farm_context(context: FarmContext) -> "DecisionResponse":
    """
    Deterministic evaluation of a FarmContext.

    Order of operations:
    1. Extract weather signals (empty when weather is unavailable).
    2. Resolve the effective growth stage (calendar first, farmer fallback).
    3. Run the deterministic rules; collect decisions and conflicts.
    4. Assess data quality (completeness, staleness, unavailable models).
    5. Sort decisions by documented priority order, then type (stable).
    """
    from app.schemas.decision import DecisionResponse

    signals = _weather_signals(context)
    stage = _effective_growth_stage(context)

    decisions: List[Decision] = []
    rules = [
        _rule_weather_irrigation,
        _rule_weather_stage,
        _rule_disease_weather,
        _rule_pest_stage,
        _rule_market_crop,
        _rule_fertilizer,
        _rule_yield_market,
    ]
    for rule in rules:
        decision = rule(context, signals, stage)
        if decision is not None:
            decisions.append(decision)

    conflicts = [
        d.reason for d in decisions
        if d.decision_type == DecisionType.conflicting_signals
    ]

    status = _context_status(context, conflicts)
    data_quality = _assess_data_quality(context, conflicts)

    # Final context status (incl. conflicts) is assigned to every
    # decision so each decision is self-contained and traceable.
    final_status = DecisionStatus(status)
    for decision in decisions:
        decision.status = final_status

    priority_order = {
        Priority.CRITICAL: 0,
        Priority.HIGH: 1,
        Priority.MEDIUM: 2,
        Priority.LOW: 3,
    }
    decisions.sort(
        key=lambda d: (priority_order[d.priority], d.decision_type.value)
    )

    warnings: List[DecisionWarning] = []
    for missing in data_quality.missing_sources:
        warnings.append(DecisionWarning(
            warning=(
                f"{missing} data was unavailable; {missing} context was "
                "not evaluated (no values were substituted)"
            ),
            source=missing,
        ))
    for model in data_quality.unavailable_ml_models:
        warnings.append(DecisionWarning(
            warning=(
                f"ML model '{model}' reported status unavailable/error; "
                "its signal was not fabricated"
            ),
            source=model,
        ))

    return DecisionResponse(
        status=status,
        data_quality=data_quality,
        decisions=decisions,
        warnings=warnings,
        engine_version=ENGINE_VERSION,
        ruleset_version=RULESET_VERSION,
        evaluation_timestamp=_utc_now_iso(),
        total_decisions=len(decisions),
    )
