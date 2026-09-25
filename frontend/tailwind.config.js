/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#FAFBF7',
        surface: {
          DEFAULT: '#EEF3E8',
          card: '#FFFFFF',
          glass: 'rgba(255, 255, 255, 0.85)',
          dark: '#112316',
          darker: '#07120A',
          darkDeep: '#0B1C10',
        },
        agriDark: '#0B1C10',
        agriForest: '#112316',
        agriDarker: '#07120A',
        agriBg: '#FAFBF7',
        agriSurface: '#EEF3E8',
        agriLime: '#D4E768',
        agriGreen: '#2F6B3C',
        agriMediumGreen: '#5E9F48',
        agriBorder: '#E2E7DA',
        agriText: '#162018',
        agriMuted: '#536056',
        agri: {
          50: '#F4F8F1',
          100: '#EEF3E8',
          200: '#D6E4CC',
          300: '#B2CF9F',
          400: '#8CBF68',
          500: '#5E9F48',
          600: '#2F6B3C',
          700: '#24522E',
          800: '#1D3E24',
          900: '#162018',
          950: '#0B1C10',
        },
        earth: {
          50: '#FAF8F5',
          100: '#FAFBF7',
          200: '#ECE8DE',
          300: '#E2E7DA',
          400: '#D4CDBC',
          500: '#B8AD95',
          600: '#8C8068',
          700: '#536056',
          800: '#112316',
          900: '#0B1C10',
        },
        primary: {
          50: '#F4F8F1',
          100: '#EEF3E8',
          500: '#5E9F48',
          600: '#2F6B3C',
          700: '#24522E',
        },
        accent: {
          lime: '#D4E768',
          sand: '#ECE8DE',
          amber: '#D97706',
          sky: '#0284C7',
          teal: '#0D9488',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Plus Jakarta Sans', 'Manrope', 'system-ui', 'sans-serif'],
        editorial: ['Plus Jakarta Sans', 'Manrope', 'Inter', 'sans-serif'],
        serif: ['Georgia', 'Cambria', 'serif'],
      },
      backdropBlur: {
        glass: '16px',
        strong: '24px',
      },
      boxShadow: {
        card: '0 4px 20px -2px rgba(11, 28, 16, 0.04)',
        'card-hover': '0 20px 40px -15px rgba(47, 107, 60, 0.12)',
        floating: '0 16px 36px -8px rgba(11, 28, 16, 0.1)',
        glow: '0 0 30px rgba(212, 231, 104, 0.25)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'float-slow': 'float 9s ease-in-out infinite',
        'fade-in': 'fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'slide-up': 'slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [],
}

