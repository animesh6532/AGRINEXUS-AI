"""
Pydantic schemas for the Risk & Opportunity Analysis module.

Defines the normalized input context, the structured risk/opportunity
objects, and the responses produced by the deterministic Risk &
Opportunity analysis engine.

Conventions follow the existing weather/market/crop_calendar/decision
schemas (Pydantic v2, Field with examples).

REUSE POLICY (intentionally no duplication):
The Risk & Opportunity layer consumes the SAME normalized contracts
already exposed by the project:

- ``FarmContext``        (Decision Engine input contract)
- ``DecisionResponse``   (Decision Engine output contract)
- ``SupportingSignal``   (evidence entry)
- ``DataQuality``        (data-quality assessment)
- ``DecisionStatus``     (documented context-status vocabulary)

Only the objects that are genuinely new to this layer (risks,
opportunities, data-quality notices, conflict notices, summary) are
defined here.

IMPORTANT SCOPE NOTE:
Risk & Opportunity Analysis is NOT a machine-learning model. It is a
deterministic decision-intelligence layer that consumes the existing
module outputs (Weather Intelligence, Market Forecast, Crop Calendar,
Decision Engine) plus the standardized ML prediction contracts, and
classifies them as risks and opportunities using documented rules.
It never trains, replaces, or reimplements any of the project's ML
models, and it never fabricates data, predictions or confidence values.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Reused upstream contracts (see REUSE POLICY above).
from .decision import (
    DataQuality,
    DecisionResponse,
    DecisionStatus,
    FarmContext,
    SupportingSignal,
)


# =============================================================================
# Enumerations
# =============================================================================


class RiskCategory(str, Enum):
    """Categories of risks the engine can identify."""
    WEATHER = "weather"
    IRRIGATION = "irrigation"
    DISEASE = "disease"
    PEST = "pest"
    SOIL = "soil"
    FERTILIZER = "fertilizer"
    MARKET = "market"
    YIELD = "yield"
    CROP_STAGE = "crop_stage"
    DATA_QUALITY = "data_quality"
    SYSTEM = "system"


class OpportunityCategory(str, Enum):
    """Categories of opportunities the engine can identify."""
    WEATHER = "weather"
    MARKET = "market"
    IRRIGATION = "irrigation"
    CROP_STAGE = "crop_stage"
    DISEASE = "disease"
    PEST = "pest"
    FERTILIZER = "fertilizer"
    YIELD = "yield"
    HARVEST = "harvest"
    DATA = "data"


class SeverityLevel(str, Enum):
    """Deterministic severity levels for risks (documented rules)."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PriorityLevel(str, Enum):
    """Deterministic priority levels for risks and opportunities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    """
    Confidence category.

    ``INSUFFICIENT_EVIDENCE`` is the explicitly documented state used
    when too few independent sources support an item for any confidence
    to be reported (confidence is never invented).
    """
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ConfidenceSource(str, Enum):
    """Where a reported confidence value came from (attribution)."""
    DECISION_ENGINE = "decision_engine"
    ML_MODEL = "ml_model"
    RISK_OPPORTUNITY = "risk_opportunity"


class ItemStatus(str, Enum):
    """
    Lifecycle status of an identified risk/opportunity.

    - active:     currently supported by the available signals
    - monitoring: supported, but reliability is reduced (for example a
                  contributing source is stale) - reported so downstream
                  layers can qualify it instead of dropping it silently
    """
    ACTIVE = "active"
    MONITORING = "monitoring"


class SourceType(str, Enum):
    """
    Source classification for contributing sources.

    This is a documented SUPERSET of the Decision Engine's source
    vocabulary: it adds ``decision_engine`` because this layer consumes
    upstream Decision Engine decisions.
    """
    EXTERNAL_DATA = "external_data"
    ML_MODEL = "ml_model"
    DECISION_ENGINE = "decision_engine"
    FARMER_CONTEXT = "farmer_context"


class DataQualityIssueType(str, Enum):
    """Types of data-quality issues surfaced by the analysis."""
    MISSING_DATA = "missing_data"
    STALE_DATA = "stale_data"
    UNAVAILABLE_MODEL = "unavailable_model"
    MISSING_FIELD = "missing_field"
    INSUFFICIENT_BASELINE = "insufficient_baseline"
    LIMITED_COVERAGE = "limited_coverage"


class ConflictType(str, Enum):
    """Types of conflicting upstream signals the analysis can surface."""
    RAINFALL_VS_IRRIGATION_NEED = "rainfall_vs_irrigation_need"
    MARKET_VS_YIELD = "market_vs_yield"
    OTHER = "other"


class ContributingSource(BaseModel):
    """A data source that contributed to a risk/opportunity identification."""
    source: str = Field(
        ..., description="Source identifier", example="weather",
    )
    source_type: SourceType = Field(
        ...,
        description="external_data | ml_model | decision_engine | "
                    "farmer_context",
        example="external_data",
    )
    detail: Optional[str] = Field(
        None,
        description="What this source contributed",
        example="Forecast precipitation and humidity signals",
    )


# =============================================================================
# Input context
# =============================================================================


class RiskOpportunityContext(BaseModel):
    """
    Normalized input context for Risk & Opportunity Analysis.

    The context deliberately EMBEDS the existing Decision Engine contracts
    instead of redefining them:

    - ``farm_context``:  the normalized FarmContext already exposed by the
      Context/Decision Engine (crop, location, sowing date, normalized
      weather/market/crop-calendar signals, standardized ML predictions,
      optional data-freshness timestamps).
    - ``decision_engine_output``: the Decision Engine's structured response
      for the same farm context, consumed (and attributed) rather than
      recomputed.

    Everything is optional apart from ``farm_context`` itself, so the
    analysis degrades gracefully: missing data produces data-quality
    notices - never fabricated values.
    """
    farm_context: FarmContext = Field(
        ...,
        description="Normalized farm context (Decision Engine input "
                    "contract: crop/location/weather/market/crop-calendar "
                    "signals + standardized ML predictions)",
    )
    decision_engine_output: Optional[DecisionResponse] = Field(
        None,
        description="Structured Decision Engine output for the same "
                    "context. Consumed and attributed; never recomputed. "
                    "When absent, the analysis runs on direct signals and "
                    "reports the absence as a data-quality notice.",
    )
    source_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional free-form provenance metadata supplied by "
                    "the caller (informational only; never treated as a "
                    "data source).",
    )


# =============================================================================
# Risk & Opportunity objects
# =============================================================================


class Risk(BaseModel):
    """
    A structured risk identification with traceable evidence.

    Every risk is traceable: ``reasoning`` explains WHY it exists,
    ``evidence`` lists the supporting signals (each stamped with its
    source) and ``contributing_sources`` identifies the upstream modules
    that contributed. Multi-source signals describing the same underlying
    condition are consolidated into a single risk (duplicate suppression).
    """
    id: str = Field(
        ...,
        description="Deterministic identifier (stable for the same "
                    "context and risk)",
        example="ro-risk-1f4c2a9d3b7e",
    )
    category: RiskCategory = Field(
        ..., description="Category of risk", example="disease",
    )
    title: str = Field(
        ..., description="Short risk title",
        example="Elevated Disease Pressure",
    )
    description: str = Field(
        ..., description="Detailed description of the risk",
    )
    severity: SeverityLevel = Field(
        ...,
        description="Deterministic severity (documented rule ladder; NOT "
                    "a calibrated probability)",
        example="high",
    )
    priority: PriorityLevel = Field(
        ...,
        description="Deterministic priority (severity + time sensitivity "
                    "+ upstream Decision Engine priority)",
        example="high",
    )
    status: ItemStatus = Field(
        ...,
        description="active | monitoring (reduced reliability)",
        example="active",
    )
    confidence: ConfidenceLevel = Field(
        ...,
        description="Confidence category. insufficient_evidence when too "
                    "few independent sources support this risk.",
        example="medium",
    )
    numerical_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Numeric confidence, only when it is reused from an "
                    "upstream source or derived with the documented "
                    "deterministic method (never invented)",
        example=0.7,
    )
    confidence_source: Optional[ConfidenceSource] = Field(
        None,
        description="Where numerical_confidence came from (attribution)",
        example="decision_engine",
    )
    confidence_rationale: str = Field(
        ...,
        description="Why this confidence (or absence of confidence) was "
                    "reported",
    )
    affected_crop: Optional[str] = Field(None, example="rice")
    affected_stage: Optional[str] = Field(
        None,
        description="Growth stage affected by this risk (only when the "
                    "crop calendar or farmer context provided one)",
        example="flowering",
    )
    evidence: List[SupportingSignal] = Field(
        default_factory=list,
        description="Evidence signals supporting this risk (traceable: "
                    "signal + source + description + value)",
    )
    contributing_sources: List[ContributingSource] = Field(
        default_factory=list,
        description="Upstream sources that contributed to this risk",
    )
    contributing_signals: List[str] = Field(
        default_factory=list,
        description="Machine-readable names of the contributing signals",
        example=["high_humidity", "disease_model_elevated_probability"],
    )
    reasoning: str = Field(
        ...,
        description="Explainable reasoning: which signals, which sources, "
                    "and why the risk was identified",
    )
    recommended_follow_up: Optional[str] = Field(
        None,
        description="Follow-up action derived only from the upstream "
                    "signals (no new agronomic advice is invented)",
        example="Increase disease scouting frequency for the current stage",
    )
    detected_at: str = Field(
        ..., description="Identification timestamp (ISO-8601, UTC)",
        example="2026-09-19T10:30:00+00:00",
    )
    valid_until: Optional[str] = Field(
        None,
        description="End of the validity window when derivable from the "
                    "upstream data (e.g. the weather forecast horizon); "
                    "otherwise null",
        example="2026-09-26T10:30:00+00:00",
    )


class Opportunity(BaseModel):
    """
    A structured opportunity identification with traceable evidence.

    Every opportunity is traceable: ``reasoning`` explains WHY it exists,
    ``evidence`` lists the supporting signals (each stamped with its
    source) and ``contributing_sources`` identifies the upstream modules
    that contributed.
    """
    id: str = Field(
        ...,
        description="Deterministic identifier (stable for the same "
                    "context and opportunity)",
        example="ro-opp-8c1d0f4a2b6e",
    )
    category: OpportunityCategory = Field(
        ..., description="Category of opportunity", example="weather",
    )
    title: str = Field(
        ..., description="Short opportunity title",
        example="Favourable Weather Window",
    )
    description: str = Field(
        ..., description="Detailed description of the opportunity",
    )
    priority: PriorityLevel = Field(
        ...,
        description="Deterministic priority (documented rules)",
        example="medium",
    )
    status: ItemStatus = Field(
        ..., description="active | monitoring (reduced reliability)",
        example="active",
    )
    confidence: ConfidenceLevel = Field(
        ...,
        description="Confidence category. insufficient_evidence when too "
                    "few independent sources support this opportunity.",
        example="medium",
    )
    numerical_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Numeric confidence, only when reused from an upstream "
                    "source or derived with the documented deterministic "
                    "method (never invented)",
    )
    confidence_source: Optional[ConfidenceSource] = Field(
        None, description="Where numerical_confidence came from",
    )
    confidence_rationale: str = Field(
        ...,
        description="Why this confidence (or absence of confidence) was "
                    "reported",
    )
    affected_crop: Optional[str] = Field(None, example="rice")
    affected_stage: Optional[str] = Field(None, example="tillering")
    evidence: List[SupportingSignal] = Field(
        default_factory=list,
        description="Evidence signals supporting this opportunity",
    )
    contributing_sources: List[ContributingSource] = Field(
        default_factory=list,
        description="Upstream sources that contributed to this opportunity",
    )
    contributing_signals: List[str] = Field(
        default_factory=list,
        description="Machine-readable names of the contributing signals",
    )
    reasoning: str = Field(
        ...,
        description="Explainable reasoning: which signals, which sources, "
                    "and why the opportunity was identified",
    )
    suggested_action: Optional[str] = Field(
        None,
        description="Action derived only from the upstream signals "
                    "(no new agronomic advice is invented)",
        example="Plan field operations inside the identified window",
    )
    time_window: Optional[str] = Field(
        None,
        description="Window in which the opportunity applies, when it is "
                    "derivable from the upstream data",
        example="2026-10-17 to 2026-11-06",
    )
    detected_at: str = Field(
        ..., description="Identification timestamp (ISO-8601, UTC)",
        example="2026-09-19T10:30:00+00:00",
    )


# =============================================================================
# Data quality & conflict notices
# =============================================================================


class DataQualityNotice(BaseModel):
    """
    A data-quality notice reporting how missing/stale/unavailable data
    affected the analysis. Notices never contain substituted values: they
    state what was skipped and why.
    """
    id: str = Field(
        ..., description="Deterministic identifier",
        example="ro-dq-3a91c07be4d2",
    )
    type: DataQualityIssueType = Field(
        ..., description="Type of data-quality issue", example="missing_data",
    )
    source: str = Field(
        ..., description="Source/module the issue relates to",
        example="weather",
    )
    message: str = Field(
        ...,
        description="Human-readable explanation of the issue and its "
                    "impact on the analysis",
        example="Weather data unavailable; weather-related risks and "
                "opportunities were skipped (no values were substituted).",
    )
    affected_analysis: List[str] = Field(
        default_factory=list,
        description="Analysis groups skipped or qualified because of this "
                    "issue (e.g. ['weather_rules', 'disease_rules'])",
        example=["weather_rules"],
    )
    detected_at: str = Field(
        ..., description="Detection timestamp (ISO-8601, UTC)",
        example="2026-09-19T10:30:00+00:00",
    )


class ConflictNotice(BaseModel):
    """
    A structured indication that upstream signals disagree.

    Conflicts are reported explicitly - the analysis never silently picks
    one side. ``unresolved_reason`` explains why the system cannot
    confidently resolve them from the supplied data.
    """
    id: str = Field(
        ..., description="Deterministic identifier",
        example="ro-conflict-77b0c1a5d9e3",
    )
    type: ConflictType = Field(
        ...,
        description="rainfall_vs_irrigation_need | market_vs_yield | other",
        example="rainfall_vs_irrigation_need",
    )
    description: str = Field(
        ...,
        description="Description of the conflicting signals",
        example="Weather forecasts significant rainfall while the smart "
                "irrigation model reports irrigation need for the same "
                "window.",
    )
    conflicting_signals: List[SupportingSignal] = Field(
        default_factory=list,
        description="The conflicting signals with their sources",
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Sources involved in the conflict",
        example=["weather", "smart_irrigation"],
    )
    detected_by: str = Field(
        ...,
        pattern="^(decision_engine|risk_opportunity)$",
        description="Which layer detected the conflict (attribution)",
        example="decision_engine",
    )
    unresolved_reason: str = Field(
        ...,
        description="Why the conflict cannot be confidently resolved from "
                    "the supplied data",
    )
    recommended_action: str = Field(
        ...,
        description="Action derived from the conflict (no new agronomic "
                    "advice is invented)",
        example="Verify in-field soil moisture before acting on either "
                "signal.",
    )
    detected_at: str = Field(
        ..., description="Detection timestamp (ISO-8601, UTC)",
        example="2026-09-19T10:30:00+00:00",
    )


# =============================================================================
# Analysis responses
# =============================================================================


class RiskOpportunitySummary(BaseModel):
    """Summary statistics of a risk & opportunity analysis."""
    risk_count: int = Field(..., ge=0, example=3)
    opportunity_count: int = Field(..., ge=0, example=2)
    data_quality_notice_count: int = Field(..., ge=0, example=1)
    conflict_notice_count: int = Field(..., ge=0, example=0)
    risk_count_by_category: Dict[str, int] = Field(
        default_factory=dict,
        description="Risk count per category value",
        example={"disease": 1, "weather": 2},
    )
    opportunity_count_by_category: Dict[str, int] = Field(
        default_factory=dict,
        description="Opportunity count per category value",
        example={"market": 1},
    )
    highest_risk_severity: Optional[SeverityLevel] = Field(
        None,
        description="Highest severity among the identified risks "
                    "(null when no risks were identified)",
        example="high",
    )
    highest_risk_priority: Optional[PriorityLevel] = Field(
        None,
        description="Highest priority among the identified risks",
        example="high",
    )
    highest_opportunity_priority: Optional[PriorityLevel] = Field(
        None,
        description="Highest priority among the identified opportunities",
        example="medium",
    )


class RiskOpportunityResponse(BaseModel):
    """
    Complete Risk & Opportunity analysis response.

    ``status`` reuses the project's documented context-status vocabulary
    (DecisionStatus): complete_context, partial_context,
    insufficient_context, conflicting_signals.
    """
    status: DecisionStatus = Field(
        ..., description="Overall analysis context status",
        example="partial_context",
    )
    risks: List[Risk] = Field(
        default_factory=list,
        description="Structured risk identifications (consolidated, "
                    "sorted by severity then priority)",
    )
    opportunities: List[Opportunity] = Field(
        default_factory=list,
        description="Structured opportunity identifications "
                    "(consolidated, sorted by priority)",
    )
    data_quality: DataQuality = Field(
        ...,
        description="Data-quality assessment (reuses the Decision Engine's "
                    "documented assessment contract)",
    )
    data_quality_notices: List[DataQualityNotice] = Field(
        default_factory=list,
        description="Data-quality issues encountered during analysis",
    )
    conflict_notices: List[ConflictNotice] = Field(
        default_factory=list,
        description="Conflicting upstream signals detected (never silently "
                    "resolved)",
    )
    summary: RiskOpportunitySummary = Field(
        ..., description="Summary statistics",
    )
    engine_version: str = Field(..., example="1.0.0")
    ruleset_version: str = Field(
        ..., description="Deterministic ruleset version", example="1.0.0",
    )
    analysis_timestamp: str = Field(
        ..., description="Analysis timestamp (ISO-8601, UTC)",
        example="2026-09-19T10:30:00+00:00",
    )
    total_risks: int = Field(..., ge=0, example=3)
    total_opportunities: int = Field(..., ge=0, example=2)


class CategoryInfo(BaseModel):
    """A documented category/level supported by the analysis ruleset."""
    value: str = Field(..., example="weather")
    label: str = Field(..., example="Weather")
    description: str = Field(
        ..., description="What this category/level means",
    )


class RiskOpportunityCategoriesResponse(BaseModel):
    """Documented vocabulary of the Risk & Opportunity ruleset."""
    risk_categories: List[CategoryInfo] = Field(default_factory=list)
    opportunity_categories: List[CategoryInfo] = Field(default_factory=list)
    severity_levels: List[CategoryInfo] = Field(default_factory=list)
    priority_levels: List[CategoryInfo] = Field(default_factory=list)
    conflict_types: List[CategoryInfo] = Field(default_factory=list)
    data_quality_issue_types: List[CategoryInfo] = Field(default_factory=list)
    ruleset_version: str = Field(..., example="1.0.0")
    timestamp: str = Field(..., example="2026-09-19T10:30:00+00:00")


class RiskOpportunityHealthResponse(BaseModel):
    """
    Health check response for the Risk & Opportunity Analysis service.

    Reports service/ruleset availability and dependency readiness only.
    Never exposes secrets, API keys, credentials or model artifacts.
    """
    status: str = Field(..., example="healthy")
    service: str = Field(..., example="agrinexus-risk-opportunity")
    version: str = Field(..., example="1.0.0")
    timestamp: str = Field(..., example="2026-09-19T10:30:00+00:00")
    engine_available: bool = Field(
        ..., description="Whether the analysis engine is operational",
        example=True,
    )
    ruleset_version: str = Field(..., example="1.0.0")
    supported_risk_categories: List[str] = Field(default_factory=list)
    supported_opportunity_categories: List[str] = Field(default_factory=list)
    severity_levels: List[str] = Field(default_factory=list)
    priority_levels: List[str] = Field(default_factory=list)
    upstream_dependencies: List[str] = Field(
        default_factory=list,
        description="Upstream contracts this layer consumes (names only)",
        example=["weather", "market", "crop_calendar", "decision_engine"],
    )
    ml_model_contracts_available: List[str] = Field(
        default_factory=list,
        description="Known standardized ML prediction contracts the layer "
                    "can consume (contract names only; no model secrets)",
    )
