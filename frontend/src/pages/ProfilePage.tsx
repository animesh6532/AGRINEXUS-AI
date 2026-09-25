import React, { useState } from 'react';
import { User, MapPin, Save, CheckCircle2, Navigation } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { useLocationContext } from '../context/LocationContext';
import { LocationMapPreview } from '../components/location/LocationMapPreview';

export const ProfilePage: React.FC = () => {
  const { user, updateProfile } = useAuth();
  const { location: globalLocation, openPicker, clearLocation } = useLocationContext();

  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [primaryCrop, setPrimaryCrop] = useState(user?.primaryCrop || 'Rice');
  const [savedNotice, setSavedNotice] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile({ name, email, location: globalLocation?.displayName || 'Not Set', primaryCrop });
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="ACCOUNT"
        title="Farmer Profile & Field Location"
        description="Manage your agronomic identity, field geographic location, map center, primary crop focus, and operational preferences."
        imageSrc="/images/crop-calendar.webp"
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Profile Overview Card & Field Location Card (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* User Identity Card */}
          <div className="p-8 rounded-3xl bg-[#0B1C10] text-[#FAFBF7] space-y-6 border border-white/10 shadow-xl">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-black text-2xl font-editorial shadow-md">
                {(name || 'F').charAt(0).toUpperCase()}
              </div>
              <div>
                <h3 className="text-2xl font-extrabold font-editorial text-white">{name || 'Farmer'}</h3>
                <p className="text-xs text-white/60">{email || 'farmer@agrinexus.ai'}</p>
                <span className="inline-block mt-2 px-3 py-0.5 rounded-full bg-[#D4E768]/20 text-[#D4E768] text-[10px] font-bold uppercase border border-[#D4E768]/30">
                  Commercial Agronomist
                </span>
              </div>
            </div>

            <div className="space-y-3 pt-4 border-t border-white/10 text-xs font-sans">
              <div className="flex justify-between py-1.5 border-b border-white/5">
                <span className="text-white/60">Primary Crop:</span>
                <span className="font-bold text-[#D4E768]">{primaryCrop}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-white/5">
                <span className="text-white/60">Registered Services:</span>
                <span className="font-bold text-white">All 8 Inference Models</span>
              </div>
            </div>
          </div>

          {/* Premium Field Location Card with Map Preview */}
          <GlassCard variant="solid" className="p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-[#2F6B3C]" />
                <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">FIELD LOCATION</h3>
              </div>
              <button
                onClick={openPicker}
                className="px-3 py-1 rounded-xl bg-[#EEF3E8] border border-[#E2E7DA] text-xs font-bold text-[#2F6B3C] hover:bg-[#D4E768] hover:text-[#0B1C10] transition-colors"
              >
                {globalLocation ? 'Change Location' : 'Set Location'}
              </button>
            </div>

            <LocationMapPreview location={globalLocation} onClick={openPicker} />

            {globalLocation ? (
              <div className="space-y-2 text-xs pt-1">
                <div className="flex justify-between py-1 border-b border-[#E2E7DA]">
                  <span className="text-[#536056]">Location Name:</span>
                  <span className="font-bold text-[#0B1C10]">{globalLocation.displayName}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#E2E7DA] font-mono">
                  <span className="text-[#536056]">Coordinates:</span>
                  <span className="font-bold text-[#2F6B3C]">
                    {globalLocation.latitude.toFixed(4)}° N, {globalLocation.longitude.toFixed(4)}° E
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#E2E7DA]">
                  <span className="text-[#536056]">Acquisition Source:</span>
                  <span className="font-bold text-[#0B1C10] flex items-center gap-1">
                    <Navigation className="w-3 h-3 text-[#2F6B3C]" />
                    {globalLocation.source === 'device' ? 'Device GPS' : 'Manual / Map'}
                  </span>
                </div>
                {globalLocation.timestamp && (
                  <div className="flex justify-between py-1 text-[11px] text-[#536056]">
                    <span>Last Updated:</span>
                    <span>{new Date(globalLocation.timestamp).toLocaleTimeString()}</span>
                  </div>
                )}

                <button
                  onClick={clearLocation}
                  className="w-full mt-2 text-xs text-rose-600 hover:text-rose-800 font-bold py-1.5 transition-colors"
                >
                  Clear Saved Location
                </button>
              </div>
            ) : (
              <p className="text-xs text-[#536056] text-center italic py-2">
                No field location selected. Click map above to choose your farm location.
              </p>
            )}
          </GlassCard>
        </div>

        {/* Form Settings (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
            <div className="border-b border-[#E2E7DA] pb-4">
              <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                EDIT PREFERENCES
              </span>
              <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">
                Agronomic Identity Settings
              </h3>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                label="Full Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                icon={<User className="w-4 h-4 text-[#2F6B3C]" />}
                required
              />

              <Input
                label="Email Address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <Select
                label="Primary Crop Interest"
                value={primaryCrop}
                onChange={(e) => setPrimaryCrop(e.target.value)}
                options={[
                  { value: 'Rice', label: 'Rice / Paddy' },
                  { value: 'Wheat', label: 'Wheat' },
                  { value: 'Maize', label: 'Maize' },
                  { value: 'Cotton', label: 'Cotton' },
                  { value: 'Sugarcane', label: 'Sugarcane' },
                ]}
              />

              <Button
                type="submit"
                variant="lime"
                size="lg"
                className="w-full mt-2 shadow-md hover:shadow-glow"
                icon={<Save className="w-4 h-4" />}
              >
                Save Farmer Profile
              </Button>

              {savedNotice && (
                <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] text-[#2F6B3C] text-xs font-bold flex items-center gap-2 animate-fade-in">
                  <CheckCircle2 className="w-4 h-4 text-[#2F6B3C]" />
                  <span>Farmer profile preferences saved successfully!</span>
                </div>
              )}
            </form>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
