'use client';

import { useState } from "react";
import { motion } from "framer-motion";
import { KeyRound, Lock, Server, Zap } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const connections = [
  {
    name: "Owner Safe",
    address: "0x42ac…9f11",
    status: "Primary",
    icon: Lock,
  },
  {
    name: "Automation Safe",
    address: "0xcb81…1dea",
    status: "Guarded",
    icon: KeyRound,
  },
];

const providers = [
  {
    name: "Groq",
    plan: "LLM core · 70B",
    usage: "62%",
  },
  {
    name: "Google AI Studio",
    plan: "Gemini 1.5",
    usage: "21%",
  },
  {
    name: "Supabase",
    plan: "Postgres + Functions",
    usage: "41%",
  },
];

export function SettingsScreen() {
  const [spendingGuard, setSpendingGuard] = useState(true);
  const [multiNet, setMultiNet] = useState(true);
  const [telemetry, setTelemetry] = useState(false);

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-muted">Identity & Guardrails</p>
          <h1 className="text-2xl font-semibold text-foreground">Operate responsibly</h1>
        </div>
        <Button size="sm">Add new guardian</Button>
      </div>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_minmax(0,0.9fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Lock className="h-5 w-5 text-accent" />
              Smart account guardians
            </CardTitle>
            <CardDescription>Spending limits enforced at Safe module layer.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {connections.map((conn, index) => (
              <motion.div
                key={conn.address}
                className="flex items-center justify-between rounded-2xl border border-white/5 bg-black/30 p-4"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
              >
                <div className="flex items-center gap-3">
                  <conn.icon className="h-5 w-5 text-accent" />
                  <div>
                    <p className="text-sm font-semibold text-foreground">{conn.name}</p>
                    <p className="font-mono text-xs text-muted">{conn.address}</p>
                  </div>
                </div>
                <Badge variant="gold">{conn.status}</Badge>
              </motion.div>
            ))}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-muted">
              Emergency pause enabled · Operator key required for overrides.
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Server className="h-5 w-5 text-accent" />
              Connected providers
            </CardTitle>
            <CardDescription>WalletMind maintains auto-top-ups per provider.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {providers.map((provider, index) => (
              <motion.div
                key={provider.name}
                className="rounded-2xl border border-white/5 bg-black/30 p-4"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-foreground">{provider.name}</p>
                    <p className="text-xs text-muted">{provider.plan}</p>
                  </div>
                  <Badge variant="outline">Usage {provider.usage}</Badge>
                </div>
                <div className="mt-3 h-2 w-full rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-accent"
                    style={{ width: provider.usage }}
                  />
                </div>
              </motion.div>
            ))}
          </CardContent>
        </Card>
      </section>

      <Card className="grid gap-6 border-accent/30 bg-accent/10 p-6 md:grid-cols-3">
        <ToggleCard
          label="Spending guard"
          description="Caps agent transactions at configured limits."
          active={spendingGuard}
          onToggle={setSpendingGuard}
        />
        <ToggleCard
          label="Multi-network routing"
          description="Allow agents to select Polygon Amoy or Base Goerli when cheaper."
          active={multiNet}
          onToggle={setMultiNet}
        />
        <ToggleCard
          label="Telemetry sharing"
          description="Send anonymized stats to improve WalletMind models."
          active={telemetry}
          onToggle={setTelemetry}
        />
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Zap className="h-5 w-5 text-gold" />
            Automation routines
          </CardTitle>
          <CardDescription>Scheduled tasks triggered by LangGraph orchestrator.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          {[
            {
              name: "Weekly safe rotation",
              detail: "Rotates guardian keys and refreshes spending limits.",
            },
            {
              name: "API billing audit",
              detail: "Ensures invoice totals reconcile with on-chain spend.",
            },
            {
              name: "Liquidity sweep",
              detail: "Rebalances pools nightly with evaluator heuristics.",
            },
            {
              name: "Decision archive",
              detail: "Uploads proofs to IPFS + Supabase for compliance.",
            },
          ].map((routine, index) => (
            <motion.div
              key={routine.name}
              className="rounded-2xl border border-white/5 bg-black/30 p-4"
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
            >
              <p className="text-sm font-semibold text-foreground">{routine.name}</p>
              <p className="text-xs text-muted">{routine.detail}</p>
            </motion.div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

interface ToggleCardProps {
  label: string;
  description: string;
  active: boolean;
  onToggle: (value: boolean) => void;
}

function ToggleCard({ label, description, active, onToggle }: ToggleCardProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-foreground">{label}</p>
          <p className="text-xs text-muted">{description}</p>
        </div>
        <button
          type="button"
          onClick={() => onToggle(!active)}
          className={`relative inline-flex h-9 w-16 items-center rounded-full border border-white/10 transition ${
            active ? "bg-accent/40" : "bg-white/5"
          }`}
        >
          <motion.span
            layout
            className="absolute left-1 top-1 h-7 w-7 rounded-full bg-white/90 shadow-glass"
            animate={{ x: active ? 28 : 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
          />
        </button>
      </div>
      <p className="mt-3 text-[11px] text-muted/70">{active ? "Enabled" : "Disabled"}</p>
    </div>
  );
}
