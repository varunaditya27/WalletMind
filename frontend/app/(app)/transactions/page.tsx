import type { Metadata } from "next";

import { TransactionsScreen } from "@/components/pages/transactions";

export const metadata: Metadata = {
  title: "Transactions | WalletMind",
  description: "Explore verified agent transactions, API spend, and guardrail activity.",
};

export default function TransactionsPage() {
  return <TransactionsScreen />;
}
