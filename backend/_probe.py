"""Temporary probe: dump exact runtime contracts for test authoring."""
import json

from app.schemas.decision import FarmContext, DecisionResponse, MLPrediction, WeatherContext, MarketContext, CropCalendarContext
from app.schemas.risk_opportunity import RiskOpportunityContext, RiskOpportunityResponse, Risk, Opportunity
from app.services.risk_opportunity_service import RiskOpportunityService
from app.intelligence.risk_opportunity import analyze_risk_opportunity, ENGINE_VERSION, RULESET_VERSION


def req(model):
    return list(model.model_json_schema().get("required", []))


print("=== FarmContext required:", req(FarmContext))
print("=== FarmContext all fields:", list(FarmContext.model_fields))
print("=== WeatherContext fields:", list(WeatherContext.model_fields))
print("=== MarketContext fields:", list(MarketContext.model_fields))
print("=== CropCalendarContext fields:", list(CropCalendarContext.model_fields))
print("=== MLPrediction fields:", list(MLPrediction.model_fields))
print("=== RiskOpportunityContext fields:", list(RiskOpportunityContext.model_fields), "required:", req(RiskOpportunityContext))
print("=== DecisionResponse fields:", list(DecisionResponse.model_fields))
print("=== Risk fields:", list(Risk.model_fields))
print("=== Opportunity fields:", list(Opportunity.model_fields))
print("=== RiskOpportunityResponse fields:", list(RiskOpportunityResponse.model_fields))
print("=== service methods:", [m for m in dir(RiskOpportunityService) if not m.startswith("_")])
print("=== ENGINE_VERSION:", ENGINE_VERSION, "RULESET_VERSION:", RULESET_VERSION)

# Severity / priority / confidence enum values
print("=== Risk.severity enum:", Risk.model_fields["severity"].annotation)
print("=== Risk.priority enum:", Risk.model_fields["priority"].annotation)
print("=== Risk.confidence enum:", Risk.model_fields["confidence"].annotation)

# Build a rich context
farm = FarmContext(
    crop="rice",
    location="Pune, Maharashtra",
    sowing_date="2026-07-10",
    weather=WeatherContext(
        is_weather_data_available=True,
        current_temperature_c=36.0,
        current_humidity_percent=92.0,
        forecast_rainfall_mm=25.0,
        forecast_signals=["heavy_rainfall_expected", "high_humidity_disease_pressure"],
        data_timestamp="2026-09-20T00:00:00+00:00",
    ),
    market=MarketContext(
        is_market_data_available=True,
        commodity="rice",
        current_price=2100.0,
        forecast_trend="decreasing",
        forecast_change_percent=-8.5,
        signal_strength="strong",
        data_timestamp="2026-09-20T00:00:00+00:00",
    ),
    crop_calendar=CropCalendarContext(
        is_crop_calendar_available=True,
        current_stage="flowering",
        next_stage="maturity",
        days_to_next_stage=6,
        days_since_sowing=72,
        data_timestamp="2026-09-20T00:00:00+00:00",
    ),
    ml_predictions=[
        MLPrediction(model_name="disease_detection", prediction="Leaf blight", confidence=0.88, status="available"),
        MLPrediction(model_name="smart_irrigation", prediction="irrigation required", status="available", metadata={"irrigation_required": True}),
        MLPrediction(model_name="crop_yield_prediction", prediction="2100", unit="kg/ha", status="available", metadata={"comparative_yield_hint": "low"}),
        MLPrediction(model_name="fertilizer_recommendation", prediction="NPK 12:32:16 @ 50kg/acre", status="available"),
        MLPrediction(model_name="pest_prediction", prediction="Aphid risk elevated", confidence=0.7, status="available"),
        MLPrediction(model_name="soil_analysis", prediction="145", status="available"),
        MLPrediction(model_name="crop_recommendation", prediction="rice", status="available"),
    ],
)
ctx = RiskOpportunityContext(farm_context=farm)
resp = analyze_risk_opportunity(ctx)
print("=== status:", resp.status)
print("=== risks:")
for r in resp.risks:
    print("   -", r.category.value, "|", r.title, "| sev:", r.severity.value, "| pri:", r.priority.value, "| conf:", r.confidence.value, "| num:", r.numerical_confidence, "| src:", r.confidence_source)
print("=== opportunities:")
for o in resp.opportunities:
    print("   -", o.category.value, "|", o.title, "| pri:", o.priority.value, "| conf:", o.confidence.value, "| num:", o.numerical_confidence)
print("=== dq notices:", [(n.type.value, n.source) for n in resp.data_quality_notices])
print("=== conflicts:", [(c.type.value) for c in resp.conflict_notices])
print("=== summary:", resp.summary.model_dump() if hasattr(resp.summary, "model_dump") else resp.summary)
print("=== status value:", resp.status.value if hasattr(resp.status, "value") else resp.status)

# Minimal context
min_ctx = RiskOpportunityContext(farm_context=FarmContext(crop="wheat"))
min_resp = analyze_risk_opportunity(min_ctx)
print("=== MIN status:", min_resp.status.value if hasattr(min_resp.status, "value") else min_resp.status)
print("=== MIN risks:", [(r.title, r.severity.value) for r in min_resp.risks])
print("=== MIN opps:", [o.title for o in min_resp.opportunities])
print("=== MIN dq:", [(n.type.value, n.source) for n in min_resp.data_quality_notices])

# Service surface
svc = RiskOpportunityService()
print("=== svc.health keys:", sorted(svc.health().keys()) if callable(getattr(svc, "health", None)) else "no health")
for name in ("analyze", "analyze_risk_opportunity", "run"):
    print("=== svc has", name, ":", callable(getattr(svc, name, None)))
import inspect
for m in [m for m in dir(svc) if not m.startswith("_")]:
    attr = getattr(svc, m)
    if callable(attr):
        try:
            print("=== svc sig", m, inspect.signature(attr))
        except (ValueError, TypeError):
            pass
