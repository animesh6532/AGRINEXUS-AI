"""
Pydantic schemas for Plant Disease Detection API.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class DiseasePredictionProbability(BaseModel):
    disease: str
    probability: float


class ImageQualityReport(BaseModel):
    is_valid: bool
    blur_score: float
    is_blurry: bool
    brightness_score: float
    is_exposure_ok: bool
    resolution: List[int]
    warnings: List[str] = Field(default_factory=list)


class DiseasePredictResponse(BaseModel):
    success: bool = True
    model: str = "disease_detection"
    predicted_disease: str = Field(..., description="Predicted plant disease or healthy status")
    confidence: float = Field(..., description="Top prediction confidence probability")
    top_k_predictions: List[DiseasePredictionProbability] = Field(default_factory=list)
    image_quality: ImageQualityReport
    gradcam_available: bool = Field(False, description="Whether Grad-CAM explainability was generated")
    gradcam_heatmap: Optional[str] = Field(None, description="Base64 encoded Grad-CAM PNG visualization")
    model_status: str = "READY"
    safety_disclaimer: str = (
        "AI-assisted decision support tool based on PlantVillage dataset. "
        "Not a 100% field-grade clinical diagnosis. Verify with an agricultural expert."
    )
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
