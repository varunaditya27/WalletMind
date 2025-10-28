'use client';

import { motion } from "framer-motion";
import { Activity, ArrowUpRight, DatabaseZap, ShieldCheck, Zap } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardBackground,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

const balances = [
  {
    label: "Operational Balance",
    amount: "14.28 ETH",
    change: "+3.4%",
    network: "Sepolia",
  },
  {
    label: "API Spend",
    amount: "$482",
    change: "−6.2%",
    network: "Stablecoins",
  },
  {
    label: "Guarded Reserve",
    amount: "4,500 USDC",
    change: "Cap 10k",
    network: "Safe module",
  },
];

const highlights = [
  {
    title: "Strategy Uptime",
    subtitle: "Agents online",
    metric: "99.96%",
    icon: ShieldCheck,
    tone: "success" as const,
  },
  {
    title: "Proof Integrity",
    subtitle: "Logged decisions",
    metric: "48 / 48",
    icon: DatabaseZap,
    tone: "accent" as const,
  },
  {
    title: "Gas Efficiency",
    subtitle: "Blended Gwei",
    metric: "12.4",
    icon: Zap,
    tone: "gold" as const,
  },
];

const activity = [
  {
    title: "Arbitrage cycle complete",
    detail: "Executor bundled 3 swaps via Safe relay",
    status: "Success",
    time: "2m ago",
  },
  {
    title: "API credit top-up",
    detail: "Groq credits purchased autonomously",
    status: "Proof logged",
    time: "12m ago",
  },
  {
    title: "Risk evaluation",
    detail: "Evaluator downgraded Base liquidity route",
    status: "Mitigated",
    time: "46m ago",
  },
];

const agentStacks = [
  { label: "Planner", state: "Objectives refreshed", variant: "default" as const },
  { label: "Executor", state: "UserOp queue: 1", variant: "gold" as const },
  { label: "Evaluator", state: "8 heuristics active", variant: "outline" as const },
  { label: "Communicator", state: "Websocket link stable", variant: "default" as const },
];

export function DashboardScreen() {
  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-muted">Mission Control</p>
          <h1 className="text-2xl font-semibold text-foreground">WalletMind Autonomy Overview</h1>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm">
            Export Proof Ledger
          </Button>
          <Button size="sm">
            <ArrowUpRight className="h-4 w-4" />
            Deploy New Agent
          </Button>
        </div>
      </div>

      <section className="grid gap-6 lg:grid-cols-3">
        {balances.map((balance) => (
          <Card key={balance.label}>
            <CardBackground className="bg-[radial-gradient(circle_at_top,rgba(0,191,255,0.2),transparent_70%)]" />
            <CardHeader>
              <p className="text-xs uppercase tracking-[0.25em] text-muted">{balance.label}</p>
              <CardTitle className="mt-3 text-3xl font-semibold">{balance.amount}</CardTitle>
              <CardDescription className="mt-1 text-xs uppercase tracking-[0.35em] text-accent">
                {balance.network}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Badge variant="default">{balance.change}</Badge>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.2fr_minmax(0,0.8fr)]">
        <Card className="overflow-hidden">
          <CardHeader className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-muted">Live Activity</p>
              <CardTitle className="mt-2 flex items-center gap-2 text-xl">
                <Activity className="h-5 w-5" />
                Cognition Stream
              </CardTitle>
            </div>
            <Badge variant="outline">Synced · 4s ago</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            {activity.map((item, index) => (
              <motion.div
                key={item.title}
                className="rounded-2xl border border-white/5 bg-black/30 p-4"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-foreground">{item.title}</p>
                  <span className="text-xs text-muted">{item.time}</span>
                </div>
                <p className="mt-1 text-sm text-muted">{item.detail}</p>
                <Badge variant="gold" className="mt-3">
                  {item.status}
                </Badge>
              </motion.div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Agent Status</CardTitle>
            <CardDescription>LangGraph lanes monitored in real-time.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {agentStacks.map((agent) => (
              <div key={agent.label} className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-foreground">{agent.label}</p>
                  <p className="text-xs text-muted">{agent.state}</p>
                </div>
                <Badge variant={agent.variant}>{agent.variant === "outline" ? "Observe" : "Active"}</Badge>
              </div>
            ))}

            <div className="rounded-2xl border border-accent/30 bg-accent/10 p-4 text-sm text-foreground">
              <p className="font-semibold">Next Action</p>
              <p className="mt-1 text-muted">
                Planner evaluating market data feed before dispatching arbitrage plan to Executor.
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        {highlights.map((item) => (
          <Card key={item.title}>
            <CardContent className="flex flex-col gap-4">
              <div className={cn("flex h-12 w-12 items-center justify-center rounded-xl", highlightTone(item.tone))}>
                <item.icon className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-muted">{item.subtitle}</p>
                <h3 className="mt-2 text-xl font-semibold text-foreground">{item.title}</h3>
              </div>
              <p className="text-3xl font-semibold text-foreground">{item.metric}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <div className="rounded-3xl border border-white/5 bg-black/30 p-6 backdrop-blur-18">
        <p className="text-xs uppercase tracking-[0.3em] text-muted">On-chain verifications</p>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div className="space-y-2">
            <p className="font-mono text-sm text-accent">Decision Hash · 0x6af2d3…18b7</p>
            <p className="text-xs text-muted">Logged before execution, accessible via dashboard proof explorer.</p>
          </div>
          <div className="space-y-2">
            <p className="font-mono text-sm text-gold">Safe Tx · 0x9c1b…87ef</p>
            <p className="text-xs text-muted">Executed with guard module enforcing 5 ETH max limit.</p>
          </div>
          <div className="space-y-2">
            <p className="font-mono text-sm text-success">Bundler Receipt · OK</p>
            <p className="text-xs text-muted">Latency 1.8s via Biconomy relayer, fallback ready.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function highlightTone(tone: "success" | "accent" | "gold") {
  switch (tone) {
    case "success":
      return "bg-success/15 text-success";
    case "gold":
      return "bg-gold/15 text-gold";
    default:
      return "bg-accent/15 text-accent";
  }
}
