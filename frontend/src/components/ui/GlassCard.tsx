import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'light' | 'strong' | 'solid' | 'dark' | 'cream' | 'floating';
  hoverEffect?: boolean;
  className?: string;
  children: React.ReactNode;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  variant = 'light',
  hoverEffect = true,
  className,
  children,
  ...props
}) => {
  const baseClasses = 'rounded-3xl transition-all duration-300 relative overflow-hidden';
  
  const variantClasses = {
    light: 'bg-white/80 backdrop-blur-xl border border-[#E2E7DA] shadow-sm',
    strong: 'bg-white/95 backdrop-blur-2xl border border-[#E2E7DA] shadow-md',
    solid: 'bg-white border border-[#E2E7DA] shadow-sm',
    dark: 'bg-[#112316] text-[#FAFBF7] border border-white/10 shadow-xl',
    cream: 'bg-[#EEF3E8] border border-[#E2E7DA] text-[#162018]',
    floating: 'bg-[#0B1C10]/85 backdrop-blur-xl border border-[#D4E768]/30 text-[#FAFBF7] shadow-floating',
  };

  const hoverClasses = hoverEffect ? 'hover:shadow-card-hover hover:border-[#D4E768]/40 hover:-translate-y-1' : '';

  return (
    <div
      className={twMerge(clsx(baseClasses, variantClasses[variant], hoverClasses, className))}
      {...props}
    >
      {children}
    </div>
  );
};
