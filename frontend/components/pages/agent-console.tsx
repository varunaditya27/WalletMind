'use client';

import { useEffect, useMemo, useState, useCallback } from "react";
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
import { AgentChat } from "@/components/ui/agent-chat";
import { useWalletMindStore } from "@/lib/stores/walletmind-store";
import { sendAgentRequest, respondToApproval, respondToClarification } from "@/lib/services/walletmind-service";
import { authService } from "@/lib/services/auth-service";
import type { AuditEntry, WebsocketEvent, ChatMessage } from "@/lib/types";
import { useShallow } from "zustand/react/shallow";

export function AgentConsoleScreen() {
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [, setPendingDecisionId] = useState<string | null>(null);

  const {
    agentActivity,
    auditTrail,
    websocketMessages,
    loading,
    initializeAgentConsole,
  } = useWalletMindStore(
    useShallow((state) => ({
      agentActivity: state.agentActivity,
      auditTrail: state.auditTrail,
      websocketMessages: state.websocketMessages,
      loading: state.loading.agent,
      initializeAgentConsole: state.initializeAgentConsole,
    }))
  );

  useEffect(() => {
    initializeAgentConsole();
  }, [initializeAgentConsole]);

  const handleSendMessage = useCallback(async (message: string) => {
    const currentUser = authService.getUser();
    if (!currentUser) {
      alert("Please log in to interact with the agent");
      return;
    }

    // Add user message to chat
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
    };
    setChatMessages(prev => [...prev, userMessage]);
    setIsLoadingChat(true);
    setIsTyping(true);

    try {
      // Send request to agent
      const response = await sendAgentRequest({
        user_id: currentUser.id,
        request: message,
        context: {
          wallet_address: currentUser.wallet_address,
          username: currentUser.username,
        },
      });

      setIsTyping(false);

      // Add agent response to chat
      const agentMessage: ChatMessage = {
        id: `agent-${Date.now()}`,
        role: "agent",
        content: response.message,
        timestamp: new Date().toISOString(),
        decision: response.decision || undefined,
        needsApproval: response.decision?.requires_approval || false,
        needsClarification: response.decision?.action_type === "clarification" || false,
      };

      setChatMessages(prev => [...prev, agentMessage]);

      // If successful execution, show confirmation
      if (response.success && response.transaction_hash) {
        const confirmMessage: ChatMessage = {
          id: `system-${Date.now()}`,
          role: "system",
          content: `✅ Transaction executed successfully!\n\nTransaction Hash: ${response.transaction_hash}\n\nYou can view it on the blockchain explorer.`,
          timestamp: new Date().toISOString(),
        };
        setChatMessages(prev => [...prev, confirmMessage]);
      }

    } catch (error) {
      setIsTyping(false);
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "system",
        content: `❌ Error: ${error instanceof Error ? error.message : "Failed to process request. Please try again."}`,
        timestamp: new Date().toISOString(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoadingChat(false);
    }
  }, []);

  const handleApprove = useCallback(async (decisionId: string) => {
    setIsLoadingChat(true);
    setIsTyping(true);

    try {
      const response = await respondToApproval(decisionId, true);
      setIsTyping(false);

      const agentMessage: ChatMessage = {
        id: `agent-${Date.now()}`,
        role: "agent",
        content: response.message,
        timestamp: new Date().toISOString(),
      };
      setChatMessages(prev => [...prev, agentMessage]);

      if (response.success && response.transaction_hash) {
        const confirmMessage: ChatMessage = {
          id: `system-${Date.now()}`,
          role: "system",
          content: `✅ Transaction approved and executed!\n\nTransaction Hash: ${response.transaction_hash}`,
          timestamp: new Date().toISOString(),
        };
        setChatMessages(prev => [...prev, confirmMessage]);
      }

      setPendingDecisionId(null);
    } catch (error) {
      setIsTyping(false);
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "system",
        content: `❌ Error approving decision: ${error instanceof Error ? error.message : "Unknown error"}`,
        timestamp: new Date().toISOString(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoadingChat(false);
    }
  }, []);

  const handleReject = useCallback(async (decisionId: string, reason?: string) => {
    setIsLoadingChat(true);
    setIsTyping(true);

    try {
      const response = await respondToApproval(decisionId, false, reason);
      setIsTyping(false);

      const agentMessage: ChatMessage = {
        id: `agent-${Date.now()}`,
        role: "agent",
        content: response.message,
        timestamp: new Date().toISOString(),
      };
      setChatMessages(prev => [...prev, agentMessage]);
      setPendingDecisionId(null);
    } catch (error) {
      setIsTyping(false);
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "system",
        content: `❌ Error rejecting decision: ${error instanceof Error ? error.message : "Unknown error"}`,
        timestamp: new Date().toISOString(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoadingChat(false);
    }
  }, []);

  const handleClarify = useCallback(async (decisionId: string, clarification: string) => {
    // Add user clarification to chat
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: clarification,
      timestamp: new Date().toISOString(),
    };
    setChatMessages(prev => [...prev, userMessage]);

    setIsLoadingChat(true);
    setIsTyping(true);

    try {
      const response = await respondToClarification(decisionId, clarification);
      setIsTyping(false);

      const agentMessage: ChatMessage = {
        id: `agent-${Date.now()}`,
        role: "agent",
        content: response.message,
        timestamp: new Date().toISOString(),
        decision: response.decision || undefined,
        needsApproval: response.decision?.requires_approval || false,
      };
      setChatMessages(prev => [...prev, agentMessage]);

      if (response.decision?.requires_approval) {
        setPendingDecisionId(response.decision.decision_id);
      } else {
        setPendingDecisionId(null);
      }
    } catch (error) {
      setIsTyping(false);
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "system",
        content: `❌ Error processing clarification: ${error instanceof Error ? error.message : "Unknown error"}`,
        timestamp: new Date().toISOString(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoadingChat(false);
    }
  }, []);

  const cognitionNodes = useMemo(() => {
    if (agentActivity.length) {
      return agentActivity.slice(0, 5).map((activity, index) => ({
        id: String(activity.id ?? `activity-${index}`),
        stage: normalizeText(activity.agent_type ?? activity.stage ?? "Agent"),
        summary: summarizeActivity(activity),
        latency: extractLatency(activity),
        risk: normalizeText(activity.status ?? activity.outcome ?? "Observed"),
      }));
    }
    return auditTrail.slice(0, 5).map((entry) => ({
      id: entry.entry_id,
      stage: normalizeText(entry.agent_type ?? entry.entry_type),
      summary: entry.action,
      latency: relativeTimestamp(entry.timestamp),
      risk: entry.status,
    }));
  }, [agentActivity, auditTrail]);

  const conversation = useMemo(() => {
    const communicatorEvents = websocketMessages
      .filter((event) => (event.channel ?? event.type)?.includes("communicator") || event.event?.includes("message"))
      .slice(0, 6)
      .map((event, index) => ({
        id: `${event.event ?? event.type}-${index}`,
        role: event.data?.role === "operator" ? "operator" : "agent",
        text: extractConversationText(event),
        timestamp: event.timestamp,
      }));

    if (communicatorEvents.length) {
      return communicatorEvents;
    }

    return auditTrail.slice(0, 4).map((entry, index) => ({
      id: `${entry.entry_id}-${index}`,
      role: entry.agent_type ? "agent" : "operator",
      text: entry.action,
      timestamp: entry.timestamp,
    }));
  }, [websocketMessages, auditTrail]);

  const taskGraph = useMemo(() => {
    const withSteps = agentActivity
      .map((activity, index) => ({
        title: normalizeText(activity.action ?? activity.goal ?? `Task ${index + 1}`),
        steps: extractSteps(activity),
      }))
      .filter((task) => task.steps.length > 0)
      .slice(0, 3);

    if (withSteps.length) {
      return withSteps;
    }

    return auditTrail.slice(0, 3).map((entry, index) => ({
      title: normalizeText(entry.action ?? `Audit ${index + 1}`),
      steps: deriveStepsFromAudit(entry),
    }));
  }, [agentActivity, auditTrail]);

  const telemetry = useMemo(() => deriveTelemetry(agentActivity, auditTrail), [agentActivity, auditTrail]);

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-muted">Agent Interaction</p>
          <h1 className="text-2xl font-semibold text-foreground">Talk to Your AI Agent</h1>
          <p className="mt-1 text-sm text-muted">
            Have a conversation with your intelligent blockchain assistant
          </p>
        </div>
        <Badge variant={loading || isLoadingChat ? "outline" : "gold"} className={loading || isLoadingChat ? "animate-pulse" : ""}>
          {isLoadingChat ? "Processing..." : loading ? "Syncing..." : "Agent ready"}
        </Badge>
      </div>

      {/* Main Chat Interface - Prominent Position */}
      <AgentChat
        messages={chatMessages}
        onSendMessage={handleSendMessage}
        onApprove={handleApprove}
        onReject={handleReject}
        onClarify={handleClarify}
        isLoading={isLoadingChat}
        isTyping={isTyping}
      />

      {/* Additional Agent Information Sections */}
      <section className="grid gap-6 lg:grid-cols-[1.1fr_minmax(0,0.9fr)]">
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Brain className="h-5 w-5 text-accent" />
              Thought timeline
            </CardTitle>
            <CardDescription>Recent agent reasoning and decision-making process.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {loading && (
              <div className="rounded-2xl border border-white/5 bg-black/20 p-6 text-sm text-muted animate-pulse">
                Loading agent cognition stream...
              </div>
            )}
            {!loading && cognitionNodes.length === 0 && (
              <div className="rounded-2xl border border-white/5 bg-black/20 p-6 text-sm text-muted">
                <p className="font-semibold">No recent cognition events</p>
                <p className="mt-2 text-xs">
                  Agent thoughts will appear here when decisions are processed.
                  Start a conversation above to see the agent think!
                </p>
              </div>
            )}
            {cognitionNodes.map((node, index) => (
              <motion.div
                key={node.id}
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
                  Status · {node.risk}
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
              {loading && (
                <div className="rounded-2xl border border-white/5 bg-white/5 p-4 text-sm text-muted animate-pulse">
                  Loading conversations...
                </div>
              )}
              {!loading && conversation.length === 0 && (
                <div className="rounded-2xl border border-white/5 bg-white/5 p-4 text-sm text-muted">
                  <p className="font-semibold">No conversations yet</p>
                  <p className="mt-2 text-xs">
                    Messages between you and the WalletMind agents will appear here.
                  </p>
                </div>
              )}
              {conversation.map((message, index) => (
                <motion.div
                  key={message.id}
                  className="rounded-2xl border border-white/5 bg-white/5 p-4"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.06, duration: 0.4, ease: "easeOut" }}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-[0.3em] text-muted">
                      {message.role === "agent" ? "WalletMind" : "Operator"}
                    </span>
                    <span className="text-[11px] text-muted/70">{relativeTimestamp(message.timestamp)}</span>
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
              {loading && (
                <div className="rounded-2xl border border-white/5 bg-black/20 p-4 text-sm text-muted animate-pulse">
                  Loading task graph...
                </div>
              )}
              {!loading && taskGraph.length === 0 && (
                <div className="rounded-2xl border border-white/5 bg-black/20 p-4 text-sm text-muted">
                  <p className="font-semibold">No active tasks</p>
                  <p className="mt-2 text-xs">
                    Multi-step tasks broken down by agents will appear here.
                  </p>
                </div>
              )}
              {taskGraph.map((task, index) => (
                <motion.div
                  key={`${task.title}-${index}`}
                  className="rounded-2xl border border-white/5 bg-black/30 p-4"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
                >
                  <h3 className="text-sm font-semibold text-foreground">{task.title}</h3>
                  <ul className="mt-2 space-y-1 text-xs text-muted">
                    {task.steps.map((child) => (
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
          <Metric label="Planning depth" value={telemetry.planningDepth} icon={<Network className="h-4 w-4" />} />
          <Metric label="Memory tokens" value={telemetry.memoryTokens} icon={<Radar className="h-4 w-4" />} />
          <Metric label="API spend (24h)" value={telemetry.apiSpend} icon={<Brain className="h-4 w-4" />} />
          <Metric label="Fallback LLM" value={telemetry.fallbackModel} icon={<MessageCircle className="h-4 w-4" />} />
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

function normalizeText(value: unknown) {
  if (typeof value !== "string" || value.length === 0) {
    return "Agent";
  }
  return value.charAt(0).toUpperCase() + value.slice(1).replace(/_/g, " ");
}

function summarizeActivity(activity: Record<string, unknown>) {
  const description =
    (typeof activity.summary === "string" && activity.summary) ||
    (typeof activity.action === "string" && activity.action) ||
    (typeof activity.description === "string" && activity.description);
  if (description) {
    return description;
  }
  if (activity.metadata && typeof activity.metadata === "object") {
    return JSON.stringify(activity.metadata);
  }
  return "Real-time cognition update";
}

function extractLatency(activity: Record<string, unknown>) {
  if (typeof activity.latency === "string") {
    return activity.latency;
  }
  if (typeof activity.latency_ms === "number") {
    return `${activity.latency_ms}ms`;
  }
  if (typeof activity.duration_ms === "number") {
    return `${activity.duration_ms}ms`;
  }
  return relativeTimestamp(activity.timestamp as string | undefined);
}

function extractConversationText(event: WebsocketEvent) {
  if (typeof event.data?.message === "string") {
    return event.data.message;
  }
  if (typeof event.data?.content === "string") {
    return event.data.content;
  }
  if (typeof event.data?.summary === "string") {
    return event.data.summary;
  }
  return event.event ?? "Realtime message";
}

function relativeTimestamp(timestamp?: string) {
  if (!timestamp) {
    return "now";
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

function extractSteps(activity: Record<string, unknown>): string[] {
  const metadata = activity.metadata as Record<string, unknown> | undefined;
  if (!metadata) {
    return [];
  }
  if (Array.isArray(metadata.steps)) {
    return metadata.steps
      .map((step) => (typeof step === "string" ? step : typeof step === "object" && step !== null ? step.title ?? step.name : null))
      .filter((value): value is string => typeof value === "string");
  }
  if (Array.isArray(metadata.tasks)) {
    return metadata.tasks
      .map((task) => (typeof task === "string" ? task : typeof task === "object" && task !== null ? task.title ?? task.summary : null))
      .filter((value): value is string => typeof value === "string");
  }
  return [];
}

function deriveStepsFromAudit(entry: AuditEntry) {
  const actions = [] as string[];
  if (entry.decision_hash) {
    actions.push(`Decision hash ${entry.decision_hash.slice(0, 8)}…`);
  }
  if (entry.transaction_hash) {
    actions.push(`Tx ${entry.transaction_hash.slice(0, 8)}… (${entry.status})`);
  }
  if (actions.length === 0) {
    actions.push(entry.action);
  }
  return actions;
}

function deriveTelemetry(agentActivity: Array<Record<string, unknown>>, auditTrail: AuditEntry[]) {
  const planningDepth = agentActivity.find((activity) => typeof activity.planning_depth === "number");
  const memoryUsage = agentActivity.find((activity) => typeof activity.memory_tokens === "number");
  const apiSpend = agentActivity.find((activity) => typeof activity.api_spend_24h === "number");
  const fallback = agentActivity.find((activity) => typeof activity.fallback_model === "string");

  return {
    planningDepth: planningDepth ? `${planningDepth.planning_depth} layers` : "—",
    memoryTokens: memoryUsage ? `${memoryUsage.memory_tokens} tokens` : `${auditTrail.length} entries`,
    apiSpend: apiSpend ? `$${Number(apiSpend.api_spend_24h).toFixed(2)}` : "—",
    fallbackModel: fallback ? String(fallback.fallback_model) : "LangGraph default",
  };
}
