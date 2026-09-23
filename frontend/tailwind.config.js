/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#F7FBFF',
        surface: {
          DEFAULT: 'rgba(255, 255, 255, 0.65)',
          strong: 'rgba(255, 255, 255, 0.85)',
          solid: '#FFFFFF',
        },
        primary: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
        },
        agri: {
          50: '#F0FDF4',
          100: '#DCFCE7',
          500: '#22C55E',
          600: '#16A34A',
          700: '#15803D',
        },
        accent: {
          50: '#ECFEFF',
          500: '#06B6D4',
          600: '#0891B2',
        },
        slate: {
          850: '#0F172A',
          900: '#0B132B',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Manrope', 'system-ui', 'sans-serif'],
      },
      backdropBlur: {
        glass: '18px',
      },
      boxShadow: {
        glass: '0 10px 40px rgba(70, 120, 160, 0.08)',
        'glass-hover': '0 15px 45px rgba(70, 120, 160, 0.14)',
        glow: '0 0 25px rgba(37, 99, 235, 0.15)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        }
      }
    },
  },
  plugins: [],
}
