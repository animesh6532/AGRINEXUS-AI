import React from 'react';
import { useHealth } from '../../context/HealthContext';
import { ShieldCheck, ShieldAlert } from 'lucide-react';

interface AgriculturalPageHeroProps {
  category: string;
  title: string;
  description: string;
  imageSrc?: string;
  children?: React.ReactNode;
}

export const AgriculturalPageHero: React.FC<AgriculturalPageHeroProps> = ({
  category,
  title,
  description,
  imageSrc = '/images/hero-farmland.webp',
  children,
}) => {
  const { isModelSystemReady, isApiConnected } = useHealth();

  return (
    <div className="relative rounded-3xl overflow-hidden bg-[#0B1C10] text-[#FAFBF7] p-6 sm:p-10 border border-[#E2E7DA]/20 shadow-xl mb-8 min-h-[220px] flex flex-col justify-between group">
      {/* Background Photography with subtle Zoom & Overlay */}
      {imageSrc && (
        <div className="absolute inset-0 z-0 overflow-hidden">
          <img
            src={imageSrc}
            alt={title}
            className="w-full h-full object-cover object-center opacity-35 transition-transform duration-1000 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#0B1C10] via-[#0B1C10]/85 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10] via-transparent to-transparent" />
        </div>
      )}

      {/* Hero Content */}
      <div className="relative z-10 space-y-3 max-w-3xl">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="px-3 py-1 rounded-full bg-[#D4E768] text-[#0B1C10] text-[10px] sm:text-xs font-bold uppercase tracking-widest">
            {category}
          </span>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-[11px] font-medium text-[#FAFBF7] border border-white/15">
            {isModelSystemReady ? (
              <ShieldCheck className="w-3.5 h-3.5 text-[#D4E768]" />
            ) : (
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            )}
            <span>{isModelSystemReady ? '● Systems operational' : '● System status degraded'}</span>
          </div>
        </div>

        <h1 className="text-2xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight font-editorial leading-tight text-[#FAFBF7]">
          {title}
        </h1>

        <p className="text-xs sm:text-sm text-[#FAFBF7]/80 leading-relaxed font-sans max-w-2xl">
          {description}
        </p>
      </div>

      {children && <div className="relative z-10 pt-4 flex items-center gap-3 flex-wrap">{children}</div>}
    </div>
  );
};
