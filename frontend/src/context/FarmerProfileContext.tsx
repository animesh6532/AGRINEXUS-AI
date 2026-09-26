import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { useLocationContext } from './LocationContext';
import { api } from '../services/api';
import type {
  FarmerProfile,
  FarmRecord,
  FieldRecord,
  CropPlanting,
  FarmDashboardResponse,
} from '../types/farmer';

interface FarmerProfileContextType {
  farmer: FarmerProfile | null;
  farms: FarmRecord[];
  fields: FieldRecord[];
  activeCrops: CropPlanting[];
  dashboardData: FarmDashboardResponse | null;
  selectedFarm: FarmRecord | null;
  selectedField: FieldRecord | null;
  selectedCrop: CropPlanting | null;
  isLoading: boolean;
  isRefreshing: boolean;
  error: string | null;

  fetchProfile: () => Promise<void>;
  fetchDashboard: (locationOverride?: { latitude: number; longitude: number; displayName?: string }) => Promise<void>;
  saveProfile: (data: Partial<FarmerProfile>) => Promise<void>;
  saveFarm: (data: Partial<FarmRecord>) => Promise<FarmRecord | null>;
  saveField: (data: Partial<FieldRecord> & { farm_id: number }) => Promise<FieldRecord | null>;
  saveCrop: (data: Partial<CropPlanting> & { field_id: number }) => Promise<CropPlanting | null>;
  deleteFarm: (farmId: number) => Promise<boolean>;
  deleteField: (fieldId: number) => Promise<boolean>;
  deleteCrop: (cropId: number) => Promise<boolean>;
  selectFarm: (farm: FarmRecord | null) => void;
  selectField: (field: FieldRecord | null) => void;
  selectCrop: (crop: CropPlanting | null) => void;
  refreshIntelligence: () => Promise<void>;
}

const FarmerProfileContext = createContext<FarmerProfileContextType | undefined>(undefined);

export const FarmerProfileProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const { location } = useLocationContext();

  const userId = user?.email || 'default_farmer';

  const [farmer, setFarmer] = useState<FarmerProfile | null>(null);
  const [dashboardData, setDashboardData] = useState<FarmDashboardResponse | null>(null);
  const [selectedFarm, setSelectedFarm] = useState<FarmRecord | null>(null);
  const [selectedField, setSelectedField] = useState<FieldRecord | null>(null);
  const [selectedCrop, setSelectedCrop] = useState<CropPlanting | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    try {
      const data = await api.getFarmerProfile(userId);
      setFarmer(data);
      if (data.farms && data.farms.length > 0) {
        setSelectedFarm((prev) => prev || data.farms[0]);
      }
    } catch (err: any) {
      console.warn('Failed to fetch farmer profile:', err);
    }
  }, [userId]);

  const fetchDashboard = useCallback(
    async (locationOverride?: { latitude: number; longitude: number; displayName?: string }) => {
      setIsRefreshing(true);
      setError(null);
      try {
        const lat = locationOverride?.latitude ?? location?.latitude;
        const lon = locationOverride?.longitude ?? location?.longitude;
        const name = locationOverride?.displayName ?? location?.displayName;

        const data = await api.getFarmerDashboard(userId, lat, lon, name);
        setDashboardData(data);
        if (data.farmer) {
          setFarmer(data.farmer);
        }
      } catch (err: any) {
        console.error('Failed to fetch farm dashboard:', err);
        setError(err.message || 'Failed to load farm command center intelligence.');
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [userId, location?.latitude, location?.longitude, location?.displayName]
  );

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const saveProfile = async (data: Partial<FarmerProfile>) => {
    setIsRefreshing(true);
    try {
      const updated = await api.updateFarmerProfile(data, userId);
      setFarmer(updated);
      await fetchDashboard();
    } catch (err: any) {
      setError(err.message || 'Failed to save farmer profile.');
      throw err;
    } finally {
      setIsRefreshing(false);
    }
  };

  const saveFarm = async (data: Partial<FarmRecord>): Promise<FarmRecord | null> => {
    setIsRefreshing(true);
    try {
      let result: FarmRecord;
      if (data.id) {
        result = await api.updateFarm(data.id, data, userId);
      } else {
        result = await api.createFarm(data, userId);
      }
      setSelectedFarm(result);
      await fetchDashboard();
      return result;
    } catch (err: any) {
      setError(err.message || 'Failed to save farm.');
      return null;
    } finally {
      setIsRefreshing(false);
    }
  };

  const saveField = async (data: Partial<FieldRecord> & { farm_id: number }): Promise<FieldRecord | null> => {
    setIsRefreshing(true);
    try {
      let result: FieldRecord;
      if (data.id) {
        result = await api.updateField(data.id, data, userId);
      } else {
        result = await api.createField(data, userId);
      }
      setSelectedField(result);
      await fetchDashboard();
      return result;
    } catch (err: any) {
      setError(err.message || 'Failed to save field.');
      return null;
    } finally {
      setIsRefreshing(false);
    }
  };

  const saveCrop = async (data: Partial<CropPlanting> & { field_id: number }): Promise<CropPlanting | null> => {
    setIsRefreshing(true);
    try {
      let result: CropPlanting;
      if (data.id) {
        result = await api.updateCrop(data.id, data, userId);
      } else {
        result = await api.createCrop(data, userId);
      }
      setSelectedCrop(result);
      await fetchDashboard();
      return result;
    } catch (err: any) {
      setError(err.message || 'Failed to save crop planting.');
      return null;
    } finally {
      setIsRefreshing(false);
    }
  };

  const deleteFarm = async (farmId: number): Promise<boolean> => {
    setIsRefreshing(true);
    try {
      await api.deleteFarm(farmId, userId);
      if (selectedFarm?.id === farmId) setSelectedFarm(null);
      await fetchDashboard();
      return true;
    } catch (err: any) {
      setError(err.message || 'Failed to delete farm.');
      return false;
    } finally {
      setIsRefreshing(false);
    }
  };

  const deleteField = async (fieldId: number): Promise<boolean> => {
    setIsRefreshing(true);
    try {
      await api.deleteField(fieldId, userId);
      if (selectedField?.id === fieldId) setSelectedField(null);
      await fetchDashboard();
      return true;
    } catch (err: any) {
      setError(err.message || 'Failed to delete field.');
      return false;
    } finally {
      setIsRefreshing(false);
    }
  };

  const deleteCrop = async (cropId: number): Promise<boolean> => {
    setIsRefreshing(true);
    try {
      await api.deleteCrop(cropId, userId);
      if (selectedCrop?.id === cropId) setSelectedCrop(null);
      await fetchDashboard();
      return true;
    } catch (err: any) {
      setError(err.message || 'Failed to delete crop planting.');
      return false;
    } finally {
      setIsRefreshing(false);
    }
  };

  const farms = farmer?.farms || [];
  const fields: FieldRecord[] = farms.flatMap((f) => f.fields || []);
  const activeCrops: CropPlanting[] = fields
    .flatMap((f) => f.plantings || [])
    .filter((cp) => cp.status === 'ACTIVE');

  return (
    <FarmerProfileContext.Provider
      value={{
        farmer,
        farms,
        fields,
        activeCrops,
        dashboardData,
        selectedFarm,
        selectedField,
        selectedCrop,
        isLoading,
        isRefreshing,
        error,
        fetchProfile,
        fetchDashboard,
        saveProfile,
        saveFarm,
        saveField,
        saveCrop,
        deleteFarm,
        deleteField,
        deleteCrop,
        selectFarm: setSelectedFarm,
        selectField: setSelectedField,
        selectCrop: setSelectedCrop,
        refreshIntelligence: () => fetchDashboard(),
      }}
    >
      {children}
    </FarmerProfileContext.Provider>
  );
};

export const useFarmerProfile = () => {
  const context = useContext(FarmerProfileContext);
  if (!context) {
    throw new Error('useFarmerProfile must be used within a FarmerProfileProvider');
  }
  return context;
};
