"""
Risk & Opportunity Analysis - Deterministic Decision Intelligence.

This layer sits AFTER the Context/Decision Engine and BEFORE the future
Smart Alerts, Personalized Action Plan and AI Farming Assistant layers.
It consumes the project's existing normalized contracts (``FarmContext``,
the Decision Engine response and the standardized ML prediction
contracts) and classifies the available signals as RISKS and
OPPORTUNITIES with traceable evidence.

DESIGN PRINCIPLES
-----------------
- Deterministic: the same input always produces the same output (only
  timestamps/IDs are timing-dependent, and IDs are derived from stable
  context attributes).
- Explainable: every risk/opportunity carries ``reasoning``, ``evidence``
  with per-signal source attribution and ``contributing_sources``.
- NOT an ML model: this module never trains, replaces or reimplements any
  of the project's 7 ML models, and never fabricates weather, market,
  crop-stage, prediction or confidence values. Missing or unavailable
  inputs are REPORTED (data-quality notices), never filled in.
- Correlating, not alerting: related signals describing the SAME
  underlying condition are consolidated into ONE item (duplicate
  suppression). Turning items into notifications is the job of the later
  Smart Alerts layer.

SEVERITY RULES (documented, deterministic - NOT calibrated probabilities)
------------------------------------------------------------------------
Inputs:
- ``n``        = number of independent CORROBORATING sources (weather,
                 market and ML models; the crop calendar supplies context,
                 not corroboration)
- ``elevated`` = a strong single signal is present (heavy rainfall,
                 extreme heat, frost, strong wind, severe-weather
                 indicator, model probability >= 0.6, market move >= 3%)
- ``sensitive``= the crop is in a sensitive growth stage
- ``ts``       = the condition is time-sensitive
- ``severe``   = the weather module reported a severe-weather indicator
- ``upstream`` = priority reported by the Decision Engine for the same
                 condition (attribution, never recomputed)

1. CRITICAL: ``n >= 2`` and ``upstream == critical`` (attributed)
2. CRITICAL: a severe-weather indicator is active in a sensitive stage
             (mirrors the Decision Engine's documented CRITICAL rule)
3. CRITICAL: ``n >= 3`` and (``sensitive`` or ``ts``)
4. CRITICAL: ``n >= 2`` and ``elevated`` and ``ts``
5. HIGH:     ``n >= 2`` and (``elevated`` or ``sensitive`` or ``ts``)
6. HIGH:     ``n == 1`` and ``elevated`` and ``sensitive``
7. MEDIUM:   ``n >= 2``
8. MEDIUM:   ``elevated``
9. LOW:      otherwise (single, low-impact signal)

PRIORITY RULES (documented)
---------------------------
- CRITICAL: severity CRITICAL (severe AND time-sensitive multi-source)
- HIGH:     severity HIGH and (time-sensitive or sensitive stage)
- MEDIUM:   severity HIGH, or severity MEDIUM with an actionable follow-up
- LOW:      everything else

Opportunities use their own ladder:
- HIGH:   ``n >= 2`` and bound to a specific time window
- MEDIUM: ``n >= 2``, or bound to a specific time window
- LOW:    otherwise

CONFIDENCE RULES (never fabricated)
-----------------------------------
1. A numeric confidence already produced upstream is REUSED verbatim with
   attribution: first the Decision Engine decision confidence for the same
   condition, then the ML model's own reported confidence/probability when
   the model is this item's only corroborating source.
2. Otherwise, when ``n >= 2`` independent sources agree, the documented
   deterministic method (identical to the Decision Engine's) is applied:
   ``0.5 + 0.1`` per source beyond the second, ``+0.1`` when an ML model
   reported a probability, capped at ``0.9``.
3. Otherwise ``confidence = insufficient_evidence`` and
   ``numerical_confidence`` is ``null``.
Mapping a number to a category (documented constants): ``>= 0.75`` high,
``>= 0.50`` medium, else low. A stale contributing source downgrades the
category by one step and marks the item ``monitoring``.

STALE DATA
----------
Staleness uses the decision engine's existing threshold
(``STALENESS_DAYS_THRESHOLD``) applied to caller-provided ``data_freshness``
timestamps only. Sources without a timestamp are never marked stale.

CONFLICTS
---------
Conflicting signals are surfaced explicitly (``ConflictNotice``) and are
never silently resolved. When the Decision Engine already reported the
same conflict, the notice is attributed to it (``detected_by=
"decision_engine"``) instead of being duplicated.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Documented thresholds/constants REUSED from the Decision Engine so both
# layers can never diverge on the same upstream signals.
from app.intelligence.decision_engine import (
    CROP_SYNONYM_GROUPS,
    EXPECTED_SOURCE_COUNT,
    EXTREME_HEAT_C_THRESHOLD,
    FROST_C_THRESHOLD,
    HEAVY_RAINFALL_MM_THRESHOLD,
    HIGH_HUMIDITY_PERCENT,
    KNOWN_ML_MODELS,
    MARKET_CHANGE_PERCENT_THRESHOLD,
    ML_PROBABILITY_THRESHOLD,
    PRECIPITATION_MM_THRESHOLD,
    PRECIP_PROBABILITY_THRESHOLD,
    SENSITIVE_STAGES,
    STALENESS_DAYS_THRESHOLD,
    STRONG_WIND_KMH_THRESHOLD,
)
from app.schemas.decision import (
    DataQuality,
    Decision,
    DecisionStatus,
    DecisionType,
    FarmContext,
    MLPrediction,
    SupportingSignal,
)
from app.schemas.risk_opportunity import (
    ConfidenceLevel,
    ConfidenceSource,
    ConflictNotice,
    ConflictType,
    ContributingSource,
    DataQualityIssueType,
    DataQualityNotice,
    ItemStatus,
    Opportunity,
    OpportunityCategory,
    PriorityLevel,
    Risk,
    RiskCategory,
    RiskOpportunityContext,
    RiskOpportunityResponse,
    RiskOpportunitySummary,
    SeverityLevel,
    SourceType,
)

# Engine / ruleset versions (bumped when the risk rules change).
ENGINE_VERSION = "1.0.0"
RULESET_VERSION = "1.0.0"

# =============================================================================
# Documented constants
# =============================================================================

# Thresholds that have no upstream equivalent (documented defaults, easily
# adjusted). Everything that already exists upstream is imported above.

# Dry-window detection (water-stress rules).
LOW_PRECIP_PROBABILITY_THRESHOLD = 25.0   # percent
LOW_RAINFALL_MM_THRESHOLD = 5.0           # mm over the forecast horizon

# Explicitly-benign forecast ranges used by the "favourable window"
# opportunity rule. A window is only called favourable when the forecast
# actually reported values inside these ranges.
FAVOURABLE_TEMP_MIN_C = 5.0               # deg C (min forecast)
FAVOURABLE_TEMP_MAX_C = 35.0              # deg C (max forecast)

# Crop-calendar-derived urgency windows.
STAGE_TRANSITION_IMMINENT_DAYS = 7
HARVEST_WINDOW_IMMINENT_DAYS = 14

# Crop/commodity matching (mirrors the decision engine's documented matcher).
MIN_MATCH_WORD_LENGTH = 3

# Documented deterministic confidence method (identical to the Decision
# Engine's, so both layers report the same semantics).
CONFIDENCE_BASE = 0.5
CONFIDENCE_SOURCE_STEP = 0.1
CONFIDENCE_ML_BONUS = 0.1
CONFIDENCE_MAX = 0.9
CONFIDENCE_HIGH_MIN = 0.75
CONFIDENCE_MEDIUM_MIN = 0.50

# Sources that can CORROBORATE a condition (the crop calendar and the
# Decision Engine supply context/attribution, not corroboration).
CORROBORATING_SOURCES = ("weather", "market") + tuple(KNOWN_ML_MODELS)

# Normalized phrase vocabularies used to read the ML models' OWN reported
# outcome vocabulary. They never invent a status: a rule that depends on
# one of these only fires when the model itself reported a matching value.
WATER_STRESS_PHRASES = frozenset({
    "low", "very low", "dry", "deficit", "deficient", "below normal",
    "critical", "wilting", "irrigation recommended", "irrigation needed",
    "recommended", "required", "needed",
})
ADEQUATE_MOISTURE_PHRASES = frozenset({
    "sufficient", "adequate", "high", "optimal", "good", "field capacity",
    "no irrigation needed", "not required",
})
PEST_ADVERSE_PHRASES = frozenset({
    "high", "very high", "severe", "elevated", "outbreak",
})
PEST_FAVOURABLE_PHRASES = frozenset({
    "low", "very low", "minimal", "negligible",
})
YIELD_ADVERSE_PHRASES = frozenset({
    "below normal", "below average", "poor", "deficit", "reduced",
    "adverse", "declining",
})
YIELD_FAVOURABLE_PHRASES = frozenset({
    "above normal", "above average", "surplus", "increased", "bumper",
    "favourable", "favorable",
})
SOIL_ADVERSE_PHRASES = frozenset({
    "degraded", "poor", "depleted", "deficient", "organic carbon deficit",
})
SOIL_FAVOURABLE_PHRASES = frozenset({
    "healthy", "adequate", "optimal", "sufficient", "organic carbon adequate",
})

# Consolidation keys. Signals that share a key describe the SAME underlying
# condition and are merged into a single risk/opportunity with combined
# evidence (duplicate suppression).
KEY_EXCESS_RAINFALL = "excess_rainfall"
KEY_HEAT_STRESS = "heat_stress"
KEY_COLD_STRESS = "cold_stress"
KEY_WIND_DAMAGE = "wind_damage"
KEY_SEVERE_WEATHER = "severe_weather"
KEY_WATER_STRESS = "water_stress"
KEY_DISEASE_PRESSURE = "disease_pressure"
KEY_PEST_PRESSURE = "pest_pressure"
KEY_SOIL_CONDITION = "soil_condition"
KEY_FERTILIZER_APPLICATION = "fertilizer_application"
KEY_MARKET_DOWNSIDE = "market_price_downside"
KEY_MARKET_UPSIDE = "market_price_upside"
KEY_YIELD_MARKET = "yield_market_relationship"
KEY_STAGE_TRANSITION = "stage_transition"
KEY_HARVEST_WINDOW = "harvest_window"
KEY_IRRIGATION_EFFICIENCY = "irrigation_efficiency"
KEY_FAVOURABLE_WINDOW = "favourable_weather_window"
KEY_CONFLICTING_SIGNALS = "conflicting_signals"

# Ordering used for deterministic sorting of the response.
SEVERITY_ORDER = {
    SeverityLevel.CRITICAL: 0,
    SeverityLevel.HIGH: 1,
    SeverityLevel.MEDIUM: 2,
    SeverityLevel.LOW: 3,
}
PRIORITY_ORDER = {
    PriorityLevel.CRITICAL: 0,
    PriorityLevel.HIGH: 1,
    PriorityLevel.MEDIUM: 2,
    PriorityLevel.LOW: 3,
}
CONFIDENCE_ORDER = {
    ConfidenceLevel.HIGH: 0,
    ConfidenceLevel.MEDIUM: 1,
    ConfidenceLevel.LOW: 2,
    ConfidenceLevel.INSUFFICIENT_EVIDENCE: 3,
}

# Weather-signal groups used by several rules.
RAIN_SIGNALS = (
    "high_precipitation_probability",
    "notable_rainfall_expected",
    "heavy_rainfall_expected",
)
DISEASE_FAVOURABLE_SIGNALS = (
    "high_humidity",
    "high_precipitation_probability",
    "notable_rainfall_expected",
    "heavy_rainfall_expected",
)
ADVERSE_WEATHER_SIGNALS = (
    "heavy_rainfall_expected",
    "notable_rainfall_expected",
    "extreme_heat_expected",
    "frost_risk_expected",
    "strong_wind_expected",
    "severe_weather_indicator",
)

# =============================================================================
# Internal candidate representation
# =============================================================================


@dataclass
class _Candidate:
    """
    Pre-grading representation of ONE contribution to a risk/opportunity.

    Rules emit candidates; candidates sharing a ``key`` are consolidated
    (duplicate suppression) before severity/priority/confidence are graded
    in a single documented place (``_grade_risk`` / ``_grade_opportunity``).
    """
    kind: str                      # "risk" | "opportunity"
    key: str                       # consolidation key
    category: str                  # category enum value
    title: str
    description: str
    reasoning: str
    sources: List[ContributingSource] = field(default_factory=list)
    evidence: List[SupportingSignal] = field(default_factory=list)
    action: Optional[str] = None   # recommended follow-up / suggested action
    stage: Optional[str] = None
    primary: bool = False          # owns the consolidated item when merging
    elevated: bool = False         # strong single signal present
    severe: bool = False           # severe-weather indicator reported
    sensitive: bool = False        # condition sits in a sensitive stage
    time_sensitive: bool = False   # condition requires action within a window
    time_bound: bool = False       # opportunity restricted to a window
    time_window: Optional[str] = None
    valid_until: Optional[str] = None
    ml_probability: Optional[float] = None
    upstream_priority: Optional[str] = None
    upstream_confidence: Optional[float] = None
    upstream_confidence_rationale: Optional[str] = None


# =============================================================================
# Pure helpers (deterministic)
# =============================================================================


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _normalize(name: Optional[str]) -> str:
    """Normalize a name (crop/stage/commodity/model text) for comparisons."""
    if not name:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()


def _item_id(kind: str, key: str, farm: FarmContext) -> str:
    """Deterministic ID from stable context attributes + item kind/key."""
    payload = "|".join([
        kind,
        key,
        _normalize(farm.crop),
        _normalize(farm.location),
        str(farm.sowing_date or ""),
        str(farm.as_of_date or ""),
    ])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"ro-{'risk' if kind == 'risk' else 'opp'}-{digest}"


def _notice_id(issue_type: str, source: str) -> str:
    payload = f"dq|{issue_type}|{source}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"ro-dq-{digest}"


def _conflict_id(conflict_type: str) -> str:
    payload = f"conflict|{conflict_type}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"ro-conflict-{digest}"


def _stage_is_sensitive(stage: Optional[str]) -> bool:
    """Whether the crop calendar's stage vocabulary flags this stage."""
    normalized = _normalize(stage)
    if not normalized:
        return False
    return any(
        normalized == _normalize(s) or _normalize(s) in normalized
        for s in SENSITIVE_STAGES
    )


def _model_probability(pred: Optional[MLPrediction]) -> Optional[float]:
    """Best probability the MODEL itself reported, else None (never invented)."""
    if pred is None:
        return None
    if pred.probability is not None:
        return pred.probability
    if pred.confidence is not None:
        return pred.confidence
    return None


def _hint_phrases(pred: MLPrediction) -> set:
    """
    Normalized phrases taken from a model's OWN reported output
    (``prediction`` plus every string/number in ``metadata``).

    Used only to read the model's reported outcome vocabulary - never to
    infer a value the model did not report.
    """
    parts: List[str] = []
    if pred.prediction:
        parts.append(str(pred.prediction))
    metadata = pred.metadata or {}
    for key in sorted(metadata.keys()):
        value = metadata[key]
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, bool):
            parts.append(str(value))
        elif isinstance(value, (int, float)):
            parts.append(str(value))
        elif isinstance(value, (list, tuple)):
            parts.extend(
                str(v) for v in value if isinstance(v, (str, int, float))
            )
    phrases: set = set()
    for part in parts:
        normalized = _normalize(part)
        if normalized:
            phrases.add(normalized)
            phrases.update(normalized.split())
    return phrases


def _matches(phrases: set, vocabulary) -> bool:
    """Whether any normalized phrase/token match exists."""
    return bool(phrases & set(vocabulary))


def _commodity_matches_crop(crop: Optional[str], commodity: Optional[str]) -> bool:
    """
    Deterministic crop <-> market-commodity matching.

    Reuses the decision engine's documented synonym groups; it performs no
    inference beyond those fixed groups.
    """
    crop_norm = _normalize(crop)
    commodity_norm = _normalize(commodity)
    if not crop_norm or not commodity_norm:
        return False
    crop_words = [
        w for w in crop_norm.split() if len(w) >= MIN_MATCH_WORD_LENGTH
    ]
    if any(word in commodity_norm for word in crop_words):
        return True
    for group in CROP_SYNONYM_GROUPS:
        normalized_group = {_normalize(item) for item in group}
        crop_in_group = crop_norm in normalized_group or any(
            word in normalized_group for word in crop_words
        )
        if crop_in_group and any(
            synonym in commodity_norm for synonym in normalized_group
        ):
            return True
    return False


def _sig(name: str, source: str, detail: Optional[str] = None,
         value: Any = None) -> SupportingSignal:
    """Build a traceable evidence entry."""
    return SupportingSignal(
        signal=name, source=source, description=detail, value=value,
    )


def _src(source: str, source_type: SourceType,
         detail: Optional[str] = None) -> ContributingSource:
    """Build a contributing-source entry."""
    return ContributingSource(
        source=source, source_type=source_type, detail=detail,
    )


def _weather_source() -> ContributingSource:
    return _src(
        "weather", SourceType.EXTERNAL_DATA,
        "Weather Intelligence signals (current/forecast)",
    )


def _ml_source(model_name: str, detail: str) -> ContributingSource:
    return _src(model_name, SourceType.ML_MODEL, detail)


def _calendar_source(detail: str) -> ContributingSource:
    return _src("crop_calendar", SourceType.EXTERNAL_DATA, detail)


def _decision_source(decision: Decision) -> ContributingSource:
    return _src(
        "decision_engine", SourceType.DECISION_ENGINE,
        f"Decision Engine '{decision.title}' "
        f"(priority: {decision.priority.value}, id: {decision.id})",
    )


# =============================================================================
# Context view (read-only; no value is ever invented)
# =============================================================================


def _effective_stage(farm: FarmContext) -> Optional[str]:
    """
    Resolve the growth stage: crop calendar first, farmer fallback.

    The Crop Calendar module is authoritative; the farmer-supplied stage is
    used only when the calendar did not provide one.
    """
    calendar = farm.crop_calendar_context
    if calendar and calendar.current_growth_stage:
        return calendar.current_growth_stage
    return farm.current_growth_stage


def _weather_signals(farm: FarmContext) -> Dict[str, Any]:
    """
    Extract boolean weather signals from the Weather Intelligence context.

    Mirrors the decision engine's documented signal extraction (identical
    thresholds, imported from that module) and adds the two signals this
    layer needs. A signal is inactive when the underlying value is absent -
    missing data never becomes a fabricated value.
    """
    signals: Dict[str, Any] = {}
    weather = farm.weather_context
    if not weather or not weather.is_weather_data_available:
        return signals

    if weather.precipitation_probability is not None:
        probability = weather.precipitation_probability
        signals["high_precipitation_probability"] = {
            "active": probability >= PRECIP_PROBABILITY_THRESHOLD,
            "detail": f"Forecast precipitation probability: {probability}%",
            "value": probability,
        }
        signals["low_precipitation_probability"] = {
            "active": probability <= LOW_PRECIP_PROBABILITY_THRESHOLD,
            "detail": f"Forecast precipitation probability: {probability}%",
            "value": probability,
        }
    if weather.forecast_precipitation_sum is not None:
        total = weather.forecast_precipitation_sum
        heavy = total >= HEAVY_RAINFALL_MM_THRESHOLD
        notable = total >= PRECIPITATION_MM_THRESHOLD
        signals["heavy_rainfall_expected"] = {
            "active": heavy,
            "detail": f"Forecast rainfall total: {total} mm over horizon",
            "value": total,
        }
        signals["notable_rainfall_expected"] = {
            "active": notable and not heavy,
            "detail": f"Forecast rainfall total: {total} mm over horizon",
            "value": total,
        }
        signals["insufficient_rainfall_expected"] = {
            "active": total < LOW_RAINFALL_MM_THRESHOLD,
            "detail": (
                f"Forecast rainfall total: {total} mm over horizon "
                f"(below {LOW_RAINFALL_MM_THRESHOLD} mm)"
            ),
            "value": total,
        }
    if weather.temperature_max_forecast is not None:
        maximum = weather.temperature_max_forecast
        signals["extreme_heat_expected"] = {
            "active": maximum >= EXTREME_HEAT_C_THRESHOLD,
            "detail": f"Forecast maximum temperature: {maximum} deg C",
            "value": maximum,
        }
        signals["favourable_max_temperature"] = {
            "active": maximum < FAVOURABLE_TEMP_MAX_C,
            "detail": f"Forecast maximum temperature: {maximum} deg C",
            "value": maximum,
        }
    if weather.temperature_min_forecast is not None:
        minimum = weather.temperature_min_forecast
        signals["frost_risk_expected"] = {
            "active": minimum <= FROST_C_THRESHOLD,
            "detail": f"Forecast minimum temperature: {minimum} deg C",
            "value": minimum,
        }
        signals["favourable_min_temperature"] = {
            "active": minimum > FAVOURABLE_TEMP_MIN_C,
            "detail": f"Forecast minimum temperature: {minimum} deg C",
            "value": minimum,
        }
    if weather.wind_speed_max_forecast is not None:
        wind = weather.wind_speed_max_forecast
        signals["strong_wind_expected"] = {
            "active": wind >= STRONG_WIND_KMH_THRESHOLD,
            "detail": f"Forecast maximum wind speed: {wind} km/h",
            "value": wind,
        }
        signals["favourable_wind_conditions"] = {
            "active": wind < STRONG_WIND_KMH_THRESHOLD,
            "detail": f"Forecast maximum wind speed: {wind} km/h",
            "value": wind,
        }
    if weather.current_humidity is not None:
        humidity = weather.current_humidity
        signals["high_humidity"] = {
            "active": humidity >= HIGH_HUMIDITY_PERCENT,
            "detail": f"Current humidity: {humidity}%",
            "value": humidity,
        }
    if weather.severe_weather_indicators:
        signals["severe_weather_indicator"] = {
            "active": True,
            "detail": (
                "Severe weather indicators: "
                f"{', '.join(weather.severe_weather_indicators)}"
            ),
            "value": list(weather.severe_weather_indicators),
        }
    return signals


def _active_signal_names(signals: Dict[str, Any]) -> List[str]:
    return sorted(name for name, info in signals.items() if info["active"])


def _active_in(signals: Dict[str, Any], names: Sequence[str]) -> List[str]:
    """Names from ``names`` that are active in the signals map."""
    return [n for n in names if signals.get(n, {}).get("active")]


def _signal_evidence(
    signals: Dict[str, Any], names: Sequence[str], source: str = "weather",
) -> List[SupportingSignal]:
    """Build evidence entries for active signals."""
    evidence: List[SupportingSignal] = []
    for name in names:
        info = signals.get(name)
        if info and info["active"]:
            evidence.append(
                _sig(name, source, info["detail"], info["value"])
            )
    return evidence


def _stale_sources(farm: FarmContext) -> List[str]:
    """
    Deterministic staleness check on caller-provided freshness timestamps.

    Reuses the decision engine's documented threshold. Sources without a
    timestamp are NOT marked stale: freshness is only assessed when a
    timestamp exists.
    """
    stale: List[str] = []
    freshness = farm.data_freshness or {}
    now = datetime.now(timezone.utc)
    for source, timestamp in freshness.items():
        raw = (timestamp or "").strip()
        try:
            parsed = datetime.fromisoformat(raw)
        except (ValueError, TypeError):
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        age_days = (now - parsed).total_seconds() / 86400.0
        if age_days > STALENESS_DAYS_THRESHOLD:
            stale.append(source)
    return sorted(stale)


def _available_source_names(farm: FarmContext) -> List[str]:
    """Names of the data sources present in the context."""
    sources: List[str] = []
    if farm.weather_context and farm.weather_context.is_weather_data_available:
        sources.append("weather")
    if farm.market_context and farm.market_context.is_market_data_available:
        sources.append("market")
    if farm.crop_calendar_context and \
            farm.crop_calendar_context.is_crop_calendar_available:
        sources.append("crop_calendar")
    return sources


def _unavailable_ml_models(farm: FarmContext) -> List[str]:
    """Known ML models explicitly reported as unavailable/errored."""
    unavailable: List[str] = []
    for prediction in farm.ml_predictions:
        if prediction.model_name in KNOWN_ML_MODELS and prediction.status in (
            "unavailable", "error",
        ):
            unavailable.append(prediction.model_name)
    return sorted(set(unavailable))


class _AnalysisView:
    """
    Read-only view over the supplied context.

    Gives rules normalized access to ML predictions, upstream decisions and
    derived signals. Nothing is invented: absent data yields None / empty
    results, and a rule simply does not fire.
    """

    def __init__(
        self,
        context: RiskOpportunityContext,
        signals: Dict[str, Any],
        stage: Optional[str],
    ) -> None:
        self.context = context
        self.farm = context.farm_context
        self.signals = signals
        self.stage = stage
        self.decisions: List[Decision] = (
            list(context.decision_engine_output.decisions)
            if context.decision_engine_output is not None else []
        )
        self.stale_sources = _stale_sources(self.farm)

    # ------------------------------------------------------------------
    # Context accessors
    # ------------------------------------------------------------------

    @property
    def crop(self) -> Optional[str]:
        return self.farm.crop

    @property
    def location(self) -> Optional[str]:
        return self.farm.location

    @property
    def weather(self):
        return self.farm.weather_context

    @property
    def market(self):
        return self.farm.market_context

    @property
    def calendar(self):
        return self.farm.crop_calendar_context

    def reference_date(self) -> date:
        """As-of date when supplied, else the current UTC date."""
        if self.farm.as_of_date:
            return self.farm.as_of_date
        return datetime.now(timezone.utc).date()

    def ml(self, model_name: str) -> Optional[MLPrediction]:
        """
        Return an AVAILABLE prediction for a model, else None.

        Unavailable/errored models are never treated as data and never
        fabricated; they are reported in the data-quality notices.
        """
        for prediction in self.farm.ml_predictions:
            if prediction.model_name == model_name and \
                    prediction.status == "available":
                return prediction
        return None

    def decision(self, *decision_types: DecisionType) -> Optional[Decision]:
        """First upstream decision of one of the given types, else None."""
        wanted = {t.value for t in decision_types}
        for decision in self.decisions:
            if decision.decision_type.value in wanted:
                return decision
        return None

    def active(self, name: str) -> bool:
        return bool(self.signals.get(name, {}).get("active"))

    def any_active(self, names: Sequence[str]) -> bool:
        return any(self.active(name) for name in names)

    def active_in(self, names: Sequence[str]) -> List[str]:
        return _active_in(self.signals, names)

    def stage_sensitive(self) -> bool:
        return _stage_is_sensitive(self.stage)

    def is_stale(self, *sources: str) -> bool:
        """Whether any of the named sources is stale."""
        return any(source in self.stale_sources for source in sources)

    def forecast_valid_until(self) -> Optional[str]:
        """
        End of the available weather forecast horizon (ISO-8601, UTC).

        Derived only from the horizon the weather module reported; None when
        the horizon is unknown.
        """
        if not self.weather or not self.weather.is_weather_data_available:
            return None
        horizon = self.weather.forecast_horizon_days
        if horizon is None:
            return None
        end = datetime.now(timezone.utc) + timedelta(days=int(horizon))
        return end.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    def harvest_imminent(self) -> bool:
        """
        Whether the calendar harvest window is active or starts soon.

        Derived only from the calendar's harvest window dates and the
        as-of date; False when the calendar did not provide a window.
        """
        calendar = self.calendar
        if not calendar or not calendar.is_crop_calendar_available:
            return False
        start = calendar.expected_harvest_window_start
        end = calendar.expected_harvest_window_end
        if start is None and end is None:
            return False
        reference = self.reference_date()
        window_start = start or end
        window_end = end or start
        if window_start and reference < window_start - timedelta(
            days=HARVEST_WINDOW_IMMINENT_DAYS
        ):
            return False
        if window_end and reference > window_end:
            return False
        return True

    def harvest_window_text(self) -> Optional[str]:
        """Harvest window as 'start to end' when the calendar supplied it."""
        calendar = self.calendar
        if not calendar or not calendar.is_crop_calendar_available:
            return None
        start = calendar.expected_harvest_window_start
        end = calendar.expected_harvest_window_end
        if start is None or end is None:
            return None
        return f"{start.isoformat()} to {end.isoformat()}"


# =============================================================================
# Grading (single place where severity/priority/confidence are derived)
# =============================================================================


def _independent_source_count(evidence: Sequence[SupportingSignal]) -> int:
    """
    Number of independent CORROBORATING sources behind an item.

    The crop calendar supplies context (stage) rather than corroboration,
    and the Decision Engine supplies attribution, so neither counts.
    """
    return len({
        e.source for e in evidence if e.source in CORROBORATING_SOURCES
    })


def _severity_for_risk(
    *,
    source_count: int,
    elevated: bool,
    sensitive: bool,
    time_sensitive: bool,
    upstream_priority: Optional[str],
    severe: bool = False,
) -> SeverityLevel:
    """Documented severity ladder (see module docstring)."""
    if source_count >= 2 and upstream_priority == PriorityLevel.CRITICAL.value:
        return SeverityLevel.CRITICAL
    if severe and sensitive:
        return SeverityLevel.CRITICAL
    if source_count >= 3 and (sensitive or time_sensitive):
        return SeverityLevel.CRITICAL
    if source_count >= 2 and elevated and time_sensitive:
        return SeverityLevel.CRITICAL
    if source_count >= 2 and (elevated or sensitive or time_sensitive):
        return SeverityLevel.HIGH
    if source_count == 1 and elevated and sensitive:
        return SeverityLevel.HIGH
    if source_count >= 2:
        return SeverityLevel.MEDIUM
    if elevated:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


def _priority_for_risk(
    severity: SeverityLevel,
    *,
    sensitive: bool,
    time_sensitive: bool,
    actionable: bool,
) -> PriorityLevel:
    """Documented priority ladder (see module docstring)."""
    if severity == SeverityLevel.CRITICAL:
        return PriorityLevel.CRITICAL
    if severity == SeverityLevel.HIGH and (time_sensitive or sensitive):
        return PriorityLevel.HIGH
    if severity == SeverityLevel.HIGH:
        return PriorityLevel.MEDIUM
    if severity == SeverityLevel.MEDIUM and actionable:
        return PriorityLevel.MEDIUM
    return PriorityLevel.LOW


def _priority_for_opportunity(
    *, source_count: int, time_bound: bool,
) -> PriorityLevel:
    """Documented opportunity priority ladder (see module docstring)."""
    if source_count >= 2 and time_bound:
        return PriorityLevel.HIGH
    if source_count >= 2 or time_bound:
        return PriorityLevel.MEDIUM
    return PriorityLevel.LOW


def _level_for_value(value: float) -> ConfidenceLevel:
    """Documented numeric -> category mapping (CONFIDENCE_* constants)."""
    if value >= CONFIDENCE_HIGH_MIN:
        return ConfidenceLevel.HIGH
    if value >= CONFIDENCE_MEDIUM_MIN:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def _downgrade(level: ConfidenceLevel) -> ConfidenceLevel:
    """One-step downgrade applied when a contributing source is stale."""
    order = [
        ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW,
    ]
    if level in order:
        index = order.index(level)
        return order[min(index + 1, len(order) - 1)]
    return level


def _confidence_for(
    *,
    source_count: int,
    ml_probability: Optional[float],
    upstream_confidence: Optional[float],
    upstream_confidence_rationale: Optional[str],
    stale: bool,
    single_source_model: Optional[MLPrediction] = None,
    single_source_probability: Optional[float] = None,
) -> Tuple[ConfidenceLevel, Optional[float], Optional[ConfidenceSource], str]:
    """
    Documented confidence resolution (see module docstring).

    Returns (level, numerical_confidence, source, rationale). Confidence is
    never fabricated: it is either reused from an upstream source with
    attribution, produced by the documented deterministic method, or
    reported as insufficient_evidence.
    """
    level: ConfidenceLevel
    value: Optional[float]
    source: Optional[ConfidenceSource]
    rationale: str

    if upstream_confidence is not None:
        level = _level_for_value(upstream_confidence)
        value = upstream_confidence
        source = ConfidenceSource.DECISION_ENGINE
        rationale = (
            "Reused verbatim from the Decision Engine decision"
            + (f" ({upstream_confidence_rationale})"
               if upstream_confidence_rationale else "")
            + " (methodology documented in the Decision Engine)."
        )
    elif source_count >= 2:
        computed = CONFIDENCE_BASE + CONFIDENCE_SOURCE_STEP * (source_count - 2)
        ml_note = ""
        if ml_probability is not None:
            computed += CONFIDENCE_ML_BONUS
            ml_note = " plus a model-reported probability"
        computed = round(min(CONFIDENCE_MAX, computed), 2)
        level = _level_for_value(computed)
        value = computed
        source = ConfidenceSource.RISK_OPPORTUNITY
        rationale = (
            f"{source_count} independent sources agree{ml_note}; "
            "deterministic method documented in this module "
            f"(base {CONFIDENCE_BASE}, +{CONFIDENCE_SOURCE_STEP} per extra "
            f"source, cap {CONFIDENCE_MAX})."
        )
    elif single_source_model is not None and \
            single_source_probability is not None:
        level = _level_for_value(single_source_probability)
        value = single_source_probability
        source = ConfidenceSource.ML_MODEL
        rationale = (
            f"Reused verbatim from the {single_source_model.model_name} "
            "model's own reported probability/confidence (the only "
            "corroborating source for this item)."
        )
    else:
        level = ConfidenceLevel.INSUFFICIENT_EVIDENCE
        value = None
        source = None
        rationale = (
            "Single corroborating source; numeric confidence is not "
            "calculated (no confirmed basis for a value)."
        )

    if stale:
        level = _downgrade(level)
        rationale += (
            " Downgraded one level because a contributing source is stale."
        )
    return level, value, source, rationale


# =============================================================================
# Consolidation (multi-source correlation + duplicate suppression)
# =============================================================================


def _dedupe_signals(
    entries: Sequence[SupportingSignal],
) -> List[SupportingSignal]:
    """Deduplicate evidence entries by (signal, source), preserving order."""
    seen = set()
    result: List[SupportingSignal] = []
    for entry in entries:
        marker = (entry.signal, entry.source)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(entry)
    return result


def _dedupe_sources(
    entries: Sequence[ContributingSource],
) -> List[ContributingSource]:
    """Deduplicate contributing sources by name, preserving order."""
    seen = set()
    result: List[ContributingSource] = []
    for entry in entries:
        if entry.source in seen:
            continue
        seen.add(entry.source)
        result.append(entry)
    return result


def _priority_rank(value: Optional[str]) -> int:
    order = {
        PriorityLevel.CRITICAL.value: 0,
        PriorityLevel.HIGH.value: 1,
        PriorityLevel.MEDIUM.value: 2,
        PriorityLevel.LOW.value: 3,
    }
    return order.get(value or "", 4)


def _stronger_priority(
    first: Optional[str], second: Optional[str],
) -> Optional[str]:
    """The stronger (higher) of two upstream priorities, else whichever exists."""
    if first is None:
        return second
    if second is None:
        return first
    return first if _priority_rank(first) <= _priority_rank(second) else second


def _merge_candidates(first: _Candidate, second: _Candidate) -> _Candidate:
    """
    Merge two candidates describing the SAME underlying condition.

    The primary candidate owns the title/description; evidence, sources,
    flags, actions and reasoning are combined. Nothing is dropped: every
    piece of evidence and every contributing source is retained on the
    single consolidated item.
    """
    if second.primary and not first.primary:
        owner, other = second, first
    else:
        owner, other = first, second

    reasoning_parts = [owner.reasoning]
    other_reasoning = " ".join(other.reasoning.split())
    if other_reasoning and other_reasoning not in reasoning_parts[0]:
        reasoning_parts.append(f"Additionally: {other_reasoning}")

    actions: List[str] = []
    for candidate_action in (owner.action, other.action):
        if candidate_action and candidate_action not in actions:
            actions.append(candidate_action)

    return _Candidate(
        kind=owner.kind,
        key=owner.key,
        category=owner.category,
        title=owner.title,
        description=owner.description,
        reasoning=" ".join(reasoning_parts),
        sources=_dedupe_sources(list(owner.sources) + list(other.sources)),
        evidence=_dedupe_signals(list(owner.evidence) + list(other.evidence)),
        action=" ".join(actions) if actions else None,
        stage=owner.stage or other.stage,
        primary=owner.primary or other.primary,
        elevated=owner.elevated or other.elevated,
        severe=owner.severe or other.severe,
        sensitive=owner.sensitive or other.sensitive,
        time_sensitive=owner.time_sensitive or other.time_sensitive,
        time_bound=owner.time_bound or other.time_bound,
        time_window=owner.time_window or other.time_window,
        valid_until=owner.valid_until or other.valid_until,
        ml_probability=(
            owner.ml_probability
            if owner.ml_probability is not None else other.ml_probability
        ),
        upstream_priority=_stronger_priority(
            owner.upstream_priority, other.upstream_priority
        ),
        upstream_confidence=(
            owner.upstream_confidence
            if owner.upstream_confidence is not None
            else other.upstream_confidence
        ),
        upstream_confidence_rationale=(
            owner.upstream_confidence_rationale
            or other.upstream_confidence_rationale
        ),
    )


def _consolidate(candidates: Sequence[_Candidate]) -> List[_Candidate]:
    """
    Merge candidates that share a consolidation key (rule order preserved).

    This is where multi-source correlation and duplicate suppression
    happen: one consolidated item is produced per underlying condition,
    carrying the combined evidence of every contributing rule.
    """
    merged: Dict[str, _Candidate] = {}
    for candidate in candidates:
        if candidate.key not in merged:
            merged[candidate.key] = candidate
        else:
            merged[candidate.key] = _merge_candidates(
                merged[candidate.key], candidate
            )
    return list(merged.values())


# =============================================================================
# Upstream signal readers (read only what upstream reported)
# =============================================================================


def _irrigation_need(pred: Optional[MLPrediction]) -> Optional[bool]:
    """
    The irrigation model's OWN reported need, or None when it did not report
    one.

    Only model-reported values are used (boolean metadata flag or the
    model's own status vocabulary). The model's threshold logic is never
    recomputed here.
    """
    if pred is None:
        return None
    metadata = pred.metadata or {}
    for key in ("irrigation_required", "irrigation_needed"):
        value = metadata.get(key)
        if isinstance(value, bool):
            return value
    phrases = _hint_phrases(pred)
    if _matches(phrases, WATER_STRESS_PHRASES):
        return True
    if _matches(phrases, ADEQUATE_MOISTURE_PHRASES):
        return False
    return None


def _categorical_level(
    pred: Optional[MLPrediction], adverse, favourable,
) -> Optional[str]:
    """
    Read a model's OWN categorical outcome ('adverse'/'favourable') or None.

    Adverse is checked first. No level is inferred when the model reported
    nothing that matches its documented output vocabulary.
    """
    if pred is None:
        return None
    phrases = _hint_phrases(pred)
    if _matches(phrases, adverse):
        return "adverse"
    if _matches(phrases, favourable):
        return "favourable"
    return None


def _yield_hint(pred: Optional[MLPrediction]) -> Optional[str]:
    """
    Comparative yield hint reported by the yield model, or None.

    The shipped yield contract returns a numeric prediction with an
    interval but no reference baseline, so a comparative hint is only
    available when the model (or its adapter) reported one. None means
    "not comparable" and is reported as a data-quality notice instead of
    being interpreted.
    """
    if pred is None:
        return None
    metadata = pred.metadata or {}
    for key in ("expected_change_percent", "predicted_change_percent"):
        value = metadata.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if value <= -MARKET_CHANGE_PERCENT_THRESHOLD:
                return "adverse"
            if value >= MARKET_CHANGE_PERCENT_THRESHOLD:
                return "favourable"
            return "neutral"
    return _categorical_level(pred, YIELD_ADVERSE_PHRASES, YIELD_FAVOURABLE_PHRASES)


def _market_move(market) -> Tuple[Optional[str], Optional[float]]:
    """
    (direction, change_percent) from the Market Forecast context, else
    (None, None). The forecast trend takes precedence over the recent trend.
    """
    if not market or not market.is_market_data_available:
        return None, None
    trend = market.forecast_trend or market.recent_trend
    if trend not in ("increasing", "decreasing"):
        return None, None
    change = (
        market.forecast_change_percent
        if market.forecast_change_percent is not None
        else market.recent_change_percent
    )
    if change is None or abs(change) < MARKET_CHANGE_PERCENT_THRESHOLD:
        return None, None
    return trend, change


def _apply_upstream(
    view: _AnalysisView, candidate: _Candidate, *decision_types: DecisionType,
) -> _Candidate:
    """
    Attribute an upstream Decision Engine decision for the same condition.

    Attribution only: the upstream priority/confidence is reused (never
    recomputed), the decision is added as a contributing source and one
    reasoning sentence keeps the item traceable to it.
    """
    decision = view.decision(*decision_types)
    if decision is None:
        return candidate
    candidate.sources.append(_decision_source(decision))
    candidate.upstream_priority = _stronger_priority(
        candidate.upstream_priority, decision.priority.value
    )
    if candidate.upstream_confidence is None and decision.confidence is not None:
        candidate.upstream_confidence = decision.confidence
        candidate.upstream_confidence_rationale = decision.confidence_rationale
    candidate.reasoning += (
        f" The Decision Engine independently reports '{decision.title}' "
        f"for this condition (priority: {decision.priority.value})."
    )
    return candidate


def _stage_sentence(view: _AnalysisView) -> str:
    """Deterministic stage-context sentence (never assumes a stage)."""
    if not view.stage:
        return (
            " No growth stage was available, so no stage-specific "
            "amplification was applied."
        )
    if view.stage_sensitive():
        return (
            f" The crop is currently in the {view.stage} stage, which the "
            "crop calendar flags as sensitive."
        )
    return f" The crop is currently in the {view.stage} stage."


def _append_stage_context(
    view: _AnalysisView, candidate: _Candidate,
) -> _Candidate:
    """Attach growth-stage context (calendar evidence + source) when known."""
    if not view.stage:
        return candidate
    candidate.evidence.append(_sig(
        "growth_stage", "crop_calendar",
        f"Current growth stage: {view.stage}", view.stage,
    ))
    candidate.sources.append(
        _calendar_source("Crop Calendar growth-stage context")
    )
    return candidate


# =============================================================================
# RISK RULES - weather hazards
# =============================================================================


def _weather_hazard(
    view: _AnalysisView,
    *,
    key: str,
    category: RiskCategory,
    title: str,
    description: str,
    reason: str,
    active_signals: Sequence[str],
    action: str,
    elevated: bool,
    time_sensitive: bool,
    time_bound: bool = True,
    primary: bool = True,
    severe: bool = False,
) -> _Candidate:
    """Build a weather-driven risk candidate with complete evidence."""
    candidate = _Candidate(
        kind="risk",
        key=key,
        category=category.value,
        title=title,
        description=description,
        reasoning=reason,
        sources=[_weather_source()],
        evidence=_signal_evidence(view.signals, active_signals),
        action=action,
        stage=view.stage,
        primary=primary,
        elevated=elevated,
        severe=severe,
        sensitive=view.stage_sensitive(),
        time_sensitive=time_sensitive,
        valid_until=view.forecast_valid_until() if time_bound else None,
    )
    _append_stage_context(view, candidate)
    return candidate


def _rule_excess_rainfall(view: _AnalysisView) -> List[_Candidate]:
    """
    Excess rainfall / heavy rainfall expected.

    Fires whenever the weather module reported a rain signal; a sensitive
    growth stage amplifies the severity (documented ladder).
    """
    active = view.active_in(RAIN_SIGNALS)
    if not active:
        return []
    heavy = view.active("heavy_rainfall_expected")
    title = "Heavy Rainfall Expected" if heavy else "Rainfall Expected"
    reason = (
        f"Forecast signals ({', '.join(active)}) indicate rainfall during "
        f"the forecast window.{_stage_sentence(view)}"
    )
    return [_weather_hazard(
        view,
        key=KEY_EXCESS_RAINFALL,
        category=RiskCategory.WEATHER,
        title=title,
        description=(
            "Rainfall is forecast for the current window; field operations "
            "and drainage should be reviewed."
        ),
        reason=reason,
        active_signals=active,
        action=(
            "Review field drainage and field-operation timing for the "
            "forecast window."
        ),
        # The rule only fires on a weather-reported rain signal, which is
        # itself an adverse condition for field operations (documented).
        elevated=True,
        time_sensitive=heavy,
    )]


def _rule_heat_stress(view: _AnalysisView) -> List[_Candidate]:
    """Extreme heat expected (weather-reported threshold)."""
    if not view.active("extreme_heat_expected"):
        return []
    reason = (
        "The weather module reports extreme heat in the forecast window "
        "(maximum temperature at or above the documented threshold)."
        f"{_stage_sentence(view)}"
    )
    return [_weather_hazard(
        view,
        key=KEY_HEAT_STRESS,
        category=RiskCategory.WEATHER,
        title="Heat Stress Risk",
        description=(
            "Extreme heat is forecast; the crop may be exposed to heat "
            "stress during the forecast window."
        ),
        reason=reason,
        active_signals=["extreme_heat_expected"],
        action=(
            "Review the irrigation plan and field-operation timing for the "
            "forecast heat window."
        ),
        elevated=True,
        time_sensitive=False,
    )]


def _rule_cold_stress(view: _AnalysisView) -> List[_Candidate]:
    """Frost / cold stress expected (weather-reported threshold)."""
    if not view.active("frost_risk_expected"):
        return []
    reason = (
        "The weather module reports minimum temperatures at or below the "
        f"frost threshold in the forecast window.{_stage_sentence(view)}"
    )
    return [_weather_hazard(
        view,
        key=KEY_COLD_STRESS,
        category=RiskCategory.WEATHER,
        title="Cold / Frost Risk",
        description=(
            "Low minimum temperatures are forecast; the crop may be "
            "exposed to cold or frost stress."
        ),
        reason=reason,
        active_signals=["frost_risk_expected"],
        action=(
            "Review frost-protection options and field-operation timing "
            "for the forecast window."
        ),
        elevated=True,
        time_sensitive=True,
    )]


def _rule_wind_damage(view: _AnalysisView) -> List[_Candidate]:
    """Strong wind expected (weather-reported threshold)."""
    if not view.active("strong_wind_expected"):
        return []
    reason = (
        "The weather module reports strong winds in the forecast window "
        f"(at or above the documented threshold).{_stage_sentence(view)}"
    )
    return [_weather_hazard(
        view,
        key=KEY_WIND_DAMAGE,
        category=RiskCategory.WEATHER,
        title="Strong Wind Risk",
        description=(
            "Strong winds are forecast; field operations and standing crop "
            "may be affected."
        ),
        reason=reason,
        active_signals=["strong_wind_expected"],
        action=(
            "Review field-operation and crop-support needs for the "
            "forecast wind window."
        ),
        elevated=True,
        time_sensitive=True,
    )]


def _rule_severe_weather(view: _AnalysisView) -> List[_Candidate]:
    """Severe-weather indicators reported by the weather module."""
    if not view.active("severe_weather_indicator"):
        return []
    reason = (
        "The weather module reported severe-weather indicators for this "
        f"location.{_stage_sentence(view)}"
    )
    return [_weather_hazard(
        view,
        key=KEY_SEVERE_WEATHER,
        category=RiskCategory.WEATHER,
        title="Severe Weather Reported",
        description=(
            "Severe-weather indicators were reported; the condition is "
            "treated as time-sensitive."
        ),
        reason=reason,
        active_signals=["severe_weather_indicator"],
        action=(
            "Review protective measures and follow the weather module's "
            "severe-weather indicators."
        ),
        elevated=True,
        time_sensitive=True,
        severe=True,
    )]


# =============================================================================
# RISK RULES - water / irrigation (multi-source correlation)
# =============================================================================


def _irrigation_need_candidate(
    view: _AnalysisView, irrigation: MLPrediction,
) -> _Candidate:
    """Irrigation-model contributor to the consolidated water-stress risk."""
    probability = _model_probability(irrigation)
    status_message = (irrigation.metadata or {}).get("status_message")
    detail = "Irrigation model reports irrigation need"
    if status_message:
        detail += f" (model status: {status_message})"
    candidate = _Candidate(
        kind="risk",
        key=KEY_WATER_STRESS,
        category=RiskCategory.IRRIGATION.value,
        title="Irrigation Requirement Reported by Model",
        description=(
            "The irrigation model reports that irrigation is required for "
            "this context; no quantity is stated because the model did not "
            "provide one."
        ),
        reasoning=(
            "The smart irrigation model reports irrigation need for this "
            "context. The model's own agronomic status is the source of "
            "this signal; this layer does not recompute its thresholds."
        ),
        sources=[_ml_source(
            "smart_irrigation",
            "Smart Irrigation ML prediction (signal source; friend's ML layer)",
        )],
        evidence=[_sig(
            "irrigation_model_requires_irrigation", "smart_irrigation",
            detail, probability,
        )],
        action=(
            "Review the irrigation plan for the forecast window (the model "
            "reported irrigation need and did not provide a quantity)."
        ),
        stage=view.stage,
        primary=True,
        elevated=True,
        sensitive=view.stage_sensitive(),
        time_sensitive=False,
        ml_probability=probability,
    )
    _append_stage_context(view, candidate)
    return candidate


def _rule_water_stress(view: _AnalysisView) -> List[_Candidate]:
    """
    Water stress / irrigation risk, consolidated into ONE item.

    Contributors (same consolidation key):
    - weather: the forecast window is dry (insufficient rainfall and no
      high precipitation probability), optionally amplified by heat
    - irrigation model: the model itself reports irrigation need

    When the irrigation model reports need AND rainfall is expected, the
    sources conflict: this rule stays silent and the conflict path reports
    the disagreement instead (never silently resolved).
    """
    irrigation = view.ml("smart_irrigation")
    need = _irrigation_need(irrigation)
    if need is True and view.any_active(RAIN_SIGNALS):
        return []

    dry = view.active("insufficient_rainfall_expected") and \
        not view.active("high_precipitation_probability")
    heat = view.active("extreme_heat_expected")
    if not dry and need is not True:
        return []

    candidates: List[_Candidate] = []
    if dry:
        active_signals = ["insufficient_rainfall_expected"]
        if view.active("low_precipitation_probability"):
            active_signals.append("low_precipitation_probability")
        if heat:
            active_signals.append("extreme_heat_expected")
        reason = (
            "The forecast window is dry (insufficient rainfall and no high "
            "precipitation probability)"
            + (", with extreme heat also forecast" if heat else "")
            + f".{_stage_sentence(view)}"
        )
        candidates.append(_weather_hazard(
            view,
            key=KEY_WATER_STRESS,
            category=RiskCategory.WEATHER,
            title="Water Deficit Risk",
            description=(
                "Rainfall is not expected within the forecast window; soil "
                "moisture may decline."
            ),
            reason=reason,
            active_signals=active_signals,
            action="Review the irrigation plan for the forecast window.",
            elevated=heat,
            time_sensitive=False,
            primary=need is not True,
        ))
    if need is True and irrigation is not None:
        candidates.append(_irrigation_need_candidate(view, irrigation))
    return candidates


# =============================================================================
# RISK RULES - disease / pest / soil (ML signal + independent context)
# =============================================================================


def _rule_disease_favourable_weather(view: _AnalysisView) -> List[_Candidate]:
    """
    Disease-favourable weather conditions.

    This is a WEATHER-condition risk, not a diagnosis: the disease model
    remains the only source of a disease diagnosis. It contributes to the
    same consolidation key as the model rule, so the two are merged into a
    single consolidated disease-pressure risk when both apply.
    """
    favourable = view.active_in(DISEASE_FAVOURABLE_SIGNALS)
    if not favourable:
        return []

    model = view.ml("disease_detection")
    probability = _model_probability(model)
    if probability is not None and probability >= ML_PROBABILITY_THRESHOLD:
        # The model rule owns the consolidated item as its primary source.
        return []

    elevated = view.active("heavy_rainfall_expected") or (
        view.active("high_humidity") and view.any_active(RAIN_SIGNALS)
    )
    reason = (
        "Weather conditions reported by the weather module ("
        + ", ".join(favourable)
        + ") favour disease development. The disease model reported no "
        "elevated probability, so this is a weather-condition risk only - "
        "no disease diagnosis is made by this layer."
        + _stage_sentence(view)
    )
    candidate = _Candidate(
        kind="risk",
        key=KEY_DISEASE_PRESSURE,
        category=RiskCategory.DISEASE.value,
        title="Disease-Favourable Weather Conditions",
        description=(
            "Humidity/rainfall conditions favour disease development; "
            "monitor the crop (no disease diagnosis is available)."
        ),
        reasoning=reason,
        sources=[_weather_source()],
        evidence=_signal_evidence(view.signals, favourable),
        action=(
            "Increase scouting frequency for disease symptoms while these "
            "weather conditions persist."
        ),
        stage=view.stage,
        elevated=elevated,
        sensitive=view.stage_sensitive(),
        time_sensitive=False,
        valid_until=view.forecast_valid_until(),
    )
    _append_stage_context(view, candidate)
    return [candidate]


def _rule_disease_model(view: _AnalysisView) -> List[_Candidate]:
    """
    Elevated disease probability reported by the disease detection model.

    The ML model remains the ONLY source of the disease diagnosis; this
    layer consolidates it with weather and growth-stage context.
    """
    model = view.ml("disease_detection")
    if model is None:
        return []
    probability = _model_probability(model)
    if probability is None or probability < ML_PROBABILITY_THRESHOLD:
        return []

    favourable = view.active_in(DISEASE_FAVOURABLE_SIGNALS)
    detail = f"Disease model reports elevated probability ({probability:.2f})"
    if model.prediction:
        detail += f" for {model.prediction}"
    evidence = [_sig(
        "disease_model_elevated_probability", "disease_detection",
        detail, probability,
    )]
    sources = [_ml_source(
        "disease_detection",
        "Disease Detection ML prediction (diagnosis source; friend's ML "
        "layer)",
    )]
    if favourable:
        evidence += _signal_evidence(view.signals, favourable)
        sources.append(_weather_source())
        reason = (
            f"The disease detection model reports elevated probability "
            f"({probability:.2f})"
            + (f" for {model.prediction}" if model.prediction else "")
            + " and the weather module reports conditions ("
            + ", ".join(favourable)
            + ") favourable for disease development. The ML model remains "
            "the source of the diagnosis; this layer consolidates it with "
            "weather and stage context."
            + _stage_sentence(view)
        )
    else:
        reason = (
            f"The disease detection model reports elevated probability "
            f"({probability:.2f})"
            + (f" for {model.prediction}" if model.prediction else "")
            + ". Weather conditions were not identified as especially "
            "favourable for disease development, but the model signal "
            "warrants monitoring. The ML model remains the source of the "
            "diagnosis."
            + _stage_sentence(view)
        )

    stage_note = (
        f" during the {view.stage} stage" if view.stage
        else " for the current crop"
    )
    candidate = _Candidate(
        kind="risk",
        key=KEY_DISEASE_PRESSURE,
        category=RiskCategory.DISEASE.value,
        title="Elevated Disease Pressure",
        description=(
            "The disease model reports elevated probability"
            + (f" for {model.prediction}" if model.prediction else "")
            + "; weather and stage context are attached."
        ),
        reasoning=reason,
        sources=sources,
        evidence=evidence,
        action=f"Increase scouting frequency for disease symptoms{stage_note}.",
        stage=view.stage,
        primary=True,
        elevated=True,
        sensitive=view.stage_sensitive(),
        time_sensitive=False,
        valid_until=view.forecast_valid_until(),
        ml_probability=probability,
    )
    _append_stage_context(view, candidate)
    return [_apply_upstream(
        view, candidate, DecisionType.disease_weather_risk,
    )]


def _rule_pest_pressure(view: _AnalysisView) -> List[_Candidate]:
    """
    Pest pressure reported by the pest prediction model.

    The ML model remains the only source of the pest signal; the crop
    calendar supplies stage relevance and never a pest prediction.
    """
    model = view.ml("pest_prediction")
    if model is None:
        return []
    probability = _model_probability(model)
    level = _categorical_level(
        model, PEST_ADVERSE_PHRASES, PEST_FAVOURABLE_PHRASES,
    )
    elevated = (
        probability is not None and probability >= ML_PROBABILITY_THRESHOLD
    ) or level == "adverse"
    if not elevated:
        return []

    detail = "Pest model reports an elevated pest signal"
    if model.prediction:
        detail += f": {model.prediction}"
    if probability is not None:
        detail += f" (reported confidence {probability:.2f})"
    reason = (
        "The pest prediction model reports an elevated pest signal"
        + (f" ({model.prediction})" if model.prediction else "")
        + (f" with reported confidence {probability:.2f}"
           if probability is not None else "")
        + f".{_stage_sentence(view)}"
        + " The ML model remains the source of the pest prediction."
    )
    stage_note = (
        f" during the {view.stage} stage" if view.stage
        else " for the current crop"
    )
    candidate = _Candidate(
        kind="risk",
        key=KEY_PEST_PRESSURE,
        category=RiskCategory.PEST.value,
        title="Elevated Pest Risk",
        description=(
            "The pest prediction model reports an elevated pest signal"
            + (f" ({model.prediction})" if model.prediction else "")
            + "; growth-stage context is attached."
        ),
        reasoning=reason,
        sources=[_ml_source(
            "pest_prediction",
            "Pest Prediction ML (signal source; friend's ML layer)",
        )],
        evidence=[_sig(
            "pest_model_elevated_signal", "pest_prediction", detail, probability,
        )],
        action=f"Increase pest scouting frequency{stage_note}.",
        stage=view.stage,
        primary=True,
        elevated=True,
        sensitive=view.stage_sensitive(),
        time_sensitive=False,
        ml_probability=probability,
    )
    _append_stage_context(view, candidate)
    return [_apply_upstream(
        view, candidate, DecisionType.pest_crop_stage_risk,
    )]


def _rule_soil_condition(view: _AnalysisView) -> List[_Candidate]:
    """
    Soil condition risk, only when the Soil Analysis model itself reported an
    adverse status.

    The shipped soil contract returns a numeric prediction with an interval
    and no reference baseline, so no soil risk is inferred from it; the rule
    fires only on an explicit model-reported status.
    """
    model = view.ml("soil_analysis")
    if model is None:
        return []
    if _categorical_level(
        model, SOIL_ADVERSE_PHRASES, SOIL_FAVOURABLE_PHRASES,
    ) != "adverse":
        return []

    detail = "Soil analysis model reports an adverse soil status"
    if model.prediction:
        detail += f": {model.prediction}"
    candidate = _Candidate(
        kind="risk",
        key=KEY_SOIL_CONDITION,
        category=RiskCategory.SOIL.value,
        title="Adverse Soil Condition Reported by Model",
        description=(
            "The Soil Analysis model reported an adverse soil status for "
            "this context."
        ),
        reasoning=(
            "The soil analysis model reported an adverse soil status. The "
            "numeric soil values are not interpreted by this layer because "
            "the model does not provide a reference baseline."
        ),
        sources=[_ml_source(
            "soil_analysis",
            "Soil Analysis ML (status source; friend's ML layer)",
        )],
        evidence=[_sig(
            "soil_model_adverse_status", "soil_analysis", detail,
            model.prediction,
        )],
        action=(
            "Review the soil analysis output before the next fertilizer "
            "application."
        ),
        stage=view.stage,
        primary=True,
        elevated=True,
        sensitive=False,
        time_sensitive=False,
        ml_probability=_model_probability(model),
    )
    _append_stage_context(view, candidate)
    return [candidate]


# =============================================================================
# RISK RULES - market / yield / fertilizer / crop stage
# =============================================================================


def _market_signals(direction: str, market) -> List[SupportingSignal]:
    """Evidence entries for a meaningful market move (source: market)."""
    trend_signal = (
        f"market_forecast_{direction}"
        if market.forecast_trend == direction
        else f"market_recent_{direction}"
    )
    change = (
        market.forecast_change_percent
        if market.forecast_change_percent is not None
        else market.recent_change_percent
    )
    strength = (
        market.signal_strength if market.signal_strength is not None else "n/a"
    )
    return [_sig(
        trend_signal, "market",
        f"Market trend for {market.commodity}: {direction} "
        f"({change:+.1f}%); signal strength {strength}",
        change,
    )]


def _market_crop_match_signal(view: _AnalysisView) -> SupportingSignal:
    return _sig(
        "crop_market_match", "crop_calendar",
        f"Commodity {view.market.commodity} corresponds to crop {view.crop}",
        view.crop,
    )


def _rule_market_downside(view: _AnalysisView) -> List[_Candidate]:
    """
    Adverse market price trend for the farmer's crop.

    Only fires when the Market Forecast reported a meaningful decrease for a
    commodity that corresponds to the farmer's crop (fixed synonym matching).
    """
    if not view.crop:
        return []
    market = view.market
    if not market or not _commodity_matches_crop(view.crop, market.commodity):
        return []
    direction, change = _market_move(market)
    if direction != "decreasing":
        return []

    harvest_note = (
        " The crop is approaching its harvest window, which makes the price "
        "trend time-sensitive."
        if view.harvest_imminent() else ""
    )
    candidate = _Candidate(
        kind="risk",
        key=KEY_MARKET_DOWNSIDE,
        category=RiskCategory.MARKET.value,
        title=f"Adverse Market Trend for {view.crop}",
        description=(
            f"The Market Forecast reports a decreasing price trend "
            f"({change:+.1f}%) for {market.commodity}, which corresponds to "
            f"the farmer's crop."
        ),
        reasoning=(
            f"The Market Forecast reports a decreasing price trend for "
            f"{market.commodity} ({change:+.1f}% expected change), and the "
            f"commodity corresponds to the farmer's crop ({view.crop}). "
            "This is market context only: this layer does not advise buying "
            "or selling and performs no economic calculation."
            + harvest_note
        ),
        sources=[
            _src("market", SourceType.EXTERNAL_DATA,
                 "Market Forecast trend signals"),
            _calendar_source("Crop identification used for market matching"),
        ],
        evidence=_market_signals(direction, market) + [
            _market_crop_match_signal(view),
        ],
        action=(
            "Review the market forecast trend before planning sales; "
            "pricing decisions belong to a downstream module."
        ),
        stage=view.stage,
        primary=True,
        elevated=True,
        sensitive=False,
        time_sensitive=view.harvest_imminent(),
    )
    return [_apply_upstream(view, candidate, DecisionType.market_crop_context)]


def _rule_yield_market_risk(view: _AnalysisView) -> List[_Candidate]:
    """
    Yield + market risk, only when a comparative signal exists.

    Requires an adverse yield hint reported by the yield model AND a
    meaningful market decrease for a matching commodity. No economic
    calculation is performed.
    """
    yield_prediction = view.ml("crop_yield_prediction")
    if yield_prediction is None or not view.crop:
        return []
    market = view.market
    if not market or not _commodity_matches_crop(view.crop, market.commodity):
        return []
    if _yield_hint(yield_prediction) != "adverse":
        return []
    direction, change = _market_move(market)
    if direction != "decreasing":
        return []

    unit = f" {yield_prediction.unit}" if yield_prediction.unit else ""
    candidate = _Candidate(
        kind="risk",
        key=KEY_YIELD_MARKET,
        category=RiskCategory.YIELD.value,
        title=f"Yield and Market Risk for {view.crop}",
        description=(
            "The yield model reports an adverse yield signal while the "
            "market trend for the matching commodity is decreasing."
        ),
        reasoning=(
            "The crop yield model reports an adverse yield signal"
            + (f" ({yield_prediction.prediction}{unit})"
               if yield_prediction.prediction else "")
            + ", and the Market Forecast reports a decreasing price trend "
            f"for {market.commodity} ({change:+.1f}%). Both independent "
            "sources point in the same adverse direction. No economic "
            "estimate is produced because not all required inputs are "
            "provided by the existing modules."
            + _stage_sentence(view)
        ),
        sources=[
            _ml_source(
                "crop_yield_prediction",
                "Crop Yield Prediction ML (signal source; friend's ML layer)",
            ),
            _src("market", SourceType.EXTERNAL_DATA,
                 "Market Forecast price context"),
            _calendar_source("Crop identification used for market matching"),
        ],
        evidence=[
            _sig(
                "yield_model_adverse_signal", "crop_yield_prediction",
                "Yield model reports an adverse yield signal"
                + (f": {yield_prediction.prediction}{unit}"
                   if yield_prediction.prediction else ""),
                _model_probability(yield_prediction),
            ),
            *_market_signals(direction, market),
            _market_crop_match_signal(view),
        ],
        action=(
            "Review the yield and market signals together before planning "
            "sales; this layer produces no economic estimate."
        ),
        stage=view.stage,
        primary=True,
        elevated=True,
        sensitive=view.stage_sensitive(),
        time_sensitive=view.harvest_imminent(),
        ml_probability=_model_probability(yield_prediction),
    )
    return [_apply_upstream(view, candidate, DecisionType.yield_market_context)]


def _rule_fertilizer_risk(view: _AnalysisView) -> List[_Candidate]:
    """
    Fertilizer application context risk.

    Fires only when a fertilizer recommendation exists AND adverse weather
    is forecast for the window. The recommendation itself always comes from
    the ML model and is never recomputed here.
    """
    fertilizer = view.ml("fertilizer_recommendation")
    if fertilizer is None:
        return []
    adverse = view.active_in(ADVERSE_WEATHER_SIGNALS)
    if not adverse:
        return []

    detail = "Fertilizer model recommendation available"
    if fertilizer.prediction:
        detail = f"Fertilizer model recommendation: {fertilizer.prediction}"
    reason = (
        f"The fertilizer recommendation model reports: "
        f"{fertilizer.prediction or 'a recommendation (see model output)'}. "
        f"Adverse weather is forecast ({', '.join(adverse)}), so the "
        "application window may be affected. The recommendation itself "
        "comes from the ML model; this layer only adds context and does not "
        "recompute it."
        + _stage_sentence(view)
    )
    candidate = _Candidate(
        kind="risk",
        key=KEY_FERTILIZER_APPLICATION,
        category=RiskCategory.FERTILIZER.value,
        title="Fertilizer Application Timing at Risk",
        description=(
            "A fertilizer recommendation is available while adverse weather "
            "is forecast for the application window."
        ),
        reasoning=reason,
        sources=[
            _ml_source(
                "fertilizer_recommendation",
                "Fertilizer Recommendation ML (recommendation source; "
                "friend's ML layer)",
            ),
            _weather_source(),
        ],
        evidence=[
            _sig(
                "fertilizer_model_recommendation",
                "fertilizer_recommendation", detail,
                _model_probability(fertilizer),
            ),
            *_signal_evidence(view.signals, adverse),
        ],
        action=(
            "Review fertilizer application timing against the forecast "
            "weather window."
        ),
        stage=view.stage,
        primary=True,
        elevated=False,
        # The concern is application TIMING (logistics), not crop
        # susceptibility in this stage, so the sensitive-stage amplification
        # is deliberately NOT applied here (documented rule-level decision).
        sensitive=False,
        time_sensitive=False,
    )
    _append_stage_context(view, candidate)
    return [_apply_upstream(
        view, candidate, DecisionType.fertilizer_contextualization,
    )]


def _rule_stage_transition_risk(view: _AnalysisView) -> List[_Candidate]:
    """
    Crop-stage risk: an imminent sensitive stage coincides with adverse
    weather.

    Only fires when the crop calendar reported BOTH the next stage and the
    days until it, that stage is a sensitive stage, and adverse weather is
    forecast. No stage or date is ever assumed.
    """
    calendar = view.calendar
    if not calendar or not calendar.is_crop_calendar_available:
        return []
    next_stage = calendar.next_stage
    days = calendar.days_to_next_stage
    if not next_stage or days is None:
        return []
    if days > STAGE_TRANSITION_IMMINENT_DAYS:
        return []
    if not _stage_is_sensitive(next_stage):
        return []
    adverse = view.active_in(ADVERSE_WEATHER_SIGNALS)
    if not adverse:
        return []

    current_note = (
        f" The crop is currently in the {view.stage} stage." if view.stage
        else ""
    )
    evidence = _signal_evidence(view.signals, adverse) + [
        _sig(
            "next_growth_stage", "crop_calendar",
            f"Next growth stage: {next_stage} (in {days} days)", next_stage,
        ),
        _sig(
            "sensitive_stage_approaching", "crop_calendar",
            f"{next_stage} is flagged as a sensitive stage by the crop "
            "calendar",
            next_stage,
        ),
    ]
    if view.stage:
        evidence.append(_sig(
            "growth_stage", "crop_calendar",
            f"Current growth stage: {view.stage}", view.stage,
        ))

    candidate = _Candidate(
        kind="risk",
        key=KEY_STAGE_TRANSITION,
        category=RiskCategory.CROP_STAGE.value,
        title=f"Sensitive Stage Approaching During Adverse Weather",
        description=(
            f"The crop approaches the {next_stage} stage (a sensitive stage) "
            f"in {days} days while adverse weather is forecast."
        ),
        reasoning=(
            f"Adverse weather is forecast ({', '.join(adverse)}) while the "
            f"crop approaches the {next_stage} stage in {days} days; the "
            "crop calendar flags that stage as sensitive."
            + current_note
        ),
        sources=[
            _weather_source(),
            _calendar_source("Crop Calendar stage schedule"),
        ],
        evidence=evidence,
        action=(
            f"Prepare for the {next_stage} stage before it begins; the crop "
            f"calendar reports it starts in {days} days."
        ),
        stage=next_stage,
        primary=True,
        elevated=True,
        sensitive=True,
        time_sensitive=True,
    )
    return [_apply_upstream(
        view, candidate, DecisionType.weather_crop_stage_interaction,
    )]


# =============================================================================
# RISK RULES - conflicting signals
# =============================================================================


def _source_type_for(name: str) -> SourceType:
    """Map a source name to its documented source type."""
    if name == "decision_engine":
        return SourceType.DECISION_ENGINE
    if name in KNOWN_ML_MODELS:
        return SourceType.ML_MODEL
    if name == "farmer_context":
        return SourceType.FARMER_CONTEXT
    return SourceType.EXTERNAL_DATA


def _irrigation_conflict(view: _AnalysisView) -> Optional[ConflictNotice]:
    """Rainfall expected vs the irrigation model reporting irrigation need."""
    rain = view.active_in(RAIN_SIGNALS)
    if not rain:
        return None
    irrigation = view.ml("smart_irrigation")
    if _irrigation_need(irrigation) is not True:
        return None

    status_message = (irrigation.metadata or {}).get("status_message")
    detail = "Irrigation model reports irrigation need"
    if status_message:
        detail += f" (model status: {status_message})"
    evidence = _signal_evidence(view.signals, rain) + [_sig(
        "irrigation_model_requires_irrigation", "smart_irrigation",
        detail, _model_probability(irrigation),
    )]
    return ConflictNotice(
        id=_conflict_id(ConflictType.RAINFALL_VS_IRRIGATION_NEED.value),
        type=ConflictType.RAINFALL_VS_IRRIGATION_NEED,
        description=(
            f"Weather forecasts rainfall ({', '.join(rain)}) while the smart "
            "irrigation model reports irrigation need for the same window."
        ),
        conflicting_signals=evidence,
        sources=["smart_irrigation", "weather"],
        detected_by="risk_opportunity",
        unresolved_reason=(
            "Both signals are valid within their own scope: the weather "
            "module describes the forecast window while the irrigation model "
            "describes the soil-moisture state it was given. This layer "
            "cannot determine which one reflects the actual field condition "
            "from the supplied data alone."
        ),
        recommended_action=(
            "Verify in-field soil moisture before acting on either signal."
        ),
        detected_at=_utc_now_iso(),
    )


def _market_yield_conflict(view: _AnalysisView) -> Optional[ConflictNotice]:
    """Market direction vs the yield model's comparative signal."""
    yield_prediction = view.ml("crop_yield_prediction")
    market = view.market
    if yield_prediction is None or not market:
        return None
    if not _commodity_matches_crop(view.crop, market.commodity):
        return None
    hint = _yield_hint(yield_prediction)
    direction, change = _market_move(market)
    if hint is None or direction is None:
        return None
    conflicting = (
        (direction == "increasing" and hint == "adverse")
        or (direction == "decreasing" and hint == "favourable")
    )
    if not conflicting:
        return None

    unit = f" {yield_prediction.unit}" if yield_prediction.unit else ""
    evidence = [
        _sig(
            "yield_model_comparative_signal", "crop_yield_prediction",
            f"Yield model reports a {hint} yield signal"
            + (f" ({yield_prediction.prediction}{unit})"
               if yield_prediction.prediction else ""),
            _model_probability(yield_prediction),
        ),
        *_market_signals(direction, market),
        _market_crop_match_signal(view),
    ]
    return ConflictNotice(
        id=_conflict_id(ConflictType.MARKET_VS_YIELD.value),
        type=ConflictType.MARKET_VS_YIELD,
        description=(
            f"The yield model reports a {hint} yield signal while the "
            f"Market Forecast reports a {direction} price trend for "
            f"{market.commodity} ({change:+.1f}%)."
        ),
        conflicting_signals=evidence,
        sources=["crop_yield_prediction", "market"],
        detected_by="risk_opportunity",
        unresolved_reason=(
            "The two signals describe different quantities (production vs "
            "price) and this layer performs no economic modelling, so it "
            "cannot determine which one dominates the outcome."
        ),
        recommended_action=(
            "Review both signals together before planning sales or storage."
        ),
        detected_at=_utc_now_iso(),
    )


def _detect_conflicts(view: _AnalysisView) -> List[ConflictNotice]:
    """
    Detect conflicting upstream signals.

    When the Decision Engine already reported the same conflict, the notice
    is attributed to it (``detected_by="decision_engine"``) and its
    evidence is merged in, so the conflict is never duplicated.
    """
    conflicts: List[ConflictNotice] = []
    irrigation = _irrigation_conflict(view)
    de_conflict = view.decision(DecisionType.conflicting_signals)
    if irrigation is not None and de_conflict is not None:
        existing = {(e.signal, e.source) for e in irrigation.conflicting_signals}
        for signal in de_conflict.supporting_signals:
            if (signal.signal, signal.source) not in existing:
                irrigation.conflicting_signals.append(signal)
                existing.add((signal.signal, signal.source))
        irrigation.detected_by = "decision_engine"
        irrigation.description += (
            f" The Decision Engine independently reported this conflict "
            f"('{de_conflict.title}', id: {de_conflict.id})."
        )
    if irrigation is not None:
        conflicts.append(irrigation)

    market_yield = _market_yield_conflict(view)
    if market_yield is not None:
        conflicts.append(market_yield)
    return conflicts


def _conflict_risk(
    view: _AnalysisView, conflicts: Sequence[ConflictNotice],
) -> Optional[_Candidate]:
    """
    ONE consolidated risk representing every detected conflict.

    A conflict means the system cannot decide between valid upstream
    signals, so it is surfaced as a data-quality risk rather than being
    resolved silently.
    """
    if not conflicts:
        return None

    evidence: List[SupportingSignal] = []
    sources: List[ContributingSource] = []
    seen_sources = set()
    for conflict in conflicts:
        for signal in conflict.conflicting_signals:
            evidence.append(signal)
            if signal.source not in seen_sources:
                seen_sources.add(signal.source)
                sources.append(_src(
                    signal.source, _source_type_for(signal.source),
                    f"Involved in conflict '{conflict.type.value}'",
                ))

    detectors = sorted({c.detected_by for c in conflicts})
    time_sensitive = any(
        c.type == ConflictType.RAINFALL_VS_IRRIGATION_NEED for c in conflicts
    )
    reasoning = " ".join(
        f"Conflict {index + 1} ({conflict.type.value}): "
        f"{conflict.description} {conflict.unresolved_reason}"
        for index, conflict in enumerate(conflicts)
    ) + (
        " Conflicting signals are reported explicitly; this layer does not "
        "silently choose one interpretation. Detected by: "
        + ", ".join(detectors)
        + "."
    )
    actions: List[str] = []
    for conflict in conflicts:
        if conflict.recommended_action not in actions:
            actions.append(conflict.recommended_action)

    return _Candidate(
        kind="risk",
        key=KEY_CONFLICTING_SIGNALS,
        category=RiskCategory.DATA_QUALITY.value,
        title="Conflicting Signals Detected",
        description=(
            "Upstream signals disagree for the same window: "
            + "; ".join(c.type.value for c in conflicts)
            + "."
        ),
        reasoning=reasoning,
        sources=sources,
        evidence=_dedupe_signals(evidence),
        action=" ".join(actions),
        stage=view.stage,
        primary=True,
        elevated=False,
        sensitive=view.stage_sensitive(),
        time_sensitive=time_sensitive,
    )


# =============================================================================
# OPPORTUNITY RULES
# =============================================================================


def _opportunity(
    view: _AnalysisView,
    *,
    key: str,
    category: OpportunityCategory,
    title: str,
    description: str,
    reasoning: str,
    evidence: Sequence[SupportingSignal],
    sources: Sequence[ContributingSource],
    action: Optional[str] = None,
    time_bound: bool = False,
    time_window: Optional[str] = None,
) -> _Candidate:
    """Build an opportunity candidate with complete evidence."""
    return _Candidate(
        kind="opportunity",
        key=key,
        category=category.value,
        title=title,
        description=description,
        reasoning=reasoning,
        sources=list(sources),
        evidence=list(evidence),
        action=action,
        stage=view.stage,
        primary=True,
        time_bound=time_bound,
        time_window=time_window,
    )


def _rule_favourable_weather_window(view: _AnalysisView) -> List[_Candidate]:
    """
    Favourable weather window for field operations.

    Only fires when EVERY required forecast value was reported AND lies
    inside the documented benign ranges - "no adverse signal" alone is not
    treated as a favourable window.
    """
    required = (
        "low_precipitation_probability",
        "insufficient_rainfall_expected",
        "favourable_max_temperature",
        "favourable_min_temperature",
        "favourable_wind_conditions",
    )
    if view.any_active(ADVERSE_WEATHER_SIGNALS):
        return []
    if any(not view.active(name) for name in required):
        return []

    valid_until = view.forecast_valid_until()
    horizon = (
        f" The window is bounded by the reported forecast horizon "
        f"({view.weather.forecast_horizon_days} days)."
        if valid_until else ""
    )
    time_window = (
        f"{view.reference_date().isoformat()} to "
        f"{valid_until.split('T')[0]}"
        if valid_until else None
    )
    evidence = _signal_evidence(view.signals, required)
    if view.weather.forecast_horizon_days is not None:
        evidence.append(_sig(
            "forecast_horizon", "weather",
            f"Reported forecast horizon: "
            f"{view.weather.forecast_horizon_days} days",
            view.weather.forecast_horizon_days,
        ))
    candidate = _opportunity(
        view,
        key=KEY_FAVOURABLE_WINDOW,
        category=OpportunityCategory.WEATHER,
        title="Favourable Weather Window",
        description=(
            "Rainfall probability, rainfall total, temperature and wind are "
            "all inside the documented benign ranges for the forecast "
            "window."
        ),
        reasoning=(
            "Every reported forecast value is inside the documented benign "
            "ranges (low precipitation probability, low rainfall total, "
            "temperature within range and wind below the threshold), so the "
            f"window is favourable for planned operations.{horizon}"
        ),
        evidence=evidence,
        sources=[_weather_source()],
        action=(
            "Use this window for planned field operations; the reported "
            "forecast conditions are favourable."
        ),
        time_bound=valid_until is not None,
        time_window=time_window,
    )
    _append_stage_context(view, candidate)
    return [candidate]


def _rule_irrigation_efficiency(view: _AnalysisView) -> List[_Candidate]:
    """
    Reduced irrigation requirement (rainfall expected + model reports
    adequate soil moisture). Consolidates two independent sources.
    """
    rain = view.active_in(RAIN_SIGNALS)
    if not rain:
        return []
    irrigation = view.ml("smart_irrigation")
    if irrigation is None or _irrigation_need(irrigation) is not False:
        return []

    status_message = (irrigation.metadata or {}).get("status_message")
    detail = "Irrigation model reports adequate soil moisture"
    if status_message:
        detail += f" (model status: {status_message})"
    candidate = _opportunity(
        view,
        key=KEY_IRRIGATION_EFFICIENCY,
        category=OpportunityCategory.IRRIGATION,
        title="Reduced Irrigation Requirement",
        description=(
            "Rainfall is forecast and the irrigation model reports adequate "
            "soil moisture, so the planned irrigation may be reduced."
        ),
        reasoning=(
            "The weather module forecasts rainfall ("
            + ", ".join(rain)
            + ") and the smart irrigation model reports adequate soil "
            "moisture for this context. Both independent sources point to a "
            "reduced immediate irrigation need; no quantity is stated "
            "because neither source provides one."
        ),
        evidence=_signal_evidence(view.signals, rain) + [_sig(
            "irrigation_model_adequate_moisture", "smart_irrigation",
            detail, _model_probability(irrigation),
        )],
        sources=[
            _weather_source(),
            _ml_source(
                "smart_irrigation",
                "Smart Irrigation ML prediction (signal source; friend's ML "
                "layer)",
            ),
        ],
        action=(
            "Review planned irrigation against the expected rainfall before "
            "applying water."
        ),
    )
    candidate.ml_probability = _model_probability(irrigation)
    _append_stage_context(view, candidate)
    return [_apply_upstream(
        view, candidate, DecisionType.weather_irrigation_interaction,
    )]


def _rule_reduced_disease_pressure(view: _AnalysisView) -> List[_Candidate]:
    """
    Reduced disease pressure: the disease model reported a low probability
    AND the weather does not favour disease development.
    """
    model = view.ml("disease_detection")
    if model is None:
        return []
    probability = _model_probability(model)
    if probability is None or probability >= ML_PROBABILITY_THRESHOLD:
        return []
    if view.any_active(DISEASE_FAVOURABLE_SIGNALS):
        return []

    weather_context = bool(view.weather and view.weather.is_weather_data_available)
    reasons = [
        f"The disease detection model reported a low probability "
        f"({probability:.2f})"
    ]
    evidence = [_sig(
        "disease_model_low_probability", "disease_detection",
        f"Disease model reports low probability ({probability:.2f})"
        + (f" for {model.prediction}" if model.prediction else ""),
        probability,
    )]
    sources = [_ml_source(
        "disease_detection",
        "Disease Detection ML prediction (diagnosis source; friend's ML layer)",
    )]
    if weather_context:
        reasons.append(
            "and the weather module reported no conditions favourable for "
            "disease development"
        )
        sources.append(_weather_source())
    reasoning = (
        " ".join(reasons)
        + ". The ML model remains the source of the disease assessment; "
        "this layer only consolidates it with weather context."
        + _stage_sentence(view)
    )
    return [_opportunity(
        view,
        key=KEY_DISEASE_PRESSURE,
        category=OpportunityCategory.DISEASE,
        title="Reduced Disease Pressure",
        description=(
            "The disease model reported a low probability and the weather "
            "does not favour disease development."
        ),
        reasoning=reasoning,
        evidence=evidence,
        sources=sources,
        action=(
            "Continue routine monitoring; no elevated disease pressure is "
            "indicated by the model or the weather."
        ),
    )]


def _rule_reduced_pest_pressure(view: _AnalysisView) -> List[_Candidate]:
    """Reduced pest pressure reported by the pest prediction model."""
    model = view.ml("pest_prediction")
    if model is None:
        return []
    probability = _model_probability(model)
    level = _categorical_level(
        model, PEST_ADVERSE_PHRASES, PEST_FAVOURABLE_PHRASES,
    )
    if level != "favourable":
        return []
    if probability is not None and probability >= ML_PROBABILITY_THRESHOLD:
        return []

    detail = "Pest model reports a low pest signal"
    if model.prediction:
        detail += f": {model.prediction}"
    return [_opportunity(
        view,
        key=KEY_PEST_PRESSURE,
        category=OpportunityCategory.PEST,
        title="Reduced Pest Pressure",
        description="The pest prediction model reports a low pest signal.",
        reasoning=(
            "The pest prediction model reports a low pest signal"
            + (f" ({model.prediction})" if model.prediction else "")
            + ". The ML model remains the source of the pest assessment."
            + _stage_sentence(view)
        ),
        evidence=[_sig(
            "pest_model_low_signal", "pest_prediction", detail, probability,
        )],
        sources=[_ml_source(
            "pest_prediction",
            "Pest Prediction ML (signal source; friend's ML layer)",
        )],
        action="Continue routine pest monitoring.",
    )]


def _rule_market_upside(view: _AnalysisView) -> List[_Candidate]:
    """
    Favourable market price trend for the farmer's crop.

    Only fires when the Market Forecast reported a meaningful increase for a
    commodity that corresponds to the farmer's crop.
    """
    if not view.crop:
        return []
    market = view.market
    if not market or not _commodity_matches_crop(view.crop, market.commodity):
        return []
    direction, change = _market_move(market)
    if direction != "increasing":
        return []

    harvest_note = (
        " The crop is approaching its harvest window, so the window is "
        "time-bound."
        if view.harvest_imminent() else ""
    )
    candidate = _opportunity(
        view,
        key=KEY_MARKET_UPSIDE,
        category=OpportunityCategory.MARKET,
        title=f"Favourable Market Trend for {view.crop}",
        description=(
            f"The Market Forecast reports an increasing price trend "
            f"({change:+.1f}%) for {market.commodity}, which corresponds to "
            f"the farmer's crop."
        ),
        reasoning=(
            f"The Market Forecast reports an increasing price trend for "
            f"{market.commodity} ({change:+.1f}% expected change) and the "
            f"commodity corresponds to the farmer's crop ({view.crop}). "
            "This is market context only: this layer does not advise buying "
            "or selling." + harvest_note
        ),
        evidence=_market_signals(direction, market) + [
            _market_crop_match_signal(view),
        ],
        sources=[
            _src("market", SourceType.EXTERNAL_DATA,
                 "Market Forecast trend signals"),
            _calendar_source("Crop identification used for market matching"),
        ],
        action=(
            "Review the market forecast trend when planning sales; pricing "
            "decisions belong to a downstream module."
        ),
        time_bound=view.harvest_imminent(),
    )
    return [_apply_upstream(view, candidate, DecisionType.market_crop_context)]


def _rule_yield_market_opportunity(view: _AnalysisView) -> List[_Candidate]:
    """
    Yield + market opportunity, only when a comparative signal exists.

    Requires a favourable yield hint reported by the yield model AND a
    meaningful market increase for a matching commodity.
    """
    yield_prediction = view.ml("crop_yield_prediction")
    if yield_prediction is None or not view.crop:
        return []
    market = view.market
    if not market or not _commodity_matches_crop(view.crop, market.commodity):
        return []
    if _yield_hint(yield_prediction) != "favourable":
        return []
    direction, change = _market_move(market)
    if direction != "increasing":
        return []

    unit = f" {yield_prediction.unit}" if yield_prediction.unit else ""
    time_bound = view.harvest_imminent()
    harvest_note = (
        " The crop is approaching its harvest window." if time_bound else ""
    )
    candidate = _opportunity(
        view,
        key=KEY_YIELD_MARKET,
        category=OpportunityCategory.YIELD,
        title=f"Favourable Yield and Market Combination for {view.crop}",
        description=(
            "The yield model reports a favourable yield signal while the "
            "market trend for the matching commodity is increasing."
        ),
        reasoning=(
            "The crop yield model reports a favourable yield signal"
            + (f" ({yield_prediction.prediction}{unit})"
               if yield_prediction.prediction else "")
            + f", and the Market Forecast reports an increasing price trend "
            f"for {market.commodity} ({change:+.1f}%). Both independent "
            "sources point in the same favourable direction. No economic "
            "estimate is produced by this layer."
            + harvest_note
        ),
        evidence=[
            _sig(
                "yield_model_favourable_signal", "crop_yield_prediction",
                "Yield model reports a favourable yield signal"
                + (f": {yield_prediction.prediction}{unit}"
                   if yield_prediction.prediction else ""),
                _model_probability(yield_prediction),
            ),
            *_market_signals(direction, market),
            _market_crop_match_signal(view),
        ],
        sources=[
            _ml_source(
                "crop_yield_prediction",
                "Crop Yield Prediction ML (signal source; friend's ML layer)",
            ),
            _src("market", SourceType.EXTERNAL_DATA,
                 "Market Forecast price context"),
            _calendar_source("Crop identification used for market matching"),
        ],
        action=(
            "Review the yield and market signals together when planning "
            "sales; this layer produces no economic estimate."
        ),
        time_bound=time_bound,
    )
    candidate.ml_probability = _model_probability(yield_prediction)
    return [_apply_upstream(view, candidate, DecisionType.yield_market_context)]


def _benign_weather_signals(view: _AnalysisView) -> List[str]:
    """Active, explicitly-benign weather signals (never inferred)."""
    return view.active_in((
        "low_precipitation_probability",
        "insufficient_rainfall_expected",
        "favourable_max_temperature",
        "favourable_min_temperature",
        "favourable_wind_conditions",
    ))


def _rule_fertilizer_window(view: _AnalysisView) -> List[_Candidate]:
    """
    Fertilizer application window.

    Fires only when a fertilizer recommendation exists, the crop stage is
    known and the weather module reported benign conditions (no adverse
    signal and at least one explicitly benign value).
    """
    fertilizer = view.ml("fertilizer_recommendation")
    if fertilizer is None or not view.stage:
        return []
    if not view.weather or not view.weather.is_weather_data_available:
        return []
    if view.any_active(ADVERSE_WEATHER_SIGNALS):
        return []
    benign = _benign_weather_signals(view)
    if not benign:
        return []

    detail = "Fertilizer model recommendation available"
    if fertilizer.prediction:
        detail = f"Fertilizer model recommendation: {fertilizer.prediction}"
    return [_opportunity(
        view,
        key=KEY_FERTILIZER_APPLICATION,
        category=OpportunityCategory.FERTILIZER,
        title="Favourable Fertilizer Application Window",
        description=(
            f"A fertilizer recommendation is available for the {view.stage} "
            "stage while no adverse weather is forecast."
        ),
        reasoning=(
            f"The fertilizer recommendation model reports: "
            f"{fertilizer.prediction or 'a recommendation (see model output)'}"
            f", the crop is in the {view.stage} stage, and the weather module "
            "reported benign conditions ("
            + ", ".join(benign)
            + ") with no adverse signal. The recommendation itself comes "
            "from the ML model and is not recomputed here."
        ),
        evidence=[
            _sig(
                "fertilizer_model_recommendation",
                "fertilizer_recommendation", detail,
                _model_probability(fertilizer),
            ),
            *_signal_evidence(view.signals, benign),
            _sig(
                "growth_stage", "crop_calendar",
                f"Current growth stage: {view.stage}", view.stage,
            ),
        ],
        sources=[
            _ml_source(
                "fertilizer_recommendation",
                "Fertilizer Recommendation ML (recommendation source; "
                "friend's ML layer)",
            ),
            _weather_source(),
            _calendar_source("Crop Calendar growth-stage context"),
        ],
        action=(
            "Apply the model's recommended formulation within the current "
            "stage while the forecast stays benign."
        ),
    )]


def _rule_stage_transition_opportunity(
    view: _AnalysisView,
) -> List[_Candidate]:
    """
    Upcoming growth-stage transition under favourable conditions.

    Fires only when the crop calendar reported both the next stage and the
    days until it, the transition is imminent, no adverse weather is
    forecast and the weather module reported benign values.
    """
    calendar = view.calendar
    if not calendar or not calendar.is_crop_calendar_available:
        return []
    next_stage = calendar.next_stage
    days = calendar.days_to_next_stage
    if not next_stage or days is None:
        return []
    if days > STAGE_TRANSITION_IMMINENT_DAYS:
        return []
    if not view.weather or not view.weather.is_weather_data_available:
        return []
    if view.any_active(ADVERSE_WEATHER_SIGNALS):
        return []
    benign = _benign_weather_signals(view)
    if not benign:
        return []

    evidence = [
        _sig(
            "next_growth_stage", "crop_calendar",
            f"Next growth stage: {next_stage} (in {days} days)", next_stage,
        ),
        *_signal_evidence(view.signals, benign),
    ]
    if view.stage:
        evidence.append(_sig(
            "growth_stage", "crop_calendar",
            f"Current growth stage: {view.stage}", view.stage,
        ))
    return [_opportunity(
        view,
        key=KEY_STAGE_TRANSITION,
        category=OpportunityCategory.CROP_STAGE,
        title=f"Upcoming {next_stage} Stage Under Favourable Conditions",
        description=(
            f"The crop moves into the {next_stage} stage in {days} days and "
            "no adverse weather is forecast."
        ),
        reasoning=(
            f"The crop calendar reports the transition to the {next_stage} "
            f"stage in {days} days, and the weather module reported benign "
            "conditions (" + ", ".join(benign) + ") with no adverse signal, "
            "so the transition window is favourable for the planned stage "
            "activities."
        ),
        evidence=evidence,
        sources=[
            _calendar_source("Crop Calendar stage schedule"),
            _weather_source(),
        ],
        action=(
            f"Prepare the {next_stage} stage activities for the upcoming "
            "window."
        ),
        time_bound=True,
        time_window=f"next {days} days until the {next_stage} stage",
    )]


def _rule_harvest_window(view: _AnalysisView) -> List[_Candidate]:
    """
    Harvest window opportunity.

    Fires only when the crop calendar supplied BOTH harvest window dates and
    the as-of date falls inside (or shortly before) that window.
    """
    window_text = view.harvest_window_text()
    if window_text is None or not view.harvest_imminent():
        return []

    evidence = [_sig(
        "calendar_harvest_window", "crop_calendar",
        f"Crop calendar harvest window: {window_text}", window_text,
    )]
    sources = [_calendar_source("Crop Calendar harvest window")]
    market_note = ""
    market = view.market
    if market and market.is_market_data_available:
        sources.append(_src(
            "market", SourceType.EXTERNAL_DATA,
            "Market Forecast context for the harvest window",
        ))
        if market.current_price is not None:
            evidence.append(_sig(
                "market_price_available", "market",
                f"Current market price: {market.current_price}",
                market.current_price,
            ))
        trend = market.forecast_trend or market.recent_trend
        if trend in ("increasing", "decreasing", "stable"):
            market_note = (
                f" The Market Forecast trend for {market.commodity} is "
                f"{trend}."
            )

    return [_opportunity(
        view,
        key=KEY_HARVEST_WINDOW,
        category=OpportunityCategory.HARVEST,
        title="Harvest Window Approaching",
        description=(
            f"The crop calendar harvest window is {window_text}; harvest "
            "logistics can be planned inside it."
        ),
        reasoning=(
            f"The crop calendar reports a harvest window of {window_text} "
            "and the as-of date falls inside (or just before) that window."
            + market_note
        ),
        evidence=evidence,
        sources=sources,
        action=(
            "Plan harvest logistics inside the calendar harvest window; the "
            "window comes from the Crop Calendar module."
        ),
        time_bound=True,
        time_window=window_text,
    )]


# =============================================================================
# Data-quality notices and assessment
# =============================================================================


def _notice(
    issue_type: DataQualityIssueType,
    source: str,
    message: str,
    affected: Sequence[str] = (),
) -> DataQualityNotice:
    return DataQualityNotice(
        id=_notice_id(issue_type.value, source),
        type=issue_type,
        source=source,
        message=message,
        affected_analysis=list(affected),
        detected_at=_utc_now_iso(),
    )


def _data_quality_notices(view: _AnalysisView) -> List[DataQualityNotice]:
    """
    Deterministic data-quality notices (fixed emission order).

    Notices state what was skipped and why. They never contain substituted
    values and never mark an unknown source as stale.
    """
    farm = view.farm
    notices: List[DataQualityNotice] = []

    if not view.crop:
        notices.append(_notice(
            DataQualityIssueType.MISSING_FIELD, "farmer_context",
            "Crop was not specified; crop-specific market matching and "
            "crop-stage rules were skipped (no crop was assumed).",
            ["market_rules", "crop_stage_rules"],
        ))

    if not view.weather or not view.weather.is_weather_data_available:
        notices.append(_notice(
            DataQualityIssueType.MISSING_DATA, "weather",
            "Weather data was unavailable; weather-related risks and "
            "opportunities were skipped (no values were substituted).",
            ["weather_rules", "irrigation_rules", "disease_rules",
             "fertilizer_window_rules"],
        ))

    if not view.market or not view.market.is_market_data_available:
        notices.append(_notice(
            DataQualityIssueType.MISSING_DATA, "market",
            "Market data was unavailable; market risks and opportunities "
            "were skipped (no prices were substituted).",
            ["market_rules", "yield_rules"],
        ))

    calendar = view.calendar
    if not calendar or not calendar.is_crop_calendar_available:
        if farm.current_growth_stage:
            notices.append(_notice(
                DataQualityIssueType.MISSING_DATA, "crop_calendar",
                "Crop calendar data was unavailable; the farmer-supplied "
                "growth stage was used for context, but calendar-derived "
                "dates, stage transitions and harvest windows were skipped.",
                ["crop_stage_rules", "harvest_rules"],
            ))
        else:
            notices.append(_notice(
                DataQualityIssueType.MISSING_DATA, "crop_calendar",
                "Crop calendar data was unavailable; crop-stage-specific "
                "risk and opportunity analysis was skipped (no stage was "
                "assumed).",
                ["crop_stage_rules", "harvest_rules"],
            ))
    elif not calendar.current_growth_stage:
        notices.append(_notice(
            DataQualityIssueType.MISSING_FIELD, "crop_calendar",
            "The crop calendar did not report a current growth stage; "
            "stage-specific amplification was not applied.",
            ["crop_stage_rules"],
        ))

    if view.context.decision_engine_output is None:
        notices.append(_notice(
            DataQualityIssueType.MISSING_DATA, "decision_engine",
            "Decision Engine output was not supplied; upstream decisions "
            "were not attributed and the analysis ran on direct signals "
            "only.",
            ["decision_engine_attribution"],
        ))

    for model in _unavailable_ml_models(farm):
        notices.append(_notice(
            DataQualityIssueType.UNAVAILABLE_MODEL, model,
            f"ML model '{model}' reported status unavailable/error; its "
            "signal was not fabricated and no risk or opportunity was "
            "derived from it.",
            [model],
        ))

    for source in view.stale_sources:
        notices.append(_notice(
            DataQualityIssueType.STALE_DATA, source,
            f"Source '{source}' reported a freshness timestamp older than "
            f"the documented threshold ({STALENESS_DAYS_THRESHOLD} days); "
            "items depending on it are marked 'monitoring' and their "
            "confidence was downgraded.",
            [source],
        ))

    yield_prediction = view.ml("crop_yield_prediction")
    if yield_prediction is not None and view.market and \
            view.market.is_market_data_available and \
            _yield_hint(yield_prediction) is None:
        notices.append(_notice(
            DataQualityIssueType.INSUFFICIENT_BASELINE,
            "crop_yield_prediction",
            "The yield model did not report a comparative yield signal "
            "(for example yield_status or expected_change_percent), so the "
            "yield-versus-market comparison was skipped; the numeric "
            "prediction alone is not interpreted by this layer.",
            ["yield_rules"],
        ))

    return notices


def _assess_data_quality(
    farm: FarmContext, conflicts: Sequence[ConflictNotice],
) -> DataQuality:
    """
    Deterministic data-quality assessment.

    Mirrors the Decision Engine's documented methodology (same expected
    source count, same completeness formula, same staleness threshold) so
    both layers report consistent semantics. ``conflicts`` carries this
    layer's conflict notice IDs.
    """
    available = _available_source_names(farm)
    missing = sorted({"weather", "market", "crop_calendar"} - set(available))
    unavailable_ml = _unavailable_ml_models(farm)
    stale = _stale_sources(farm)

    available_ml = len(farm.ml_predictions) - len(unavailable_ml)
    present = len(available) + max(0, available_ml)
    completeness = round(
        min(100.0, (present / EXPECTED_SOURCE_COUNT) * 100.0), 1,
    ) if present > 0 else 0.0

    ml_available = any(p.status == "available" for p in farm.ml_predictions)
    if conflicts:
        status = DecisionStatus.conflicting_signals.value
    elif not available and not ml_available:
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
        conflicts=sorted(c.id for c in conflicts),
        unavailable_ml_models=unavailable_ml,
        missing_critical_fields=[],
    )


def _analysis_status(
    farm: FarmContext, conflicts: Sequence[ConflictNotice],
) -> DecisionStatus:
    """
    Overall analysis status (reuses the project's documented vocabulary):
    conflicting_signals > insufficient_context > complete_context >
    partial_context.
    """
    if conflicts:
        return DecisionStatus.conflicting_signals
    available = _available_source_names(farm)
    ml_available = any(p.status == "available" for p in farm.ml_predictions)
    if not available and not ml_available:
        return DecisionStatus.insufficient_context
    if set(available) == {"weather", "market", "crop_calendar"}:
        return DecisionStatus.complete_context
    return DecisionStatus.partial_context


# =============================================================================
# Grading to public objects
# =============================================================================


def _single_source_model(
    view: _AnalysisView, evidence: Sequence[SupportingSignal],
) -> Tuple[Optional[MLPrediction], Optional[float]]:
    """
    The ML prediction when it is an item's ONLY corroborating source.

    Enables reusing the model's own reported probability with attribution
    instead of inventing a confidence value.
    """
    corroborating = sorted({
        e.source for e in evidence if e.source in CORROBORATING_SOURCES
    })
    if len(corroborating) != 1:
        return None, None
    name = corroborating[0]
    if name not in KNOWN_ML_MODELS:
        return None, None
    prediction = view.ml(name)
    if prediction is None:
        return None, None
    return prediction, _model_probability(prediction)


def _evidence_is_stale(view: _AnalysisView, candidate: _Candidate) -> bool:
    """Whether any contributing source of the item is stale."""
    contributing = {e.source for e in candidate.evidence}
    contributing.update(s.source for s in candidate.sources)
    return any(source in view.stale_sources for source in contributing)


def _grade_risk(view: _AnalysisView, candidate: _Candidate) -> Risk:
    """Deterministic grading of a consolidated risk candidate."""
    evidence = _dedupe_signals(candidate.evidence)
    sources = _dedupe_sources(candidate.sources)
    source_count = _independent_source_count(evidence)
    stale = _evidence_is_stale(view, candidate)

    severity = _severity_for_risk(
        source_count=source_count,
        elevated=candidate.elevated,
        sensitive=candidate.sensitive,
        time_sensitive=candidate.time_sensitive,
        upstream_priority=candidate.upstream_priority,
        severe=candidate.severe,
    )
    priority = _priority_for_risk(
        severity,
        sensitive=candidate.sensitive,
        time_sensitive=candidate.time_sensitive,
        actionable=bool(candidate.action),
    )
    single_model, single_probability = _single_source_model(view, evidence)
    confidence, value, source, rationale = _confidence_for(
        source_count=source_count,
        ml_probability=candidate.ml_probability,
        upstream_confidence=candidate.upstream_confidence,
        upstream_confidence_rationale=candidate.upstream_confidence_rationale,
        stale=stale,
        single_source_model=single_model,
        single_source_probability=single_probability,
    )

    return Risk(
        id=_item_id("risk", candidate.key, view.farm),
        category=RiskCategory(candidate.category),
        title=candidate.title,
        description=candidate.description,
        severity=severity,
        priority=priority,
        status=ItemStatus.MONITORING if stale else ItemStatus.ACTIVE,
        confidence=confidence,
        numerical_confidence=value,
        confidence_source=source,
        confidence_rationale=rationale,
        affected_crop=view.crop,
        affected_stage=candidate.stage,
        evidence=evidence,
        contributing_sources=sources,
        contributing_signals=sorted({e.signal for e in evidence}),
        reasoning=candidate.reasoning,
        recommended_follow_up=candidate.action,
        detected_at=_utc_now_iso(),
        valid_until=candidate.valid_until,
    )


def _grade_opportunity(
    view: _AnalysisView, candidate: _Candidate,
) -> Opportunity:
    """Deterministic grading of a consolidated opportunity candidate."""
    evidence = _dedupe_signals(candidate.evidence)
    sources = _dedupe_sources(candidate.sources)
    source_count = _independent_source_count(evidence)
    stale = _evidence_is_stale(view, candidate)

    priority = _priority_for_opportunity(
        source_count=source_count, time_bound=candidate.time_bound,
    )
    single_model, single_probability = _single_source_model(view, evidence)
    confidence, value, source, rationale = _confidence_for(
        source_count=source_count,
        ml_probability=candidate.ml_probability,
        upstream_confidence=candidate.upstream_confidence,
        upstream_confidence_rationale=candidate.upstream_confidence_rationale,
        stale=stale,
        single_source_model=single_model,
        single_source_probability=single_probability,
    )

    return Opportunity(
        id=_item_id("opportunity", candidate.key, view.farm),
        category=OpportunityCategory(candidate.category),
        title=candidate.title,
        description=candidate.description,
        priority=priority,
        status=ItemStatus.MONITORING if stale else ItemStatus.ACTIVE,
        confidence=confidence,
        numerical_confidence=value,
        confidence_source=source,
        confidence_rationale=rationale,
        affected_crop=view.crop,
        affected_stage=candidate.stage,
        evidence=evidence,
        contributing_sources=sources,
        contributing_signals=sorted({e.signal for e in evidence}),
        reasoning=candidate.reasoning,
        suggested_action=candidate.action,
        time_window=candidate.time_window,
        detected_at=_utc_now_iso(),
    )


def _summary(
    risks: Sequence[Risk],
    opportunities: Sequence[Opportunity],
    notices: Sequence[DataQualityNotice],
    conflicts: Sequence[ConflictNotice],
) -> RiskOpportunitySummary:
    """Deterministic summary statistics."""
    risk_counts: Dict[str, int] = {}
    for risk in risks:
        risk_counts[risk.category.value] = (
            risk_counts.get(risk.category.value, 0) + 1
        )
    opportunity_counts: Dict[str, int] = {}
    for opportunity in opportunities:
        opportunity_counts[opportunity.category.value] = (
            opportunity_counts.get(opportunity.category.value, 0) + 1
        )

    return RiskOpportunitySummary(
        risk_count=len(risks),
        opportunity_count=len(opportunities),
        data_quality_notice_count=len(notices),
        conflict_notice_count=len(conflicts),
        risk_count_by_category=dict(sorted(risk_counts.items())),
        opportunity_count_by_category=dict(sorted(opportunity_counts.items())),
        highest_risk_severity=(
            min(risks, key=lambda r: SEVERITY_ORDER[r.severity]).severity
            if risks else None
        ),
        highest_risk_priority=(
            min(risks, key=lambda r: PRIORITY_ORDER[r.priority]).priority
            if risks else None
        ),
        highest_opportunity_priority=(
            min(
                opportunities, key=lambda o: PRIORITY_ORDER[o.priority],
            ).priority
            if opportunities else None
        ),
    )


# =============================================================================
# Engine entry point
# =============================================================================

# Documented rule order (deterministic; also used for merge tie-breaks when
# two contributors of the same consolidation key are both non-primary).
RISK_RULES = (
    _rule_excess_rainfall,
    _rule_heat_stress,
    _rule_cold_stress,
    _rule_wind_damage,
    _rule_severe_weather,
    _rule_water_stress,
    _rule_disease_favourable_weather,
    _rule_disease_model,
    _rule_pest_pressure,
    _rule_soil_condition,
    _rule_market_downside,
    _rule_yield_market_risk,
    _rule_fertilizer_risk,
    _rule_stage_transition_risk,
)

OPPORTUNITY_RULES = (
    _rule_favourable_weather_window,
    _rule_irrigation_efficiency,
    _rule_reduced_disease_pressure,
    _rule_reduced_pest_pressure,
    _rule_market_upside,
    _rule_yield_market_opportunity,
    _rule_fertilizer_window,
    _rule_stage_transition_opportunity,
    _rule_harvest_window,
)


def analyze_risk_opportunity(
    context: RiskOpportunityContext,
) -> RiskOpportunityResponse:
    """
    Deterministic risk & opportunity analysis.

    Order of operations:
    1. Extract weather signals (empty when weather is unavailable).
    2. Resolve the effective growth stage (calendar first, farmer fallback).
    3. Detect conflicting upstream signals.
    4. Run the documented risk and opportunity rules over the context view.
    5. Consolidate candidates per underlying condition (duplicate
       suppression), then grade severity/priority/confidence in one place.
    6. Assess data quality, collect notices and sort deterministically.
    """
    farm = context.farm_context
    signals = _weather_signals(farm)
    stage = _effective_stage(farm)
    view = _AnalysisView(context, signals, stage)

    conflicts = _detect_conflicts(view)

    risk_candidates: List[_Candidate] = []
    for rule in RISK_RULES:
        risk_candidates.extend(rule(view))
    conflict_candidate = _conflict_risk(view, conflicts)
    if conflict_candidate is not None:
        risk_candidates.append(conflict_candidate)

    opportunity_candidates: List[_Candidate] = []
    for rule in OPPORTUNITY_RULES:
        opportunity_candidates.extend(rule(view))

    risks = [
        _grade_risk(view, candidate)
        for candidate in _consolidate(risk_candidates)
    ]
    opportunities = [
        _grade_opportunity(view, candidate)
        for candidate in _consolidate(opportunity_candidates)
    ]
    risks.sort(key=lambda risk: (
        SEVERITY_ORDER[risk.severity],
        PRIORITY_ORDER[risk.priority],
        risk.category.value,
        risk.title,
    ))
    opportunities.sort(key=lambda opportunity: (
        PRIORITY_ORDER[opportunity.priority],
        CONFIDENCE_ORDER[opportunity.confidence],
        opportunity.category.value,
        opportunity.title,
    ))

    notices = _data_quality_notices(view)
    data_quality = _assess_data_quality(farm, conflicts)
    status = _analysis_status(farm, conflicts)

    return RiskOpportunityResponse(
        status=status,
        risks=risks,
        opportunities=opportunities,
        data_quality=data_quality,
        data_quality_notices=notices,
        conflict_notices=conflicts,
        summary=_summary(risks, opportunities, notices, conflicts),
        engine_version=ENGINE_VERSION,
        ruleset_version=RULESET_VERSION,
        analysis_timestamp=_utc_now_iso(),
        total_risks=len(risks),
        total_opportunities=len(opportunities),
    )
