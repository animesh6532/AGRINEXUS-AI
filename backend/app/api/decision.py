"""
Decision Engine API endpoints.

Exposes the deterministic Context/Decision Engine: it consumes a
normalized FarmContext (built from existing Weather Intelligence, Market
Forecast and Crop Calendar outputs plus standardized ML prediction
contracts) and produces structured, explainable farming decisions.

The engine is NOT an ML model and performs no external API calls of its
own; it never fabricates missing predictions.

Error handling contract:
- 400: invalid request payload caught at the service layer (ValueError)
- 422: request body validation failures (FastAPI/Pydantic)
- 500: unexpected internal errors (no stack trace is exposed)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.logging import logger
from ..schemas.decision import (
    DecisionHealthResponse,
    DecisionResponse,
    FarmContext,
)
from ..services.decision_engine_service import DecisionEngineService

# Create router
router = APIRouter(
    prefix="/api/decision",
    tags=["decision"],
    responses={404: {"description": "Not found"}},
)

SERVICE_NAME = "agrinexus-decision-engine"


# Dependency injection
def get_decision_engine_service() -> DecisionEngineService:
    """Dependency to get the decision engine service."""
    return DecisionEngineService()


def _utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


@router.post(
    "/evaluate",
    response_model=DecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate a normalized farm context",
    description=(
        "Run the deterministic decision engine over a normalized "
        "FarmContext (weather/market/crop-calendar context plus "
        "standardized ML predictions) and return structured, explainable "
        "decisions with supporting signals, contributing sources, "
        "data-quality assessment and documented priority. Missing inputs "
        "are handled gracefully: they are reported, never substituted."
    ),
)
async def evaluate_context(
    context: FarmContext,
    service: DecisionEngineService = Depends(get_decision_engine_service),
) -> DecisionResponse:
    """Evaluate a normalized FarmContext and return explainable decisions."""
    logger.info(
        f"Evaluating farm context: crop={context.crop}, "
        f"location={context.location}, "
        f"weather={context.weather_context is not None}, "
        f"market={context.market_context is not None}, "
        f"calendar={context.crop_calendar_context is not None}, "
        f"ml_predictions={len(context.ml_predictions)}"
    )
    try:
        response = service.evaluate(context)
        logger.info(
            f"Decision evaluation complete: status={response.status}, "
            f"decisions={response.total_decisions}"
        )
        return response
    except ValueError as exc:
        logger.error(f"Invalid decision evaluation request: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Decision evaluation failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/health",
    response_model=DecisionHealthResponse,
    summary="Decision Engine health check",
    description=(
        "Report decision engine availability, version and ruleset "
        "version. Exposes no secrets, API keys or credentials."
    ),
)
async def decision_health(
    service: DecisionEngineService = Depends(get_decision_engine_service),
) -> DecisionHealthResponse:
    """Health snapshot for the Decision Engine."""
    logger.info("Decision Engine health check requested")
    health = service.health()
    return DecisionHealthResponse(
        status=health["status"],
        service=health["service"],
        version=health["version"],
        timestamp=_utc_now_iso(),
        engine_available=health["engine_available"],
        ruleset_version=health["ruleset_version"],
        ml_model_contracts_available=health["ml_model_contracts_available"],
    )