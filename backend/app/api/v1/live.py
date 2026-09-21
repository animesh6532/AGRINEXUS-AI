"""
Live Camera Computer Vision Endpoints (REST & WebSocket).
Provides real-time frame inference with OpenCV quality gates, session-isolated temporal prediction smoothing,
and frame skipping for invalid/blurry inputs for Plant Disease Detection and Visual Pest Classification.
"""

import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, File, UploadFile, Header, WebSocket, WebSocketDisconnect, HTTPException, status
from pydantic import BaseModel, Field

from ...services.model_registry import ModelRegistry
from ...services.temporal_smoother import TemporalSmoother
from ...services.cv_service import CVService
from ...core.config import settings
from ...core.logging import logger

router = APIRouter(tags=["live_cv"])

# Session registry for REST live endpoints (keyed by session_id)
_rest_disease_sessions: Dict[str, TemporalSmoother] = {}
_rest_pest_sessions: Dict[str, TemporalSmoother] = {}


def _get_rest_smoother(session_id: str, session_dict: Dict[str, TemporalSmoother]) -> TemporalSmoother:
    """Get or create session-specific temporal smoother for REST live streaming."""
    if session_id not in session_dict:
        # Keep maximum 100 active sessions to prevent memory leaks
        if len(session_dict) > 100:
            session_dict.clear()
        session_dict[session_id] = TemporalSmoother(buffer_size=settings.SMOOTHING_BUFFER_SIZE)
    return session_dict[session_id]


class FramePredictionResponse(BaseModel):
    success: bool = True
    stream: str
    prediction: str
    confidence: float
    raw_prediction: str
    raw_confidence: float
    quality_report: Dict[str, Any]
    timestamp: float


# ------------------------------------------------------------------
# 1. PLANT DISEASE LIVE CAM (REST POST + WEBSOCKET)
# ------------------------------------------------------------------
@router.post(
    "/disease/live",
    response_model=FramePredictionResponse,
    summary="Process live camera video frame for disease detection",
    description="Evaluates single frame from live video feed using OpenCV quality check, frozen ResNet18 model, and session-isolated temporal smoothing."
)
async def process_disease_live_frame(
    file: UploadFile = File(...),
    x_session_id: Optional[str] = Header("default_disease_session")
):
    """Process a single live video frame for disease detection."""
    contents = await file.read()
    registry = ModelRegistry()

    try:
        # 1. Inspect OpenCV Image Quality first
        quality_report = CVService.inspect_image_bytes(contents)
        smoother = _get_rest_smoother(x_session_id, _rest_disease_sessions)

        # 2. Skip inference if frame quality is unacceptable
        if not quality_report["is_valid"]:
            stable_pred, stable_conf = smoother.get_smoothed_prediction()
            return FramePredictionResponse(
                stream="disease_live",
                prediction=stable_pred if stable_pred != "Unknown" else "Frame Skipped (Low Quality)",
                confidence=stable_conf,
                raw_prediction="Skipped",
                raw_confidence=0.0,
                quality_report=quality_report,
                timestamp=time.time()
            )

        # 3. Run Disease Model without Grad-CAM for high-throughput live stream
        raw_res = registry.predict_disease(contents, include_gradcam=False)
        raw_pred = raw_res["predicted_disease"]
        raw_conf = raw_res["confidence"]

        # 4. Temporal prediction smoothing
        smoother.add_prediction(raw_pred, raw_conf)
        stable_pred, stable_conf = smoother.get_smoothed_prediction()

        return FramePredictionResponse(
            stream="disease_live",
            prediction=stable_pred,
            confidence=stable_conf,
            raw_prediction=raw_pred,
            raw_confidence=raw_conf,
            quality_report=quality_report,
            timestamp=time.time()
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Live frame processing error: {str(e)}")


@router.websocket("/disease/live")
@router.websocket("/ws/disease/live")
async def websocket_disease_live(websocket: WebSocket):
    """WebSocket endpoint for continuous live camera disease prediction stream."""
    await websocket.accept()
    logger.info("WebSocket connection established for disease live camera stream.")
    registry = ModelRegistry()
    local_smoother = TemporalSmoother(buffer_size=settings.SMOOTHING_BUFFER_SIZE)

    last_eval_time = 0.0
    min_frame_interval = 1.0 / max(1, settings.LIVE_FRAME_SAMPLING_FPS)

    try:
        while True:
            data = await websocket.receive_bytes()
            now = time.time()

            if (now - last_eval_time) < min_frame_interval:
                continue
            last_eval_time = now

            try:
                # 1. Check frame quality before running inference
                quality_report = CVService.inspect_image_bytes(data)

                if not quality_report["is_valid"]:
                    stable_pred, stable_conf = local_smoother.get_smoothed_prediction()
                    await websocket.send_json({
                        "success": True,
                        "is_valid_frame": False,
                        "prediction": stable_pred if stable_pred != "Unknown" else "Frame Skipped (Low Quality)",
                        "confidence": stable_conf,
                        "warnings": quality_report["warnings"],
                        "timestamp": now
                    })
                    continue

                # 2. Run inference on valid frame without Grad-CAM
                raw_res = registry.predict_disease(data, include_gradcam=False)
                raw_pred = raw_res["predicted_disease"]
                raw_conf = raw_res["confidence"]

                # 3. Add to session-isolated temporal smoother
                local_smoother.add_prediction(raw_pred, raw_conf)
                stable_pred, stable_conf = local_smoother.get_smoothed_prediction()

                await websocket.send_json({
                    "success": True,
                    "is_valid_frame": True,
                    "prediction": stable_pred,
                    "confidence": stable_conf,
                    "raw_prediction": raw_pred,
                    "raw_confidence": raw_conf,
                    "warnings": quality_report["warnings"],
                    "timestamp": now
                })
            except Exception as frame_err:
                await websocket.send_json({
                    "success": False,
                    "error": str(frame_err),
                    "timestamp": now
                })
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for disease live stream.")


# ------------------------------------------------------------------
# 2. PEST VISUAL RECOGNITION LIVE CAM (REST POST + WEBSOCKET)
# ------------------------------------------------------------------
@router.post(
    "/pest/live",
    response_model=FramePredictionResponse,
    summary="Process live camera video frame for pest recognition",
    description="Evaluates single frame from live video feed using MobileNetV3 Small insect classification model and session-isolated temporal smoothing."
)
async def process_pest_live_frame(
    file: UploadFile = File(...),
    x_session_id: Optional[str] = Header("default_pest_session")
):
    """Process a single live video frame for visual pest recognition."""
    contents = await file.read()
    registry = ModelRegistry()

    try:
        quality_report = CVService.inspect_image_bytes(contents)
        smoother = _get_rest_smoother(x_session_id, _rest_pest_sessions)

        if not quality_report["is_valid"]:
            stable_pred, stable_conf = smoother.get_smoothed_prediction()
            return FramePredictionResponse(
                stream="pest_live",
                prediction=stable_pred if stable_pred != "Unknown" else "Frame Skipped (Low Quality)",
                confidence=stable_conf,
                raw_prediction="Skipped",
                raw_confidence=0.0,
                quality_report=quality_report,
                timestamp=time.time()
            )

        raw_res = registry.predict_pest_visual(contents)
        raw_pred = raw_res["predicted_pest"]
        raw_conf = raw_res["confidence"]

        smoother.add_prediction(raw_pred, raw_conf)
        stable_pred, stable_conf = smoother.get_smoothed_prediction()

        return FramePredictionResponse(
            stream="pest_live",
            prediction=stable_pred,
            confidence=stable_conf,
            raw_prediction=raw_pred,
            raw_confidence=raw_conf,
            quality_report=quality_report,
            timestamp=time.time()
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Live pest frame processing error: {str(e)}")


@router.websocket("/pest/live")
@router.websocket("/ws/pest/live")
async def websocket_pest_live(websocket: WebSocket):
    """WebSocket endpoint for continuous live camera visual pest recognition stream."""
    await websocket.accept()
    logger.info("WebSocket connection established for pest live camera stream.")
    registry = ModelRegistry()
    local_smoother = TemporalSmoother(buffer_size=settings.SMOOTHING_BUFFER_SIZE)

    last_eval_time = 0.0
    min_frame_interval = 1.0 / max(1, settings.LIVE_FRAME_SAMPLING_FPS)

    try:
        while True:
            data = await websocket.receive_bytes()
            now = time.time()

            if (now - last_eval_time) < min_frame_interval:
                continue
            last_eval_time = now

            try:
                quality_report = CVService.inspect_image_bytes(data)

                if not quality_report["is_valid"]:
                    stable_pred, stable_conf = local_smoother.get_smoothed_prediction()
                    await websocket.send_json({
                        "success": True,
                        "is_valid_frame": False,
                        "prediction": stable_pred if stable_pred != "Unknown" else "Frame Skipped (Low Quality)",
                        "confidence": stable_conf,
                        "warnings": quality_report["warnings"],
                        "timestamp": now
                    })
                    continue

                raw_res = registry.predict_pest_visual(data)
                raw_pred = raw_res["predicted_pest"]
                raw_conf = raw_res["confidence"]

                local_smoother.add_prediction(raw_pred, raw_conf)
                stable_pred, stable_conf = local_smoother.get_smoothed_prediction()

                await websocket.send_json({
                    "success": True,
                    "is_valid_frame": True,
                    "prediction": stable_pred,
                    "confidence": stable_conf,
                    "raw_prediction": raw_pred,
                    "raw_confidence": raw_conf,
                    "warnings": quality_report["warnings"],
                    "timestamp": now
                })
            except Exception as frame_err:
                await websocket.send_json({
                    "success": False,
                    "error": str(frame_err),
                    "timestamp": now
                })
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for pest live stream.")
