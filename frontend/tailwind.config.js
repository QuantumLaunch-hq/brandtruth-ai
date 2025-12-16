/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Quantum Green - Primary Brand
        quantum: {
          50:  '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        // Dark Backgrounds
        dark: {
          primary:  '#050505',
          surface:  '#0a0a0a',
          elevated: '#111111',
          hover:    '#1a1a1a',
        },
        // Borders
        border: {
          subtle:  '#1a1a1a',
          default: '#27272a',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'quantum-pulse': 'quantum-pulse 2s infinite',
        'quantum-spin': 'quantum-spin 1s linear infinite',
        'fade-in': 'fade-in 0.3s ease-out',
        'fade-up': 'fade-up 0.4s ease-out',
        'shimmer': 'shimmer 1.5s infinite',
      },
      keyframes: {
        'quantum-pulse': {
          '0%, 100%': { 
            opacity: '1',
            boxShadow: '0 0 20px rgba(34, 197, 94, 0.15)',
          },
          '50%': { 
            opacity: '0.8',
            boxShadow: '0 0 40px rgba(34, 197, 94, 0.25)',
          },
        },
        'quantum-spin': {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      boxShadow: {
        'quantum': '0 0 30px rgba(34, 197, 94, 0.15)',
        'quantum-lg': '0 0 50px rgba(34, 197, 94, 0.2)',
      },
    },
  },
  plugins: [],
}
