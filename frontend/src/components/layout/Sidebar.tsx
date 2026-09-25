import React, { useEffect } from 'react';
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
  ShieldAlert,
  PanelLeftClose,
  PanelLeft,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useHealth } from '../../context/HealthContext';
import { LocationBadge } from '../location/LocationBadge';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const { logout, user } = useAuth();
  const { isModelSystemReady } = useHealth();

  // Keyboard shortcut Ctrl+B / Cmd+B to toggle sidebar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        onToggle();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onToggle]);

  const navGroups = [
    {
      title: 'OVERVIEW',
      items: [
        { path: '/dashboard', label: 'Dashboard Overview', shortLabel: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4 shrink-0" /> },
      ],
    },
    {
      title: 'FIELD INTELLIGENCE',
      items: [
        { path: '/crop', label: 'Crop Recommendation', shortLabel: 'Crop', icon: <Sprout className="w-4 h-4 shrink-0" /> },
        { path: '/disease', label: 'Plant Health Diagnostics', shortLabel: 'Disease', icon: <Stethoscope className="w-4 h-4 shrink-0" /> },
        { path: '/pest', label: 'Pest Intelligence', shortLabel: 'Pest', icon: <Bug className="w-4 h-4 shrink-0" /> },
        { path: '/fertilizer', label: 'Fertilizer Advisor', shortLabel: 'Fertilizer', icon: <FlaskConical className="w-4 h-4 shrink-0" /> },
        { path: '/irrigation', label: 'Irrigation Predictor', shortLabel: 'Irrigation', icon: <Droplets className="w-4 h-4 shrink-0" /> },
        { path: '/soil', label: 'Soil Analysis', shortLabel: 'Soil', icon: <Mountain className="w-4 h-4 shrink-0" /> },
        { path: '/yield', label: 'Yield Forecasting', shortLabel: 'Yield', icon: <TrendingUp className="w-4 h-4 shrink-0" /> },
      ],
    },
    {
      title: 'LIVE VISION',
      items: [
        { path: '/live', label: 'Camera Intelligence', shortLabel: 'Live Camera', icon: <Camera className="w-4 h-4 shrink-0" /> },
      ],
    },
    {
      title: 'FIELD SIGNALS',
      items: [
        { path: '/weather', label: 'Weather Telemetry', shortLabel: 'Weather', icon: <CloudSun className="w-4 h-4 shrink-0" /> },
        { path: '/market', label: 'Mandi Markets', shortLabel: 'Market', icon: <BarChart3 className="w-4 h-4 shrink-0" /> },
        { path: '/crop-calendar', label: 'Crop Calendar', shortLabel: 'Calendar', icon: <Calendar className="w-4 h-4 shrink-0" /> },
      ],
    },
    {
      title: 'ACTIVITY',
      items: [
        { path: '/history', label: 'Intelligence History', shortLabel: 'History', icon: <History className="w-4 h-4 shrink-0" /> },
      ],
    },
    {
      title: 'ACCOUNT',
      items: [
        { path: '/profile', label: 'Farmer Profile', shortLabel: 'Profile', icon: <User className="w-4 h-4 shrink-0" /> },
        { path: '/settings', label: 'Platform Settings', shortLabel: 'Settings', icon: <SettingsIcon className="w-4 h-4 shrink-0" /> },
      ],
    },
  ];

  return (
    <aside
      className={`shrink-0 bg-[#0B1C10] text-[#FAFBF7] h-screen sticky top-0 flex flex-col justify-between border-r border-[#E2E7DA]/10 hidden md:flex z-40 overflow-y-auto selection:bg-[#D4E768] selection:text-[#0B1C10] transition-all duration-300 ease-in-out ${
        collapsed ? 'w-20 p-3' : 'w-64 p-5'
      }`}
    >
      <div className="space-y-5">
        {/* Header Branding + Toggle Button */}
        <div className={`pt-1 pb-3 border-b border-white/10 flex items-center ${collapsed ? 'justify-center flex-col gap-3' : 'justify-between'}`}>
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-xl bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-extrabold text-sm tracking-tighter shadow-sm shrink-0">
              AN
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <h1 className="font-extrabold text-base tracking-tight font-editorial text-[#FAFBF7] truncate">
                  AGRI NEXUS-AI
                </h1>
                <p className="text-[9px] text-[#D4E768] font-bold tracking-widest uppercase truncate">
                  Intelligence Platform
                </p>
              </div>
            )}
          </div>

          <button
            onClick={onToggle}
            className="p-1.5 rounded-xl text-white/60 hover:text-[#D4E768] hover:bg-white/10 transition-colors"
            title={collapsed ? 'Expand sidebar (Ctrl+B)' : 'Collapse sidebar (Ctrl+B)'}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <PanelLeft className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
          </button>
        </div>

        {/* Sidebar Location Entry (Section 60, 61, 62) */}
        <div className="px-0.5">
          <LocationBadge variant={collapsed ? 'sidebar-collapsed' : 'sidebar'} />
        </div>

        {/* System Health Status Indicator */}
        <div className="px-0.5">
          {collapsed ? (
            <div
              className="w-10 h-10 mx-auto rounded-2xl bg-[#112316] border border-white/10 flex items-center justify-center"
              title={`System Status: ${isModelSystemReady ? 'Operational' : 'Degraded'}`}
            >
              <div className={`w-2.5 h-2.5 rounded-full ${isModelSystemReady ? 'bg-[#D4E768]' : 'bg-amber-400'}`} />
            </div>
          ) : (
            <div className="p-3 rounded-2xl bg-[#112316] border border-white/10 flex items-center justify-between">
              <span className="text-xs text-white/80 font-medium flex items-center gap-2">
                {isModelSystemReady ? (
                  <ShieldCheck className="w-3.5 h-3.5 text-[#D4E768]" />
                ) : (
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                )}
                <span>System Status</span>
              </span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  isModelSystemReady
                    ? 'bg-[#D4E768]/20 text-[#D4E768] border border-[#D4E768]/30'
                    : 'bg-amber-500/20 text-amber-300'
                }`}
              >
                {isModelSystemReady ? '● Operational' : '● Degraded'}
              </span>
            </div>
          )}
        </div>

        {/* Navigation Links */}
        <nav className="space-y-4">
          {navGroups.map((group, idx) => (
            <div key={idx} className="space-y-1">
              {!collapsed && (
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] px-3 block truncate">
                  {group.title}
                </span>
              )}
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  title={collapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-2xl text-xs font-medium transition-all duration-200 relative group ${
                      collapsed ? 'justify-center' : ''
                    } ${
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
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </div>

      {/* User Profile & Logout */}
      <div className="pt-3 border-t border-white/10 space-y-2 mt-3">
        {user && (
          <div className={`flex items-center gap-3 px-1 py-1 ${collapsed ? 'justify-center' : ''}`}>
            <div className="w-8 h-8 rounded-full bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-extrabold text-xs shrink-0 shadow-sm">
              {user.name.charAt(0).toUpperCase()}
            </div>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-[#FAFBF7] truncate">{user.name}</p>
                <p className="text-[10px] text-white/50 truncate">{user.email}</p>
              </div>
            )}
          </div>
        )}
        <button
          onClick={logout}
          title={collapsed ? 'Sign Out' : undefined}
          className={`w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-rose-400 hover:bg-rose-950/40 transition-colors ${
            collapsed ? 'justify-center' : 'justify-center'
          }`}
        >
          <LogOut className="w-3.5 h-3.5 shrink-0" />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </div>
    </aside>
  );
};
