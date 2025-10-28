'use client';

import { motion } from "framer-motion";
import { ArrowUpRight, Filter, Shield, Wallet } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const filters = ["All", "Swaps", "API spend", "Bridging", "Gas"];

const transactions = [
  {
    hash: "0x6af2d3…18b7",
    type: "Swap",
    network: "Sepolia",
    value: "1.42 ETH",
    status: "Settled",
    timestamp: "2m ago",
    proof: "decision",
  },
  {
    hash: "0x9b44c1…17aa",
    type: "API spend",
    network: "Polygon Amoy",
    value: "$42",
    status: "Paid",
    timestamp: "16m ago",
    proof: "receipt",
  },
  {
    hash: "0xff21b8…b1bd",
    type: "Gas",
    network: "Base Goerli",
    value: "0.0021 ETH",
    status: "Confirming",
    timestamp: "24m ago",
    proof: "queued",
  },
  {
    hash: "0xdb27ec…c4e0",
    type: "Swap",
    network: "Sepolia",
    value: "2.01 ETH",
    status: "Settled",
    timestamp: "58m ago",
    proof: "decision",
  },
];

const proofs = [
  {
    title: "Decision hash",
    hash: "0x6af2d3…18b7",
    description: "Logged pre-transaction via AgentWallet.sol",
  },
  {
    title: "IPFS rationale",
    hash: "ipfs://bafy…zk44",
    description: "Contains plan JSON + evaluator notes",
  },
  {
    title: "Safe module",
    hash: "module#limit-5000",
    description: "Enforced via spending guard extension",
  },
];

export function TransactionsScreen() {
  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-muted">Transaction Diary</p>
          <h1 className="text-2xl font-semibold text-foreground">On-chain actions & API spend</h1>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm">
            <Filter className="h-4 w-4" />
            Advanced filters
          </Button>
          <Button size="sm">
            Export CSV
          </Button>
        </div>
      </div>

      <section className="flex flex-wrap gap-3">
        {filters.map((item) => (
          <Badge key={item} variant={item === "All" ? "default" : "outline"}>
            {item}
          </Badge>
        ))}
      </section>

      <Card className="overflow-hidden">
        <CardHeader className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl">Ledger</CardTitle>
            <CardDescription>Sorted by newest first · Bundler latency avg 1.8s</CardDescription>
          </div>
          <Badge variant="outline">Total 428 entries</Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          {transactions.map((tx, index) => (
            <motion.div
              key={tx.hash}
              className="grid gap-3 rounded-2xl border border-white/5 bg-black/30 p-4 sm:grid-cols-[1.4fr_1fr_1fr_1fr]"
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
            >
              <div>
                <p className="font-mono text-sm text-foreground">{tx.hash}</p>
                <p className="text-xs text-muted">{tx.timestamp}</p>
              </div>
              <div className="space-y-1">
                <Badge variant="outline">{tx.type}</Badge>
                <p className="text-xs text-muted">{tx.network}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-foreground">{tx.value}</p>
                <p className="text-xs text-muted">Status: {tx.status}</p>
              </div>
              <div className="space-y-1">
                <Badge variant={proofTone(tx.proof)}>{tx.proof}</Badge>
                <p className="text-xs text-muted">Proof verified</p>
              </div>
            </motion.div>
          ))}
        </CardContent>
      </Card>

      <section className="grid gap-6 lg:grid-cols-3">
        <InfoCard
          title="Bundler performance"
          icon={<ArrowUpRight className="h-5 w-5" />}
          description="Sepolia bundler latency steady at sub 2s with 0 failures in 24h."
        />
        <InfoCard
          title="Guardrail activations"
          icon={<Shield className="h-5 w-5" />}
          description="Spending guard prevented 2 attempts exceeding configured cap."
        />
        <InfoCard
          title="API wallet balance"
          icon={<Wallet className="h-5 w-5" />}
          description="USDC balance at $1,820. Automatic refill threshold set to $1,000."
        />
      </section>

      <Card className="grid gap-6 border-white/10 bg-white/5 p-6 md:grid-cols-3">
        {proofs.map((proof) => (
          <div key={proof.title} className="rounded-2xl border border-white/5 bg-black/30 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-muted">{proof.title}</p>
            <p className="mt-2 font-mono text-sm text-foreground">{proof.hash}</p>
            <p className="text-xs text-muted">{proof.description}</p>
          </div>
        ))}
      </Card>
    </div>
  );
}

function InfoCard({ title, description, icon }: { title: string; description: string; icon: ReactNode }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-center gap-3 text-accent">
          {icon}
          <h3 className="text-lg font-semibold text-foreground">{title}</h3>
        </div>
        <p className="text-sm text-muted">{description}</p>
      </CardContent>
    </Card>
  );
}

function proofTone(kind: string) {
  switch (kind) {
    case "decision":
      return "default";
    case "receipt":
      return "gold";
    default:
      return "outline";
  }
}
