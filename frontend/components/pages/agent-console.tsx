'use client';

import { motion } from "framer-motion";
import { Brain, GitBranch, MessageCircle, Network, Radar } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardBackground,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const cognitionNodes = [
  {
    stage: "Planner",
    summary: "Querying DEX routes for cross-chain arbitrage",
    latency: "184ms",
    risk: "Low",
  },
  {
    stage: "Communicator",
    summary: "Pulled pricing feed from API3 oracle",
    latency: "236ms",
    risk: "Traceable",
  },
  {
    stage: "Evaluator",
    summary: "Gas-to-profit ratio 1.8 acceptable",
    latency: "96ms",
    risk: "Green",
  },
  {
    stage: "Executor",
    summary: "Constructing Safe userOp with 42k gas",
    latency: "451ms",
    risk: "Within limit",
  },
];

const conversation = [
  {
    role: "operator",
    text: "Initiate liquidity sweep between Sepolia and Base pools if spread exceeds 1.2%",
    time: "00:00",
  },
  {
    role: "agent",
    text: "Strategy acknowledged. Calculating optimal route and required gas budget.",
    time: "00:04",
  },
  {
    role: "agent",
    text: "Risk heuristics set: Max slippage 0.4%, guard module enforced.",
    time: "00:12",
  },
  {
    role: "agent",
    text: "Decision hash logged · 0x6af2d3…18b7. Awaiting operator override window.",
    time: "00:17",
  },
];

const taskGraph = [
  {
    title: "Assess Spread",
    children: ["Fetch DEX quotes", "Compare base pair depth"],
  },
  {
    title: "Project Gas",
    children: ["Estimate base network gas", "Apply Safe module multiplier"],
  },
  {
    title: "Authorize",
    children: ["Log decision hash", "Push to Safe relayer"],
  },
];

export function AgentConsoleScreen() {
  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-muted">Agent cognition</p>
          <h1 className="text-2xl font-semibold text-foreground">Live reasoning stream</h1>
        </div>
        <Badge variant="gold">AI thinking · pulse active</Badge>
      </div>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_minmax(0,0.9fr)]">
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Brain className="h-5 w-5 text-accent" />
              Thought timeline
            </CardTitle>
            <CardDescription>Planner → Evaluator reasoning path in chronological order.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {cognitionNodes.map((node, index) => (
              <motion.div
                key={node.stage}
                className="rounded-2xl border border-white/5 bg-black/30 p-4"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-foreground">{node.stage}</h3>
                  <span className="text-xs text-muted">{node.latency}</span>
                </div>
                <p className="mt-2 text-sm text-muted">{node.summary}</p>
                <Badge variant="outline" className="mt-3">
                  Risk · {node.risk}
                </Badge>
              </motion.div>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <MessageCircle className="h-5 w-5 text-accent" />
                Conversation log
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {conversation.map((message, index) => (
                <motion.div
                  key={`${message.role}-${index}`}
                  className="rounded-2xl border border-white/5 bg-white/5 p-4"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.06, duration: 0.4, ease: "easeOut" }}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-[0.3em] text-muted">
                      {message.role === "agent" ? "WalletMind" : "Operator"}
                    </span>
                    <span className="text-[11px] text-muted/70">{message.time}</span>
                  </div>
                  <p className="mt-2 text-sm text-foreground">{message.text}</p>
                </motion.div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <GitBranch className="h-5 w-5 text-gold" />
                Current task graph
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {taskGraph.map((task, index) => (
                <motion.div
                  key={task.title}
                  className="rounded-2xl border border-white/5 bg-black/30 p-4"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
                >
                  <h3 className="text-sm font-semibold text-foreground">{task.title}</h3>
                  <ul className="mt-2 space-y-1 text-xs text-muted">
                    {task.children.map((child) => (
                      <li key={child}>• {child}</li>
                    ))}
                  </ul>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>

      <Card className="grid gap-6 border-accent/30 bg-accent/5 p-6 md:grid-cols-2">
        <CardBackground className="bg-[radial-gradient(circle_at_top_right,rgba(0,191,255,0.25),transparent_65%)]" />
        <div>
          <h3 className="text-lg font-semibold text-foreground">Telemetry snapshot</h3>
          <p className="mt-2 text-sm text-muted">
            Live metrics streaming from FastAPI agent orchestrator with Chroma recall enabled.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <Metric label="Planning depth" value="5 layers" icon={<Network className="h-4 w-4" />} />
          <Metric label="Memory tokens" value="1.2k" icon={<Radar className="h-4 w-4" />} />
          <Metric label="API spend (24h)" value="$142" icon={<Brain className="h-4 w-4" />} />
          <Metric label="Fallback LLM" value="Google AI Studio" icon={<MessageCircle className="h-4 w-4" />} />
        </div>
      </Card>
    </div>
  );
}

function Metric({ label, value, icon }: { label: string; value: string; icon: ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/30 p-3">
      <div className="flex items-center gap-2 text-xs text-muted">
        {icon}
        {label}
      </div>
      <p className="mt-2 text-sm font-semibold text-foreground">{value}</p>
    </div>
  );
}
