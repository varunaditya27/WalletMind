'use client';

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Fingerprint, ShieldCheck, Sparkles, Wifi } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SiteHeader } from "@/components/layout/site-header";
import { BackgroundGrid } from "@/components/visual/background-grid";

const heroStats = [
  { label: "Autonomous tx/day", value: "128", delta: "+42%" },
  { label: "Decision proofs", value: "100%", delta: "verifiable" },
  { label: "Smart accounts", value: "ERC-4337", delta: "Safe SDK" },
];

const featureCards = [
  {
    title: "Agent Autonomy",
    description:
      "Planner, executor, evaluator, and communicator agents coordinate through LangGraph to deliver verifiable actions.",
    icon: Sparkles,
  },
  {
    title: "On-chain Provenance",
    description:
      "Every decision is hashed, timestamped, and logged to the Agent Wallet contract before execution for auditability.",
    icon: Fingerprint,
  },
  {
    title: "Safe Smart Accounts",
    description: "ERC-4337 accounts via Safe SDK manage funds with programmable guardrails and spending limits.",
    icon: ShieldCheck,
  },
  {
    title: "API Native Wallet",
    description:
      "Agents autonomously pay for Groq, Google AI Studio, and x402 APIs while tracking real-time usage costs.",
    icon: Wifi,
  },
];

const timeline = [
  {
    title: "Intent Capture",
    body: "Natural language requests are parsed into structured plans with risk guards and budget limits.",
  },
  {
    title: "Provable Decision",
    body: "Agent rationale hashed + pinned to IPFS before any on-chain move, establishing verifiable intent.",
  },
  {
    title: "Autonomous Execution",
    body: "Executor constructs userOperations, estimates gas, and finalizes via Safe relayers across preferred testnets.",
  },
  {
    title: "Live Telemetry",
    body: "Evaluator reconciles receipts, updates Chroma memory, and streams live updates to the WalletMind dashboard.",
  },
];

export function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <SiteHeader />
      <BackgroundGrid />
      <main className="relative mx-auto flex max-w-6xl flex-col gap-24 px-6 pb-24 pt-24">
        <Hero />
        <FeatureSection />
        <TimelineSection />
        <VerificationPanel />
        <CallToAction />
      </main>
    </div>
  );
}

function Hero() {
  return (
    <section className="grid gap-12 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
      <div className="space-y-8">
        <Badge variant="gold" className="bg-gold/20 text-sm">
          Autonomous Wallet Intelligence · Live on Sepolia
        </Badge>
        <motion.h1
          className="text-4xl font-bold leading-tight sm:text-5xl lg:text-6xl"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          WalletMind turns AI agents into <span className="text-gradient">verifiable economic actors</span>.
        </motion.h1>
        <motion.p
          className="max-w-xl text-lg text-muted"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.6, ease: "easeOut" }}
        >
          Deploy autonomous agents that think, negotiate, and sign transactions on-chain—every decision pre-logged,
          every proof at your fingertips.
        </motion.p>
        <motion.div
          className="flex flex-wrap items-center gap-4"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6, ease: "easeOut" }}
        >
          <Button size="pill" className="px-8" asChild>
            <Link href="/onboarding">
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button variant="glass" size="pill" className="px-8" asChild>
            <Link href="#verification">See Proof Workflow</Link>
          </Button>
        </motion.div>
        <motion.div
          className="grid gap-4 sm:grid-cols-3"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: {},
            visible: {
              transition: {
                staggerChildren: 0.1,
              },
            },
          }}
        >
          {heroStats.map((stat) => (
            <motion.div
              key={stat.label}
              className="rounded-2xl border border-white/5 bg-white/5 px-5 py-4 backdrop-blur-xl"
              variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
            >
              <p className="text-xs uppercase tracking-[0.3em] text-muted">{stat.label}</p>
              <p className="mt-2 text-2xl font-semibold text-foreground">{stat.value}</p>
              <p className="text-sm text-accent/80">{stat.delta}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
      <motion.div
        className="relative h-full min-h-80 rounded-3xl border border-white/5 bg-white/5 p-6 backdrop-blur-30"
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_20%_20%,rgba(0,191,255,0.35),transparent_60%)]" />
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_80%_80%,rgba(230,180,0,0.25),transparent_65%)]" />
        <div className="flex h-full flex-col justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-muted">Live Agent Feed</p>
            <h2 className="mt-2 text-xl font-semibold">Strategy: DeFi Liquidity Arbitrage</h2>
          </div>
          <ul className="space-y-4 text-sm text-muted">
            <li className="rounded-xl border border-white/10 bg-black/30 p-4">
              ✦ Planner → Identified premium on Base Goerli vs. Sepolia pool.
            </li>
            <li className="rounded-xl border border-white/10 bg-black/30 p-4">
              ✦ Evaluator → Gas estimate 42k, risk score GREEN.
            </li>
            <li className="rounded-xl border border-white/10 bg-black/30 p-4">
              ✦ Executor → Preparing UserOperation with Safe.
            </li>
            <li className="rounded-xl border border-white/10 bg-black/30 p-4 text-gold">
              ✦ Proof → Hash logged: 0x6a…f2d, IPFS anchor ready.
            </li>
          </ul>
        </div>
      </motion.div>
    </section>
  );
}

function FeatureSection() {
  return (
    <section id="features" className="space-y-12">
      <div className="flex flex-col gap-4">
        <h2 className="text-3xl font-semibold">Operate with confidence.</h2>
        <p className="max-w-2xl text-lg text-muted">
          WalletMind fuses LangChain agent graphs with Safe smart accounts so every action is deliberate, observable,
          and cryptographically sound.
        </p>
      </div>
      <div className="grid gap-6 md:grid-cols-2">
        {featureCards.map((card) => (
          <motion.div
            key={card.title}
            className="glass-panel relative overflow-hidden p-6"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <card.icon className="h-10 w-10 text-accent" />
            <h3 className="mt-4 text-xl font-semibold text-foreground">{card.title}</h3>
            <p className="mt-2 text-sm text-muted">{card.description}</p>
            <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_30%_20%,rgba(0,191,255,0.15),transparent_60%)]" />
          </motion.div>
        ))}
      </div>
    </section>
  );
}

function TimelineSection() {
  return (
    <section id="agents" className="space-y-10">
      <div className="flex flex-col gap-3">
        <h2 className="text-3xl font-semibold text-foreground">Decision → Execution Timeline</h2>
        <p className="max-w-2xl text-muted">
          Each stage of the agent pipeline is observable. From initial intent capture to on-chain receipts, every step
          leaves a cryptographic breadcrumb.
        </p>
      </div>
      <div className="grid gap-6 md:grid-cols-4">
        {timeline.map((item, idx) => (
          <motion.div
            key={item.title}
            className="rounded-2xl border border-white/5 bg-white/5 p-5 backdrop-blur-18"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ delay: idx * 0.08, duration: 0.6, ease: "easeOut" }}
          >
            <p className="text-xs uppercase tracking-[0.3em] text-muted">Step {idx + 1}</p>
            <h3 className="mt-2 text-lg font-semibold text-foreground">{item.title}</h3>
            <p className="mt-2 text-sm text-muted">{item.body}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

function VerificationPanel() {
  return (
    <section id="verification" className="grid gap-10 lg:grid-cols-[1.2fr_1fr]">
      <div className="space-y-4">
        <h2 className="text-3xl font-semibold">Transparent by design.</h2>
        <p className="max-w-xl text-muted">
          Decision provenance logging ensures the agent cannot act without leaving a signed trail. Inspect hashes on-chain
          or dive into the dashboard’s verification mode.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-muted">Proof Hash</p>
            <p className="mt-2 font-mono text-sm text-accent">0x6af2d3…18b7</p>
            <p className="text-xs text-muted">Stored before UO submission.</p>
          </div>
          <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-muted">IPFS Anchor</p>
            <p className="mt-2 font-mono text-sm text-gold">ipfs://bafy…zk44</p>
            <p className="text-xs text-muted">Full rationale & cost basis.</p>
          </div>
        </div>
      </div>
      <div className="glass-panel p-6">
        <h3 className="text-lg font-semibold text-foreground">Realtime Verification Mode</h3>
        <p className="mt-2 text-sm text-muted">
          Validate signatures, hash ordering, and spending limits directly from the browser. Built for hackathon judges
          and enterprise auditors alike.
        </p>
        <ul className="mt-6 space-y-3 text-sm text-muted">
          <li>▹ Timestamp ordering ensures proofs precede execution.</li>
          <li>▹ Safe modules enforce daily spending caps and guardians.</li>
          <li>▹ Transactions categorized with Lucide visuals for clarity.</li>
          <li>▹ All activity mirrored to Supabase for analysis and alerts.</li>
        </ul>
      </div>
    </section>
  );
}

function CallToAction() {
  return (
    <section id="cta" className="glass-panel relative overflow-hidden px-10 py-12">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(0,191,255,0.25),transparent_60%)]" aria-hidden />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,rgba(230,180,0,0.2),transparent_65%)]" aria-hidden />
      <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-muted">Launch Autonomous Finance</p>
          <h3 className="mt-2 text-2xl font-semibold text-foreground">
            Spin up WalletMind in under 120 minutes.
          </h3>
          <p className="mt-2 text-sm text-muted">
            Deployed contracts, FastAPI backend, and real-time dashboard ready for your next hackathon showcase.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button size="pill" className="px-8" asChild>
            <Link href="/onboarding">
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button variant="ghost" size="pill" className="px-8" asChild>
            <Link href="https://github.com/varunaditya27/WalletMind" target="_blank">
              View Repository
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
