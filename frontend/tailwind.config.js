/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Asosiy qora tonlar
        ink: {
          950: '#0A0A0A',
          900: '#111111',
          800: '#1A1A1A',
          700: '#242424',
          600: '#2E2E2E',
          500: '#3A3A3A',
          400: '#525252',
          300: '#6B6B6B',
          200: '#A3A3A3',
          100: '#D4D4D4',
        },
        // Tilla
        gold: {
          50:  '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F5C518',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
        // Yashil
        emerald: {
          400: '#34D399',
          500: '#10B981',
          600: '#059669',
        },
        // Qizil
        crimson: {
          400: '#F87171',
          500: '#EF4444',
          600: '#DC2626',
          700: '#B91C1C',
        },
      },
      fontFamily: {
        sans:    ['Inter var', 'Inter', 'system-ui', 'sans-serif'],
        display: ['Cal Sans', 'Inter var', 'sans-serif'],
        mono:    ['JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial':   'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':    'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gold-shimmer':      'linear-gradient(105deg, transparent 40%, rgba(245,197,24,0.08) 50%, transparent 60%)',
        'hero-gradient':     'linear-gradient(to right, #0A0A0A 30%, transparent 70%), linear-gradient(to top, #0A0A0A 20%, transparent 60%)',
      },
      animation: {
        'shimmer':       'shimmer 2s infinite',
        'fade-up':       'fadeUp 0.4s ease-out',
        'fade-in':       'fadeIn 0.3s ease-out',
        'scale-in':      'scaleIn 0.2s ease-out',
        'slide-down':    'slideDown 0.3s ease-out',
        'pulse-gold':    'pulseGold 2s infinite',
        'spin-slow':     'spin 3s linear infinite',
      },
      keyframes: {
        shimmer: {
          '0%':   { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        },
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        scaleIn: {
          '0%':   { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideDown: {
          '0%':   { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGold: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(245,197,24,0.4)' },
          '50%':      { boxShadow: '0 0 0 8px rgba(245,197,24,0)' },
        },
      },
      boxShadow: {
        'gold':    '0 0 20px rgba(245,197,24,0.15)',
        'gold-lg': '0 0 40px rgba(245,197,24,0.2)',
        'card':    '0 4px 24px rgba(0,0,0,0.6)',
        'card-hover': '0 8px 40px rgba(0,0,0,0.8)',
        'glass':   '0 8px 32px rgba(0,0,0,0.4)',
        'inner-gold': 'inset 0 1px 0 rgba(245,197,24,0.1)',
      },
      backdropBlur: {
        xs: '2px',
      },
      borderRadius: {
        '2xl': '16px',
        '3xl': '24px',
        '4xl': '32px',
      },
    },
  },
  plugins: [],
}
