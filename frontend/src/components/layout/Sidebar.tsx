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
import { Badge } from '../ui/Badge';

export const Sidebar: React.FC = () => {
  const { logout, user } = useAuth();
  const { isModelSystemReady } = useHealth();

  const navGroups = [
    {
      title: 'Overview',
      items: [
        { path: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
      ]
    },
    {
      title: 'ML Intelligence',
      items: [
        { path: '/crop', label: 'Crop Recommendation', icon: <Sprout className="w-4 h-4" /> },
        { path: '/disease', label: 'Disease Detection', icon: <Stethoscope className="w-4 h-4" /> },
        { path: '/pest', label: 'Pest Intelligence', icon: <Bug className="w-4 h-4" /> },
        { path: '/fertilizer', label: 'Fertilizer Advisor', icon: <FlaskConical className="w-4 h-4" /> },
        { path: '/irrigation', label: 'Irrigation Predictor', icon: <Droplets className="w-4 h-4" /> },
        { path: '/soil', label: 'Soil Analysis', icon: <Mountain className="w-4 h-4" /> },
        { path: '/yield', label: 'Yield Prediction', icon: <TrendingUp className="w-4 h-4" /> },
      ]
    },
    {
      title: 'Computer Vision',
      items: [
        { path: '/live', label: 'Live Camera Vision', icon: <Camera className="w-4 h-4" /> },
      ]
    },
    {
      title: 'Agronomic Insights',
      items: [
        { path: '/weather', label: 'Weather Intelligence', icon: <CloudSun className="w-4 h-4" /> },
        { path: '/market', label: 'Market Intelligence', icon: <BarChart3 className="w-4 h-4" /> },
        { path: '/crop-calendar', label: 'Crop Calendar', icon: <Calendar className="w-4 h-4" /> },
        { path: '/history', label: 'Analysis History', icon: <History className="w-4 h-4" /> },
      ]
    },
    {
      title: 'System & Profile',
      items: [
        { path: '/profile', label: 'Farmer Profile', icon: <User className="w-4 h-4" /> },
        { path: '/settings', label: 'Platform Settings', icon: <SettingsIcon className="w-4 h-4" /> },
      ]
    }
  ];

  return (
    <aside className="w-64 shrink-0 glass-panel-strong h-screen sticky top-0 flex flex-col justify-between p-4 border-r border-slate-200/80 hidden md:flex z-30 overflow-y-auto">
      <div className="space-y-6">
        {/* Brand Header */}
        <div className="flex items-center gap-3 px-2 py-1">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-agri-500 to-primary-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
            🌱
          </div>
          <div>
            <h1 className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-slate-900 via-primary-700 to-agri-700 bg-clip-text text-transparent">
              AgriNexus-AI
            </h1>
            <p className="text-[10px] text-slate-500 font-medium tracking-wide uppercase">
              Agricultural Platform
            </p>
          </div>
        </div>

        {/* Model Status Badge */}
        <div className="px-2">
          <div className="p-2.5 rounded-xl bg-slate-50/80 border border-slate-200/60 flex items-center justify-between">
            <span className="text-xs text-slate-600 font-medium flex items-center gap-1.5">
              {isModelSystemReady ? (
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
              )}
              System Status
            </span>
            <Badge variant={isModelSystemReady ? 'success' : 'warning'} dot>
              {isModelSystemReady ? '8/8 Ready' : 'Degraded'}
            </Badge>
          </div>
        </div>

        {/* Navigation Group Links */}
        <nav className="space-y-5">
          {navGroups.map((group, idx) => (
            <div key={idx} className="space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3 block">
                {group.title}
              </span>
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-primary-600 text-white shadow-md font-semibold'
                        : 'text-slate-600 hover:bg-white/80 hover:text-slate-900'
                    }`
                  }
                >
                  {item.icon}
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </div>

      {/* Footer / User Profile & Logout */}
      <div className="pt-4 border-t border-slate-200/60 space-y-3">
        {user && (
          <div className="flex items-center gap-3 px-2 py-1">
            <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-xs">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-slate-900 truncate">{user.name}</p>
              <p className="text-[10px] text-slate-500 truncate">{user.email}</p>
            </div>
          </div>
        )}
        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-medium text-rose-600 hover:bg-rose-50 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
