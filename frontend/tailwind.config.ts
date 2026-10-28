import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        surface: "var(--surface)",
        foreground: "var(--foreground)",
        muted: "var(--muted)",
        primary: "var(--primary)",
        accent: "var(--accent)",
        highlight: "var(--highlight)",
        border: "var(--border)",
        success: "var(--success)",
        warning: "var(--warning)",
        destructive: "var(--destructive)",
      },
      fontFamily: {
        sans: ["Arial", "Helvetica", "sans-serif"],
      },
      maxWidth: { content: "1280px" },
    },
  },
  plugins: [],
};

export default config;
