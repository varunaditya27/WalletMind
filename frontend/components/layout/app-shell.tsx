'use client';

import { usePathname } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Bot, Gauge, History, Settings, Sparkles } from "lucide-react";
import { PropsWithChildren } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navItems = [
  {
    href: "/dashboard",
    label: "Dashboard",
  icon: Gauge,
    description: "Balances, KPIs, smart wallet health",
  },
  {
    href: "/agent",
    label: "Agent Console",
  icon: Bot,
    description: "Agent cognition stream & objectives",
  },
  {
    href: "/transactions",
    label: "Transactions",
  icon: History,
    description: "Ledger, proofs, and cost analysis",
  },
  {
    href: "/settings",
    label: "Identity & Settings",
  icon: Settings,
    description: "Wallet connections, keys, guardrails",
  },
];

export function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname() ?? "";

  return (
    <div className="relative flex min-h-screen bg-wm-gradient text-foreground">
      <DecorativeBackdrop />
      <aside className="hidden w-[280px] flex-col border-r border-white/5 bg-black/40 px-6 py-8 backdrop-blur-18 lg:flex">
        <Link href="/" className="mb-10 flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.3em] text-muted">
          <span className="h-2.5 w-2.5 rounded-full bg-accent drop-shadow-glow-blue" />
          WalletMind
        </Link>
        <nav className="space-y-2">
          {navItems.map((item) => {
            const active = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group relative block overflow-hidden rounded-xl border border-white/5 bg-white/5 px-4 py-3 transition-all duration-300",
                  active
                    ? "border-accent/50 bg-accent/10 shadow-accent-ring"
                    : "hover:border-accent/30 hover:bg-accent/5 hover:shadow-glass-sm"
                )}
              >
                {active && (
                  <motion.span
                    layoutId="nav-glow"
                    className="absolute inset-0 -z-10 rounded-xl bg-accent/10"
                    transition={{ type: "spring", stiffness: 200, damping: 24 }}
                  />
                )}
                <div className="flex items-center gap-3">
                  <span
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-black/30 text-muted",
                      active && "border-accent/40 bg-accent/15 text-accent"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </span>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-foreground">{item.label}</p>
                    <p className="text-xs text-muted">{item.description}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto space-y-4 pt-10">
          <div className="rounded-2xl border border-gold/25 bg-gold/10 p-4 text-gold shadow-gold-ring">
            <p className="text-sm font-semibold uppercase tracking-[0.3em]">Proof Mode</p>
            <p className="mt-2 text-xs text-gold/80">100% of agent actions signed and timestamped.</p>
          </div>
          <Button variant="glass" size="pill" className="w-full justify-center border-accent/40">
            <Sparkles className="h-4 w-4" />
            Trigger Strategy Sync
          </Button>
        </div>
      </aside>
      <main className="relative flex flex-1 flex-col">
        <MobileNav pathname={pathname} />
        <AppTopBar />
        <div className="flex-1 px-6 pb-12 pt-6 lg:px-10">{children}</div>
      </main>
    </div>
  );
}

function AppTopBar() {
  return (
    <div className="flex items-center justify-between border-b border-white/5 bg-black/20 px-6 py-5 backdrop-blur-18 lg:px-10">
      <div>
        <p className="text-xs uppercase tracking-[0.45em] text-muted">Autonomous Wallet OS</p>
        <h1 className="text-lg font-semibold text-foreground">Agent Control Console</h1>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2">
          <span className="relative flex h-3 w-3">
            <span className="absolute inset-0 rounded-full bg-accent/50 blur-sm" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-accent" />
          </span>
          <span className="text-xs text-muted">Agent online · Latency 42ms</span>
        </div>
        <Button variant="outline" size="sm" className="text-xs uppercase tracking-[0.3em]">
          Sync Wallet
        </Button>
      </div>
    </div>
  );
}

function DecorativeBackdrop() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 bg-wm-gradient" />
      <div className="absolute inset-0 bg-wm-radial-blue mix-blend-screen" />
      <div className="absolute inset-0 bg-wm-radial-gold mix-blend-screen" />
      <div className="absolute left-1/2 top-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/10 blur-3xl" />
    </div>
  );
}

function MobileNav({ pathname }: { pathname: string }) {
  return (
    <div className="flex items-center gap-3 overflow-x-auto border-b border-white/5 bg-black/30 px-4 py-3 backdrop-blur-18 lg:hidden">
      {navItems.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-2 rounded-full border px-3 py-2 text-xs transition",
              active
                ? "border-accent/50 bg-accent/10 text-accent"
                : "border-white/5 bg-white/5 text-muted"
            )}
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </Link>
        );
      })}
    </div>
  );
}
