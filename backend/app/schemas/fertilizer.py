"""
Pydantic schemas for Fertilizer Recommendation API.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class FertilizerRecommendRequest(BaseModel):
    Nitrogen: float = Field(..., ge=0, le=300, description="Nitrogen level", example=20.0)
    Phosphorus: float = Field(..., ge=0, le=300, description="Phosphorus level", example=20.0)
    Potassium: float = Field(..., ge=0, le=300, description="Potassium level", example=20.0)
    pH: float = Field(..., ge=0.0, le=14.0, description="Soil pH level", example=6.5)
    Rainfall: float = Field(..., ge=0.0, le=3000.0, description="Rainfall in mm", example=800.0)
    Temperature: float = Field(..., ge=-10.0, le=60.0, description="Temperature in Celsius", example=26.0)
    District_Name: str = Field(..., description="District Name (e.g., Pune, Nashik)", example="Pune")
    Soil_color: str = Field(..., description="Soil color (e.g., Black, Red)", example="Black")
    Crop: str = Field(..., description="Target crop", example="Sugarcane")
    Link: Optional[str] = Field("https://example.com", description="Information link reference")


class FertilizerProbability(BaseModel):
    formulation: str
    probability: float


class FertilizerRecommendResponse(BaseModel):
    success: bool = True
    model: str = "fertilizer_recommendation"
    predicted_formulation: str = Field(..., description="Recommended commercial fertilizer formulation")
    confidence: Optional[float] = Field(None, description="Prediction probability")
    top_k_predictions: List[FertilizerProbability] = Field(default_factory=list)
    scope_warning: str = (
        "Model trained primarily on Western Maharashtra agricultural data. "
        "Represents product formulation classification, not custom NPK optimization."
    )
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
