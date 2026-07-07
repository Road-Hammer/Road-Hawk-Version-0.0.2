import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        road: {
          bg: "#0c0f14",
          panel: "#151a23",
          border: "#2a3344",
          muted: "#8b97ab",
          amber: "#f59e0b",
          amberDim: "#b45309",
        },
      },
      fontFamily: {
        display: ["Georgia", "serif"],
        sans: ["Segoe UI", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;