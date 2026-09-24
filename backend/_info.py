"""Temporary helper: dump exact runtime contracts for test authoring."""
import json

from app.schemas.risk_opportunity import (
    RiskOpportunityContext,
    RiskOpportunityResponse,
    Risk,
    Opportunity,
)
from app.schemas.decision import (
    FarmContext,
    WeatherContext,
    MarketContext,
    CropCalendarContext,
    MLPrediction,
    DecisionResponse,
    Decision,
    DataQuality,
)
from app.services.risk_opportunity_service import RiskOpportunityService
import app.api.risk_opportunity as api


def fields(model):
    out = {}
    for name, field in model.model_fields.items():
        ann = str(field.annotation)
        req = "REQ" if field.is_required() else "opt"
        out[f"{name} [{req}]"] = ann
    return out


for model in (
    RiskOpportunityContext,
    FarmContext,
    WeatherContext,
    MarketContext,
    CropCalendarContext,
    MLPrediction,
    Decision,
    DecisionResponse,
    DataQuality,
    Risk,
    Opportunity,
    RiskOpportunityResponse,
):
    print(f"=== {model.__name__} ===")
    print(json.dumps(fields(model), indent=1))

print("=== Service public members ===")
print([m for m in dir(RiskOpportunityService) if not m.startswith("_")])

print("=== API routes ===")
for route in api.router.routes:
    print(sorted(route.methods), route.path)

# Minimal analysis ground truth
print("=== minimal analysis ===")
svc = RiskOpportunityService()
try:
    ctx = RiskOpportunityContext(farm_context=FarmContext())
    resp = svc.analyze(ctx)
    print("status:", resp.status)
    print("risks:", [(r.category.value, r.title, r.severity.value, r.priority.value, r.confidence) for r in resp.risks])
    print("opps:", [(o.category.value, o.title, o.priority.value, o.confidence) for o in resp.opportunities])
    print("dq notices:", [(n.type.value, n.source, n.message[:60]) for n in resp.data_quality_notices])
    print("conflicts:", [(c.type.value) for c in resp.conflict_notices])
    print("summary:", resp.summary.model_dump())
    print("total:", resp.total_risks, resp.total_opportunities)
except Exception as exc:  # noqa: BLE001
    print("MINIMAL FAILED:", type(exc).__name__, exc)

print("=== health ===")
print(json.dumps(svc.health(), indent=1, default=str))
try:
    print("=== categories keys ===")
    cats = svc.categories() if hasattr(svc, "categories") else None
    print(type(cats), list(cats.keys()) if isinstance(cats, dict) else cats)
except Exception as exc:  # noqa: BLE001
    print("categories failed:", exc)
