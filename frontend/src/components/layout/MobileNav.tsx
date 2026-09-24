import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Sprout,
  Stethoscope,
  Camera,
  CloudSun,
  BarChart3,
  Menu,
  X,
  Bug,
  FlaskConical,
  Droplets,
  Mountain,
  TrendingUp,
  Calendar,
  History,
  User,
  Settings,
  ShieldCheck,
  LogOut
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useHealth } from '../../context/HealthContext';

export const MobileNav: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout } = useAuth();
  const { isModelSystemReady } = useHealth();

  const mainItems = [
    { path: '/dashboard', label: 'Home', icon: <LayoutDashboard className="w-5 h-5" /> },
    { path: '/crop', label: 'Crop', icon: <Sprout className="w-5 h-5" /> },
    { path: '/disease', label: 'Disease', icon: <Stethoscope className="w-5 h-5" /> },
    { path: '/live', label: 'Camera', icon: <Camera className="w-5 h-5" /> },
    { path: '/weather', label: 'Weather', icon: <CloudSun className="w-5 h-5" /> },
    { path: '/market', label: 'Market', icon: <BarChart3 className="w-5 h-5" /> },
  ];

  const drawerSections = [
    {
      title: 'FIELD INTELLIGENCE',
      items: [
        { path: '/crop', label: 'Crop Recommendation', icon: <Sprout className="w-4 h-4" /> },
        { path: '/disease', label: 'Plant Health Diagnostics', icon: <Stethoscope className="w-4 h-4" /> },
        { path: '/pest', label: 'Pest Intelligence', icon: <Bug className="w-4 h-4" /> },
        { path: '/fertilizer', label: 'Fertilizer Advisor', icon: <FlaskConical className="w-4 h-4" /> },
        { path: '/irrigation', label: 'Irrigation Predictor', icon: <Droplets className="w-4 h-4" /> },
        { path: '/soil', label: 'Soil Analysis', icon: <Mountain className="w-4 h-4" /> },
        { path: '/yield', label: 'Yield Forecasting', icon: <TrendingUp className="w-4 h-4" /> },
      ]
    },
    {
      title: 'SIGNALS & ACTIVITY',
      items: [
        { path: '/live', label: 'Camera Intelligence', icon: <Camera className="w-4 h-4" /> },
        { path: '/weather', label: 'Weather Telemetry', icon: <CloudSun className="w-4 h-4" /> },
        { path: '/market', label: 'Mandi Markets', icon: <BarChart3 className="w-4 h-4" /> },
        { path: '/crop-calendar', label: 'Crop Calendar', icon: <Calendar className="w-4 h-4" /> },
        { path: '/history', label: 'Analysis History', icon: <History className="w-4 h-4" /> },
      ]
    },
    {
      title: 'ACCOUNT',
      items: [
        { path: '/profile', label: 'Farmer Profile', icon: <User className="w-4 h-4" /> },
        { path: '/settings', label: 'Platform Settings', icon: <Settings className="w-4 h-4" /> },
      ]
    }
  ];

  return (
    <>
      {/* Bottom Floating Bar */}
      <nav className="fixed bottom-0 left-0 right-0 h-16 bg-[#0B1C10]/95 backdrop-blur-xl border-t border-white/10 flex items-center justify-around z-40 md:hidden px-3">
        {mainItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 py-1 px-2 text-[10px] font-semibold transition-all ${
                isActive ? 'text-[#D4E768]' : 'text-white/60 hover:text-white'
              }`
            }
          >
            {item.icon}
            <span>{item.label}</span>
          </NavLink>
        ))}

        <button
          onClick={() => setIsOpen(true)}
          className="flex flex-col items-center gap-1 py-1 px-2 text-[10px] font-semibold text-white/60 hover:text-[#D4E768]"
        >
          <Menu className="w-5 h-5" />
          <span>More</span>
        </button>
      </nav>

      {/* Full Screen Premium Mobile Menu Drawer */}
      {isOpen && (
        <div className="fixed inset-0 bg-[#0B1C10] text-[#FAFBF7] z-50 overflow-y-auto p-6 md:hidden flex flex-col justify-between animate-fade-in">
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-white/10">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-extrabold text-sm">
                  AN
                </div>
                <div>
                  <h3 className="font-extrabold text-lg font-editorial text-white tracking-tight">AGRI NEXUS-AI</h3>
                  <p className="text-[10px] text-[#D4E768] font-bold tracking-widest uppercase">Intelligence Platform</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 rounded-full bg-white/10 text-white hover:bg-white/20"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Status */}
            <div className="p-3 rounded-2xl bg-[#112316] border border-white/10 flex items-center justify-between text-xs">
              <span className="flex items-center gap-2 text-white/80">
                <ShieldCheck className="w-4 h-4 text-[#D4E768]" /> System Readiness
              </span>
              <span className="font-bold text-[#D4E768]">
                {isModelSystemReady ? '● Systems operational' : '● System Degraded'}
              </span>
            </div>

            {/* Nav Groups */}
            <div className="space-y-6">
              {drawerSections.map((sec, i) => (
                <div key={i} className="space-y-2">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                    {sec.title}
                  </span>
                  <div className="grid grid-cols-1 gap-1">
                    {sec.items.map((it) => (
                      <NavLink
                        key={it.path}
                        to={it.path}
                        onClick={() => setIsOpen(false)}
                        className={({ isActive }) =>
                          `flex items-center gap-3 p-3 rounded-2xl text-xs font-semibold ${
                            isActive ? 'bg-[#112316] text-[#D4E768] border border-[#D4E768]/30' : 'text-white/80 hover:bg-white/5'
                          }`
                        }
                      >
                        {it.icon}
                        <span>{it.label}</span>
                      </NavLink>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Footer User Profile */}
          <div className="pt-6 border-t border-white/10 space-y-3 mt-8">
            {user && (
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-extrabold text-sm">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-bold text-white">{user.name}</p>
                  <p className="text-xs text-white/60">{user.email}</p>
                </div>
              </div>
            )}
            <button
              onClick={() => {
                logout();
                setIsOpen(false);
              }}
              className="w-full flex items-center justify-center gap-2 p-3 rounded-2xl bg-rose-950/40 text-rose-300 font-semibold text-xs border border-rose-500/20"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out of Platform</span>
            </button>
          </div>
        </div>
      )}
    </>
  );
};
