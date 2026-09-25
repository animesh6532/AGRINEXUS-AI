"""
Smart Alerts API endpoints. Consumes RiskOpportunityResponse and
returns deterministic traceable alerts. No external calls, no ML.

Errors: 400 service ValueError, 422 body validation, 500 unexpected.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.logging import logger
from ..intelligence.smart_alert import ENGINE_VERSION, RULESET_VERSION
from ..schemas.smart_alert import (
    AlertPriority, AlertType, SmartAlertHealthResponse,
    SmartAlertRequest, SmartAlertResponse, SmartAlertRulesResponse,
)
from ..services.smart_alert_service import SmartAlertService

router = APIRouter(
    prefix="/api/smart-alerts",
    tags=["smart-alerts"],
    responses={404: {"description": "Not found"}},
)


def get_smart_alert_service() -> SmartAlertService:
    return SmartAlertService()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post(
    "/generate",
    response_model=SmartAlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate smart alerts from Risk & Opportunity output",
)
async def generate_smart_alerts(
    request: SmartAlertRequest,
    service: SmartAlertService = Depends(get_smart_alert_service),
) -> SmartAlertResponse:
    logger.info("Generating smart alerts: risks=%d opportunities=%d",
                len(request.risk_opportunity.risks),
                len(request.risk_opportunity.opportunities))
    try:
        response = service.generate(request.risk_opportunity, request.preferences)
        logger.info("Smart alerts complete: total=%d suppressed=%d",
                    response.total_alerts, response.suppressed_count)
        return response
    except ValueError as exc:
        logger.error("Invalid smart alerts request: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Smart alerts generation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal server error")


@router.get(
    "/health",
    response_model=SmartAlertHealthResponse,
    summary="Smart Alerts health check",
)
async def smart_alerts_health(
    service: SmartAlertService = Depends(get_smart_alert_service),
) -> SmartAlertHealthResponse:
    logger.info("Smart Alerts health check requested")
    health = service.health()
    return SmartAlertHealthResponse(
        status=health["status"], service=health["service"],
        version=health["version"], timestamp=_utc_now_iso(),
        engine_available=health["engine_available"],
        ruleset_version=health["ruleset_version"],
        upstream_dependencies=health["upstream_dependencies"],
    )


@router.get(
    "/rules",
    response_model=SmartAlertRulesResponse,
    summary="Smart Alerts ruleset",
)
async def smart_alerts_rules(
    service: SmartAlertService = Depends(get_smart_alert_service),
) -> SmartAlertRulesResponse:
    rules = service.describe_rules()
    return SmartAlertRulesResponse(
        ruleset_version=rules["ruleset_version"],
        engine_version=rules["engine_version"],
        rules=rules["rules"],
        priority_order=rules["priority_order"],
        type_order=rules["type_order"],
        timestamp=_utc_now_iso(),
    )
