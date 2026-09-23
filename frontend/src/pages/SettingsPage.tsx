import React from 'react';
import { Settings as SettingsIcon, ShieldCheck, Cpu, RefreshCw } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useHealth } from '../context/HealthContext';

export const SettingsPage: React.FC = () => {
  const { isApiConnected, isModelSystemReady, modelStatus, refreshHealth, lastChecked } = useHealth();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center font-bold">
            <SettingsIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Platform Settings & System Status</h1>
            <p className="text-xs text-slate-500">
              FastAPI backend connection settings, model registry health, and accessibility preferences.
            </p>
          </div>
        </div>

        <Button variant="outline" size="sm" onClick={refreshHealth} icon={<RefreshCw className="w-3.5 h-3.5" />}>
          Re-check System Health
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Connection Status Card */}
        <GlassCard variant="strong" className="p-6 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" /> Backend API Connection
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between p-3 rounded-xl bg-white/70 border border-slate-100">
              <span className="text-slate-600">FastAPI Host URL</span>
              <span className="font-mono font-semibold text-slate-800">http://127.0.0.1:8000</span>
            </div>
            <div className="flex justify-between p-3 rounded-xl bg-white/70 border border-slate-100">
              <span className="text-slate-600">Liveness Endpoint</span>
              <Badge variant={isApiConnected ? 'success' : 'danger'}>
                {isApiConnected ? 'Connected (200 OK)' : 'Offline'}
              </Badge>
            </div>
            <div className="flex justify-between p-3 rounded-xl bg-white/70 border border-slate-100">
              <span className="text-slate-600">Last Health Check</span>
              <span className="text-slate-500">{lastChecked ? lastChecked.toLocaleTimeString() : 'Never'}</span>
            </div>
          </div>
        </GlassCard>

        {/* Model Registry Status Card */}
        <GlassCard variant="strong" className="p-6 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-primary-600" /> Model Registry Artifact Status
          </h3>

          {modelStatus && modelStatus.details ? (
            <div className="space-y-2 text-xs max-h-48 overflow-y-auto pr-1">
              {Object.entries(modelStatus.details).map(([key, detail]) => (
                <div key={key} className="flex items-center justify-between p-2 rounded-lg bg-white/70 border border-slate-100">
                  <span className="font-semibold text-slate-800 capitalize">{key.replace('_', ' ')}</span>
                  <Badge variant={detail.status === 'READY' ? 'success' : 'danger'}>
                    {detail.status} ({detail.framework})
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-400 italic">No model registry details available.</div>
          )}
        </GlassCard>
      </div>
    </div>
  );
};
