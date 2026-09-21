/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Pulled from the Talkify logo: deep navy wordmark, blue-to-purple
        // gradient accent (the chat bubble / sparkle).
        brand: {
          50: '#eef1ff',
          100: '#dfe3ff',
          200: '#c1c9ff',
          300: '#9ba6ff',
          400: '#7c7bff',
          500: '#6858f5',
          600: '#5a3fe0',
          700: '#4b32bd',
          800: '#3d2a97',
          900: '#241854',
        },
        ink: '#0b1130',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
      },
    },
  },
  plugins: [],
}
