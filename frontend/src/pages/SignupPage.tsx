import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User, MapPin, Sprout, ArrowLeft, ShieldCheck } from 'lucide-react';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';

export const SignupPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [location, setLocation] = useState('Punjab, India');
  const [primaryCrop, setPrimaryCrop] = useState('Rice');
  const [isLoading, setIsLoading] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      signup({
        name: name || 'Farmer',
        email: email || 'farmer@agrinexus.ai',
        location,
        primaryCrop,
        farmType: 'Commercial Agronomy'
      });
      setIsLoading(false);
      navigate('/dashboard');
    }, 600);
  };

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-12 bg-[#FAFBF7] text-[#162018] selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Left Column: Full-Height Cinematic Farmland Visual */}
      <div className="relative lg:col-span-7 bg-[#0B1C10] text-[#FAFBF7] overflow-hidden min-h-[320px] lg:min-h-screen flex flex-col justify-between p-8 sm:p-12 lg:p-16">
        <div className="absolute inset-0 z-0">
          <img
            src="/images/crop-intelligence.webp"
            alt="Agricultural field"
            className="w-full h-full object-cover object-center opacity-40 scale-105 transition-transform duration-1000"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10] via-[#0B1C10]/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#0B1C10]/90 via-[#0B1C10]/50 to-transparent" />
        </div>

        {/* Top Header */}
        <div className="relative z-10 flex items-center justify-between">
          <Link to="/" className="inline-flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-extrabold text-sm shadow-md">
              AN
            </div>
            <span className="font-extrabold text-lg font-editorial tracking-tight text-[#FAFBF7]">
              AGRI NEXUS-AI
            </span>
          </Link>

          <Link
            to="/"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-md text-xs font-semibold text-white hover:bg-white/20 transition-colors border border-white/15"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Home</span>
          </Link>
        </div>

        {/* Center Editorial Copy */}
        <div className="relative z-10 space-y-4 my-auto py-12">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#D4E768] text-[#0B1C10] text-xs font-extrabold uppercase tracking-widest">
            FARMER ONBOARDING
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black font-editorial tracking-tight leading-none text-[#FAFBF7]">
            Build Your <br />
            Field Intelligence <br />
            <span className="text-[#D4E768]">Profile.</span>
          </h1>

          <p className="text-xs sm:text-sm text-white/80 max-w-lg leading-relaxed font-sans">
            Connect your farm location, soil preferences, and crop targets to receive personalized agronomic recommendations and disease diagnostics.
          </p>

          <div className="pt-4 flex items-center gap-4 text-xs text-white/70">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-[#D4E768]" />
              <span>Full Privacy Protection</span>
            </div>
            <span>•</span>
            <div>Zero Hardware Required</div>
            <span>•</span>
            <div>Instant Access</div>
          </div>
        </div>

        {/* Bottom */}
        <div className="relative z-10 text-[11px] text-white/50 pt-4 border-t border-white/10">
          AgriNexus-AI Onboarding • Agricultural Decision Support System
        </div>
      </div>

      {/* Right Column: Form Panel */}
      <div className="lg:col-span-5 flex items-center justify-center p-6 sm:p-12 lg:p-16 bg-[#FAFBF7]">
        <div className="w-full max-w-md space-y-6">
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-widest text-[#2F6B3C]">
              CREATE ACCOUNT
            </span>
            <h2 className="text-3xl font-extrabold text-[#0B1C10] font-editorial tracking-tight">
              Join AgriNexus-AI
            </h2>
            <p className="text-xs text-[#536056]">
              Set up your farmer profile in 60 seconds.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Full Name"
              placeholder="Gurpreet Singh"
              value={name}
              onChange={(e) => setName(e.target.value)}
              icon={<User className="w-4 h-4 text-[#2F6B3C]" />}
              required
            />

            <Input
              label="Email Address"
              type="email"
              placeholder="gurpreet@farm.in"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail className="w-4 h-4 text-[#2F6B3C]" />}
              required
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock className="w-4 h-4 text-[#2F6B3C]" />}
              required
            />

            <Input
              label="Farm Location"
              placeholder="Ludhiana, Punjab"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              icon={<MapPin className="w-4 h-4 text-[#2F6B3C]" />}
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
              isLoading={isLoading}
              icon={<Sprout className="w-4 h-4" />}
            >
              Create AgriNexus Account
            </Button>
          </form>

          <div className="text-center text-xs text-[#536056] pt-4 border-t border-[#E2E7DA]">
            Already have an account?{' '}
            <Link to="/login" className="font-extrabold text-[#2F6B3C] hover:underline">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
