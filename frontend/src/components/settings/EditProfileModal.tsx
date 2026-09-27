import React, { useState, useEffect } from 'react';
import { X, Save, User, Mail, Phone, MapPin, Globe, Clock, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import type { FarmerProfile } from '../../types/farmer';

interface EditProfileModalProps {
  isOpen: boolean;
  farmer: FarmerProfile | null;
  userEmail?: string;
  onSave: (data: Partial<FarmerProfile>) => Promise<void>;
  onClose: () => void;
}

export const EditProfileModal: React.FC<EditProfileModalProps> = ({
  isOpen,
  farmer,
  userEmail,
  onSave,
  onClose,
}) => {
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [location, setLocation] = useState('');
  const [timezone, setTimezone] = useState('Asia/Kolkata');
  const [preferredLanguage, setPreferredLanguage] = useState('en');
  const [preferredUnits, setPreferredUnits] = useState('acre');

  const [status, setStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (farmer) {
      setFullName(farmer.full_name || '');
      setPhone(farmer.phone || '');
      setLocation(farmer.location || '');
      setTimezone(farmer.timezone || 'Asia/Kolkata');
      setPreferredLanguage(farmer.preferred_language || 'en');
      setPreferredUnits(farmer.preferred_units || 'acre');
    }
  }, [farmer, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim()) {
      setErrorMessage('Full name is required.');
      return;
    }

    setStatus('saving');
    setErrorMessage(null);

    try {
      await onSave({
        full_name: fullName.trim(),
        phone: phone.trim() || undefined,
        location: location.trim() || undefined,
        timezone,
        preferred_language: preferredLanguage,
        preferred_units: preferredUnits,
      });

      setStatus('success');
      setTimeout(() => {
        setStatus('idle');
        onClose();
      }, 600);
    } catch (err: any) {
      console.error('Error saving profile:', err);
      setStatus('error');
      setErrorMessage(err.message || 'Failed to update farmer profile. Entered values preserved.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-xl bg-[#FAFBF7] rounded-3xl border border-[#E2E7DA] shadow-2xl p-6 sm:p-8 space-y-6 overflow-y-auto max-h-[92vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#0B1C10] text-[#D4E768] flex items-center justify-center shadow-sm">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                Edit Farmer Profile
              </h3>
              <p className="text-xs text-[#536056]">
                Update identity, location, timezone, and regional defaults
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={status === 'saving'}
            className="p-1.5 rounded-full hover:bg-black/5 text-[#536056] hover:text-[#0B1C10] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Banner */}
        {errorMessage && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-900 text-xs font-semibold flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button onClick={() => setErrorMessage(null)} className="text-rose-600 hover:text-rose-900">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Success Banner */}
        {status === 'success' && (
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-900 text-xs font-bold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Profile saved successfully! Synchronizing Farm Command Center...</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Read-Only Account Identity */}
          <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1.5">
            <span className="text-[10px] font-bold text-[#536056] uppercase tracking-wider flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-[#2F6B3C]" /> Authenticated Account Identity
            </span>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-[#0B1C10]">
                {userEmail || farmer?.email || 'farmer@agrinexus.ai'}
              </span>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 border border-emerald-300 px-2 py-0.5 rounded-full">
                VERIFIED
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Full Name *"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="e.g. Ramesh Kumar"
              required
            />
            <Input
              label="Phone Number"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+91 98765 43210"
            />
          </div>

          <Input
            label="Location / Village / District / State"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g. Barasat, North 24 Parganas, West Bengal"
          />

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Select
              label="Timezone *"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              options={[
                { value: 'Asia/Kolkata', label: 'Asia/Kolkata (IST)' },
                { value: 'UTC', label: 'UTC' },
                { value: 'America/New_York', label: 'America/New_York (EST)' },
                { value: 'Europe/London', label: 'Europe/London (GMT)' },
              ]}
            />

            <Select
              label="Preferred Language"
              value={preferredLanguage}
              onChange={(e) => setPreferredLanguage(e.target.value)}
              options={[
                { value: 'en', label: 'English' },
                { value: 'bn', label: 'Bengali (বাংলা)' },
                { value: 'hi', label: 'Hindi (हिंदी)' },
                { value: 'te', label: 'Telugu (తెలుగు)' },
                { value: 'ta', label: 'Tamil (தமிழ்)' },
                { value: 'mr', label: 'Marathi (मराठी)' },
                { value: 'pa', label: 'Punjabi (ਪੰਜਾਬੀ)' },
              ]}
            />

            <Select
              label="Preferred Land Unit"
              value={preferredUnits}
              onChange={(e) => setPreferredUnits(e.target.value)}
              options={[
                { value: 'acre', label: 'Acres (acre)' },
                { value: 'hectare', label: 'Hectares (ha)' },
                { value: 'bigha', label: 'Bigha' },
                { value: 'm2', label: 'Square Meters (m²)' },
              ]}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#E2E7DA]">
            <Button
              onClick={onClose}
              type="button"
              variant="secondary"
              size="sm"
              disabled={status === 'saving'}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="lime"
              size="sm"
              disabled={status === 'saving'}
              icon={<Save className={`w-4 h-4 ${status === 'saving' ? 'animate-spin' : ''}`} />}
            >
              {status === 'saving' ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
