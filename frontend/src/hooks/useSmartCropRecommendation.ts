import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { SmartCropRequest, SmartCropResponse } from '../types/api';
import { UserLocation } from '../types/location';

export type RecommendationMode = 'auto' | 'hybrid' | 'manual';

export interface SoilOverrides {
  nitrogen?: number | null;
  phosphorus?: number | null;
  potassium?: number | null;
  ph?: number | null;
}

export interface WeatherOverrides {
  temperature?: number | null;
  humidity?: number | null;
  rainfall?: number | null;
}

export interface FarmOverrides {
  area_acres?: number | null;
  water_availability: string;
}

export interface AnalysisStage {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
}

const STAGES_LIST: { id: string; label: string }[] = [
  { id: 'location', label: 'Reading field location' },
  { id: 'weather', label: 'Fetching weather telemetry' },
  { id: 'soil', label: 'Reading soil context' },
  { id: 'season', label: 'Determining regional season' },
  { id: 'calendar', label: 'Checking crop calendar' },
  { id: 'requirements', label: 'Evaluating crop requirements' },
  { id: 'ml', label: 'Running frozen ML model' },
  { id: 'ranking', label: 'Ranking crop options' },
];

export const useSmartCropRecommendation = () => {
  const [mode, setMode] = useState<RecommendationMode>('auto');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [stages, setStages] = useState<AnalysisStage[]>(
    STAGES_LIST.map((s) => ({ ...s, status: 'pending' }))
  );
  const [result, setResult] = useState<SmartCropResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Overrides for Hybrid mode
  const [soilOverrides, setSoilOverrides] = useState<SoilOverrides>({
    nitrogen: null,
    phosphorus: null,
    potassium: null,
    ph: null,
  });

  const [weatherOverrides, setWeatherOverrides] = useState<WeatherOverrides>({
    temperature: null,
    humidity: null,
    rainfall: null,
  });

  const [farmOverrides, setFarmOverrides] = useState<FarmOverrides>({
    area_acres: null,
    water_availability: 'unknown',
  });

  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  const analyzeField = useCallback(async (currentLocation: UserLocation | null) => {
    if (!currentLocation) {
      setError('Field location is required. Please select or detect your location.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    // Reset stages
    setStages(STAGES_LIST.map((s) => ({ ...s, status: 'pending' })));

    try {
      // Simulate real step updates for UX transparency
      for (let i = 0; i < STAGES_LIST.length; i++) {
        setStages((prev) =>
          prev.map((st, idx) => {
            if (idx < i) return { ...st, status: 'completed' };
            if (idx === i) return { ...st, status: 'active' };
            return { ...st, status: 'pending' };
          })
        );
        await new Promise((resolve) => setTimeout(resolve, 80));
      }

      const payload: SmartCropRequest = {
        mode,
        location: {
          latitude: currentLocation.latitude,
          longitude: currentLocation.longitude,
          displayName: currentLocation.displayName,
          city: currentLocation.city,
          district: currentLocation.district,
          state: currentLocation.state,
          country: currentLocation.country || 'India',
          source: currentLocation.source,
        },
        soil: {
          nitrogen: soilOverrides.nitrogen,
          phosphorus: soilOverrides.phosphorus,
          potassium: soilOverrides.potassium,
          ph: soilOverrides.ph,
        },
        weather_override: {
          temperature: weatherOverrides.temperature,
          humidity: weatherOverrides.humidity,
          rainfall: weatherOverrides.rainfall,
        },
        farm: {
          area_acres: farmOverrides.area_acres,
          water_availability: farmOverrides.water_availability,
        },
        preferences: {
          category: categoryFilter,
        },
      };

      const response = await api.predictCropSmart(payload);

      setStages((prev) => prev.map((st) => ({ ...st, status: 'completed' })));
      setResult(response);
    } catch (err: any) {
      setStages((prev) =>
        prev.map((st) => (st.status === 'active' ? { ...st, status: 'failed' } : st))
      );
      setError(err.message || 'Failed to analyze field conditions.');
    } finally {
      setIsAnalyzing(false);
    }
  }, [mode, soilOverrides, weatherOverrides, farmOverrides, categoryFilter]);

  return {
    mode,
    setMode,
    isAnalyzing,
    stages,
    result,
    error,
    soilOverrides,
    setSoilOverrides,
    weatherOverrides,
    setWeatherOverrides,
    farmOverrides,
    setFarmOverrides,
    categoryFilter,
    setCategoryFilter,
    analyzeField,
  };
};
