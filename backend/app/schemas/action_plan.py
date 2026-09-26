"""
Pydantic schemas for the Personalized Action Plan module.

Deterministic orchestration layer AFTER Smart Alerts. Converts
already-processed farm intelligence (Decision Engine output, Risk &
Opportunity analysis, Smart Alerts) plus FarmContext / farmer context
into a prioritized, explainable sequence of concrete actions.

Conventions follow decision / risk_opportunity / smart_alert schemas
(Pydantic v2, Field with examples).

REUSE POLICY: FarmContext, DecisionResponse, DecisionStatus,
SupportingSignal are REUSED from the Decision schema; ContributingSource,
RiskOpportunityResponse, DataQualityNotice, ConflictNotice are REUSED from
the Risk & Opportunity schema; SmartAlertResponse is REUSED from Smart
Alerts. Only genuinely new objects are defined here.

SCOPE: NOT an ML model, NO external API calls, NO ML calls, never
fabricates facts/confidence/dosages/validity periods.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .decision import DecisionResponse, DecisionStatus, FarmContext, SupportingSignal
from .risk_opportunity import (
    ConflictNotice,
    ContributingSource,
    DataQualityNotice,
    RiskOpportunityResponse,
)
from .smart_alert import SmartAlertResponse


class ActionType(str, Enum):
    IRRIGATION = "irrigation"
    CROP_MONITORING = "crop_monitoring"
    DISEASE_MONITORING = "disease_monitoring"
    PEST_MONITORING = "pest_monitoring"
    FERTILIZER_MANAGEMENT = "fertilizer_management"
    WEATHER_PREPARATION = "weather_preparation"
    HARVEST_PLANNING = "harvest_planning"
    MARKET_ACTION = "market_action"
    FIELD_INSPECTION = "field_inspection"
    CROP_STAGE_ACTION = "crop_stage_action"
    GENERAL_FARM_MANAGEMENT = "general_farm_management"


class ActionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(str, Enum):
    ACTIVE = "active"
    MONITORING = "monitoring"
    NEEDS_REVIEW = "needs_review"


class ActionSourceType(str, Enum):
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    ALERT = "alert"
    DECISION = "decision"
    CONFLICT = "conflict"
    DATA_QUALITY = "data_quality"


class ActionPlanItem(BaseModel):
    id: str = Field(..., description="Deterministic action id")
    action_type: ActionType = Field(...)
    priority: ActionPriority = Field(...)
    status: ActionStatus = Field(...)
    title: str = Field(...)
    action: str = Field(..., description="Concrete farmer-facing action")
    reason: str = Field(..., description="Why this action is recommended")
    affected_crop: Optional[str] = Field(None)
    affected_stage: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    source_id: str = Field(..., description="Upstream item traced to")
    source_type: ActionSourceType = Field(...)
    contributing_sources: List[ContributingSource] = Field(default_factory=list)
    contributing_signals: List[str] = Field(default_factory=list)
    evidence: List[SupportingSignal] = Field(default_factory=list)
    reasoning: Optional[str] = Field(None)
    confidence: Optional[str] = Field(None)
    numerical_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    recommended_time: Optional[str] = Field(None)
    time_window: Optional[str] = Field(None)
    valid_until: Optional[str] = Field(None)
    created_at: str = Field(...)
    dedupe_key: str = Field(...)


class ActionPlanPreferences(BaseModel):
    min_priority: ActionPriority = Field(default=ActionPriority.LOW)
    max_actions: Optional[int] = Field(default=None, ge=1)
    include_opportunities: bool = Field(default=True)
    include_monitoring: bool = Field(default=True)


class FarmerContext(BaseModel):
    crop: Optional[str] = Field(None)
    variety: Optional[str] = Field(None)
    growth_stage: Optional[str] = Field(None)
    sowing_date: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    season: Optional[str] = Field(None)
    irrigation_available: Optional[bool] = Field(None)
    farm_constraints: Optional[str] = Field(None)
    preferences: Optional[str] = Field(None)
    model_config = {"extra": "allow"}


class ActionPlanRequest(BaseModel):
    farm_context: Optional[FarmContext] = Field(None)
    decision: Optional[DecisionResponse] = Field(None)
    risk_opportunity: Optional[RiskOpportunityResponse] = Field(None)
    smart_alerts: Optional[SmartAlertResponse] = Field(None)
    farmer_context: Optional[Dict] = Field(None)
    preferences: ActionPlanPreferences = Field(default_factory=ActionPlanPreferences)


class ActionPlanResponse(BaseModel):
    status: DecisionStatus = Field(...)
    actions: List[ActionPlanItem] = Field(default_factory=list)
    total_actions: int = Field(..., ge=0)
    critical_count: int = Field(..., ge=0)
    high_count: int = Field(..., ge=0)
    medium_count: int = Field(..., ge=0)
    low_count: int = Field(..., ge=0)
    suppressed_count: int = Field(..., ge=0)
    data_quality_notices: List[DataQualityNotice] = Field(default_factory=list)
    conflict_notices: List[ConflictNotice] = Field(default_factory=list)
    engine_version: str = Field(...)
    ruleset_version: str = Field(...)
    generated_at: str = Field(...)


class ActionPlanRuleInfo(BaseModel):
    rule: str = Field(...)
    description: str = Field(...)


class ActionPlanCategoriesResponse(BaseModel):
    action_types: List[Dict[str, str]] = Field(default_factory=list)
    priorities: List[str] = Field(default_factory=list)
    source_types: List[str] = Field(default_factory=list)
    ruleset_version: str = Field(...)
    engine_version: str = Field(...)
    timestamp: str = Field(...)


class ActionPlanHealthResponse(BaseModel):
    status: str = Field(...)
    service: str = Field(...)
    version: str = Field(...)
    timestamp: str = Field(...)
    engine_available: bool = Field(...)
    ruleset_version: str = Field(...)
    upstream_dependencies: List[str] = Field(default_factory=list)
