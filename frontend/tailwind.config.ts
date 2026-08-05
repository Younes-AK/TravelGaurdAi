import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#ffffff",
        panel: "#f7f8fa",
        line: "#e5e7eb",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgba(16, 24, 40, 0.05)",
        glow: "0 12px 24px -16px rgba(16, 24, 40, 0.35)",
      },
    },
  },
  plugins: [],
} satisfies Config;
