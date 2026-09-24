import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Menu, X, Leaf, Sparkles, Activity } from 'lucide-react';
import { useHealth } from '../../context/HealthContext';

export const Navbar: React.FC = () => {
  const { isApiConnected, isModelSystemReady, modelStatus } = useHealth();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 30);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const totalServices = modelStatus?.models ? Object.keys(modelStatus.models).length : 8;
  const readyServices = modelStatus?.models 
    ? Object.values(modelStatus.models).filter((m: any) => m.status === 'loaded' || m.status === 'healthy' || m === 'ready').length
    : (isModelSystemReady ? 8 : 0);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-4 sm:px-8 pt-4 pb-2 transition-all duration-300 pointer-events-none">
      <div
        className={`max-w-7xl mx-auto pointer-events-auto rounded-full transition-all duration-500 ${
          scrolled
            ? 'agri-nav-floating py-3 px-6 shadow-xl border border-[#D4E768]/30 bg-[#FAFBF7]/90 backdrop-blur-xl'
            : 'bg-[#0B1C10]/60 backdrop-blur-md py-4 px-6 sm:px-8 border border-white/10 text-white'
        } flex items-center justify-between`}
      >
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center shadow-lg transition-transform group-hover:scale-105 ${
            scrolled ? 'bg-[#0B1C10] text-[#D4E768]' : 'bg-[#D4E768] text-[#0B1C10]'
          }`}>
            <Leaf className="w-5 h-5 fill-current" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className={`font-extrabold text-lg tracking-tight font-sans ${
                scrolled ? 'text-[#0B1C10]' : 'text-white'
              }`}>
                AgriNexus<span className={scrolled ? 'text-[#5E9F48]' : 'text-[#D4E768]'}>-AI</span>
              </span>
              <span className={`hidden sm:inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest px-2.5 py-0.5 rounded-full ${
                scrolled 
                  ? 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#8CBF68]/30' 
                  : 'bg-white/10 text-[#D4E768] border border-white/15'
              }`}>
                <Sparkles className="w-2.5 h-2.5" /> Intelligence
              </span>
            </div>
            <span className={`text-[9px] font-semibold tracking-widest uppercase ${
              scrolled ? 'text-[#39463B]' : 'text-gray-300'
            }`}>
              Agricultural Platform
            </span>
          </div>
        </Link>

        {/* Center Editorial Links */}
        <div className={`hidden lg:flex items-center gap-8 text-xs font-bold uppercase tracking-wider ${
          scrolled ? 'text-[#162018]' : 'text-gray-200'
        }`}>
          <a href="#platform" className="hover:text-[#D4E768] transition-colors py-1">
            Platform
          </a>
          <a href="#intelligence" className="hover:text-[#D4E768] transition-colors py-1">
            Intelligence
          </a>
          <a href="#live-vision" className="hover:text-[#D4E768] transition-colors py-1">
            Live AI
          </a>
          <a href="#insights" className="hover:text-[#D4E768] transition-colors py-1">
            Insights
          </a>
          <a href="#transparency" className="hover:text-[#D4E768] transition-colors py-1">
            About
          </a>
        </div>

        {/* Right Action & Real Health Status */}
        <div className="hidden sm:flex items-center gap-4">
          <div className={`hidden xl:flex items-center gap-2 text-[11px] font-semibold px-3 py-1.5 rounded-full ${
            scrolled ? 'bg-[#EEF3E8] text-[#162018] border border-[#D6E4CC]' : 'bg-white/10 text-gray-200 border border-white/15'
          }`}>
            <span
              className={`w-2 h-2 rounded-full ${
                isApiConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
              }`}
            />
            <span>
              {isApiConnected ? `${readyServices}/${totalServices} Services Online` : 'Backend Standby'}
            </span>
          </div>

          <Link
            to="/login"
            className={`text-xs font-bold tracking-wide uppercase px-3 py-2 transition-colors ${
              scrolled ? 'text-[#162018] hover:text-[#2F6B3C]' : 'text-white hover:text-[#D4E768]'
            }`}
          >
            Sign In
          </Link>

          <Link
            to="/dashboard"
            className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-bold tracking-wide transition-all transform hover:-translate-y-0.5 shadow-md ${
              scrolled 
                ? 'bg-[#0B1C10] text-[#D4E768] hover:bg-[#112316] hover:shadow-lg' 
                : 'bg-[#D4E768] text-[#0B1C10] hover:bg-[#E2F165] hover:shadow-xl'
            }`}
          >
            <span>Get Started</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Mobile Toggle Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className={`lg:hidden p-2 rounded-full transition-colors ${
            scrolled ? 'text-[#162018] hover:bg-[#EEF3E8]' : 'text-white hover:bg-white/10'
          }`}
          aria-label="Toggle Navigation Menu"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden pointer-events-auto mt-3 max-w-7xl mx-auto bg-[#0B1C10] text-white border border-[#D4E768]/30 rounded-3xl p-6 shadow-2xl space-y-5">
          <div className="flex flex-col space-y-3 text-sm font-bold tracking-wide">
            <a
              href="#platform"
              onClick={() => setMobileMenuOpen(false)}
              className="px-4 py-2.5 rounded-xl hover:bg-white/10 hover:text-[#D4E768] transition-colors"
            >
              Platform Overview
            </a>
            <a
              href="#intelligence"
              onClick={() => setMobileMenuOpen(false)}
              className="px-4 py-2.5 rounded-xl hover:bg-white/10 hover:text-[#D4E768] transition-colors"
            >
              Intelligence Suite
            </a>
            <a
              href="#live-vision"
              onClick={() => setMobileMenuOpen(false)}
              className="px-4 py-2.5 rounded-xl hover:bg-white/10 hover:text-[#D4E768] transition-colors"
            >
              Live AI Vision
            </a>
            <a
              href="#insights"
              onClick={() => setMobileMenuOpen(false)}
              className="px-4 py-2.5 rounded-xl hover:bg-white/10 hover:text-[#D4E768] transition-colors"
            >
              Field & Soil Insights
            </a>
            <a
              href="#transparency"
              onClick={() => setMobileMenuOpen(false)}
              className="px-4 py-2.5 rounded-xl hover:bg-white/10 hover:text-[#D4E768] transition-colors"
            >
              Model Transparency
            </a>
          </div>

          <div className="pt-4 border-t border-white/10 flex flex-col gap-3">
            <Link
              to="/dashboard"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full text-center py-3 rounded-full bg-[#D4E768] text-[#0B1C10] text-sm font-bold shadow-lg"
            >
              Get Started with AgriNexus-AI
            </Link>
            <Link
              to="/login"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full text-center py-2.5 rounded-full border border-white/20 text-white text-sm font-semibold hover:border-[#D4E768]"
            >
              Sign In to Account
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
};
