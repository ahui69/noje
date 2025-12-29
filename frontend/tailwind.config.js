/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: '#0b0c10',
        panel: '#111218',
        accent: '#8b5cf6',
        subtle: '#1b1c23'
      }
    },
  },
  plugins: [],
};
