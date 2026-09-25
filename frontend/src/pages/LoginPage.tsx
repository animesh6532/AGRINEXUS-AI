import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, LogIn, ArrowLeft, ShieldCheck } from 'lucide-react';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('farmer@agrinexus.ai');
  const [password, setPassword] = useState('password123');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      login(email);
      setIsLoading(false);
      navigate('/dashboard');
    }, 600);
  };

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-12 bg-[#FAFBF7] text-[#162018] selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Left Column: Full-Height Cinematic Farmland Hero (Desktop 7 Cols) */}
      <div className="relative lg:col-span-7 bg-[#0B1C10] text-[#FAFBF7] overflow-hidden min-h-[320px] lg:min-h-screen flex flex-col justify-between p-8 sm:p-12 lg:p-16">
        {/* Background Image & Gradient */}
        <div className="absolute inset-0 z-0">
          <img
            src="/images/hero-farmland.webp"
            alt="Farmland visual"
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
            AI-POWERED AGRICULTURAL INTELLIGENCE
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black font-editorial tracking-tight leading-none text-[#FAFBF7]">
            Intelligence <br />
            Rooted in <br />
            <span className="text-[#D4E768]">the Field.</span>
          </h1>

          <p className="text-xs sm:text-sm text-white/80 max-w-lg leading-relaxed font-sans">
            Unifying crop recommendation, plant disease diagnostics, pest risk modeling, soil organic carbon analysis, and live vision into one connected platform.
          </p>

          <div className="pt-4 flex items-center gap-4 text-xs text-white/70">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-[#D4E768]" />
              <span>7 Frozen ML Models</span>
            </div>
            <span>•</span>
            <div>OpenCV Live Camera</div>
            <span>•</span>
            <div>Mandi Pricing</div>
          </div>
        </div>

        {/* Bottom Status */}
        <div className="relative z-10 text-[11px] text-white/50 pt-4 border-t border-white/10">
          AgriNexus-AI Platform • Secure Operational Gateway
        </div>
      </div>

      {/* Right Column: Premium Glass/Cream Onboarding Panel (Desktop 5 Cols) */}
      <div className="lg:col-span-5 flex items-center justify-center p-6 sm:p-12 lg:p-16 bg-[#FAFBF7]">
        <div className="w-full max-w-md space-y-8">
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-widest text-[#2F6B3C]">
              ACCOUNT ACCESS
            </span>
            <h2 className="text-3xl font-extrabold text-[#0B1C10] font-editorial tracking-tight">
              Welcome Back
            </h2>
            <p className="text-xs text-[#536056]">
              Sign in to access your agricultural intelligence workspace and field signals.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Email Address"
              type="email"
              placeholder="farmer@agrinexus.ai"
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

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-2 text-[#536056] cursor-pointer">
                <input
                  type="checkbox"
                  defaultChecked
                  className="rounded text-[#2F6B3C] focus:ring-[#2F6B3C] accent-[#2F6B3C]"
                />
                <span>Remember session</span>
              </label>
              <Link to="/forgot-password" className="font-bold text-[#2F6B3C] hover:underline">
                Forgot password?
              </Link>
            </div>

            <Button
              type="submit"
              variant="lime"
              size="lg"
              className="w-full mt-2 shadow-md hover:shadow-glow"
              isLoading={isLoading}
              icon={<LogIn className="w-4 h-4" />}
            >
              Sign In to Workspace
            </Button>
          </form>

          <div className="text-center text-xs text-[#536056] pt-6 border-t border-[#E2E7DA]">
            Don't have an account?{' '}
            <Link to="/signup" className="font-extrabold text-[#2F6B3C] hover:underline">
              Create Field Profile
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
