"""
Pydantic schemas for Irrigation Prediction API.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class IrrigationPredictRequest(BaseModel):
    SWC: float = Field(..., ge=0.0, le=1.0, description="Current Soil Water Content (m3/m3)", example=0.22)
    SWC_lag1h: float = Field(..., ge=0.0, le=1.0, description="SWC 1 hour ago", example=0.225)
    SWC_lag2h: float = Field(..., ge=0.0, le=1.0, description="SWC 2 hours ago", example=0.23)
    SWC_lag3h: float = Field(..., ge=0.0, le=1.0, description="SWC 3 hours ago", example=0.235)
    SWC_roll6h_mean: float = Field(..., ge=0.0, le=1.0, description="6-hour rolling mean of SWC", example=0.23)
    Rainfall_mm: float = Field(..., ge=0.0, le=500.0, description="Current hour rainfall in mm", example=0.0)
    Rain_roll6h_sum: float = Field(..., ge=0.0, le=1000.0, description="6-hour rolling sum of rainfall", example=0.0)


class AgronomicStatus(BaseModel):
    field_capacity: float = 0.32
    wilting_point: float = 0.14
    critical_threshold: float = 0.23
    irrigation_needed: bool
    status_message: str


class IrrigationPredictResponse(BaseModel):
    success: bool = True
    model: str = "irrigation_prediction"
    ml_predicted_swc_3h: float = Field(..., description="ML model prediction for 3-hour ahead SWC (m3/m3)")
    persistence_swc_3h: float = Field(..., description="Persistence baseline prediction (SWC_t+3h = SWC_t)")
    target_unit: str = "m3/m3"
    horizon_hours: int = 3
    agronomic_status: AgronomicStatus
    benchmark_note: str = (
        "IMPORTANT: Persistence baseline (SWC_t+3h = SWC_t) performed better than ML models "
        "on the held-out test evaluation. Both outputs are provided for full transparency."
    )
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
