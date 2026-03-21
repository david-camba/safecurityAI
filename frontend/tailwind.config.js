/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: '#0a0a0a',      // Deep Dark
          card: '#141414',    // Dark Gray
          border: '#333333',  // Subtle Borders
          accent: '#00ff41',  // Matrix/Terminal Green
          error: '#ff3131',   // Red
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'IBM Plex Mono', 'ui-monospace', 'monospace'],
      }
    },
  },
  plugins: [
    //require('@tailwindcss/typography'),
  ],
}