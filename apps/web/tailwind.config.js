/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Grouping colors keeps this file clean and improves editor autocomplete.
      // Note: Using 'surface' prevents the repetitive `bg-bg-primary` utility class.
      colors: {
        surface: {
          primary: 'rgb(var(--bg-primary) / <alpha-value>)',
          secondary: 'rgb(var(--bg-secondary) / <alpha-value>)',
          tertiary: 'rgb(var(--bg-tertiary) / <alpha-value>)',
          hover: 'rgb(var(--bg-hover) / <alpha-value>)',
        },
        border: {
          default: 'rgb(var(--border-default) / <alpha-value>)',
          active: 'rgb(var(--border-active) / <alpha-value>)',
        },
        severity: {
          critical: 'rgb(var(--severity-critical) / <alpha-value>)',
          high: 'rgb(var(--severity-high) / <alpha-value>)',
          medium: 'rgb(var(--severity-medium) / <alpha-value>)',
          low: 'rgb(var(--severity-low) / <alpha-value>)',
          info: 'rgb(var(--severity-info) / <alpha-value>)',
        },
        confidence: {
          high: 'rgb(var(--confidence-high) / <alpha-value>)',
          medium: 'rgb(var(--confidence-medium) / <alpha-value>)',
          low: 'rgb(var(--confidence-low) / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        mono: ['var(--font-mono)'],
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-slow': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        }
      },
      animation: {
        'fade-in': 'fade-in 0.3s ease-out forwards',
        'slide-up': 'slide-up 0.4s ease-out forwards',
        'pulse-slow': 'pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}