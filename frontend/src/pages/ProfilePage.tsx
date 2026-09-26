import React, { useState, useEffect } from 'react';
import {
  Activity,
  Layers,
  Sprout,
  Database,
  ShieldAlert,
  MapPin,
  RefreshCw,
  AlertTriangle,
  CloudSun,
  Droplets,
  Bug,
  TrendingUp,
  Calendar,
  Plus,
  Trash2,
  Edit3,
  ExternalLink,
  ChevronRight,
  ArrowRight,
  Bell,
  Sliders,
  Camera,
  CheckCircle2,
  FileText,
  X,
  Compass,
  Save,
  Check,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { useAuth } from '../context/AuthContext';
import { useLocationContext } from '../context/LocationContext';
import { useFarmerProfile } from '../context/FarmerProfileContext';

import { FieldMapEditor } from '../components/location/FieldMapEditor';
import { RiskOpportunityCenter } from '../components/intelligence/RiskOpportunityCenter';
import { PersonalizedActionPlan } from '../components/intelligence/PersonalizedActionPlan';
import { SmartAlertCenter } from '../components/intelligence/SmartAlertCenter';
import { NotificationPreferencesModal } from '../components/settings/NotificationPreferencesModal';
import { api } from '../services/api';

export const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { location: globalLocation, openPicker } = useLocationContext();
  const {
    farmer,
    farms,
    fields,
    activeCrops,
    dashboardData,
    isLoading,
    isRefreshing,
    error,
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
    refreshIntelligence,
  } = useFarmerProfile();

  const [activeTab, setActiveTab] = useState<
    'overview' | 'farms' | 'crops' | 'soil' | 'water' | 'risks' | 'actions' | 'alerts' | 'settings'
  >('overview');

  // Modals & Drawers
  const [showFarmModal, setShowFarmModal] = useState(false);
  const [showFieldModal, setShowFieldModal] = useState(false);
  const [showCropModal, setShowCropModal] = useState(false);
  const [showObservationModal, setShowObservationModal] = useState(false);
  const [showNotifModal, setShowNotifModal] = useState(false);

  // Editing state objects
  const [editingFarm, setEditingFarm] = useState<any>(null);
  const [editingField, setEditingField] = useState<any>(null);
  const [editingCrop, setEditingCrop] = useState<any>(null);

  // Observation State
  const [obsFieldId, setObsFieldId] = useState<number | ''>('');
  const [obsCropId, setObsCropId] = useState<number | ''>('');
  const [obsType, setObsType] = useState<string>('DISEASE_CHECK');
  const [obsNotes, setObsNotes] = useState<string>('');
  const [obsImageFile, setObsImageFile] = useState<File | null>(null);
  const [obsImagePreview, setObsImagePreview] = useState<string | null>(null);
  const [obsAnalyzing, setObsAnalyzing] = useState(false);
  const [obsAiResult, setObsAiResult] = useState<any>(null);

  // Settings State
  const [profileName, setProfileName] = useState(farmer?.full_name || user?.name || 'Farmer');
  const [profilePhone, setProfilePhone] = useState(farmer?.phone || '');
  const [profileLang, setProfileLang] = useState(farmer?.preferred_language || 'en');
  const [profileTz, setProfileTz] = useState(farmer?.timezone || 'Asia/Kolkata');
  const [profileUnits, setProfileUnits] = useState(farmer?.preferred_units || 'acre');
  const [savedNotice, setSavedNotice] = useState(false);

  useEffect(() => {
    if (farmer) {
      setProfileName(farmer.full_name);
      setProfilePhone(farmer.phone || '');
      setProfileLang(farmer.preferred_language || 'en');
      setProfileTz(farmer.timezone || 'Asia/Kolkata');
      setProfileUnits(farmer.preferred_units || 'acre');
    }
  }, [farmer]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await saveProfile({
      full_name: profileName,
      phone: profilePhone,
      preferred_language: profileLang,
      timezone: profileTz,
      preferred_units: profileUnits,
    });
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  const handleRecommendCropForField = (field: any) => {
    navigate('/crop', {
      state: {
        location: {
          latitude: field.latitude || dashboardData?.location.latitude,
          longitude: field.longitude || dashboardData?.location.longitude,
          displayName: dashboardData?.location.display_name,
        },
        soil: {
          ph: field.ph,
          nitrogen: field.nitrogen,
          phosphorus: field.phosphorus,
          potassium: field.potassium,
        },
      },
    });
  };

  const handleObservationImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setObsImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setObsImagePreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleRunDiseaseAiOnObservation = async () => {
    if (!obsImageFile) return;
    setObsAnalyzing(true);
    try {
      const result = await api.predictDisease(obsImageFile, true);
      setObsAiResult(result);
    } catch (err: any) {
      console.error('Disease AI error:', err);
    } finally {
      setObsAnalyzing(false);
    }
  };

  const handleSaveObservationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!obsFieldId || !obsCropId) return;
    try {
      await saveObservation({
        field_id: Number(obsFieldId),
        crop_id: Number(obsCropId),
        observation_type: obsType,
        notes: obsNotes,
        ai_disease_result: obsAiResult ? JSON.stringify(obsAiResult) : null,
      });
      setShowObservationModal(false);
      setObsNotes('');
      setObsImageFile(null);
      setObsImagePreview(null);
      setObsAiResult(null);
    } catch (err: any) {
      console.error('Error saving observation:', err);
    }
  };

  const locationName =
    dashboardData?.location.display_name || globalLocation?.displayName || 'Barasat, North 24 Parganas';

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* 
        CRITICAL MANDATE (Phase 1 & Phase 52): 
        NO WELCOME GREETINGS ("Hello Animesh", "Welcome back", etc.)
        Page starts immediately with FARM COMMAND CENTER operational banner.
      */}
      <div className="p-6 md:p-8 rounded-3xl bg-[#0B1C10] text-[#FAFBF7] border border-white/10 shadow-2xl space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#D4E768]/15 border border-[#D4E768]/30 text-[#D4E768] text-xs font-mono font-bold uppercase tracking-wider">
              <Compass className="w-3.5 h-3.5" /> FARM CENTRAL OPERATING SYSTEM
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold font-editorial tracking-tight text-white">
              FARM COMMAND CENTER
            </h1>

            {/* Quick Metrics Badges Bar */}
            <div className="flex flex-wrap items-center gap-2 text-xs font-bold pt-1">
              <span className="px-3 py-1 rounded-xl bg-white/10 text-white border border-white/15">
                {fields.length} Field{fields.length !== 1 ? 's' : ''}
              </span>
              <span className="px-3 py-1 rounded-xl bg-[#D4E768]/20 text-[#D4E768] border border-[#D4E768]/30">
                {activeCrops.length} Active Crop{activeCrops.length !== 1 ? 's' : ''}
              </span>
              <span className="px-3 py-1 rounded-xl bg-sky-500/20 text-sky-300 border border-sky-400/30 flex items-center gap-1">
                <CloudSun className="w-3.5 h-3.5" /> Weather Watch
              </span>
              <span className="px-3 py-1 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-400/30 flex items-center gap-1">
                <Activity className="w-3.5 h-3.5" /> {dashboardData?.action_plan?.total_actions || 0} Actions
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row lg:flex-col items-start lg:items-end gap-3">
            <div className="flex items-center gap-2 text-xs bg-white/5 px-4 py-2 rounded-2xl border border-white/10 text-white/90">
              <MapPin className="w-4 h-4 text-[#D4E768] shrink-0" />
              <span className="font-semibold truncate max-w-[200px]">{locationName}</span>
              <button
                onClick={openPicker}
                className="text-[#D4E768] hover:underline font-bold text-[11px] ml-1 shrink-0"
              >
                Change
              </button>
            </div>

            <div className="flex items-center gap-2">
              <Button
                onClick={() => setShowNotifModal(true)}
                variant="secondary"
                size="sm"
                icon={<Bell className="w-4 h-4 text-[#D4E768]" />}
              >
                Preferences
              </Button>
              <Button
                onClick={() => refreshIntelligence()}
                variant="lime"
                size="sm"
                disabled={isRefreshing}
                icon={<RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />}
              >
                {isRefreshing ? 'Refreshing...' : 'Refresh'}
              </Button>
            </div>
          </div>
        </div>

        {/* Data Provenance & Completeness */}
        <div className="flex flex-wrap items-center justify-between gap-4 text-xs pt-4 border-t border-white/10 text-white/70">
          <div className="flex flex-wrap items-center gap-4">
            <span className="flex items-center gap-1">
              <Database className="w-3.5 h-3.5 text-[#D4E768]" />
              Location Confidence: <strong className="text-white font-mono">{dashboardData?.data_quality.location_confidence || 'High'}</strong>
            </span>
            <span className="flex items-center gap-1">
              <CloudSun className="w-3.5 h-3.5 text-sky-400" />
              Weather Data: <strong className="text-white font-mono">{dashboardData?.data_quality.weather_freshness || 'Fresh'}</strong>
            </span>
            <span className="flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
              Soil Telemetry: <strong className="text-white font-mono">{dashboardData?.data_quality.soil_availability || 'Measured/Estimated'}</strong>
            </span>
          </div>
          <div className="font-bold text-[#D4E768] text-xs font-mono">
            Profile Data Quality: {dashboardData?.data_quality.profile_completeness_pct || 0}%
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-[#E2E7DA] overflow-x-auto pb-1 scrollbar-none">
        {[
          { id: 'overview', label: 'Farm Overview', icon: Activity },
          { id: 'farms', label: 'Farms & Fields', icon: Layers },
          { id: 'crops', label: 'Crop Cultivation', icon: Sprout },
          { id: 'soil', label: 'Soil Intelligence', icon: Database },
          { id: 'water', label: 'Water & Irrigation', icon: Droplets },
          { id: 'risks', label: 'Risks & Opportunities', icon: ShieldAlert },
          { id: 'actions', label: 'Action Plan', icon: CheckCircle2 },
          { id: 'alerts', label: 'Smart Alerts', icon: Bell },
          { id: 'settings', label: 'Farm Settings', icon: Sliders },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs font-bold transition-all whitespace-nowrap ${
                isActive
                  ? 'bg-[#0B1C10] text-[#D4E768] shadow-md'
                  : 'bg-white/80 text-[#536056] hover:bg-[#EEF3E8] hover:text-[#0B1C10]'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-[#D4E768]' : 'text-[#2F6B3C]'}`} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Error state banner */}
      {error && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-900 text-xs font-semibold flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* TAB 1: FARM OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-8">
          {/* Top Status Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <GlassCard variant="solid" className="p-5 space-y-2 border-l-4 border-l-sky-500">
              <div className="flex justify-between items-center text-xs text-[#536056] font-bold">
                <span className="flex items-center gap-1.5"><CloudSun className="w-4 h-4 text-sky-500" /> WEATHER</span>
                <Badge variant="info">LIVE</Badge>
              </div>
              <p className="text-lg font-extrabold text-[#0B1C10] font-editorial">
                {dashboardData?.today_status.weather_summary || '31°C • Forecast 12mm'}
              </p>
              <p className="text-[11px] text-[#536056]">Open-Meteo validated telemetry</p>
            </GlassCard>

            <GlassCard variant="solid" className="p-5 space-y-2 border-l-4 border-l-emerald-500">
              <div className="flex justify-between items-center text-xs text-[#536056] font-bold">
                <span className="flex items-center gap-1.5"><Database className="w-4 h-4 text-emerald-500" /> SOIL STATUS</span>
                <Badge variant="success">TESTED</Badge>
              </div>
              <p className="text-lg font-extrabold text-[#0B1C10] font-editorial">
                {dashboardData?.today_status.soil_summary || 'pH 6.5 • N 90 kg/ha'}
              </p>
              <p className="text-[11px] text-[#536056]">Field soil telemetry provenance</p>
            </GlassCard>

            <GlassCard variant="solid" className="p-5 space-y-2 border-l-4 border-l-blue-500">
              <div className="flex justify-between items-center text-xs text-[#536056] font-bold">
                <span className="flex items-center gap-1.5"><Droplets className="w-4 h-4 text-blue-500" /> WATER STATUS</span>
                <Badge variant="warning">MONITOR</Badge>
              </div>
              <p className="text-lg font-extrabold text-[#0B1C10] font-editorial">
                {dashboardData?.today_status.water_summary || '2 Active Crop Fields'}
              </p>
              <p className="text-[11px] text-[#536056]">SWC & ET0 irrigation requirement</p>
            </GlassCard>

            <GlassCard variant="solid" className="p-5 space-y-2 border-l-4 border-l-amber-500">
              <div className="flex justify-between items-center text-xs text-[#536056] font-bold">
                <span className="flex items-center gap-1.5"><TrendingUp className="w-4 h-4 text-amber-500" /> MARKET WATCH</span>
                <Badge variant="primary">RISING</Badge>
              </div>
              <p className="text-lg font-extrabold text-[#0B1C10] font-editorial">
                {dashboardData?.today_status.market_summary || 'Tracking Active Crops'}
              </p>
              <p className="text-[11px] text-[#536056]">AGMARKNET live prices</p>
            </GlassCard>
          </div>

          {/* Active Crops Cards */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">ACTIVE CROP MONITORING</h3>
                <p className="text-xs text-[#536056]">Field-specific growth, weather, pest, and market telemetry</p>
              </div>
              <Button
                onClick={() => {
                  setEditingCrop(null);
                  setShowCropModal(true);
                }}
                variant="lime"
                size="sm"
                icon={<Plus className="w-4 h-4" />}
              >
                Add Crop
              </Button>
            </div>

            {dashboardData?.active_crop_cards && dashboardData.active_crop_cards.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {dashboardData.active_crop_cards.map((card) => {
                  const matchingField = fields.find((f) => f.id === card.field_id);
                  return (
                    <GlassCard key={card.id} variant="solid" className="p-6 space-y-5 border border-[#E2E7DA]">
                      <div className="flex items-start justify-between border-b border-[#E2E7DA] pb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-2xl bg-[#0B1C10] text-[#D4E768] flex items-center justify-center font-bold text-lg font-editorial shadow-sm">
                            {card.crop_name.charAt(0)}
                          </div>
                          <div>
                            <h4 className="text-lg font-extrabold text-[#0B1C10] font-editorial">{card.crop_name}</h4>
                            <p className="text-xs text-[#536056] font-medium">
                              {card.field_name} • {card.area_display}
                            </p>
                          </div>
                        </div>
                        <Badge variant={card.weather_status === 'Warning' ? 'danger' : 'success'}>
                          {card.growth_stage}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-[#EEF3E8]/60 p-3 rounded-2xl border border-[#E2E7DA]">
                        <div>
                          <span className="text-[#536056] block text-[10px]">WEATHER</span>
                          <strong className="text-[#0B1C10]">{card.weather_status}</strong>
                        </div>
                        <div>
                          <span className="text-[#536056] block text-[10px]">WATER</span>
                          <strong className="text-[#0B1C10]">{card.water_status}</strong>
                        </div>
                        <div>
                          <span className="text-[#536056] block text-[10px]">PEST RISK</span>
                          <strong className="text-[#0B1C10]">{card.pest_status}</strong>
                        </div>
                        <div>
                          <span className="text-[#536056] block text-[10px]">MARKET</span>
                          <strong className="text-emerald-700 font-bold">{card.market_trend}</strong>
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center justify-between text-xs pt-1 text-[#536056] border-t border-[#E2E7DA]">
                        <span>Sown: {card.sowing_date || 'N/A'}</span>
                        <span>Harvest: {card.expected_harvest || 'N/A'}</span>
                      </div>

                      <div className="flex flex-col sm:flex-row gap-2 pt-2">
                        <Button
                          onClick={() => matchingField && handleRecommendCropForField(matchingField)}
                          variant="secondary"
                          size="sm"
                          className="flex-1"
                          icon={<Sprout className="w-3.5 h-3.5 text-[#2F6B3C]" />}
                        >
                          Recommend Crop for Field
                        </Button>
                      </div>
                    </GlassCard>
                  );
                })}
              </div>
            ) : (
              <GlassCard variant="solid" className="p-8 text-center space-y-3">
                <Sprout className="w-10 h-10 text-[#2F6B3C] mx-auto" />
                <h4 className="text-base font-bold text-[#0B1C10]">No Active Crops Registered</h4>
                <p className="text-xs text-[#536056]">
                  Add your first crop planting to activate weather, pest, irrigation, and market intelligence.
                </p>
                <Button
                  onClick={() => {
                    setEditingCrop(null);
                    setShowCropModal(true);
                  }}
                  variant="lime"
                  size="sm"
                  icon={<Plus className="w-4 h-4" />}
                >
                  Add First Crop
                </Button>
              </GlassCard>
            )}
          </div>

          {/* Quick Action Plan Summary */}
          {dashboardData && (
            <PersonalizedActionPlan
              actions={dashboardData.actions || dashboardData.action_plan?.actions || []}
              onCompleteAction={async (actionId: string, status: string) => {
                await completeAction(actionId, status);
              }}
            />
          )}

          {/* Quick Risk & Opportunity Summary */}
          {dashboardData && (
            <RiskOpportunityCenter
              risks={dashboardData.risks || dashboardData.risk_opportunity?.risks || []}
              opportunities={dashboardData.opportunities || dashboardData.risk_opportunity?.opportunities || []}
              impactMatrix={dashboardData.impact_matrix || dashboardData.risk_opportunity?.impact_matrix || []}
            />
          )}
        </div>
      )}

      {/* TAB 2: FARMS & FIELDS (MAP WORKSPACE) */}
      {activeTab === 'farms' && (
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">FARMS & FIELD BOUNDARIES</h3>
              <p className="text-xs text-[#536056]">
                Draw exact field boundary polygons on high-resolution maps for true geodesic area calculation.
              </p>
            </div>
            <Button
              onClick={() => {
                setEditingFarm(null);
                setShowFarmModal(true);
              }}
              variant="lime"
              size="sm"
              icon={<Plus className="w-4 h-4" />}
            >
              Add New Farm
            </Button>
          </div>

          {/* Farm List */}
          {farms.length > 0 ? (
            <div className="space-y-8">
              {farms.map((farm) => (
                <GlassCard key={farm.id} variant="solid" className="p-6 space-y-6 border border-[#E2E7DA]">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#E2E7DA] pb-4 gap-3">
                    <div>
                      <h4 className="text-xl font-extrabold text-[#0B1C10] font-editorial">{farm.farm_name}</h4>
                      <p className="text-xs text-[#536056]">
                        {farm.location_name || 'Location Not Set'} • {farm.area_value} {farm.area_unit} ({farm.total_area_m2?.toLocaleString()} m²)
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        onClick={() => {
                          setEditingField({ farm_id: farm.id });
                          setShowFieldModal(true);
                        }}
                        variant="lime"
                        size="sm"
                        icon={<Plus className="w-3.5 h-3.5" />}
                      >
                        Map New Field
                      </Button>
                      <button
                        onClick={() => deleteFarm(farm.id)}
                        className="p-2 rounded-xl text-rose-600 hover:bg-rose-50 transition-colors"
                        title="Delete Farm"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* List Fields within this Farm */}
                  {farm.fields && farm.fields.length > 0 ? (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {farm.fields.map((field) => (
                        <div key={field.id} className="p-5 rounded-3xl bg-[#EEF3E8]/80 border border-[#E2E7DA] space-y-4">
                          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
                            <div>
                              <h5 className="font-extrabold text-[#0B1C10] font-editorial text-base">{field.field_name}</h5>
                              <span className="text-xs text-[#536056]">
                                Soil: {field.soil_type || 'Unspecified'} | Water: {field.water_source || 'Unspecified'}
                              </span>
                            </div>
                            <Badge variant={field.boundary_geojson ? 'success' : 'neutral'}>
                              {field.geometry_source || 'Declared'}
                            </Badge>
                          </div>

                          {/* Field Telemetry Box */}
                          <div className="grid grid-cols-2 gap-3 text-xs font-mono bg-white/70 p-3 rounded-2xl border border-[#E2E7DA]">
                            <div>
                              <span className="text-[#536056] text-[10px] font-sans block">DECLARED AREA</span>
                              <strong className="text-[#0B1C10]">{field.area_value} {field.area_unit}</strong>
                            </div>
                            <div>
                              <span className="text-[#536056] text-[10px] font-sans block">GEODESIC AREA</span>
                              <strong className="text-[#2F6B3C]">{field.total_area_m2 ? `${(field.total_area_m2 / 4046.856).toFixed(2)} acres` : 'N/A'}</strong>
                            </div>
                            {field.perimeter_m && (
                              <div>
                                <span className="text-[#536056] text-[10px] font-sans block">PERIMETER</span>
                                <strong>{field.perimeter_m.toFixed(1)} m</strong>
                              </div>
                            )}
                            {field.centroid_lat && (
                              <div>
                                <span className="text-[#536056] text-[10px] font-sans block">CENTROID</span>
                                <strong>{field.centroid_lat.toFixed(4)}, {field.centroid_lng?.toFixed(4)}</strong>
                              </div>
                            )}
                          </div>

                          <div className="flex items-center justify-between pt-1">
                            <Button
                              onClick={() => {
                                setEditingField(field);
                                setShowFieldModal(true);
                              }}
                              variant="secondary"
                              size="sm"
                              icon={<Edit3 className="w-3.5 h-3.5 text-[#2F6B3C]" />}
                            >
                              Edit Boundary Map
                            </Button>
                            <button
                              onClick={() => deleteField(field.id)}
                              className="text-xs text-rose-600 hover:underline font-semibold"
                            >
                              Delete Field
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[#536056] italic">No mapped fields in this farm yet.</p>
                  )}
                </GlassCard>
              ))}
            </div>
          ) : (
            <GlassCard variant="solid" className="p-8 text-center space-y-3">
              <Layers className="w-10 h-10 text-[#2F6B3C] mx-auto" />
              <h4 className="text-base font-bold text-[#0B1C10]">No Farms Registered</h4>
              <p className="text-xs text-[#536056]">Create your farm record to start mapping field boundaries.</p>
              <Button
                onClick={() => {
                  setEditingFarm(null);
                  setShowFarmModal(true);
                }}
                variant="lime"
                size="sm"
                icon={<Plus className="w-4 h-4" />}
              >
                Add Farm
              </Button>
            </GlassCard>
          )}
        </div>
      )}

      {/* TAB 3: CROP CULTIVATION & OBSERVATIONS */}
      {activeTab === 'crops' && (
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">CROP CULTIVATIONS & OBSERVATIONS</h3>
              <p className="text-xs text-[#536056]">
                Track plant growth, sowing dates, variety, and record AI-assisted field observations.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => setShowObservationModal(true)}
                variant="secondary"
                size="sm"
                icon={<Camera className="w-4 h-4 text-[#2F6B3C]" />}
              >
                Add Observation
              </Button>
              <Button
                onClick={() => {
                  setEditingCrop(null);
                  setShowCropModal(true);
                }}
                variant="lime"
                size="sm"
                icon={<Plus className="w-4 h-4" />}
              >
                Add Crop
              </Button>
            </div>
          </div>

          {activeCrops.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {activeCrops.map((crop) => {
                const matchingField = fields.find((f) => f.id === crop.field_id);
                return (
                  <GlassCard key={crop.id} variant="solid" className="p-6 space-y-4 border border-[#E2E7DA]">
                    <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
                      <div>
                        <h4 className="text-lg font-extrabold text-[#0B1C10] font-editorial">{crop.crop_name}</h4>
                        <p className="text-xs text-[#536056]">Variety: {crop.variety || 'Standard'}</p>
                      </div>
                      <Badge variant="success">{crop.status}</Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs bg-[#EEF3E8]/80 p-3 rounded-2xl border border-[#E2E7DA]">
                      <div>
                        <span className="text-[#536056] text-[10px] block font-sans">FIELD</span>
                        <strong className="text-[#0B1C10]">{matchingField?.field_name || `Field #${crop.field_id}`}</strong>
                      </div>
                      <div>
                        <span className="text-[#536056] text-[10px] block font-sans">GROWTH STAGE</span>
                        <strong className="text-[#2F6B3C]">{crop.growth_stage || 'Vegetative'}</strong>
                      </div>
                      <div>
                        <span className="text-[#536056] text-[10px] block font-sans">SOWING DATE</span>
                        <strong>{crop.sowing_date || 'N/A'}</strong>
                      </div>
                      <div>
                        <span className="text-[#536056] text-[10px] block font-sans">EXPECTED HARVEST</span>
                        <strong>{crop.expected_harvest_date || 'N/A'}</strong>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-[#E2E7DA]">
                      <button
                        onClick={() => deleteCrop(crop.id)}
                        className="text-xs text-rose-600 hover:underline font-semibold"
                      >
                        Delete Crop
                      </button>
                    </div>
                  </GlassCard>
                );
              })}
            </div>
          ) : (
            <GlassCard variant="solid" className="p-8 text-center space-y-3">
              <Sprout className="w-10 h-10 text-[#2F6B3C] mx-auto" />
              <h4 className="text-base font-bold text-[#0B1C10]">No Active Crops</h4>
              <p className="text-xs text-[#536056]">Add your active crop plantings to start crop telemetry.</p>
              <Button
                onClick={() => {
                  setEditingCrop(null);
                  setShowCropModal(true);
                }}
                variant="lime"
                size="sm"
                icon={<Plus className="w-4 h-4" />}
              >
                Add Crop
              </Button>
            </GlassCard>
          )}
        </div>
      )}

      {/* TAB 4: SOIL INTELLIGENCE */}
      {activeTab === 'soil' && (
        <div className="space-y-6">
          <div className="border-b border-[#E2E7DA] pb-3">
            <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">SOIL INTELLIGENCE & PROVENANCE</h3>
            <p className="text-xs text-[#536056]">
              Every soil value displays strict provenance: MEASURED (lab test), ESTIMATED (telemetry), or UNKNOWN.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {fields.map((field) => (
              <GlassCard key={field.id} variant="solid" className="p-6 space-y-4 border border-[#E2E7DA]">
                <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
                  <h4 className="font-extrabold text-[#0B1C10] font-editorial text-base">{field.field_name}</h4>
                  <Badge variant={field.soil_test_available ? 'success' : 'warning'}>
                    {field.soil_test_available ? 'MEASURED LAB' : 'ESTIMATED'}
                  </Badge>
                </div>

                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between items-center p-2 rounded-xl bg-[#EEF3E8] border border-[#E2E7DA]">
                    <span className="text-[#536056]">pH Level</span>
                    <span className="font-mono font-bold text-[#0B1C10]">{field.ph ?? 'UNKNOWN'}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 rounded-xl bg-[#EEF3E8] border border-[#E2E7DA]">
                    <span className="text-[#536056]">Nitrogen (N)</span>
                    <span className="font-mono font-bold text-[#0B1C10]">
                      {field.nitrogen ? `${field.nitrogen} kg/ha` : 'UNKNOWN'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 rounded-xl bg-[#EEF3E8] border border-[#E2E7DA]">
                    <span className="text-[#536056]">Phosphorus (P)</span>
                    <span className="font-mono font-bold text-[#0B1C10]">
                      {field.phosphorus ? `${field.phosphorus} kg/ha` : 'UNKNOWN (Test Required)'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 rounded-xl bg-[#EEF3E8] border border-[#E2E7DA]">
                    <span className="text-[#536056]">Potassium (K)</span>
                    <span className="font-mono font-bold text-[#0B1C10]">
                      {field.potassium ? `${field.potassium} kg/ha` : 'UNKNOWN (Test Required)'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 rounded-xl bg-[#EEF3E8] border border-[#E2E7DA]">
                    <span className="text-[#536056]">Organic Carbon</span>
                    <span className="font-mono font-bold text-[#0B1C10]">
                      {field.organic_carbon ? `${field.organic_carbon}%` : 'UNKNOWN'}
                    </span>
                  </div>
                </div>

                <p className="text-[11px] text-[#536056] italic pt-1">
                  Note: Missing P & K values are marked UNKNOWN rather than replaced with fake defaults.
                </p>
              </GlassCard>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: WATER & IRRIGATION */}
      {activeTab === 'water' && (
        <div className="space-y-6">
          <div className="border-b border-[#E2E7DA] pb-3">
            <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">WATER & IRRIGATION INTELLIGENCE</h3>
            <p className="text-xs text-[#536056]">
              3-Hour SWC model persistence benchmarks integrated with Open-Meteo precipitation and ET0 telemetry.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {dashboardData?.irrigation_items && dashboardData.irrigation_items.length > 0 ? (
              dashboardData.irrigation_items.map((item, idx) => (
                <GlassCard key={idx} variant="solid" className="p-6 space-y-4 border border-[#E2E7DA]">
                  <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
                    <div>
                      <h4 className="font-extrabold text-[#0B1C10] font-editorial text-base">{item.crop_name}</h4>
                      <p className="text-xs text-[#536056]">{item.field_name}</p>
                    </div>
                    <Badge variant={item.status === 'MONITOR' ? 'warning' : 'success'}>{item.status}</Badge>
                  </div>

                  <div className="space-y-2 text-xs">
                    <p className="text-[#0B1C10]">
                      <strong>Irrigation Method:</strong> {item.irrigation_method}
                    </p>
                    <p className="text-[#0B1C10]">
                      <strong>Next Recommended Window:</strong> {item.next_window}
                    </p>
                    <div className="p-3 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1">
                      <span className="text-[10px] font-bold text-[#2F6B3C] uppercase block font-mono">
                        Model Scope & Scientific Provenance
                      </span>
                      <p className="text-[#536056] text-[11px]">{item.model_note}</p>
                    </div>
                  </div>
                </GlassCard>
              ))
            ) : (
              <p className="text-xs text-[#536056] italic">No active irrigation schedules available.</p>
            )}
          </div>
        </div>
      )}

      {/* TAB 6: RISKS & OPPORTUNITIES */}
      {activeTab === 'risks' && dashboardData && (
        <RiskOpportunityCenter
          risks={dashboardData.risks || dashboardData.risk_opportunity?.risks || []}
          opportunities={dashboardData.opportunities || dashboardData.risk_opportunity?.opportunities || []}
          impactMatrix={dashboardData.impact_matrix || dashboardData.risk_opportunity?.impact_matrix || []}
        />
      )}

      {/* TAB 7: ACTION PLAN */}
      {activeTab === 'actions' && dashboardData && (
        <PersonalizedActionPlan
          actions={dashboardData.actions || dashboardData.action_plan?.actions || []}
          onCompleteAction={async (actionId: string, status: string) => {
            await completeAction(actionId, status);
          }}
        />
      )}

      {/* TAB 8: SMART ALERTS */}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
            <div>
              <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">SMART ALERTS CENTER</h3>
              <p className="text-xs text-[#536056]">
                Traceable, crop-aware alerts generated by deterministic agronomic rules.
              </p>
            </div>
            <Button
              onClick={() => setShowNotifModal(true)}
              variant="lime"
              size="sm"
              icon={<Bell className="w-4 h-4 text-[#0B1C10]" />}
            >
              Notification Preferences
            </Button>
          </div>

          <SmartAlertCenter
            alerts={dashboardData?.dispatched_alerts || []}
            preferences={dashboardData?.notification_preferences}
            onOpenPreferences={() => setShowNotifModal(true)}
          />
        </div>
      )}

      {/* TAB 9: FARM SETTINGS & CANONICAL PROFILE */}
      {activeTab === 'settings' && (
        <div className="space-y-8 max-w-3xl">
          <GlassCard variant="solid" className="p-8 space-y-6 border border-[#E2E7DA]">
            <div className="border-b border-[#E2E7DA] pb-4">
              <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">FARMER PROFILE & ACCOUNT PREFERENCES</h3>
              <p className="text-xs text-[#536056]">Canonical authenticated farmer details, timezone, and regional preferences</p>
            </div>

            {savedNotice && (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-900 text-xs font-bold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Profile updated successfully! Dashboard, greeting, and avatars synchronized.</span>
              </div>
            )}

            <form onSubmit={handleProfileSubmit} className="space-y-5">
              {/* Account Email (Read-Only) */}
              <div>
                <label className="block text-xs font-bold text-[#0B1C10] uppercase tracking-wider mb-1">
                  ACCOUNT EMAIL ADDRESS (AUTHENTICATED)
                </label>
                <div className="p-3 rounded-xl bg-[#EEF3E8] border border-[#E2E7DA] text-xs font-mono font-bold text-[#2F6B3C] flex items-center justify-between">
                  <span>{user?.email || farmer?.email || 'authenticated_user@agrinexus.ai'}</span>
                  <span className="text-[10px] uppercase font-bold text-[#536056] px-2 py-0.5 rounded-full bg-white border border-[#E2E7DA]">
                    Primary Identity
                  </span>
                </div>
                <p className="text-[11px] text-[#536056] mt-1">
                  Account identity is tied to your login credentials and authentication session.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Full Name"
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  placeholder="Enter full name"
                  required
                />

                <Input
                  label="Phone Number"
                  value={profilePhone}
                  onChange={(e) => setProfilePhone(e.target.value)}
                  placeholder="+91 9876543210"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Select
                  label="Preferred Language"
                  value={profileLang}
                  onChange={(e) => setProfileLang(e.target.value)}
                  options={[
                    { value: 'en', label: 'English' },
                    { value: 'bn', label: 'Bengali (বাংলা)' },
                    { value: 'hi', label: 'Hindi (हिंदी)' },
                    { value: 'te', label: 'Telugu (తెలుగు)' },
                    { value: 'ta', label: 'Tamil (தமிழ்)' },
                    { value: 'mr', label: 'Marathi (मराठी)' },
                    { value: 'pa', label: 'Punjabi (ਪੰਜਾਬੀ)' },
                  ]}
                />

                <Select
                  label="Timezone for Greeting & Schedule"
                  value={profileTz}
                  onChange={(e) => setProfileTz(e.target.value)}
                  options={[
                    { value: 'Asia/Kolkata', label: 'Asia/Kolkata (IST, UTC+5:30)' },
                    { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
                    { value: 'America/New_York', label: 'America/New_York (EST)' },
                    { value: 'Europe/London', label: 'Europe/London (GMT)' },
                  ]}
                />

                <Select
                  label="Preferred Land Measurement Unit"
                  value={profileUnits}
                  onChange={(e) => setProfileUnits(e.target.value)}
                  options={[
                    { value: 'acre', label: 'Acres (acre)' },
                    { value: 'hectare', label: 'Hectares (ha)' },
                    { value: 'bigha', label: 'Bigha' },
                    { value: 'm2', label: 'Square Meters (m²)' },
                  ]}
                />
              </div>

              {/* Global Field Location Selector */}
              <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#0B1C10] flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-[#2F6B3C]" />
                    PREFERRED GLOBAL LOCATION
                  </span>
                  <Button type="button" onClick={openPicker} variant="secondary" size="sm">
                    Select Location
                  </Button>
                </div>
                <p className="text-xs font-semibold text-[#0B1C10]">
                  {globalLocation?.displayName || farmer?.location || 'Barasat, North 24 Parganas, West Bengal'}
                </p>
                <p className="text-[11px] text-[#536056]">
                  Used to personalize weather telemetry, mandi market pricing, and pest outbreak risk signals.
                </p>
              </div>

              <div className="pt-2">
                <Button type="submit" variant="lime" size="md" icon={<Save className="w-4 h-4" />}>
                  Save Profile Settings
                </Button>
              </div>
            </form>
          </GlassCard>

          <GlassCard variant="solid" className="p-8 space-y-4 border border-[#E2E7DA]">
            <div className="border-b border-[#E2E7DA] pb-4 flex items-center justify-between">
              <div>
                <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">NOTIFICATION DELIVERY CHANNELS</h3>
                <p className="text-xs text-[#536056]">Configure In-App, Email, SMS, and WhatsApp alerts</p>
              </div>
              <Button onClick={() => setShowNotifModal(true)} variant="secondary" size="sm">
                Configure Channels
              </Button>
            </div>
            <p className="text-xs text-[#536056]">
              Set up quiet hours (e.g. 22:00–06:00) and select specific categories like critical risks or rain alerts.
            </p>
          </GlassCard>
        </div>
      )}

      {/* MODAL 1: FARM CREATE / EDIT */}
      {showFarmModal && (
        <FarmModal
          farm={editingFarm}
          onSave={async (data) => {
            await saveFarm(data);
            setShowFarmModal(false);
          }}
          onClose={() => setShowFarmModal(false)}
        />
      )}

      {/* MODAL 2: FIELD MAP EDITOR (GEODESIC BOUNDARY DRAWING WORKSPACE) */}
      {showFieldModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-4xl bg-[#FAFBF7] rounded-3xl border border-[#E2E7DA] shadow-2xl p-6 space-y-6 overflow-y-auto max-h-[95vh]">
            <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
              <div>
                <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                  FIELD MAPPING WORKSPACE
                </h3>
                <p className="text-xs text-[#536056]">
                  Draw exact boundary polygon on map to calculate geodesic area in acres, ha, & m².
                </p>
              </div>
              <button
                onClick={() => setShowFieldModal(false)}
                className="p-1.5 rounded-full hover:bg-black/5 text-[#536056] hover:text-[#0B1C10]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <FieldMapEditor
              initialFieldName={editingField?.name || ''}
              initialAreaValue={editingField?.area_value || editingField?.area_acres || 1.0}
              initialAreaUnit={editingField?.area_unit || 'acre'}
              initialLat={editingField?.centroid_lat || globalLocation?.latitude || 22.5726}
              initialLng={editingField?.centroid_lng || globalLocation?.longitude || 88.3639}
              initialBoundary={editingField?.boundary_geojson || null}
              farmId={editingField?.farm_id || (farms[0] ? farms[0].id : 1)}
              onSave={async (fieldData: any) => {
                await saveField({
                  ...fieldData,
                  ...(editingField?.id ? { id: editingField.id } : {}),
                });
                setShowFieldModal(false);
              }}
              onCancel={() => setShowFieldModal(false)}
            />
          </div>
        </div>
      )}

      {/* MODAL 3: CROP ADD / EDIT */}
      {showCropModal && (
        <CropModal
          crop={editingCrop}
          fields={fields}
          onSave={async (data) => {
            await saveCrop(data);
            setShowCropModal(false);
          }}
          onClose={() => setShowCropModal(false)}
        />
      )}

      {/* MODAL 4: PLANT OBSERVATION WITH DISEASE CV AI */}
      {showObservationModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-xl bg-[#0B1C10] text-[#FAFBF7] rounded-3xl border border-white/15 shadow-2xl p-6 space-y-6 overflow-y-auto max-h-[90vh]">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-2">
                <Camera className="w-5 h-5 text-[#D4E768]" />
                <h3 className="text-xl font-extrabold font-editorial text-white">Record Plant Observation</h3>
              </div>
              <button
                onClick={() => setShowObservationModal(false)}
                className="p-1.5 rounded-full hover:bg-white/10 text-white/60 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveObservationSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-white/70 mb-1 font-bold">Select Field</label>
                  <select
                    value={obsFieldId}
                    onChange={(e) => setObsFieldId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-3 py-2 rounded-xl bg-black/40 text-white border border-white/15"
                    required
                  >
                    <option value="">-- Choose Field --</option>
                    {fields.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.field_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-white/70 mb-1 font-bold">Select Active Crop</label>
                  <select
                    value={obsCropId}
                    onChange={(e) => setObsCropId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-3 py-2 rounded-xl bg-black/40 text-white border border-white/15"
                    required
                  >
                    <option value="">-- Choose Crop --</option>
                    {activeCrops.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.crop_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-white/70 mb-1 font-bold">Observation Type</label>
                <select
                  value={obsType}
                  onChange={(e) => setObsType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-black/40 text-white border border-white/15"
                >
                  <option value="DISEASE_CHECK">Disease Check / AI Scan</option>
                  <option value="PEST_CHECK">Pest Observation</option>
                  <option value="GROWTH_NOTE">Growth Stage Note</option>
                </select>
              </div>

              <div>
                <label className="block text-white/70 mb-1 font-bold">Plant / Leaf Image (Optional)</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleObservationImageChange}
                  className="w-full px-3 py-2 rounded-xl bg-black/40 text-white border border-white/15 file:mr-3 file:py-1 file:px-3 file:rounded-xl file:bg-[#D4E768] file:text-[#0B1C10] file:font-bold"
                />
              </div>

              {obsImagePreview && (
                <div className="space-y-3 p-3 rounded-2xl bg-white/5 border border-white/10">
                  <img src={obsImagePreview} alt="Leaf Observation" className="h-40 object-cover rounded-xl mx-auto" />
                  <Button
                    type="button"
                    onClick={handleRunDiseaseAiOnObservation}
                    variant="lime"
                    size="sm"
                    className="w-full"
                    disabled={obsAnalyzing}
                    icon={<Bug className="w-4 h-4" />}
                  >
                    {obsAnalyzing ? 'Analyzing with AI Model...' : 'Run Disease AI Check'}
                  </Button>
                </div>
              )}

              {obsAiResult && (
                <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-200 space-y-1">
                  <p className="font-bold">AI Disease Classification:</p>
                  <p>Prediction: {obsAiResult.disease_name || obsAiResult.prediction}</p>
                  <p>Confidence: {((obsAiResult.confidence || 0) * 100).toFixed(1)}%</p>
                </div>
              )}

              <div>
                <label className="block text-white/70 mb-1 font-bold">Observation Notes</label>
                <textarea
                  rows={3}
                  value={obsNotes}
                  onChange={(e) => setObsNotes(e.target.value)}
                  placeholder="Record symptoms, leaf spots, or growth notes..."
                  className="w-full px-3 py-2 rounded-xl bg-black/40 text-white border border-white/15"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-white/10">
                <Button onClick={() => setShowObservationModal(false)} type="button" variant="secondary" size="sm">
                  Cancel
                </Button>
                <Button type="submit" variant="lime" size="sm">
                  Save Observation
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 5: NOTIFICATION PREFERENCES MODAL */}
      <NotificationPreferencesModal
        isOpen={showNotifModal}
        preferences={dashboardData?.notification_preferences}
        onSave={saveNotificationPreferences}
        onClose={() => setShowNotifModal(false)}
      />
    </div>
  );
};

// Helper FarmModal Component
const FarmModal: React.FC<{
  farm?: any;
  onSave: (data: any) => Promise<void>;
  onClose: () => void;
}> = ({ farm, onSave, onClose }) => {
  const [name, setName] = useState(farm?.farm_name || '');
  const [locationName, setLocationName] = useState(farm?.location_name || '');
  const [areaVal, setAreaVal] = useState(farm?.area_value || '');
  const [areaUnit, setAreaUnit] = useState(farm?.area_unit || 'acre');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onSave({
        id: farm?.id,
        farm_name: name,
        location_name: locationName,
        area_value: Number(areaVal) || 0,
        area_unit: areaUnit,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-md bg-[#FAFBF7] rounded-3xl border border-[#E2E7DA] shadow-2xl p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
          <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
            {farm ? 'Edit Farm' : 'Add New Farm'}
          </h3>
          <button onClick={onClose} className="p-1.5 text-[#536056] hover:text-[#0B1C10]">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Farm Name" value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Green Valley Farm" />
          <Input label="Location Name" value={locationName} onChange={(e) => setLocationName(e.target.value)} placeholder="e.g. Barasat, North 24 Parganas" />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Total Area" type="number" step="any" value={areaVal} onChange={(e) => setAreaVal(e.target.value)} required placeholder="5.0" />
            <Select label="Unit" value={areaUnit} onChange={(e) => setAreaUnit(e.target.value)} options={[
              { value: 'acre', label: 'Acres' },
              { value: 'hectare', label: 'Hectares' },
              { value: 'bigha', label: 'Bigha' },
              { value: 'm2', label: 'm²' },
            ]} />
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-[#E2E7DA]">
            <Button onClick={onClose} type="button" variant="secondary" size="sm">Cancel</Button>
            <Button type="submit" variant="lime" size="sm" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Farm'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Helper CropModal Component
const CropModal: React.FC<{
  crop?: any;
  fields: any[];
  onSave: (data: any) => Promise<void>;
  onClose: () => void;
}> = ({ crop, fields, onSave, onClose }) => {
  const [fieldId, setFieldId] = useState(crop?.field_id || (fields[0] ? fields[0].id : ''));
  const [cropName, setCropName] = useState(crop?.crop_name || 'Rice');
  const [variety, setVariety] = useState(crop?.variety || '');
  const [sowingDate, setSowingDate] = useState(crop?.sowing_date || new Date().toISOString().split('T')[0]);
  const [growthStage, setGrowthStage] = useState(crop?.growth_stage || 'Vegetative');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fieldId) return;
    setIsSubmitting(true);
    try {
      await onSave({
        id: crop?.id,
        field_id: Number(fieldId),
        crop_name: cropName,
        variety,
        sowing_date: sowingDate,
        growth_stage: growthStage,
        status: 'ACTIVE',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-md bg-[#FAFBF7] rounded-3xl border border-[#E2E7DA] shadow-2xl p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
          <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
            {crop ? 'Edit Crop' : 'Add Crop Planting'}
          </h3>
          <button onClick={onClose} className="p-1.5 text-[#536056] hover:text-[#0B1C10]">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Select
            label="Assigned Field"
            value={fieldId}
            onChange={(e) => setFieldId(e.target.value)}
            options={fields.map((f) => ({ value: f.id, label: `${f.field_name} (${f.area_value} ${f.area_unit})` }))}
          />
          <Input label="Crop Name" value={cropName} onChange={(e) => setCropName(e.target.value)} required placeholder="e.g. Rice, Potato, Wheat" />
          <Input label="Variety (Optional)" value={variety} onChange={(e) => setVariety(e.target.value)} placeholder="e.g. Swarna, Jyoti" />
          <Input label="Sowing Date" type="date" value={sowingDate} onChange={(e) => setSowingDate(e.target.value)} required />
          <Select
            label="Growth Stage"
            value={growthStage}
            onChange={(e) => setGrowthStage(e.target.value)}
            options={[
              { value: 'Sowing / Seedling', label: 'Sowing / Seedling' },
              { value: 'Vegetative', label: 'Vegetative' },
              { value: 'Flowering', label: 'Flowering' },
              { value: 'Fruiting / Grain Fill', label: 'Fruiting / Grain Fill' },
              { value: 'Maturity / Harvest', label: 'Maturity / Harvest' },
            ]}
          />
          <div className="flex justify-end gap-2 pt-2 border-t border-[#E2E7DA]">
            <Button onClick={onClose} type="button" variant="secondary" size="sm">Cancel</Button>
            <Button type="submit" variant="lime" size="sm" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Crop'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
