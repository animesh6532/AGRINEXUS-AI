/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#F7F8F3',
        surface: {
          DEFAULT: '#EEF3E8',
          card: '#FFFFFF',
          glass: 'rgba(255, 255, 255, 0.75)',
          dark: '#162018',
          darkSurface: '#1F2C22',
        },
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
          950: '#0D140F',
        },
        earth: {
          50: '#FAF8F5',
          100: '#F7F8F3',
          200: '#ECE8DE',
          300: '#E8E4D9',
          400: '#D4CDBC',
          500: '#B8AD95',
          600: '#8C8068',
          700: '#645B4A',
          800: '#39463B',
          900: '#162018',
        },
        primary: {
          50: '#F4F8F1',
          100: '#EEF3E8',
          500: '#5E9F48',
          600: '#2F6B3C',
          700: '#24522E',
        },
        accent: {
          sand: '#ECE8DE',
          amber: '#D97706',
          sky: '#0284C7',
          teal: '#0D9488',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Manrope', 'DM Sans', 'system-ui', 'sans-serif'],
        serif: ['Georgia', 'Cambria', 'serif'],
      },
      backdropBlur: {
        glass: '16px',
        strong: '24px',
      },
      boxShadow: {
        card: '0 4px 20px -2px rgba(22, 32, 24, 0.05)',
        'card-hover': '0 20px 40px -15px rgba(47, 107, 60, 0.12)',
        floating: '0 16px 36px -8px rgba(22, 32, 24, 0.1)',
        glow: '0 0 30px rgba(94, 159, 72, 0.2)',
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

