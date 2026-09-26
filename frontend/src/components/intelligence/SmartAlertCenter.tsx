import React, { useState } from 'react';
import {
  Bell,
  ShieldAlert,
  CloudSun,
  Droplets,
  Bug,
  Database,
  TrendingUp,
  Settings,
  Check,
  X,
  Info,
  Clock,
  Send,
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import type { SmartAlertItem, NotificationPreferences } from '../../types/farmer';

interface SmartAlertCenterProps {
  alerts?: SmartAlertItem[];
  preferences?: NotificationPreferences;
  onOpenPreferences?: () => void;
  onDismissAlert?: (alertId: string) => void;
}

export const SmartAlertCenter: React.FC<SmartAlertCenterProps> = ({
  alerts = [],
  preferences,
  onOpenPreferences,
  onDismissAlert,
}) => {
  const [filterCategory, setFilterCategory] = useState<string>('ALL');

  const criticalAlerts = alerts.filter(
    (a) => a.priority === 'Critical' || a.priority === 'High'
  );
  const infoAlerts = alerts.filter(
    (a) => a.priority === 'Moderate' || a.priority === 'Info'
  );

  const filteredAlerts = alerts.filter((a) => {
    if (filterCategory === 'ALL') return true;
    return (a.category || '').toUpperCase() === filterCategory;
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-[#0B1C10] text-[#FAFBF7] border border-white/10 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-[#D4E768]" />
            <h3 className="text-xl font-extrabold font-editorial text-white">
              SMART FARM ALERTS CENTER
            </h3>
          </div>
          <p className="text-xs text-white/60">
            Crop-aware weather risk alerts, disease/pest warnings, irrigation triggers, and market movement notifications
          </p>
        </div>

        <div className="flex items-center gap-3">
          {onOpenPreferences && (
            <Button
              onClick={onOpenPreferences}
              variant="lime"
              size="sm"
              icon={<Settings className="w-4 h-4" />}
            >
              Notification Settings
            </Button>
          )}
        </div>
      </div>

      {/* Active Preferences Channel Badges */}
      {preferences && (
        <div className="flex flex-wrap items-center gap-3 p-4 rounded-2xl bg-white/70 border border-[#E2E7DA] text-xs font-semibold text-[#536056]">
          <span>Active Channels:</span>
          <span className={`px-2.5 py-1 rounded-lg ${preferences.channels.in_app ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-500'}`}>
            ☑ In-App
          </span>
          <span className={`px-2.5 py-1 rounded-lg ${preferences.channels.email ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-500'}`}>
            {preferences.channels.email ? '☑ Email ON' : '☐ Email OFF'}
          </span>
          <span className={`px-2.5 py-1 rounded-lg ${preferences.channels.sms ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-500'}`}>
            {preferences.channels.sms ? '☑ SMS ON' : '☐ SMS OFF'}
          </span>
          <span className={`px-2.5 py-1 rounded-lg ${preferences.channels.whatsapp ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-500'}`}>
            {preferences.channels.whatsapp ? '☑ WhatsApp ON' : '☐ WhatsApp OFF'}
          </span>
          {preferences.quiet_hours.enabled && (
            <span className="ml-auto text-[11px] text-amber-700 font-mono">
              🌙 Quiet Hours: {preferences.quiet_hours.start}–{preferences.quiet_hours.end}
            </span>
          )}
        </div>
      )}

      {/* Category Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-none pb-1 border-b border-[#E2E7DA]">
        {['ALL', 'WEATHER', 'IRRIGATION', 'PEST', 'SOIL', 'MARKET', 'CALENDAR'].map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterCategory(cat)}
            className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all whitespace-nowrap ${
              filterCategory === cat
                ? 'bg-[#0B1C10] text-[#D4E768] shadow-md'
                : 'bg-white/80 text-[#536056] hover:bg-[#EEF3E8] hover:text-[#0B1C10]'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Alerts Grid */}
      {filteredAlerts.length > 0 ? (
        <div className="space-y-4">
          {filteredAlerts.map((alert) => {
            const isCritical = alert.priority === 'Critical' || alert.priority === 'High';

            return (
              <GlassCard
                key={alert.id}
                variant="solid"
                className={`p-5 space-y-3 border-l-4 ${
                  isCritical
                    ? 'border-l-rose-500 bg-rose-50/20 border-[#E2E7DA]'
                    : 'border-l-sky-500 bg-sky-50/20 border-[#E2E7DA]'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant={isCritical ? 'danger' : 'info'}>
                        {alert.priority.toUpperCase()}
                      </Badge>
                      <span className="text-xs font-mono font-bold text-[#536056]">
                        {alert.category}
                      </span>
                      {alert.field_name && (
                        <span className="text-xs text-[#2F6B3C] font-semibold">
                          • {alert.field_name}
                        </span>
                      )}
                    </div>

                    <h4 className="text-base font-extrabold text-[#0B1C10] font-editorial">
                      {alert.title}
                    </h4>
                  </div>

                  <span className="text-[10px] text-[#536056] font-mono">
                    {alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Today'}
                  </span>
                </div>

                <p className="text-xs text-[#0B1C10] font-medium leading-relaxed">
                  {alert.description}
                </p>

                {alert.recommended_action && (
                  <div className="p-3 rounded-2xl bg-white/80 border border-[#E2E7DA] text-xs space-y-1">
                    <strong className="text-[#2F6B3C] block font-sans text-[11px]">RECOMMENDED ACTION:</strong>
                    <p className="text-[#0B1C10]">{alert.recommended_action}</p>
                  </div>
                )}

                {/* Delivery Provenance Indicator */}
                <div className="flex items-center justify-between text-[11px] text-[#536056] pt-2 border-t border-[#E2E7DA]">
                  <span className="flex items-center gap-1 font-mono">
                    <Info className="w-3 h-3 text-[#2F6B3C]" />
                    Triggered by threshold check • Suppressed duplicate alerts
                  </span>

                  {onDismissAlert && (
                    <button
                      onClick={() => onDismissAlert(alert.id)}
                      className="text-xs text-gray-500 hover:text-gray-800 font-semibold"
                    >
                      Dismiss
                    </button>
                  )}
                </div>
              </GlassCard>
            );
          })}
        </div>
      ) : (
        <GlassCard variant="solid" className="p-8 text-center space-y-2">
          <Bell className="w-8 h-8 text-[#2F6B3C] mx-auto" />
          <h4 className="text-base font-bold text-[#0B1C10]">No Active Smart Alerts</h4>
          <p className="text-xs text-[#536056]">
            No risk threshold violations detected for your active crop fields.
          </p>
        </GlassCard>
      )}
    </div>
  );
};
