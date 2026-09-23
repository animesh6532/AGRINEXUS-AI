import React, { useState } from 'react';
import { User, MapPin, Sprout, Save } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';

export const ProfilePage: React.FC = () => {
  const { user, updateProfile } = useAuth();

  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [location, setLocation] = useState(user?.location || 'Punjab, India');
  const [primaryCrop, setPrimaryCrop] = useState(user?.primaryCrop || 'Rice');
  const [savedNotice, setSavedNotice] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile({ name, email, location, primaryCrop });
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary-100 text-primary-700 flex items-center justify-center font-bold">
          <User className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Farmer Profile</h1>
          <p className="text-xs text-slate-500">
            Manage your personal agronomic preferences and farm location.
          </p>
        </div>
      </div>

      <GlassCard variant="strong" className="p-6 max-w-xl space-y-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Full Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            icon={<User className="w-4 h-4" />}
            required
          />

          <Input
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <Input
            label="Farm Location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            icon={<MapPin className="w-4 h-4" />}
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

          <Button type="submit" variant="primary" size="md" icon={<Save className="w-4 h-4" />}>
            Save Profile Preferences
          </Button>

          {savedNotice && (
            <p className="text-xs text-emerald-600 font-bold animate-pulse">Profile updated successfully!</p>
          )}
        </form>
      </GlassCard>
    </div>
  );
};
