/**
 * TypeScript interface definitions matching the exact FastAPI backend Pydantic schemas.
 */

// ------------------------------------------------------------------
// 1. CROP RECOMMENDATION
// ------------------------------------------------------------------
export interface CropRecommendationRequest {
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
}

export interface CropProbability {
  crop: string;
  probability: number;
}

export interface CropRecommendationResponse {
  success: boolean;
  model: string;
  prediction: string;
  confidence: number;
  top_k_predictions: CropProbability[];
  is_plausible: boolean;
  anomaly_status: string;
  warnings: string[];
}

// ------------------------------------------------------------------
// 2. PLANT DISEASE DETECTION
// ------------------------------------------------------------------
export interface ImageQualityReport {
  is_valid: boolean;
  blur_score: number;
  is_blurry: boolean;
  brightness_score: number;
  is_exposure_ok: boolean;
  resolution: [number, number];
  warnings: string[];
}

export interface DiseaseProbability {
  disease: string;
  probability: number;
}

export interface DiseasePredictResponse {
  success: boolean;
  model: string;
  predicted_disease: string;
  confidence: number;
  top_k_predictions: DiseaseProbability[];
  image_quality: ImageQualityReport;
  gradcam_available: boolean;
  gradcam_heatmap: string | null;
  warnings: string[];
  metadata: Record<string, any>;
}

// ------------------------------------------------------------------
// 3. FERTILIZER RECOMMENDATION
// ------------------------------------------------------------------
export interface FertilizerRecommendRequest {
  Nitrogen: number;
  Phosphorus: number;
  Potassium: number;
  pH: number;
  Rainfall: number;
  Temperature: number;
  District_Name: string;
  Soil_color: string;
  Crop: string;
  Link?: string;
}

export interface FertilizerProbability {
  formulation: string;
  probability: number;
}

export interface FertilizerRecommendResponse {
  success: boolean;
  model: string;
  predicted_formulation: string;
  confidence: number | null;
  top_k_predictions: FertilizerProbability[];
  scope_warning: string;
  warnings: string[];
  metadata: Record<string, any>;
}

// ------------------------------------------------------------------
// 4. IRRIGATION PREDICTION
// ------------------------------------------------------------------
export interface IrrigationPredictionRequest {
  SWC: number;
  SWC_lag1h: number;
  SWC_lag2h: number;
  SWC_lag3h: number;
  SWC_roll6h_mean: number;
  Rainfall_mm: number;
  Rain_roll6h_sum: number;
}

export interface AgronomicStatus {
  field_capacity: number;
  wilting_point: number;
  critical_threshold: number;
  irrigation_needed: boolean;
  status_message: string;
  decision_note: string;
}

export interface IrrigationPredictionResponse {
  success: boolean;
  model: string;
  ml_predicted_swc_3h: number;
  persistence_swc_3h: number;
  agronomic_status: AgronomicStatus;
  warnings: string[];
  metadata: Record<string, any>;
}

// ------------------------------------------------------------------
// 5. PEST PREDICTION (Visual & Environmental)
// ------------------------------------------------------------------
export interface PestVisualProbability {
  pest_class: string;
  probability: number;
}

export interface VisualPestPredictResponse {
  success: boolean;
  model: string;
  predicted_pest: string;
  confidence: number;
  top_k_predictions: PestVisualProbability[];
  image_quality: ImageQualityReport;
  warnings: string[];
  metadata: Record<string, any>;
}

export interface PestRiskRequest {
  Temperature: number;
  Humidity: number;
  Rainfall: number;
  Crop_Type: string;
  Soil_Type: string;
  Region: string;
}

export interface PestRiskProbability {
  risk_level: string;
  probability: number;
}

export interface PestRiskResponse {
  success: boolean;
  model: string;
  pest_severity_risk: string;
  confidence: number | null;
  top_k_predictions: PestRiskProbability[];
  warnings: string[];
  metadata: Record<string, any>;
}

// ------------------------------------------------------------------
// 6. SOIL ORGANIC CARBON ANALYSIS
// ------------------------------------------------------------------
export interface SoilAnalysisRequest {
  "pH(CaCl2)": number;
  "pH(H2O)": number;
  Clay: number;
  Silt: number;
  Sand: number;
  CaCO3: number;
  P: number;
  N: number;
  K: number;
  EC: number;
  NUTS_0: string;
  LC1: string;
}

export interface PredictionInterval {
  lower: number;
  upper: number;
  margin: number;
}

export interface SoilAnalysisResponse {
  success: boolean;
  model: string;
  predicted_soc: number;
  unit: string;
  prediction_interval: PredictionInterval;
  scope_warning: string;
  warnings: string[];
  metadata: Record<string, any>;
}

// ------------------------------------------------------------------
// 7. YIELD PREDICTION
// ------------------------------------------------------------------
export interface YieldPredictionRequest {
  Crop: string;
  Season: string;
  State: string;
  Area: number;
  Annual_Rainfall: number;
  Fertilizer: number;
  Pesticide: number;
  Fertilizer_Per_Area: number;
  Pesticide_Per_Area: number;
}

export interface YieldPredictionResponse {
  success: boolean;
  model: string;
  predicted_yield: number;
  prediction_interval: PredictionInterval;
  dataset_notice: string;
  warnings: string[];
  metadata: Record<string, any>;
}

// ------------------------------------------------------------------
// 8. LIVE CAMERA FRAME PREDICTION
// ------------------------------------------------------------------
export interface FramePredictionResponse {
  success: boolean;
  stream: string;
  prediction: string;
  confidence: number;
  raw_prediction: string;
  raw_confidence: number;
  quality_report: ImageQualityReport;
  timestamp: number;
}

// ------------------------------------------------------------------
// 9. WEATHER INTELLIGENCE
// ------------------------------------------------------------------
export interface CurrentWeatherResponse {
  latitude: number;
  longitude: number;
  timezone: string;
  observation_time: string;
  temperature: number;
  relative_humidity: number;
  precipitation: number;
  wind_speed: number;
  wind_direction: number;
  weather_code: number;
  is_day?: number;
  apparent_temperature?: number;
  cloud_cover?: number;
  wind_gusts?: number;
  data_source: string;
}

export interface HourlyForecastItem {
  time: string;
  temperature: number;
  relative_humidity: number;
  precipitation: number;
  wind_speed: number;
  wind_direction?: number;
  weather_code: number;
  is_day?: number;
  cloud_cover?: number;
  apparent_temperature?: number;
}

export interface DailyForecastItem {
  date: string;
  temperature_max: number;
  temperature_min: number;
  precipitation_sum: number;
  precipitation_probability_max?: number;
  wind_speed_max: number;
  weather_code: number;
  sunrise?: string;
  sunset?: string;
}

export interface WeatherForecastResponse {
  latitude: number;
  longitude: number;
  timezone: string;
  forecast_days: number;
  hourly: HourlyForecastItem[];
  daily: DailyForecastItem[];
  data_source: string;
}

export interface WeatherInsightItem {
  type: string;
  severity: "low" | "medium" | "high";
  title: string;
  description: string;
  affected_operations?: string[];
  recommended_actions?: string[];
}

export interface WeatherInsightsResponse {
  latitude: number;
  longitude: number;
  as_of: string;
  forecast_days: number;
  insights: WeatherInsightItem[];
}

// ------------------------------------------------------------------
// 10. MARKET INTELLIGENCE
// ------------------------------------------------------------------
export interface MarketPriceRecord {
  state: string;
  district: string;
  market: string;
  commodity: string;
  variety: string;
  grade: string;
  arrival_date: string;
  min_price: number;
  max_price: number;
  modal_price: number;
}

export interface MarketForecastItem {
  date: string;
  predicted_modal_price: number;
  lower_ci?: number;
  upper_ci?: number;
}

export interface MarketForecastResponse {
  commodity: string;
  model_used: string;
  forecast_horizon_days: number;
  forecasts: MarketForecastItem[];
  last_historical_date: string;
}

export interface ActionableSignalItem {
  type: string;
  severity: string;
  description: string;
  signal_strength: number;
  recommendation: string;
}

export interface MarketSignalsResponse {
  commodity: string;
  as_of_date: string;
  trend_signal: Record<string, any>;
  forecast_signal: Record<string, any>;
  actionable_signals: ActionableSignalItem[];
}

// ------------------------------------------------------------------
// 11. CROP CALENDAR
// ------------------------------------------------------------------
export interface GrowthStage {
  stage: string;
  duration_days: number;
  activities: string[];
  start_date?: string;
  end_date?: string;
  is_current?: boolean;
}

export interface CropCalendarItem {
  crop: string;
  crop_name_display?: string;
  primary_season: string;
  crop_duration_days: number;
  sowing_window: { start: string; end: string };
  growth_stages: GrowthStage[];
}

export interface CropScheduleResponse {
  crop: string;
  season: string;
  sowing_date: string;
  as_of_date: string;
  crop_duration_days: number;
  scheduled_growth_stages: GrowthStage[];
  current_stage: string;
  current_stage_progress_percent: number;
  next_stage: string;
  harvest_window: { start_date: string; end_date: string };
  upcoming_activities: { stage: string; activities: string[] }[];
  sowing_window_compliant: boolean;
  warnings: string[];
  data_source: string;
  is_reference_data: boolean;
}

// ------------------------------------------------------------------
// 12. HEALTH & SYSTEM READINESS
// ------------------------------------------------------------------
export interface ModelStatusDetail {
  status: "READY" | "UNAVAILABLE";
  task: string;
  artifact_path: string;
  framework: string;
  last_error: string | null;
}

export interface ModelsHealthResponse {
  status: "healthy" | "degraded";
  models: Record<string, "READY" | "UNAVAILABLE">;
  details: Record<string, ModelStatusDetail>;
}

export interface AppHealthResponse {
  status: string;
  service: string;
  version: string;
  models_status?: string;
  models: Record<string, string>;
}

// ------------------------------------------------------------------
// 13. SMART CROP ADVISOR
// ------------------------------------------------------------------
export interface SmartCropLocationInput {
  latitude: number;
  longitude: number;
  displayName?: string;
  city?: string;
  district?: string;
  state?: string;
  country?: string;
  source?: string;
}

export interface SmartCropSoilInput {
  nitrogen?: number | null;
  phosphorus?: number | null;
  potassium?: number | null;
  ph?: number | null;
}

export interface SmartCropWeatherOverrideInput {
  temperature?: number | null;
  humidity?: number | null;
  rainfall?: number | null;
}

export interface SmartCropFarmInput {
  area_acres?: number | null;
  water_availability?: string;
}

export interface SmartCropPreferencesInput {
  category?: string;
}

export interface SmartCropRequest {
  mode: "auto" | "hybrid" | "manual";
  location: SmartCropLocationInput;
  soil?: SmartCropSoilInput;
  weather_override?: SmartCropWeatherOverrideInput;
  farm?: SmartCropFarmInput;
  preferences?: SmartCropPreferencesInput;
}

export interface SmartCropFactorScores {
  season: number;
  temperature: number;
  rainfall: number;
  water?: number;
  ph: number;
  texture: number;
  soil_texture?: number;
  region: number;
  land_suitability?: number;
  sowing_feasibility?: number;
  ml?: number;
  [key: string]: number | undefined;
}

export interface SmartCropRecommendationItem {
  crop: string;
  display_name: string;
  scientific_name: string;
  ml_supported: boolean;
  category: string;
  suitability_score: number;
  suitability_level: "Highly Suitable" | "Suitable" | "Conditionally Suitable" | "Low Suitability" | "Insufficient Data" | "Not Suitable";
  land_suitability?: string;
  sowing_feasibility?: string;
  is_sowing_recommended_now?: boolean;
  ml_prediction?: {
    supported: boolean;
    probability: number | null;
  };
  image?: {
    available: boolean;
    url?: string | null;
    thumbnail_url?: string | null;
    provider?: string | null;
    source_url?: string | null;
    author?: string | null;
    license?: string | null;
    license_url?: string | null;
    alt?: string | null;
    relevance_score?: number | null;
    reason?: string | null;
  } | null;
  factor_scores: SmartCropFactorScores;
  limiting_factors?: string[];
  positive_factors?: string[];
  reasons: string[];
  warnings: string[];
  missing_data: string[];
  data_sources: { domain: string; source: string }[];
  profile_details: Record<string, any>;
}

export interface SmartCropSoilParameter {
  value: number | null;
  unit: string;
  label: string;
  provenance: string;
  source_description: string;
  is_estimated: boolean;
}

export interface SmartCropResponse {
  success: boolean;
  engine_version: string;
  mode: string;
  data_completeness: number;
  location: {
    latitude: number;
    longitude: number;
    display_name: string;
    district?: string;
    state?: string;
    country?: string;
  };
  season: {
    season: string;
    regional_season: string;
    sowing_window: string;
    harvest_window: string;
    current_month: string;
    state: string;
    source: string;
    data_status: string;
  };
  weather: {
    current_temperature?: number;
    current_humidity?: number;
    current_rainfall?: number;
    recent_rainfall_14d?: number;
    recent_temperature_14d?: number;
    forecast_temperature_mean?: number;
    forecast_rainfall_sum?: number;
    rain_probability_max?: number;
    wind_speed?: number;
    et0?: number;
    data_available: boolean;
    source: string;
    error_message?: string;
  };
  soil: {
    ph?: SmartCropSoilParameter;
    nitrogen?: SmartCropSoilParameter;
    phosphorus?: SmartCropSoilParameter;
    potassium?: SmartCropSoilParameter;
    soil_texture: string;
    organic_carbon_g_kg?: number;
    soil_depth_layer: string;
    data_source: string;
    data_completeness: number;
  };
  ml_status: {
    available: boolean;
    anomaly_status: string;
  };
  farm: {
    area_acres?: number;
    water_availability: string;
  };
  recommendations: SmartCropRecommendationItem[];
}

// ------------------------------------------------------------------
// 14. IRRIGATION INTELLIGENCE & WATER MANAGEMENT
// ------------------------------------------------------------------
export interface FieldIrrigationContext {
  field_id: number;
  field_name: string;
  farm_name: string;
  crop_name: string;
  variety?: string | null;
  growth_stage: string;
  area_value: number;
  area_unit: string;
  total_area_m2: number;
  water_source: string;
  irrigation_method: string;
  soil_type: string;
}

export interface WaterStatusInfo {
  current_swc: number;
  field_capacity: number;
  wilting_point: number;
  critical_threshold: number;
  status_code: string;
  status_title: string;
  status_description: string;
  water_zone: string;
}

export interface IrrigationDecisionInfo {
  state: "IRRIGATE_NOW" | "IRRIGATE_SOON" | "WAIT_FOR_RAIN" | "MONITOR" | "NO_IRRIGATION_REQUIRED" | "INSUFFICIENT_DATA";
  state_title: string;
  window: string;
  net_depth_mm?: number | null;
  gross_depth_mm?: number | null;
  water_volume_liters?: number | null;
  efficiency_pct?: number | null;
  efficiency_note?: string | null;
  reason: string;
  actionable: boolean;
}

export interface ET0Info {
  et0_today_mm: number;
  et0_tomorrow_mm: number;
  et0_3day_mm: number;
  etc_today_mm?: number | null;
  kc_value?: number | null;
  kc_source: string;
  kc_note: string;
}

export interface TrajectoryPoint {
  label: string;
  timestamp: string;
  swc_projected: number;
  rainfall_mm: number;
  etc_mm: number;
  threshold: number;
  status: string;
}

export interface DailyPlanItem {
  day: string;
  date_str: string;
  status: string;
  rain_expected_mm: number;
  etc_mm: number;
  action: string;
}

export interface WaterBudgetInfo {
  period: string;
  rainfall_received_mm: number;
  irrigation_applied_mm: number;
  crop_consumed_mm: number;
  estimated_deficit_mm: number;
  season_total_liters: number;
}

export interface MLForecastSignal {
  ml_predicted_swc_3h: number;
  persistence_swc_3h: number;
  target_unit: string;
  horizon_hours: number;
  baseline_note: string;
}

export interface WaterSavingOpportunity {
  type: string;
  title: string;
  description: string;
  potential_water_saved_liters?: number | null;
}

export interface WhatIfScenarioResult {
  scenario_id: string;
  scenario_name: string;
  description: string;
  water_applied_mm: number;
  projected_swc_48h: number;
  deficit_mm: number;
  risk_level: string;
  recommendation: string;
}

export interface IrrigationLogCreate {
  field_id: number;
  water_amount_mm: number;
  method?: string;
  duration_minutes?: number;
  notes?: string;
  logged_at?: string;
}

export interface IrrigationLogResponse {
  id: number;
  field_id: number;
  farmer_id: number;
  water_amount_mm: number;
  water_amount_liters?: number | null;
  method?: string | null;
  duration_minutes?: number | null;
  notes?: string | null;
  logged_at: string;
  created_at: string;
}

export interface WhatIfSimulationRequest {
  field_id: number;
  custom_irrigation_mm?: number;
  delay_hours?: number;
  simulated_rain_mm?: number;
}

export interface WhatIfSimulationResponse {
  field_id: number;
  base_swc: number;
  scenarios: WhatIfScenarioResult[];
}

export interface IrrigationIntelligenceResponse {
  field_context: FieldIrrigationContext;
  water_status: WaterStatusInfo;
  decision: IrrigationDecisionInfo;
  et0: ET0Info;
  water_balance_trajectory: TrajectoryPoint[];
  seven_day_plan: DailyPlanItem[];
  water_budget: WaterBudgetInfo;
  ml_forecast: MLForecastSignal;
  evidence_items: string[];
  evidence_quality: string;
  water_saving_opportunities: WaterSavingOpportunity[];
  what_if_scenarios: WhatIfScenarioResult[];
  irrigation_history: IrrigationLogResponse[];
  generated_at: string;
}

