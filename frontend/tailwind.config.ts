import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas:  "#0B0F19",
        glass:   "#131B2E",
        // Accent palette
        cyan:    { DEFAULT: "#00F5FF", dim: "rgba(0,245,255,0.15)", glow: "rgba(0,245,255,0.08)" },
        purple:  { DEFAULT: "#9B5DE5", dim: "rgba(155,93,229,0.15)", glow: "rgba(155,93,229,0.08)" },
        amber:   { DEFAULT: "#FFB800", dim: "rgba(255,184,0,0.15)",  glow: "rgba(255,184,0,0.08)" },
        emerald: { DEFAULT: "#00D68F" },
        rose:    { DEFAULT: "#FF4D6D" },
        // Text scale
        text: {
          primary:   "#E8EDF5",
          secondary: "#8892A4",
          muted:     "#4A5568",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        "glow-cyan":   "0 0 24px rgba(0,245,255,0.18), 0 0 48px rgba(0,245,255,0.06)",
        "glow-purple": "0 0 24px rgba(155,93,229,0.18), 0 0 48px rgba(155,93,229,0.06)",
        "glow-amber":  "0 0 24px rgba(255,184,0,0.18),  0 0 48px rgba(255,184,0,0.06)",
        "glow-green":  "0 0 24px rgba(0,214,143,0.18),  0 0 48px rgba(0,214,143,0.06)",
        "card":        "0 1px 0 rgba(255,255,255,0.04) inset, 0 4px 24px rgba(0,0,0,0.4)",
      },
      backdropBlur: {
        "glass": "16px",
      },
      animation: {
        "spin-slow": "spin 3s linear infinite",
        "pulse-soft": "pulse 3s ease-in-out infinite",
      },
      backgroundImage: {
        "grid-subtle": "linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px)",
        "radial-canvas": "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(0,245,255,0.06) 0%, transparent 60%), radial-gradient(ellipse 60% 40% at 80% 80%, rgba(155,93,229,0.06) 0%, transparent 60%)",
      },
      backgroundSize: {
        "grid-subtle": "32px 32px",
      },
    },
  },
  plugins: [],
};
export default config;
