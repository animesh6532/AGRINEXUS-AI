import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Camera,
  Sparkles,
  Leaf,
  Droplets,
  CheckCircle2,
  ChevronDown,
  Activity,
  Layers,
  ShieldCheck
} from 'lucide-react';
import { useHealth } from '../../context/HealthContext';

export const HeroSection: React.FC = () => {
  const { isApiConnected, isModelSystemReady, modelStatus } = useHealth();
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [videoLoaded, setVideoLoaded] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);
    const handleChange = () => setPrefersReducedMotion(mediaQuery.matches);
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return (
    <section id="platform" className="relative min-h-screen pt-32 lg:pt-40 pb-20 px-6 sm:px-12 flex flex-col justify-between overflow-hidden bg-[#0B1C10]">
      {/* Background Video / Reduced Motion Poster Fallback */}
      {!prefersReducedMotion ? (
        <video
          autoPlay
          muted
          loop
          playsInline
          poster="/images/hero-poster.webp"
          onLoadedData={() => setVideoLoaded(true)}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-1000 ${
            videoLoaded ? 'opacity-40' : 'opacity-20'
          }`}
        >
          <source src="/videos/agrinexus-hero.mp4" type="video/mp4" />
          <source src="/videos/agrinexus-hero.webm" type="video/webm" />
        </video>
      ) : (
        <img
          src="/images/hero-poster.webp"
          alt="Cinematic Farmland Aerial View"
          className="hero-video-poster absolute inset-0 w-full h-full object-cover opacity-35"
        />
      )}

      {/* Deep Natural Dark Green Atmospheric Overlays */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#0B1C10] via-[#0B1C10]/80 to-[#0B1C10]/50 z-10 pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10] via-transparent to-[#0B1C10]/70 z-10 pointer-events-none" />

      {/* Main Editorial Hero Content */}
      <div className="relative z-20 max-w-7xl mx-auto w-full pt-6 lg:pt-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-start">
          
          {/* Left Column: Oversized Editorial Typography & Core CTA (8 Cols) */}
          <div className="lg:col-span-8 space-y-8 text-left">
            
            {/* Eyebrow Pill */}
            <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-white/10 border border-[#D4E768]/30 backdrop-blur-md text-xs font-bold uppercase tracking-widest text-[#D4E768]">
              <Sparkles className="w-4 h-4 text-[#D4E768] animate-pulse" />
              <span>VerdaAgro-Inspired Agricultural Intelligence</span>
            </div>

            {/* VerdaAgro Oversized Typography */}
            <h1 className="hero-heading text-white tracking-tight leading-[0.96]">
              Intelligence <br />
              <span className="text-[#D4E768] italic font-serif font-normal">Rooted in the Field.</span>
            </h1>

            {/* Editorial Description */}
            <p className="text-lg sm:text-2xl text-gray-200/90 max-w-2xl leading-relaxed font-normal">
              AgriNexus-AI bridges raw field telemetry with actionable agronomic intelligence — connecting crop selection, plant health, subsurface soil moisture, pest risks, yield forecasting, and market dynamics into a unified visual experience.
            </p>

            {/* Primary Action Group */}
            <div className="flex flex-wrap items-center gap-4 pt-4">
              <Link
                to="/dashboard"
                className="btn-agri-lime text-base shadow-2xl hover:scale-105"
              >
                <span>Explore Platform</span>
                <ArrowRight className="w-5 h-5" />
              </Link>

              <Link
                to="/live"
                className="btn-agri-ghost text-base backdrop-blur-md hover:scale-105"
              >
                <Camera className="w-5 h-5 text-[#D4E768]" />
                <span>Launch Live AI Vision</span>
              </Link>
            </div>

            {/* Platform Facts Bar */}
            <div className="pt-8 flex flex-wrap items-center gap-6 text-xs font-semibold text-gray-300 border-t border-white/10">
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${isApiConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                <span className="text-white font-bold">
                  {isApiConnected ? '8 Inference Services Ready' : 'System Standby'}
                </span>
              </div>
              <span className="text-white/20">•</span>
              <span className="flex items-center gap-1.5 text-gray-300">
                <Layers className="w-3.5 h-3.5 text-[#D4E768]" /> 7 Frozen ML Artifacts
              </span>
              <span className="text-white/20">•</span>
              <span className="flex items-center gap-1.5 text-gray-300">
                <ShieldCheck className="w-3.5 h-3.5 text-[#D4E768]" /> OpenCV Computer Vision
              </span>
            </div>

          </div>

          {/* Right Column: Typographic Platform Fact & Floating Intelligence Cards (4 Cols) */}
          <div className="lg:col-span-4 relative flex flex-col justify-between h-full space-y-6 pt-4 lg:pt-0">
            
            {/* Massive Typographic Statistic (Inspired by VerdaAgro Reference) */}
            <div className="bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-xl hover:border-[#D4E768]/40 transition-all text-left">
              <div className="text-xs font-bold uppercase tracking-widest text-[#D4E768] mb-2 flex items-center justify-between">
                <span>Frozen ML Artifacts</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-white/10 text-gray-300 font-mono">Verifiable ML</span>
              </div>
              <div className="text-7xl sm:text-8xl font-black text-white tracking-tighter font-sans leading-none">
                07
              </div>
              <p className="text-xs text-gray-300 mt-4 leading-relaxed">
                Deterministic inference models trained on specialized agronomic benchmarks, including ExtraTrees, ResNet18, XGBoost, and temporal smoothing.
              </p>
            </div>

            {/* Floating Intelligence Elements (Small Compact Pills) */}
            <div className="space-y-3">
              
              {/* Card 1: Crop Intelligence */}
              <div className="agri-glass-floating p-4 rounded-2xl flex items-center justify-between text-left transform transition-transform hover:translate-x-2">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-[#D4E768]/20 text-[#D4E768] flex items-center justify-center">
                    <Leaf className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-[10px] font-extrabold uppercase tracking-wider text-[#D4E768]">CROP INTELLIGENCE</div>
                    <div className="text-xs font-bold text-white">Optimal Crop Profile</div>
                  </div>
                </div>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-white/10 text-gray-300">
                  Sample
                </span>
              </div>

              {/* Card 2: Live AI */}
              <div className="agri-glass-floating p-4 rounded-2xl flex items-center justify-between text-left transform transition-transform hover:translate-x-2">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                    <Camera className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-400">LIVE AI VISION</div>
                    <div className="text-xs font-bold text-white">Camera Ready • Quality Passed</div>
                  </div>
                </div>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-emerald-400/20 text-emerald-300">
                  Active
                </span>
              </div>

              {/* Card 3: Soil Moisture */}
              <div className="agri-glass-floating p-4 rounded-2xl flex items-center justify-between text-left transform transition-transform hover:translate-x-2">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center">
                    <Droplets className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-[10px] font-extrabold uppercase tracking-wider text-sky-400">SOIL MOISTURE</div>
                    <div className="text-xs font-bold text-white">Water Content Baseline</div>
                  </div>
                </div>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-white/10 text-gray-300">
                  Forecast
                </span>
              </div>

            </div>

          </div>

        </div>
      </div>

      {/* Floating Hero Service Pills (Bottom Hero Bar inspired by VerdaAgro) */}
      <div className="relative z-20 max-w-7xl mx-auto w-full pt-12">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          
          <Link
            to="/crop"
            className="group p-5 rounded-2xl bg-white/5 border border-white/10 hover:border-[#D4E768]/50 hover:bg-white/10 transition-all backdrop-blur-md text-left flex items-center justify-between"
          >
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-[#D4E768] group-hover:text-white transition-colors">
                Crop Intelligence
              </div>
              <div className="text-sm font-semibold text-gray-200 mt-0.5">
                Explore crop recommendations
              </div>
            </div>
            <div className="w-8 h-8 rounded-full bg-white/10 text-[#D4E768] flex items-center justify-center group-hover:bg-[#D4E768] group-hover:text-[#0B1C10] transition-colors">
              <ArrowRight className="w-4 h-4" />
            </div>
          </Link>

          <Link
            to="/disease"
            className="group p-5 rounded-2xl bg-white/5 border border-white/10 hover:border-[#D4E768]/50 hover:bg-white/10 transition-all backdrop-blur-md text-left flex items-center justify-between"
          >
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-[#D4E768] group-hover:text-white transition-colors">
                Plant Health
              </div>
              <div className="text-sm font-semibold text-gray-200 mt-0.5">
                Analyze a leaf & diagnostics
              </div>
            </div>
            <div className="w-8 h-8 rounded-full bg-white/10 text-[#D4E768] flex items-center justify-center group-hover:bg-[#D4E768] group-hover:text-[#0B1C10] transition-colors">
              <ArrowRight className="w-4 h-4" />
            </div>
          </Link>

          <Link
            to="/live"
            className="group p-5 rounded-2xl bg-white/5 border border-white/10 hover:border-[#D4E768]/50 hover:bg-white/10 transition-all backdrop-blur-md text-left flex items-center justify-between"
          >
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-[#D4E768] group-hover:text-white transition-colors">
                Live AI Camera
              </div>
              <div className="text-sm font-semibold text-gray-200 mt-0.5">
                Inspect field in real-time
              </div>
            </div>
            <div className="w-8 h-8 rounded-full bg-white/10 text-[#D4E768] flex items-center justify-center group-hover:bg-[#D4E768] group-hover:text-[#0B1C10] transition-colors">
              <ArrowRight className="w-4 h-4" />
            </div>
          </Link>

        </div>
      </div>

      {/* Scroll Chevron */}
      <div className="relative z-20 pt-8 flex justify-center">
        <a href="#intro" className="flex flex-col items-center gap-1 text-gray-400 hover:text-[#D4E768] transition-colors">
          <span className="text-[10px] uppercase font-bold tracking-widest">Scroll Down</span>
          <ChevronDown className="w-4 h-4 animate-bounce text-[#D4E768]" />
        </a>
      </div>
    </section>
  );
};
