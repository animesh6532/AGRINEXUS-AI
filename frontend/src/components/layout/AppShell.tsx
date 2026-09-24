import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { MobileNav } from './MobileNav';
import { Footer } from './Footer';

export const AppShell: React.FC = () => {
  return (
    <div className="flex min-h-screen bg-[#FAFBF7] text-[#162018] font-sans selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Left Navigation Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 pb-20 md:pb-0">
        <Topbar />
        <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-7xl w-full mx-auto space-y-8">
          <Outlet />
        </main>
        <Footer />
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileNav />
    </div>
  );
};
