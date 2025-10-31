'use client';

import { useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { KeyRound, Lock, Server, Zap } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useWalletMindStore } from "@/lib/stores/walletmind-store";
import { authService } from "@/lib/services/auth-service";
import type { APIProviderInfo, WalletStatusResponse } from "@/lib/types";
import { useShallow } from "zustand/react/shallow";

export function SettingsScreen() {
  const {
    providers,
    walletStatus,
    preferences,
    loading,
    errors,
    initializeSettings,
    toggleSpendingGuard,
    toggleMultiNetwork,
    toggleTelemetry,
    pauseWallet,
    unpauseWallet,
  } = useWalletMindStore(
    useShallow((state) => ({
      providers: state.providers,
      walletStatus: state.walletStatus,
      preferences: state.preferences,
      loading: state.loading.settings,
      errors: state.errors.settings,
      initializeSettings: state.initializeSettings,
      toggleSpendingGuard: state.toggleSpendingGuard,
      toggleMultiNetwork: state.toggleMultiNetwork,
      toggleTelemetry: state.toggleTelemetry,
      pauseWallet: state.pauseWallet,
      unpauseWallet: state.unpauseWallet,
    }))
  );

  useEffect(() => {
    initializeSettings();
  }, [initializeSettings]);

  const connections = useMemo(() => deriveConnections(walletStatus), [walletStatus]);
  const providerCards = useMemo<APIProviderInfo[]>(() => providers, [providers]);
  const paused = walletStatus?.is_paused ?? false;

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-muted">Identity & Guardrails</p>
          <h1 className="text-2xl font-semibold text-foreground">Operate responsibly</h1>
        </div>
        <div className="flex items-center gap-2">
          {errors && <Badge variant="warning" className="border-destructive/40 text-destructive">{errors}</Badge>}
          <Button size="sm" onClick={paused ? unpauseWallet : pauseWallet}>
            {paused ? "Resume wallet" : "Pause wallet"}
          </Button>
        </div>
      </div>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_minmax(0,0.9fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Lock className="h-5 w-5 text-accent" />
              Smart account guardians
            </CardTitle>
            <CardDescription>
              {walletStatus ? "Derived from AgentWallet registry" : "Spending limits enforced at Safe module layer."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading && (
              <div className="rounded-2xl border border-white/5 bg-black/30 p-4 text-sm text-muted animate-pulse">
                Loading guardian connections...
              </div>
            )}
            {!loading && connections.length === 0 && (
              <div className="rounded-2xl border border-white/5 bg-black/30 p-4 text-sm text-muted">
                No guardians found. Connect a Safe owner to enable guardrails.
              </div>
            )}
            {!loading && connections.map((conn, index) => (
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
                <Badge variant={conn.variant}>{conn.status}</Badge>
              </motion.div>
            ))}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-muted">
              Emergency pause {paused ? "active" : "standby"} · Operator key required for overrides.
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
            {loading && (
              <div className="rounded-2xl border border-white/5 bg-black/30 p-4 text-sm text-muted animate-pulse">
                Loading API providers...
              </div>
            )}
            {!loading && providerCards.length === 0 && (
              <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
                <p className="text-sm text-muted mb-2">No providers configured yet.</p>
                <p className="text-xs text-muted/70">
                  Configure API providers in your backend .env file:
                </p>
                <code className="text-xs text-accent block mt-2 font-mono">
                  GROQ_API_KEY=your_key_here
                </code>
              </div>
            )}
            {!loading && providerCards.map((provider, index) => (
              <motion.div
                key={provider.provider}
                className="rounded-2xl border border-white/5 bg-black/30 p-4"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-foreground">{provider.name}</p>
                    <p className="text-xs text-muted">{provider.base_url}</p>
                  </div>
                  <Badge variant={provider.supported ? "outline" : "warning"}>
                    {provider.supported ? "Supported" : "Pending"}
                  </Badge>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs text-muted">
                  <span>{`Cost ${formatCurrency(provider.cost_per_request ?? 0)}/req`}</span>
                  <span className="font-mono text-[11px] uppercase tracking-[0.2em]">
                    {provider.provider}
                  </span>
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
          active={preferences.spendingGuard}
          disabled={loading}
          onToggle={toggleSpendingGuard}
        />
        <ToggleCard
          label="Multi-network routing"
          description="Allow agents to select Polygon Amoy or Base Goerli when cheaper."
          active={preferences.multiNetwork}
          disabled={loading}
          onToggle={toggleMultiNetwork}
        />
        <ToggleCard
          label="Telemetry sharing"
          description="Send anonymized stats to improve WalletMind models."
          active={preferences.telemetry}
          disabled={loading}
          onToggle={toggleTelemetry}
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
          {deriveAutomationRoutines(walletStatus).map((routine, index) => (
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
  disabled?: boolean;
  onToggle: (value: boolean) => void | Promise<void>;
}

type BadgeVariant = "default" | "gold" | "warning" | "outline" | "success";

interface ConnectionCard {
  name: string;
  address: string;
  status: string;
  variant: BadgeVariant;
  icon: typeof Lock;
}

function ToggleCard({ label, description, active, disabled, onToggle }: ToggleCardProps) {
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
          disabled={disabled}
          className={`relative inline-flex h-9 w-16 items-center rounded-full border border-white/10 transition ${
            active ? "bg-accent/40" : "bg-white/5"
          } ${disabled ? "opacity-60" : ""}`}
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

function deriveConnections(walletStatus: WalletStatusResponse | null | undefined): ConnectionCard[] {
  // Get current user's wallet address from auth service
  const currentUser = authService.getUser();
  const userWalletAddress = currentUser?.wallet_address || "Not connected";
  
  if (!walletStatus) {
    return [
      {
        name: "Owner Safe",
        address: userWalletAddress,
        status: "Not connected",
        variant: "outline" as const,
        icon: Lock,
      },
    ];
  }

  return [
    {
      name: "Owner",
      address: walletStatus.owner,
      status: walletStatus.is_active ? "Active" : "Offline",
      variant: walletStatus.is_active ? "gold" : "outline",
      icon: Lock,
    },
    {
      name: "Wallet",
      address: walletStatus.wallet_address,
      status: walletStatus.is_paused ? "Paused" : "Guarded",
      variant: walletStatus.is_paused ? "warning" : "default",
      icon: KeyRound,
    },
  ];
}

function deriveAutomationRoutines(walletStatus: WalletStatusResponse | null | undefined) {
  const paused = walletStatus?.is_paused;
  return [
    {
      name: "Weekly safe rotation",
      detail: paused ? "Paused while wallet is on hold." : "Rotates guardian keys and refreshes limits.",
    },
    {
      name: "API billing audit",
      detail: "Ensures invoice totals reconcile with on-chain spend.",
    },
    {
      name: "Liquidity sweep",
      detail: paused ? "Standing by until wallet resumes." : "Rebalances pools nightly with heuristics.",
    },
    {
      name: "Decision archive",
      detail: "Uploads proofs to IPFS + Supabase for compliance.",
    },
  ];
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 4,
  }).format(value);
}
