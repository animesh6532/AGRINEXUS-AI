import React, { useState } from 'react';
import { X, Check, Bell, Mail, MessageSquare, Smartphone, Moon, ShieldAlert } from 'lucide-react';
import { Button } from '../ui/Button';
import type { NotificationPreferences } from '../../types/farmer';

interface NotificationPreferencesModalProps {
  isOpen: boolean;
  preferences?: NotificationPreferences | null;
  onSave: (updated: any) => Promise<void>;
  onClose: () => void;
}

export const NotificationPreferencesModal: React.FC<NotificationPreferencesModalProps> = ({
  isOpen,
  preferences,
  onSave,
  onClose,
}) => {
  const [inApp, setInApp] = useState(preferences?.channels.in_app ?? true);
  const [email, setEmail] = useState(preferences?.channels.email ?? true);
  const [sms, setSms] = useState(preferences?.channels.sms ?? false);
  const [whatsapp, setWhatsapp] = useState(preferences?.channels.whatsapp ?? false);

  const [criticalRisks, setCriticalRisks] = useState(preferences?.categories.critical_risks ?? true);
  const [weather, setWeather] = useState(preferences?.categories.weather ?? true);
  const [cropHealth, setCropHealth] = useState(preferences?.categories.crop_health ?? true);
  const [irrigation, setIrrigation] = useState(preferences?.categories.irrigation ?? true);
  const [market, setMarket] = useState(preferences?.categories.market ?? true);
  const [calendar, setCalendar] = useState(preferences?.categories.calendar ?? true);
  const [actionReminders, setActionReminders] = useState(preferences?.categories.action_reminders ?? true);

  const [quietEnabled, setQuietEnabled] = useState(preferences?.quiet_hours.enabled ?? false);
  const [quietStart, setQuietStart] = useState(preferences?.quiet_hours.start || '22:00');
  const [quietEnd, setQuietEnd] = useState(preferences?.quiet_hours.end || '06:00');
  const [criticalOverride, setCriticalOverride] = useState(preferences?.quiet_hours.critical_override ?? true);

  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'failed'>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveStatus('saving');
    setErrorMsg(null);
    try {
      await onSave({
        channels: { in_app: inApp, email, sms, whatsapp },
        categories: {
          critical_risks: criticalRisks,
          weather,
          crop_health: cropHealth,
          irrigation,
          market,
          calendar,
          action_reminders: actionReminders,
        },
        quiet_hours: {
          enabled: quietEnabled,
          start: quietStart,
          end: quietEnd,
          critical_override: criticalOverride,
        },
      });
      setSaveStatus('saved');
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (err: any) {
      console.error('Error saving notification preferences:', err);
      setSaveStatus('failed');
      setErrorMsg('Unable to save notification preferences. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-xl bg-[#0B1C10] text-[#FAFBF7] rounded-3xl border border-white/15 shadow-2xl p-6 space-y-6 overflow-y-auto max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-[#D4E768]" />
            <h3 className="text-xl font-extrabold font-editorial text-white">
              Notification Preferences
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-white/10 text-white/60 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-xl bg-red-500/15 border border-red-500/30 text-red-200 text-xs font-semibold flex items-center justify-between">
            <span>{errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} className="text-red-300 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Notification Channels */}
          <div className="space-y-3">
            <h4 className="text-xs font-extrabold text-[#D4E768] uppercase font-mono">
              1. Delivery Channels
            </h4>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <label className="flex items-center gap-2.5 p-3 rounded-2xl bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors">
                <input
                  type="checkbox"
                  checked={inApp}
                  onChange={(e) => setInApp(e.target.checked)}
                  className="rounded text-[#D4E768] focus:ring-0"
                />
                <Bell className="w-4 h-4 text-[#D4E768]" />
                <span className="font-bold">In-App Alerts</span>
              </label>

              <label className="flex items-center gap-2.5 p-3 rounded-2xl bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors">
                <input
                  type="checkbox"
                  checked={email}
                  onChange={(e) => setEmail(e.target.checked)}
                  className="rounded text-[#D4E768] focus:ring-0"
                />
                <Mail className="w-4 h-4 text-sky-400" />
                <span className="font-bold">Email Digest</span>
              </label>

              <label className="flex items-center gap-2.5 p-3 rounded-2xl bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors">
                <input
                  type="checkbox"
                  checked={sms}
                  onChange={(e) => setSms(e.target.checked)}
                  className="rounded text-[#D4E768] focus:ring-0"
                />
                <Smartphone className="w-4 h-4 text-amber-400" />
                <span className="font-bold">SMS (Critical)</span>
              </label>

              <label className="flex items-center gap-2.5 p-3 rounded-2xl bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors">
                <input
                  type="checkbox"
                  checked={whatsapp}
                  onChange={(e) => setWhatsapp(e.target.checked)}
                  className="rounded text-[#D4E768] focus:ring-0"
                />
                <MessageSquare className="w-4 h-4 text-emerald-400" />
                <span className="font-bold">WhatsApp Business</span>
              </label>
            </div>
          </div>

          {/* Alert Categories */}
          <div className="space-y-3">
            <h4 className="text-xs font-extrabold text-[#D4E768] uppercase font-mono">
              2. Alert Categories
            </h4>
            <div className="space-y-2 text-xs">
              {[
                { label: 'Critical Farm Risks', state: criticalRisks, set: setCriticalRisks },
                { label: 'Weather Impacts & Rain Forecasts', state: weather, set: setWeather },
                { label: 'Crop Health & Pest/Disease Watch', state: cropHealth, set: setCropHealth },
                { label: 'Irrigation & Soil Moisture Triggers', state: irrigation, set: setIrrigation },
                { label: 'Market Movement & Price Opportunities', state: market, set: setMarket },
                { label: 'Crop Calendar Operations', state: calendar, set: setCalendar },
                { label: 'Personalized Daily Action Plan Reminders', state: actionReminders, set: setActionReminders },
              ].map((item, idx) => (
                <label
                  key={idx}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors"
                >
                  <span className="font-semibold text-white/90">{item.label}</span>
                  <input
                    type="checkbox"
                    checked={item.state}
                    onChange={(e) => item.set(e.target.checked)}
                    className="rounded text-[#D4E768] focus:ring-0"
                  />
                </label>
              ))}
            </div>
          </div>

          {/* Quiet Hours */}
          <div className="space-y-3 pt-2 border-t border-white/10">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-extrabold text-[#D4E768] uppercase font-mono flex items-center gap-1.5">
                <Moon className="w-4 h-4 text-amber-300" /> 3. Quiet Hours
              </h4>
              <input
                type="checkbox"
                checked={quietEnabled}
                onChange={(e) => setQuietEnabled(e.target.checked)}
                className="rounded text-[#D4E768] focus:ring-0"
              />
            </div>

            {quietEnabled && (
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-3 text-xs">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <label className="block text-white/70 mb-1">Start Time</label>
                    <input
                      type="time"
                      value={quietStart}
                      onChange={(e) => setQuietStart(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-black/40 text-white border border-white/15"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="block text-white/70 mb-1">End Time</label>
                    <input
                      type="time"
                      value={quietEnd}
                      onChange={(e) => setQuietEnd(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-black/40 text-white border border-white/15"
                    />
                  </div>
                </div>

                <label className="flex items-center gap-2 pt-1 font-medium text-amber-200">
                  <input
                    type="checkbox"
                    checked={criticalOverride}
                    onChange={(e) => setCriticalOverride(e.target.checked)}
                    className="rounded text-amber-400 focus:ring-0"
                  />
                  <span>Critical alerts override quiet hours</span>
                </label>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
            <Button onClick={onClose} type="button" variant="secondary" size="sm">
              Cancel
            </Button>
            <Button type="submit" variant="lime" size="sm" disabled={isSaving}>
              {saveStatus === 'saving'
                ? 'Saving...'
                : saveStatus === 'saved'
                ? 'Saved'
                : saveStatus === 'failed'
                ? 'Save failed'
                : 'Save Preferences'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
