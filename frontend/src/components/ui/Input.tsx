import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  unit?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, unit, icon, className, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {icon && (
            <span className="absolute left-3 text-slate-400 pointer-events-none">
              {icon}
            </span>
          )}
          <input
            ref={ref}
            className={twMerge(
              clsx(
                'glass-input w-full rounded-xl px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400',
                icon && 'pl-9',
                unit && 'pr-12',
                error && 'border-rose-400 focus:border-rose-500 focus:ring-rose-200',
                className
              )
            )}
            {...props}
          />
          {unit && (
            <span className="absolute right-3.5 text-xs font-medium text-slate-400 pointer-events-none">
              {unit}
            </span>
          )}
        </div>
        {error ? (
          <p className="text-xs text-rose-500 font-medium">{error}</p>
        ) : helperText ? (
          <p className="text-xs text-slate-400">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';
