"""
Pydantic schemas for Soil Organic Carbon Analysis API.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class SoilAnalyzeRequest(BaseModel):
    pH_CaCl2: float = Field(..., alias="pH(CaCl2)", ge=0.0, le=14.0, description="pH measured in CaCl2", example=6.2)
    pH_H2O: float = Field(..., alias="pH(H2O)", ge=0.0, le=14.0, description="pH measured in H2O", example=6.8)
    Clay: float = Field(..., ge=0.0, le=100.0, description="Clay content percentage", example=25.0)
    Silt: float = Field(..., ge=0.0, le=100.0, description="Silt content percentage", example=40.0)
    Sand: float = Field(..., ge=0.0, le=100.0, description="Sand content percentage", example=35.0)
    CaCO3: float = Field(..., ge=0.0, le=1000.0, description="Calcium Carbonate content (g/kg)", example=12.0)
    P: float = Field(..., ge=0.0, le=1000.0, description="Phosphorus content (mg/kg)", example=18.5)
    N: float = Field(..., ge=0.0, le=100.0, description="Total Nitrogen (g/kg)", example=2.1)
    K: float = Field(..., ge=0.0, le=5000.0, description="Extractable Potassium (mg/kg)", example=180.0)
    EC: float = Field(..., ge=0.0, le=100.0, description="Electrical Conductivity (mS/m)", example=15.0)
    NUTS_0: str = Field(..., description="NUTS-0 Country Code (e.g. DE, FR, IT)", example="DE")
    LC1: str = Field(..., description="Land Cover class code (e.g. B11, B12, C10)", example="B11")

    model_config = {
        "populate_by_name": True
    }


class PredictionInterval(BaseModel):
    lower: float = Field(..., description="Lower 95% empirical residual interval bound")
    upper: float = Field(..., description="Upper 95% empirical residual interval bound")
    margin: float = Field(..., description="Empirical 95th percentile residual margin")


class SoilAnalyzeResponse(BaseModel):
    success: bool = True
    model: str = "soil_organic_carbon_analysis"
    predicted_soc: float = Field(..., description="Predicted Soil Organic Carbon (OC)")
    unit: str = "g/kg"
    prediction_interval: PredictionInterval
    geographic_scope: str = "LUCAS European Union Topsoil Survey Domain"
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
