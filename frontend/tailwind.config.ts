import type { Config } from "tailwindcss";

const config: Config = {
	darkMode: "class",
			content: [
				"./app/**/*.{ts,tsx,js,jsx,md,mdx}",
				"./components/**/*.{ts,tsx,js,jsx,md,mdx}",
				"./lib/**/*.{ts,tsx,js,jsx,md,mdx}",
				"./ui/**/*.{ts,tsx,js,jsx,md,mdx}",
				"./content/**/*.{md,mdx}",
			],
	theme: {
		container: {
			center: true,
			padding: {
				DEFAULT: "1.5rem",
				lg: "2rem",
				xl: "2.5rem",
				"2xl": "3rem",
			},
			screens: {
				"2xl": "1440px",
			},
		},
		extend: {
			colors: {
				background: "#0D0D0D",
				foreground: "#EAEAEA",
				surface: {
					DEFAULT: "#1A1A1A",
					subtle: "rgba(26, 26, 26, 0.85)",
					elevated: "rgba(34, 34, 34, 0.95)",
				},
				accent: {
					DEFAULT: "#00BFFF",
					50: "#E6F6FF",
					100: "#C7ECFF",
					200: "#8CDAFF",
					300: "#52C7FF",
					400: "#1AB8FF",
					500: "#00BFFF",
					600: "#0195CC",
					700: "#026B99",
					800: "#034466",
					900: "#032D47",
				},
				gold: {
					DEFAULT: "#E6B400",
					soft: "#FFD166",
					400: "#FFD166",
					500: "#E6B400",
					600: "#C29300",
				},
				muted: {
					DEFAULT: "#9CA3AF",
					200: "#6B7280",
					300: "#4B5563",
				},
				success: "#22C55E",
				warning: "#F59E0B",
				danger: "#FF4D4D",
				info: "#38BDF8",
				card: "rgba(19, 19, 19, 0.75)",
				outline: "rgba(255, 255, 255, 0.05)",
			},
			fontFamily: {
				sans: ["var(--font-sora)", "Sora", "system-ui", "sans-serif"],
				heading: [
					"var(--font-space-grotesk)",
					"Space Grotesk",
					"Sora",
					"system-ui",
					"sans-serif",
				],
				mono: [
					"var(--font-jetbrains-mono)",
					"JetBrains Mono",
					"ui-monospace",
					"SFMono-Regular",
					"Menlo",
					"monospace",
				],
				numeric: [
					"var(--font-jetbrains-mono)",
					"JetBrains Mono",
					"ui-monospace",
					"monospace",
				],
			},
			backgroundImage: {
				"wm-gradient":
					"linear-gradient(180deg, rgba(13,13,13,1) 0%, rgba(20,20,20,1) 100%)",
				"wm-radial-blue":
					"radial-gradient(circle at 30% 20%, rgba(0,191,255,0.35), transparent 60%)",
				"wm-radial-gold":
					"radial-gradient(circle at 70% 80%, rgba(230,180,0,0.2), transparent 65%)",
				"wm-glass":
					"linear-gradient(145deg, rgba(26,26,26,0.65) 0%, rgba(20,20,20,0.3) 100%)",
			},
			boxShadow: {
				glass: "0 24px 60px -20px rgba(0, 0, 0, 0.65)",
				"glass-sm": "0 12px 30px -15px rgba(0, 0, 0, 0.55)",
				"accent-ring":
					"0 0 0 1px rgba(0,191,255,0.35), 0 10px 35px rgba(0,191,255,0.2)",
				"gold-ring":
					"0 0 0 1px rgba(230,180,0,0.35), 0 10px 35px rgba(230,180,0,0.18)",
				ambient: "0 36px 140px -40px rgba(0, 0, 0, 0.95)",
			},
			dropShadow: {
				"glow-blue": "0 0 1.75rem rgba(0, 191, 255, 0.45)",
				"glow-gold": "0 0 1.75rem rgba(230, 180, 0, 0.35)",
				"glow-danger": "0 0 1.5rem rgba(255, 77, 77, 0.4)",
			},
			borderRadius: {
				glass: "1.5rem",
				xl: "1.35rem",
			},
			backdropBlur: {
				18: "18px",
				30: "30px",
			},
			transitionTimingFunction: {
				gentle: "cubic-bezier(0.22, 1, 0.36, 1)",
				swift: "cubic-bezier(0.76, 0, 0.24, 1)",
			},
			transitionDuration: {
				400: "400ms",
				600: "600ms",
			},
			keyframes: {
				"ai-pulse": {
					"0%, 100%": {
						boxShadow: "0 0 0 0 rgba(0,191,255,0.35)",
					},
					"50%": {
						boxShadow: "0 0 0 18px rgba(0,191,255,0)",
					},
				},
				"gold-ripple": {
					"0%": {
						transform: "scale(0.9)",
						opacity: "0.9",
					},
					"70%": {
						transform: "scale(1.2)",
						opacity: "0",
					},
					"100%": {
						opacity: "0",
					},
				},
				"fade-slide": {
					"0%": {
						opacity: "0",
						transform: "translateY(12px)",
					},
					"100%": {
						opacity: "1",
						transform: "translateY(0)",
					},
				},
				float: {
					"0%, 100%": {
						transform: "translateY(0)",
					},
					"50%": {
						transform: "translateY(-6px)",
					},
				},
				"cursor-trail": {
					"0%": {
						transform: "scale(0.85)",
						opacity: "0.65",
					},
					"100%": {
						transform: "scale(1.4)",
						opacity: "0",
					},
				},
				"gradient-move": {
					"0%": {
						backgroundPosition: "0% 50%",
					},
					"50%": {
						backgroundPosition: "100% 50%",
					},
					"100%": {
						backgroundPosition: "0% 50%",
					},
				},
			},
			animation: {
				"ai-pulse": "ai-pulse 2.5s cubic-bezier(0.66, 0, 0.34, 1) infinite",
				"gold-ripple": "gold-ripple 1.6s ease-out",
				"fade-slide": "fade-slide 0.6s ease-out both",
				"float-slow": "float 6s ease-in-out infinite",
				"cursor-trail": "cursor-trail 1.25s ease-out forwards",
				"gradient-move": "gradient-move 18s ease-in-out infinite",
			},
			ringColor: {
				accent: "#00BFFF",
				gold: "#E6B400",
			},
			ringOffsetColor: {
				dark: "rgba(13, 13, 13, 0.7)",
			},
			spacing: {
				18: "4.5rem",
				22: "5.5rem",
			},
			zIndex: {
				60: "60",
				70: "70",
				80: "80",
			},
		},
	},
	plugins: [],
};

export default config;
