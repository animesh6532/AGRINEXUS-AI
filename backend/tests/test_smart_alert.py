"""
Tests for Smart Alerts (schemas/intelligence/service/API).

Deterministic, no external API calls, no ML models. Inputs built
directly from existing Risk & Opportunity contracts.
"""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.intelligence.smart_alert import (
    ENGINE_VERSION, RULESET_VERSION, dedupe_key_for, generate_alerts,
)
from app.main import app
from app.schemas.decision import DataQuality, SupportingSignal
from app.schemas.risk_opportunity import (
    ConflictNotice, ConflictType, ContributingSource, DataQualityIssueType,
    DataQualityNotice, ItemStatus, Opportunity, OpportunityCategory,
    PriorityLevel, Risk, RiskCategory, RiskOpportunityResponse,
    RiskOpportunitySummary, SeverityLevel, ConfidenceLevel, SourceType,
)
from app.schemas.smart_alert import (
    AlertPriority, AlertSourceType, AlertType, SmartAlertPreferences,
)
from app.services.smart_alert_service import SmartAlertService

client = TestClient(app)
NOW = "2026-09-19T10:30:00+00:00"


def _ev(signal="high_humidity", source="weather"):
    return SupportingSignal(signal=signal, source=source,
                            description=f"{signal} from {source}", value=80.0)


def _cs(source="weather", stype=SourceType.EXTERNAL_DATA):
    return ContributingSource(source=source, source_type=stype, detail="contrib")


def make_risk(rid="ro-risk-1", priority=PriorityLevel.HIGH,
              severity=SeverityLevel.HIGH, follow_up="Scout field",
              crop="rice", stage="flowering", valid_until=None,
              reasoning="reason", title="Disease risk"):
    return Risk(
        id=rid, category=RiskCategory.DISEASE, title=title,
        description="desc", severity=severity, priority=priority,
        status=ItemStatus.ACTIVE, confidence=ConfidenceLevel.MEDIUM,
        numerical_confidence=None, confidence_source=None,
        confidence_rationale="r", affected_crop=crop, affected_stage=stage,
        evidence=[_ev()], contributing_sources=[_cs()],
        contributing_signals=["high_humidity"], reasoning=reasoning,
        recommended_follow_up=follow_up, detected_at=NOW,
        valid_until=valid_until,
    )


def make_opp(oid="ro-opp-1", priority=PriorityLevel.HIGH,
             action="Act now", window="2026-10-17 to 2026-11-06"):
    return Opportunity(
        id=oid, category=OpportunityCategory.MARKET, title="Opp",
        description="desc", priority=priority, status=ItemStatus.ACTIVE,
        confidence=ConfidenceLevel.MEDIUM, numerical_confidence=None,
        confidence_source=None, confidence_rationale="r",
        affected_crop="rice", affected_stage="tillering",
        evidence=[_ev("price_up", "market")], contributing_sources=[_cs("market")],
        contributing_signals=["price_up"], reasoning="reason",
        suggested_action=action, time_window=window, detected_at=NOW,
    )


def make_conflict(cid="ro-conflict-1", action="Verify moisture",
                 reason="Cannot resolve"):
    return ConflictNotice(
        id=cid, type=ConflictType.RAINFALL_VS_IRRIGATION_NEED,
        description="Rain vs irrigation", conflicting_signals=[_ev()],
        sources=["weather", "smart_irrigation"],
        detected_by="risk_opportunity", unresolved_reason=reason,
        recommended_action=action, detected_at=NOW,
    )


def make_dq(did="ro-dq-1", dtype=DataQualityIssueType.MISSING_DATA,
            affected=("weather_rules",)):
    return DataQualityNotice(
        id=did, type=dtype, source="weather", message="Weather missing",
        affected_analysis=list(affected), detected_at=NOW,
    )


def make_response(risks=(), opps=(), dqs=(), conflicts=()):
    return RiskOpportunityResponse(
        status="partial_context",
        risks=list(risks), opportunities=list(opps),
        data_quality=DataQuality(status="partial_context"),
        data_quality_notices=list(dqs), conflict_notices=list(conflicts),
        summary=RiskOpportunitySummary(
            risk_count=len(list(risks)), opportunity_count=len(list(opps)),
            data_quality_notice_count=len(list(dqs)),
            conflict_notice_count=len(list(conflicts))),
        engine_version="1.0.0", ruleset_version="1.0.0",
        analysis_timestamp=NOW, total_risks=len(list(risks)),
        total_opportunities=len(list(opps)),
    )

def test_critical_risk_always_alerts():
    out = generate_alerts(make_response(risks=[make_risk(priority=PriorityLevel.CRITICAL, severity=SeverityLevel.CRITICAL)]))
    assert out.total_alerts == 1 and out.critical_count == 1


def test_high_risk_alerts():
    out = generate_alerts(make_response(risks=[make_risk()]))
    assert out.total_alerts == 1 and out.high_count == 1
    assert out.alerts[0].source_id == "ro-risk-1"
    assert out.alerts[0].source_type == AlertSourceType.RISK


def test_medium_actionable_risk_alerts():
    r = make_risk(rid="ro-risk-m", priority=PriorityLevel.MEDIUM,
                 severity=SeverityLevel.MEDIUM, follow_up="Check within days")
    out = generate_alerts(make_response(risks=[r]))
    assert out.total_alerts == 1


def test_medium_nonactionable_risk_suppressed():
    r = make_risk(rid="ro-risk-m2", priority=PriorityLevel.MEDIUM,
                 severity=SeverityLevel.MEDIUM, follow_up=None,
                 reasoning="routine note", title="Routine note")
    out = generate_alerts(make_response(risks=[r]))
    assert out.total_alerts == 0 and out.suppressed_count == 1


def test_low_risk_suppressed():
    r = make_risk(priority=PriorityLevel.LOW, severity=SeverityLevel.LOW, follow_up=None)
    out = generate_alerts(make_response(risks=[r]))
    assert out.total_alerts == 0 and out.suppressed_count == 1


def test_high_opp_alerts():
    out = generate_alerts(make_response(opps=[make_opp()]))
    assert out.total_alerts == 1 and out.opportunity_count == 1
    assert out.alerts[0].time_window == "2026-10-17 to 2026-11-06"
    assert out.alerts[0].recommended_action == "Act now"

def test_medium_actionable_opp_alerts():
    out = generate_alerts(make_response(opps=[make_opp(oid="ro-opp-m", priority=PriorityLevel.MEDIUM)]))
    assert out.total_alerts == 1


def test_low_opp_suppressed():
    out = generate_alerts(make_response(opps=[make_opp(priority=PriorityLevel.LOW, action=None, window=None)]))
    assert out.total_alerts == 0


def test_conflict_alert():
    out = generate_alerts(make_response(conflicts=[make_conflict()]))
    assert out.total_alerts == 1 and out.conflict_count == 1
    a = out.alerts[0]
    assert a.unresolved_reason == "Cannot resolve"
    assert a.conflict_sources == ["weather", "smart_irrigation"]
    assert len(a.conflicting_signals) == 1 and len(a.evidence) == 1


def test_empty_conflict_suppressed():
    c = make_conflict(action="", reason="")
    out = generate_alerts(make_response(conflicts=[c]))
    assert out.total_alerts == 0


def test_material_dq_alert():
    out = generate_alerts(make_response(dqs=[make_dq()]))
    assert out.total_alerts == 1 and out.data_quality_count == 1
    assert out.alerts[0].affected_analysis == ["weather_rules"]


def test_nonactionable_dq_suppressed():
    dq = make_dq(dtype=DataQualityIssueType.LIMITED_COVERAGE, affected=())
    out = generate_alerts(make_response(dqs=[dq]))
    assert out.total_alerts == 0

def test_dedupe_and_key_deterministic():
    out = generate_alerts(make_response(risks=[make_risk(), make_risk()]))
    assert out.total_alerts == 1 and out.suppressed_count == 1
    k1 = dedupe_key_for("risk", "ro-risk-1", "disease", "rice", "flowering")
    assert k1 == dedupe_key_for("risk", "ro-risk-1", "disease", "rice", "flowering")
    assert len(k1) == 64


def test_critical_survives_max_alerts():
    risks = [make_risk(rid=f"ro-risk-{i}", priority=PriorityLevel.HIGH) for i in range(5)]
    crit = make_risk(rid="ro-risk-c", priority=PriorityLevel.CRITICAL,
                    severity=SeverityLevel.CRITICAL)
    out = generate_alerts(make_response(risks=[crit] + risks),
                          SmartAlertPreferences(max_alerts=2))
    assert "ro-risk-c" in [a.source_id for a in out.alerts]
    assert out.critical_count == 1


def test_ordering_deterministic():
    kw = dict(risks=[make_risk(priority=PriorityLevel.HIGH)], opps=[make_opp()],
              conflicts=[make_conflict()], dqs=[make_dq()])
    out = generate_alerts(make_response(**kw))
    kinds = [a.alert_type for a in out.alerts]
    assert kinds[0] == AlertType.RISK and kinds[1] == AlertType.CONFLICT
    out2 = generate_alerts(make_response(**kw))
    assert [a.id for a in out.alerts] == [a.id for a in out2.alerts]


def test_traceability_preserved():
    r = make_risk(valid_until="2026-09-26T10:30:00+00:00")
    a = generate_alerts(make_response(risks=[r])).alerts[0]
    assert a.evidence[0].signal == "high_humidity"
    assert a.contributing_sources[0].source == "weather"
    assert a.contributing_signals == ["high_humidity"]
    assert a.valid_until == "2026-09-26T10:30:00+00:00"
    assert a.recommended_action == "Scout field"
    assert a.affected_crop == "rice" and a.affected_stage == "flowering"


def test_counts_and_empty():
    out = generate_alerts(make_response())
    assert out.total_alerts == 0 and out.suppressed_count == 0
    assert out.engine_version == ENGINE_VERSION
    assert out.ruleset_version == RULESET_VERSION
    low = make_risk(rid="ro-risk-2", priority=PriorityLevel.LOW,
                   severity=SeverityLevel.LOW, follow_up=None)
    out2 = generate_alerts(make_response(risks=[make_risk(), low], opps=[make_opp()]))
    assert out2.total_alerts == 2 and out2.suppressed_count == 1
    assert out2.risk_count == 1 and out2.opportunity_count == 1


def test_no_external_or_ml_calls():
    import app.intelligence.smart_alert as eng
    src = open(eng.__file__).read()
    assert "requests.get" not in src and "urlopen" not in src
    assert "ModelRegistry" not in src


def test_health_and_rules_endpoints():
    r = client.get("/api/smart-alerts/health")
    assert r.status_code == 200 and r.json()["status"] == "healthy"
    r = client.get("/api/smart-alerts/rules")
    assert r.status_code == 200 and len(r.json()["rules"]) >= 10


def test_api_generate_and_validation():
    body = {"risk_opportunity": make_response(risks=[make_risk()]).model_dump(),
            "preferences": {}}
    r = client.post("/api/smart-alerts/generate", json=body)
    assert r.status_code == 200 and r.json()["total_alerts"] == 1
    r = client.post("/api/smart-alerts/generate", json={"preferences": {}})
    assert r.status_code == 422


def test_deterministic_repeat():
    resp = make_response(risks=[make_risk()], opps=[make_opp()])
    a = generate_alerts(resp)
    b = generate_alerts(resp)
    assert [al.model_dump() for al in a.alerts] == [al.model_dump() for al in b.alerts]


def test_preferences_filter():
    prefs = SmartAlertPreferences(include_opportunities=False,
                                  include_conflicts=False,
                                  include_data_quality=False)
    out = generate_alerts(make_response(risks=[make_risk()], opps=[make_opp()],
                                        conflicts=[make_conflict()], dqs=[make_dq()]),
                          prefs)
    assert out.total_alerts == 1 and out.risk_count == 1



