import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
        "./content/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                porcelain: "#f8fafc",
                "porcelain-dark": "#f1f5f9",
                mint: {
                    50: "#f0fdf4",
                    100: "#dcfce7",
                    200: "#bbf7d0",
                    300: "#86efac",
                    400: "#4ade80",
                    500: "#22c55e",
                },
                sky: {
                    50: "#f0f9ff",
                    100: "#e0f2fe",
                    200: "#bae6fd",
                    300: "#7dd3fc",
                    400: "#38bdf8",
                    500: "#0ea5e9",
                },
                coral: {
                    50: "#fff7ed",
                    100: "#ffedd5",
                    200: "#fed7aa",
                    300: "#fdba74",
                    400: "#fb923c",
                    500: "#f97316",
                },
                slate: {
                    850: "#1a2332",
                    900: "#0f172a",
                    950: "#020617",
                },
            },
            fontFamily: {
                sans: ["var(--font-inter)", "system-ui", "sans-serif"],
                mono: ["var(--font-jetbrains)", "monospace"],
            },
            backdropBlur: {
                "2xl": "40px",
                "3xl": "64px",
            },
            animation: {
                "fade-in": "fadeIn 0.5s ease-out",
                "slide-up": "slideUp 0.5s ease-out",
                "slide-in-right": "slideInRight 0.3s ease-out",
                glow: "glow 2s ease-in-out infinite alternate",
                "pulse-soft": "pulseSoft 3s ease-in-out infinite",
            },
            keyframes: {
                fadeIn: {
                    "0%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
                slideUp: {
                    "0%": { opacity: "0", transform: "translateY(20px)" },
                    "100%": { opacity: "1", transform: "translateY(0)" },
                },
                slideInRight: {
                    "0%": { opacity: "0", transform: "translateX(-10px)" },
                    "100%": { opacity: "1", transform: "translateX(0)" },
                },
                glow: {
                    "0%": { boxShadow: "0 0 5px rgba(34, 197, 94, 0.3)" },
                    "100%": { boxShadow: "0 0 20px rgba(34, 197, 94, 0.6)" },
                },
                pulseSoft: {
                    "0%, 100%": { opacity: "1" },
                    "50%": { opacity: "0.7" },
                },
            },
            boxShadow: {
                glass: "0 8px 32px 0 rgba(31, 38, 135, 0.07)",
                "glass-lg": "0 16px 48px 0 rgba(31, 38, 135, 0.1)",
                soft: "0 2px 8px -2px rgba(0, 0, 0, 0.05), 0 4px 16px -4px rgba(0, 0, 0, 0.08)",
            },
        },
    },
    plugins: [],
};

export default config;
