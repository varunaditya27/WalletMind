import type { Metadata } from "next";
import { JetBrains_Mono, Sora, Space_Grotesk } from "next/font/google";

import { CursorGlow } from "@/components/visual/cursor-glow";
import "./globals.css";

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sora",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const jetBrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "WalletMind | Autonomous AI Wallet OS",
  description:
    "WalletMind blends AI agents with ERC-4337 smart accounts, delivering verifiable autonomous finance.",
  metadataBase: new URL("https://walletmind.ai"),
  openGraph: {
    title: "WalletMind | Autonomous AI Wallet OS",
    description:
      "Control, verify, and monitor autonomous AI wallet agents with cryptographic transparency.",
    url: "https://walletmind.ai",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "WalletMind | Autonomous AI Wallet OS",
    description:
      "Control, verify, and monitor autonomous AI wallet agents with cryptographic transparency.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${sora.variable} ${spaceGrotesk.variable} ${jetBrains.variable} bg-background font-sans text-foreground antialiased`}
      >
        <CursorGlow />
        <div className="relative min-h-screen bg-wm-gradient">
          <div className="absolute inset-0 bg-wm-radial-blue" aria-hidden="true" />
          <div className="absolute inset-0 bg-wm-radial-gold" aria-hidden="true" />
          <div className="relative z-10 min-h-screen">{children}</div>
        </div>
      </body>
    </html>
  );
}
