"""
Pydantic schemas for Crop Yield Prediction API.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .soil import PredictionInterval


class YieldPredictRequest(BaseModel):
    Crop: str = Field(..., description="Crop name (e.g. Rice, Wheat, Maize)", example="Rice")
    Season: str = Field(..., description="Cropping Season (e.g. Kharif, Rabi, Whole Year)", example="Kharif")
    State: str = Field(..., description="Indian State Name (e.g. Punjab, Uttar Pradesh)", example="Punjab")
    Area: float = Field(..., ge=0.01, description="Cultivated Area in Hectares", example=100.0)
    Annual_Rainfall: float = Field(..., ge=0.0, le=10000.0, description="Annual Rainfall in mm", example=1200.0)
    Fertilizer: float = Field(..., ge=0.0, description="Total Fertilizer applied in kg", example=15000.0)
    Pesticide: float = Field(..., ge=0.0, description="Total Pesticide applied in kg", example=500.0)
    Fertilizer_Per_Area: float = Field(..., ge=0.0, description="Fertilizer application density (kg/ha)", example=150.0)
    Pesticide_Per_Area: float = Field(..., ge=0.0, description="Pesticide application density (kg/ha)", example=5.0)


class YieldPredictResponse(BaseModel):
    success: bool = True
    model: str = "yield_prediction"
    predicted_yield: float = Field(..., description="Predicted crop yield")
    prediction_interval: PredictionInterval
    scope_warning: str = (
        "Dataset contains heterogeneous crop yield metric conventions across regions/crops. "
        "Predictions represent statistical expectation based on Indian Agricultural Crop Yield benchmarks."
    )
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
