"""Ground-truth probe: print schema fields and scenario outputs."""
import json

from app.schemas.decision import (
    FarmContext, WeatherContext, MarketContext, CropCalendarContext,
    MLPrediction, Decision, DecisionResponse,
)
from app.schemas.risk_opportunity import RiskOpportunityContext
from app.intelligence.risk_opportunity import analyze_risk_opportunity


def fields(cls):
    return {k: str(v.annotation) for k, v in cls.model_fields.items()}


print("=== FIELDS ===")
for cls in (FarmContext, WeatherContext, MarketContext, CropCalendarContext,
            MLPrediction, Decision, DecisionResponse):
    print(cls.__name__, json.dumps(fields(cls), indent=1))

print("=== SAMPLE ANALYSIS ===")
weather = WeatherContext(
    is_weather_data_available=True,
    temperature_c=34.0,
    humidity_percent=92.0,
    rainfall_mm=0.0,
    forecast_rainfall_mm=0.0,
    wind_speed_kmh=10.0,
    conditions="humid",
)
farm = FarmContext(
    crop="rice",
    growth_stage="flowering",
    weather=weather,
    ml_predictions=[
        MLPrediction(model_name="disease_detection", prediction="Blast",
                     confidence=0.8, status="available"),
        MLPrediction(model_name="smart_irrigation", prediction="irrigate now",
                     confidence=0.7, status="available"),
    ],
)
ctx = RiskOpportunityContext(farm_context=farm)
resp = analyze_risk_opportunity(ctx)
print("status:", resp.status)
print("risks:", [(r.title, r.severity.value, r.priority.value,
                  r.confidence, [s.signal for s in r.evidence],
                  [s.source for s in r.contributing_sources])
                 for r in resp.risks])
print("opps:", [(o.title, o.priority.value) for o in resp.opportunities])
print("dq_notices:", [(n.type.value, n.source, n.message) for n in resp.data_quality_notices])
print("conflicts:", [(c.type.value) for c in resp.conflict_notices])
print("summary:", resp.summary)
