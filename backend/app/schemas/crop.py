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


# --- SMART CROP ADVISOR SCHEMAS ---

class LocationInput(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate", json_schema_extra={"example": 22.72})
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate", json_schema_extra={"example": 88.48})
    displayName: Optional[str] = Field(None, description="Location display name")
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    source: Optional[str] = Field("MAP_SELECTION", description="GPS, MAP_SELECTION, SEARCH, SAVED_LOCATION, MANUAL")


class SoilInput(BaseModel):
    nitrogen: Optional[float] = Field(None, ge=0.0, le=300.0, description="Measured Soil N (mg/kg)")
    phosphorus: Optional[float] = Field(None, ge=0.0, le=300.0, description="Measured Soil P (mg/kg)")
    potassium: Optional[float] = Field(None, ge=0.0, le=300.0, description="Measured Soil K (mg/kg)")
    ph: Optional[float] = Field(None, ge=0.0, le=14.0, description="Measured Soil pH")


class WeatherOverrideInput(BaseModel):
    temperature: Optional[float] = Field(None, description="Temperature override °C")
    humidity: Optional[float] = Field(None, description="Relative humidity override %")
    rainfall: Optional[float] = Field(None, description="Rainfall override mm")


class FarmInput(BaseModel):
    area_acres: Optional[float] = Field(None, ge=0.0, le=10000.0, description="Farm size in acres")
    water_availability: Optional[str] = Field("unknown", description="Rainfed, Limited Irrigation, Irrigated, unknown")


class PreferencesInput(BaseModel):
    category: Optional[str] = Field("all", description="Crop category filter")


class SmartCropRequest(BaseModel):
    mode: str = Field("auto", description="auto, hybrid, manual")
    location: LocationInput
    soil: Optional[SoilInput] = Field(default_factory=SoilInput)
    weather_override: Optional[WeatherOverrideInput] = None
    farm: Optional[FarmInput] = Field(default_factory=FarmInput)
    preferences: Optional[PreferencesInput] = Field(default_factory=PreferencesInput)


class SmartCropResponse(BaseModel):
    success: bool = True
    engine_version: str = "1.0.0"
    mode: str
    data_completeness: float = Field(..., description="Completeness score (0.0 to 1.0)")
    location: Dict[str, Any]
    season: Dict[str, Any]
    weather: Dict[str, Any]
    soil: Dict[str, Any]
    ml_status: Dict[str, Any]
    farm: Dict[str, Any]
    recommendations: List[Dict[str, Any]]

