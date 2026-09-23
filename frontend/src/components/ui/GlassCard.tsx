import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'light' | 'strong' | 'solid';
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
  const baseClasses = 'rounded-2xl transition-all duration-300 relative overflow-hidden';
  
  const variantClasses = {
    light: 'bg-white/65 backdrop-blur-glass border border-white/70 shadow-glass',
    strong: 'bg-white/85 backdrop-blur-2xl border border-white/90 shadow-glass-hover',
    solid: 'bg-white border border-slate-200/80 shadow-sm',
  };

  const hoverClasses = hoverEffect ? 'hover:shadow-glass-hover hover:border-white/90 hover:-translate-y-0.5' : '';

  return (
    <div
      className={twMerge(clsx(baseClasses, variantClasses[variant], hoverClasses, className))}
      {...props}
    >
      {children}
    </div>
  );
};
