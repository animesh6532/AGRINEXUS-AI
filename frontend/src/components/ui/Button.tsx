import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'lime' | 'dark';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  children,
  className,
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-semibold transition-all duration-300 rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary: 'bg-[#2F6B3C] hover:bg-[#24522E] text-white shadow-sm hover:shadow-md focus:ring-[#2F6B3C]',
    secondary: 'bg-[#D4E768] hover:bg-[#E2F165] text-[#0B1C10] font-bold shadow-sm focus:ring-[#D4E768]',
    lime: 'bg-[#D4E768] hover:bg-[#E2F165] text-[#0B1C10] font-bold shadow-sm hover:shadow-glow focus:ring-[#D4E768]',
    dark: 'bg-[#0B1C10] hover:bg-[#112316] text-[#FAFBF7] border border-white/20 focus:ring-[#D4E768]',
    outline: 'bg-transparent hover:bg-[#EEF3E8] border border-[#E2E7DA] text-[#162018] focus:ring-[#2F6B3C]',
    ghost: 'bg-transparent hover:bg-[#EEF3E8] text-[#536056] hover:text-[#162018] focus:ring-[#2F6B3C]',
    danger: 'bg-rose-600 hover:bg-rose-700 text-white shadow-sm focus:ring-rose-500',
  };

  const sizes = {
    sm: 'px-3.5 py-1.5 text-xs gap-1.5',
    md: 'px-5 py-2.5 text-xs sm:text-sm gap-2',
    lg: 'px-7 py-3.5 text-sm sm:text-base gap-2.5',
  };

  return (
    <button
      className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <svg className="animate-spin h-4 w-4 text-current" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      ) : icon ? (
        <span>{icon}</span>
      ) : null}
      <span>{children}</span>
    </button>
  );
};
