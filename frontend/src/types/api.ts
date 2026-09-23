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
  data_source: string;
}

export interface HourlyForecastItem {
  time: string;
  temperature: number;
  relative_humidity: number;
  precipitation: number;
  wind_speed: number;
  weather_code: number;
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
