'use client';

import { useEffect, useMemo } from "react";
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
import { useWalletMindStore } from "@/lib/stores/walletmind-store";
import type { AgentHealth, AuditEntry, BalanceResponse, WebsocketEvent } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useShallow } from "zustand/react/shallow";

const highlightIcons = {
  uptime: ShieldCheck,
  proofs: DatabaseZap,
  gas: Zap,
} as const;

export function DashboardScreen() {
  const {
    balances,
    networks,
    transactionStats,
    agentHealth,
    auditTrail,
    websocketMessages,
    lastSyncedAt,
    loading,
    errors,
    initializeDashboard,
  } = useWalletMindStore(
    useShallow((state) => ({
      balances: state.balances,
      networks: state.networks,
      transactionStats: state.transactionStats,
      agentHealth: state.agentHealth,
      auditTrail: state.auditTrail,
      websocketMessages: state.websocketMessages,
      lastSyncedAt: state.lastSyncedAt,
      loading: state.loading.dashboard,
      errors: state.errors.dashboard,
      initializeDashboard: state.initializeDashboard,
    }))
  );

  useEffect(() => {
    initializeDashboard();
  }, [initializeDashboard]);

  const balanceCards = useMemo(() => {
    if (!balances.length) {
      return networks.slice(0, 3).map((network) => ({
        label: network.name,
        amount: "—",
        sublabel: network.native_currency,
        badge: "Awaiting data",
      }));
    }

    return balances.slice(0, 3).map((balance) => {
      const network = networks.find((net) => net.network === balance.network);
      const primaryToken = balance.tokens?.[0];
      const amount = primaryToken
        ? `${formatNumber(primaryToken.amount)} ${primaryToken.symbol}`
        : `${formatNumber(balance.balance)} ${network?.native_currency ?? ""}`.trim();
      const usd = balance.balance_usd ?? primaryToken?.amount_usd;
      return {
        label: network?.name ?? balance.network,
        amount,
        sublabel: usd ? formatCurrency(usd) : balance.address,
        badge: `${balance.tokens?.length ?? 0} tokens`,
      };
    });
  }, [balances, networks]);

  const highlights = useMemo(() => {
    const stats = transactionStats;
    if (!stats) {
      return [
        {
          key: "uptime",
          title: "Success rate",
          subtitle: "Awaiting stats",
          metric: "—",
        },
        {
          key: "proofs",
          title: "Proof integrity",
          subtitle: "Audit trail entries",
          metric: auditTrail.length ? `${auditTrail.length}` : "—",
        },
        {
          key: "gas",
          title: "Gas spend",
          subtitle: "Total units",
          metric: "—",
        },
      ];
    }

    return [
      {
        key: "uptime",
        title: "Success rate",
        subtitle: `${stats.successful_transactions} / ${stats.total_transactions} settled`,
        metric: formatPercent(stats.success_rate),
      },
      {
        key: "proofs",
        title: "Average tx value",
        subtitle: "Weighted across all intents",
        metric: formatCurrency(stats.average_transaction_value),
      },
      {
        key: "gas",
        title: "Gas spend",
        subtitle: "Lifetime across supported chains",
        metric: `${formatNumber(stats.total_gas_spent)} gwei`,
      },
    ];
  }, [transactionStats, auditTrail.length]);

  const liveActivity = useMemo(() => {
    const realtime = websocketMessages.slice(0, 6).map((event, index) => toActivityItem(event, index));
    if (realtime.length) {
      return realtime;
    }

    return auditTrail.slice(0, 6).map((entry) => ({
      id: entry.entry_id,
      title: entry.action || entry.entry_type,
      detail: entry.agent_type ? `Agent · ${capitalize(entry.agent_type)}` : entry.status,
      status: entry.status,
      timestamp: entry.timestamp,
    }));
  }, [websocketMessages, auditTrail]);

  const agentStatus = useMemo(() => {
    if (!agentHealth.length) {
      const defaults: AgentHealth["agent_type"][] = ["planner", "executor", "evaluator", "communicator"];
      return defaults.map((type) => ({
        agent_type: type,
        status: "waiting" as AgentHealth["status"],
        uptime: 0,
        total_requests: 0,
        success_rate: 0,
        last_active: new Date().toISOString(),
      }));
    }
    return agentHealth;
  }, [agentHealth]);

  const latestProofs = useMemo(() => {
    if (!auditTrail.length) {
      return [] as AuditEntry[];
    }
    return auditTrail.slice(0, 3);
  }, [auditTrail]);

  const syncedLabel = loading
    ? "Syncing…"
    : lastSyncedAt
      ? `Synced · ${formatRelativeTime(lastSyncedAt)}`
      : "Synced · awaiting";

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-muted">Mission Control</p>
          <h1 className="text-2xl font-semibold text-foreground">WalletMind Autonomy Overview</h1>
        </div>
        <div className="flex items-center gap-3">
          {errors && <Badge variant="warning" className="border-destructive/40 text-destructive">{errors}</Badge>}
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
        {balanceCards.map((balance) => (
          <Card key={balance.label}>
            <CardBackground className="bg-[radial-gradient(circle_at_top,rgba(0,191,255,0.2),transparent_70%)]" />
            <CardHeader>
              <p className="text-xs uppercase tracking-[0.25em] text-muted">{balance.label}</p>
              <CardTitle className="mt-3 text-3xl font-semibold">{balance.amount}</CardTitle>
              <CardDescription className="mt-1 text-xs uppercase tracking-[0.35em] text-accent">
                {balance.sublabel}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Badge variant="default">{balance.badge}</Badge>
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
            <Badge variant="outline">{syncedLabel}</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            {liveActivity.length === 0 && (
              <div className="rounded-2xl border border-white/5 bg-black/20 p-6 text-sm text-muted">
                Awaiting realtime events from orchestrator…
              </div>
            )}
            {liveActivity.map((item, index) => (
              <motion.div
                key={item.id ?? `${item.title}-${index}`}
                className="rounded-2xl border border-white/5 bg-black/30 p-4"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-foreground">{item.title}</p>
                  <span className="text-xs text-muted">{formatRelativeTime(item.timestamp)}</span>
                </div>
                <p className="mt-1 text-sm text-muted">{item.detail}</p>
                {item.status && (
                  <Badge variant="gold" className="mt-3">
                    {item.status}
                  </Badge>
                )}
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
            {agentStatus.map((agent) => (
              <div key={agent.agent_type} className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-foreground">{capitalize(agent.agent_type)}</p>
                  <p className="text-xs text-muted">
                    Success {formatPercent(agent.success_rate)} · {formatNumber(agent.total_requests)} ops
                  </p>
                </div>
                <Badge variant={statusVariant(agent.status)}>{statusLabel(agent.status)}</Badge>
              </div>
            ))}

            <div className="rounded-2xl border border-accent/30 bg-accent/10 p-4 text-sm text-foreground">
              <p className="font-semibold">Next Action</p>
              <p className="mt-1 text-muted">
                {liveActivity[0]?.detail ?? "Planner evaluating incoming instructions."}
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        {highlights.map((item) => {
          const Icon = highlightIcons[item.key as keyof typeof highlightIcons];
          return (
            <Card key={item.key}>
              <CardContent className="flex flex-col gap-4">
                <div className={cn("flex h-12 w-12 items-center justify-center rounded-xl", highlightTone(item.key))}>
                  {Icon && <Icon className="h-6 w-6" />}
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-muted">{item.subtitle}</p>
                  <h3 className="mt-2 text-xl font-semibold text-foreground">{item.title}</h3>
                </div>
                <p className="text-3xl font-semibold text-foreground">{item.metric}</p>
              </CardContent>
            </Card>
          );
        })}
      </section>

      <div className="rounded-3xl border border-white/5 bg-black/30 p-6 backdrop-blur-18">
        <p className="text-xs uppercase tracking-[0.3em] text-muted">On-chain verifications</p>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          {latestProofs.length === 0 && (
            <p className="col-span-3 text-sm text-muted">No on-chain proofs recorded yet for this wallet.</p>
          )}
          {latestProofs.map((proof) => (
            <div key={proof.entry_id} className="space-y-2">
              <p className="font-mono text-sm text-accent">
                {proof.decision_hash ?? proof.transaction_hash ?? proof.entry_id}
              </p>
              <p className="text-xs text-muted">{proof.action}</p>
              <p className="text-xs text-muted">Status · {proof.status}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function highlightTone(key: string) {
  switch (key) {
    case "uptime":
      return "bg-success/15 text-success";
    case "gas":
      return "bg-gold/15 text-gold";
    default:
      return "bg-accent/15 text-accent";
  }
}

function statusVariant(status: AgentHealth["status"]) {
  switch (status) {
    case "thinking":
      return "default" as const;
    case "executing":
      return "gold" as const;
    case "idle":
    case "waiting":
      return "outline" as const;
    case "error":
      return "warning" as const;
    default:
      return "outline" as const;
  }
}

function statusLabel(status: AgentHealth["status"]) {
  switch (status) {
    case "thinking":
      return "Thinking";
    case "executing":
      return "Executing";
    case "idle":
      return "Idle";
    case "waiting":
      return "Waiting";
    case "error":
      return "Attention";
    default:
      return capitalize(status ?? "waiting");
  }
}

function toActivityItem(event: WebsocketEvent, index: number) {
  const label = event.event ?? event.type ?? `Event ${index + 1}`;
  const channel = event.channel ? `Channel · ${capitalize(event.channel)}` : undefined;
  const detail = typeof event.data?.message === "string"
    ? event.data.message
    : channel ?? "Realtime update received.";
  return {
    id: `${label}-${event.timestamp ?? index}`,
    title: label,
    detail,
    status: event.status ?? event.type,
    timestamp: event.timestamp ?? new Date().toISOString(),
  };
}

function capitalize(value?: string | null) {
  if (!value) {
    return "";
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatNumber(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "0";
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

function formatCurrency(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "—";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "0%";
  }
  const percent = value > 1 ? value : value * 100;
  return `${percent.toFixed(1)}%`;
}

function formatRelativeTime(timestamp?: string) {
  if (!timestamp) {
    return "—";
  }
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }
  const diff = Date.now() - date.getTime();
  if (diff < 30_000) {
    return "just now";
  }
  const minutes = Math.round(diff / 60_000);
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.round(minutes / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}
