"""
Unit & API tests for the Risk & Opportunity Analysis module
(app/schemas/risk_opportunity.py, app/intelligence/risk_opportunity.py,
app/services/risk_opportunity_service.py, app/api/risk_opportunity.py).

These tests exercise the deterministic decision-intelligence layer with NO
external API calls, NO ML model implementations and NO fabricated data.
Inputs are constructed directly from the existing normalized contracts
(FarmContext + optional Decision Engine output). No secrets or API keys
are used anywhere in this file.

Covered acceptance areas:
1. health endpoint            14. missing ML prediction
2. empty/minimal input        15. stale data
3. complete valid input       16. conflicting signals
4. weather risk               17. duplicate suppression
5. irrigation risk            18. severity calculation
6. disease + weather          19. priority calculation
7. pest + crop stage          20. confidence handling
8. market risk                21. evidence generation
9. market opportunity         22. multiple simultaneous risks
10. yield + market            23. multiple simultaneous opportunities
11. fertilizer context        24. API validation errors
12. missing weather           25. existing backend regression
13. missing market
"""

from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.intelligence.decision_engine import (
    KNOWN_ML_MODELS,
    STALENESS_DAYS_THRESHOLD,
)
from app.intelligence.risk_opportunity import (
    ENGINE_VERSION,
    RULESET_VERSION,
    _confidence_for,
    _priority_for_opportunity,
    _priority_for_risk,
    _severity_for_risk,
    analyze_risk_opportunity,
)
from app.main import app
from app.schemas.decision import (
    CropCalendarContext,
    DataQuality,
    Decision,
    DecisionResponse,
    DecisionStatus,
    DecisionType,
    FarmContext,
    MarketContext,
    MLPrediction,
    MLPredictionStatus,
    Priority,
    WeatherContext,
)
from app.schemas.risk_opportunity import (
    ConfidenceLevel,
    ConfidenceSource,
    ConflictType,
    DataQualityIssueType,
    ItemStatus,
    OpportunityCategory,
    PriorityLevel,
    RiskCategory,
    RiskOpportunityContext,
    SeverityLevel,
)
from app.services.decision_engine_service import DecisionEngineService
from app.services.risk_opportunity_service import RiskOpportunityService

test_client = TestClient(app)

AS_OF = date(2026, 9, 19)


# =============================================================================
# Fixtures / builders (deterministic; every value is supplied explicitly)
# =============================================================================


def make_ml(model_name, *, prediction=None, probability=None,
            confidence=None, unit=None, status="available", metadata=None,
            timestamp=None):
    """Build a standardized MLPrediction (values echoed, never invented)."""
    return MLPrediction(
        model_name=model_name,
        prediction=prediction,
        probability=probability,
        confidence=confidence,
        unit=unit,
        status=MLPredictionStatus(status),
        metadata=metadata,
        timestamp=timestamp,
    )


def make_weather(**overrides):
    """Benign WeatherContext; overrides activate adverse/benign signals."""
    values = dict(
        is_weather_data_available=True,
        precipitation_probability=10.0,
        forecast_precipitation_sum=0.0,
        temperature_max_forecast=30.0,
        temperature_min_forecast=20.0,
        wind_speed_max_forecast=10.0,
        current_humidity=60.0,
        forecast_horizon_days=7,
    )
    values.update(overrides)
    return WeatherContext(**values)


def make_market(**overrides):
    values = dict(
        is_market_data_available=True,
        commodity="Paddy (Common)",
        current_price=2800.0,
        recent_trend="stable",
        forecast_trend="stable",
    )
    values.update(overrides)
    return MarketContext(**values)


def make_calendar(**overrides):
    values = dict(is_crop_calendar_available=True, crop="rice")
    values.update(overrides)
    return CropCalendarContext(**values)


def make_farm(**kwargs):
    """FarmContext with stable identity fields; sources via kwargs."""
    kwargs.setdefault("crop", "rice")
    kwargs.setdefault("location", "West Bengal")
    kwargs.setdefault("sowing_date", date(2026, 6, 15))
    kwargs.setdefault("as_of_date", AS_OF)
    return FarmContext(**kwargs)


def make_context(decision_output=None, source_metadata=None, **kwargs):
    """RiskOpportunityContext wrapping a FarmContext."""
    return RiskOpportunityContext(
        farm_context=make_farm(**kwargs),
        decision_engine_output=decision_output,
        source_metadata=source_metadata,
    )


def analyze(context):
    """Run the deterministic engine and return the response."""
    return analyze_risk_opportunity(context)


def make_de_output(decisions):
    """Minimal DecisionResponse carrying the given decisions."""
    return DecisionResponse(
        status=DecisionStatus.complete_context,
        data_quality=DataQuality(
            status="complete_context",
            completeness_percent=100.0,
            missing_sources=[],
            stale_sources=[],
            conflicts=[],
            unavailable_ml_models=[],
            missing_critical_fields=[],
        ),
        decisions=decisions,
        engine_version="1.0.0",
        ruleset_version="1.0.0",
        evaluation_timestamp="2026-09-19T10:00:00+00:00",
        total_decisions=len(decisions),
    )


def make_de_decision(decision_type, *, priority=Priority.HIGH,
                     confidence=None, title="Upstream decision",
                     decision_id="dec-1"):
    return Decision(
        id=decision_id,
        decision_type=decision_type,
        status=DecisionStatus.complete_context,
        priority=priority,
        title=title,
        summary="summary",
        reason="reason",
        crop="rice",
        confidence=confidence,
        confidence_rationale="two sources agree" if confidence else None,
        created_at="2026-09-19T10:00:00+00:00",
    )


def risks_of(response, category=None):
    return [
        r for r in response.risks
        if category is None or r.category == category
    ]


def opps_of(response, category=None):
    return [
        o for o in response.opportunities
        if category is None or o.category == category
    ]


def notice_sources(response, issue_type=None):
    return [
        n.source for n in response.data_quality_notices
        if issue_type is None or n.type == issue_type
    ]


def disease_context(**weather_overrides):
    """Disease + weather + susceptible stage (consolidation scenario)."""
    values = dict(
        precipitation_probability=85.0,
        forecast_precipitation_sum=60.0,
        current_humidity=90.0,
    )
    values.update(weather_overrides)
    return make_context(
        weather_context=make_weather(**values),
        crop_calendar_context=make_calendar(current_growth_stage="flowering"),
        ml_predictions=[
            make_ml("disease_detection", prediction="rice blast",
                    probability=0.82),
        ],
    )


# =============================================================================
# Service layer
# =============================================================================


class TestServiceLayer:
    def test_health_snapshot(self):
        health = RiskOpportunityService().health()
        assert health["status"] == "healthy"
        assert health["service"] == "agrinexus-risk-opportunity"
        assert health["version"] == ENGINE_VERSION == "1.0.0"
        assert health["ruleset_version"] == RULESET_VERSION == "1.0.0"
        assert health["engine_available"] is True
        assert set(health["upstream_dependencies"]) == {
            "weather", "market", "crop_calendar", "decision_engine",
        }
        assert health["ml_model_contracts_available"] == list(KNOWN_ML_MODELS)

    def test_health_exposes_no_secrets(self):
        health_text = str(RiskOpportunityService().health()).lower()
        for forbidden in ("api_key", "password", "secret", "token"):
            assert forbidden not in health_text

    def test_describe_ruleset(self):
        ruleset = RiskOpportunityService().describe_ruleset()
        assert ruleset["ruleset_version"] == RULESET_VERSION
        assert "weather" in ruleset["risk_categories"]
        assert "data_quality" in ruleset["risk_categories"]
        assert "harvest" in ruleset["opportunity_categories"]

    def test_supported_ml_contracts(self):
        assert RiskOpportunityService().supported_ml_contracts() == [
            "crop_recommendation",
            "soil_analysis",
            "disease_detection",
            "pest_prediction",
            "fertilizer_recommendation",
            "smart_irrigation",
            "crop_yield_prediction",
        ]

    def test_service_analyze(self):
        response = RiskOpportunityService().analyze(make_context())
        assert response.total_risks == len(response.risks)
        assert response.engine_version == ENGINE_VERSION

    def test_service_analyze_farm_context(self):
        response = RiskOpportunityService().analyze_farm_context(
            make_farm(weather_context=make_weather()),
        )
        assert response.total_opportunities == len(response.opportunities)

    def test_service_reuses_decision_service_adapters(self):
        service = RiskOpportunityService()
        assert isinstance(service.decision_service, DecisionEngineService)


# =============================================================================
# API: health + categories endpoints
# =============================================================================


class TestApiHealth:
    def test_health_endpoint(self):
        response = test_client.get("/api/risk-opportunity/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "agrinexus-risk-opportunity"
        assert data["version"] == "1.0.0"
        assert data["ruleset_version"] == "1.0.0"
        assert data["engine_available"] is True
        assert data["timestamp"].endswith("+00:00")
        assert data["severity_levels"] == ["low", "medium", "high", "critical"]
        assert data["priority_levels"] == ["low", "medium", "high", "critical"]
        assert set(data["supported_risk_categories"]) == {
            member.value for member in RiskCategory
        }
        assert set(data["supported_opportunity_categories"]) == {
            member.value for member in OpportunityCategory
        }
        assert set(data["upstream_dependencies"]) == {
            "weather", "market", "crop_calendar", "decision_engine",
        }
        assert data["ml_model_contracts_available"] == list(KNOWN_ML_MODELS)

    def test_health_exposes_no_secrets(self):
        response = test_client.get("/api/risk-opportunity/health")
        body = response.text.lower()
        for forbidden in ("api_key", "password", "secret", "token="):
            assert forbidden not in body


class TestApiCategories:
    def test_categories_endpoint(self):
        response = test_client.get("/api/risk-opportunity/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["ruleset_version"] == RULESET_VERSION
        risk_values = [c["value"] for c in data["risk_categories"]]
        assert risk_values == [c.value for c in RiskCategory]
        opp_values = [c["value"] for c in data["opportunity_categories"]]
        assert opp_values == [c.value for c in OpportunityCategory]
        severity_values = [c["value"] for c in data["severity_levels"]]
        assert severity_values == ["low", "medium", "high", "critical"]
        conflict_values = [c["value"] for c in data["conflict_types"]]
        assert set(conflict_values) == {c.value for c in ConflictType}
        issue_values = [c["value"] for c in data["data_quality_issue_types"]]
        assert set(issue_values) == {
            t.value for t in DataQualityIssueType
        }
        for entry in data["risk_categories"]:
            assert entry["description"]


# =============================================================================
# API: analyze endpoint (valid payloads + validation errors)
# =============================================================================


def api_payload(**farm_overrides):
    """JSON payload for POST /api/risk-opportunity/analyze."""
    farm = {
        "crop": "rice",
        "location": "West Bengal",
        "sowing_date": "2026-06-15",
        "as_of_date": "2026-09-19",
    }
    farm.update(farm_overrides)
    return {"farm_context": farm}


class TestApiAnalyze:
    def test_analyze_minimal_valid_payload(self):
        response = test_client.post(
            "/api/risk-opportunity/analyze", json=api_payload(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "insufficient_context"
        assert data["risks"] == []
        assert data["opportunities"] == []
        assert data["summary"]["risk_count"] == 0
        assert data["summary"]["opportunity_count"] == 0
        assert data["engine_version"] == "1.0.0"
        assert data["ruleset_version"] == "1.0.0"
        assert data["total_risks"] == 0
        assert data["total_opportunities"] == 0

    def test_analyze_valid_payload_with_weather(self):
        payload = api_payload(
            weather_context={
                "is_weather_data_available": True,
                "precipitation_probability": 85.0,
                "forecast_precipitation_sum": 60.0,
                "temperature_max_forecast": 30.0,
                "temperature_min_forecast": 20.0,
                "wind_speed_max_forecast": 10.0,
                "current_humidity": 90.0,
                "forecast_horizon_days": 7,
            },
        )
        response = test_client.post(
            "/api/risk-opportunity/analyze", json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_risks"] >= 1
        categories = {r["category"] for r in data["risks"]}
        assert "weather" in categories
        for risk in data["risks"]:
            assert risk["severity"] in {"low", "medium", "high", "critical"}
            assert risk["confidence"]
            assert risk["reasoning"]
            assert risk["id"].startswith("ro-risk-")

    def test_analyze_missing_farm_context_is_validation_error(self):
        response = test_client.post(
            "/api/risk-opportunity/analyze", json={},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Validation Failure"

    def test_analyze_wrong_type_farm_context_is_validation_error(self):
        response = test_client.post(
            "/api/risk-opportunity/analyze",
            json={"farm_context": "not-an-object"},
        )
        assert response.status_code == 422
        assert response.json()["success"] is False

    def test_analyze_malformed_json_is_validation_error(self):
        response = test_client.post(
            "/api/risk-opportunity/analyze",
            content=b"not-json-at-all",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_analyze_invalid_nested_field_is_validation_error(self):
        response = test_client.post(
            "/api/risk-opportunity/analyze",
            json=api_payload(sowing_date="not-a-date"),
        )
        assert response.status_code == 422


# =============================================================================
# 2. Empty / minimal input
# =============================================================================


class TestMinimalInput:
    def test_empty_context_is_insufficient(self):
        response = analyze(make_context())
        assert response.status == DecisionStatus.insufficient_context
        assert response.risks == []
        assert response.opportunities == []
        assert response.total_risks == 0
        assert response.total_opportunities == 0

    def test_empty_context_reports_missing_sources(self):
        response = analyze(make_context())
        missing = set(notice_sources(
            response, DataQualityIssueType.MISSING_DATA,
        ))
        assert {
            "weather", "market", "crop_calendar", "decision_engine",
        } <= missing
        assert response.data_quality.missing_sources == [
            "crop_calendar", "market", "weather",
        ]
        assert response.data_quality.completeness_percent == 0.0

    def test_empty_context_has_no_conflicts(self):
        response = analyze(make_context())
        assert response.conflict_notices == []
        assert response.status != DecisionStatus.conflicting_signals

    def test_engine_metadata_present(self):
        response = analyze(make_context())
        assert response.engine_version == ENGINE_VERSION == "1.0.0"
        assert response.ruleset_version == RULESET_VERSION == "1.0.0"
        assert response.analysis_timestamp.endswith("+00:00")
        assert response.total_risks == len(response.risks)
        assert response.total_opportunities == len(response.opportunities)

    def test_summary_counts_match_lists(self):
        response = analyze(make_context())
        summary = response.summary
        assert summary.risk_count == len(response.risks)
        assert summary.opportunity_count == len(response.opportunities)
        assert summary.data_quality_notice_count == len(
            response.data_quality_notices,
        )
        assert summary.conflict_notice_count == len(response.conflict_notices)
        assert summary.highest_risk_severity is None


# =============================================================================
# 3. Complete valid input
# =============================================================================


def complete_context():
    """All three data sources + stage + all seven ML contracts available."""
    return make_context(
        weather_context=make_weather(),
        market_context=make_market(),
        crop_calendar_context=make_calendar(current_growth_stage="tillering"),
        ml_predictions=[
            make_ml(name, prediction="ok", probability=0.9)
            for name in KNOWN_ML_MODELS
        ],
    )


class TestCompleteInput:
    def test_complete_context_status(self):
        response = analyze(complete_context())
        assert response.status == DecisionStatus.complete_context
        assert response.data_quality.status == "complete_context"
        assert response.data_quality.completeness_percent == 100.0
        assert response.data_quality.missing_sources == []
        assert response.data_quality.unavailable_ml_models == []

    def test_complete_context_no_missing_source_notices(self):
        response = analyze(complete_context())
        missing = set(notice_sources(
            response, DataQualityIssueType.MISSING_DATA,
        ))
        assert "weather" not in missing
        assert "market" not in missing
        assert "crop_calendar" not in missing
        # Decision Engine output still absent by design - reported, not hidden.
        assert "decision_engine" in missing

    def test_complete_context_still_produces_opportunities(self):
        response = analyze(complete_context())
        assert response.total_opportunities >= 1
        assert response.summary.highest_opportunity_priority is not None


# =============================================================================
# 4. Weather risks
# =============================================================================


class TestWeatherRisks:
    def test_heavy_rainfall_with_sensitive_stage(self):
        response = analyze(make_context(
            weather_context=make_weather(
                precipitation_probability=85.0,
                forecast_precipitation_sum=60.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="flowering",
            ),
        ))
        weather_risks = risks_of(response, RiskCategory.WEATHER)
        heavy = [
            r for r in weather_risks
            if r.title == "Heavy Rainfall Expected"
        ]
        assert len(heavy) == 1
        risk = heavy[0]
        # single weather source + elevated + sensitive stage -> HIGH
        assert risk.severity == SeverityLevel.HIGH
        assert risk.priority == PriorityLevel.HIGH
        assert "heavy_rainfall_expected" in [
            e.signal for e in risk.evidence
        ]
        assert risk.valid_until is not None
        assert risk.affected_stage == "flowering"

    def test_notable_rainfall_without_sensitive_stage(self):
        response = analyze(make_context(
            weather_context=make_weather(
                precipitation_probability=50.0,
                forecast_precipitation_sum=20.0,
            ),
        ))
        risk = next(
            r for r in risks_of(response, RiskCategory.WEATHER)
            if r.title == "Rainfall Expected"
        )
        # single source, elevated, not sensitive -> MEDIUM
        assert risk.severity == SeverityLevel.MEDIUM

    def test_heat_stress(self):
        response = analyze(make_context(
            weather_context=make_weather(temperature_max_forecast=42.0),
        ))
        heat = [
            r for r in risks_of(response, RiskCategory.WEATHER)
            if r.title == "Heat Stress Risk"
        ]
        assert len(heat) == 1
        assert heat[0].severity == SeverityLevel.MEDIUM
        assert "extreme_heat_expected" in [
            e.signal for e in heat[0].evidence
        ]

    def test_cold_frost_stress(self):
        response = analyze(make_context(
            weather_context=make_weather(temperature_min_forecast=2.0),
        ))
        cold = [
            r for r in risks_of(response, RiskCategory.WEATHER)
            if r.title == "Cold / Frost Risk"
        ]
        assert len(cold) == 1
        assert "frost_risk_expected" in [e.signal for e in cold[0].evidence]

    def test_strong_wind(self):
        response = analyze(make_context(
            weather_context=make_weather(wind_speed_max_forecast=45.0),
        ))
        wind = [
            r for r in risks_of(response, RiskCategory.WEATHER)
            if r.title == "Strong Wind Risk"
        ]
        assert len(wind) == 1
        assert "strong_wind_expected" in [e.signal for e in wind[0].evidence]

    def test_severe_weather_in_sensitive_stage_is_critical(self):
        response = analyze(make_context(
            weather_context=make_weather(
                severe_weather_indicators=["thunderstorm"],
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="flowering",
            ),
        ))
        severe = [
            r for r in risks_of(response, RiskCategory.WEATHER)
            if r.title == "Severe Weather Reported"
        ]
        assert len(severe) == 1
        assert severe[0].severity == SeverityLevel.CRITICAL
        assert severe[0].priority == PriorityLevel.CRITICAL
        assert response.summary.highest_risk_severity == SeverityLevel.CRITICAL

    def test_benign_weather_produces_no_adverse_weather_risk(self):
        response = analyze(make_context(weather_context=make_weather()))
        admissible = {
            "Heat Stress Risk", "Cold / Frost Risk", "Strong Wind Risk",
            "Severe Weather Reported", "Heavy Rainfall Expected",
            "Rainfall Expected",
        }
        titles = {r.title for r in risks_of(response, RiskCategory.WEATHER)}
        assert not (titles & admissible)


# =============================================================================
# 5. Irrigation risk (multi-source water-stress consolidation)
# =============================================================================


def irrigation_risk_context(**kwargs):
    values = dict(
        weather_context=make_weather(
            precipitation_probability=5.0,
            forecast_precipitation_sum=0.0,
            temperature_max_forecast=40.0,
        ),
        crop_calendar_context=make_calendar(
            current_growth_stage="flowering",
        ),
        ml_predictions=[
            make_ml(
                "smart_irrigation",
                prediction="irrigation_required",
                probability=0.88,
                metadata={"irrigation_required": True},
            ),
        ],
    )
    values.update(kwargs)
    return make_context(**values)


class TestIrrigationRisk:
    def test_dry_forecast_and_model_consolidate_into_one_risk(self):
        response = analyze(irrigation_risk_context())
        irrigation_risks = risks_of(response, RiskCategory.IRRIGATION)
        assert len(irrigation_risks) == 1
        risk = irrigation_risks[0]
        # Weather dry-window evidence merged with the model signal.
        signals = {e.signal for e in risk.evidence}
        assert "irrigation_model_requires_irrigation" in signals
        assert "insufficient_rainfall_expected" in signals
        sources = {s.source for s in risk.contributing_sources}
        assert "smart_irrigation" in sources
        assert "weather" in sources

    def test_duplicate_water_deficit_suppressed(self):
        response = analyze(irrigation_risk_context())
        # The weather-only "Water Deficit Risk" is merged into the single
        # consolidated irrigation item - not emitted separately.
        titles = [r.title for r in response.risks]
        assert "Water Deficit Risk" not in titles

    def test_consolidated_risk_grading(self):
        response = analyze(irrigation_risk_context())
        risk = risks_of(response, RiskCategory.IRRIGATION)[0]
        # sources: weather + smart_irrigation (2), elevated, sensitive stage
        assert risk.severity == SeverityLevel.HIGH
        assert risk.priority == PriorityLevel.HIGH
        # documented method: 0.5 + 0.1 (model probability) = 0.6
        assert risk.confidence == ConfidenceLevel.MEDIUM
        assert risk.numerical_confidence == 0.6
        assert risk.confidence_source == ConfidenceSource.RISK_OPPORTUNITY

    def test_dry_forecast_without_model_is_weather_risk(self):
        response = analyze(make_context(
            weather_context=make_weather(
                precipitation_probability=5.0,
                forecast_precipitation_sum=0.0,
            ),
        ))
        titles = [r.title for r in response.risks]
        assert "Water Deficit Risk" in titles
        assert risks_of(response, RiskCategory.IRRIGATION) == []


# =============================================================================
# 6. Disease + weather correlation (multi-source consolidation)
# =============================================================================


class TestDiseaseWeatherCorrelation:
    def test_signals_consolidate_into_single_disease_risk(self):
        response = analyze(disease_context())
        disease_risks = risks_of(response, RiskCategory.DISEASE)
        # Exactly ONE consolidated item - not four separate alerts.
        assert len(disease_risks) == 1
        risk = disease_risks[0]
        assert risk.title == "Elevated Disease Pressure"
        signals = {e.signal for e in risk.evidence}
        assert {
            "disease_model_elevated_probability",
            "high_humidity",
            "high_precipitation_probability",
            "heavy_rainfall_expected",
            "growth_stage",
        } <= signals
        sources = {s.source for s in risk.contributing_sources}
        assert {"disease_detection", "weather", "crop_calendar"} <= sources

    def test_disease_risk_grading(self):
        risk = risks_of(analyze(disease_context()), RiskCategory.DISEASE)[0]
        # 2 corroborating sources (model + weather), elevated, sensitive
        assert risk.severity == SeverityLevel.HIGH
        assert risk.priority == PriorityLevel.HIGH
        # documented method: 0.5 + 0 model extras + 0.1 (probability) = 0.6
        assert risk.confidence == ConfidenceLevel.MEDIUM
        assert risk.numerical_confidence == 0.6
        assert risk.confidence_source == ConfidenceSource.RISK_OPPORTUNITY
        assert risk.affected_stage == "flowering"

    def test_weather_favourable_without_model_is_condition_only(self):
        response = analyze(make_context(
            weather_context=make_weather(
                precipitation_probability=85.0,
                forecast_precipitation_sum=55.0,
                current_humidity=90.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="flowering",
            ),
        ))
        disease_risks = risks_of(response, RiskCategory.DISEASE)
        assert len(disease_risks) == 1
        risk = disease_risks[0]
        assert risk.title == "Disease-Favourable Weather Conditions"
        # no fabricated diagnosis
        assert "disease_model_elevated_probability" not in [
            e.signal for e in risk.evidence
        ]
        assert "no disease diagnosis" in risk.description

    def test_model_alone_without_weather_support(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            ml_predictions=[
                make_ml("disease_detection", prediction="rice blast",
                        probability=0.82),
            ],
        ))
        disease_risks = risks_of(response, RiskCategory.DISEASE)
        assert len(disease_risks) == 1
        risk = disease_risks[0]
        assert risk.title == "Elevated Disease Pressure"
        # single source: model's own probability reused with attribution
        assert risk.numerical_confidence == 0.82
        assert risk.confidence_source == ConfidenceSource.ML_MODEL


# =============================================================================
# 7. Pest + crop stage correlation
# =============================================================================


class TestPestCropStageCorrelation:
    def pest_context(self, **kwargs):
        values = dict(
            weather_context=make_weather(),
            crop_calendar_context=make_calendar(
                current_growth_stage="flowering",
            ),
            ml_predictions=[
                make_ml("pest_prediction", prediction="high",
                        probability=0.75),
            ],
        )
        values.update(kwargs)
        return make_context(**values)

    def test_elevated_pest_with_sensitive_stage(self):
        response = analyze(self.pest_context())
        pest_risks = risks_of(response, RiskCategory.PEST)
        assert len(pest_risks) == 1
        risk = pest_risks[0]
        assert risk.title == "Elevated Pest Risk"
        assert risk.affected_stage == "flowering"
        # single source (model), elevated + sensitive stage -> HIGH
        assert risk.severity == SeverityLevel.HIGH
        assert risk.priority == PriorityLevel.HIGH
        # model's own probability reused with attribution
        assert risk.numerical_confidence == 0.75
        assert risk.confidence_source == ConfidenceSource.ML_MODEL

    def test_elevated_pest_without_stage_context(self):
        response = analyze(self.pest_context(
            crop_calendar_context=make_calendar(),
        ))
        risk = risks_of(response, RiskCategory.PEST)[0]
        # elevated but not sensitive -> MEDIUM
        assert risk.severity == SeverityLevel.MEDIUM

    def test_pest_model_low_signal_is_opportunity_not_risk(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            crop_calendar_context=make_calendar(
                current_growth_stage="tillering",
            ),
            ml_predictions=[
                make_ml("pest_prediction", prediction="low",
                        probability=0.2),
            ],
        ))
        assert risks_of(response, RiskCategory.PEST) == []
        pest_opps = opps_of(response, OpportunityCategory.PEST)
        assert len(pest_opps) == 1
        assert pest_opps[0].title == "Reduced Pest Pressure"


# =============================================================================
# 8/9. Market risk and opportunity
# =============================================================================


class TestMarketRules:
    def test_decreasing_market_is_risk(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            market_context=make_market(
                forecast_trend="decreasing",
                forecast_change_percent=-5.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="grain filling",
            ),
        ))
        market_risks = risks_of(response, RiskCategory.MARKET)
        assert len(market_risks) == 1
        risk = market_risks[0]
        assert "Adverse Market Trend" in risk.title
        assert risk.severity in {
            SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL,
        }
        signals = {e.signal for e in risk.evidence}
        assert "market_forecast_decreasing" in signals
        assert "crop_market_match" in signals

    def test_increasing_market_is_opportunity(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            market_context=make_market(
                forecast_trend="increasing",
                forecast_change_percent=6.0,
            ),
        ))
        assert risks_of(response, RiskCategory.MARKET) == []
        market_opps = opps_of(response, OpportunityCategory.MARKET)
        assert len(market_opps) == 1
        opp = market_opps[0]
        assert "Favourable Market Trend" in opp.title
        assert opp.suggested_action
        assert "market_forecast_increasing" in [
            e.signal for e in opp.evidence
        ]

    def test_small_market_move_is_ignored(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            market_context=make_market(
                forecast_trend="decreasing",
                forecast_change_percent=-1.0,
            ),
        ))
        assert risks_of(response, RiskCategory.MARKET) == []
        assert opps_of(response, OpportunityCategory.MARKET) == []

    def test_non_matching_commodity_is_ignored(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            market_context=make_market(
                commodity="Wheat",
                forecast_trend="decreasing",
                forecast_change_percent=-5.0,
            ),
        ))
        assert risks_of(response, RiskCategory.MARKET) == []

    def test_crop_missing_skips_market_rules(self):
        response = analyze(make_context(
            crop=None,
            weather_context=make_weather(),
            market_context=make_market(
                forecast_trend="increasing",
                forecast_change_percent=6.0,
            ),
        ))
        assert opps_of(response, OpportunityCategory.MARKET) == []
        assert risks_of(response, RiskCategory.MARKET) == []
        assert DataQualityIssueType.MISSING_FIELD in [
            n.type for n in response.data_quality_notices
        ]


# =============================================================================
# 10. Yield + market interaction
# =============================================================================


def adverse_yield_context(**kwargs):
    values = dict(
        weather_context=make_weather(),
        market_context=make_market(
            forecast_trend="decreasing",
            forecast_change_percent=-5.0,
        ),
        crop_calendar_context=make_calendar(
            current_growth_stage="grain filling",
        ),
        ml_predictions=[
            make_ml(
                "crop_yield_prediction", prediction="3.4", unit="t/ha",
                metadata={"expected_change_percent": -10.0},
            ),
        ],
    )
    values.update(kwargs)
    return make_context(**values)


class TestYieldMarketInteraction:
    def test_adverse_yield_and_declining_market_form_combined_risk(self):
        response = analyze(adverse_yield_context())
        yield_risks = risks_of(response, RiskCategory.YIELD)
        assert len(yield_risks) == 1
        risk = yield_risks[0]
        assert "Yield and Market Risk" in risk.title
        signals = {e.signal for e in risk.evidence}
        assert {
            "yield_model_adverse_signal",
            "market_forecast_decreasing",
            "crop_market_match",
        } <= signals
        # the plain market risk is a separate underlying condition
        assert len(risks_of(response, RiskCategory.MARKET)) == 1

    def test_adverse_yield_and_declining_market_grading(self):
        risk = risks_of(
            analyze(adverse_yield_context()), RiskCategory.YIELD,
        )[0]
        # 2 corroborating sources (yield model + market), elevated, sensitive
        assert risk.severity == SeverityLevel.HIGH
        assert risk.confidence == ConfidenceLevel.MEDIUM
        # yield model reported no probability -> only base 0.5 documented
        assert risk.numerical_confidence == 0.5

    def test_favourable_yield_and_increasing_market_opportunity(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            market_context=make_market(
                forecast_trend="increasing",
                forecast_change_percent=6.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="maturity",
            ),
            ml_predictions=[
                make_ml(
                    "crop_yield_prediction", prediction="5.1", unit="t/ha",
                    metadata={"expected_change_percent": 12.0},
                ),
            ],
        ))
        yield_opps = opps_of(response, OpportunityCategory.YIELD)
        assert len(yield_opps) == 1
        opp = yield_opps[0]
        assert "Favourable Yield and Market Combination" in opp.title
        assert opp.numerical_confidence == 0.5
        assert opp.confidence == ConfidenceLevel.MEDIUM

    def test_yield_without_comparative_baseline_is_skipped_with_notice(
        self,
    ):
        response = analyze(make_context(
            weather_context=make_weather(),
            market_context=make_market(
                forecast_trend="decreasing",
                forecast_change_percent=-5.0,
            ),
            ml_predictions=[
                make_ml("crop_yield_prediction", prediction="4.0",
                        unit="t/ha"),
            ],
        ))
        assert risks_of(response, RiskCategory.YIELD) == []
        assert opps_of(response, OpportunityCategory.YIELD) == []
        insufficient = [
            n for n in response.data_quality_notices
            if n.type == DataQualityIssueType.INSUFFICIENT_BASELINE
        ]
        assert len(insufficient) == 1
        assert insufficient[0].source == "crop_yield_prediction"


# =============================================================================
# 11. Fertilizer contextualization
# =============================================================================


class TestFertilizerContext:
    def test_fertilizer_with_adverse_weather_is_timing_risk(self):
        response = analyze(make_context(
            weather_context=make_weather(
                precipitation_probability=85.0,
                forecast_precipitation_sum=60.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="tillering",
            ),
            ml_predictions=[
                make_ml("fertilizer_recommendation",
                        prediction="NPK 20-20-0", probability=0.8),
            ],
        ))
        fert_risks = risks_of(response, RiskCategory.FERTILIZER)
        assert len(fert_risks) == 1
        risk = fert_risks[0]
        assert risk.title == "Fertilizer Application Timing at Risk"
        assert "fertilizer_model_recommendation" in [
            e.signal for e in risk.evidence
        ]
        # contextualization only: the recommendation itself is not replaced
        assert "does not recompute it" in risk.reasoning

    def test_fertilizer_with_benign_weather_is_window_opportunity(self):
        response = analyze(make_context(
            weather_context=make_weather(
                precipitation_probability=5.0,
                forecast_precipitation_sum=0.0,
                temperature_max_forecast=28.0,
                temperature_min_forecast=18.0,
                wind_speed_max_forecast=8.0,
                current_humidity=50.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="tillering",
            ),
            ml_predictions=[
                make_ml("fertilizer_recommendation",
                        prediction="NPK 20-20-0", probability=0.8),
            ],
        ))
        assert risks_of(response, RiskCategory.FERTILIZER) == []
        fert_opps = opps_of(response, OpportunityCategory.FERTILIZER)
        assert len(fert_opps) == 1
        opp = fert_opps[0]
        assert "Fertilizer Application Window" in opp.title
        assert "fertilizer_model_recommendation" in [
            e.signal for e in opp.evidence
        ]

    def test_fertilizer_without_weather_context_is_skipped(self):
        response = analyze(make_context(
            crop_calendar_context=make_calendar(
                current_growth_stage="tillering",
            ),
            ml_predictions=[
                make_ml("fertilizer_recommendation",
                        prediction="NPK 20-20-0", probability=0.8),
            ],
        ))
        assert risks_of(response, RiskCategory.FERTILIZER) == []
        assert opps_of(response, OpportunityCategory.FERTILIZER) == []
        assert "weather" in notice_sources(
            response, DataQualityIssueType.MISSING_DATA,
        )


# =============================================================================
# 11b. Soil model contextual risk
# =============================================================================


class TestSoilContext:
    def test_soil_adverse_status_is_reported(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            ml_predictions=[
                make_ml("soil_analysis", prediction="soil degraded",
                        metadata={"soil_status": "degraded"}),
            ],
        ))
        soil_risks = risks_of(response, RiskCategory.SOIL)
        assert len(soil_risks) == 1
        risk = soil_risks[0]
        assert risk.title == "Adverse Soil Condition Reported by Model"
        assert risk.contributing_signals == ["soil_model_adverse_status"]
        # numeric soil values are not interpreted without a baseline
        assert "does not provide a reference baseline" in risk.reasoning

    def test_soil_numeric_only_is_not_interpreted(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            ml_predictions=[
                make_ml("soil_analysis", prediction="42.5",
                        unit="mg/kg"),
            ],
        ))
        assert risks_of(response, RiskCategory.SOIL) == []


# =============================================================================
# 12/13/14. Missing weather / market / ML prediction
# =============================================================================


class TestMissingData:
    def test_missing_weather_skips_weather_rules(self):
        response = analyze(make_context(
            market_context=make_market(),
            crop_calendar_context=make_calendar(
                current_growth_stage="tillering",
            ),
        ))
        assert risks_of(response, RiskCategory.WEATHER) == []
        assert opps_of(response, OpportunityCategory.WEATHER) == []
        notices = [
            n for n in response.data_quality_notices
            if n.source == "weather"
            and n.type == DataQualityIssueType.MISSING_DATA
        ]
        assert len(notices) == 1
        assert "no values were substituted" in notices[0].message
        assert "weather_rules" in notices[0].affected_analysis

    def test_missing_market_skips_market_rules(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            ml_predictions=[
                make_ml(
                    "crop_yield_prediction", prediction="3.4",
                    metadata={"expected_change_percent": -10.0},
                ),
            ],
        ))
        assert risks_of(response, RiskCategory.MARKET) == []
        assert risks_of(response, RiskCategory.YIELD) == []
        assert opps_of(response, OpportunityCategory.MARKET) == []
        assert "market" in notice_sources(
            response, DataQualityIssueType.MISSING_DATA,
        )

    def test_missing_crop_calendar_reports_stage_skip(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            market_context=make_market(),
        ))
        notices = [
            n for n in response.data_quality_notices
            if n.source == "crop_calendar"
        ]
        assert notices
        assert "no stage was assumed" in notices[0].message

    def test_unavailable_ml_model_is_reported_not_fabricated(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            ml_predictions=[
                make_ml("disease_detection", status="unavailable"),
                make_ml("pest_prediction", status="error"),
            ],
        ))
        # no disease/pest item derived from unavailable models
        assert risks_of(response, RiskCategory.DISEASE) == []
        assert risks_of(response, RiskCategory.PEST) == []
        unavailable = [
            n for n in response.data_quality_notices
            if n.type == DataQualityIssueType.UNAVAILABLE_MODEL
        ]
        assert {n.source for n in unavailable} == {
            "disease_detection", "pest_prediction",
        }
        assert response.data_quality.unavailable_ml_models == [
            "disease_detection", "pest_prediction",
        ]
        for notice in unavailable:
            assert "not fabricated" in notice.message


# =============================================================================
# 15. Stale data
# =============================================================================


def stale_freshness(days=10):
    stamp = datetime.now(timezone.utc) - timedelta(days=days)
    return {"weather": stamp.isoformat()}


class TestStaleData:
    def test_stale_weather_is_reported_and_items_marked_monitoring(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            data_freshness=stale_freshness(),
        ))
        stale_notices = [
            n for n in response.data_quality_notices
            if n.type == DataQualityIssueType.STALE_DATA
        ]
        assert [n.source for n in stale_notices] == ["weather"]
        assert str(STALENESS_DAYS_THRESHOLD) in stale_notices[0].message
        assert "monitoring" in stale_notices[0].message
        # every risk whose evidence depends on weather is downgraded in status
        weather_dependent = [
            r for r in response.risks
            if "weather" in {s.source for s in r.contributing_sources}
        ]
        assert weather_dependent
        for risk in weather_dependent:
            assert risk.status == ItemStatus.MONITORING
            assert "stale" in risk.confidence_rationale

    def test_fresh_weather_is_not_marked_stale(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            data_freshness={"weather": datetime.now(
                timezone.utc,
            ).isoformat()},
        ))
        assert not [
            n for n in response.data_quality_notices
            if n.type == DataQualityIssueType.STALE_DATA
        ]
        for risk in response.risks:
            assert risk.status == ItemStatus.ACTIVE

    def test_source_without_timestamp_is_never_stale(self):
        response = analyze(make_context(weather_context=make_weather()))
        assert response.data_quality.stale_sources == []
        assert not [
            n for n in response.data_quality_notices
            if n.type == DataQualityIssueType.STALE_DATA
        ]


# =============================================================================
# 16. Conflicting signals
# =============================================================================


def rainfall_irrigation_context(decision_output=None):
    return make_context(
        decision_output=decision_output,
        weather_context=make_weather(
            precipitation_probability=85.0,
            forecast_precipitation_sum=55.0,
        ),
        ml_predictions=[
            make_ml(
                "smart_irrigation", prediction="irrigation_required",
                probability=0.9,
                metadata={"irrigation_required": True},
            ),
        ],
    )


class TestConflicts:
    def test_rainfall_vs_irrigation_conflict_is_surfaced(self):
        response = analyze(rainfall_irrigation_context())
        assert response.status == DecisionStatus.conflicting_signals
        assert len(response.conflict_notices) == 1
        conflict = response.conflict_notices[0]
        assert conflict.type == ConflictType.RAINFALL_VS_IRRIGATION_NEED
        assert conflict.detected_by == "risk_opportunity"
        assert conflict.unresolved_reason
        assert conflict.recommended_action
        assert {"weather", "smart_irrigation"} <= set(conflict.sources)

    def test_conflict_becomes_single_data_quality_risk(self):
        response = analyze(rainfall_irrigation_context())
        dq_risks = risks_of(response, RiskCategory.DATA_QUALITY)
        assert len(dq_risks) == 1
        risk = dq_risks[0]
        assert risk.title == "Conflicting Signals Detected"
        assert risk.confidence_rationale
        # the silent water-stress rule must not also claim irrigation need
        assert risks_of(response, RiskCategory.IRRIGATION) == []

    def test_conflict_is_never_silently_resolved(self):
        response = analyze(rainfall_irrigation_context())
        risk = risks_of(response, RiskCategory.DATA_QUALITY)[0]
        assert "does not silently choose" in risk.reasoning
        assert response.data_quality.status == (
            DecisionStatus.conflicting_signals.value
        )

    def test_conflict_attributed_to_decision_engine_when_upstream_found(
        self,
    ):
        de_output = make_de_output([
            make_de_decision(
                DecisionType.conflicting_signals,
                title="Rain vs irrigation conflict",
                decision_id="dec-conflict",
            ),
        ])
        response = analyze(
            rainfall_irrigation_context(decision_output=de_output),
        )
        assert len(response.conflict_notices) == 1
        conflict = response.conflict_notices[0]
        assert conflict.detected_by == "decision_engine"
        assert "Decision Engine independently reported" in (
            conflict.description
        )

    def test_market_vs_yield_conflict_is_surfaced(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            market_context=make_market(
                forecast_trend="increasing",
                forecast_change_percent=6.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="grain filling",
            ),
            ml_predictions=[
                make_ml(
                    "crop_yield_prediction", prediction="3.1", unit="t/ha",
                    metadata={"expected_change_percent": -8.0},
                ),
            ],
        ))
        assert response.status == DecisionStatus.conflicting_signals
        types = {c.type for c in response.conflict_notices}
        assert ConflictType.MARKET_VS_YIELD in types
        conflict = next(
            c for c in response.conflict_notices
            if c.type == ConflictType.MARKET_VS_YIELD
        )
        assert conflict.detected_by == "risk_opportunity"
        assert set(conflict.sources) == {"crop_yield_prediction", "market"}

    def test_no_conflict_in_fully_agreeing_context(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            market_context=make_market(),
            ml_predictions=[
                make_ml(
                    "smart_irrigation", prediction="no_irrigation",
                    metadata={"irrigation_required": False},
                ),
            ],
        ))
        assert response.conflict_notices == []
        assert response.status != DecisionStatus.conflicting_signals


# =============================================================================
# 17. Duplicate suppression / 18. Severity / 19. Priority (documented ladders)
# =============================================================================


class TestDuplicateSuppression:
    def test_weather_and_disease_signals_do_not_duplicate(self):
        response = analyze(disease_context())
        # humidity + rain + disease model + susceptible stage produce ONE
        # consolidated disease risk - not four separate entries
        assert len(risks_of(response, RiskCategory.DISEASE)) == 1
        # and the underlying weather rain hazard is a distinct condition
        # reported exactly once as well
        rain_risks = [
            r for r in risks_of(response, RiskCategory.WEATHER)
            if "rain" in r.title.lower()
        ]
        assert len(rain_risks) == 1

    def test_consolidated_item_retains_all_evidence(self):
        response = analyze(disease_context())
        risk = risks_of(response, RiskCategory.DISEASE)[0]
        signals = [e.signal for e in risk.evidence]
        # no duplicate (signal, source) pairs inside the evidence list
        pairs = [(e.signal, e.source) for e in risk.evidence]
        assert len(pairs) == len(set(pairs))
        assert len(signals) >= 5

    def test_ids_are_deterministic_per_condition(self):
        first = analyze(disease_context())
        second = analyze(disease_context())
        assert [r.id for r in first.risks] == [r.id for r in second.risks]
        assert [r.id for r in first.opportunities] == [
            r.id for r in second.opportunities
        ]


class TestSeverityCalculation:
    """Direct tests of the documented deterministic severity ladder."""

    def test_critical_when_upstream_critical_and_multi_source(self):
        assert _severity_for_risk(
            source_count=2, elevated=True, sensitive=False,
            time_sensitive=False, upstream_priority="critical",
        ) == SeverityLevel.CRITICAL

    def test_critical_when_severe_and_sensitive(self):
        assert _severity_for_risk(
            source_count=1, elevated=True, sensitive=True,
            time_sensitive=True, upstream_priority=None, severe=True,
        ) == SeverityLevel.CRITICAL

    def test_critical_when_three_sources_and_sensitive(self):
        assert _severity_for_risk(
            source_count=3, elevated=False, sensitive=True,
            time_sensitive=False, upstream_priority=None,
        ) == SeverityLevel.CRITICAL

    def test_critical_when_two_sources_elevated_and_time_sensitive(self):
        assert _severity_for_risk(
            source_count=2, elevated=True, sensitive=False,
            time_sensitive=True, upstream_priority=None,
        ) == SeverityLevel.CRITICAL

    def test_high_when_two_sources_elevated(self):
        assert _severity_for_risk(
            source_count=2, elevated=True, sensitive=False,
            time_sensitive=False, upstream_priority=None,
        ) == SeverityLevel.HIGH

    def test_high_when_single_source_elevated_and_sensitive(self):
        assert _severity_for_risk(
            source_count=1, elevated=True, sensitive=True,
            time_sensitive=False, upstream_priority=None,
        ) == SeverityLevel.HIGH

    def test_medium_when_two_plain_sources(self):
        assert _severity_for_risk(
            source_count=2, elevated=False, sensitive=False,
            time_sensitive=False, upstream_priority=None,
        ) == SeverityLevel.MEDIUM

    def test_medium_when_single_elevated_source(self):
        assert _severity_for_risk(
            source_count=1, elevated=True, sensitive=False,
            time_sensitive=False, upstream_priority=None,
        ) == SeverityLevel.MEDIUM

    def test_low_when_single_plain_source(self):
        assert _severity_for_risk(
            source_count=1, elevated=False, sensitive=False,
            time_sensitive=False, upstream_priority=None,
        ) == SeverityLevel.LOW


class TestPriorityCalculation:
    """Direct tests of the documented deterministic priority ladders."""

    def test_critical_severity_forces_critical_priority(self):
        assert _priority_for_risk(
            SeverityLevel.CRITICAL, sensitive=False, time_sensitive=False,
            actionable=False,
        ) == PriorityLevel.CRITICAL

    def test_high_severity_time_sensitive_is_high_priority(self):
        assert _priority_for_risk(
            SeverityLevel.HIGH, sensitive=False, time_sensitive=True,
            actionable=True,
        ) == PriorityLevel.HIGH

    def test_high_severity_without_urgency_is_medium_priority(self):
        assert _priority_for_risk(
            SeverityLevel.HIGH, sensitive=False, time_sensitive=False,
            actionable=True,
        ) == PriorityLevel.MEDIUM

    def test_medium_severity_actionable_is_medium_priority(self):
        assert _priority_for_risk(
            SeverityLevel.MEDIUM, sensitive=False, time_sensitive=False,
            actionable=True,
        ) == PriorityLevel.MEDIUM

    def test_low_severity_is_low_priority(self):
        assert _priority_for_risk(
            SeverityLevel.LOW, sensitive=False, time_sensitive=False,
            actionable=True,
        ) == PriorityLevel.LOW

    def test_opportunity_priority_ladder(self):
        assert _priority_for_opportunity(
            source_count=2, time_bound=True,
        ) == PriorityLevel.HIGH
        assert _priority_for_opportunity(
            source_count=2, time_bound=False,
        ) == PriorityLevel.MEDIUM
        assert _priority_for_opportunity(
            source_count=1, time_bound=True,
        ) == PriorityLevel.MEDIUM
        assert _priority_for_opportunity(
            source_count=1, time_bound=False,
        ) == PriorityLevel.LOW


# =============================================================================
# 20. Confidence handling (never fabricated)
# =============================================================================


class TestConfidenceHandling:
    def test_single_plain_source_reports_insufficient_evidence(self):
        level, value, source, rationale = _confidence_for(
            source_count=1, ml_probability=None, upstream_confidence=None,
            upstream_confidence_rationale=None, stale=False,
        )
        assert level == ConfidenceLevel.INSUFFICIENT_EVIDENCE
        assert value is None
        assert source is None
        assert "not calculated" in rationale

    def test_documented_multi_source_method(self):
        level, value, source, rationale = _confidence_for(
            source_count=3, ml_probability=None, upstream_confidence=None,
            upstream_confidence_rationale=None, stale=False,
        )
        expected = min(0.9, 0.5 + 0.1 * (3 - 2))
        assert value == expected == 0.6
        assert source == ConfidenceSource.RISK_OPPORTUNITY
        assert "independent sources agree" in rationale
        # numeric -> category mapping is documented
        assert level == ConfidenceLevel.MEDIUM

    def test_ml_probability_bonus_and_cap(self):
        _, value, _, _ = _confidence_for(
            source_count=2, ml_probability=0.8, upstream_confidence=None,
            upstream_confidence_rationale=None, stale=False,
        )
        assert value == 0.5 + 0.1
        _, capped, _, _ = _confidence_for(
            source_count=9, ml_probability=0.9, upstream_confidence=None,
            upstream_confidence_rationale=None, stale=False,
        )
        assert capped == 0.9

    def test_upstream_confidence_reused_verbatim(self):
        level, value, source, rationale = _confidence_for(
            source_count=2, ml_probability=None, upstream_confidence=0.8,
            upstream_confidence_rationale="weather and model agree",
            stale=False,
        )
        assert value == 0.8
        assert source == ConfidenceSource.DECISION_ENGINE
        assert level == ConfidenceLevel.HIGH
        assert "weather and model agree" in rationale

    def test_single_source_model_probability_reused_with_attribution(self):
        fake_model = make_ml("disease_detection", probability=0.7)
        level, value, source, rationale = _confidence_for(
            source_count=1, ml_probability=None, upstream_confidence=None,
            upstream_confidence_rationale=None, stale=False,
            single_source_model=fake_model,
            single_source_probability=0.7,
        )
        assert value == 0.7
        assert source == ConfidenceSource.ML_MODEL
        assert "disease_detection" in rationale

    def test_stale_downgrades_confidence_level_only(self):
        level, value, _, rationale = _confidence_for(
            source_count=2, ml_probability=None, upstream_confidence=None,
            upstream_confidence_rationale=None, stale=True,
        )
        # numeric value unchanged; category downgraded one step
        assert value == 0.5
        assert level == ConfidenceLevel.LOW
        assert "stale" in rationale

    def test_numerical_confidence_always_bounded(self):
        response = analyze(disease_context())
        for item in list(response.risks) + list(response.opportunities):
            if item.numerical_confidence is not None:
                assert 0.0 <= item.numerical_confidence <= 1.0
                assert item.confidence_source is not None
            else:
                assert item.confidence == (
                    ConfidenceLevel.INSUFFICIENT_EVIDENCE
                )
                assert item.confidence_rationale


# =============================================================================
# 21. Evidence & explainability
# =============================================================================


def rich_context():
    """Multiple active sources for evidence-traceability tests."""
    return make_context(
        weather_context=make_weather(
            precipitation_probability=85.0,
            forecast_precipitation_sum=60.0,
            current_humidity=90.0,
        ),
        market_context=make_market(
            forecast_trend="decreasing",
            forecast_change_percent=-5.0,
        ),
        crop_calendar_context=make_calendar(
            current_growth_stage="flowering",
        ),
        ml_predictions=[
            make_ml("disease_detection", prediction="rice blast",
                    probability=0.82),
        ],
    )


class TestEvidenceGeneration:
    def test_every_risk_is_traceable(self):
        response = analyze(rich_context())
        assert response.risks
        for risk in response.risks:
            assert risk.id.startswith("ro-risk-")
            assert risk.title
            assert risk.description
            assert risk.reasoning
            assert risk.evidence
            assert risk.contributing_sources
            assert risk.recommended_follow_up
            assert risk.detected_at.endswith("+00:00")
            for entry in risk.evidence:
                assert entry.signal
                assert entry.source
            # contributing_signals mirrors the evidence signals (sorted)
            assert risk.contributing_signals == sorted({
                e.signal for e in risk.evidence
            })

    def test_every_opportunity_is_traceable(self):
        response = analyze(make_context(
            weather_context=make_weather(
                precipitation_probability=5.0,
                forecast_precipitation_sum=0.0,
                temperature_max_forecast=28.0,
                temperature_min_forecast=18.0,
                wind_speed_max_forecast=8.0,
                current_humidity=50.0,
            ),
            market_context=make_market(
                forecast_trend="increasing",
                forecast_change_percent=6.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="tillering",
                expected_harvest_window_start=date(2026, 9, 15),
                expected_harvest_window_end=date(2026, 10, 5),
            ),
            ml_predictions=[
                make_ml("disease_detection", prediction="healthy",
                        probability=0.1),
            ],
        ))
        assert response.opportunities
        for opp in response.opportunities:
            assert opp.id.startswith("ro-opp-")
            assert opp.reasoning
            assert opp.evidence
            assert opp.contributing_sources
            assert opp.suggested_action
            assert opp.detected_at.endswith("+00:00")

    def test_sources_identify_upstream_modules(self):
        response = analyze(rich_context())
        disease = risks_of(response, RiskCategory.DISEASE)[0]
        source_names = {s.source for s in disease.contributing_sources}
        assert {"disease_detection", "weather"} <= source_names
        for source in disease.contributing_sources:
            assert source.source_type.value in {
                "external_data", "ml_model", "decision_engine",
                "farmer_context",
            }
            assert source.detail


# =============================================================================
# 21b. Decision Engine integration (consume, attribute, never recompute)
# =============================================================================


def de_disease_context(*, priority=Priority.HIGH, confidence=0.8):
    context = disease_context()
    context.decision_engine_output = make_de_output([
        make_de_decision(
            DecisionType.disease_weather_risk,
            priority=priority,
            confidence=confidence,
            title="Disease risk with weather support",
            decision_id="dec-disease",
        ),
    ])
    return context


class TestDecisionEngineIntegration:
    def test_upstream_confidence_is_reused_with_attribution(self):
        risk = risks_of(
            analyze(de_disease_context(confidence=0.8)),
            RiskCategory.DISEASE,
        )[0]
        assert risk.numerical_confidence == 0.8
        assert risk.confidence_source == ConfidenceSource.DECISION_ENGINE
        assert risk.confidence == ConfidenceLevel.HIGH
        assert "two sources agree" in risk.confidence_rationale

    def test_upstream_decision_is_a_contributing_source(self):
        risk = risks_of(
            analyze(de_disease_context()), RiskCategory.DISEASE,
        )[0]
        names = {s.source for s in risk.contributing_sources}
        assert "decision_engine" in names
        assert "Disease risk with weather support" in risk.reasoning

    def test_upstream_critical_priority_forces_critical_severity(self):
        risk = risks_of(
            analyze(de_disease_context(
                priority=Priority.CRITICAL, confidence=0.9,
            )),
            RiskCategory.DISEASE,
        )[0]
        # 2 corroborating sources + upstream critical -> CRITICAL (attributed)
        assert risk.severity == SeverityLevel.CRITICAL
        assert risk.priority == PriorityLevel.CRITICAL

    def test_without_de_output_nothing_is_attributed(self):
        response = analyze(disease_context())
        risk = risks_of(response, RiskCategory.DISEASE)[0]
        names = {s.source for s in risk.contributing_sources}
        assert "decision_engine" not in names
        assert "Decision Engine" not in risk.reasoning
        assert "decision_engine" in notice_sources(
            response, DataQualityIssueType.MISSING_DATA,
        )


# =============================================================================
# 11c. Crop stage rules (risk + opportunity)
# =============================================================================


class TestCropStageRules:
    def test_sensitive_stage_approaching_during_adverse_weather(self):
        response = analyze(make_context(
            weather_context=make_weather(
                precipitation_probability=85.0,
                forecast_precipitation_sum=60.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="vegetative",
                next_stage="flowering",
                days_to_next_stage=5,
            ),
        ))
        stage_risks = risks_of(response, RiskCategory.CROP_STAGE)
        assert len(stage_risks) == 1
        risk = stage_risks[0]
        assert risk.title.startswith("Sensitive Stage Approaching")
        assert risk.affected_stage == "flowering"
        assert risk.severity in {
            SeverityLevel.HIGH, SeverityLevel.CRITICAL,
        }
        assert risk.priority == PriorityLevel.HIGH
        signals = {e.signal for e in risk.evidence}
        assert {"next_growth_stage", "sensitive_stage_approaching"} <= signals

    def test_transition_risk_requires_imminent_sensitive_stage(self):
        response = analyze(make_context(
            weather_context=make_weather(
                precipitation_probability=85.0,
                forecast_precipitation_sum=60.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="vegetative",
                next_stage="harvest",
                days_to_next_stage=30,
            ),
        ))
        assert risks_of(response, RiskCategory.CROP_STAGE) == []

    def test_stage_transition_opportunity_under_benign_weather(self):
        response = analyze(make_context(
            weather_context=make_weather(
                precipitation_probability=5.0,
                forecast_precipitation_sum=0.0,
                temperature_max_forecast=28.0,
                temperature_min_forecast=18.0,
                wind_speed_max_forecast=8.0,
                current_humidity=50.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="tillering",
                next_stage="panicle initiation",
                days_to_next_stage=4,
            ),
        ))
        stage_opps = opps_of(response, OpportunityCategory.CROP_STAGE)
        assert len(stage_opps) == 1
        opp = stage_opps[0]
        assert "panicle initiation" in opp.title
        assert opp.time_window is not None
        assert "panicle initiation" in opp.time_window

    def test_harvest_window_opportunity(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            market_context=make_market(),
            crop_calendar_context=make_calendar(
                current_growth_stage="maturity",
                expected_harvest_window_start=date(2026, 9, 15),
                expected_harvest_window_end=date(2026, 10, 5),
            ),
        ))
        harvest_opps = opps_of(response, OpportunityCategory.HARVEST)
        assert len(harvest_opps) == 1
        opp = harvest_opps[0]
        assert opp.title == "Harvest Window Approaching"
        assert opp.time_window == "2026-09-15 to 2026-10-05"

    def test_no_harvest_opportunity_without_window(self):
        response = analyze(make_context(
            weather_context=make_weather(),
            crop_calendar_context=make_calendar(
                current_growth_stage="maturity",
            ),
        ))
        assert opps_of(response, OpportunityCategory.HARVEST) == []


# =============================================================================
# 22/23. Multiple simultaneous risks and opportunities
# =============================================================================


def multi_risk_context():
    """Heavy rain + heat + pest + declining market simultaneously."""
    return make_context(
        weather_context=make_weather(
            precipitation_probability=85.0,
            forecast_precipitation_sum=60.0,
            temperature_max_forecast=42.0,
        ),
        market_context=make_market(
            forecast_trend="decreasing",
            forecast_change_percent=-5.0,
        ),
        crop_calendar_context=make_calendar(
            current_growth_stage="flowering",
        ),
        ml_predictions=[
            make_ml("pest_prediction", prediction="high",
                    probability=0.75),
        ],
    )


class TestMultipleSimultaneousItems:
    def test_multiple_risks_are_returned_together(self):
        response = analyze(multi_risk_context())
        categories = {r.category for r in response.risks}
        assert {RiskCategory.WEATHER, RiskCategory.PEST,
                RiskCategory.MARKET} <= categories
        assert response.total_risks == len(response.risks) >= 3
        assert response.summary.risk_count == response.total_risks

    def test_risks_are_sorted_by_severity_then_priority(self):
        from app.intelligence.risk_opportunity import (
            PRIORITY_ORDER, SEVERITY_ORDER,
        )
        response = analyze(multi_risk_context())
        keys = [
            (SEVERITY_ORDER[r.severity], PRIORITY_ORDER[r.priority])
            for r in response.risks
        ]
        assert keys == sorted(keys)
        assert response.summary.highest_risk_severity == response.risks[
            0
        ].severity

    def test_category_counts_match_summary(self):
        response = analyze(multi_risk_context())
        counted = {}
        for risk in response.risks:
            counted[risk.category.value] = counted.get(
                risk.category.value, 0,
            ) + 1
        assert response.summary.risk_count_by_category == counted

    def test_risks_and_opportunities_can_coexist(self):
        # favourable market window while heavy rain falls
        response = analyze(make_context(
            weather_context=make_weather(
                precipitation_probability=85.0,
                forecast_precipitation_sum=60.0,
            ),
            market_context=make_market(
                forecast_trend="increasing",
                forecast_change_percent=6.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="flowering",
            ),
        ))
        assert response.risks
        assert opps_of(response, OpportunityCategory.MARKET)


class TestMultipleOpportunities:
    def multi_opportunity_context(self):
        """Benign weather + rising market + favourable models + calendar."""
        return make_context(
            weather_context=make_weather(
                precipitation_probability=5.0,
                forecast_precipitation_sum=0.0,
                temperature_max_forecast=28.0,
                temperature_min_forecast=18.0,
                wind_speed_max_forecast=8.0,
                current_humidity=50.0,
            ),
            market_context=make_market(
                forecast_trend="increasing",
                forecast_change_percent=6.0,
            ),
            crop_calendar_context=make_calendar(
                current_growth_stage="tillering",
                next_stage="panicle initiation",
                days_to_next_stage=5,
                expected_harvest_window_start=date(2026, 9, 15),
                expected_harvest_window_end=date(2026, 10, 5),
            ),
            ml_predictions=[
                make_ml("disease_detection", prediction="healthy",
                        probability=0.1),
                make_ml("pest_prediction", prediction="low",
                        probability=0.2),
            ],
        )

    def test_multiple_opportunities_are_returned_together(self):
        response = analyze(self.multi_opportunity_context())
        categories = {o.category for o in response.opportunities}
        assert {OpportunityCategory.MARKET, OpportunityCategory.DISEASE,
                OpportunityCategory.PEST} <= categories
        assert response.total_opportunities == len(
            response.opportunities,
        ) >= 3
        assert response.summary.opportunity_count == (
            response.total_opportunities
        )
        assert response.summary.highest_opportunity_priority is not None

    def test_opportunity_category_counts_match_summary(self):
        response = analyze(self.multi_opportunity_context())
        counted = {}
        for opp in response.opportunities:
            counted[opp.category.value] = counted.get(
                opp.category.value, 0,
            ) + 1
        assert response.summary.opportunity_count_by_category == counted


# =============================================================================
# 25. Existing backend regression (routers still registered)
# =============================================================================


def registered_paths():
    return {route.path for route in app.routes}


class TestBackendRegression:
    def test_existing_module_routes_still_registered(self):
        paths = registered_paths()
        assert "/" in paths
        assert "/health" in paths
        assert "/api/market/health" in paths
        assert "/api/weather/health" in paths
        assert "/api/weather/current" in paths
        assert "/api/weather/forecast" in paths
        assert "/api/crop-calendar/health" in paths
        assert "/api/crop-calendar/{crop}/schedule" in paths
        assert "/api/decision/health" in paths
        assert "/api/decision/evaluate" in paths
        assert "/api/v1/models/health" in paths

    def test_risk_opportunity_routes_registered(self):
        paths = registered_paths()
        assert "/api/risk-opportunity/health" in paths
        assert "/api/risk-opportunity/analyze" in paths
        assert "/api/risk-opportunity/categories" in paths

    def test_existing_health_endpoints_still_respond(self):
        for path in ("/", "/health", "/api/market/health"):
            response = test_client.get(path)
            assert response.status_code == 200, path

    def test_decision_engine_evaluate_still_works(self):
        response = test_client.post(
            "/api/decision/evaluate",
            json={
                "location": "West Bengal",
                "crop": "rice",
                "sowing_date": "2026-06-15",
                "as_of_date": "2026-09-19",
            },
        )
        assert response.status_code == 200
        assert "decisions" in response.json()

    def test_openapi_includes_all_modules(self):
        openapi = test_client.get("/openapi.json").json()
        paths = openapi["paths"]
        assert "/api/risk-opportunity/analyze" in paths
        assert "/api/decision/evaluate" in paths
        assert "/api/market/health" in paths




















