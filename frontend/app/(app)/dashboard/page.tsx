import type { Metadata } from "next";

import { DashboardScreen } from "@/components/pages/dashboard";

export const metadata: Metadata = {
  title: "Dashboard | WalletMind",
  description: "Monitor balances, agent cognition, and on-chain proofs in real-time.",
};

export default function DashboardPage() {
  return <DashboardScreen />;
}
