"use client";

import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { sepolia, polygonAmoy, baseGoerli } from "wagmi/chains";

export const wagmiConfig = getDefaultConfig({
  appName: "WalletMind",
  projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || "YOUR_PROJECT_ID",
  chains: [sepolia, polygonAmoy, baseGoerli],
  ssr: true,
});
