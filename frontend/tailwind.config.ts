import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        // High contrast colors for accessibility
        accessible: {
          bg: '#ffffff',
          'bg-dark': '#000000',
          text: '#000000',
          'text-dark': '#ffffff',
          primary: '#0066cc',
          success: '#008800',
          warning: '#cc6600',
          danger: '#cc0000',
        }
      },
      fontSize: {
        // Larger text sizes for accessibility
        'a11y-xs': '1rem',
        'a11y-sm': '1.125rem',
        'a11y-base': '1.25rem',
        'a11y-lg': '1.5rem',
        'a11y-xl': '1.875rem',
        'a11y-2xl': '2.25rem',
        'a11y-3xl': '3rem',
      }
    },
  },
  plugins: [],
}
export default config
