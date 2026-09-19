"""
Live Camera Computer Vision Endpoints (REST & WebSocket).
Provides real-time frame inference with OpenCV validation and temporal prediction smoothing
for Plant Disease Detection and Visual Pest Classification.
"""

import base64
import time
from typing import Dict, Any
from fastapi import APIRouter, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException, status
from pydantic import BaseModel, Field

from ...services.model_registry import ModelRegistry
from ...services.temporal_smoother import TemporalSmoother
from ...services.cv_service import CVService
from ...core.config import settings
from ...core.logging import logger

router = APIRouter(tags=["live_cv"])

# Singleton temporal smoothers for live streams
disease_smoother = TemporalSmoother(buffer_size=settings.SMOOTHING_BUFFER_SIZE)
pest_smoother = TemporalSmoother(buffer_size=settings.SMOOTHING_BUFFER_SIZE)


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
    description="Evaluates single frame from live video feed using OpenCV quality check, frozen ResNet18 model, and temporal smoothing buffer."
)
async def process_disease_live_frame(file: UploadFile = File(...)):
    """Process a single live video frame for disease detection."""
    contents = await file.read()
    registry = ModelRegistry()

    try:
        raw_res = registry.predict_disease(contents)
        raw_pred = raw_res["predicted_disease"]
        raw_conf = raw_res["confidence"]

        # Temporal prediction smoothing
        disease_smoother.add_prediction(raw_pred, raw_conf)
        stable_pred, stable_conf = disease_smoother.get_smoothed_prediction()

        return FramePredictionResponse(
            stream="disease_live",
            prediction=stable_pred,
            confidence=stable_conf,
            raw_prediction=raw_pred,
            raw_confidence=raw_conf,
            quality_report=raw_res["image_quality"],
            timestamp=time.time()
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Live frame processing error: {str(e)}")


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
            # Receive base64 encoded frame or bytes from client
            data = await websocket.receive_bytes()
            now = time.time()

            # Frame sampling rate limit
            if (now - last_eval_time) < min_frame_interval:
                continue
            last_eval_time = now

            try:
                raw_res = registry.predict_disease(data)
                raw_pred = raw_res["predicted_disease"]
                raw_conf = raw_res["confidence"]

                local_smoother.add_prediction(raw_pred, raw_conf)
                stable_pred, stable_conf = local_smoother.get_smoothed_prediction()

                await websocket.send_json({
                    "success": True,
                    "prediction": stable_pred,
                    "confidence": stable_conf,
                    "raw_prediction": raw_pred,
                    "raw_confidence": raw_conf,
                    "is_valid_frame": raw_res["image_quality"]["is_valid"],
                    "warnings": raw_res["image_quality"]["warnings"],
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
    description="Evaluates single frame from live video feed using MobileNetV3 Small insect classification model and temporal smoothing."
)
async def process_pest_live_frame(file: UploadFile = File(...)):
    """Process a single live video frame for visual pest recognition."""
    contents = await file.read()
    registry = ModelRegistry()

    try:
        raw_res = registry.predict_pest_visual(contents)
        raw_pred = raw_res["predicted_pest"]
        raw_conf = raw_res["confidence"]

        pest_smoother.add_prediction(raw_pred, raw_conf)
        stable_pred, stable_conf = pest_smoother.get_smoothed_prediction()

        return FramePredictionResponse(
            stream="pest_live",
            prediction=stable_pred,
            confidence=stable_conf,
            raw_prediction=raw_pred,
            raw_confidence=raw_conf,
            quality_report=raw_res["image_quality"],
            timestamp=time.time()
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Live pest frame processing error: {str(e)}")


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
                raw_res = registry.predict_pest_visual(data)
                raw_pred = raw_res["predicted_pest"]
                raw_conf = raw_res["confidence"]

                local_smoother.add_prediction(raw_pred, raw_conf)
                stable_pred, stable_conf = local_smoother.get_smoothed_prediction()

                await websocket.send_json({
                    "success": True,
                    "prediction": stable_pred,
                    "confidence": stable_conf,
                    "raw_prediction": raw_pred,
                    "raw_confidence": raw_conf,
                    "is_valid_frame": raw_res["image_quality"]["is_valid"],
                    "warnings": raw_res["image_quality"]["warnings"],
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
