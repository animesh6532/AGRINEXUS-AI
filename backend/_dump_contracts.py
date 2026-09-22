import io

from app.schemas.decision import (
    CropCalendarContext,
    DataQuality,
    Decision,
    DecisionResponse,
    FarmContext,
    MarketContext,
    MLPrediction,
    SupportingSignal,
    WeatherContext,
)
from app.schemas.risk_opportunity import (
    ConflictNotice,
    DataQualityNotice,
    Opportunity,
    Risk,
    RiskOpportunityContext,
    RiskOpportunityResponse,
    RiskOpportunitySummary,
)

out = []
for m in (
    FarmContext,
    WeatherContext,
    MarketContext,
    CropCalendarContext,
    MLPrediction,
    Decision,
    DecisionResponse,
    DataQuality,
    SupportingSignal,
    RiskOpportunityContext,
    RiskOpportunityResponse,
    Risk,
    Opportunity,
    DataQualityNotice,
    ConflictNotice,
    RiskOpportunitySummary,
):
    out.append(f"{m.__name__}: {list(m.model_fields.keys())}")

import app.intelligence.risk_opportunity as ro  # noqa: E402

out.append(f"ENGINE_VERSION={ro.ENGINE_VERSION} RULESET_VERSION={ro.RULESET_VERSION}")
out.append(f"KNOWN_ML_MODELS={getattr(ro, 'KNOWN_ML_MODELS', 'MISSING')}")
for name in (
    "ML_PROBABILITY_THRESHOLD",
    "STAGE_TRANSITION_IMMINENT_DAYS",
    "SEVERITY_ORDER",
    "PRIORITY_ORDER",
    "CONFIDENCE_ORDER",
    "RISK_RULES",
    "OPPORTUNITY_RULES",
):
    out.append(f"{name}={getattr(ro, name, 'MISSING')}")

import app.services.risk_opportunity_service as svc  # noqa: E402

out.append(
    "SERVICE_METHODS="
    + str([x for x in dir(svc.RiskOpportunityService) if not x.startswith("_")])
)

import app.api.risk_opportunity as api  # noqa: E402

out.append(
    "API_ROUTES="
    + str([(r.path, sorted(r.methods)) for r in api.router.routes])
)

from app.main import app as fastapi_app  # noqa: E402

out.append(
    "APP_ROUTES_WITH_RISK="
    + str([r.path for r in fastapi_app.routes if "risk" in getattr(r, "path", "")])
)

with io.open("_contracts_dump.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(str(x) for x in out))
print("OK")
