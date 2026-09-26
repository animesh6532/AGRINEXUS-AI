"""
Personalized Action Plan API endpoints. Consumes Decision Engine output,
Risk & Opportunity analysis and Smart Alerts; returns deterministic
traceable actions. No external calls, no ML.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.logging import logger
from ..schemas.action_plan import (
    ActionPlanCategoriesResponse, ActionPlanHealthResponse,
    ActionPlanRequest, ActionPlanResponse,
    ActionSourceType, ActionType,
)
from ..services.action_plan_service import ActionPlanService

router = APIRouter(prefix="/api/action-plan", tags=["action-plan"], responses={404: {"description": "Not found"}})


def get_action_plan_service() -> ActionPlanService:
    return ActionPlanService()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/generate", response_model=ActionPlanResponse, status_code=status.HTTP_200_OK, summary="Generate personalized action plan")
async def generate_action_plan(request: ActionPlanRequest, service: ActionPlanService = Depends(get_action_plan_service)) -> ActionPlanResponse:
    logger.info("Generating action plan")
    try:
        response = service.generate(request)
        logger.info("Action plan complete: total=%d suppressed=%d", response.total_actions, response.suppressed_count)
        return response
    except ValueError as exc:
        logger.error("Invalid action plan request: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Action plan generation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/health", response_model=ActionPlanHealthResponse, summary="Action Plan health check")
async def action_plan_health(service: ActionPlanService = Depends(get_action_plan_service)) -> ActionPlanHealthResponse:
    logger.info("Action Plan health check requested")
    health = service.health()
    return ActionPlanHealthResponse(status=health["status"], service=health["service"], version=health["version"], timestamp=_utc_now_iso(), engine_available=health["engine_available"], ruleset_version=health["ruleset_version"], upstream_dependencies=health["upstream_dependencies"])


@router.get("/categories", response_model=ActionPlanCategoriesResponse, summary="Action Plan vocabulary")
async def action_plan_categories(service: ActionPlanService = Depends(get_action_plan_service)) -> ActionPlanCategoriesResponse:
    rules = service.describe_rules()
    return ActionPlanCategoriesResponse(action_types=[{"value": t.value, "label": t.value.replace("_", " ").title()} for t in ActionType], priorities=[p for p in rules["priority_order"]], source_types=[s.value for s in ActionSourceType], ruleset_version=rules["ruleset_version"], engine_version=rules["engine_version"], timestamp=_utc_now_iso())
