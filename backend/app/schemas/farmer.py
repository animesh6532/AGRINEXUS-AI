"""
Pydantic schemas for Farmer Profile, Farm, Field, Crop Cultivation, and Farm Command Center.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field as PydanticField, ConfigDict


class SoilValueWithProvenance(BaseModel):
    value: Optional[Any] = None
    provenance: str = "UNKNOWN"  # "MEASURED", "ESTIMATED", "UNKNOWN"


class SoilDataInput(BaseModel):
    ph: Optional[float] = None
    ph_provenance: str = "UNKNOWN"
    nitrogen: Optional[float] = None
    nitrogen_provenance: str = "UNKNOWN"
    phosphorus: Optional[float] = None
    phosphorus_provenance: str = "UNKNOWN"
    potassium: Optional[float] = None
    potassium_provenance: str = "UNKNOWN"
    organic_carbon: Optional[float] = None
    organic_carbon_provenance: str = "UNKNOWN"
    ec: Optional[float] = None
    ec_provenance: str = "UNKNOWN"
    texture: Optional[str] = None
    texture_provenance: str = "UNKNOWN"
    moisture: Optional[float] = None
    moisture_provenance: str = "UNKNOWN"


# --- CROP PLANTING ---

class CropPlantingBase(BaseModel):
    crop_name: str
    crop_id: Optional[str] = None
    scientific_name: Optional[str] = None
    variety: Optional[str] = None
    category: Optional[str] = None
    sowing_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    growth_stage: Optional[str] = None
    growth_stage_source: str = "farmer"  # "farmer" or "calculated"
    cultivation_type: Optional[str] = None
    irrigation_method: Optional[str] = None
    water_availability: Optional[str] = None
    status: str = "ACTIVE"  # PLANNED, ACTIVE, HARVESTED, COMPLETED
    notes: Optional[str] = None


class CropPlantingCreate(CropPlantingBase):
    field_id: int


class CropPlantingUpdate(BaseModel):
    crop_name: Optional[str] = None
    crop_id: Optional[str] = None
    scientific_name: Optional[str] = None
    variety: Optional[str] = None
    category: Optional[str] = None
    sowing_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    growth_stage: Optional[str] = None
    growth_stage_source: Optional[str] = None
    cultivation_type: Optional[str] = None
    irrigation_method: Optional[str] = None
    water_availability: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class CropPlantingResponse(CropPlantingBase):
    id: int
    field_id: int
    created_at: str
    updated_at: str
    model_config = ConfigDict(from_attributes=True)


# --- FIELD ---

class FieldBase(BaseModel):
    field_name: str
    area_value: float
    area_unit: str = "acre"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    soil_type: Optional[str] = None
    soil_test_available: bool = False
    notes: Optional[str] = None

    # Soil Data & Provenance
    ph: Optional[float] = None
    ph_provenance: str = "UNKNOWN"
    nitrogen: Optional[float] = None
    nitrogen_provenance: str = "UNKNOWN"
    phosphorus: Optional[float] = None
    phosphorus_provenance: str = "UNKNOWN"
    potassium: Optional[float] = None
    potassium_provenance: str = "UNKNOWN"
    organic_carbon: Optional[float] = None
    organic_carbon_provenance: str = "UNKNOWN"
    ec: Optional[float] = None
    ec_provenance: str = "UNKNOWN"
    texture: Optional[str] = None
    texture_provenance: str = "UNKNOWN"
    moisture: Optional[float] = None
    moisture_provenance: str = "UNKNOWN"


class FieldCreate(FieldBase):
    farm_id: int


class FieldUpdate(BaseModel):
    field_name: Optional[str] = None
    area_value: Optional[float] = None
    area_unit: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    soil_type: Optional[str] = None
    soil_test_available: Optional[bool] = None
    notes: Optional[str] = None

    ph: Optional[float] = None
    ph_provenance: Optional[str] = None
    nitrogen: Optional[float] = None
    nitrogen_provenance: Optional[str] = None
    phosphorus: Optional[float] = None
    phosphorus_provenance: Optional[str] = None
    potassium: Optional[float] = None
    potassium_provenance: Optional[str] = None
    organic_carbon: Optional[float] = None
    organic_carbon_provenance: Optional[str] = None
    ec: Optional[float] = None
    ec_provenance: Optional[str] = None
    texture: Optional[str] = None
    texture_provenance: Optional[str] = None
    moisture: Optional[float] = None
    moisture_provenance: Optional[str] = None


class FieldResponse(BaseModel):
    id: int
    farm_id: int
    field_name: str
    area_value: float
    area_unit: str
    total_area_m2: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    soil_type: Optional[str] = None
    soil_test_available: bool
    soil_data: Dict[str, SoilValueWithProvenance]
    notes: Optional[str] = None
    plantings: List[CropPlantingResponse] = []
    created_at: str
    updated_at: str


# --- FARM ---

class FarmBase(BaseModel):
    farm_name: str
    location_name: Optional[str] = None
    latitude: float
    longitude: float
    area_value: float
    area_unit: str = "acre"
    soil_type_manual: Optional[str] = None
    water_source: Optional[str] = None
    irrigation_method: Optional[str] = None
    ownership_type: Optional[str] = None
    notes: Optional[str] = None


class FarmCreate(FarmBase):
    pass


class FarmUpdate(BaseModel):
    farm_name: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_value: Optional[float] = None
    area_unit: Optional[str] = None
    soil_type_manual: Optional[str] = None
    water_source: Optional[str] = None
    irrigation_method: Optional[str] = None
    ownership_type: Optional[str] = None
    notes: Optional[str] = None


class FarmResponse(FarmBase):
    id: int
    farmer_id: int
    total_area_m2: float
    fields: List[FieldResponse] = []
    created_at: str
    updated_at: str


# --- FARMER PROFILE ---

class FarmerProfileBase(BaseModel):
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    preferred_language: str = "en"


class FarmerProfileCreate(FarmerProfileBase):
    user_id: Optional[str] = "default_farmer"


class FarmerProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    preferred_language: Optional[str] = None


class FarmerProfileResponse(FarmerProfileBase):
    id: int
    user_id: str
    farms: List[FarmResponse] = []
    created_at: str
    updated_at: str


# --- COMMAND CENTER & AGGREGATED DASHBOARD ---

class WeatherImpactItem(BaseModel):
    crop_name: str
    field_name: str
    temperature: Optional[float] = None
    rain_forecast_mm: Optional[float] = None
    impact: str
    action: str
    status: str  # "Favorable", "Monitor", "Warning"


class SoilImpactItem(BaseModel):
    crop_name: str
    field_name: str
    ph_status: str
    texture_status: str
    n_status: str
    p_status: str
    k_status: str
    impact_text: str


class IrrigationContextItem(BaseModel):
    crop_name: str
    field_name: str
    current_moisture: Optional[float] = None
    expected_moisture: Optional[float] = None
    rainfall_forecast_mm: Optional[float] = None
    irrigation_method: Optional[str] = None
    water_availability: Optional[str] = None
    status: str  # "LOW", "NORMAL", "HIGH", "MONITOR"
    next_window: Optional[str] = None
    model_note: str  # Label e.g., "Planning estimate" or "Gallipoli ML dataset baseline"


class FertilizerContextItem(BaseModel):
    crop_name: str
    field_name: str
    n_status: str
    p_status: str
    k_status: str
    model_available: bool
    model_scope_note: str  # e.g., "Western Maharashtra regional model scope limitation"
    recommendation: Optional[str] = None
    reason: str


class PestRiskItem(BaseModel):
    crop_name: str
    field_name: str
    risk_level: str  # "Low", "Moderate", "High"
    weather_drivers: List[str] = []
    crop_stage: Optional[str] = None
    action: str
    model_scope_note: str = "Environmental weather risk indicator"


class MarketWatchItem(BaseModel):
    crop_name: str
    commodity: str
    current_price: Optional[float] = None
    trend: str  # "Increasing", "Decreasing", "Stable", "Unknown"
    change_30d_pct: Optional[float] = None
    period: str = "Last 30 days"
    market_location: Optional[str] = None


class CropTimelineItem(BaseModel):
    date_label: str
    crop_name: str
    field_name: str
    event_title: str
    reason: str
    priority: str  # "Critical", "High", "Moderate", "Info"
    source: str
    evidence_status: str


class FarmAlertItem(BaseModel):
    id: str
    priority: str  # "Critical", "High", "Moderate", "Info"
    category: str  # "Weather", "Irrigation", "Pest", "Soil", "Market", "Crop"
    title: str
    description: str
    crop_name: Optional[str] = None
    field_name: Optional[str] = None
    timestamp: str
    actionable: bool = True


class ImpactMatrixRow(BaseModel):
    crop_name: str
    field_name: str
    area_display: str
    weather: str
    soil: str
    water: str
    pest: str
    market: str
    attention_level: str  # "High", "Medium", "Low"


class DataQualitySummary(BaseModel):
    location_confidence: str
    weather_freshness: str
    soil_availability: str
    npk_availability: str
    market_status: str
    profile_completeness_pct: float
    missing_fields: List[str] = []


class TodayFarmStatus(BaseModel):
    weather_summary: str
    soil_summary: str
    water_summary: str
    market_summary: str
    action_items_count: int


class FarmDashboardResponse(BaseModel):
    farmer: FarmerProfileResponse
    location: Dict[str, Any]
    total_farm_area: float
    total_farm_area_unit: str
    active_crops_count: int
    fields_count: int
    today_status: TodayFarmStatus
    active_crop_cards: List[Dict[str, Any]]
    weather_impacts: List[WeatherImpactItem]
    soil_impacts: List[SoilImpactItem]
    irrigation_items: List[IrrigationContextItem]
    fertilizer_items: List[FertilizerContextItem]
    pest_items: List[PestRiskItem]
    market_watch: List[MarketWatchItem]
    crop_calendar_events: List[Dict[str, Any]]
    alerts: List[FarmAlertItem]
    timeline: List[CropTimelineItem]
    impact_matrix: List[ImpactMatrixRow]
    data_quality: DataQualitySummary
    last_updated: str
