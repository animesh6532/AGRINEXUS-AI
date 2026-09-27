import React, { useState, useEffect, useRef } from 'react';
import {
  FlaskConical,
  AlertTriangle,
  Layers,
  MapPin,
  Sparkles,
  CheckCircle2,
  Info,
  RefreshCw,
  UserCheck,
  Camera,
  Store,
  Compass,
  FileText,
  ExternalLink,
  Phone,
  Globe,
  Star,
  Clock,
  X,
  Navigation,
  Upload,
  Eye,
  Stethoscope,
  ShieldAlert,
  ChevronRight
} from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { ConfidenceBar } from '../components/intelligence/ConfidenceBar';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
import { useLocationContext } from '../context/LocationContext';
import { useFarmerProfile } from '../context/FarmerProfileContext';
import { api } from '../services/api';
import { FertilizerRecommendResponse } from '../types/api';

const SUPPORTED_DISTRICTS = ['Pune', 'Kolhapur', 'Sangli', 'Satara', 'Solapur'];

const SUPPORTED_SOIL_COLORS = [
  { value: 'Black', label: 'Black Soil' },
  { value: 'Dark Brown', label: 'Dark Brown' },
  { value: 'Light Brown', label: 'Light Brown' },
  { value: 'Medium Brown', label: 'Medium Brown' },
  { value: 'Red', label: 'Red Soil' },
  { value: 'Reddish Brown', label: 'Reddish Brown' },
];

const SUPPORTED_CROPS = [
  { value: 'Rice', label: 'Paddy / Rice' },
  { value: 'Sugarcane', label: 'Sugarcane' },
  { value: 'Cotton', label: 'Cotton' },
  { value: 'Wheat', label: 'Wheat' },
  { value: 'Maize', label: 'Maize' },
  { value: 'Groundnut', label: 'Groundnut' },
  { value: 'Soybean', label: 'Soybean' },
  { value: 'Jowar', label: 'Jowar' },
  { value: 'Tur', label: 'Tur / Arhar' },
  { value: 'Moong', label: 'Moong' },
  { value: 'Urad', label: 'Urad' },
  { value: 'Gram', label: 'Gram / Chickpea' },
  { value: 'Masoor', label: 'Masoor' },
  { value: 'Grapes', label: 'Grapes' },
  { value: 'Ginger', label: 'Ginger' },
  { value: 'Turmeric', label: 'Turmeric' },
];

export const FertilizerPage: React.FC = () => {
  const { location, openPicker, requestCurrentLocation, permissionState } = useLocationContext();
  const { activeCrops, fields } = useFarmerProfile();

  // Workflow Tabs: 'manual' | 'location' | 'scanner'
  const [activeWorkflow, setActiveWorkflow] = useState<'manual' | 'location' | 'scanner'>('manual');

  // Manual Mode State
  const [inputMode, setInputMode] = useState<'manual' | 'field_data'>('manual');
  const [weatherProvenance, setWeatherProvenance] = useState<'LIVE WEATHER' | 'Manual Input'>('Manual Input');

  const [formData, setFormData] = useState({
    Nitrogen: 37.0,
    Phosphorus: 20.0,
    Potassium: 20.0,
    pH: 6.5,
    Rainfall: 120.0,
    Temperature: 26.0,
    District_Name: 'Pune',
    Soil_color: 'Black',
    Crop: 'Rice',
  });

  const [statusState, setStatusState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [result, setResult] = useState<FertilizerRecommendResponse | null>(null);
  const [resolvedImage, setResolvedImage] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Smart Location / Nearby Shops State
  const [shops, setShops] = useState<any[]>([]);
  const [loadingShops, setLoadingShops] = useState<boolean>(false);
  const [shopsMessage, setShopsMessage] = useState<string | null>(null);
  const [shopsErrorDiagnostic, setShopsErrorDiagnostic] = useState<string | null>(null);
  const [shopSortBy, setShopSortBy] = useState<'nearest' | 'highest_rated' | 'open_now'>('nearest');
  const [selectedShop, setSelectedShop] = useState<any | null>(null);
  const shopsRequestSeqRef = useRef<number>(0);

  const [soilContext, setSoilContext] = useState<any | null>(null);
  const [loadingSoilContext, setLoadingSoilContext] = useState<boolean>(false);

  // AI Camera Scanner State (sub-tabs: 'soil_scan' | 'plant_scan' | 'ocr_report')
  const [scannerSubTab, setScannerSubTab] = useState<'soil_scan' | 'plant_scan' | 'ocr_report'>('ocr_report');
  const [scannerFile, setScannerFile] = useState<File | null>(null);
  const [scannerPreview, setScannerPreview] = useState<string | null>(null);
  const [scannerLoading, setScannerLoading] = useState<boolean>(false);
  const [scannerResult, setScannerResult] = useState<any | null>(null);
  const [ocrExtractedValues, setOcrExtractedValues] = useState<any | null>(null);

  // Camera stream state
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);


  // Pre-populate District_Name if location resolves to a supported Western Maharashtra district
  useEffect(() => {
    if (location) {
      const locName = location.district || location.city || '';
      const matched = SUPPORTED_DISTRICTS.find(
        (d) => d.toLowerCase() === locName.toLowerCase()
      );
      if (matched) {
        setFormData((prev) => ({ ...prev, District_Name: matched }));
      }
    }
  }, [location?.district, location?.city]);

  // Load live weather values if location is available
  useEffect(() => {
    async function loadWeather() {
      if (location?.latitude && location?.longitude) {
        try {
          const wx = await api.getWeatherCurrent(location.latitude, location.longitude);
          if (wx) {
            setFormData((prev) => ({
              ...prev,
              Temperature: wx.temperature ?? prev.Temperature,
              Rainfall: wx.precipitation ?? prev.Rainfall,
            }));
            setWeatherProvenance('LIVE WEATHER');
          }
        } catch {
          // Keep current values
        }
      }
    }
    loadWeather();
  }, [location?.latitude, location?.longitude]);

  // Load Soil Context & Nearby Shops when Location tab is active
  useEffect(() => {
    if (activeWorkflow === 'location' && location?.latitude && location?.longitude) {
      loadSoilContext(location.latitude, location.longitude);
      loadNearbyShops(location.latitude, location.longitude, shopSortBy);
    }
  }, [activeWorkflow, location?.latitude, location?.longitude, shopSortBy]);

  const loadSoilContext = async (lat: number, lon: number) => {
    setLoadingSoilContext(true);
    try {
      const res = await api.getSoilContext(lat, lon);
      setSoilContext(res);
    } catch {
      setSoilContext({ status: 'unavailable', source: 'SoilGrids', data: null });
    } finally {
      setLoadingSoilContext(false);
    }
  };

  const loadNearbyShops = async (lat: number, lon: number, sortBy: string) => {
    const currentSeq = ++shopsRequestSeqRef.current;
    setLoadingShops(true);
    setShopsMessage(null);
    setShopsErrorDiagnostic(null);

    try {
      const res = await api.findNearbyShops(lat, lon, 25.0, sortBy as any);
      if (shopsRequestSeqRef.current !== currentSeq) {
        // Discard stale response from an old location or filter change
        return;
      }
      if (res) {
        setShops(res.shops || []);
        setShopsMessage(res.message || null);
        setShopsErrorDiagnostic(res.error_diagnostic || null);
      }
    } catch (err: any) {
      if (shopsRequestSeqRef.current !== currentSeq) return;
      console.warn('Failed to load nearby shops:', err);
      setShops([]);
      setShopsErrorDiagnostic(err?.message || 'Unable to connect to supplier search service.');
    } finally {
      if (shopsRequestSeqRef.current === currentSeq) {
        setLoadingShops(false);
      }
    }
  };

  // Camera stream controls (Requirement 29)
  const startCamera = async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      mediaStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsCameraActive(true);
    } catch (err: any) {
      console.warn('Camera acquisition error:', err);
      setCameraError('Camera access is unavailable. Please upload an image file.');
      setIsCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const captureCameraFrame = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (blob) {
          const capturedFile = new File([blob], `camera_scan_${Date.now()}.jpg`, { type: 'image/jpeg' });
          setScannerFile(capturedFile);
          setScannerPreview(canvas.toDataURL('image/jpeg'));
          stopCamera();
        }
      }, 'image/jpeg', 0.9);
    }
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);


  // Optional: Load My Field Data from Farmer Profile
  const handleUseFieldData = () => {
    setInputMode('field_data');
    const primaryCrop = activeCrops[0];
    const primaryField = fields[0];

    const updated = { ...formData };

    if (primaryCrop) {
      const matchedCrop = SUPPORTED_CROPS.find(
        (c) =>
          c.value.toLowerCase() === primaryCrop.crop_name.toLowerCase() ||
          c.label.toLowerCase().includes(primaryCrop.crop_name.toLowerCase())
      );
      if (matchedCrop) {
        updated.Crop = matchedCrop.value;
      }
    }

    if (primaryField) {
      if (primaryField.nitrogen !== undefined && primaryField.nitrogen !== null) {
        updated.Nitrogen = Number(primaryField.nitrogen);
      }
      if (primaryField.phosphorus !== undefined && primaryField.phosphorus !== null) {
        updated.Phosphorus = Number(primaryField.phosphorus);
      }
      if (primaryField.potassium !== undefined && primaryField.potassium !== null) {
        updated.Potassium = Number(primaryField.potassium);
      }
      if (primaryField.ph !== undefined && primaryField.ph !== null) {
        updated.pH = Number(primaryField.ph);
      }
    }

    setFormData(updated);
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (field === 'Temperature' || field === 'Rainfall') {
      setWeatherProvenance('Manual Input');
    }
    if (statusState === 'success' || statusState === 'error') {
      setStatusState('idle');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Input Validation
    if (formData.Nitrogen < 0 || formData.Phosphorus < 0 || formData.Potassium < 0) {
      setError('Nutrient values (N, P, K) cannot be negative.');
      setStatusState('error');
      return;
    }
    if (formData.pH < 0 || formData.pH > 14) {
      setError('Soil pH must be between 0.0 and 14.0.');
      setStatusState('error');
      return;
    }
    if (formData.Rainfall < 0) {
      setError('Rainfall cannot be negative.');
      setStatusState('error');
      return;
    }
    if (formData.Temperature < -10 || formData.Temperature > 60) {
      setError('Temperature must be between -10°C and 60°C.');
      setStatusState('error');
      return;
    }
    if (!formData.District_Name) {
      setError('Please select a valid district.');
      setStatusState('error');
      return;
    }

    setStatusState('loading');
    setError(null);
    setResolvedImage(null);

    try {
      const res = await api.predictFertilizer({
        Nitrogen: Number(formData.Nitrogen),
        Phosphorus: Number(formData.Phosphorus),
        Potassium: Number(formData.Potassium),
        pH: Number(formData.pH),
        Rainfall: Number(formData.Rainfall),
        Temperature: Number(formData.Temperature),
        District_Name: formData.District_Name,
        Soil_color: formData.Soil_color,
        Crop: formData.Crop,
        Link: 'https://example.com',
      });

      setResult(res);
      setStatusState('success');

      // Async resolution of fertilizer product image (non-blocking)
      if (res && res.predicted_formulation) {
        api.resolveFertilizerImage(res.predicted_formulation)
          .then((imgRes) => setResolvedImage(imgRes))
          .catch(() => setResolvedImage(null));
      }
    } catch (err: any) {
      console.error('Fertilizer Recommendation Error:', err);
      setError('Unable to generate a recommendation. Please check your inputs and try again.');
      setStatusState('error');
    }
  };

  // Handle Scanner File Selected
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setScannerFile(file);
      setScannerPreview(URL.createObjectURL(file));
      setScannerResult(null);
      setOcrExtractedValues(null);
    }
  };

  // Run AI Scanner Process
  const handleRunScanner = async () => {
    if (!scannerFile) return;
    setScannerLoading(true);
    setScannerResult(null);
    setError(null);

    try {
      if (scannerSubTab === 'ocr_report') {
        const ocrRes = await api.ocrSoilReport(scannerFile);
        setScannerResult(ocrRes);
        if (ocrRes && ocrRes.extracted_values) {
          setOcrExtractedValues(ocrRes.extracted_values);
        }
      } else if (scannerSubTab === 'soil_scan') {
        const soilRes = await api.soilVisualScan(scannerFile);
        setScannerResult(soilRes);
      } else if (scannerSubTab === 'plant_scan') {
        const plantRes = await api.predictDisease(scannerFile, false);
        setScannerResult(plantRes);
      }
    } catch (err: any) {
      setError(err.message || 'Scanner processing failed.');
    } finally {
      setScannerLoading(false);
    }
  };

  // Apply OCR Extracted Values to ML Form & switch to Manual Recommendation mode
  const handleApplyExtractedValues = () => {
    if (!ocrExtractedValues) return;
    setFormData((prev) => ({
      ...prev,
      Nitrogen: ocrExtractedValues.Nitrogen ?? prev.Nitrogen,
      Phosphorus: ocrExtractedValues.Phosphorus ?? prev.Phosphorus,
      Potassium: ocrExtractedValues.Potassium ?? prev.Potassium,
      pH: ocrExtractedValues.pH ?? prev.pH,
    }));
    setActiveWorkflow('manual');
  };

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Hero Section */}
      <AgriculturalPageHero
        category="FIELD INTELLIGENCE"
        title="Fertilizer Recommendation"
        description="Get an ML-based fertilizer recommendation using soil, crop and environmental information."
        imageSrc="/images/smart-farming.webp"
      >
        <span className="px-3 py-1 rounded-full bg-[#D4E768] text-[#0B1C10] text-xs font-extrabold uppercase tracking-widest">
          ML MODEL READY
        </span>
        <span className="px-3 py-1 rounded-full bg-white/10 text-white border border-white/20 text-xs font-semibold tracking-wider">
          TRAINED ON WESTERN MAHARASHTRA DATA
        </span>
      </AgriculturalPageHero>

      {/* Primary Workflow Selector Tabs (A, B, C) */}
      <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4 flex-wrap gap-4">
        <div className="flex items-center gap-2 bg-[#EEF3E8] p-1.5 rounded-2xl border border-[#E2E7DA]">
          <button
            onClick={() => setActiveWorkflow('manual')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeWorkflow === 'manual'
                ? 'bg-[#2F6B3C] text-white shadow-md'
                : 'text-[#536056] hover:text-[#0B1C10]'
            }`}
          >
            <FlaskConical className="w-4 h-4" />
            <span>A. MANUAL RECOMMENDATION</span>
          </button>

          <button
            onClick={() => setActiveWorkflow('location')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeWorkflow === 'location'
                ? 'bg-[#2F6B3C] text-white shadow-md'
                : 'text-[#536056] hover:text-[#0B1C10]'
            }`}
          >
            <Compass className="w-4 h-4" />
            <span>B. SMART LOCATION & SHOPS</span>
          </button>

          <button
            onClick={() => setActiveWorkflow('scanner')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeWorkflow === 'scanner'
                ? 'bg-[#2F6B3C] text-white shadow-md'
                : 'text-[#536056] hover:text-[#0B1C10]'
            }`}
          >
            <Camera className="w-4 h-4" />
            <span>C. AI CAMERA SCANNER</span>
          </button>
        </div>

        {location && (
          <span className="text-xs font-semibold text-[#2F6B3C] flex items-center gap-1 bg-white px-3 py-1.5 rounded-full border border-[#E2E7DA]">
            <MapPin className="w-3.5 h-3.5" />
            {location.city || location.district || location.displayName}
          </span>
        )}
      </div>

      {/* WORKFLOW A: MANUAL RECOMMENDATION */}
      {activeWorkflow === 'manual' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Form Panel (5 Cols) */}
          <div className="lg:col-span-5 space-y-6">
            <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#E2E7DA] pb-4 gap-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-5 h-5 text-[#2F6B3C]" />
                  <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                    SOIL & CROP INFORMATION
                  </h3>
                </div>

                <div className="flex items-center gap-1.5 bg-[#FAFBF7] p-1 rounded-xl border border-[#E2E7DA]">
                  <button
                    type="button"
                    onClick={() => setInputMode('manual')}
                    className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-colors ${
                      inputMode === 'manual'
                        ? 'bg-[#2F6B3C] text-white shadow-sm'
                        : 'text-[#536056] hover:text-[#0B1C10]'
                    }`}
                  >
                    Manual
                  </button>
                  {(activeCrops.length > 0 || fields.length > 0) && (
                    <button
                      type="button"
                      onClick={handleUseFieldData}
                      className={`px-2.5 py-1 rounded-lg text-xs font-bold flex items-center gap-1 transition-colors ${
                        inputMode === 'field_data'
                          ? 'bg-[#2F6B3C] text-white shadow-sm'
                          : 'text-[#536056] hover:text-[#0B1C10]'
                      }`}
                    >
                      <UserCheck className="w-3 h-3" />
                      <span>My Field Data</span>
                    </button>
                  )}
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                {/* SOIL */}
                <div className="space-y-3">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-[#2F6B3C] block border-b border-[#EEF3E8] pb-1">
                    SOIL
                  </span>

                  <div className="grid grid-cols-2 gap-3">
                    <Select
                      label="Soil Color"
                      value={formData.Soil_color}
                      onChange={(e) => handleInputChange('Soil_color', e.target.value)}
                      options={SUPPORTED_SOIL_COLORS}
                    />

                    <Input
                      label="Soil pH"
                      type="number"
                      step="0.1"
                      min="0"
                      max="14"
                      value={formData.pH}
                      onChange={(e) => handleInputChange('pH', parseFloat(e.target.value) || 0)}
                      required
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    <Input
                      label="Nitrogen (N)"
                      type="number"
                      step="0.1"
                      min="0"
                      value={formData.Nitrogen}
                      onChange={(e) => handleInputChange('Nitrogen', parseFloat(e.target.value) || 0)}
                      unit="kg/ha"
                      required
                    />
                    <Input
                      label="Phosphorus (P)"
                      type="number"
                      step="0.1"
                      min="0"
                      value={formData.Phosphorus}
                      onChange={(e) => handleInputChange('Phosphorus', parseFloat(e.target.value) || 0)}
                      unit="kg/ha"
                      required
                    />
                    <Input
                      label="Potassium (K)"
                      type="number"
                      step="0.1"
                      min="0"
                      value={formData.Potassium}
                      onChange={(e) => handleInputChange('Potassium', parseFloat(e.target.value) || 0)}
                      unit="kg/ha"
                      required
                    />
                  </div>
                </div>

                {/* CROP & ENVIRONMENT */}
                <div className="space-y-3">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-[#2F6B3C] block border-b border-[#EEF3E8] pb-1">
                    CROP & ENVIRONMENT
                  </span>

                  <div className="grid grid-cols-2 gap-3">
                    <Select
                      label="Crop"
                      value={formData.Crop}
                      onChange={(e) => handleInputChange('Crop', e.target.value)}
                      options={SUPPORTED_CROPS}
                    />

                    <Select
                      label="District"
                      value={formData.District_Name}
                      onChange={(e) => handleInputChange('District_Name', e.target.value)}
                      options={[
                        { value: '', label: 'Select district' },
                        ...SUPPORTED_DISTRICTS.map((d) => ({ value: d, label: d })),
                      ]}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="relative">
                      <Input
                        label="Temperature"
                        type="number"
                        step="0.1"
                        value={formData.Temperature}
                        onChange={(e) => handleInputChange('Temperature', parseFloat(e.target.value) || 0)}
                        unit="°C"
                        required
                      />
                      <span className="absolute top-0 right-0 text-[9px] font-bold text-[#2F6B3C] bg-[#EEF3E8] px-1.5 py-0.5 rounded-full">
                        {weatherProvenance}
                      </span>
                    </div>

                    <div className="relative">
                      <Input
                        label="Rainfall"
                        type="number"
                        step="0.1"
                        value={formData.Rainfall}
                        onChange={(e) => handleInputChange('Rainfall', parseFloat(e.target.value) || 0)}
                        unit="mm"
                        required
                      />
                      <span className="absolute top-0 right-0 text-[9px] font-bold text-[#2F6B3C] bg-[#EEF3E8] px-1.5 py-0.5 rounded-full">
                        {weatherProvenance}
                      </span>
                    </div>
                  </div>
                </div>

                <Button
                  type="submit"
                  variant="lime"
                  size="lg"
                  className="w-full mt-2 shadow-md hover:shadow-glow"
                  isLoading={statusState === 'loading'}
                  icon={<FlaskConical className="w-4 h-4" />}
                >
                  {statusState === 'loading'
                    ? 'Analyzing...'
                    : statusState === 'success'
                    ? 'Recommendation Ready'
                    : 'Recommend Fertilizer'}
                </Button>
              </form>
            </GlassCard>

            <ScopeWarning
              message="ML recommendation trained on Western Maharashtra soil/crop data. For farm-specific fertilizer rates, use current soil-test results and local agronomic guidance."
              type="info"
            />
          </div>

          {/* Right Recommendation Panel (7 Cols) */}
          <div className="lg:col-span-7 space-y-6">
            {statusState === 'error' && error && (
              <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {statusState === 'loading' && (
              <GlassCard variant="solid" className="p-8 sm:p-12 text-center space-y-6 flex flex-col items-center justify-center min-h-[380px]">
                <RefreshCw className="w-10 h-10 text-[#2F6B3C] animate-spin" />
                <div className="space-y-2">
                  <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                    Analyzing soil and crop inputs...
                  </h3>
                  <p className="text-xs text-[#536056]">
                    Evaluating feature space against trained LightGBM fertilizer classification model.
                  </p>
                </div>
              </GlassCard>
            )}

            {statusState === 'idle' && !result && (
              <div className="relative rounded-3xl overflow-hidden border border-[#E2E7DA] bg-[#FAFBF7] p-8 sm:p-12 text-center space-y-6 flex flex-col items-center justify-center min-h-[380px] group">
                <div className="w-14 h-14 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center font-extrabold text-xl shadow-sm">
                  <FlaskConical className="w-7 h-7" />
                </div>

                <div className="space-y-2 max-w-md">
                  <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                    Enter your soil and crop information to get a fertilizer recommendation.
                  </h3>
                  <p className="text-xs text-[#536056] leading-relaxed">
                    Provide soil nutrients, pH, soil color, crop type, district, and weather conditions on the left panel to execute ML inference.
                  </p>
                </div>
              </div>
            )}

            {statusState === 'success' && result && (
              <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
                {/* Header & Product Image Card */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 border-b border-[#E2E7DA] pb-6 items-center">
                  <div className="md:col-span-7 space-y-2">
                    <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                      RECOMMENDED FERTILIZER
                    </span>
                    <h2 className="text-3xl sm:text-4xl font-black font-editorial text-[#0B1C10] flex items-center gap-3">
                      <FlaskConical className="w-8 h-8 text-[#2F6B3C]" />
                      {result.predicted_formulation}
                    </h2>
                    <p className="text-xs text-[#536056] font-sans">
                      Based on your entered soil, crop, and environmental conditions.
                    </p>

                    {result.confidence !== null && result.confidence !== undefined && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA] mt-2">
                        {(result.confidence * 100).toFixed(1)}% Model Confidence
                      </span>
                    )}
                  </div>

                  {/* Resolved Product Image */}
                  <div className="md:col-span-5 flex flex-col items-center justify-center">
                    {resolvedImage && resolvedImage.image_url ? (
                      <div className="w-full rounded-2xl overflow-hidden border border-[#E2E7DA] bg-[#FAFBF7] p-2 space-y-1.5 group">
                        <img
                          src={resolvedImage.image_url}
                          alt={result.predicted_formulation}
                          className="w-full h-36 object-cover rounded-xl transition-transform duration-500 group-hover:scale-105"
                        />
                        <div className="flex items-center justify-between text-[10px] text-[#536056] px-1 gap-2">
                          <span className="truncate">
                            {resolvedImage.source_url ? (
                              <a
                                href={resolvedImage.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="hover:underline font-semibold text-[#2F6B3C] inline-flex items-center gap-1"
                              >
                                <span>
                                  {resolvedImage.photographer
                                    ? `Photo by ${resolvedImage.photographer} on Pexels`
                                    : 'Photos provided by Pexels'}
                                </span>
                                <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                              </a>
                            ) : (
                              <span>
                                {resolvedImage.photographer
                                  ? `Photo by ${resolvedImage.photographer} on Pexels`
                                  : 'Photos provided by Pexels'}
                              </span>
                            )}
                          </span>
                          <span className="font-extrabold text-[#2F6B3C] uppercase text-[9px] shrink-0 bg-[#EEF3E8] px-2 py-0.5 rounded-full border border-[#E2E7DA]">
                            {resolvedImage.image_type || 'Representative'}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="w-full h-36 rounded-2xl border border-dashed border-[#E2E7DA] bg-[#FAFBF7] flex flex-col items-center justify-center text-center p-4 space-y-1">
                        <FlaskConical className="w-6 h-6 text-[#536056]/50" />
                        <span className="text-xs font-bold text-[#536056]">Fertilizer image unavailable</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Input Conditions */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
                    INPUT CONDITIONS
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
                    <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                      <span className="text-[10px] text-[#536056] uppercase font-bold block">CROP</span>
                      <span className="font-bold text-[#0B1C10]">
                        {SUPPORTED_CROPS.find((c) => c.value === formData.Crop)?.label || formData.Crop}
                      </span>
                    </div>
                    <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                      <span className="text-[10px] text-[#536056] uppercase font-bold block">SOIL</span>
                      <span className="font-bold text-[#0B1C10]">{formData.Soil_color} Soil</span>
                    </div>
                    <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                      <span className="text-[10px] text-[#536056] uppercase font-bold block">DISTRICT</span>
                      <span className="font-bold text-[#0B1C10]">{formData.District_Name}</span>
                    </div>
                    <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                      <span className="text-[10px] text-[#536056] uppercase font-bold block">SOIL pH</span>
                      <span className="font-bold text-[#0B1C10]">{formData.pH}</span>
                    </div>
                    <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                      <span className="text-[10px] text-[#536056] uppercase font-bold block">NITROGEN (N)</span>
                      <span className="font-bold text-[#0B1C10]">{formData.Nitrogen} kg/ha</span>
                    </div>
                    <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                      <span className="text-[10px] text-[#536056] uppercase font-bold block">PHOSPHORUS (P)</span>
                      <span className="font-bold text-[#0B1C10]">{formData.Phosphorus} kg/ha</span>
                    </div>
                    <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                      <span className="text-[10px] text-[#536056] uppercase font-bold block">POTASSIUM (K)</span>
                      <span className="font-bold text-[#0B1C10]">{formData.Potassium} kg/ha</span>
                    </div>
                    <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                      <span className="text-[10px] text-[#536056] uppercase font-bold block">CLIMATE</span>
                      <span className="font-bold text-[#0B1C10]">
                        {formData.Temperature}°C • {formData.Rainfall}mm
                      </span>
                    </div>
                  </div>
                </div>

                {/* Model Result / Evidence */}
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
                      MODEL RESULT
                    </h4>
                    <span className="text-[10px] text-[#2F6B3C] font-semibold">
                      Recommended based on the trained fertilizer classification model.
                    </span>
                  </div>

                  {result.confidence !== null && result.confidence !== undefined && (
                    <ConfidenceBar confidence={result.confidence} label="Model Prediction Probability" />
                  )}

                  {result.top_k_predictions && result.top_k_predictions.length > 0 && (
                    <div className="space-y-2 pt-2">
                      <span className="text-[10px] font-bold text-[#536056] uppercase tracking-wider block">
                        Alternative Model Candidate Formulations
                      </span>
                      <div className="space-y-1.5">
                        {result.top_k_predictions.map((item, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-3 rounded-xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs font-semibold"
                          >
                            <span className="text-[#0B1C10] flex items-center gap-2">
                              <span className="w-5 h-5 rounded-full bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center text-[10px] font-extrabold">
                                {idx + 1}
                              </span>
                              {item.formulation}
                            </span>
                            <span className="font-mono font-extrabold text-[#2F6B3C]">
                              {(item.probability * 100).toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Simple Explanation */}
                <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1.5">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#2F6B3C]">
                    <Sparkles className="w-4 h-4 shrink-0" />
                    <span>SIMPLE EXPLANATION</span>
                  </div>
                  <p className="text-xs text-[#0B1C10] leading-relaxed">
                    Your recommendation was generated using the selected crop, soil type, nutrient values, pH, rainfall, temperature, and district.
                  </p>
                </div>

                {/* Nutrient Summary Cards */}
                <div className="space-y-3 pt-2">
                  <h4 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
                    NUTRIENT SUMMARY
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                    <div className="p-3.5 rounded-2xl bg-white border border-[#E2E7DA]">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] block">
                        NITROGEN
                      </span>
                      <span className="text-lg font-black font-editorial text-[#0B1C10] block mt-0.5">
                        {formData.Nitrogen} kg/ha
                      </span>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-white border border-[#E2E7DA]">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] block">
                        PHOSPHORUS
                      </span>
                      <span className="text-lg font-black font-editorial text-[#0B1C10] block mt-0.5">
                        {formData.Phosphorus} kg/ha
                      </span>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-white border border-[#E2E7DA]">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] block">
                        POTASSIUM
                      </span>
                      <span className="text-lg font-black font-editorial text-[#0B1C10] block mt-0.5">
                        {formData.Potassium} kg/ha
                      </span>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-white border border-[#E2E7DA]">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] block">
                        SOIL pH
                      </span>
                      <span className="text-lg font-black font-editorial text-[#0B1C10] block mt-0.5">
                        {formData.pH}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Educational 4R Context */}
                <div className="p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#0B1C10] flex items-center gap-1.5">
                      <Info className="w-4 h-4 text-[#2F6B3C]" />
                      <span>Nutrient Management Context</span>
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#EEF3E8] text-[#2F6B3C]">
                      General nutrient-management guidance
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] text-[#536056]">
                    <div className="p-2 rounded-xl bg-white border border-[#E2E7DA]">
                      <strong className="text-[#0B1C10] block">Right Source</strong>
                      Choose suitable formulation.
                    </div>
                    <div className="p-2 rounded-xl bg-white border border-[#E2E7DA]">
                      <strong className="text-[#0B1C10] block">Right Rate</strong>
                      Base rate on lab soil test.
                    </div>
                    <div className="p-2 rounded-xl bg-white border border-[#E2E7DA]">
                      <strong className="text-[#0B1C10] block">Right Time</strong>
                      Apply at growth stage demand.
                    </div>
                    <div className="p-2 rounded-xl bg-white border border-[#E2E7DA]">
                      <strong className="text-[#0B1C10] block">Right Place</strong>
                      Place near root zone.
                    </div>
                  </div>
                </div>

                <div className="pt-2 border-t border-[#E2E7DA] text-[11px] text-[#536056] space-y-1">
                  <span className="font-bold text-[#0B1C10] uppercase tracking-wider block text-[10px]">
                    MODEL SCOPE
                  </span>
                  <p>
                    This recommendation is generated by an ML model trained on Western Maharashtra fertilizer data. For farm-specific fertilizer rates, use current soil-test results and local agronomic guidance.
                  </p>
                </div>
              </GlassCard>
            )}
          </div>
        </div>
      )}

      {/* WORKFLOW B: SMART LOCATION & NEARBY SHOPS */}
      {activeWorkflow === 'location' && (
        <div className="space-y-6">
          {/* Missing Soil Test Banner Notice */}
          <div className="p-5 rounded-3xl bg-[#FAFBF7] border border-[#E2E7DA] flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center shrink-0 mt-0.5">
                <Info className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-extrabold text-[#0B1C10]">
                  Soil nutrient values are required for the ML fertilizer recommendation.
                </h4>
                <p className="text-xs text-[#536056]">
                  Location provides environmental telemetry and nearby supplier context. Lab soil measurements (N, P, K) are needed to calculate crop formulation recommendations.
                </p>
              </div>
            </div>

            <Button
              variant="lime"
              size="md"
              onClick={() => setActiveWorkflow('manual')}
              icon={<FlaskConical className="w-4 h-4" />}
            >
              Enter Soil Test Values
            </Button>
          </div>

          {/* Location & Weather Context Header */}
          <GlassCard variant="solid" className="p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#E2E7DA] pb-4 gap-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056]">
                  LOCATION CONTEXT
                </span>
                <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10] flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-[#2F6B3C]" />
                  {location?.displayName || 'Current Location'}
                </h3>
              </div>

              <button
                onClick={openPicker}
                className="px-3.5 py-1.5 rounded-xl bg-[#EEF3E8] border border-[#E2E7DA] text-xs font-bold text-[#2F6B3C] hover:bg-[#D4E768] hover:text-[#0B1C10] transition-colors self-start sm:self-auto"
              >
                Change Location
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[10px] text-[#536056] uppercase font-bold block">DISTRICT</span>
                <span className="font-bold text-[#0B1C10]">{location?.district || formData.District_Name}</span>
              </div>
              <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[10px] text-[#536056] uppercase font-bold block">STATE</span>
                <span className="font-bold text-[#0B1C10]">{location?.state || 'Maharashtra'}</span>
              </div>
              <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[10px] text-[#536056] uppercase font-bold block">GPS COORDINATES</span>
                <span className="font-mono text-[#0B1C10]">
                  {location?.latitude?.toFixed(4)}, {location?.longitude?.toFixed(4)}
                </span>
              </div>
              <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[10px] text-[#536056] uppercase font-bold block">LOCATION SOURCE</span>
                <span className="font-bold text-[#2F6B3C]">{location?.source || 'GPS'}</span>
              </div>
            </div>
          </GlassCard>

          {/* NEARBY FERTILIZER & AGRO INPUT SHOPS */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#E2E7DA] pb-3 gap-3">
              <div>
                <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                  SUPPLIER DIRECTORY
                </span>
                <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10] flex items-center gap-2">
                  <Store className="w-5 h-5 text-[#2F6B3C]" />
                  NEARBY FERTILIZER & AGRO INPUT SHOPS
                </h3>
              </div>

              {/* Filters */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-[#536056] font-semibold">Sort:</span>
                <select
                  value={shopSortBy}
                  onChange={(e: any) => setShopSortBy(e.target.value)}
                  className="text-xs font-bold px-3 py-1.5 rounded-xl bg-white border border-[#E2E7DA] text-[#0B1C10]"
                >
                  <option value="nearest">Nearest</option>
                  <option value="highest_rated">Highest Rated</option>
                  <option value="open_now">Open Now</option>
                </select>
              </div>
            </div>

            {shopsMessage && (
              <div className="p-3.5 rounded-2xl bg-[#EEF3E8] border border-[#2F6B3C]/20 text-xs font-semibold text-[#2F6B3C] flex items-center gap-2">
                <span>ℹ️</span>
                <span>{shopsMessage}</span>
              </div>
            )}

            {shopsErrorDiagnostic && (
              <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1">
                <strong className="block font-bold">Supplier Search Diagnostic:</strong>
                <p>{shopsErrorDiagnostic}</p>
              </div>
            )}

            {loadingShops ? (
              <GlassCard variant="solid" className="p-8 text-center space-y-3">
                <RefreshCw className="w-8 h-8 text-[#2F6B3C] animate-spin mx-auto" />
                <p className="text-xs text-[#536056] font-semibold">Searching nearby fertilizer suppliers...</p>
                <p className="text-[11px] text-[#536056]/80">Progressively expanding search radius (5 km → 10 km → 20 km → 30 km)...</p>
              </GlassCard>
            ) : shops.length === 0 ? (
              <div className="p-8 rounded-3xl bg-[#FAFBF7] border border-[#E2E7DA] text-center space-y-4">
                <Store className="w-10 h-10 text-[#536056]/50 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-extrabold text-[#0B1C10]">No fertilizer suppliers were found within 30 km.</h4>
                  <p className="text-xs text-[#536056]">
                    Google Places search around coordinates ({location?.latitude?.toFixed(4)}, {location?.longitude?.toFixed(4)}) yielded 0 matching businesses.
                  </p>
                </div>
                <div className="flex items-center justify-center gap-3 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadNearbyShops(location?.latitude || 22.7321, location?.longitude || 88.4996, shopSortBy)}
                  >
                    Expand Search Radius
                  </Button>
                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=fertilizer+shop+near+${location?.latitude || 22.7321},${location?.longitude || 88.4996}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button variant="lime" size="sm" icon={<ExternalLink className="w-3.5 h-3.5" />}>
                      Search on Google Maps
                    </Button>
                  </a>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {shops.map((shop) => (
                  <GlassCard
                    key={shop.shop_id}
                    variant="solid"
                    className="p-5 space-y-3 flex flex-col justify-between hover:border-[#2F6B3C] transition-all cursor-pointer group"
                    onClick={() => setSelectedShop(shop)}
                  >
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-sm font-extrabold text-[#0B1C10] group-hover:text-[#2F6B3C] transition-colors">
                          {shop.name}
                        </h4>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#EEF3E8] text-[#2F6B3C] shrink-0">
                          {shop.distance} km
                        </span>
                      </div>

                      <p className="text-xs text-[#536056] line-clamp-2">{shop.address}</p>

                      <div className="flex items-center gap-3 text-xs pt-1">
                        <span className="flex items-center gap-1 text-amber-600 font-bold">
                          <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                          {shop.rating} ({shop.review_count})
                        </span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {shop.opening_status}
                        </span>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-[#E2E7DA] flex items-center justify-between text-xs">
                      <span className="text-[#2F6B3C] font-bold flex items-center gap-1 group-hover:underline">
                        <span>View Details</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </span>

                      {shop.phone && (
                        <a
                          href={`tel:${shop.phone}`}
                          onClick={(e) => e.stopPropagation()}
                          className="p-1.5 rounded-lg bg-[#EEF3E8] text-[#2F6B3C] hover:bg-[#D4E768] transition-colors"
                          title="Call Shop"
                        >
                          <Phone className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </GlassCard>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* WORKFLOW C: AI CAMERA SCANNER */}
      {activeWorkflow === 'scanner' && (
        <div className="space-y-6">
          {/* Sub-tabs: SOIL SCAN, PLANT SCAN, SCAN SOIL TEST REPORT */}
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4 flex-wrap gap-3">
            <div>
              <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                AI FIELD SCANNER
              </span>
              <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                Capture a clear photo of your soil or plant for visual analysis.
              </h3>
            </div>

            <div className="flex items-center gap-2 bg-[#EEF3E8] p-1 rounded-2xl border border-[#E2E7DA]">
              <button
                onClick={() => {
                  setScannerSubTab('ocr_report');
                  setScannerResult(null);
                }}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                  scannerSubTab === 'ocr_report'
                    ? 'bg-[#2F6B3C] text-white shadow-md'
                    : 'text-[#536056] hover:text-[#0B1C10]'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>SCAN SOIL TEST REPORT</span>
              </button>

              <button
                onClick={() => {
                  setScannerSubTab('soil_scan');
                  setScannerResult(null);
                }}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                  scannerSubTab === 'soil_scan'
                    ? 'bg-[#2F6B3C] text-white shadow-md'
                    : 'text-[#536056] hover:text-[#0B1C10]'
                }`}
              >
                <Eye className="w-3.5 h-3.5" />
                <span>SOIL SCAN</span>
              </button>

              <button
                onClick={() => {
                  setScannerSubTab('plant_scan');
                  setScannerResult(null);
                }}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                  scannerSubTab === 'plant_scan'
                    ? 'bg-[#2F6B3C] text-white shadow-md'
                    : 'text-[#536056] hover:text-[#0B1C10]'
                }`}
              >
                <Stethoscope className="w-3.5 h-3.5" />
                <span>PLANT SCAN</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Upload / Capture Card (5 Cols) */}
            <div className="lg:col-span-5 space-y-6">
              <GlassCard variant="solid" className="p-6 space-y-5 text-center">
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                {scannerPreview ? (
                  <div className="relative rounded-2xl overflow-hidden border border-[#E2E7DA] group">
                    <img src={scannerPreview} alt="Scanner Preview" className="w-full h-56 object-cover" />
                    <button
                      onClick={() => {
                        setScannerFile(null);
                        setScannerPreview(null);
                        setScannerResult(null);
                      }}
                      className="absolute top-2 right-2 p-1.5 rounded-full bg-black/60 text-white hover:bg-black transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-[#E2E7DA] hover:border-[#2F6B3C] bg-[#FAFBF7] rounded-3xl p-8 space-y-4 cursor-pointer transition-all flex flex-col items-center justify-center min-h-[220px]"
                  >
                    <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center">
                      <Upload className="w-6 h-6" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs font-extrabold text-[#0B1C10]">
                        Click or drag photo here to upload
                      </p>
                      <p className="text-[11px] text-[#536056]">
                        {scannerSubTab === 'ocr_report'
                          ? 'Upload Soil Health Card or Lab Report image'
                          : scannerSubTab === 'soil_scan'
                          ? 'Capture surface photo of soil'
                          : 'Capture photo of plant leaf'}
                      </p>
                    </div>
                  </div>
                )}

                <Button
                  variant="lime"
                  size="lg"
                  className="w-full shadow-md"
                  disabled={!scannerFile || scannerLoading}
                  isLoading={scannerLoading}
                  onClick={handleRunScanner}
                  icon={<Camera className="w-4 h-4" />}
                >
                  {scannerLoading
                    ? 'Processing Image...'
                    : scannerSubTab === 'ocr_report'
                    ? 'Extract Lab Report Values'
                    : scannerSubTab === 'soil_scan'
                    ? 'Run Visual Soil Inspection'
                    : 'Run Plant Disease Diagnosis'}
                </Button>
              </GlassCard>
            </div>

            {/* Right Scanner Results Card (7 Cols) */}
            <div className="lg:col-span-7 space-y-6">
              {!scannerResult && !scannerLoading && (
                <div className="p-8 rounded-3xl bg-[#FAFBF7] border border-[#E2E7DA] text-center space-y-3 flex flex-col items-center justify-center min-h-[300px]">
                  <Camera className="w-8 h-8 text-[#536056]/40" />
                  <h4 className="text-sm font-extrabold text-[#0B1C10]">
                    Select or capture an image to execute visual scanner inference.
                  </h4>
                  <p className="text-xs text-[#536056] max-w-sm">
                    OpenCV quality inspection checks image resolution, blur, and exposure before processing.
                  </p>
                </div>
              )}

              {/* OCR REPORT RESULT & VERIFICATION */}
              {scannerSubTab === 'ocr_report' && scannerResult && (
                <GlassCard variant="solid" className="p-6 space-y-5">
                  <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
                    <div className="flex items-center gap-2">
                      <FileText className="w-5 h-5 text-[#2F6B3C]" />
                      <h4 className="text-base font-extrabold text-[#0B1C10]">
                        EXTRACTED REPORT VALUES
                      </h4>
                    </div>
                    <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-[#EEF3E8] text-[#2F6B3C]">
                      Please verify extracted values
                    </span>
                  </div>

                  <p className="text-xs text-[#536056]">{scannerResult.status}</p>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {Object.entries(ocrExtractedValues || {}).map(([key, val]: [string, any]) => (
                      <div key={key} className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-1">
                        <span className="text-[10px] text-[#536056] uppercase font-bold block">{key}</span>
                        <input
                          type="number"
                          step="0.1"
                          value={val}
                          onChange={(e) =>
                            setOcrExtractedValues({
                              ...ocrExtractedValues,
                              [key]: parseFloat(e.target.value) || 0,
                            })
                          }
                          className="w-full font-bold text-sm text-[#0B1C10] bg-white border border-[#E2E7DA] rounded-lg px-2 py-1"
                        />
                      </div>
                    ))}
                  </div>

                  <Button
                    variant="lime"
                    size="md"
                    className="w-full shadow-md"
                    onClick={handleApplyExtractedValues}
                    icon={<CheckCircle2 className="w-4 h-4" />}
                  >
                    Use These Values For Fertilizer Recommendation
                  </Button>
                </GlassCard>
              )}

              {/* SOIL VISUAL SCAN RESULT */}
              {scannerSubTab === 'soil_scan' && scannerResult && (
                <GlassCard variant="solid" className="p-6 space-y-5">
                  <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
                    <span className="text-xs font-bold uppercase tracking-widest text-[#536056]">
                      VISUAL OBSERVATION
                    </span>
                    <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                      Visual Cues (Not Lab Result)
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                      <span className="text-[10px] text-[#536056] uppercase font-bold block">VISUAL COLOR TONE</span>
                      <span className="font-bold text-[#0B1C10]">{scannerResult.visual_color}</span>
                    </div>
                    <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                      <span className="text-[10px] text-[#536056] uppercase font-bold block">SURFACE TEXTURE</span>
                      <span className="font-bold text-[#0B1C10]">{scannerResult.visual_texture}</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-1">
                    <strong className="block font-bold">Important Notice:</strong>
                    <p>{scannerResult.notice}</p>
                  </div>

                  <Button
                    variant="lime"
                    size="md"
                    className="w-full"
                    onClick={() => setActiveWorkflow('manual')}
                    icon={<FlaskConical className="w-4 h-4" />}
                  >
                    Enter Laboratory Soil Test Values
                  </Button>
                </GlassCard>
              )}

              {/* PLANT SCAN RESULT */}
              {scannerSubTab === 'plant_scan' && scannerResult && (
                <GlassCard variant="solid" className="p-6 space-y-5">
                  <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
                    <span className="text-xs font-bold uppercase tracking-widest text-[#536056]">
                      PLANT HEALTH DIAGNOSIS
                    </span>
                    <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-[#EEF3E8] text-[#2F6B3C]">
                      ResNet18 Model Result
                    </span>
                  </div>

                  <div className="space-y-2">
                    <span className="text-[10px] text-[#536056] uppercase font-bold block">PREDICTED CONDITION</span>
                    <h4 className="text-2xl font-black font-editorial text-[#0B1C10]">
                      {scannerResult.predicted_disease}
                    </h4>
                  </div>

                  {scannerResult.confidence && (
                    <ConfidenceBar confidence={scannerResult.confidence} label="Model Diagnostic Confidence" />
                  )}

                  {scannerResult.image_quality && scannerResult.image_quality.warnings.length > 0 && (
                    <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs space-y-1">
                      <strong className="block font-bold">Quality Warnings:</strong>
                      {scannerResult.image_quality.warnings.map((w: string, i: number) => (
                        <p key={i}>• {w}</p>
                      ))}
                    </div>
                  )}
                </GlassCard>
              )}
            </div>
          </div>
        </div>
      )}

      {/* SHOP DETAILS DRAWER / MODAL */}
      {selectedShop && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 space-y-5 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setSelectedShop(null)}
              className="absolute top-4 right-4 p-2 rounded-full bg-[#FAFBF7] border border-[#E2E7DA] text-[#536056] hover:text-[#0B1C10]"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="space-y-1 pr-8">
              <span className="text-[10px] font-bold uppercase tracking-widest text-[#2F6B3C]">
                SUPPLIER DETAILS
              </span>
              <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">
                {selectedShop.name}
              </h3>
              <p className="text-xs text-[#536056]">{selectedShop.address}</p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[10px] text-[#536056] uppercase font-bold block">DISTANCE</span>
                <span className="font-bold text-[#0B1C10]">{selectedShop.distance} km away</span>
              </div>
              <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[10px] text-[#536056] uppercase font-bold block">RATING</span>
                <span className="font-bold text-amber-600 flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                  {selectedShop.rating} ({selectedShop.review_count} reviews)
                </span>
              </div>
              <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[10px] text-[#536056] uppercase font-bold block">STATUS</span>
                <span className="font-bold text-emerald-700">{selectedShop.opening_status}</span>
              </div>
              <div className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[10px] text-[#536056] uppercase font-bold block">PHONE</span>
                <span className="font-bold text-[#0B1C10]">{selectedShop.phone || 'N/A'}</span>
              </div>
            </div>

            {selectedShop.categories && selectedShop.categories.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[10px] font-bold text-[#536056] uppercase tracking-wider block">
                  PRODUCTS & CATEGORIES
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedShop.categories.map((cat: string, i: number) => (
                    <span key={i} className="px-2.5 py-1 rounded-full bg-[#EEF3E8] text-[#2F6B3C] text-[11px] font-bold">
                      {cat}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-3 border-t border-[#E2E7DA] flex items-center gap-3">
              {selectedShop.google_maps_uri && (
                <a
                  href={selectedShop.google_maps_uri}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1"
                >
                  <Button variant="lime" size="md" className="w-full" icon={<ExternalLink className="w-4 h-4" />}>
                    Open in Google Maps
                  </Button>
                </a>
              )}

              {selectedShop.phone && (
                <a href={`tel:${selectedShop.phone}`}>
                  <Button variant="outline" size="md" icon={<Phone className="w-4 h-4" />}>
                    Call
                  </Button>
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
