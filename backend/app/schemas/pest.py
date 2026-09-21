"""
Pydantic schemas for Pest Prediction API (Visual Classification & Environmental Risk).
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .disease import ImageQualityReport


class PestProbability(BaseModel):
    pest_class: str
    probability: float


class VisualPestPredictResponse(BaseModel):
    success: bool = True
    model: str = "visual_pest_classification"
    predicted_pest: str = Field(..., description="Predicted pest category from IP102 benchmark")
    confidence: float = Field(..., description="Classification probability for top class")
    top_k_predictions: List[PestProbability] = Field(default_factory=list)
    image_quality: ImageQualityReport
    disclaimer: str = (
        "MobileNetV3 Small visual classification model (102 classes, IP102 dataset). "
        "This model performs single-insect image classification, NOT object detection or bounding-box extraction."
    )
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PestRiskRequest(BaseModel):
    Temperature: float = Field(..., ge=-10.0, le=60.0, description="Temperature in Celsius", example=28.5)
    Humidity: float = Field(..., ge=0.0, le=100.0, description="Relative Humidity percentage", example=75.0)
    Rainfall: float = Field(..., ge=0.0, le=3000.0, description="Rainfall in mm", example=120.0)
    Crop_Type: str = Field(..., description="Crop Type (e.g. Rice, Wheat, Cotton)", example="Rice")
    Soil_Type: str = Field(..., description="Soil Type (e.g. Clay, Loam, Alluvial)", example="Clay")
    Region: str = Field(..., description="Geographic Region", example="South")


class PestRiskResponse(BaseModel):
    success: bool = True
    model: str = "environmental_pest_risk"
    pest_severity_risk: str = Field(..., description="Predicted pest severity level: Low, Medium, or High")
    confidence: Optional[float] = Field(None, description="Risk prediction confidence probability")
    top_k_predictions: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
