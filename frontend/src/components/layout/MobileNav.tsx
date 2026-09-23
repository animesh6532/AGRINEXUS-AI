import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Sprout,
  Stethoscope,
  Camera,
  CloudSun,
  BarChart3
} from 'lucide-react';

export const MobileNav: React.FC = () => {
  const items = [
    { path: '/dashboard', label: 'Home', icon: <LayoutDashboard className="w-5 h-5" /> },
    { path: '/crop', label: 'Crop', icon: <Sprout className="w-5 h-5" /> },
    { path: '/disease', label: 'Disease', icon: <Stethoscope className="w-5 h-5" /> },
    { path: '/live', label: 'Camera', icon: <Camera className="w-5 h-5" /> },
    { path: '/weather', label: 'Weather', icon: <CloudSun className="w-5 h-5" /> },
    { path: '/market', label: 'Market', icon: <BarChart3 className="w-5 h-5" /> },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 h-16 glass-panel-strong border-t border-slate-200/80 flex items-center justify-around z-40 md:hidden px-2">
      {items.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) =>
            `flex flex-col items-center gap-1 py-1 px-2 text-[10px] font-medium transition-colors ${
              isActive ? 'text-primary-600 font-bold' : 'text-slate-500 hover:text-slate-900'
            }`
          }
        >
          {item.icon}
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
};
