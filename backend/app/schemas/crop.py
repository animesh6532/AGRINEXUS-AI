"""
Pydantic schemas for Crop Recommendation API.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class CropRecommendationRequest(BaseModel):
    N: float = Field(..., ge=0, le=200, description="Nitrogen content in soil (mg/kg or ratio)", example=90.0)
    P: float = Field(..., ge=0, le=200, description="Phosphorus content in soil (mg/kg or ratio)", example=42.0)
    K: float = Field(..., ge=0, le=200, description="Potassium content in soil (mg/kg or ratio)", example=43.0)
    temperature: float = Field(..., ge=-10.0, le=60.0, description="Temperature in Celsius", example=20.87)
    humidity: float = Field(..., ge=0.0, le=100.0, description="Relative humidity percentage", example=82.0)
    ph: float = Field(..., ge=0.0, le=14.0, description="Soil pH level (0-14)", example=6.5)
    rainfall: float = Field(..., ge=0.0, le=3000.0, description="Rainfall in mm", example=202.9)


class PredictionProbability(BaseModel):
    crop: str
    probability: float


class CropRecommendationResponse(BaseModel):
    success: bool = True
    model: str = "crop_recommendation"
    prediction: str = Field(..., description="Recommended crop class")
    confidence: Optional[float] = Field(None, description="Model probability for top class")
    top_k_predictions: List[PredictionProbability] = Field(default_factory=list)
    is_plausible: bool = Field(True, description="IsolationForest input plausibility status")
    anomaly_status: str = Field("Plausible input", description="Description of input plausibility")
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
