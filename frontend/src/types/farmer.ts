export interface SoilValueWithProvenance {
  value?: any;
  provenance: 'MEASURED' | 'ESTIMATED' | 'UNKNOWN';
}

export interface GeoJSONPolygon {
  type: 'Polygon';
  coordinates: number[][][]; // [[[lng, lat], [lng, lat], ...]]
}

export interface PlantObservationRecord {
  id: number;
  field_id: number;
  crop_planting_id?: number;
  observation_date: string;
  image_url?: string;
  disease_result?: string;
  pest_result?: string;
  severity: string;
  notes?: string;
  location_in_field?: string;
  created_at?: string;
}

export interface CropPlanting {
  id: number;
  field_id: number;
  crop_id?: string;
  crop_name: string;
  scientific_name?: string;
  variety?: string;
  category?: string;
  sowing_date?: string;
  expected_harvest_date?: string;
  growth_stage?: string;
  growth_stage_source?: 'farmer' | 'calculated';
  cultivation_type?: string;
  irrigation_method?: string;
  water_availability?: string;
  status: 'PLANNED' | 'ACTIVE' | 'HARVESTED' | 'COMPLETED';
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface FieldRecord {
  id: number;
  farm_id: number;
  field_name: string;
  area_value: number;
  area_unit: string;
  total_area_m2: number;
  latitude?: number;
  longitude?: number;
  boundary_geojson?: GeoJSONPolygon | null;
  perimeter_m?: number;
  centroid_lat?: number;
  centroid_lng?: number;
  geometry_source?: 'GEOMETRIC' | 'MANUAL';
  geometry_updated_at?: string;
  soil_type?: string;
  soil_test_available: boolean;
  ph?: number;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  organic_carbon?: number;
  water_source?: string;
  soil_data?: {
    ph: SoilValueWithProvenance;
    nitrogen: SoilValueWithProvenance;
    phosphorus: SoilValueWithProvenance;
    potassium: SoilValueWithProvenance;
    organic_carbon: SoilValueWithProvenance;
    ec: SoilValueWithProvenance;
    texture: SoilValueWithProvenance;
    moisture: SoilValueWithProvenance;
  };
  notes?: string;
  plantings: CropPlanting[];
  observations?: PlantObservationRecord[];
  created_at?: string;
  updated_at?: string;
}

export interface FarmRecord {
  id: number;
  farmer_id: number;
  farm_name: string;
  location_name?: string;
  latitude: number;
  longitude: number;
  area_value: number;
  area_unit: string;
  total_area_m2: number;
  soil_type_manual?: string;
  water_source?: string;
  irrigation_method?: string;
  ownership_type?: string;
  notes?: string;
  fields: FieldRecord[];
  created_at?: string;
  updated_at?: string;
}

export interface FarmerProfile {
  id: number;
  user_id: string;
  full_name: string;
  phone?: string;
  email?: string;
  preferred_language: string;
  farms: FarmRecord[];
  created_at?: string;
  updated_at?: string;
}

export interface RiskItem {
  id: string;
  category: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: string;
  confidence: string;
  reasoning: string;
  recommended_follow_up?: string;
  affected_crop?: string;
  affected_stage?: string;
  evidence?: any[];
  detected_at?: string;
  valid_until?: string;
}

export interface OpportunityItem {
  id: string;
  category: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: string;
  confidence: string;
  reasoning: string;
  suggested_action?: string;
  time_window?: string;
  affected_crop?: string;
  affected_stage?: string;
  evidence?: any[];
  detected_at?: string;
}

export interface ActionPlanItem {
  id: string;
  action_type: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'monitoring' | 'needs_review' | 'TODO' | 'DONE' | 'DISMISSED';
  title: string;
  action: string;
  reason: string;
  affected_crop?: string;
  affected_stage?: string;
  location?: string;
  recommended_time?: string;
  time_window?: string;
  due_date?: string;
}

export interface SmartAlertItem {
  id: string;
  priority: 'Critical' | 'High' | 'Moderate' | 'Info';
  category: string;
  title: string;
  description: string;
  trigger_evidence?: string;
  potential_impact?: string;
  recommended_action?: string;
  status?: string;
  crop_name?: string;
  field_name?: string;
  timestamp: string;
  actionable: boolean;
}

export interface NotificationPreferences {
  farmer_id: number;
  channels: {
    in_app: boolean;
    email: boolean;
    sms: boolean;
    whatsapp: boolean;
  };
  categories: {
    critical_risks: boolean;
    weather: boolean;
    crop_health: boolean;
    irrigation: boolean;
    market: boolean;
    calendar: boolean;
    action_reminders: boolean;
  };
  quiet_hours: {
    enabled: boolean;
    start: string;
    end: string;
    critical_override: boolean;
  };
}

export interface WeatherImpactItem {
  crop_name: string;
  field_name: string;
  temperature?: number;
  rain_forecast_mm?: number;
  impact: string;
  action: string;
  status: 'Favorable' | 'Monitor' | 'Warning';
}

export interface SoilImpactItem {
  crop_name: string;
  field_name: string;
  ph_status: string;
  texture_status: string;
  n_status: string;
  p_status: string;
  k_status: string;
  impact_text: string;
}

export interface IrrigationContextItem {
  crop_name: string;
  field_name: string;
  current_moisture?: number;
  expected_moisture?: number;
  rainfall_forecast_mm?: number;
  irrigation_method?: string;
  water_availability?: string;
  status: 'LOW' | 'NORMAL' | 'HIGH' | 'MONITOR';
  next_window?: string;
  model_note: string;
}

export interface FertilizerContextItem {
  crop_name: string;
  field_name: string;
  n_status: string;
  p_status: string;
  k_status: string;
  model_available: boolean;
  model_scope_note: string;
  recommendation?: string;
  reason: string;
}

export interface PestRiskItem {
  crop_name: string;
  field_name: string;
  risk_level: 'Low' | 'Moderate' | 'High';
  weather_drivers: string[];
  crop_stage?: string;
  action: string;
  model_scope_note: string;
}

export interface MarketWatchItem {
  crop_name: string;
  commodity: string;
  current_price?: number;
  trend: string;
  change_30d_pct?: number;
  period: string;
  market_location?: string;
}

export interface CropTimelineItem {
  date_label: string;
  crop_name: string;
  field_name: string;
  event_title: string;
  reason: string;
  priority: 'Critical' | 'High' | 'Moderate' | 'Info';
  source: string;
  evidence_status: string;
}

export interface ImpactMatrixRow {
  crop_name: string;
  field_name: string;
  area_display: string;
  weather: string;
  soil: string;
  water: string;
  pest: string;
  market: string;
  attention_level: 'High' | 'Medium' | 'Low';
}

export interface DataQualitySummary {
  location_confidence: string;
  weather_freshness: string;
  soil_availability: string;
  npk_availability: string;
  market_status: string;
  profile_completeness_pct: number;
  missing_fields: string[];
}

export interface TodayFarmStatus {
  weather_summary: string;
  soil_summary: string;
  water_summary: string;
  market_summary: string;
  action_items_count: number;
  critical_risks_count?: number;
}

export interface ActiveCropCard {
  id: number;
  field_id: number;
  crop_name: string;
  field_name: string;
  area_display: string;
  growth_stage: string;
  days_since_sowing?: number;
  sowing_date?: string;
  expected_harvest?: string;
  weather_status: string;
  water_status: string;
  pest_status: string;
  market_trend: string;
}

export interface FarmDashboardResponse {
  farmer: FarmerProfile;
  location: {
    latitude: number;
    longitude: number;
    display_name: string;
    source: string;
  };
  total_farm_area: number;
  total_farm_area_unit: string;
  active_crops_count: number;
  fields_count: number;
  today_status: TodayFarmStatus;
  active_crop_cards: ActiveCropCard[];
  weather_impacts: WeatherImpactItem[];
  soil_impacts: SoilImpactItem[];
  irrigation_items: IrrigationContextItem[];
  fertilizer_items: FertilizerContextItem[];
  pest_items: PestRiskItem[];
  market_watch: MarketWatchItem[];
  crop_calendar_events: any[];
  risks_and_opportunities?: {
    risks: RiskItem[];
    opportunities: OpportunityItem[];
    summary?: any;
  };
  risks?: RiskItem[];
  opportunities?: OpportunityItem[];
  actions?: ActionPlanItem[];
  risk_opportunity?: any;
  action_plan?: {
    actions: ActionPlanItem[];
    total_actions: number;
  };
  alerts: SmartAlertItem[];
  dispatched_alerts?: SmartAlertItem[];
  plant_observations?: PlantObservationRecord[];
  notification_preferences?: NotificationPreferences;
  timeline: CropTimelineItem[];
  impact_matrix: ImpactMatrixRow[];
  data_quality: DataQualitySummary;
  last_updated: string;
}
