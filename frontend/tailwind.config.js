/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#EFF6FF",
          100: "#DBEAFE",
          500: "#3B82F6",
          600: "#2563EB",
          700: "#1D4ED8",
        },
        surface: {
          page: "#F4F6F9",
          card: "#FFFFFF",
          sidebar: "#FFFFFF",
          border: "#E5E9F0",
          hover: "#F1F5F9",
        },
        ink: {
          hi: "#0F172A",
          mid: "#475569",
          dim: "#94A3B8",
        },
        status: {
          critical: "#E11D48",
          criticalBg: "#FEF1F3",
          warning: "#D97706",
          warningBg: "#FEF6E7",
          normal: "#16A34A",
          normalBg: "#EDFBF3",
          info: "#2563EB",
          infoBg: "#EFF6FF",
        },
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgba(15, 23, 42, 0.04), 0 1px 3px 0 rgba(15, 23, 42, 0.06)",
        panel: "0 1px 3px 0 rgba(15, 23, 42, 0.08)",
      },
      borderRadius: {
        card: "12px",
      },
    },
  },
  plugins: [],
};
