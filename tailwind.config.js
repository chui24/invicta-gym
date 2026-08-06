/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html"
  ],
  theme: {
    extend: {
      colors: {
        'brand-bg': '#0d0d12',
        'brand-sidebar': '#121212',
        'brand-accent': '#d500f9',
        'brand-card': '#1e1e24',
        'brand-text': '#ffffff',
        'brand-muted': '#a0a0b0',
      },
      fontFamily: {
        'sans': ['Inter', 'Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
