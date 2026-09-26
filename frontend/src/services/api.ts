import type {
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
  SmartCropRequest,
  SmartCropResponse,
  IrrigationIntelligenceResponse,
  IrrigationLogCreate,
  IrrigationLogResponse,
  WhatIfSimulationRequest,
  WhatIfSimulationResponse,
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

  async predictCropSmart(payload: SmartCropRequest): Promise<SmartCropResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/crop/recommend-smart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<SmartCropResponse>(res);
  },

  async getCropImage(cropId: string, refresh: boolean = false): Promise<any> {
    const res = await fetch(`${BASE_URL}/api/v1/images/crop/${encodeURIComponent(cropId)}?refresh=${refresh}`);
    return handleResponse<any>(res);
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

  async getIrrigationIntelligence(
    fieldId?: number,
    lat?: number,
    lon?: number,
    userId?: string
  ): Promise<IrrigationIntelligenceResponse> {
    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;

    const params: string[] = [];
    if (fieldId !== undefined) params.push(`field_id=${fieldId}`);
    if (lat !== undefined) params.push(`lat=${lat}`);
    if (lon !== undefined) params.push(`lon=${lon}`);

    const queryString = params.length > 0 ? `?${params.join('&')}` : '';
    const res = await fetch(`${BASE_URL}/api/v1/irrigation/intelligence${queryString}`, { headers });
    return handleResponse<IrrigationIntelligenceResponse>(res);
  },

  async logIrrigationEvent(
    payload: IrrigationLogCreate,
    userId?: string
  ): Promise<IrrigationLogResponse> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;

    const res = await fetch(`${BASE_URL}/api/v1/irrigation/log`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<IrrigationLogResponse>(res);
  },

  async getIrrigationLogs(
    fieldId: number,
    userId?: string
  ): Promise<IrrigationLogResponse[]> {
    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;

    const res = await fetch(`${BASE_URL}/api/v1/irrigation/logs?field_id=${fieldId}`, { headers });
    return handleResponse<IrrigationLogResponse[]>(res);
  },

  async simulateWhatIf(
    payload: WhatIfSimulationRequest,
    userId?: string
  ): Promise<WhatIfSimulationResponse> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;

    const res = await fetch(`${BASE_URL}/api/v1/irrigation/simulate`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<WhatIfSimulationResponse>(res);
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
  async getWeatherCurrent(lat: number, lon: number): Promise<CurrentWeatherResponse> {
    const res = await fetch(`${BASE_URL}/api/weather/current?latitude=${lat}&longitude=${lon}`);
    return handleResponse<CurrentWeatherResponse>(res);
  },

  async getWeatherForecast(lat: number, lon: number, forecastDays: number = 7): Promise<WeatherForecastResponse> {
    const res = await fetch(`${BASE_URL}/api/weather/forecast?latitude=${lat}&longitude=${lon}&forecast_days=${forecastDays}`);
    return handleResponse<WeatherForecastResponse>(res);
  },

  async getWeatherInsights(lat: number, lon: number): Promise<WeatherInsightsResponse> {
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

  // ------------------------------------------------------------------
  // Farmer Profile & Personalized Farm Command Center (/api/v1/farmer)
  // ------------------------------------------------------------------
  async getFarmerProfile(userId?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/profile`, { headers });
    return handleResponse<any>(res);
  },

  async updateFarmerProfile(payload: any, userId?: string): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/profile`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async getFarmerDashboard(userId?: string, lat?: number, lon?: number, displayName?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;

    let url = `${BASE_URL}/api/v1/farmer/dashboard`;
    const params: string[] = [];
    if (lat !== undefined && lon !== undefined) {
      params.push(`lat=${lat}`, `lon=${lon}`);
    }
    if (displayName) {
      params.push(`display_name=${encodeURIComponent(displayName)}`);
    }
    if (params.length > 0) {
      url += `?${params.join('&')}`;
    }

    const res = await fetch(url, { headers });
    return handleResponse<any>(res);
  },

  async createFarm(payload: any, userId?: string): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/farms`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async updateFarm(farmId: number, payload: any, userId?: string): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/farms/${farmId}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async deleteFarm(farmId: number, userId?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/farms/${farmId}`, {
      method: 'DELETE',
      headers,
    });
    return handleResponse<any>(res);
  },

  async createField(payload: any, userId?: string): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/fields`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async updateField(fieldId: number, payload: any, userId?: string): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/fields/${fieldId}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async deleteField(fieldId: number, userId?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/fields/${fieldId}`, {
      method: 'DELETE',
      headers,
    });
    return handleResponse<any>(res);
  },

  async createCrop(payload: any, userId?: string): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/crops`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async updateCrop(cropId: number, payload: any, userId?: string): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/crops/${cropId}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async deleteCrop(cropId: number, userId?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/crops/${cropId}`, {
      method: 'DELETE',
      headers,
    });
    return handleResponse<any>(res);
  },

  async createObservation(payload: any, userId?: string): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/observations`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async completeActionItem(actionId: string, status: string = 'DONE', userId?: string): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/actions/${actionId}/complete`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ status }),
    });
    return handleResponse<any>(res);
  },

  async getNotificationPreferences(userId?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/notifications/preferences`, { headers });
    return handleResponse<any>(res);
  },

  async updateNotificationPreferences(payload: any, userId?: string): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/farmer/notifications/preferences`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  // ------------------------------------------------------------------
  // Farm AI Copilot / Assistant (/api/v1/assistant)
  // ------------------------------------------------------------------
  async sendCopilotChat(
    payload: {
      message: string;
      conversation_id?: string;
      page_context?: any;
    },
    userId?: string
  ): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;

    const res = await fetch(`${BASE_URL}/api/v1/assistant/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async streamCopilotChat(
    payload: {
      message: string;
      conversation_id?: string;
      page_context?: any;
    },
    onEvent: (event: { event: string; data: any }) => void,
    userId?: string,
    signal?: AbortSignal
  ): Promise<void> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;

    const res = await fetch(`${BASE_URL}/api/v1/assistant/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal,
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new ApiClientError(errText || 'Failed to connect to assistant stream', res.status);
    }

    if (!res.body) {
      throw new Error('Response body is null');
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let currentEvent = 'message_delta';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.slice(6).trim();
        } else if (trimmed.startsWith('data:')) {
          const rawData = trimmed.slice(5).trim();
          let parsedData: any = rawData;
          try {
            parsedData = JSON.parse(rawData);
          } catch {
            // Keep string if not JSON
          }
          onEvent({ event: currentEvent, data: parsedData });
        }
      }
    }
  },

  async analyzeCopilotImage(
    file: File,
    taskType: 'disease' | 'pest' = 'disease',
    conversationId?: string,
    userId?: string
  ): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('task_type', taskType);
    if (conversationId) formData.append('conversation_id', conversationId);

    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;

    const res = await fetch(`${BASE_URL}/api/v1/assistant/analyze-image`, {
      method: 'POST',
      headers,
      body: formData,
    });
    return handleResponse<any>(res);
  },

  async getCopilotConversations(userId?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/assistant/conversations`, { headers });
    return handleResponse<any>(res);
  },

  async getCopilotConversation(conversationId: string, userId?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/assistant/conversations/${conversationId}`, { headers });
    return handleResponse<any>(res);
  },

  async deleteCopilotConversation(conversationId: string, userId?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/assistant/conversations/${conversationId}`, {
      method: 'DELETE',
      headers,
    });
    return handleResponse<any>(res);
  },

  async updateCopilotConversationTitle(
    conversationId: string,
    title: string,
    userId?: string
  ): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (userId) headers['X-User-ID'] = userId;
    const res = await fetch(`${BASE_URL}/api/v1/assistant/conversations/${conversationId}/title`, {
      method: 'PUT',
      headers,
      body: JSON.stringify({ title }),
    });
    return handleResponse<any>(res);
  },
};

