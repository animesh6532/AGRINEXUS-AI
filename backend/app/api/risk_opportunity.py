"""
Risk & Opportunity Analysis API endpoints.

Exposes the deterministic Risk & Opportunity layer: it consumes a
normalized RiskOpportunityContext (FarmContext plus the Decision Engine
output for the same context) and returns structured, explainable risks
and opportunities.

The module is NOT an ML model and performs no external API calls of its
own; it never fabricates missing predictions.

Error handling contract:
- 400: invalid request payload caught at the service layer (ValueError)
- 422: request body validation failures (FastAPI/Pydantic)
- 500: unexpected internal errors (no stack trace is exposed)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.logging import logger
from ..intelligence.risk_opportunity import RULESET_VERSION
from ..schemas.risk_opportunity import (
    CategoryInfo,
    ConflictType,
    DataQualityIssueType,
    OpportunityCategory,
    PriorityLevel,
    RiskCategory,
    RiskOpportunityCategoriesResponse,
    RiskOpportunityContext,
    RiskOpportunityHealthResponse,
    RiskOpportunityResponse,
    SeverityLevel,
)
from ..services.risk_opportunity_service import RiskOpportunityService

router = APIRouter(
    prefix="/api/risk-opportunity",
    tags=["risk-opportunity"],
    responses={404: {"description": "Not found"}},
)

SERVICE_NAME = "agrinexus-risk-opportunity"


def get_risk_opportunity_service() -> RiskOpportunityService:
    """Dependency to get the risk & opportunity service."""
    return RiskOpportunityService()


def _utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


_RISK_CATEGORY_DESCRIPTIONS = {
    RiskCategory.WEATHER: "Weather-driven risks (rainfall, heat, frost, wind).",
    RiskCategory.IRRIGATION: "Water/irrigation risks from moisture and rainfall signals.",
    RiskCategory.DISEASE: "Disease pressure combining model and weather/stage context.",
    RiskCategory.PEST: "Pest pressure reported by the pest model with stage context.",
    RiskCategory.SOIL: "Adverse soil status explicitly reported by the soil model.",
    RiskCategory.FERTILIZER: "Fertilizer timing/context risks.",
    RiskCategory.MARKET: "Market price downside for the matching commodity.",
    RiskCategory.YIELD: "Yield/market relationship risks.",
    RiskCategory.CROP_STAGE: "Growth-stage transition risks.",
    RiskCategory.DATA_QUALITY: "Conflicting-signal and data-reliability risks.",
    RiskCategory.SYSTEM: "Reserved for system-level risk notices.",
}

_OPPORTUNITY_CATEGORY_DESCRIPTIONS = {
    OpportunityCategory.WEATHER: "Favourable weather windows for field operations.",
    OpportunityCategory.MARKET: "Market price upside for the matching commodity.",
    OpportunityCategory.IRRIGATION: "Efficient irrigation conditions.",
    OpportunityCategory.CROP_STAGE: "Favourable growth-stage transitions.",
    OpportunityCategory.DISEASE: "Reduced disease-pressure conditions.",
    OpportunityCategory.PEST: "Reduced pest-pressure conditions.",
    OpportunityCategory.FERTILIZER: "Favourable fertilizer application windows.",
    OpportunityCategory.YIELD: "Yield/market upside relationships.",
    OpportunityCategory.HARVEST: "Harvest-window planning opportunities.",
    OpportunityCategory.DATA: "Reserved for data-driven opportunity notices.",
}


def _category_infos(
    members, descriptions
) -> list[CategoryInfo]:
    """Documented category vocabulary for the categories endpoint."""
    return [
        CategoryInfo(
            value=member.value,
            label=member.value.replace("_", " ").title(),
            description=descriptions[member],
        )
        for member in members
    ]


def _enum_infos(members, meaning: str) -> list[CategoryInfo]:
    """Documented controlled vocabulary entries for levels/types."""
    return [
        CategoryInfo(
            value=member.value,
            label=member.value.replace("_", " ").title(),
            description=f"{meaning}: {member.value}.",
        )
        for member in members
    ]


@router.post(
    "/analyze",
    response_model=RiskOpportunityResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze risks and opportunities for a farm context",
    description=(
        "Run the deterministic Risk & Opportunity analysis over a "
        "normalized RiskOpportunityContext and return structured risks, "
        "opportunities, data-quality and conflict notices with evidence. "
        "Missing inputs are reported, never substituted."
    ),
)
async def analyze_risk_opportunity_endpoint(
    context: RiskOpportunityContext,
    service: RiskOpportunityService = Depends(get_risk_opportunity_service),
) -> RiskOpportunityResponse:
    """Analyze a normalized context and return risks/opportunities."""
    logger.info(
        "Analyzing risk & opportunity: crop=%s, location=%s, "
        "decision_output=%s, ml_predictions=%d",
        context.farm_context.crop,
        context.farm_context.location,
        context.decision_engine_output is not None,
        len(context.farm_context.ml_predictions),
    )
    try:
        response = service.analyze(context)
        logger.info(
            "Risk & opportunity analysis complete: status=%s, risks=%d, "
            "opportunities=%d",
            response.status,
            response.total_risks,
            response.total_opportunities,
        )
        return response
    except ValueError as exc:
        logger.error("Invalid risk & opportunity request: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Risk & opportunity analysis failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/health",
    response_model=RiskOpportunityHealthResponse,
    summary="Risk & Opportunity health check",
    description=(
        "Report Risk & Opportunity service availability, version, ruleset "
        "version and supported categories. Exposes no secrets, API keys or "
        "credentials."
    ),
)
async def risk_opportunity_health(
    service: RiskOpportunityService = Depends(get_risk_opportunity_service),
) -> RiskOpportunityHealthResponse:
    """Health snapshot for Risk & Opportunity Analysis."""
    logger.info("Risk & Opportunity health check requested")
    health = service.health()
    return RiskOpportunityHealthResponse(
        status=health["status"],
        service=health["service"],
        version=health["version"],
        timestamp=_utc_now_iso(),
        engine_available=health["engine_available"],
        ruleset_version=health["ruleset_version"],
        supported_risk_categories=health["supported_risk_categories"],
        supported_opportunity_categories=health[
            "supported_opportunity_categories"
        ],
        severity_levels=[level.value for level in SeverityLevel],
        priority_levels=[level.value for level in PriorityLevel],
        upstream_dependencies=health["upstream_dependencies"],
        ml_model_contracts_available=health["ml_model_contracts_available"],
    )


@router.get(
    "/categories",
    response_model=RiskOpportunityCategoriesResponse,
    summary="Risk & Opportunity ruleset vocabulary",
    description=(
        "Return the documented risk/opportunity categories, severity and "
        "priority levels, conflict types and data-quality issue types."
    ),
)
async def risk_opportunity_categories() -> RiskOpportunityCategoriesResponse:
    """Documented vocabulary of the Risk & Opportunity ruleset."""
    return RiskOpportunityCategoriesResponse(
        risk_categories=_category_infos(
            RiskCategory, _RISK_CATEGORY_DESCRIPTIONS
        ),
        opportunity_categories=_category_infos(
            OpportunityCategory, _OPPORTUNITY_CATEGORY_DESCRIPTIONS
        ),
        severity_levels=_enum_infos(
            SeverityLevel, "Deterministic risk severity level"
        ),
        priority_levels=_enum_infos(
            PriorityLevel, "Deterministic priority level"
        ),
        conflict_types=_enum_infos(ConflictType, "Conflict type"),
        data_quality_issue_types=_enum_infos(
            DataQualityIssueType, "Data-quality issue type"
        ),
        ruleset_version=RULESET_VERSION,
        timestamp=_utc_now_iso(),
    )
