/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Apple Design inspired dark theme
        'slate': {
          950: '#09090b',
          900: '#0f0f12',
          850: '#18181b',
          800: '#27272a',
        },
        'teal': {
          500: '#14b8a6',
          400: '#2dd4bf',
        },
        'indigo': {
          500: '#6366f1',
          400: '#818cf8',
        }
      },
      backdropBlur: {
        'xs': '2px',
        'apple': '20px',
      },
      animation: {
        'spring-in': 'spring-in 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'fade-in': 'fade-in 0.3s ease-out',
      },
      keyframes: {
        'spring-in': {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
