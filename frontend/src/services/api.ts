import {
  AppHealthResponse,
  ModelsHealthResponse,
  CropRecommendationRequest,
  CropRecommendationResponse,
  DiseasePredictResponse,
  FertilizerRecommendRequest,
  FertilizerRecommendResponse,
  IrrigationPredictionRequest,
  IrrigationPredictionResponse,
  VisualPestPredictResponse,
  PestRiskRequest,
  PestRiskResponse,
  SoilAnalysisRequest,
  SoilAnalysisResponse,
  YieldPredictionRequest,
  YieldPredictionResponse,
  FramePredictionResponse,
  CurrentWeatherResponse,
  WeatherForecastResponse,
  WeatherInsightsResponse,
  MarketPriceRecord,
  MarketForecastResponse,
  MarketSignalsResponse,
  CropCalendarItem,
  CropScheduleResponse,
} from '../types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

class ApiClientError extends Error {
  statusCode: number;
  details?: any;

  constructor(message: string, statusCode: number, details?: any) {
    super(message);
    this.name = 'ApiClientError';
    this.statusCode = statusCode;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = 'An unexpected error occurred during request processing.';
    let detailsObj: any = null;
    try {
      const errData = await response.json();
      if (errData.detail) {
        errorDetail = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
        detailsObj = errData.detail;
      } else if (errData.error) {
        errorDetail = errData.error;
      } else if (errData.message) {
        errorDetail = errData.message;
      }
    } catch {
      errorDetail = response.statusText || errorDetail;
    }

    throw new ApiClientError(errorDetail, response.status, detailsObj);
  }

  return response.json() as Promise<T>;
}

// Centralized API Service Object
export const api = {
  // ------------------------------------------------------------------
  // System & Health Endpoints
  // ------------------------------------------------------------------
  async getAppHealth(): Promise<AppHealthResponse> {
    const res = await fetch(`${BASE_URL}/health`);
    return handleResponse<AppHealthResponse>(res);
  },

  async getModelsHealth(): Promise<ModelsHealthResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/models/health`);
    return handleResponse<ModelsHealthResponse>(res);
  },

  // ------------------------------------------------------------------
  // ML Inference Services (/api/v1)
  // ------------------------------------------------------------------
  async predictCrop(payload: CropRecommendationRequest): Promise<CropRecommendationResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/crop/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<CropRecommendationResponse>(res);
  },

  async predictDisease(file: File, includeGradcam: boolean = false): Promise<DiseasePredictResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${BASE_URL}/api/v1/disease/predict?include_gradcam=${includeGradcam}`;
    const res = await fetch(url, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<DiseasePredictResponse>(res);
  },

  async predictFertilizer(payload: FertilizerRecommendRequest): Promise<FertilizerRecommendResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/fertilizer/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<FertilizerRecommendResponse>(res);
  },

  async predictIrrigation(payload: IrrigationPredictionRequest): Promise<IrrigationPredictionResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/irrigation/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<IrrigationPredictionResponse>(res);
  },

  async predictPestVisual(file: File): Promise<VisualPestPredictResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${BASE_URL}/api/v1/pest/predict`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<VisualPestPredictResponse>(res);
  },

  async predictPestRisk(payload: PestRiskRequest): Promise<PestRiskResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/pest/risk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<PestRiskResponse>(res);
  },

  async analyzeSoil(payload: SoilAnalysisRequest): Promise<SoilAnalysisResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/soil/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<SoilAnalysisResponse>(res);
  },

  async predictYield(payload: YieldPredictionRequest): Promise<YieldPredictionResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/yield/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<YieldPredictionResponse>(res);
  },

  // ------------------------------------------------------------------
  // Live OpenCV Endpoints (/api/v1)
  // ------------------------------------------------------------------
  async processDiseaseLiveFrame(file: Blob, sessionId: string = 'default_session'): Promise<FramePredictionResponse> {
    const formData = new FormData();
    formData.append('file', file, 'frame.jpg');

    const res = await fetch(`${BASE_URL}/api/v1/disease/live`, {
      method: 'POST',
      headers: { 'x-session-id': sessionId },
      body: formData,
    });
    return handleResponse<FramePredictionResponse>(res);
  },

  async processPestLiveFrame(file: Blob, sessionId: string = 'default_session'): Promise<FramePredictionResponse> {
    const formData = new FormData();
    formData.append('file', file, 'frame.jpg');

    const res = await fetch(`${BASE_URL}/api/v1/pest/live`, {
      method: 'POST',
      headers: { 'x-session-id': sessionId },
      body: formData,
    });
    return handleResponse<FramePredictionResponse>(res);
  },

  getLiveWebSocketUrl(type: 'disease' | 'pest'): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws/${type}/live`;
  },

  // ------------------------------------------------------------------
  // Weather Intelligence (/api/weather)
  // ------------------------------------------------------------------
  async getWeatherCurrent(lat: number = 19.076, lon: number = 72.8777): Promise<CurrentWeatherResponse> {
    const res = await fetch(`${BASE_URL}/api/weather/current?latitude=${lat}&longitude=${lon}`);
    return handleResponse<CurrentWeatherResponse>(res);
  },

  async getWeatherForecast(lat: number = 19.076, lon: number = 72.8777, forecastDays: number = 7): Promise<WeatherForecastResponse> {
    const res = await fetch(`${BASE_URL}/api/weather/forecast?latitude=${lat}&longitude=${lon}&forecast_days=${forecastDays}`);
    return handleResponse<WeatherForecastResponse>(res);
  },

  async getWeatherInsights(lat: number = 19.076, lon: number = 72.8777): Promise<WeatherInsightsResponse> {
    const res = await fetch(`${BASE_URL}/api/weather/insights?latitude=${lat}&longitude=${lon}`);
    return handleResponse<WeatherInsightsResponse>(res);
  },

  // ------------------------------------------------------------------
  // Market Intelligence (/api/market)
  // ------------------------------------------------------------------
  async getMarketCurrent(commodity: string, state?: string): Promise<MarketPriceRecord> {
    let url = `${BASE_URL}/api/market/current?commodity=${encodeURIComponent(commodity)}`;
    if (state) url += `&state=${encodeURIComponent(state)}`;
    const res = await fetch(url);
    return handleResponse<MarketPriceRecord>(res);
  },

  async getMarketHistory(commodity: string): Promise<MarketPriceRecord[]> {
    const url = `${BASE_URL}/api/market/history?commodity=${encodeURIComponent(commodity)}`;
    const res = await fetch(url);
    return handleResponse<MarketPriceRecord[]>(res);
  },

  async getMarketForecast(commodity: string, horizon: number = 7, model: string = 'ets'): Promise<MarketForecastResponse> {
    const url = `${BASE_URL}/api/market/forecast?commodity=${encodeURIComponent(commodity)}&horizon=${horizon}&model=${model}`;
    const res = await fetch(url);
    return handleResponse<MarketForecastResponse>(res);
  },

  async getMarketSignals(commodity: string): Promise<MarketSignalsResponse> {
    const url = `${BASE_URL}/api/market/signals?commodity=${encodeURIComponent(commodity)}`;
    const res = await fetch(url);
    return handleResponse<MarketSignalsResponse>(res);
  },

  // ------------------------------------------------------------------
  // Crop Calendar (/api/crop-calendar)
  // ------------------------------------------------------------------
  async getCropCalendarCatalogue(): Promise<CropCalendarItem[]> {
    const res = await fetch(`${BASE_URL}/api/crop-calendar`);
    return handleResponse<CropCalendarItem[]>(res);
  },

  async getCropSchedule(crop: string, sowingDate: string, season?: string): Promise<CropScheduleResponse> {
    let url = `${BASE_URL}/api/crop-calendar/${encodeURIComponent(crop)}/schedule?sowing_date=${sowingDate}`;
    if (season) url += `&season=${encodeURIComponent(season)}`;
    const res = await fetch(url);
    return handleResponse<CropScheduleResponse>(res);
  },
};
