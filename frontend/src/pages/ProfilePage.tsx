import React, { useState } from 'react';
import {
  User,
  MapPin,
  Save,
  CheckCircle2,
  RefreshCw,
  AlertTriangle,
  CloudSun,
  Droplets,
  Sprout,
  Bug,
  TrendingUp,
  Calendar,
  Layers,
  Activity,
  Plus,
  Trash2,
  Edit3,
  ExternalLink,
  ShieldAlert,
  Info,
  ChevronRight,
  Database,
  ArrowRight,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { useAuth } from '../context/AuthContext';
import { useLocationContext } from '../context/LocationContext';
import { useFarmerProfile } from '../context/FarmerProfileContext';
import { LocationMapPreview } from '../components/location/LocationMapPreview';

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
    refreshIntelligence,
  } = useFarmerProfile();

  const [activeTab, setActiveTab] = useState<'overview' | 'farms' | 'crops' | 'soil' | 'settings'>('overview');

  // Modal / Form States
  const [editingFarm, setEditingFarm] = useState<any>(null);
  const [editingField, setEditingField] = useState<any>(null);
  const [editingCrop, setEditingCrop] = useState<any>(null);

  const [showFarmModal, setShowFarmModal] = useState(false);
  const [showFieldModal, setShowFieldModal] = useState(false);
  const [showCropModal, setShowCropModal] = useState(false);

  const [profileName, setProfileName] = useState(farmer?.full_name || user?.name || 'Farmer');
  const [profilePhone, setProfilePhone] = useState(farmer?.phone || '');
  const [profileLang, setProfileLang] = useState(farmer?.preferred_language || 'en');
  const [savedNotice, setSavedNotice] = useState(false);

  // Sync profile form when loaded
  React.useEffect(() => {
    if (farmer) {
      setProfileName(farmer.full_name);
      setProfilePhone(farmer.phone || '');
      setProfileLang(farmer.preferred_language || 'en');
    }
  }, [farmer]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await saveProfile({
      full_name: profileName,
      phone: profilePhone,
      preferred_language: profileLang,
    });
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  const handleRecommendCropForField = (field: any) => {
    // Navigate to Smart Crop recommendation pre-filling field coordinates & soil
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

  const farmerName = farmer?.full_name || user?.name || 'Farmer';
  const locationName = dashboardData?.location.display_name || globalLocation?.displayName || 'North 24 Parganas, West Bengal';

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero & Command Center Title */}
      <AgriculturalPageHero
        category="FARM COMMAND CENTER"
        title={`Welcome, ${farmerName}`}
        description="Persistent personalized agronomic decision-support platform integrating live weather, soil telemetry, irrigation schedules, pest watch, and active crop market intelligence."
        imageSrc="/images/crop-calendar.webp"
      />

      {/* Top Header Summary Bar */}
      <div className="p-6 rounded-3xl bg-[#0B1C10] text-[#FAFBF7] border border-white/10 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-[#D4E768]" />
              <span className="text-sm font-semibold text-white/90">{locationName}</span>
              <button
                onClick={openPicker}
                className="text-xs text-[#D4E768] hover:underline font-bold ml-1"
              >
                (Change Location)
              </button>
            </div>
            <p className="text-xs text-white/60">
              {dashboardData?.total_farm_area || 0} {dashboardData?.total_farm_area_unit || 'acres'} • {fields.length} Field(s) • {activeCrops.length} Active Crop(s)
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              onClick={() => refreshIntelligence()}
              variant="lime"
              size="sm"
              disabled={isRefreshing}
              icon={<RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />}
            >
              {isRefreshing ? 'Refreshing...' : 'Refresh Intelligence'}
            </Button>
          </div>
        </div>

        {/* Data Quality & Provenance Indicator */}
        <div className="flex flex-wrap items-center gap-4 text-xs pt-3 border-t border-white/10 text-white/70">
          <span className="flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-[#D4E768]" />
            Location: <strong className="text-white font-mono">{dashboardData?.data_quality.location_confidence || 'High'}</strong>
          </span>
          <span className="flex items-center gap-1">
            <CloudSun className="w-3.5 h-3.5 text-sky-400" />
            Weather: <strong className="text-white font-mono">{dashboardData?.data_quality.weather_freshness || 'Fresh'}</strong>
          </span>
          <span className="flex items-center gap-1">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            Soil: <strong className="text-white font-mono">{dashboardData?.data_quality.soil_availability || 'Partial'}</strong>
          </span>
          <span className="flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
            Market: <strong className="text-white font-mono">{dashboardData?.data_quality.market_status || 'Active'}</strong>
          </span>
          <span className="ml-auto font-bold text-[#D4E768]">
            Profile Completeness: {dashboardData?.data_quality.profile_completeness_pct || 0}%
          </span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-[#E2E7DA] overflow-x-auto pb-1 scrollbar-none">
        {[
          { id: 'overview', label: 'Farm Command Center', icon: Activity },
          { id: 'farms', label: 'Farms & Fields', icon: Layers },
          { id: 'crops', label: 'Crop Cultivation', icon: Sprout },
          { id: 'soil', label: 'Soil Lab Data', icon: Database },
          { id: 'settings', label: 'Settings', icon: User },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-5 py-3 rounded-2xl text-xs font-bold transition-all whitespace-nowrap ${
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

      {/* Error state alert */}
      {error && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-900 text-xs font-semibold flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* TAB 1: FARM COMMAND CENTER OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-8">
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-28 rounded-3xl" />
              ))}
            </div>
          ) : (
            <>
              {/* TODAY'S FARM STATUS - Compact Editorial Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <GlassCard variant="solid" className="p-5 space-y-2 border-l-4 border-l-sky-500">
                  <div className="flex justify-between items-center text-xs text-[#536056] font-bold">
                    <span className="flex items-center gap-1.5"><CloudSun className="w-4 h-4 text-sky-500" /> WEATHER</span>
                    <Badge variant="blue">LIVE</Badge>
                  </div>
                  <p className="text-lg font-extrabold text-[#0B1C10] font-editorial">
                    {dashboardData?.today_status.weather_summary || '31°C • Rain 12mm'}
                  </p>
                  <p className="text-[11px] text-[#536056]">Open-Meteo telemetry</p>
                </GlassCard>

                <GlassCard variant="solid" className="p-5 space-y-2 border-l-4 border-l-emerald-500">
                  <div className="flex justify-between items-center text-xs text-[#536056] font-bold">
                    <span className="flex items-center gap-1.5"><Database className="w-4 h-4 text-emerald-500" /> SOIL STATUS</span>
                    <Badge variant="green">TESTED</Badge>
                  </div>
                  <p className="text-lg font-extrabold text-[#0B1C10] font-editorial">
                    {dashboardData?.today_status.soil_summary || 'pH 6.5 • N 90 kg/ha'}
                  </p>
                  <p className="text-[11px] text-[#536056]">Field soil telemetry</p>
                </GlassCard>

                <GlassCard variant="solid" className="p-5 space-y-2 border-l-4 border-l-blue-500">
                  <div className="flex justify-between items-center text-xs text-[#536056] font-bold">
                    <span className="flex items-center gap-1.5"><Droplets className="w-4 h-4 text-blue-500" /> WATER STATUS</span>
                    <Badge variant="yellow">MONITOR</Badge>
                  </div>
                  <p className="text-lg font-extrabold text-[#0B1C10] font-editorial">
                    {dashboardData?.today_status.water_summary || '2 Active Crop Field(s)'}
                  </p>
                  <p className="text-[11px] text-[#536056]">Irrigation schedule</p>
                </GlassCard>

                <GlassCard variant="solid" className="p-5 space-y-2 border-l-4 border-l-amber-500">
                  <div className="flex justify-between items-center text-xs text-[#536056] font-bold">
                    <span className="flex items-center gap-1.5"><TrendingUp className="w-4 h-4 text-amber-500" /> MARKET WATCH</span>
                    <Badge variant="lime">RISING</Badge>
                  </div>
                  <p className="text-lg font-extrabold text-[#0B1C10] font-editorial">
                    {dashboardData?.today_status.market_summary || 'Tracking Active Crops'}
                  </p>
                  <p className="text-[11px] text-[#536056]">AGMARKNET live prices</p>
                </GlassCard>
              </div>

              {/* YOUR ACTIVE CROPS CARDS */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">YOUR ACTIVE CROPS</h3>
                    <p className="text-xs text-[#536056]">Field-specific growth, weather, pest, and market intelligence</p>
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
                            <Badge variant={card.weather_status === 'Warning' ? 'red' : 'green'}>
                              {card.growth_stage}
                            </Badge>
                          </div>

                          {/* Quick Crop Metrics Grid */}
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

                          {/* Crop Actions */}
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
                      Add your first crop planting to activate personalized weather, pest, irrigation, and market intelligence.
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

              {/* FARM WEATHER IMPACT & FIELD CONDITIONS */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Weather Impact per Crop */}
                <GlassCard variant="solid" className="p-6 space-y-4">
                  <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-3">
                    <CloudSun className="w-5 h-5 text-[#2F6B3C]" />
                    <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">FARM WEATHER IMPACT</h3>
                  </div>

                  {dashboardData?.weather_impacts && dashboardData.weather_impacts.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.weather_impacts.map((item, idx) => (
                        <div key={idx} className="p-4 rounded-2xl bg-[#EEF3E8]/80 border border-[#E2E7DA] space-y-2 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="font-extrabold text-[#0B1C10] font-editorial text-sm">
                              {item.crop_name} ({item.field_name})
                            </span>
                            <Badge variant={item.status === 'Warning' ? 'red' : 'green'}>{item.status}</Badge>
                          </div>
                          <div className="space-y-1">
                            <p className="text-[#0B1C10] font-medium">
                              <strong>Weather Fact:</strong> {item.temperature ? `${item.temperature}°C` : 'N/A'}, Rain Forecast: {item.rain_forecast_mm} mm
                            </p>
                            <p className="text-[#2F6B3C]">
                              <strong>Interpretation:</strong> {item.impact}
                            </p>
                            <p className="text-[#536056]">
                              <strong>Recommended Action:</strong> {item.action}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[#536056] italic">No weather impact data available.</p>
                  )}
                </GlassCard>

                {/* Soil Intelligence */}
                <GlassCard variant="solid" className="p-6 space-y-4">
                  <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-3">
                    <Database className="w-5 h-5 text-[#2F6B3C]" />
                    <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">FARM SOIL INTELLIGENCE</h3>
                  </div>

                  {dashboardData?.soil_impacts && dashboardData.soil_impacts.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.soil_impacts.map((item, idx) => (
                        <div key={idx} className="p-4 rounded-2xl bg-[#EEF3E8]/80 border border-[#E2E7DA] space-y-3 text-xs">
                          <div className="flex items-center justify-between font-editorial font-extrabold text-sm text-[#0B1C10]">
                            <span>{item.crop_name} ({item.field_name})</span>
                            <span className="text-xs font-sans font-normal text-[#536056]">{item.texture_status}</span>
                          </div>

                          <div className="grid grid-cols-4 gap-2 text-center bg-white/70 p-2 rounded-xl border border-[#E2E7DA] font-mono">
                            <div>
                              <span className="text-[10px] text-[#536056] block font-sans">pH</span>
                              <strong className="text-[#0B1C10] text-[11px]">{item.ph_status}</strong>
                            </div>
                            <div>
                              <span className="text-[10px] text-[#536056] block font-sans">N</span>
                              <strong className="text-[#0B1C10] text-[11px]">{item.n_status}</strong>
                            </div>
                            <div>
                              <span className="text-[10px] text-[#536056] block font-sans">P</span>
                              <strong className="text-[#0B1C10] text-[11px]">{item.p_status}</strong>
                            </div>
                            <div>
                              <span className="text-[10px] text-[#536056] block font-sans">K</span>
                              <strong className="text-[#0B1C10] text-[11px]">{item.k_status}</strong>
                            </div>
                          </div>

                          <p className="text-[#536056] italic">{item.impact_text}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[#536056] italic">No soil intelligence records available.</p>
                  )}
                </GlassCard>
              </div>

              {/* IRRIGATION & FERTILIZER CENTER */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Irrigation Center */}
                <GlassCard variant="solid" className="p-6 space-y-4">
                  <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-3">
                    <Droplets className="w-5 h-5 text-[#2F6B3C]" />
                    <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">IRRIGATION CENTER</h3>
                  </div>

                  {dashboardData?.irrigation_items && dashboardData.irrigation_items.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.irrigation_items.map((item, idx) => (
                        <div key={idx} className="p-4 rounded-2xl bg-[#EEF3E8]/80 border border-[#E2E7DA] space-y-2 text-xs">
                          <div className="flex items-center justify-between font-bold text-[#0B1C10]">
                            <span>{item.crop_name} • {item.field_name}</span>
                            <Badge variant={item.status === 'MONITOR' ? 'yellow' : 'green'}>{item.status}</Badge>
                          </div>
                          <p className="text-[#536056]">
                            <strong>Method:</strong> {item.irrigation_method} | <strong>Window:</strong> {item.next_window}
                          </p>
                          <p className="text-[11px] text-[#536056] bg-white/60 p-2 rounded-xl border border-[#E2E7DA]">
                            ℹ️ <em>{item.model_note}</em>
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[#536056] italic">No irrigation records available.</p>
                  )}
                </GlassCard>

                {/* Fertilizer Plan */}
                <GlassCard variant="solid" className="p-6 space-y-4">
                  <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-3">
                    <Sprout className="w-5 h-5 text-[#2F6B3C]" />
                    <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">FERTILIZER INTELLIGENCE</h3>
                  </div>

                  {dashboardData?.fertilizer_items && dashboardData.fertilizer_items.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.fertilizer_items.map((item, idx) => (
                        <div key={idx} className="p-4 rounded-2xl bg-[#EEF3E8]/80 border border-[#E2E7DA] space-y-2 text-xs">
                          <div className="flex items-center justify-between font-bold text-[#0B1C10]">
                            <span>{item.crop_name} ({item.field_name})</span>
                            <Badge variant={item.model_available ? 'green' : 'gray'}>
                              {item.model_available ? 'ML Available' : 'Regional Context'}
                            </Badge>
                          </div>
                          {item.recommendation && (
                            <p className="font-extrabold text-[#2F6B3C] font-mono text-xs">{item.recommendation}</p>
                          )}
                          <p className="text-[#536056]">{item.reason}</p>
                          <p className="text-[11px] text-[#536056] bg-white/60 p-2 rounded-xl border border-[#E2E7DA]">
                            ⚠️ <em>{item.model_scope_note}</em>
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[#536056] italic">No fertilizer records available.</p>
                  )}
                </GlassCard>
              </div>

              {/* PEST WATCH & MARKET WATCH */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Pest & Disease Watch */}
                <GlassCard variant="solid" className="p-6 space-y-4">
                  <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-3">
                    <Bug className="w-5 h-5 text-[#2F6B3C]" />
                    <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">PEST & DISEASE WATCH</h3>
                  </div>

                  {dashboardData?.pest_items && dashboardData.pest_items.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.pest_items.map((item, idx) => (
                        <div key={idx} className="p-4 rounded-2xl bg-[#EEF3E8]/80 border border-[#E2E7DA] space-y-2 text-xs">
                          <div className="flex items-center justify-between font-bold text-[#0B1C10]">
                            <span>{item.crop_name} • {item.field_name}</span>
                            <Badge variant={item.risk_level === 'High' ? 'red' : item.risk_level === 'Moderate' ? 'yellow' : 'green'}>
                              Risk: {item.risk_level}
                            </Badge>
                          </div>
                          {item.weather_drivers.length > 0 && (
                            <p className="text-[#536056]">
                              <strong>Weather Drivers:</strong> {item.weather_drivers.join(', ')}
                            </p>
                          )}
                          <p className="text-[#0B1C10]">
                            <strong>Action:</strong> {item.action}
                          </p>
                          <p className="text-[11px] text-[#536056] bg-white/60 p-2 rounded-xl border border-[#E2E7DA]">
                            💡 <em>{item.model_scope_note}</em>
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[#536056] italic">No pest watch records available.</p>
                  )}
                </GlassCard>

                {/* Market Watch for Active Crops */}
                <GlassCard variant="solid" className="p-6 space-y-4">
                  <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-3">
                    <TrendingUp className="w-5 h-5 text-[#2F6B3C]" />
                    <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">ACTIVE CROPS MARKET WATCH</h3>
                  </div>

                  {dashboardData?.market_watch && dashboardData.market_watch.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.market_watch.map((item, idx) => (
                        <div key={idx} className="p-4 rounded-2xl bg-[#EEF3E8]/80 border border-[#E2E7DA] space-y-2 text-xs">
                          <div className="flex items-center justify-between font-bold text-[#0B1C10]">
                            <span className="font-editorial text-sm">{item.crop_name}</span>
                            <Badge variant="lime">{item.trend}</Badge>
                          </div>
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-[#536056]">Market Price:</span>
                            <span className="font-extrabold text-[#0B1C10] font-mono text-sm">
                              {item.current_price ? `₹${item.current_price} / quintal` : 'AGMARKNET Syncing...'}
                            </span>
                          </div>
                          <div className="flex justify-between items-center text-[11px] text-[#536056]">
                            <span>30-Day Trend: {item.change_30d_pct ? `+${item.change_30d_pct}%` : 'Stable'}</span>
                            <span>Location: {item.market_location}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[#536056] italic">No market data available for active crops.</p>
                  )}
                </GlassCard>
              </div>

              {/* FARM TIMELINE & ALERTS */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Farm Timeline */}
                <GlassCard variant="solid" className="p-6 space-y-4">
                  <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-3">
                    <Calendar className="w-5 h-5 text-[#2F6B3C]" />
                    <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">FARM TIMELINE</h3>
                  </div>

                  {dashboardData?.timeline && dashboardData.timeline.length > 0 ? (
                    <div className="space-y-3 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#E2E7DA]">
                      {dashboardData.timeline.map((item, idx) => (
                        <div key={idx} className="pl-8 relative space-y-1 text-xs">
                          <div className="absolute left-1.5 top-1 w-3 h-3 rounded-full bg-[#2F6B3C] border-2 border-white" />
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-[#0B1C10]">{item.event_title}</span>
                            <span className="text-[11px] font-mono text-[#536056]">{item.date_label}</span>
                          </div>
                          <p className="text-[#536056]">
                            {item.crop_name} ({item.field_name}) • Reason: {item.reason}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[#536056] italic">No timeline events recorded.</p>
                  )}
                </GlassCard>

                {/* Farm Alerts */}
                <GlassCard variant="solid" className="p-6 space-y-4">
                  <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-3">
                    <ShieldAlert className="w-5 h-5 text-amber-600" />
                    <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">FARM ALERTS CENTER</h3>
                  </div>

                  {dashboardData?.alerts && dashboardData.alerts.length > 0 ? (
                    <div className="space-y-3">
                      {dashboardData.alerts.map((alert) => (
                        <div key={alert.id} className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs space-y-1">
                          <div className="flex items-center justify-between font-bold text-amber-950">
                            <span>{alert.title}</span>
                            <Badge variant={alert.priority === 'High' ? 'red' : 'yellow'}>{alert.priority}</Badge>
                          </div>
                          <p className="text-amber-900/90">{alert.description}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] text-xs text-[#2F6B3C] font-semibold text-center">
                      ✓ No active critical alerts. Your farm operations are running smoothly!
                    </div>
                  )}
                </GlassCard>
              </div>

              {/* CROP IMPACT MATRIX */}
              <GlassCard variant="solid" className="p-6 space-y-4 overflow-x-auto">
                <div className="border-b border-[#E2E7DA] pb-3">
                  <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">CROP IMPACT MATRIX</h3>
                  <p className="text-xs text-[#536056]">Integrated multi-dimensional decision-support prioritization</p>
                </div>

                {dashboardData?.impact_matrix && dashboardData.impact_matrix.length > 0 ? (
                  <table className="w-full text-left text-xs font-sans border-collapse">
                    <thead>
                      <tr className="border-b border-[#E2E7DA] text-[#536056] font-bold uppercase text-[10px]">
                        <th className="py-2.5 px-3">Crop</th>
                        <th className="py-2.5 px-3">Field</th>
                        <th className="py-2.5 px-3">Area</th>
                        <th className="py-2.5 px-3">Weather</th>
                        <th className="py-2.5 px-3">Soil</th>
                        <th className="py-2.5 px-3">Water</th>
                        <th className="py-2.5 px-3">Pest</th>
                        <th className="py-2.5 px-3">Market</th>
                        <th className="py-2.5 px-3">Attention</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E2E7DA]">
                      {dashboardData.impact_matrix.map((row, idx) => (
                        <tr key={idx} className="hover:bg-[#EEF3E8]/50 transition-colors font-medium">
                          <td className="py-3 px-3 font-extrabold text-[#0B1C10]">{row.crop_name}</td>
                          <td className="py-3 px-3 text-[#536056]">{row.field_name}</td>
                          <td className="py-3 px-3 font-mono">{row.area_display}</td>
                          <td className="py-3 px-3">{row.weather}</td>
                          <td className="py-3 px-3">{row.soil}</td>
                          <td className="py-3 px-3">{row.water}</td>
                          <td className="py-3 px-3">{row.pest}</td>
                          <td className="py-3 px-3 text-emerald-700 font-bold">{row.market}</td>
                          <td className="py-3 px-3">
                            <Badge variant={row.attention_level === 'High' ? 'red' : row.attention_level === 'Medium' ? 'yellow' : 'green'}>
                              {row.attention_level}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-xs text-[#536056] italic">No active crops registered for impact matrix.</p>
                )}
              </GlassCard>
            </>
          )}
        </div>
      )}

      {/* TAB 2: FARMS & FIELDS */}
      {activeTab === 'farms' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">FARM & FIELD MANAGEMENT</h3>
              <p className="text-xs text-[#536056]">Manage your farm boundaries, multi-field areas, and locations</p>
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

          {farms.length > 0 ? (
            <div className="space-y-6">
              {farms.map((farm) => (
                <GlassCard key={farm.id} variant="solid" className="p-6 space-y-6 border border-[#E2E7DA]">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#E2E7DA] pb-4 gap-3">
                    <div>
                      <h4 className="text-lg font-extrabold text-[#0B1C10] font-editorial">{farm.farm_name}</h4>
                      <p className="text-xs text-[#536056]">
                        {farm.location_name || 'Location Not Set'} • {farm.area_value} {farm.area_unit} ({farm.total_area_m2.toLocaleString()} m²)
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        onClick={() => {
                          setEditingField({ farm_id: farm.id });
                          setShowFieldModal(true);
                        }}
                        variant="secondary"
                        size="sm"
                        icon={<Plus className="w-3.5 h-3.5" />}
                      >
                        Add Field
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
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {farm.fields.map((field) => (
                        <div key={field.id} className="p-4 rounded-2xl bg-[#EEF3E8]/70 border border-[#E2E7DA] space-y-3">
                          <div className="flex items-center justify-between">
                            <h5 className="font-extrabold text-[#0B1C10] font-editorial text-sm">{field.field_name}</h5>
                            <span className="text-xs font-mono font-bold text-[#2F6B3C]">
                              {field.area_value} {field.area_unit}
                            </span>
                          </div>

                          <div className="text-xs text-[#536056] space-y-1">
                            <p>Soil Type: {field.soil_type || 'Manual'}</p>
                            <p>Soil Test: {field.soil_test_available ? '✓ Lab Measured' : '✕ Test Recommended'}</p>
                          </div>

                          <div className="flex items-center justify-between pt-2 border-t border-[#E2E7DA]">
                            <button
                              onClick={() => handleRecommendCropForField(field)}
                              className="text-xs text-[#2F6B3C] font-bold hover:underline flex items-center gap-1"
                            >
                              Recommend Crop <ArrowRight className="w-3 h-3" />
                            </button>

                            <button
                              onClick={() => deleteField(field.id)}
                              className="text-xs text-rose-600 hover:underline font-semibold"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[#536056] italic">No fields created for this farm yet.</p>
                  )}
                </GlassCard>
              ))}
            </div>
          ) : (
            <GlassCard variant="solid" className="p-8 text-center space-y-3">
              <Layers className="w-10 h-10 text-[#2F6B3C] mx-auto" />
              <h4 className="text-base font-bold text-[#0B1C10]">No Farms Registered</h4>
              <p className="text-xs text-[#536056]">Add your farm details to start organizing your fields and crops.</p>
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

      {/* TAB 3: CROP CULTIVATION */}
      {activeTab === 'crops' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">CROP CULTIVATIONS</h3>
              <p className="text-xs text-[#536056]">Track sowing dates, varieties, and growth stages per field</p>
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

          {activeCrops.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {activeCrops.map((crop) => (
                <GlassCard key={crop.id} variant="solid" className="p-6 space-y-4 border border-[#E2E7DA]">
                  <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
                    <div>
                      <h4 className="text-lg font-extrabold text-[#0B1C10] font-editorial">{crop.crop_name}</h4>
                      <p className="text-xs text-[#536056]">{crop.variety ? `Variety: ${crop.variety}` : 'Standard Variety'}</p>
                    </div>
                    <button
                      onClick={() => deleteCrop(crop.id)}
                      className="p-1.5 rounded-xl text-rose-600 hover:bg-rose-50 transition-colors"
                      title="Delete Crop"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[#536056] block">Growth Stage:</span>
                      <strong className="text-[#0B1C10]">{crop.growth_stage}</strong>
                    </div>
                    <div>
                      <span className="text-[#536056] block">Status:</span>
                      <strong className="text-[#2F6B3C]">{crop.status}</strong>
                    </div>
                    <div>
                      <span className="text-[#536056] block">Sowing Date:</span>
                      <strong className="text-[#0B1C10]">{crop.sowing_date || 'N/A'}</strong>
                    </div>
                    <div>
                      <span className="text-[#536056] block">Expected Harvest:</span>
                      <strong className="text-[#0B1C10]">{crop.expected_harvest_date || 'N/A'}</strong>
                    </div>
                  </div>
                </GlassCard>
              ))}
            </div>
          ) : (
            <GlassCard variant="solid" className="p-8 text-center space-y-3">
              <Sprout className="w-10 h-10 text-[#2F6B3C] mx-auto" />
              <h4 className="text-base font-bold text-[#0B1C10]">No Active Crops</h4>
              <p className="text-xs text-[#536056]">Add active crops to get crop-specific weather, pest, and market intelligence.</p>
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

      {/* TAB 4: SOIL LAB DATA */}
      {activeTab === 'soil' && (
        <div className="space-y-6">
          <div className="border-b border-[#E2E7DA] pb-3">
            <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">SOIL TEST LAB DATA</h3>
            <p className="text-xs text-[#536056]">Enter lab measurements with provenance (MEASURED / ESTIMATED / UNKNOWN)</p>
          </div>

          {fields.length > 0 ? (
            <div className="space-y-6">
              {fields.map((field) => (
                <GlassCard key={field.id} variant="solid" className="p-6 space-y-4 border border-[#E2E7DA]">
                  <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
                    <h4 className="text-lg font-extrabold font-editorial text-[#0B1C10]">{field.field_name} Soil Profile</h4>
                    <Badge variant={field.soil_test_available ? 'green' : 'gray'}>
                      {field.soil_test_available ? 'Lab Test Available' : 'No Lab Test'}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                    <div className="p-3 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1">
                      <span className="text-[#536056] block font-bold">pH</span>
                      <p className="text-base font-extrabold font-mono text-[#0B1C10]">{field.ph ?? '—'}</p>
                      <span className="text-[10px] text-[#2F6B3C] font-semibold">{field.ph_provenance}</span>
                    </div>

                    <div className="p-3 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1">
                      <span className="text-[#536056] block font-bold">Nitrogen (N)</span>
                      <p className="text-base font-extrabold font-mono text-[#0B1C10]">{field.nitrogen ? `${field.nitrogen} kg/ha` : '—'}</p>
                      <span className="text-[10px] text-[#2F6B3C] font-semibold">{field.nitrogen_provenance}</span>
                    </div>

                    <div className="p-3 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1">
                      <span className="text-[#536056] block font-bold">Phosphorus (P)</span>
                      <p className="text-base font-extrabold font-mono text-[#0B1C10]">{field.phosphorus ? `${field.phosphorus} kg/ha` : '—'}</p>
                      <span className="text-[10px] text-[#2F6B3C] font-semibold">{field.phosphorus_provenance}</span>
                    </div>

                    <div className="p-3 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1">
                      <span className="text-[#536056] block font-bold">Potassium (K)</span>
                      <p className="text-base font-extrabold font-mono text-[#0B1C10]">{field.potassium ? `${field.potassium} kg/ha` : '—'}</p>
                      <span className="text-[10px] text-[#2F6B3C] font-semibold">{field.potassium_provenance}</span>
                    </div>
                  </div>
                </GlassCard>
              ))}
            </div>
          ) : (
            <GlassCard variant="solid" className="p-8 text-center space-y-3">
              <Database className="w-10 h-10 text-[#2F6B3C] mx-auto" />
              <h4 className="text-base font-bold text-[#0B1C10]">No Fields Found</h4>
              <p className="text-xs text-[#536056]">Add fields first to input soil lab measurements.</p>
            </GlassCard>
          )}
        </div>
      )}

      {/* TAB 5: SETTINGS */}
      {activeTab === 'settings' && (
        <div className="max-w-2xl space-y-6">
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
            <div className="border-b border-[#E2E7DA] pb-4">
              <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">
                Farmer Identity & Preferences
              </h3>
            </div>

            <form onSubmit={handleProfileSubmit} className="space-y-5">
              <Input
                label="Full Name"
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                icon={<User className="w-4 h-4 text-[#2F6B3C]" />}
                required
              />

              <Input
                label="Phone Number"
                value={profilePhone}
                onChange={(e) => setProfilePhone(e.target.value)}
              />

              <Select
                label="Preferred Language"
                value={profileLang}
                onChange={(e) => setProfileLang(e.target.value)}
                options={[
                  { value: 'en', label: 'English' },
                  { value: 'bn', label: 'Bengali (বাংলা)' },
                  { value: 'hi', label: 'Hindi (हिंदी)' },
                  { value: 'mr', label: 'Marathi (मराठी)' },
                ]}
              />

              <Button
                type="submit"
                variant="lime"
                size="lg"
                className="w-full mt-2"
                icon={<Save className="w-4 h-4" />}
              >
                Save Preferences
              </Button>

              {savedNotice && (
                <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] text-[#2F6B3C] text-xs font-bold flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#2F6B3C]" />
                  <span>Profile updated successfully!</span>
                </div>
              )}
            </form>
          </GlassCard>
        </div>
      )}

      {/* CREATE / EDIT FARM MODAL */}
      {showFarmModal && (
        <FarmFormModal
          farm={editingFarm}
          onClose={() => setShowFarmModal(false)}
          onSave={async (data) => {
            await saveFarm(data);
            setShowFarmModal(false);
          }}
          defaultLat={globalLocation?.latitude || 22.5726}
          defaultLon={globalLocation?.longitude || 88.3639}
          defaultLocationName={globalLocation?.displayName || 'North 24 Parganas, West Bengal'}
        />
      )}

      {/* CREATE / EDIT FIELD MODAL */}
      {showFieldModal && (
        <FieldFormModal
          farms={farms}
          field={editingField}
          onClose={() => setShowFieldModal(false)}
          onSave={async (data) => {
            await saveField(data);
            setShowFieldModal(false);
          }}
        />
      )}

      {/* CREATE / EDIT CROP MODAL */}
      {showCropModal && (
        <CropFormModal
          fields={fields}
          crop={editingCrop}
          onClose={() => setShowCropModal(false)}
          onSave={async (data) => {
            await saveCrop(data);
            setShowCropModal(false);
          }}
        />
      )}
    </div>
  );
};

// --- MODAL COMPONENTS ---

const FarmFormModal: React.FC<{
  farm: any;
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
  defaultLat: number;
  defaultLon: number;
  defaultLocationName: string;
}> = ({ farm, onClose, onSave, defaultLat, defaultLon, defaultLocationName }) => {
  const [farmName, setFarmName] = useState(farm?.farm_name || 'Main Farm');
  const [locationName, setLocationName] = useState(farm?.location_name || defaultLocationName);
  const [lat, setLat] = useState(farm?.latitude || defaultLat);
  const [lon, setLon] = useState(farm?.longitude || defaultLon);
  const [areaVal, setAreaVal] = useState(farm?.area_value || 5.0);
  const [areaUnit, setAreaUnit] = useState(farm?.area_unit || 'acre');
  const [waterSource, setWaterSource] = useState(farm?.water_source || 'Borewell');
  const [irrigationMethod, setIrrigationMethod] = useState(farm?.irrigation_method || 'Flood/Furrow');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      id: farm?.id,
      farm_name: farmName,
      location_name: locationName,
      latitude: Number(lat),
      longitude: Number(lon),
      area_value: Number(areaVal),
      area_unit: areaUnit,
      water_source: waterSource,
      irrigation_method: irrigationMethod,
    });
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl border border-[#E2E7DA]">
        <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
          {farm ? 'Edit Farm' : 'Add New Farm'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <Input label="Farm Name" value={farmName} onChange={(e) => setFarmName(e.target.value)} required />
          <Input label="Location Name" value={locationName} onChange={(e) => setLocationName(e.target.value)} required />

          <div className="grid grid-cols-2 gap-3">
            <Input label="Latitude" type="number" step="any" value={lat} onChange={(e) => setLat(e.target.value)} required />
            <Input label="Longitude" type="number" step="any" value={lon} onChange={(e) => setLon(e.target.value)} required />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input label="Total Area" type="number" step="any" value={areaVal} onChange={(e) => setAreaVal(e.target.value)} required />
            <Select
              label="Area Unit"
              value={areaUnit}
              onChange={(e) => setAreaUnit(e.target.value)}
              options={[
                { value: 'acre', label: 'Acres' },
                { value: 'hectare', label: 'Hectares' },
                { value: 'bigha', label: 'Bighas' },
              ]}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Water Source"
              value={waterSource}
              onChange={(e) => setWaterSource(e.target.value)}
              options={[
                { value: 'Borewell', label: 'Borewell' },
                { value: 'Canal', label: 'Canal' },
                { value: 'Rainfed', label: 'Rainfed' },
                { value: 'River', label: 'River' },
              ]}
            />
            <Select
              label="Irrigation Method"
              value={irrigationMethod}
              onChange={(e) => setIrrigationMethod(e.target.value)}
              options={[
                { value: 'Drip', label: 'Drip Irrigation' },
                { value: 'Sprinkler', label: 'Sprinkler' },
                { value: 'Flood/Furrow', label: 'Flood / Furrow' },
                { value: 'Manual', label: 'Manual Watering' },
              ]}
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="lime">
              Save Farm
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

const FieldFormModal: React.FC<{
  farms: any[];
  field: any;
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}> = ({ farms, field, onClose, onSave }) => {
  const [farmId, setFarmId] = useState(field?.farm_id || (farms[0]?.id ?? 1));
  const [fieldName, setFieldName] = useState(field?.field_name || 'Field A');
  const [areaVal, setAreaVal] = useState(field?.area_value || 2.0);
  const [areaUnit, setAreaUnit] = useState(field?.area_unit || 'acre');
  const [soilType, setSoilType] = useState(field?.soil_type || 'Clay Loam');
  const [soilTest, setSoilTest] = useState(field?.soil_test_available || false);
  const [ph, setPh] = useState(field?.ph || '');
  const [n, setN] = useState(field?.nitrogen || '');
  const [p, setP] = useState(field?.phosphorus || '');
  const [k, setK] = useState(field?.potassium || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      id: field?.id,
      farm_id: Number(farmId),
      field_name: fieldName,
      area_value: Number(areaVal),
      area_unit: areaUnit,
      soil_type: soilType,
      soil_test_available: soilTest,
      ph: ph !== '' ? Number(ph) : null,
      nitrogen: n !== '' ? Number(n) : null,
      phosphorus: p !== '' ? Number(p) : null,
      potassium: k !== '' ? Number(k) : null,
    });
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl border border-[#E2E7DA]">
        <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
          {field?.id ? 'Edit Field' : 'Add New Field'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <Select
            label="Select Farm"
            value={farmId}
            onChange={(e) => setFarmId(e.target.value)}
            options={farms.map((f) => ({ value: f.id, label: f.farm_name }))}
          />

          <Input label="Field Name" value={fieldName} onChange={(e) => setFieldName(e.target.value)} required />

          <div className="grid grid-cols-2 gap-3">
            <Input label="Field Area" type="number" step="any" value={areaVal} onChange={(e) => setAreaVal(e.target.value)} required />
            <Select
              label="Area Unit"
              value={areaUnit}
              onChange={(e) => setAreaUnit(e.target.value)}
              options={[
                { value: 'acre', label: 'Acres' },
                { value: 'hectare', label: 'Hectares' },
                { value: 'bigha', label: 'Bighas' },
              ]}
            />
          </div>

          <Input label="Soil Type" value={soilType} onChange={(e) => setSoilType(e.target.value)} />

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="soilTest"
              checked={soilTest}
              onChange={(e) => setSoilTest(e.target.checked)}
              className="rounded text-[#2F6B3C]"
            />
            <label htmlFor="soilTest" className="font-bold text-[#0B1C10]">
              Soil Lab Test Available?
            </label>
          </div>

          {soilTest && (
            <div className="grid grid-cols-2 gap-3 p-3 bg-[#EEF3E8] rounded-2xl border border-[#E2E7DA]">
              <Input label="pH Value" type="number" step="any" value={ph} onChange={(e) => setPh(e.target.value)} placeholder="e.g. 6.5" />
              <Input label="Nitrogen (N) kg/ha" type="number" step="any" value={n} onChange={(e) => setN(e.target.value)} placeholder="e.g. 90" />
              <Input label="Phosphorus (P) kg/ha" type="number" step="any" value={p} onChange={(e) => setP(e.target.value)} placeholder="e.g. 42" />
              <Input label="Potassium (K) kg/ha" type="number" step="any" value={k} onChange={(e) => setK(e.target.value)} placeholder="e.g. 180" />
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="lime">
              Save Field
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

const CropFormModal: React.FC<{
  fields: any[];
  crop: any;
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}> = ({ fields, crop, onClose, onSave }) => {
  const [fieldId, setFieldId] = useState(crop?.field_id || (fields[0]?.id ?? 1));
  const [cropName, setCropName] = useState(crop?.crop_name || 'Rice');
  const [variety, setVariety] = useState(crop?.variety || 'Swarna');
  const [sowingDate, setSowingDate] = useState(crop?.sowing_date || '2026-08-15');
  const [growthStage, setGrowthStage] = useState(crop?.growth_stage || 'Vegetative');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      id: crop?.id,
      field_id: Number(fieldId),
      crop_name: cropName,
      variety,
      sowing_date: sowingDate,
      growth_stage: growthStage,
      status: 'ACTIVE',
    });
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl border border-[#E2E7DA]">
        <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
          {crop?.id ? 'Edit Crop Planting' : 'Add New Crop'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <Select
            label="Select Field"
            value={fieldId}
            onChange={(e) => setFieldId(e.target.value)}
            options={fields.map((f) => ({ value: f.id, label: `${f.field_name} (${f.area_value} ${f.area_unit})` }))}
          />

          <Select
            label="Crop Name"
            value={cropName}
            onChange={(e) => setCropName(e.target.value)}
            options={[
              { value: 'Rice', label: 'Rice / Paddy' },
              { value: 'Potato', label: 'Potato' },
              { value: 'Tomato', label: 'Tomato' },
              { value: 'Wheat', label: 'Wheat' },
              { value: 'Maize', label: 'Maize' },
              { value: 'Jute', label: 'Jute' },
              { value: 'Cotton', label: 'Cotton' },
              { value: 'Sugarcane', label: 'Sugarcane' },
            ]}
          />

          <Input label="Variety" value={variety} onChange={(e) => setVariety(e.target.value)} placeholder="e.g. Swarna, Jyoti" />
          <Input label="Sowing Date" type="date" value={sowingDate} onChange={(e) => setSowingDate(e.target.value)} />

          <Select
            label="Current Growth Stage"
            value={growthStage}
            onChange={(e) => setGrowthStage(e.target.value)}
            options={[
              { value: 'Seedling', label: 'Seedling / Germination' },
              { value: 'Vegetative', label: 'Vegetative' },
              { value: 'Flowering', label: 'Flowering' },
              { value: 'Fruiting', label: 'Fruiting / Tuber Bulking' },
              { value: 'Maturity', label: 'Maturity / Harvest Ready' },
            ]}
          />

          <div className="flex items-center justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="lime">
              Save Crop
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
