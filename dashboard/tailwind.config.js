/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        threat: {
          high: '#E24B4A',
          med: '#EF9F27',
          low: '#1D9E75',
        },
      },
    },
  },
  plugins: [],
}
