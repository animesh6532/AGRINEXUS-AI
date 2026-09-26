"""
Farming Assistant API Endpoints.

Provides:
- POST /api/farming-assistant/chat: Farmer conversational interaction.
- GET /api/farming-assistant/health: Health check and dependency status.
- GET /api/farming-assistant/capabilities: Supported crops, topics, and routing modes.
- GET /api/farming-assistant/kb-status: Verification status of the 10,000+ knowledge base.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import logger
from app.schemas.farming_assistant import (
    ChatRequest,
    ChatResponse,
    FarmingAssistantCapabilitiesResponse,
    FarmingAssistantHealthResponse,
    FarmingKnowledgeRecordCreate,
    KnowledgeBaseStatusResponse,
)
from app.services.farming_assistant_service import FarmingAssistantService

router = APIRouter(
    prefix="/api/farming-assistant",
    tags=["farming-assistant"],
    responses={404: {"description": "Not found"}},
)

_assistant_service_instance = None


def get_farming_assistant_service() -> FarmingAssistantService:
    """Dependency provider returning singleton instance of FarmingAssistantService."""
    global _assistant_service_instance
    if _assistant_service_instance is None:
        _assistant_service_instance = FarmingAssistantService()
    return _assistant_service_instance


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with the AI Farming Assistant",
)
async def chat_with_assistant(
    request: ChatRequest,
    service: FarmingAssistantService = Depends(get_farming_assistant_service),
) -> ChatResponse:
    """
    Conversational agricultural endpoint.
    Performs farming-only scope gating, routing between static knowledge base and
    dynamic AGRINEXUS modules, and returns grounded answers with preserved sources.
    """
    try:
        response = service.chat(request)
        return response
    except ValueError as exc:
        logger.warning("Farming assistant validation error: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Farming assistant unexpected error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the farming assistant request.",
        )


@router.get(
    "/health",
    response_model=FarmingAssistantHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Farming Assistant health check",
)
async def assistant_health(
    service: FarmingAssistantService = Depends(get_farming_assistant_service),
) -> FarmingAssistantHealthResponse:
    """Returns service health, local embedding status, and verified knowledge base record count."""
    health_data = service.health()
    return FarmingAssistantHealthResponse(**health_data)


@router.get(
    "/capabilities",
    response_model=FarmingAssistantCapabilitiesResponse,
    status_code=status.HTTP_200_OK,
    summary="Farming Assistant capabilities",
)
async def assistant_capabilities(
    service: FarmingAssistantService = Depends(get_farming_assistant_service),
) -> FarmingAssistantCapabilitiesResponse:
    """Returns supported agricultural topics, crops, routing intents, and thresholds."""
    cap_data = service.capabilities()
    return FarmingAssistantCapabilitiesResponse(**cap_data)


@router.get(
    "/kb-status",
    response_model=KnowledgeBaseStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Knowledge Base status and 10,000+ verification",
)
async def kb_status(
    service: FarmingAssistantService = Depends(get_farming_assistant_service),
) -> KnowledgeBaseStatusResponse:
    """Returns knowledge base record count and verification status against the 10,000+ requirement."""
    status_data = service.get_kb_status()
    return KnowledgeBaseStatusResponse(**status_data)


@router.post(
    "/ingest",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a single verified farming knowledge record",
)
async def ingest_record(
    record: FarmingKnowledgeRecordCreate,
    service: FarmingAssistantService = Depends(get_farming_assistant_service),
) -> Dict[str, Any]:
    """Ingest a validated Q&A record and update the vector index."""
    try:
        created = service.ingest_record(record)
        return {
            "status": "success",
            "message": "Record ingested successfully",
            "record": created.to_dict(),
            "total_records": service.get_kb_record_count(),
        }
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to ingest knowledge record: {str(exc)}",
        )
