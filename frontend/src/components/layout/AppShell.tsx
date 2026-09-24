import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { MobileNav } from './MobileNav';
import { Footer } from './Footer';
import { LocationPicker } from '../location/LocationPicker';

const SIDEBAR_COLLAPSED_KEY = 'agrinexus.sidebar.collapsed';

export const AppShell: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
      return saved === 'true';
    } catch {
      return false;
    }
  });

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(next));
      } catch {
        // Ignore storage error
      }
      return next;
    });
  };

  return (
    <div className="flex min-h-screen bg-[#FAFBF7] text-[#162018] font-sans selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Left Navigation Sidebar */}
      <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 pb-20 md:pb-0 transition-all duration-300">
        <Topbar />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1600px] w-full mx-auto space-y-8">
          <Outlet />
        </main>
        <Footer />
      </div>

      {/* Global Location Picker Modal */}
      <LocationPicker />

      {/* Mobile Bottom Navigation */}
      <MobileNav />
    </div>
  );
};
