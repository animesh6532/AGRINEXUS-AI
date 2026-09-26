"""
Farm AI Copilot API Endpoints (/api/v1/assistant)

Provides production-quality endpoints for global AI Copilot interaction:
- POST /api/v1/assistant/chat: Standard JSON chat completion.
- POST /api/v1/assistant/chat/stream: SSE real-time streaming endpoint.
- POST /api/v1/assistant/analyze-image: Leaf/pest image inspection integration.
- GET  /api/v1/assistant/conversations: Conversation history list.
- GET  /api/v1/assistant/conversations/{id}: Single conversation messages.
- DELETE /api/v1/assistant/conversations/{id}: Delete conversation session.
- POST /api/v1/assistant/conversations/{id}/title: Update conversation title.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.database.connection import get_db
from app.database.models import Conversation, Message, FarmerProfile
from app.services.assistant_orchestrator import AssistantOrchestrator
from app.services.model_registry import ModelRegistry


router = APIRouter(prefix="/assistant", tags=["assistant"])


def get_current_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-ID")) -> str:
    """Extract authenticated user identity from X-User-ID header or fallback default."""
    return x_user_id or "default_user"


class PageContextPayload(BaseModel):
    route: Optional[str] = None
    page_name: Optional[str] = None
    field_id: Optional[int] = None
    crop_id: Optional[int] = None
    crop_name: Optional[str] = None
    location_name: Optional[str] = None


class CopilotChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="Existing conversation session ID")
    message: str = Field(..., min_length=1, description="Farmer query message")
    page_context: Optional[PageContextPayload] = None
    field_id: Optional[int] = None
    crop_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TitleUpdatePayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


@router.post(
    "/chat",
    status_code=status.HTTP_200_OK,
    summary="Chat with Farm AI Copilot (JSON)",
)
async def chat_with_copilot(
    payload: CopilotChatRequest,
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Execute copilot reasoning and return structured JSON response."""
    try:
        p_ctx = payload.page_context.dict() if payload.page_context else None
        res = AssistantOrchestrator.process_chat(
            user_id=user_id,
            message=payload.message,
            conversation_id=payload.conversation_id,
            page_context=p_ctx,
            field_id=payload.field_id,
            crop_id=payload.crop_id,
            lat=payload.latitude,
            lon=payload.longitude,
        )
        return res
    except Exception as exc:
        logger.error("Copilot chat error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process assistant request.",
        )


@router.post(
    "/chat/stream",
    summary="Chat with Farm AI Copilot (SSE Streaming)",
)
async def stream_copilot_chat(
    payload: CopilotChatRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Stream SSE events for copilot interaction."""
    p_ctx = payload.page_context.dict() if payload.page_context else None
    return StreamingResponse(
        AssistantOrchestrator.process_chat_stream(
            user_id=user_id,
            message=payload.message,
            conversation_id=payload.conversation_id,
            page_context=p_ctx,
            field_id=payload.field_id,
            crop_id=payload.crop_id,
            lat=payload.latitude,
            lon=payload.longitude,
        ),
        media_type="text/event-stream",
    )


@router.post(
    "/analyze-image",
    status_code=status.HTTP_200_OK,
    summary="Analyze leaf or pest image via Copilot",
)
async def analyze_image_with_copilot(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    analysis_type: str = Form("disease"),  # "disease" or "pest"
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Upload plant leaf/pest photo, run ML prediction, and return grounded findings card."""
    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        reg = ModelRegistry()
        if analysis_type == "pest":
            prediction = reg.predict_pest_visual(contents)
            summary_text = f"Pest Analysis Result: Detected **{prediction.get('predicted_pest', 'Unknown Insect')}** with {prediction.get('confidence', 0)*100:.1f}% confidence."
        else:
            prediction = reg.predict_disease(contents)
            summary_text = f"Disease Diagnosis Result: Detected **{prediction.get('predicted_disease', 'Healthy/Unknown')}** with {prediction.get('confidence', 0)*100:.1f}% confidence."


        prompt_msg = f"Analyze attached plant image ({file.filename})"
        res = AssistantOrchestrator.process_chat(
            user_id=user_id,
            message=prompt_msg,
            conversation_id=conversation_id,
        )

        res["content"] = f"{summary_text}\n\n{res['content']}"
        res["metadata"] = {"card_type": "image_analysis_card", "prediction": prediction}
        return res
    except Exception as exc:
        logger.error("Image analysis copilot error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image inspection failed: {str(exc)}",
        )


@router.get(
    "/conversations",
    summary="List user's persistent conversations",
)
async def list_conversations(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Fetch history list of conversations for current authenticated user."""
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [c.to_dict() for c in convs]


@router.get(
    "/conversations/{conversation_id}",
    summary="Get conversation details and messages",
)
async def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Fetch messages in a specific conversation session."""
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    data = conv.to_dict()
    data["messages"] = [m.to_dict() for m in msgs]
    return data


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete conversation session",
)
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Delete a conversation session owned by user."""
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    db.delete(conv)
    db.commit()
    return {"status": "success", "message": f"Conversation {conversation_id} deleted."}


@router.post(
    "/conversations/{conversation_id}/title",
    status_code=status.HTTP_200_OK,
    summary="Update conversation title",
)
async def update_conversation_title(
    conversation_id: str,
    payload: TitleUpdatePayload,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Update title of a conversation session."""
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    conv.title = payload.title.strip()
    db.commit()
    return {"status": "success", "title": conv.title}
