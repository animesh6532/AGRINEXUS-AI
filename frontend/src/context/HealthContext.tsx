import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { ModelsHealthResponse } from '../types/api';

interface HealthContextType {
  isApiConnected: boolean;
  isModelSystemReady: boolean;
  modelStatus: ModelsHealthResponse | null;
  lastChecked: Date | null;
  refreshHealth: () => Promise<void>;
  isLoading: boolean;
}

const HealthContext = createContext<HealthContextType | undefined>(undefined);

export const HealthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isApiConnected, setIsApiConnected] = useState<boolean>(false);
  const [isModelSystemReady, setIsModelSystemReady] = useState<boolean>(false);
  const [modelStatus, setModelStatus] = useState<ModelsHealthResponse | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshHealth = useCallback(async () => {
    setIsLoading(true);
    try {
      // 1. Check API Liveness
      const appHealth = await api.getAppHealth();
      const connected = appHealth && appHealth.status === 'healthy';
      setIsApiConnected(connected);

      // 2. Check Models Readiness
      const mHealth = await api.getModelsHealth();
      setModelStatus(mHealth);
      
      const ready = mHealth && mHealth.status === 'healthy';
      setIsModelSystemReady(ready);
      setLastChecked(new Date());
    } catch {
      setIsApiConnected(false);
      setIsModelSystemReady(false);
      setModelStatus(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshHealth();
    // Poll every 15 seconds
    const interval = setInterval(refreshHealth, 15000);
    return () => clearInterval(interval);
  }, [refreshHealth]);

  return (
    <HealthContext.Provider
      value={{
        isApiConnected,
        isModelSystemReady,
        modelStatus,
        lastChecked,
        refreshHealth,
        isLoading
      }}
    >
      {children}
    </HealthContext.Provider>
  );
};

export const useHealth = () => {
  const context = useContext(HealthContext);
  if (!context) {
    throw new Error('useHealth must be used within a HealthProvider');
  }
  return context;
};
