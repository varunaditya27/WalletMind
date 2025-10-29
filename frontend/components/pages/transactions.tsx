'use client';

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowUpRight, Filter, Shield, Wallet } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useWalletMindStore } from "@/lib/stores/walletmind-store";
import type { TransactionInfo, TransactionStatsResponse } from "@/lib/types";
import { useShallow } from "zustand/react/shallow";

export function TransactionsScreen() {
  const {
    transactionHistory,
    transactionStats,
    auditTrail,
    loading,
    errors,
    initializeTransactions,
  } = useWalletMindStore(
    useShallow((state) => ({
      transactionHistory: state.transactionHistory,
      transactionStats: state.transactionStats,
      auditTrail: state.auditTrail,
      loading: state.loading.transactions,
      errors: state.errors.transactions,
      initializeTransactions: state.initializeTransactions,
    }))
  );

  useEffect(() => {
    initializeTransactions();
  }, [initializeTransactions]);

  const [activeFilter, setActiveFilter] = useState<string>("all");

  const filters = useMemo(() => {
    const uniqueTypes = new Set<string>();
    transactionHistory.forEach((tx) => uniqueTypes.add(tx.transaction_type));
    return ["all", ...Array.from(uniqueTypes)];
  }, [transactionHistory]);

  const filteredTransactions = useMemo(() => {
    if (activeFilter === "all") {
      return transactionHistory;
    }
    return transactionHistory.filter((tx) => tx.transaction_type === activeFilter);
  }, [transactionHistory, activeFilter]);

  const ledger = useMemo(() => filteredTransactions.slice(0, 40), [filteredTransactions]);

  const cards = useMemo(() => deriveCards(transactionStats, transactionHistory), [transactionStats, transactionHistory]);
  const proofs = useMemo(() => auditTrail.slice(0, 6), [auditTrail]);

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-muted">Transaction Diary</p>
          <h1 className="text-2xl font-semibold text-foreground">On-chain actions & API spend</h1>
        </div>
        <div className="flex items-center gap-3">
          {errors && <Badge variant="warning" className="border-destructive/40 text-destructive">{errors}</Badge>}
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
          <Badge
            key={item}
            variant={activeFilter === item ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => setActiveFilter(item)}
          >
            {formatFilterLabel(item)}
          </Badge>
        ))}
      </section>

      <Card className="overflow-hidden">
        <CardHeader className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl">Ledger</CardTitle>
            <CardDescription>
              Sorted by newest first · {loading ? "refreshing" : `${transactionHistory.length} entries cached`}
            </CardDescription>
          </div>
          <Badge variant="outline">
            Total {transactionStats?.total_transactions ?? transactionHistory.length}
          </Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          {ledger.length === 0 && (
            <div className="rounded-2xl border border-white/5 bg-black/20 p-6 text-sm text-muted">
              No transactions recorded yet for this filter.
            </div>
          )}
          {ledger.map((tx, index) => (
            <motion.div
              key={tx.transaction_id ?? `${tx.transaction_hash}-${index}`}
              className="grid gap-3 rounded-2xl border border-white/5 bg-black/30 p-4 sm:grid-cols-[1.4fr_1fr_1fr_1fr]"
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
            >
              <div>
                <p className="font-mono text-sm text-foreground">{shortHash(tx.transaction_hash)}</p>
                <p className="text-xs text-muted">{relativeTime(tx.timestamp)}</p>
              </div>
              <div className="space-y-1">
                <Badge variant="outline">{formatFilterLabel(tx.transaction_type)}</Badge>
                <p className="text-xs text-muted">{formatNetwork(tx.network)}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-foreground">{formatAmount(tx)}</p>
                <p className="text-xs text-muted">Status: {formatStatus(tx.status)}</p>
              </div>
              <div className="space-y-1">
                <Badge variant={proofVariant(tx)}>{proofLabel(tx)}</Badge>
                <p className="text-xs text-muted">{tx.decision_hash ? "Proof logged" : "Awaiting proof"}</p>
              </div>
            </motion.div>
          ))}
        </CardContent>
      </Card>

      <section className="grid gap-6 lg:grid-cols-3">
        {cards.map((card) => (
          <InfoCard key={card.title} title={card.title} description={card.description} icon={card.icon} />
        ))}
      </section>

      <Card className="grid gap-6 border-white/10 bg-white/5 p-6 md:grid-cols-3">
        {proofs.length === 0 && (
          <p className="col-span-3 text-sm text-muted">No verification entries yet. Run an action to populate this view.</p>
        )}
        {proofs.map((proof) => (
          <div key={proof.entry_id} className="rounded-2xl border border-white/5 bg-black/30 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-muted">{proof.entry_type}</p>
            <p className="mt-2 font-mono text-sm text-foreground">
              {proof.transaction_hash ?? proof.decision_hash ?? proof.entry_id}
            </p>
            <p className="text-xs text-muted">Status · {proof.status}</p>
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

function deriveCards(stats: TransactionStatsResponse | null, history: TransactionInfo[]) {
  if (!stats) {
    return [
      {
        title: "Bundler performance",
        description: "Realtime metrics pending first transaction run.",
        icon: <ArrowUpRight className="h-5 w-5" />,
      },
      {
        title: "Guardrail activations",
        description: "Waiting for evaluator verdicts to arrive.",
        icon: <Shield className="h-5 w-5" />,
      },
      {
        title: "API wallet balance",
        description: `${history.length} ledger entries tracked locally`,
        icon: <Wallet className="h-5 w-5" />,
      },
    ];
  }

  return [
    {
      title: "Bundler performance",
      description: `Success rate ${formatPercent(stats.success_rate)} across ${stats.total_transactions} ops`,
      icon: <ArrowUpRight className="h-5 w-5" />,
    },
    {
      title: "Guardrail activations",
      description: `${stats.failed_transactions} prevented · ${stats.total_volume.toFixed(2)} total volume`,
      icon: <Shield className="h-5 w-5" />,
    },
    {
      title: "API wallet balance",
      description: `Avg value ${formatCurrency(stats.average_transaction_value)}`,
      icon: <Wallet className="h-5 w-5" />,
    },
  ];
}

function formatFilterLabel(value: string) {
  return value === "all"
    ? "All"
    : value
        .replace(/_/g, " ")
        .replace(/\b\w/g, (match) => match.toUpperCase());
}

function shortHash(hash?: string | null) {
  if (!hash) {
    return "Pending hash";
  }
  return `${hash.slice(0, 8)}…${hash.slice(-4)}`;
}

function relativeTime(timestamp: string) {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }
  const diff = Date.now() - date.getTime();
  const minutes = Math.max(1, Math.round(diff / 60_000));
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

function formatNetwork(network: string) {
  return formatFilterLabel(network);
}

function formatAmount(tx: TransactionInfo) {
  const currency = tx.metadata?.currency as string | undefined;
  if (currency && typeof tx.amount === "number") {
    return `${tx.amount.toFixed(2)} ${currency.toUpperCase()}`;
  }
  if (typeof tx.amount === "number") {
    return `${tx.amount.toFixed(4)} units`;
  }
  return "—";
}

function formatStatus(status: TransactionInfo["status"]) {
  return status.replace(/_/g, " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

function proofVariant(tx: TransactionInfo) {
  if (tx.status === "failed" || tx.status === "cancelled") {
    return "warning" as const;
  }
  if (tx.decision_hash) {
    return "default" as const;
  }
  return "outline" as const;
}

function proofLabel(tx: TransactionInfo) {
  if (tx.decision_hash) {
    return "Decision";
  }
  if (tx.transaction_hash) {
    return "Tx hash";
  }
  return tx.status === "pending" ? "Pending" : "No proof";
}

function formatPercent(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "0%";
  }
  const percent = value > 1 ? value : value * 100;
  return `${percent.toFixed(1)}%`;
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
