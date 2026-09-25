import React from 'react';
import { Settings as SettingsIcon, ShieldCheck, Cpu, RefreshCw, Layers } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { useHealth } from '../context/HealthContext';

export const SettingsPage: React.FC = () => {
  const { isApiConnected, isModelSystemReady, modelStatus, refreshHealth, lastChecked } = useHealth();

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="ACCOUNT"
        title="Platform Settings & System Status"
        description="FastAPI backend connectivity, model registry readiness, liveness health checks, and platform operational preferences."
        imageSrc="/images/hero-farmland.webp"
      >
        <Button
          variant="lime"
          size="sm"
          onClick={refreshHealth}
          icon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Re-check System Health
        </Button>
      </AgriculturalPageHero>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Connection Status Card (6 Cols) */}
        <div className="lg:col-span-6 space-y-6">
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
            <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-4">
              <ShieldCheck className="w-5 h-5 text-[#2F6B3C]" />
              <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                Backend API Connection
              </h3>
            </div>

            <div className="space-y-3 text-xs font-sans">
              <div className="flex justify-between items-center p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[#536056] font-semibold">FastAPI Host URL</span>
                <span className="font-mono font-extrabold text-[#0B1C10]">http://127.0.0.1:8000</span>
              </div>

              <div className="flex justify-between items-center p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[#536056] font-semibold">API Liveness Health</span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                  isApiConnected
                    ? 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                    : 'bg-rose-500/10 text-rose-800 border border-rose-500/20'
                }`}>
                  {isApiConnected ? '● Connected (200 OK)' : '● Offline'}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[#536056] font-semibold">Model System Overall</span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                  isModelSystemReady
                    ? 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                    : 'bg-amber-500/10 text-amber-800 border border-amber-500/20'
                }`}>
                  {isModelSystemReady ? '● 8/8 Ready' : '● System Degraded'}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                <span className="text-[#536056] font-semibold">Last Verified Check</span>
                <span className="text-[#0B1C10] font-mono font-bold">
                  {lastChecked ? lastChecked.toLocaleTimeString() : 'Initial Verification'}
                </span>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Model Registry Status Card (6 Cols) */}
        <div className="lg:col-span-6 space-y-6">
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
            <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-4">
              <Cpu className="w-5 h-5 text-[#2F6B3C]" />
              <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                Model Registry Artifact Status
              </h3>
            </div>

            {modelStatus && modelStatus.details ? (
              <div className="space-y-2.5 text-xs max-h-72 overflow-y-auto pr-1">
                {Object.entries(modelStatus.details).map(([key, detail]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between p-3.5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]"
                  >
                    <span className="font-bold text-[#0B1C10] capitalize">{key.replace('_', ' ')}</span>
                    <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase ${
                      detail.status === 'READY'
                        ? 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                        : 'bg-amber-500/10 text-amber-800'
                    }`}>
                      {detail.status} ({detail.framework})
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-[#536056] italic">
                Verifying backend model artifacts...
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
