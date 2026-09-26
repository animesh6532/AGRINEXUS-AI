"""
Pydantic schemas for Irrigation Prediction & Irrigation Intelligence System.
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


# --- Original ML Inference Schemas ---

class IrrigationPredictRequest(BaseModel):
    SWC: float = Field(..., ge=0.0, le=1.0, description="Current Soil Water Content (m3/m3)")
    SWC_lag1h: float = Field(..., ge=0.0, le=1.0, description="SWC 1 hour ago")
    SWC_lag2h: float = Field(..., ge=0.0, le=1.0, description="SWC 2 hours ago")
    SWC_lag3h: float = Field(..., ge=0.0, le=1.0, description="SWC 3 hours ago")
    SWC_roll6h_mean: float = Field(..., ge=0.0, le=1.0, description="6-hour rolling mean of SWC")
    Rainfall_mm: float = Field(..., ge=0.0, le=500.0, description="Current hour rainfall in mm")
    Rain_roll6h_sum: float = Field(..., ge=0.0, le=1000.0, description="6-hour rolling sum of rainfall")


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


# --- Irrigation Logging Schemas ---

class IrrigationLogCreate(BaseModel):
    field_id: int
    water_amount_mm: float = Field(..., gt=0, description="Water applied in mm")
    method: Optional[str] = "Drip"
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    logged_at: Optional[datetime] = None


class IrrigationLogResponse(BaseModel):
    id: int
    field_id: int
    farmer_id: int
    water_amount_mm: float
    water_amount_liters: Optional[float] = None
    method: Optional[str] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    logged_at: str
    created_at: str
    model_config = ConfigDict(from_attributes=True)


# --- What-If Simulator Schemas ---

class WhatIfSimulationRequest(BaseModel):
    field_id: int
    custom_irrigation_mm: Optional[float] = 0.0
    delay_hours: Optional[int] = 0
    simulated_rain_mm: Optional[float] = 0.0


class WhatIfScenarioResult(BaseModel):
    scenario_id: str
    scenario_name: str
    description: str
    water_applied_mm: float
    projected_swc_48h: float
    deficit_mm: float
    risk_level: str  # "Low", "Moderate", "High", "Optimal"
    recommendation: str


class WhatIfSimulationResponse(BaseModel):
    field_id: int
    base_swc: float
    scenarios: List[WhatIfScenarioResult]


# --- Comprehensive Irrigation Intelligence Schemas ---

class FieldIrrigationContext(BaseModel):
    field_id: int
    field_name: str
    farm_name: str
    crop_name: str
    variety: Optional[str] = None
    growth_stage: str
    area_value: float
    area_unit: str
    total_area_m2: float
    water_source: str
    irrigation_method: str
    soil_type: str


class WaterStatusInfo(BaseModel):
    current_swc: float
    field_capacity: float
    wilting_point: float
    critical_threshold: float
    status_code: str  # "TOO_DRY", "CRITICAL", "OPTIMAL", "NEAR_CAPACITY", "SATURATED"
    status_title: str
    status_description: str
    water_zone: str  # "Below Target", "Target Range", "Full Reserve"


class IrrigationDecisionInfo(BaseModel):
    state: str  # "IRRIGATE_NOW", "IRRIGATE_SOON", "WAIT_FOR_RAIN", "MONITOR", "NO_IRRIGATION_REQUIRED", "INSUFFICIENT_DATA"
    state_title: str
    window: str  # e.g., "Today 4:00 PM – 7:00 PM" or "Within next 12 hours"
    net_depth_mm: Optional[float] = None
    gross_depth_mm: Optional[float] = None
    water_volume_liters: Optional[float] = None
    efficiency_pct: Optional[float] = None
    efficiency_note: Optional[str] = None
    reason: str
    actionable: bool = True


class ET0Info(BaseModel):
    et0_today_mm: float
    et0_tomorrow_mm: float
    et0_3day_mm: float
    etc_today_mm: Optional[float] = None
    kc_value: Optional[float] = None
    kc_source: str
    kc_note: str


class TrajectoryPoint(BaseModel):
    label: str  # e.g. "-24h", "Current", "+6h", "+12h", "+24h", "+48h", "+72h"
    timestamp: str
    swc_projected: float
    rainfall_mm: float
    etc_mm: float
    threshold: float
    status: str


class DailyPlanItem(BaseModel):
    day: str  # "Mon", "Tue", etc.
    date_str: str
    status: str  # "Irrigate", "Wait for Rain", "Monitor", "No Irrigation"
    rain_expected_mm: float
    etc_mm: float
    action: str


class WaterBudgetInfo(BaseModel):
    period: str = "This Week"
    rainfall_received_mm: float
    irrigation_applied_mm: float
    crop_consumed_mm: float
    estimated_deficit_mm: float
    season_total_liters: float


class MLForecastSignal(BaseModel):
    ml_predicted_swc_3h: float
    persistence_swc_3h: float
    target_unit: str = "m3/m3"
    horizon_hours: int = 3
    baseline_note: str


class WaterSavingOpportunity(BaseModel):
    type: str  # "RAIN_DEFERRAL", "TIMING_OPTIMIZATION", "EFFICIENCY_GAIN"
    title: str
    description: str
    potential_water_saved_liters: Optional[float] = None


class IrrigationIntelligenceResponse(BaseModel):
    field_context: FieldIrrigationContext
    water_status: WaterStatusInfo
    decision: IrrigationDecisionInfo
    et0: ET0Info
    water_balance_trajectory: List[TrajectoryPoint]
    seven_day_plan: List[DailyPlanItem]
    water_budget: WaterBudgetInfo
    ml_forecast: MLForecastSignal
    evidence_items: List[str]
    evidence_quality: str  # "HIGH", "MEDIUM", "LIMITED"
    water_saving_opportunities: List[WaterSavingOpportunity]
    what_if_scenarios: List[WhatIfScenarioResult]
    irrigation_history: List[IrrigationLogResponse]
    generated_at: str
