import type { Metadata } from "next";

import { SettingsScreen } from "@/components/pages/settings";

export const metadata: Metadata = {
  title: "Settings | WalletMind",
  description: "Configure guardians, providers, and guardrails for WalletMind agents.",
};

export default function SettingsPage() {
  return <SettingsScreen />;
}
