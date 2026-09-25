"""
Smart Alerts - deterministic alert-intelligence layer.

Sits AFTER Risk & Opportunity Analysis, BEFORE frontend / AI assistant.
Converts important risks / opportunities / conflicts / data-quality
conditions into concise, traceable alerts.

PRINCIPLES: deterministic, explainable, no external calls, no ML calls,
no invented facts/confidence/actions/validity. Transforms + prioritizes
existing intelligence only.

PRIORITY POLICY (documented, deterministic):
- risk critical/high -> always alert
- risk medium -> alert iff actionable (recommended_follow_up non-empty
  OR valid_until present OR time-sensitive wording in reasoning/
  follow-up OR monitoring status is NOT sufficient alone)
- risk low -> suppress
- opportunity high -> alert
- opportunity medium -> alert iff actionable (suggested_action
  non-empty OR time_window present)
- opportunity low -> suppress
- conflict -> alert iff important/unresolved: detected_by present and
  (recommended_action non-empty OR unresolved_reason non-empty).
  Empty boilerplate conflicts (no action and no reason) suppress.
- data_quality -> alert iff material: affected_analysis non-empty OR
  type in (missing_data, stale_data, unavailable_model). Purely
  informational notices (limited_coverage/insufficient_baseline with
  empty affected_analysis, or missing_field) suppress.

CRITICAL SAFETY: max_alerts truncation never drops CRITICAL alerts.
SORT: priority (critical>high>medium>low), then type
(risk>conflict>opportunity>data_quality), then id.
DEDUPE: sha256(alert_type|source_id|category|crop|stage); first wins.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.decision import DecisionStatus
from app.schemas.risk_opportunity import (
    ConflictNotice,
    DataQualityIssueType,
    DataQualityNotice,
    Opportunity,
    Risk,
    RiskOpportunityResponse,
)
from app.schemas.smart_alert import (
    AlertPriority,
    AlertSeverity,
    AlertSourceType,
    AlertStatus,
    AlertType,
    SmartAlert,
    SmartAlertPreferences,
    SmartAlertResponse,
)

ENGINE_VERSION = "1.0.0"
RULESET_VERSION = "1.0.0"

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
TYPE_ORDER = {"risk": 0, "conflict": 1, "opportunity": 2, "data_quality": 3}

_MATERIAL_DQ_TYPES = frozenset({"missing_data", "stale_data", "unavailable_model"})

RULES = [
    ("risk.critical.always_alert", "CRITICAL risks always generate an alert."),
    ("risk.high.always_alert", "HIGH risks always generate an alert."),
    ("risk.medium.actionable_only", "MEDIUM risks alert only when actionable (follow-up, valid_until, or time sensitivity)."),
    ("risk.low.suppress", "LOW risks are normally suppressed."),
    ("opportunity.high.always_alert", "HIGH opportunities always generate an alert."),
    ("opportunity.medium.actionable_only", "MEDIUM opportunities alert only with suggested action or time window."),
    ("opportunity.low.suppress", "LOW opportunities are normally suppressed."),
    ("conflict.important_only", "Important/unresolved conflicts generate alerts; empty boilerplate is suppressed."),
    ("data_quality.material_only", "Material data-quality notices generate alerts; minor/informational ones are suppressed."),
    ("critical.survives_max_alerts", "CRITICAL alerts are never removed by max_alerts truncation."),
    ("dedupe.stable_sha256", "Repeated identical upstream signals share one alert via stable SHA-256 dedupe key."),
    ("sort.deterministic", "Alerts sort by priority, then type (risk>conflict>opportunity>data_quality), then id."),
]

def _norm(value) -> str:
    return (value or "").strip().lower() if isinstance(value, str) else ""


def _has_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_time_sensitive(*texts) -> bool:
    blob = " ".join(_norm(t) for t in texts if isinstance(t, str))
    keys = ("urgent", "immediate", "time-sensitive", "time sensitive",
            "days", "week", "window", "before", "within", "harvest",
            "flowering", "sensitive stage")
    return any(k in blob for k in keys)


def dedupe_key_for(alert_type: str, source_id: str, category: str,
                   crop, stage) -> str:
    parts = [alert_type or "", source_id or "", category or "",
             _norm(crop), _norm(stage)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _alert_id(alert_type: str, source_id: str, dedupe_key: str) -> str:
    prefix = {"risk": "sa-risk", "opportunity": "sa-opp",
              "conflict": "sa-conflict", "data_quality": "sa-dq"}.get(alert_type, "sa")
    return f"{prefix}-{hashlib.sha256((source_id + dedupe_key).encode()).hexdigest()[:12]}"


def _risk_actionable(risk: Risk) -> bool:
    if _has_text(risk.recommended_follow_up) or risk.valid_until:
        return True
    return _is_time_sensitive(risk.recommended_follow_up, risk.reasoning,
                              risk.description, risk.title)


def _opp_actionable(opp: Opportunity) -> bool:
    return _has_text(opp.suggested_action) or _has_text(opp.time_window)


def _conflict_important(conf: ConflictNotice) -> bool:
    return _has_text(conf.recommended_action) or _has_text(conf.unresolved_reason)


def _dq_material(notice: DataQualityNotice) -> bool:
    if notice.affected_analysis:
        return True
    try:
        return notice.type.value in _MATERIAL_DQ_TYPES
    except AttributeError:
        return str(notice.type) in _MATERIAL_DQ_TYPES


def _should_include_risk(risk: Risk):
    pri = _norm(risk.priority.value if hasattr(risk.priority, "value") else risk.priority)
    if pri in ("critical", "high"):
        return True, "always_alert"
    if pri == "medium":
        ok = _risk_actionable(risk)
        return ok, ("actionable" if ok else "medium_not_actionable")
    return False, "low_suppressed"


def _should_include_opp(opp: Opportunity):
    pri = _norm(opp.priority.value if hasattr(opp.priority, "value") else opp.priority)
    if pri == "high":
        return True, "always_alert"
    if pri == "medium":
        ok = _opp_actionable(opp)
        return ok, ("actionable" if ok else "medium_not_actionable")
    return False, "low_suppressed"

def _message_for_risk(risk: Risk) -> str:
    sev = _norm(risk.severity.value if hasattr(risk.severity, "value") else risk.severity)
    cat = risk.category.value if hasattr(risk.category, "value") else str(risk.category)
    base = f"{(sev.capitalize() if sev else 'Identified')} {cat} risk: {risk.title}."
    crop = (risk.affected_crop or "").strip()
    stage = (risk.affected_stage or "").strip()
    if crop and stage:
        base += f" Affects {crop} during {stage}."
    elif crop:
        base += f" Affects {crop}."
    elif stage:
        base += f" During {stage}."
    return base


def _message_for_opp(opp: Opportunity) -> str:
    cat = opp.category.value if hasattr(opp.category, "value") else str(opp.category)
    base = f"{cat} opportunity: {opp.title}."
    if opp.time_window:
        base += f" Window: {opp.time_window}."
    crop = (opp.affected_crop or "").strip()
    if crop:
        base += f" For {crop}."
    return base


def _build_risk_alert(risk: Risk) -> SmartAlert:
    atype = AlertType.RISK.value
    cat = risk.category.value if hasattr(risk.category, "value") else str(risk.category)
    key = dedupe_key_for(atype, risk.id, cat, risk.affected_crop, risk.affected_stage)
    pri = AlertPriority(_norm(risk.priority.value if hasattr(risk.priority, "value") else risk.priority))
    sev_raw = _norm(risk.severity.value if hasattr(risk.severity, "value") else risk.severity)
    st_raw = _norm(risk.status.value if hasattr(risk.status, "value") else risk.status)
    return SmartAlert(
        id=_alert_id(atype, risk.id, key), alert_type=AlertType.RISK,
        priority=pri, severity=AlertSeverity(sev_raw) if sev_raw else None,
        status=AlertStatus(st_raw) if st_raw in ("active", "monitoring") else AlertStatus.ACTIVE,
        category=cat, title=risk.title, message=_message_for_risk(risk),
        recommended_action=risk.recommended_follow_up,
        affected_crop=risk.affected_crop, affected_stage=risk.affected_stage,
        source_id=risk.id, source_type=AlertSourceType.RISK,
        contributing_sources=list(risk.contributing_sources),
        contributing_signals=list(risk.contributing_signals),
        evidence=list(risk.evidence), reasoning=risk.reasoning,
        created_at=risk.detected_at, valid_until=risk.valid_until,
        time_window=None, dedupe_key=key,
    )


def _build_opp_alert(opp: Opportunity) -> SmartAlert:
    atype = AlertType.OPPORTUNITY.value
    cat = opp.category.value if hasattr(opp.category, "value") else str(opp.category)
    key = dedupe_key_for(atype, opp.id, cat, opp.affected_crop, opp.affected_stage)
    pri = AlertPriority(_norm(opp.priority.value if hasattr(opp.priority, "value") else opp.priority))
    st_raw = _norm(opp.status.value if hasattr(opp.status, "value") else opp.status)
    return SmartAlert(
        id=_alert_id(atype, opp.id, key), alert_type=AlertType.OPPORTUNITY,
        priority=pri, severity=None,
        status=AlertStatus(st_raw) if st_raw in ("active", "monitoring") else AlertStatus.ACTIVE,
        category=cat, title=opp.title, message=_message_for_opp(opp),
        recommended_action=opp.suggested_action,
        affected_crop=opp.affected_crop, affected_stage=opp.affected_stage,
        source_id=opp.id, source_type=AlertSourceType.OPPORTUNITY,
        contributing_sources=list(opp.contributing_sources),
        contributing_signals=list(opp.contributing_signals),
        evidence=list(opp.evidence), reasoning=opp.reasoning,
        created_at=opp.detected_at, valid_until=None,
        time_window=opp.time_window, dedupe_key=key,
    )

def _build_conflict_alert(conf: ConflictNotice) -> SmartAlert:
    atype = AlertType.CONFLICT.value
    cat = conf.type.value if hasattr(conf.type, "value") else str(conf.type)
    key = dedupe_key_for(atype, conf.id, cat, None, None)
    return SmartAlert(
        id=_alert_id(atype, conf.id, key), alert_type=AlertType.CONFLICT,
        priority=AlertPriority.HIGH, severity=None, status=AlertStatus.ACTIVE,
        category=cat, title=f"Conflicting signals: {cat.replace('_', ' ')}",
        message=f"{conf.description} {conf.unresolved_reason}".strip(),
        recommended_action=conf.recommended_action,
        affected_crop=None, affected_stage=None,
        source_id=conf.id, source_type=AlertSourceType.CONFLICT,
        contributing_sources=[],
        contributing_signals=[s.signal for s in (conf.conflicting_signals or [])],
        evidence=list(conf.conflicting_signals or []), reasoning=conf.unresolved_reason,
        conflicting_signals=list(conf.conflicting_signals or []),
        conflict_sources=list(conf.sources or []),
        unresolved_reason=conf.unresolved_reason,
        created_at=conf.detected_at, valid_until=None,
        time_window=None, dedupe_key=key,
    )


def _build_dq_alert(notice: DataQualityNotice) -> SmartAlert:
    atype = AlertType.DATA_QUALITY.value
    cat = notice.type.value if hasattr(notice.type, "value") else str(notice.type)
    key = dedupe_key_for(atype, notice.id, cat, None, None)
    return SmartAlert(
        id=_alert_id(atype, notice.id, key), alert_type=AlertType.DATA_QUALITY,
        priority=AlertPriority.MEDIUM, severity=None, status=AlertStatus.MONITORING,
        category=cat, title=f"Data quality: {notice.source} ({cat.replace('_', ' ')})",
        message=notice.message, recommended_action=None,
        affected_crop=None, affected_stage=None,
        source_id=notice.id, source_type=AlertSourceType.DATA_QUALITY,
        contributing_sources=[], contributing_signals=[],
        evidence=[], reasoning=None,
        affected_analysis=list(notice.affected_analysis or []),
        created_at=notice.detected_at, valid_until=None,
        time_window=None, dedupe_key=key,
    )


def _sort_key(alert: SmartAlert):
    return (PRIORITY_ORDER.get(alert.priority.value, 99),
            TYPE_ORDER.get(alert.alert_type.value, 99), alert.id)

def generate_alerts(response: RiskOpportunityResponse,
                    preferences=None) -> SmartAlertResponse:
    prefs = preferences or SmartAlertPreferences()
    min_rank = PRIORITY_ORDER.get(prefs.min_priority.value, 99)
    candidates: List[SmartAlert] = []
    suppressed = 0
    for risk in response.risks or []:
        include, _ = _should_include_risk(risk)
        if not include:
            suppressed += 1
            continue
        alert = _build_risk_alert(risk)
        if PRIORITY_ORDER.get(alert.priority.value, 99) > min_rank:
            suppressed += 1
            continue
        candidates.append(alert)
    if prefs.include_opportunities:
        for opp in response.opportunities or []:
            include, _ = _should_include_opp(opp)
            if not include:
                suppressed += 1
                continue
            alert = _build_opp_alert(opp)
            if PRIORITY_ORDER.get(alert.priority.value, 99) > min_rank:
                suppressed += 1
                continue
            candidates.append(alert)
    else:
        suppressed += len(response.opportunities or [])
    if prefs.include_conflicts:
        for conf in response.conflict_notices or []:
            if not _conflict_important(conf):
                suppressed += 1
                continue
            alert = _build_conflict_alert(conf)
            if PRIORITY_ORDER.get(alert.priority.value, 99) > min_rank:
                suppressed += 1
                continue
            candidates.append(alert)
    else:
        suppressed += len(response.conflict_notices or [])
    if prefs.include_data_quality:
        for notice in response.data_quality_notices or []:
            if not _dq_material(notice):
                suppressed += 1
                continue
            alert = _build_dq_alert(notice)
            if PRIORITY_ORDER.get(alert.priority.value, 99) > min_rank:
                suppressed += 1
                continue
            candidates.append(alert)
    else:
        suppressed += len(response.data_quality_notices or [])
    seen: Dict[str, SmartAlert] = {}
    deduped: List[SmartAlert] = []
    for alert in candidates:
        if alert.dedupe_key in seen:
            suppressed += 1
            continue
        seen[alert.dedupe_key] = alert
        deduped.append(alert)
    deduped.sort(key=_sort_key)
    final = deduped
    if prefs.max_alerts is not None and len(deduped) > prefs.max_alerts:
        critical = [a for a in deduped if a.priority == AlertPriority.CRITICAL]
        rest = [a for a in deduped if a.priority != AlertPriority.CRITICAL]
        slots = max(prefs.max_alerts - len(critical), 0)
        final = critical + rest[:slots]
        final.sort(key=_sort_key)
        suppressed += len(deduped) - len(final)

    def _count(pri: AlertPriority) -> int:
        return sum(1 for a in final if a.priority == pri)

    return SmartAlertResponse(
        status=response.status, alerts=final, total_alerts=len(final),
        critical_count=_count(AlertPriority.CRITICAL),
        high_count=_count(AlertPriority.HIGH),
        medium_count=_count(AlertPriority.MEDIUM),
        low_count=_count(AlertPriority.LOW),
        risk_count=sum(1 for a in final if a.alert_type == AlertType.RISK),
        opportunity_count=sum(1 for a in final if a.alert_type == AlertType.OPPORTUNITY),
        conflict_count=sum(1 for a in final if a.alert_type == AlertType.CONFLICT),
        data_quality_count=sum(1 for a in final if a.alert_type == AlertType.DATA_QUALITY),
        suppressed_count=suppressed,
        engine_version=ENGINE_VERSION, ruleset_version=RULESET_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )




