import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
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
  History,
  User,
  Settings as SettingsIcon,
  LogOut,
  ShieldCheck,
  ShieldAlert
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useHealth } from '../../context/HealthContext';

export const Sidebar: React.FC = () => {
  const { logout, user } = useAuth();
  const { isModelSystemReady } = useHealth();

  const navGroups = [
    {
      title: 'OVERVIEW',
      items: [
        { path: '/dashboard', label: 'Dashboard Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
      ]
    },
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
      title: 'LIVE VISION',
      items: [
        { path: '/live', label: 'Camera Intelligence', icon: <Camera className="w-4 h-4" /> },
      ]
    },
    {
      title: 'FIELD SIGNALS',
      items: [
        { path: '/weather', label: 'Weather Telemetry', icon: <CloudSun className="w-4 h-4" /> },
        { path: '/market', label: 'Mandi Markets', icon: <BarChart3 className="w-4 h-4" /> },
        { path: '/crop-calendar', label: 'Crop Calendar', icon: <Calendar className="w-4 h-4" /> },
      ]
    },
    {
      title: 'ACTIVITY',
      items: [
        { path: '/history', label: 'Intelligence History', icon: <History className="w-4 h-4" /> },
      ]
    },
    {
      title: 'ACCOUNT',
      items: [
        { path: '/profile', label: 'Farmer Profile', icon: <User className="w-4 h-4" /> },
        { path: '/settings', label: 'Platform Settings', icon: <SettingsIcon className="w-4 h-4" /> },
      ]
    }
  ];

  return (
    <aside className="w-64 shrink-0 bg-[#0B1C10] text-[#FAFBF7] h-screen sticky top-0 flex flex-col justify-between p-5 border-r border-[#E2E7DA]/10 hidden md:flex z-30 overflow-y-auto selection:bg-[#D4E768] selection:text-[#0B1C10]">
      <div className="space-y-6">
        {/* Brand Header */}
        <div className="px-2 pt-1 pb-2 border-b border-white/10 space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-black text-sm tracking-tighter shadow-sm">
              AN
            </div>
            <div>
              <h1 className="font-extrabold text-base tracking-tight font-editorial text-[#FAFBF7]">
                AGRI NEXUS-AI
              </h1>
              <p className="text-[9px] text-[#D4E768] font-bold tracking-widest uppercase">
                Intelligence Platform
              </p>
            </div>
          </div>
        </div>

        {/* Status Pill */}
        <div className="px-1">
          <div className="p-3 rounded-2xl bg-[#112316] border border-white/10 flex items-center justify-between">
            <span className="text-xs text-white/80 font-medium flex items-center gap-2">
              {isModelSystemReady ? (
                <ShieldCheck className="w-3.5 h-3.5 text-[#D4E768]" />
              ) : (
                <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              )}
              <span>System Status</span>
            </span>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
              isModelSystemReady ? 'bg-[#D4E768]/20 text-[#D4E768] border border-[#D4E768]/30' : 'bg-amber-500/20 text-amber-300'
            }`}>
              {isModelSystemReady ? '● Operational' : '● Degraded'}
            </span>
          </div>
        </div>

        {/* Navigation Group Links */}
        <nav className="space-y-5">
          {navGroups.map((group, idx) => (
            <div key={idx} className="space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] px-3 block">
                {group.title}
              </span>
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-2xl text-xs font-medium transition-all duration-200 relative group ${
                      isActive
                        ? 'bg-[#112316] text-[#D4E768] font-bold border border-[#D4E768]/30 shadow-sm'
                        : 'text-[#FAFBF7]/70 hover:bg-white/5 hover:text-[#FAFBF7]'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && (
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-[#D4E768] rounded-r-full" />
                      )}
                      <span className={isActive ? 'text-[#D4E768]' : 'text-white/50 group-hover:text-white/80'}>
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </div>

      {/* User Profile & Logout */}
      <div className="pt-4 border-t border-white/10 space-y-3 mt-4">
        {user && (
          <div className="flex items-center gap-3 px-2 py-1">
            <div className="w-8 h-8 rounded-full bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-extrabold text-xs">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-[#FAFBF7] truncate">{user.name}</p>
              <p className="text-[10px] text-white/50 truncate">{user.email}</p>
            </div>
          </div>
        )}
        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-rose-400 hover:bg-rose-950/40 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
