"""
Pydantic schemas for Fertilizer Recommendation API.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class FertilizerRecommendRequest(BaseModel):
    Nitrogen: float = Field(..., ge=0.0, le=500.0, description="Nitrogen level (kg/ha)", example=37.0)
    Phosphorus: float = Field(..., ge=0.0, le=500.0, description="Phosphorus level (kg/ha)", example=20.0)
    Potassium: float = Field(..., ge=0.0, le=500.0, description="Potassium level (kg/ha)", example=20.0)
    pH: float = Field(..., ge=0.0, le=14.0, description="Soil pH level", example=6.5)
    Rainfall: float = Field(..., ge=0.0, le=5000.0, description="Rainfall in mm", example=120.0)
    Temperature: float = Field(..., ge=-10.0, le=60.0, description="Temperature in Celsius", example=26.0)
    District_Name: str = Field(..., min_length=1, description="District Name (e.g., Pune, Kolhapur)", example="Pune")
    Soil_color: str = Field(..., min_length=1, description="Soil color (e.g., Black, Red)", example="Black")
    Crop: str = Field(..., min_length=1, description="Target crop", example="Rice")
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
        "ML recommendation trained on Western Maharashtra soil/crop data."
    )
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FertilizerImageRequest(BaseModel):
    fertilizer_name: str = Field(..., description="Name of fertilizer formulation")


class FertilizerImageResponse(BaseModel):
    image_url: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    photographer: Optional[str] = None
    photographer_url: Optional[str] = None
    image_type: Optional[str] = None  # "representative", "product", "fallback"
    verified_product: bool = False
    match_score: Optional[float] = 0.0



class NearbyShopsRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    radius_km: Optional[float] = Field(25.0, ge=1.0, le=100.0)
    sort_by: Optional[str] = Field("nearest", description="nearest, highest_rated, open_now")


class NearbyShopsLocation(BaseModel):
    latitude: float
    longitude: float


class ShopProviderItem(BaseModel):
    place_id: str
    name: str
    category: str
    address: str
    latitude: float
    longitude: float
    distance_km: float
    rating: Optional[float] = None
    review_count: Optional[int] = None
    open_now: Optional[bool] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    google_maps_uri: Optional[str] = None
    types: List[str] = Field(default_factory=list)


class ShopItem(BaseModel):
    shop_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    distance: float
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: float = 4.5
    review_count: int = 0
    opening_status: str = "OPEN NOW"
    categories: List[str] = Field(default_factory=list)
    google_maps_uri: Optional[str] = None


class NearbyShopsResponse(BaseModel):
    success: bool = True
    location: Optional[NearbyShopsLocation] = None
    search_radius_km: float = 25.0
    count: int = 0
    providers: List[ShopProviderItem] = Field(default_factory=list)
    shops: List[ShopItem] = Field(default_factory=list)
    total_found: int = 0
    radius_km: float = 25.0
    radius_km_searched: float = 5.0
    message: Optional[str] = None
    error_diagnostic: Optional[str] = None


class SoilContextRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class SoilContextData(BaseModel):
    ph: Optional[float] = None
    total_nitrogen_g_kg: Optional[float] = None
    organic_carbon_g_kg: Optional[float] = None
    clay_percent: Optional[float] = None
    sand_percent: Optional[float] = None
    silt_percent: Optional[float] = None
    soil_texture: str = "Unknown"
    depth_layer: str = "0-30 cm"
    provenance: str = "GEOSPATIAL_ESTIMATE"
    disclaimer: str = "Estimated from geographic soil data. This is NOT a laboratory soil test result."


class SoilContextResponse(BaseModel):
    success: bool = True
    status: str = "available"  # "available" | "unavailable"
    source: str = "SoilGrids ISRIC REST API"
    data: Optional[SoilContextData] = None
    error_message: Optional[str] = None


class OCRSoilReportResponse(BaseModel):
    success: bool = True
    scanner_type: str = "soil_test"
    status: str
    quality: Dict[str, Any] = Field(default_factory=dict)
    extracted_values: Dict[str, float] = Field(default_factory=dict)
    confidence: float = 0.0
    requires_verification: bool = True
    raw_text_snippet: Optional[str] = None


class SoilVisualScanResponse(BaseModel):
    success: bool = True
    observation_type: str = "Visual observation"
    quality_report: Dict[str, Any] = Field(default_factory=dict)
    visual_color: str
    visual_texture: str
    brightness_level: float
    notice: str = "Nutrient levels cannot be reliably determined from this photograph."
    recommendation: str = "Use laboratory soil-test results for precise N, P, K values."



