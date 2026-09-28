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
  fetchDashboard: (
    overrideFarmId?: number,
    overrideFieldId?: number,
    locationOverride?: { latitude: number; longitude: number; displayName?: string }
  ) => Promise<void>;
  saveProfile: (data: Partial<FarmerProfile>) => Promise<void>;
  saveFarm: (data: Partial<FarmRecord>) => Promise<FarmRecord | null>;
  saveField: (data: Partial<FieldRecord> & { farm_id: number }) => Promise<FieldRecord | null>;
  saveCrop: (data: Partial<CropPlanting> & { field_id: number }) => Promise<CropPlanting | null>;
  deleteFarm: (farmId: number) => Promise<boolean>;
  deleteField: (fieldId: number) => Promise<boolean>;
  deleteCrop: (cropId: number) => Promise<boolean>;
  completeAction: (actionId: string | number, status?: string) => Promise<boolean>;
  saveObservation: (data: any) => Promise<any>;
  saveNotificationPreferences: (prefs: any) => Promise<any>;
  selectFarm: (farm: FarmRecord | null) => void;
  selectField: (field: FieldRecord | null) => void;
  selectCrop: (crop: CropPlanting | null) => void;
  refreshIntelligence: () => Promise<void>;
}

const FarmerProfileContext = createContext<FarmerProfileContextType | undefined>(undefined);

export const FarmerProfileProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, updateProfile } = useAuth();
  const { location } = useLocationContext();

  const userId = user?.id || user?.email || 'default_farmer';

  const [farmer, setFarmer] = useState<FarmerProfile | null>(null);
  const [dashboardData, setDashboardData] = useState<FarmDashboardResponse | null>(null);

  const [selectedFarmId, setSelectedFarmId] = useState<number | null>(() => {
    try {
      const saved = localStorage.getItem('agrinexus.selected_farm_id.v1');
      return saved ? Number(saved) : null;
    } catch {
      return null;
    }
  });
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null);

  const [selectedFarm, setSelectedFarm] = useState<FarmRecord | null>(null);
  const [selectedField, setSelectedField] = useState<FieldRecord | null>(null);
  const [selectedCrop, setSelectedCrop] = useState<CropPlanting | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const requestIdRef = React.useRef<number>(0);

  const fetchProfile = useCallback(async () => {
    try {
      const data = await api.getFarmerProfile(userId);
      setFarmer(data);
      if (data && data.full_name) {
        updateProfile({ name: data.full_name });
      }
    } catch (err: any) {
      console.warn('Failed to fetch farmer profile:', err);
    }
  }, [userId, updateProfile]);

  const fetchDashboard = useCallback(
    async (
      overrideFarmId?: number,
      overrideFieldId?: number,
      locationOverride?: { latitude: number; longitude: number; displayName?: string }
    ) => {
      const currentRequestId = ++requestIdRef.current;
      setIsRefreshing(true);
      setError(null);
      try {
        const farmId = overrideFarmId ?? selectedFarmId ?? undefined;
        const fieldId = overrideFieldId ?? selectedFieldId ?? undefined;
        const lat = locationOverride?.latitude;
        const lon = locationOverride?.longitude;
        const name = locationOverride?.displayName;

        const data = await api.getFarmerDashboard(userId, farmId, fieldId, lat, lon, name);
        if (currentRequestId !== requestIdRef.current) {
          return;
        }
        setDashboardData(data);
        if (data.farmer) {
          setFarmer(data.farmer);
          if (data.farmer.full_name) {
            updateProfile({ name: data.farmer.full_name });
          }

          // Sync selected farm & field entities from dashboard response
          const returnedFarms = data.farmer.farms || [];
          if (returnedFarms.length > 0) {
            const match = returnedFarms.find((f: FarmRecord) => f.id === (data.selected_farm_id || farmId)) || returnedFarms[0];
            setSelectedFarm(match);
            setSelectedFarmId(match.id);
            try {
              localStorage.setItem('agrinexus.selected_farm_id.v1', String(match.id));
            } catch {
              // Ignore
            }

            if (match.fields && match.fields.length > 0) {
              const fieldMatch = match.fields.find((fl: FieldRecord) => fl.id === (data.selected_field_id || fieldId)) || match.fields[0];
              setSelectedField(fieldMatch);
              setSelectedFieldId(fieldMatch.id);
            } else {
              setSelectedField(null);
              setSelectedFieldId(null);
            }
          } else {
            setSelectedFarm(null);
            setSelectedFarmId(null);
            setSelectedField(null);
            setSelectedFieldId(null);
          }
        }
      } catch (err: any) {
        if (currentRequestId !== requestIdRef.current) return;
        console.error('Failed to fetch farm dashboard:', err);
        setError(err.message || 'Failed to load farm command center intelligence.');
      } finally {
        if (currentRequestId === requestIdRef.current) {
          setIsLoading(false);
          setIsRefreshing(false);
        }
      }
    },
    [userId, selectedFarmId, selectedFieldId, updateProfile]
  );

  // Clear state when user identity changes
  useEffect(() => {
    setFarmer(null);
    setDashboardData(null);
    setSelectedFarm(null);
    setSelectedField(null);
    setSelectedCrop(null);
    setIsLoading(true);
    fetchDashboard();
  }, [userId, fetchDashboard]);

  const handleSelectFarm = useCallback(
    (farm: FarmRecord | null) => {
      setSelectedFarm(farm);
      const farmId = farm ? farm.id : null;
      setSelectedFarmId(farmId);
      if (farmId) {
        try {
          localStorage.setItem('agrinexus.selected_farm_id.v1', String(farmId));
        } catch {
          // Ignore
        }
      } else {
        try {
          localStorage.removeItem('agrinexus.selected_farm_id.v1');
        } catch {
          // Ignore
        }
      }
      fetchDashboard(farmId || undefined, undefined);
    },
    [fetchDashboard]
  );

  const handleSelectField = useCallback(
    (field: FieldRecord | null) => {
      setSelectedField(field);
      const fieldId = field ? field.id : null;
      setSelectedFieldId(fieldId);
      fetchDashboard(selectedFarmId || undefined, fieldId || undefined);
    },
    [fetchDashboard, selectedFarmId]
  );


  const saveProfile = async (data: Partial<FarmerProfile>) => {
    setIsRefreshing(true);
    try {
      const updated = await api.updateFarmerProfile(data, userId);
      setFarmer(updated);
      if (updated && updated.full_name) {
        updateProfile({ name: updated.full_name });
      }
      await fetchDashboard(undefined, undefined, location ? { latitude: location.latitude, longitude: location.longitude, displayName: location.displayName } : undefined);
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
      await fetchDashboard(undefined, undefined, location ? { latitude: location.latitude, longitude: location.longitude, displayName: location.displayName } : undefined);
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
      await fetchDashboard(undefined, undefined, location ? { latitude: location.latitude, longitude: location.longitude, displayName: location.displayName } : undefined);
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
      await fetchDashboard(undefined, undefined, location ? { latitude: location.latitude, longitude: location.longitude, displayName: location.displayName } : undefined);
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
      await fetchDashboard(undefined, undefined, location ? { latitude: location.latitude, longitude: location.longitude, displayName: location.displayName } : undefined);
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
      await fetchDashboard(undefined, undefined, location ? { latitude: location.latitude, longitude: location.longitude, displayName: location.displayName } : undefined);
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
      await fetchDashboard(undefined, undefined, location ? { latitude: location.latitude, longitude: location.longitude, displayName: location.displayName } : undefined);
      return true;
    } catch (err: any) {
      setError(err.message || 'Failed to delete crop planting.');
      return false;
    } finally {
      setIsRefreshing(false);
    }
  };

  const completeAction = async (actionId: string | number, status: string = 'DONE'): Promise<boolean> => {
    try {
      await api.completeActionItem(String(actionId), status, userId);
      await fetchDashboard();
      return true;
    } catch (err: any) {
      console.error('Failed to complete action item:', err);
      return false;
    }
  };

  const saveObservation = async (data: any): Promise<any> => {
    try {
      const res = await api.createObservation(data, userId);
      await fetchDashboard();
      return res;
    } catch (err: any) {
      console.error('Failed to save plant observation:', err);
      throw err;
    }
  };

  const saveNotificationPreferences = async (prefs: any): Promise<any> => {
    try {
      const res = await api.updateNotificationPreferences(prefs, userId);
      await fetchDashboard();
      return res;
    } catch (err: any) {
      console.error('Failed to save notification preferences:', err);
      throw err;
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
        completeAction,
        saveObservation,
        saveNotificationPreferences,
        selectFarm: handleSelectFarm,
        selectField: handleSelectField,
        selectCrop: setSelectedCrop,
        refreshIntelligence: () => fetchDashboard(selectedFarmId || undefined, selectedFieldId || undefined),

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
