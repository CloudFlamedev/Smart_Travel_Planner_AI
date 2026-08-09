/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: { ink: '#18201c', pine: '#254c3f', moss: '#5f8b74', sand: '#f5f1e8', coral: '#e97556' },
      boxShadow: { floating: '0 24px 60px rgba(24, 32, 28, .12)' },
    },
  },
  plugins: [],
}
