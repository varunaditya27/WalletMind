import type { Metadata } from "next";
import { Sora } from "next/font/google";
import "./globals.css";
import { Web3Provider } from "@/components/providers/web3-provider";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { Toaster } from "@/hooks/use-toast";

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "WalletMind | AI-Powered Autonomous Wallet System",
  description: "Next-generation blockchain platform merging AI autonomy with decentralized finance. Autonomous economic agents with cryptographic decision verification.",
  keywords: ["AI", "Blockchain", "Web3", "DeFi", "Autonomous Agents", "Smart Wallets"],
  authors: [{ name: "WalletMind Team" }],
  openGraph: {
    title: "WalletMind | AI-Powered Autonomous Wallet System",
    description: "Next-generation blockchain platform merging AI autonomy with decentralized finance.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={sora.variable}>
      <body className="antialiased flex flex-col min-h-screen">
        <Web3Provider>
          <Navbar />
          <main className="flex-1 pt-16">
            {children}
          </main>
          <Footer />
          <Toaster />
        </Web3Provider>
      </body>
    </html>
  );
}
