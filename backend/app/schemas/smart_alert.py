"""
Pydantic schemas for the Smart Alerts module.

Smart Alerts is a deterministic alert-intelligence layer AFTER Risk &
Opportunity Analysis. It converts important risks, opportunities,
conflicts and data-quality conditions into concise, traceable alerts.

Conventions follow decision / risk_opportunity schemas (Pydantic v2).

REUSE POLICY: SupportingSignal + ContributingSource are REUSED from the
Risk & Opportunity schema; RiskOpportunityResponse is the upstream input
contract (imported, never redefined); DecisionStatus is reused for the
response status vocabulary. Only genuinely new objects are defined here.

SCOPE: NOT an ML model, NO external API calls, NO ML calls, never
fabricates facts/confidence/recommendations/validity periods.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from .decision import DecisionStatus, SupportingSignal
from .risk_opportunity import ContributingSource, RiskOpportunityResponse


class AlertType(str, Enum):
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    CONFLICT = "conflict"
    DATA_QUALITY = "data_quality"


class AlertPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    MONITORING = "monitoring"


class AlertSourceType(str, Enum):
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    CONFLICT = "conflict"
    DATA_QUALITY = "data_quality"


class SmartAlert(BaseModel):
    id: str = Field(..., description="Deterministic alert id")
    alert_type: AlertType = Field(...)
    priority: AlertPriority = Field(...)
    severity: Optional[AlertSeverity] = Field(None)
    status: AlertStatus = Field(...)
    category: str = Field(...)
    title: str = Field(...)
    message: str = Field(...)
    recommended_action: Optional[str] = Field(None)
    affected_crop: Optional[str] = Field(None)
    affected_stage: Optional[str] = Field(None)
    source_id: str = Field(...)
    source_type: AlertSourceType = Field(...)
    contributing_sources: List[ContributingSource] = Field(default_factory=list)
    contributing_signals: List[str] = Field(default_factory=list)
    evidence: List[SupportingSignal] = Field(default_factory=list)
    reasoning: Optional[str] = Field(None)
    conflicting_signals: List[SupportingSignal] = Field(default_factory=list)
    conflict_sources: List[str] = Field(default_factory=list)
    unresolved_reason: Optional[str] = Field(None)
    affected_analysis: List[str] = Field(default_factory=list)
    created_at: str = Field(...)
    valid_until: Optional[str] = Field(None)
    time_window: Optional[str] = Field(None)
    dedupe_key: str = Field(...)


class SmartAlertPreferences(BaseModel):
    min_priority: AlertPriority = Field(default=AlertPriority.LOW)
    include_opportunities: bool = Field(default=True)
    include_conflicts: bool = Field(default=True)
    include_data_quality: bool = Field(default=True)
    max_alerts: Optional[int] = Field(default=None, ge=1)


class SmartAlertRequest(BaseModel):
    risk_opportunity: RiskOpportunityResponse = Field(...)
    preferences: SmartAlertPreferences = Field(default_factory=SmartAlertPreferences)


class SmartAlertResponse(BaseModel):
    status: DecisionStatus = Field(...)
    alerts: List[SmartAlert] = Field(default_factory=list)
    total_alerts: int = Field(..., ge=0)
    critical_count: int = Field(..., ge=0)
    high_count: int = Field(..., ge=0)
    medium_count: int = Field(..., ge=0)
    low_count: int = Field(..., ge=0)
    risk_count: int = Field(..., ge=0)
    opportunity_count: int = Field(..., ge=0)
    conflict_count: int = Field(..., ge=0)
    data_quality_count: int = Field(..., ge=0)
    suppressed_count: int = Field(..., ge=0)
    engine_version: str = Field(...)
    ruleset_version: str = Field(...)
    generated_at: str = Field(...)


class SmartAlertRuleInfo(BaseModel):
    rule: str = Field(...)
    description: str = Field(...)


class SmartAlertRulesResponse(BaseModel):
    ruleset_version: str = Field(...)
    engine_version: str = Field(...)
    rules: List[SmartAlertRuleInfo] = Field(default_factory=list)
    priority_order: List[str] = Field(default_factory=list)
    type_order: List[str] = Field(default_factory=list)
    timestamp: str = Field(...)


class SmartAlertHealthResponse(BaseModel):
    status: str = Field(...)
    service: str = Field(...)
    version: str = Field(...)
    timestamp: str = Field(...)
    engine_available: bool = Field(...)
    ruleset_version: str = Field(...)
    upstream_dependencies: List[str] = Field(default_factory=list)

