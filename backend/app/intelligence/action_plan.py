"""Action Plan engine: deterministic orchestration after Smart Alerts."""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List
from app.schemas.action_plan import (
    ActionPlanItem, ActionPlanPreferences, ActionPlanResponse,
    ActionPriority, ActionSourceType, ActionStatus, ActionType,
)
from app.schemas.decision import DecisionStatus
from app.schemas.risk_opportunity import ConflictNotice, Opportunity, Risk

ENGINE_VERSION = "1.0.0"
RULESET_VERSION = "1.0.0"
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
RULES = [
    ("risk.critical.always_action", "CRITICAL risks always produce an action."),
    ("risk.high.always_action", "HIGH risks always produce an action."),
    ("risk.medium.actionable_only", "MEDIUM risks act only when actionable."),
    ("risk.low.suppress", "LOW risks are normally suppressed."),
    ("opportunity.high.always_action", "HIGH opportunities always act."),
    ("opportunity.medium.actionable_only", "MEDIUM opps act with action/window."),
    ("opportunity.low.suppress", "LOW opportunities are normally suppressed."),
    ("alert.consume_traceably", "Alerts convert preserving source_id chain."),
    ("conflict.needs_review", "Conflicts give NEEDS_REVIEW, never resolved."),
    ("data_quality.preserve_only", "DQ notices preserved, never actionized."),
    ("critical.survives_max_actions", "CRITICAL never removed by max_actions."),
    ("dedupe.stable_sha256", "Same event shares one action via stable key."),
    ("sort.deterministic", "Sort by priority, urgency, type, then id."),
    ("expiry.skip_expired", "Expired upstream items never produce actions."),
]
RK = {
    "irrigation": ("irrigation", "Irrigate the field", "Check soil moisture and irrigate as needed"),
    "weather": ("weather_preparation", "Prepare for adverse weather", "Take protective measures"),
    "disease": ("disease_monitoring", "Inspect crop for disease", "Increase disease scouting"),
    "pest": ("pest_monitoring", "Scout field for pests", "Increase pest scouting"),
    "fertilizer": ("fertilizer_management", "Review fertilizer plan", "Review fertilizer timing"),
    "market": ("market_action", "Review market position", "Review selling decision"),
    "yield": ("crop_monitoring", "Monitor crop performance", "Monitor crop performance"),
    "crop_stage": ("crop_stage_action", "Attend to crop stage needs", "Stage-appropriate operations"),
    "soil": ("field_inspection", "Inspect soil conditions", "Inspect soil conditions"),
    "data_quality": ("general_farm_management", "Review farm records", "Review farm records"),
    "system": ("general_farm_management", "Review farm advisory", "Review the advisory"),
}
OP = {
    "irrigation": ("irrigation", "Use the irrigation efficiency window", "Irrigate in the window if needed"),
    "weather": ("crop_stage_action", "Use the favourable weather window", "Plan operations in the window"),
    "fertilizer": ("fertilizer_management", "Apply fertilizer in the window", "Apply in the window if planned"),
    "market": ("market_action", "Review selling opportunity", "Review selling decision"),
    "harvest": ("harvest_planning", "Prepare for harvest window", "Prepare logistics for harvest"),
    "crop_stage": ("crop_stage_action", "Act on crop stage window", "Stage-appropriate operations"),
    "disease": ("disease_monitoring", "Maintain disease watch", "Maintain routine watch"),
    "pest": ("pest_monitoring", "Maintain pest watch", "Maintain routine watch"),
    "yield": ("harvest_planning", "Plan around yield outlook", "Align harvest and market planning"),
    "data": ("general_farm_management", "Review farm data opportunity", "Review available data"),
}
URG = [("immediately", 0), ("within 6 hours", 1), ("today", 2), ("within 24 hours", 3), ("next 2 days", 4), ("during the current weather window", 5), ("before harvest", 6)]

def _norm(v) -> str:
    return v.strip().lower() if isinstance(v, str) else ""

def _txt(v) -> bool:
    return isinstance(v, str) and bool(v.strip())

def _urg(w) -> int:
    s = _norm(w)
    for k, r in URG:
        if k in s:
            return r
    return 7 if not s else 6

def dedupe_key_for(a, c, e, crop, stage) -> str:
    parts = [a or "", c or "", e or "", _norm(crop), _norm(stage)]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()

def _pri(v) -> str:
    return _norm(v.value if hasattr(v, "value") else v)

def _aid(a, s, k) -> str:
    return "ap-" + a + "-" + hashlib.sha256((s + k).encode()).hexdigest()[:12]

def _exp(vu, now) -> bool:
    if not _txt(vu):
        return False
    try:
        pp = datetime.fromisoformat(str(vu).strip().replace("Z", "+00:00"))
        if pp.tzinfo is None:
            pp = pp.replace(tzinfo=timezone.utc)
        return pp < now
    except Exception:
        return False

def _pers(fc, fr) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if fc is not None:
        for k in ("crop", "variety", "season", "location", "current_growth_stage", "sowing_date"):
            v = getattr(fc, k, None)
            if v not in (None, ""):
                out[k] = str(v)
        cal = getattr(fc, "crop_calendar_context", None)
        if cal is not None:
            if getattr(cal, "current_growth_stage", None) and "current_growth_stage" not in out:
                out["current_growth_stage"] = str(cal.current_growth_stage)
            if getattr(cal, "crop", None) and "crop" not in out:
                out["crop"] = str(cal.crop)
            if getattr(cal, "season", None) and "season" not in out:
                out["season"] = str(cal.season)
    ex = fr.model_dump(exclude_none=True) if fr is not None and hasattr(fr, "model_dump") else (fr or {})
    if isinstance(ex, dict):
        for k, v in ex.items():
            if v in (None, ""):
                continue
            m = "current_growth_stage" if k in ("growth_stage", "stage") else k
            if m in ("crop", "variety", "current_growth_stage", "season", "location", "sowing_date"):
                out.setdefault(m, str(v))
    return out

def _pt(base: str, p: Dict[str, Any]) -> str:
    crop = str(p.get("crop", "") or "").strip()
    if crop and crop.lower() not in base.lower():
        return base + " for " + crop
    return base

def _pr(reason: str, p: Dict[str, Any]) -> str:
    bits = []
    if str(p.get("current_growth_stage", "") or "").strip():
        bits.append("during the " + str(p["current_growth_stage"]) + " stage")
    if str(p.get("season", "") or "").strip():
        bits.append("in the " + str(p["season"]) + " season")
    if str(p.get("variety", "") or "").strip():
        bits.append("for variety " + str(p["variety"]))
    if bits:
        r = reason if reason.rstrip().endswith(".") else reason + "."
        return r + " " + " ".join(bits) + "."
    return reason

def _rok(r: Risk):
    pri = _pri(r.priority)
    if pri in ("critical", "high"):
        return True, "always"
    if pri == "medium":
        blob = _norm(" ".join([str(r.recommended_follow_up or ""), str(r.reasoning or ""), str(r.description or ""), str(r.title or "")]))
        ok = bool(_txt(r.recommended_follow_up) or r.valid_until or any(k in blob for k in ("urgent", "immediate", "time-sensitive", "time sensitive", "days", "week", "window", "before", "within", "harvest", "flowering", "sensitive stage", "scout", "inspect", "irrigat", "monitor", "review")))
        return ok, ("actionable" if ok else "not_actionable")
    return False, "low"

def _ook(o: Opportunity):
    pri = _pri(o.priority)
    if pri == "high":
        return True, "always"
    if pri == "medium":
        ok = bool(_txt(o.suggested_action) or _txt(o.time_window))
        return ok, ("actionable" if ok else "not_actionable")
    return False, "low"

def _rwin(r: Risk):
    if r.valid_until:
        return None
    pri = _pri(r.priority)
    cat = _norm(r.category.value if hasattr(r.category, "value") else r.category)
    if pri == "critical":
        return "immediately"
    if cat == "irrigation":
        return "within 6 hours"
    if pri == "high":
        return "today"
    return "within 24 hours"

def _owin(o: Opportunity):
    if o.time_window:
        return o.time_window
    if _pri(o.priority) == "high":
        return "next 2 days"
    return "during the current weather window"

def _br(r: Risk, p, loc, now) -> ActionPlanItem:
    cat = _norm(r.category.value if hasattr(r.category, "value") else r.category)
    tp, ti, fb = RK.get(cat, ("general_farm_management", r.title, r.description))
    pri = _pri(r.priority)
    act = r.recommended_follow_up.strip() if _txt(r.recommended_follow_up) else fb
    win = _rwin(r)
    st = _norm(r.status.value if hasattr(r.status, "value") else r.status)
    key = dedupe_key_for(tp, cat, r.id, r.affected_crop, r.affected_stage)
    conf = r.confidence.value if hasattr(r.confidence, "value") else str(r.confidence)
    return ActionPlanItem(id=_aid(tp, r.id, key), action_type=ActionType(tp), priority=ActionPriority(pri), status=(ActionStatus.MONITORING if st == "monitoring" else ActionStatus.ACTIVE), title=_pt(ti, p), action=act, reason=_pr(str(r.reasoning) + " Evidence: " + str(r.title) + ".", p), affected_crop=r.affected_crop, affected_stage=r.affected_stage, location=loc, source_id=r.id, source_type=ActionSourceType.RISK, contributing_sources=list(r.contributing_sources or []), contributing_signals=list(r.contributing_signals or []), evidence=list(r.evidence or []), reasoning=r.reasoning, confidence=conf, numerical_confidence=r.numerical_confidence, recommended_time=win, time_window=win, valid_until=r.valid_until, created_at=now.isoformat(), dedupe_key=key)

def _bo(o: Opportunity, p, loc, now) -> ActionPlanItem:
    cat = _norm(o.category.value if hasattr(o.category, "value") else o.category)
    tp, ti, fb = OP.get(cat, ("general_farm_management", o.title, o.description))
    pri = _pri(o.priority)
    act = o.suggested_action.strip() if _txt(o.suggested_action) else fb
    win = _owin(o)
    st = _norm(o.status.value if hasattr(o.status, "value") else o.status)
    key = dedupe_key_for(tp, cat, o.id, o.affected_crop, o.affected_stage)
    conf = o.confidence.value if hasattr(o.confidence, "value") else str(o.confidence)
    return ActionPlanItem(id=_aid(tp, o.id, key), action_type=ActionType(tp), priority=ActionPriority(pri), status=(ActionStatus.MONITORING if st == "monitoring" else ActionStatus.ACTIVE), title=_pt(ti, p), action=act, reason=_pr(str(o.reasoning) + " Evidence: " + str(o.title) + ".", p), affected_crop=o.affected_crop, affected_stage=o.affected_stage, location=loc, source_id=o.id, source_type=ActionSourceType.OPPORTUNITY, contributing_sources=list(o.contributing_sources or []), contributing_signals=list(o.contributing_signals or []), evidence=list(o.evidence or []), reasoning=o.reasoning, confidence=conf, numerical_confidence=o.numerical_confidence, recommended_time=win, time_window=win, valid_until=None, created_at=now.isoformat(), dedupe_key=key)

def _ba(a, p, loc, now):
    stype = _norm(a.alert_type.value if hasattr(a.alert_type, "value") else a.alert_type)
    pri = _pri(a.priority)
    cat = _norm(a.category)
    if stype == "data_quality":
        return None
    if stype == "conflict":
        key = dedupe_key_for("field_inspection", cat, a.source_id, a.affected_crop, a.affected_stage)
        act = a.recommended_action.strip() if _txt(a.recommended_action) else "Verify field conditions before acting"
        rs = _pr((str(a.message) + " " + str(a.unresolved_reason or "")).strip(), p)
        return ActionPlanItem(id=_aid("field_inspection", a.source_id, key), action_type=ActionType.FIELD_INSPECTION, priority=ActionPriority.HIGH, status=ActionStatus.NEEDS_REVIEW, title=_pt("Review field before acting", p), action=act, reason=rs, affected_crop=a.affected_crop, affected_stage=a.affected_stage, location=loc, source_id=a.source_id, source_type=ActionSourceType.ALERT, contributing_sources=list(a.contributing_sources or []), contributing_signals=list(a.contributing_signals or []), evidence=list(a.evidence or []), reasoning=a.reasoning or a.unresolved_reason, confidence=None, numerical_confidence=None, recommended_time=a.time_window, time_window=a.time_window, valid_until=a.valid_until, created_at=now.isoformat(), dedupe_key=key)
    if stype == "risk":
        tp, ti, fb = RK.get(cat, ("general_farm_management", a.title, a.message))
    else:
        tp, ti, fb = OP.get(cat, ("general_farm_management", a.title, a.message))
    act = a.recommended_action.strip() if _txt(a.recommended_action) else fb
    rs = _pr(str(a.message), p) if _txt(a.message) else _pr("Evidence: " + str(a.title) + ".", p)
    key = dedupe_key_for(tp, cat, a.source_id, a.affected_crop, a.affected_stage)
    st = _norm(a.status.value if hasattr(a.status, "value") else a.status)
    sev = getattr(a, "severity", None)
    sv = _norm(sev.value if hasattr(sev, "value") else (sev or ""))
    return ActionPlanItem(id=_aid(tp, a.source_id, key), action_type=ActionType(tp), priority=ActionPriority(pri), status=(ActionStatus.MONITORING if st == "monitoring" else ActionStatus.ACTIVE), title=_pt(ti, p), action=act, reason=rs, affected_crop=a.affected_crop, affected_stage=a.affected_stage, location=loc, source_id=a.source_id, source_type=ActionSourceType.ALERT, contributing_sources=list(a.contributing_sources or []), contributing_signals=list(a.contributing_signals or []), evidence=list(a.evidence or []), reasoning=a.reasoning, confidence=sv or None, numerical_confidence=None, recommended_time=a.time_window, time_window=a.time_window, valid_until=a.valid_until, created_at=now.isoformat(), dedupe_key=key)

def _bc(c: ConflictNotice, p, loc, now) -> ActionPlanItem:
    cat = _norm(c.type.value if hasattr(c.type, "value") else c.type)
    key = dedupe_key_for("field_inspection", cat, c.id, None, None)
    act = c.recommended_action.strip() if _txt(c.recommended_action) else "Verify field conditions before acting"
    rs = _pr((str(c.description) + " " + str(c.unresolved_reason or "")).strip(), p)
    return ActionPlanItem(id=_aid("field_inspection", c.id, key), action_type=ActionType.FIELD_INSPECTION, priority=ActionPriority.HIGH, status=ActionStatus.NEEDS_REVIEW, title=_pt("Review field before acting", p), action=act, reason=rs, affected_crop=None, affected_stage=None, location=loc, source_id=c.id, source_type=ActionSourceType.CONFLICT, contributing_sources=[], contributing_signals=[s.signal for s in (c.conflicting_signals or [])], evidence=list(c.conflicting_signals or []), reasoning=c.unresolved_reason, confidence=None, numerical_confidence=None, recommended_time=None, time_window=None, valid_until=None, created_at=now.isoformat(), dedupe_key=key)

def _skey(a: ActionPlanItem):
    return (PRIORITY_ORDER.get(a.priority.value, 99), _urg(a.time_window), a.action_type.value, a.id)
def generate_action_plan(request) -> ActionPlanResponse:
    prefs = request.preferences or ActionPlanPreferences()
    now = datetime.now(timezone.utc)
    status = DecisionStatus("partial_context")
    for src in (request.smart_alerts, request.risk_opportunity, request.decision):
        if src is not None and getattr(src, "status", None) is not None:
            try:
                status = DecisionStatus(src.status.value if hasattr(src.status, "value") else str(src.status))
            except Exception:
                pass
            break
    p = _pers(request.farm_context, request.farmer_context)
    loc = None
    if request.farm_context is not None and request.farm_context.location:
        loc = request.farm_context.location
    elif isinstance(p.get("location"), str):
        loc = p.get("location")
    ro = request.risk_opportunity
    dq = list(ro.data_quality_notices or []) if ro is not None else []
    cn = list(ro.conflict_notices or []) if ro is not None else []
    cands: List[ActionPlanItem] = []
    supp = 0
    min_rank = PRIORITY_ORDER.get(_pri(prefs.min_priority), 99)
    if ro is not None:
        for r in ro.risks or []:
            if _exp(r.valid_until, now):
                supp += 1
                continue
            ok, _why = _rok(r)
            if not ok:
                supp += 1
                continue
            a = _br(r, p, loc, now)
            if PRIORITY_ORDER.get(a.priority.value, 99) > min_rank:
                supp += 1
                continue
            mon = _norm(r.status.value if hasattr(r.status, "value") else r.status) == "monitoring"
            if mon and not prefs.include_monitoring:
                supp += 1
                continue
            cands.append(a)
        if prefs.include_opportunities:
            for o in ro.opportunities or []:
                ok, _why = _ook(o)
                if not ok:
                    supp += 1
                    continue
                a = _bo(o, p, loc, now)
                if PRIORITY_ORDER.get(a.priority.value, 99) > min_rank:
                    supp += 1
                    continue
                mon = _norm(o.status.value if hasattr(o.status, "value") else o.status) == "monitoring"
                if mon and not prefs.include_monitoring:
                    supp += 1
                    continue
                cands.append(a)
        else:
            supp += len(ro.opportunities or [])
        for c in cn:
            cands.append(_bc(c, p, loc, now))
    if request.smart_alerts is not None:
        for al in request.smart_alerts.alerts or []:
            if _exp(al.valid_until, now):
                supp += 1
                continue
            a = _ba(al, p, loc, now)
            if a is None:
                supp += 1
                continue
            if PRIORITY_ORDER.get(a.priority.value, 99) > min_rank:
                supp += 1
                continue
            cands.append(a)
    if request.decision is not None and ro is None and request.smart_alerts is None:
        from app.schemas.risk_opportunity import ContributingSource as _CS
        for d in request.decision.decisions or []:
            pri = _pri(d.priority)
            if pri == "low":
                supp += 1
                continue
            dt = _norm(d.decision_type.value if hasattr(d.decision_type, "value") else d.decision_type)
            key = dedupe_key_for("general_farm_management", dt, d.id, d.crop, d.growth_stage)
            cands.append(ActionPlanItem(id=_aid("general_farm_management", d.id, key), action_type=ActionType.GENERAL_FARM_MANAGEMENT, priority=ActionPriority(pri), status=ActionStatus.ACTIVE, title=_pt(d.title, p), action=(d.summary if _txt(d.summary) else d.title), reason=_pr(d.reason, p), affected_crop=d.crop, affected_stage=d.growth_stage, location=(loc or d.location), source_id=d.id, source_type=ActionSourceType.DECISION, contributing_sources=[_CS(source=s.source, source_type="decision_engine", detail=s.detail) for s in (d.contributing_sources or [])], contributing_signals=[s.signal for s in (d.supporting_signals or [])], evidence=list(d.supporting_signals or []), reasoning=d.reason, confidence=None, numerical_confidence=d.confidence, recommended_time=None, time_window=None, valid_until=None, created_at=now.isoformat(), dedupe_key=key))
    seen: Dict[str, ActionPlanItem] = {}
    deduped: List[ActionPlanItem] = []
    for a in cands:
        if a.dedupe_key in seen:
            prev = seen[a.dedupe_key]
            prev.contributing_signals = list(dict.fromkeys(list(prev.contributing_signals) + list(a.contributing_signals)))
            have = {(e.signal, e.source) for e in prev.evidence}
            for ev in a.evidence:
                if (ev.signal, ev.source) not in have:
                    prev.evidence.append(ev)
                    have.add((ev.signal, ev.source))
            have_s = {c.source for c in prev.contributing_sources}
            for cs in a.contributing_sources:
                if cs.source not in have_s:
                    prev.contributing_sources.append(cs)
                    have_s.add(cs.source)
            supp += 1
            continue
        seen[a.dedupe_key] = a
        deduped.append(a)
    deduped.sort(key=_skey)
    final = deduped
    if prefs.max_actions is not None and len(deduped) > prefs.max_actions:
        crit = [a for a in deduped if a.priority == ActionPriority.CRITICAL]
        rest = [a for a in deduped if a.priority != ActionPriority.CRITICAL]
        slots = max(prefs.max_actions - len(crit), 0)
        final = crit + rest[:slots]
        final.sort(key=_skey)
        supp += len(deduped) - len(final)
    def _ct(x) -> int:
        return sum(1 for a in final if a.priority == x)
    return ActionPlanResponse(status=status, actions=final, total_actions=len(final), critical_count=_ct(ActionPriority.CRITICAL), high_count=_ct(ActionPriority.HIGH), medium_count=_ct(ActionPriority.MEDIUM), low_count=_ct(ActionPriority.LOW), suppressed_count=supp, data_quality_notices=dq, conflict_notices=cn, engine_version=ENGINE_VERSION, ruleset_version=RULESET_VERSION, generated_at=now.isoformat())
