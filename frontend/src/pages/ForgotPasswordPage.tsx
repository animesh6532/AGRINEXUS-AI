import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-12 bg-[#FAFBF7] text-[#162018] selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Left Visual Column */}
      <div className="relative lg:col-span-7 bg-[#0B1C10] text-[#FAFBF7] overflow-hidden min-h-[260px] lg:min-h-screen flex flex-col justify-between p-8 sm:p-12 lg:p-16">
        <div className="absolute inset-0 z-0">
          <img
            src="/images/soil-intelligence.webp"
            alt="Soil background"
            className="w-full h-full object-cover object-center opacity-40 scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10] via-[#0B1C10]/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#0B1C10]/90 via-[#0B1C10]/50 to-transparent" />
        </div>

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
            to="/login"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-md text-xs font-semibold text-white hover:bg-white/20 transition-colors border border-white/15"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Login</span>
          </Link>
        </div>

        <div className="relative z-10 space-y-4 my-auto py-12">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#D4E768] text-[#0B1C10] text-xs font-extrabold uppercase tracking-widest">
            SECURITY & ACCESS
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black font-editorial tracking-tight leading-none text-[#FAFBF7]">
            Reset Your <br />
            Platform Access <br />
            <span className="text-[#D4E768]">Securely.</span>
          </h1>

          <p className="text-xs sm:text-sm text-white/80 max-w-lg leading-relaxed font-sans">
            Enter your registered email address to receive password reset instructions.
          </p>
        </div>

        <div className="relative z-10 text-[11px] text-white/50 pt-4 border-t border-white/10">
          AgriNexus-AI Platform • Security Recovery
        </div>
      </div>

      {/* Right Column Form */}
      <div className="lg:col-span-5 flex items-center justify-center p-6 sm:p-12 lg:p-16 bg-[#FAFBF7]">
        <div className="w-full max-w-md space-y-6">
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-widest text-[#2F6B3C]">
              RECOVERY
            </span>
            <h2 className="text-3xl font-extrabold text-[#0B1C10] font-editorial tracking-tight">
              Reset Password
            </h2>
            <p className="text-xs text-[#536056]">
              Enter your email to receive recovery instructions.
            </p>
          </div>

          {submitted ? (
            <div className="p-6 rounded-3xl bg-[#EEF3E8] border border-[#E2E7DA] text-center space-y-3">
              <CheckCircle2 className="w-10 h-10 text-[#2F6B3C] mx-auto" />
              <h4 className="text-base font-extrabold font-editorial text-[#0B1C10]">Reset Link Sent</h4>
              <p className="text-xs text-[#536056]">
                We have sent password reset instructions to <strong className="text-[#0B1C10]">{email}</strong>.
              </p>
              <Link to="/login" className="inline-block mt-2">
                <Button variant="lime" size="md">
                  Return to Sign In
                </Button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                label="Registered Email Address"
                type="email"
                placeholder="farmer@agrinexus.ai"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                icon={<Mail className="w-4 h-4 text-[#2F6B3C]" />}
                required
              />

              <Button
                type="submit"
                variant="lime"
                size="lg"
                className="w-full mt-2 shadow-md hover:shadow-glow"
              >
                Send Reset Link
              </Button>
            </form>
          )}

          <div className="text-center text-xs text-[#536056] pt-6 border-t border-[#E2E7DA]">
            Remember your password?{' '}
            <Link to="/login" className="font-extrabold text-[#2F6B3C] hover:underline">
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
