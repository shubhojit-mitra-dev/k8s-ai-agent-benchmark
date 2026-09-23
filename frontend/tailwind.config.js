/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#090d16",
        surface: "#111827",
        "surface-raised": "#1f2937",
        "surface-border": "#374151",
        primary: "#38bdf8",
        secondary: "#818cf8",
        accent: "#34d399",
        danger: "#f87171",
        warning: "#fbbf24",
      },
    },
  },
  plugins: [],
}
