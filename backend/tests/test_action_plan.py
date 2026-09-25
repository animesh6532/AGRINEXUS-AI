"""Tests for Personalized Action Plan (schemas/intelligence/service/API)."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.intelligence.action_plan import ENGINE_VERSION, RULESET_VERSION, dedupe_key_for, generate_action_plan
from app.main import app
from app.schemas.action_plan import ActionPlanPreferences, ActionPlanRequest
from app.schemas.decision import DataQuality, FarmContext, SupportingSignal
from app.schemas.risk_opportunity import (
    ConflictNotice, ConflictType, ContributingSource, DataQualityIssueType,
    DataQualityNotice, ItemStatus, Opportunity, OpportunityCategory,
    PriorityLevel, Risk, RiskCategory, RiskOpportunityResponse,
    RiskOpportunitySummary, SeverityLevel, ConfidenceLevel, SourceType,
)
from app.schemas.smart_alert import AlertPriority, AlertSourceType, AlertStatus, AlertType, SmartAlert
from app.services.action_plan_service import ActionPlanService

client = TestClient(app)
NOW = "2026-09-19T10:30:00+00:00"

def _ev(signal="soil_moisture_low", source="smart_irrigation"):
    return SupportingSignal(signal=signal, source=source, description=signal + " from " + source, value=20.0)

def _cs(source="smart_irrigation", stype=SourceType.ML_MODEL):
    return ContributingSource(source=source, source_type=stype, detail="contrib")

def mk_risk(rid="ro-risk-1", cat=RiskCategory.IRRIGATION, pri=PriorityLevel.HIGH, sev=SeverityLevel.HIGH, crop="rice", stage="flowering", fu="Irrigate the field now", rs="Water stress detected", vu=None, st=ItemStatus.ACTIVE):
    return Risk(id=rid, category=cat, title="Water stress risk", description="desc", severity=sev, priority=pri, status=st, confidence=ConfidenceLevel.MEDIUM, numerical_confidence=0.7, confidence_source="decision_engine", confidence_rationale="r", affected_crop=crop, affected_stage=stage, evidence=[_ev()], contributing_sources=[_cs()], contributing_signals=["soil_moisture_low"], reasoning=rs, recommended_follow_up=fu, detected_at=NOW, valid_until=vu)

def mk_opp(oid="ro-opp-1", cat=OpportunityCategory.MARKET, pri=PriorityLevel.HIGH, act="Consider phased selling"):
    return Opportunity(id=oid, category=cat, title="Market upside", description="desc", priority=pri, status=ItemStatus.ACTIVE, confidence=ConfidenceLevel.MEDIUM, numerical_confidence=0.6, confidence_source="decision_engine", confidence_rationale="r", affected_crop="rice", affected_stage="maturity", evidence=[_ev("price_up", "market")], contributing_sources=[_cs("market", SourceType.EXTERNAL_DATA)], contributing_signals=["price_up"], reasoning="Prices rising", suggested_action=act, time_window="next 2 days", detected_at=NOW)

def mk_conf(cid="ro-conflict-1"):
    return ConflictNotice(id=cid, type=ConflictType.RAINFALL_VS_IRRIGATION_NEED, description="Rain vs irrigation", conflicting_signals=[_ev()], sources=["weather", "smart_irrigation"], detected_by="risk_opportunity", unresolved_reason="Cannot resolve", recommended_action="Verify moisture", detected_at=NOW)

def mk_dq(did="ro-dq-1"):
    return DataQualityNotice(id=did, type=DataQualityIssueType.MISSING_DATA, source="weather", message="Weather missing", affected_analysis=["weather_rules"], detected_at=NOW)

def mk_ro(risks=None, opps=None, confs=None, dqs=None):
    return RiskOpportunityResponse(status="partial_context", risks=risks or [], opportunities=opps or [], data_quality=DataQuality(status="partial_context"), data_quality_notices=dqs or [], conflict_notices=confs or [], summary=RiskOpportunitySummary(risk_count=len(risks or []), opportunity_count=len(opps or []), data_quality_notice_count=len(dqs or []), conflict_notice_count=len(confs or [])), engine_version="1.0.0", ruleset_version="1.0.0", analysis_timestamp=NOW, total_risks=len(risks or []), total_opportunities=len(opps or []))

def mk_alert(aid="alert-1", atype=AlertType.RISK, pri=AlertPriority.HIGH, cat="irrigation", sid="ro-risk-1"):
    return SmartAlert(id=aid, alert_type=atype, priority=pri, severity=None, status=AlertStatus.ACTIVE, category=cat, title="Water stress", message="Irrigation required", recommended_action="Irrigate now", affected_crop="rice", affected_stage="flowering", source_id=sid, source_type=AlertSourceType.RISK, contributing_sources=[_cs()], contributing_signals=["soil_moisture_low"], evidence=[_ev()], reasoning="reason", created_at=NOW, valid_until=None, time_window="within 6 hours", dedupe_key="k-" + aid)

def mk_sa(alerts):
    from app.schemas.decision import DecisionStatus
    return __import__("app.schemas.smart_alert", fromlist=["SmartAlertResponse"]).SmartAlertResponse(status=DecisionStatus("partial_context"), alerts=alerts, total_alerts=len(alerts), critical_count=0, high_count=len(alerts), medium_count=0, low_count=0, risk_count=len(alerts), opportunity_count=0, conflict_count=0, data_quality_count=0, suppressed_count=0, engine_version="1.0.0", ruleset_version="1.0.0", generated_at=NOW)

def mk_fc():
    return FarmContext(crop="rice", variety="Swarna", location="Nadia", season="kharif", current_growth_stage="flowering")

def req(ro=None, sa=None, prefs=None, fc=None, farmer=None):
    return ActionPlanRequest(farm_context=(fc if fc is not None else mk_fc()), risk_opportunity=ro, smart_alerts=sa, farmer_context=farmer, preferences=(prefs or ActionPlanPreferences()))

def test_basic_generation():
    out = generate_action_plan(req(ro=mk_ro(risks=[mk_risk()]), sa=mk_sa([mk_alert()]), prefs=None))
    assert out.total_actions >= 1
    assert out.total_actions == out.critical_count + out.high_count + out.medium_count + out.low_count
    assert out.engine_version == ENGINE_VERSION and out.ruleset_version == RULESET_VERSION

def test_empty_input():
    out = generate_action_plan(req(ro=mk_ro()))
    assert out.total_actions == 0 and out.suppressed_count == 0

def test_critical_high_medium():
    out = generate_action_plan(req(ro=mk_ro(risks=[mk_risk(rid="c", pri=PriorityLevel.CRITICAL, sev=SeverityLevel.CRITICAL, fu="Act now")]), prefs=None))
    assert out.critical_count == 1 and out.actions[0].priority.value == "critical"
    assert out.actions[0].time_window == "immediately"
    med = mk_risk(rid="m", pri=PriorityLevel.MEDIUM, sev=SeverityLevel.MEDIUM, fu="Scout field")
    out2 = generate_action_plan(req(ro=mk_ro(risks=[med]), prefs=None))
    assert out2.total_actions == 1
    med2 = mk_risk(rid="m2", pri=PriorityLevel.MEDIUM, sev=SeverityLevel.MEDIUM, fu=None, rs="mild note")
    out3 = generate_action_plan(req(ro=mk_ro(risks=[med2]), prefs=None))
    assert out3.total_actions == 0 and out3.suppressed_count == 1

def test_low_suppressed():
    low = mk_risk(rid="l", pri=PriorityLevel.LOW, sev=SeverityLevel.LOW, fu=None, rs="mild")
    out = generate_action_plan(req(ro=mk_ro(risks=[mk_risk(), low]), prefs=None))
    assert out.total_actions == 1 and out.suppressed_count == 1

def test_opportunity_and_alert():
    out = generate_action_plan(req(ro=mk_ro(opps=[mk_opp()]), prefs=None))
    assert out.total_actions == 1 and out.actions[0].source_type.value == "opportunity"
    out2 = generate_action_plan(req(ro=mk_ro(risks=[mk_risk()]), sa=mk_sa([mk_alert()]), prefs=None))
    assert out2.total_actions == 1

def test_conflict_and_dq():
    out = generate_action_plan(req(ro=mk_ro(risks=[mk_risk()], confs=[mk_conf()], dqs=[mk_dq()]), prefs=None))
    assert any(a.status.value == "needs_review" for a in out.actions)
    assert len(out.conflict_notices) == 1 and len(out.data_quality_notices) == 1
    assert all(a.source_type.value != "data_quality" for a in out.actions)

def test_traceability_and_valid_until():
    vu = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    r = mk_risk(vu=vu)
    a = generate_action_plan(req(ro=mk_ro(risks=[r]), prefs=None)).actions[0]
    assert a.source_id == "ro-risk-1" and a.evidence[0].signal == "soil_moisture_low"
    assert a.contributing_signals == ["soil_moisture_low"] and a.valid_until == vu
    assert a.confidence == "medium" and a.numerical_confidence == 0.7
    assert a.dedupe_key == dedupe_key_for("irrigation", "irrigation", "ro-risk-1", "rice", "flowering")

def test_expired_and_ordering():
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    old = mk_risk(rid="old", vu=past)
    out = generate_action_plan(req(ro=mk_ro(risks=[old, mk_risk()]), prefs=None))
    assert out.total_actions == 1 and out.actions[0].source_id == "ro-risk-1"
    r2 = mk_opp(oid="o2", pri=PriorityLevel.MEDIUM, act="Plan ops")
    out2 = generate_action_plan(req(ro=mk_ro(risks=[mk_risk()], opps=[r2]), prefs=None))
    pris = [a.priority.value for a in out2.actions]
    assert pris == sorted(pris, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x])

def test_critical_survives_limit_and_counts():
    risks = [mk_risk(rid="c", pri=PriorityLevel.CRITICAL, sev=SeverityLevel.CRITICAL, fu="Act now")] + [mk_risk(rid=f"h{i}", cat=RiskCategory.DISEASE, fu="Scout") for i in range(4)]
    out = generate_action_plan(req(ro=mk_ro(risks=risks), prefs=ActionPlanPreferences(max_actions=2)))
    assert out.total_actions == 2 and out.critical_count == 1 and out.suppressed_count == 3

def test_personalization():
    out = generate_action_plan(req(ro=mk_ro(risks=[mk_risk()]), prefs=None, fc=None, farmer={"growth_stage": "tillering"}))
    assert "rice" in out.actions[0].title.lower()
    out2 = generate_action_plan(req(ro=mk_ro(risks=[mk_risk()]), prefs=None, fc=mk_fc(), farmer=None))
    assert "flowering" in out2.actions[0].reason.lower()

def test_no_fabrication_and_deterministic():
    ro = mk_ro(risks=[mk_risk()], opps=[mk_opp()])
    a = generate_action_plan(req(ro=ro, prefs=None))
    b = generate_action_plan(req(ro=ro, prefs=None))
    da = [x.model_dump(exclude={"created_at"}) for x in a.actions]
    db = [x.model_dump(exclude={"created_at"}) for x in b.actions]
    assert da == db
    assert [x["id"] for x in da] == [x["id"] for x in db]
    assert "dosage" not in a.actions[0].action.lower() and "ml/ha" not in a.actions[0].action.lower()

def test_api_success_validation_empty():
    body = req(ro=mk_ro(risks=[mk_risk()]), prefs=None).model_dump()
    r = client.post("/api/action-plan/generate", json=body)
    assert r.status_code == 200 and r.json()["total_actions"] == 1
    r = client.post("/api/action-plan/generate", json={"preferences": {"max_actions": "bad"}})
    assert r.status_code == 422
    r = client.post("/api/action-plan/generate", json=req(ro=mk_ro()).model_dump())
    assert r.status_code == 200 and r.json()["total_actions"] == 0

def test_health_categories_rules_nomlext():
    assert client.get("/api/action-plan/health").status_code == 200
    r = client.get("/api/action-plan/categories")
    assert r.status_code == 200 and len(r.json()["action_types"]) >= 10
    import app.intelligence.action_plan as eng
    src = open(eng.__file__).read()
    assert "requests.get" not in src and "ModelRegistry" not in src
