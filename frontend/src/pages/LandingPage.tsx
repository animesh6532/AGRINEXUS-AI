import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Sprout,
  Stethoscope,
  Bug,
  FlaskConical,
  Droplets,
  Mountain,
  TrendingUp,
  Camera,
  CloudSun,
  BarChart3,
  Calendar,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Layers,
  Sparkles,
  Activity
} from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Footer } from '../components/layout/Footer';
import { useHealth } from '../context/HealthContext';

export const LandingPage: React.FC = () => {
  const { isApiConnected, isModelSystemReady } = useHealth();
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(false);
  const [videoLoaded, setVideoLoaded] = useState<boolean>(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);
    const handleChange = () => setPrefersReducedMotion(mediaQuery.matches);
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const modules = [
    {
      title: 'Crop Recommendation',
      desc: 'Recommends optimal crop species based on N, P, K, soil pH, temperature, humidity, and rainfall using ExtraTreesClassifier.',
      icon: <Sprout className="w-6 h-6 text-agri-600" />,
      tag: 'ExtraTrees + IsolationForest',
      path: '/crop'
    },
    {
      title: 'Plant Disease Detection',
      desc: 'Diagnoses 38 plant disease classes from leaf photos using PyTorch ResNet18 with optional Grad-CAM visual heatmaps.',
      icon: <Stethoscope className="w-6 h-6 text-primary-600" />,
      tag: 'ResNet18 + Grad-CAM',
      path: '/disease'
    },
    {
      title: 'Pest Intelligence',
      desc: 'Single-insect species classification (102 categories) & climate-based environmental pest outbreak risk modeling.',
      icon: <Bug className="w-6 h-6 text-amber-600" />,
      tag: 'MobileNetV3 + RandomForest',
      path: '/pest'
    },
    {
      title: 'Fertilizer Advisor',
      desc: 'Recommends commercial fertilizer product formulations tailored to soil nutrients and Western Maharashtra context.',
      icon: <FlaskConical className="w-6 h-6 text-purple-600" />,
      tag: 'LightGBM Pipeline',
      path: '/fertilizer'
    },
    {
      title: 'Irrigation Predictor',
      desc: '3-hour Soil Water Content prediction benchmarked against persistence baseline and agronomic wilting thresholds.',
      icon: <Droplets className="w-6 h-6 text-sky-600" />,
      tag: 'ML + Persistence Benchmark',
      path: '/irrigation'
    },
    {
      title: 'Soil Organic Carbon',
      desc: 'Estimates Soil Organic Carbon (g/kg) with 95% residual prediction intervals derived from LUCAS European topsoil data.',
      icon: <Mountain className="w-6 h-6 text-emerald-600" />,
      tag: 'LUCAS Preprocessing',
      path: '/soil'
    },
    {
      title: 'Yield Prediction',
      desc: 'Forecasts agricultural crop yield per hectare with 95% uncertainty confidence intervals.',
      icon: <TrendingUp className="w-6 h-6 text-indigo-600" />,
      tag: 'XGBoost Regression',
      path: '/yield'
    },
    {
      title: 'Live Camera Vision',
      desc: 'Real-time video frame inference with OpenCV blur/exposure quality inspection and session temporal smoothing.',
      icon: <Camera className="w-6 h-6 text-rose-600" />,
      tag: 'OpenCV + WebSockets',
      path: '/live'
    }
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background selection:bg-primary-100">
      {/* ------------------------------------------------------------------ */}
      {/* LANDING NAVIGATION BAR */}
      {/* ------------------------------------------------------------------ */}
      <header className="fixed top-0 left-0 right-0 h-20 glass-panel-strong border-b border-slate-200/70 z-50 px-6 sm:px-12 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-agri-500 to-primary-600 flex items-center justify-center text-white text-xl font-bold shadow-md">
            🌱
          </div>
          <div>
            <span className="font-extrabold text-lg text-slate-900 tracking-tight">AgriNexus-AI</span>
            <span className="text-[10px] text-slate-500 block uppercase font-medium">Agricultural Intelligence</span>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-xs font-semibold text-slate-600">
          <a href="#hero" className="hover:text-primary-600 transition-colors">Platform</a>
          <a href="#modules" className="hover:text-primary-600 transition-colors">AI Modules</a>
          <a href="#live-vision" className="hover:text-primary-600 transition-colors">Live Camera</a>
          <a href="#signals" className="hover:text-primary-600 transition-colors">Weather & Market</a>
          <a href="#transparency" className="hover:text-primary-600 transition-colors">Trust & Transparency</a>
        </nav>

        <div className="flex items-center gap-3">
          <Link to="/login">
            <Button variant="ghost" size="sm">Sign In</Button>
          </Link>
          <Link to="/dashboard">
            <Button variant="primary" size="sm" icon={<ArrowRight className="w-3.5 h-3.5" />}>
              Open Dashboard
            </Button>
          </Link>
        </div>
      </header>

      {/* ------------------------------------------------------------------ */}
      {/* HERO SECTION WITH VIDEO BACKGROUND */}
      {/* ------------------------------------------------------------------ */}
      <section id="hero" className="relative min-h-screen pt-32 pb-20 px-6 sm:px-12 flex items-center justify-center overflow-hidden">
        {/* Layer 1: Background Video / Reduced-Motion Poster */}
        {!prefersReducedMotion ? (
          <video
            autoPlay
            muted
            loop
            playsInline
            poster="/images/agriculture-hero-poster.webp"
            onLoadedData={() => setVideoLoaded(true)}
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-1000 ${
              videoLoaded ? 'opacity-25' : 'opacity-10'
            }`}
          >
            <source src="/videos/agriculture-hero.mp4" type="video/mp4" />
          </video>
        ) : (
          <img
            src="/images/agriculture-hero-poster.webp"
            alt="Agricultural Farmland"
            className="absolute inset-0 w-full h-full object-cover opacity-20"
          />
        )}

        {/* Layer 2: Soft Atmosphere Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-background/90 via-background/80 to-background z-0" />

        {/* Layer 3: Glass Hero Content */}
        <div className="relative z-10 max-w-5xl mx-auto text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/80 border border-slate-200/80 shadow-sm text-xs font-semibold text-slate-700">
            <Sparkles className="w-4 h-4 text-agri-600 animate-pulse" />
            <span>Integrated Agricultural Intelligence Platform</span>
            <Badge variant={isApiConnected ? 'success' : 'neutral'} dot>
              {isApiConnected ? '8/8 Services Ready' : 'Connecting Backend'}
            </Badge>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
            Smarter Decisions.{' '}
            <span className="bg-gradient-to-r from-agri-600 via-primary-600 to-accent-600 bg-clip-text text-transparent">
              Healthier Crops.
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-600 max-w-3xl mx-auto leading-relaxed">
            AgriNexus-AI brings crop, soil, disease, pest, irrigation, yield, weather, and market intelligence into one cohesive agricultural decision-support platform powered by 7 frozen ML artifacts.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Link to="/dashboard">
              <Button size="lg" variant="primary" icon={<ArrowRight className="w-4 h-4" />}>
                Explore AgriNexus-AI
              </Button>
            </Link>
            <Link to="/live">
              <Button size="lg" variant="secondary" icon={<Camera className="w-4 h-4" />}>
                View Live AI Camera
              </Button>
            </Link>
          </div>

          {/* Interactive Glass Intelligence Panel Preview */}
          <GlassCard variant="strong" className="p-6 mt-12 text-left grid grid-cols-2 md:grid-cols-5 gap-4 shadow-glass-hover">
            <div className="p-3.5 rounded-xl bg-white/60 border border-slate-100">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Crop Health</span>
              <div className="flex items-center gap-2 mt-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span className="text-xs font-semibold text-slate-900">Optimal Profile</span>
              </div>
            </div>
            <div className="p-3.5 rounded-xl bg-white/60 border border-slate-100">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Soil Moisture</span>
              <div className="flex items-center gap-2 mt-1">
                <Droplets className="w-4 h-4 text-sky-600" />
                <span className="text-xs font-semibold text-slate-900">0.22 SWC (3h Baseline)</span>
              </div>
            </div>
            <div className="p-3.5 rounded-xl bg-white/60 border border-slate-100">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Disease Camera</span>
              <div className="flex items-center gap-2 mt-1">
                <Camera className="w-4 h-4 text-rose-600" />
                <span className="text-xs font-semibold text-slate-900">OpenCV Quality Passed</span>
              </div>
            </div>
            <div className="p-3.5 rounded-xl bg-white/60 border border-slate-100">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Weather Risk</span>
              <div className="flex items-center gap-2 mt-1">
                <CloudSun className="w-4 h-4 text-amber-600" />
                <span className="text-xs font-semibold text-slate-900">28.5°C • Low Disruption</span>
              </div>
            </div>
            <div className="p-3.5 rounded-xl bg-white/60 border border-slate-100 col-span-2 md:col-span-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Market Trend</span>
              <div className="flex items-center gap-2 mt-1">
                <TrendingUp className="w-4 h-4 text-emerald-600" />
                <span className="text-xs font-semibold text-slate-900">Paddy(Common) ETS</span>
              </div>
            </div>
          </GlassCard>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* AI INTELLIGENCE MODULES SHOWCASE */}
      {/* ------------------------------------------------------------------ */}
      <section id="modules" className="py-20 px-6 sm:px-12 max-w-7xl mx-auto space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <Badge variant="primary">8 Inference Services</Badge>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Comprehensive Agricultural AI Modules
          </h2>
          <p className="text-sm text-slate-600">
            Powered by 7 validated frozen machine learning model artifacts with verified agronomic feature contracts.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {modules.map((m, idx) => (
            <Link key={idx} to={m.path}>
              <GlassCard className="p-6 h-full flex flex-col justify-between space-y-4 hover:border-primary-400">
                <div className="space-y-3">
                  <div className="w-12 h-12 rounded-2xl bg-white/80 border border-slate-200/60 flex items-center justify-center shadow-sm">
                    {m.icon}
                  </div>
                  <h3 className="text-base font-bold text-slate-900">{m.title}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed">{m.desc}</p>
                </div>
                <div className="pt-2 border-t border-slate-200/50 flex items-center justify-between text-[11px] font-medium text-slate-500">
                  <span className="truncate">{m.tag}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-primary-600" />
                </div>
              </GlassCard>
            </Link>
          ))}
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* LIVE CAMERA COMPUTER VISION SECTION */}
      {/* ------------------------------------------------------------------ */}
      <section id="live-vision" className="py-20 px-6 sm:px-12 bg-white/40 border-y border-slate-200/60">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <Badge variant="success">OpenCV Quality Gates</Badge>
            <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Real-Time Live Camera Computer Vision
            </h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              Capture frames directly from your browser camera. The backend pipeline evaluates image blur via Laplacian variance, checks mean brightness exposure, filters low-quality frames, and streams predictions over WebSockets with temporal smoothing.
            </p>

            <ul className="space-y-3 text-xs text-slate-700">
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Session-isolated rolling temporal prediction smoother</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>ResNet18 Plant Disease Detection + PyTorch MobileNetV3 Pest Classification</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Automatic frame skipping for blurry or underexposed frames</span>
              </li>
            </ul>

            <Link to="/live">
              <Button variant="primary" size="md" icon={<Camera className="w-4 h-4" />}>
                Launch Live Camera Workspace
              </Button>
            </Link>
          </div>

          <GlassCard variant="strong" className="p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200/60 pb-3">
              <span className="text-xs font-bold text-slate-900 flex items-center gap-2">
                <Activity className="w-4 h-4 text-rose-600 animate-pulse" />
                Live Camera Feed (Simulation)
              </span>
              <Badge variant="success">WebSocket Connected</Badge>
            </div>
            <div className="aspect-video rounded-xl bg-slate-900 relative flex items-center justify-center overflow-hidden">
              <img
                src="/images/agriculture-hero-poster.webp"
                alt="Live Camera Frame"
                className="w-full h-full object-cover opacity-60"
              />
              <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-md px-3 py-1 rounded-lg text-[10px] text-emerald-400 font-mono">
                ● 10 FPS • Blur: 142.5 (Passed)
              </div>
              <div className="absolute bottom-3 left-3 right-3 bg-slate-900/85 backdrop-blur-md p-3 rounded-xl text-white flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold">Corn___healthy</p>
                  <p className="text-[10px] text-slate-400">Stable Prediction (Smoother Buffer: 5/5)</p>
                </div>
                <span className="text-sm font-bold text-emerald-400">92.4%</span>
              </div>
            </div>
          </GlassCard>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* WEATHER & MARKET INTELLIGENCE SIGNALS */}
      {/* ------------------------------------------------------------------ */}
      <section id="signals" className="py-20 px-6 sm:px-12 max-w-7xl mx-auto space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <Badge variant="info">Contextual Signals</Badge>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Weather, Mandi Prices & Crop Calendar
          </h2>
          <p className="text-sm text-slate-600">
            Real-time data feeds integrated with rule-based agronomic insights and time-series forecasting.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <GlassCard className="p-6 space-y-4">
            <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold">
              <CloudSun className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-900">Weather Intelligence</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Open-Meteo integration providing current conditions, 7-day hourly forecasts, and automated agricultural field-disruption signals.
            </p>
            <Link to="/weather" className="text-xs font-semibold text-primary-600 flex items-center gap-1 hover:underline">
              View Weather Forecast <ArrowRight className="w-3 h-3" />
            </Link>
          </GlassCard>

          <GlassCard className="p-6 space-y-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-900">Market Intelligence</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Government of India mandi observations, historical price series, and ETS/ARIMA price forecasts with actionable trading signals.
            </p>
            <Link to="/market" className="text-xs font-semibold text-primary-600 flex items-center gap-1 hover:underline">
              Explore Market Forecasts <ArrowRight className="w-3 h-3" />
            </Link>
          </GlassCard>

          <GlassCard className="p-6 space-y-4">
            <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold">
              <Calendar className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-900">Crop Calendar</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Stage timelines, sowing windows, growth stages, and recommended field operations calculated from sowing dates.
            </p>
            <Link to="/crop-calendar" className="text-xs font-semibold text-primary-600 flex items-center gap-1 hover:underline">
              View Crop Schedules <ArrowRight className="w-3 h-3" />
            </Link>
          </GlassCard>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* TRUST, TRANSPARENCY & SCOPE */}
      {/* ------------------------------------------------------------------ */}
      <section id="transparency" className="py-16 px-6 sm:px-12 bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4" /> Model Transparency & Scope
            </div>
            <h2 className="text-2xl font-bold tracking-tight">Honest Agricultural Decision Support</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs text-slate-300">
            <div className="p-4 rounded-xl bg-slate-800/80 border border-slate-700 space-y-2">
              <h4 className="font-bold text-white text-sm">Fertilizer Scope</h4>
              <p className="leading-relaxed">
                Fertilizer recommendations represent product formulation classification trained on Western Maharashtra agricultural data.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-800/80 border border-slate-700 space-y-2">
              <h4 className="font-bold text-white text-sm">Irrigation Persistence</h4>
              <p className="leading-relaxed">
                3-hour Soil Water Content evaluates ML predictions side-by-side with the persistence baseline benchmark.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-800/80 border border-slate-700 space-y-2">
              <h4 className="font-bold text-white text-sm">Soil Organic Carbon</h4>
              <p className="leading-relaxed">
                Soil analysis models are trained on the LUCAS European topsoil dataset and report 95% confidence bounds.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* CALL TO ACTION */}
      {/* ------------------------------------------------------------------ */}
      <section className="py-20 px-6 sm:px-12 max-w-5xl mx-auto text-center space-y-6">
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Ready to Enhance Your Agricultural Decisions?
        </h2>
        <p className="text-sm text-slate-600 max-w-2xl mx-auto">
          Access all 8 ML inference services, OpenCV camera inspection, weather, market forecasts, and crop calendars.
        </p>
        <div className="flex justify-center gap-4">
          <Link to="/dashboard">
            <Button size="lg" variant="primary" icon={<ArrowRight className="w-4 h-4" />}>
              Open AgriNexus-AI Dashboard
            </Button>
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
};
