import type { Metadata } from "next";

import { AgentConsoleScreen } from "@/components/pages/agent-console";

export const metadata: Metadata = {
  title: "Agent Console | WalletMind",
  description: "Inspect the WalletMind agent cognition stream and task graph in real-time.",
};

export default function AgentPage() {
  return <AgentConsoleScreen />;
}
