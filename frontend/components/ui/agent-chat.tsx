'use client';

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, AlertCircle, CheckCircle, XCircle, MessageSquare, Sparkles, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { ChatMessage } from "@/lib/types";
import { cn } from "@/lib/utils";

interface AgentChatProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  onApprove: (decisionId: string) => void;
  onReject: (decisionId: string, reason?: string) => void;
  onClarify: (decisionId: string, clarification: string) => void;
  isLoading: boolean;
  isTyping: boolean;
}

export function AgentChat({
  messages,
  onSendMessage,
  onApprove,
  onReject,
  onClarify,
  isLoading,
  isTyping,
}: AgentChatProps) {
  const [input, setInput] = useState("");
  const [clarificationInput, setClarificationInput] = useState<Record<string, string>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput("");
      inputRef.current?.focus();
    }
  };

  const handleClarificationSubmit = (decisionId: string) => {
    const clarification = clarificationInput[decisionId]?.trim();
    if (clarification) {
      onClarify(decisionId, clarification);
      setClarificationInput(prev => ({ ...prev, [decisionId]: "" }));
    }
  };

  return (
    <div className="flex h-[600px] flex-col rounded-2xl border border-white/10 bg-black/40 backdrop-blur-18">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-accent/40 bg-accent/10">
            <Brain className="h-5 w-5 text-accent" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">WalletMind Agent</h3>
            <p className="text-xs text-muted">Intelligent blockchain assistant</p>
          </div>
        </div>
        <Badge variant={isLoading || isTyping ? "outline" : "gold"} className={isLoading || isTyping ? "animate-pulse" : ""}>
          {isLoading ? "Processing..." : isTyping ? "Agent typing..." : "Online"}
        </Badge>
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        <AnimatePresence mode="popLayout">
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex h-full flex-col items-center justify-center text-center"
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-full border border-accent/40 bg-accent/10 mb-4">
                <MessageSquare className="h-8 w-8 text-accent" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">Start a conversation</h3>
              <p className="text-sm text-muted max-w-md mb-6">
                Ask your AI agent to help with transactions, check balances, analyze risks, or answer questions about your wallet.
              </p>
              <div className="space-y-2 text-left">
                <p className="text-xs text-muted/70">Try asking:</p>
                <button
                  onClick={() => setInput("What's my current ETH balance?")}
                  className="block w-full rounded-lg border border-white/5 bg-white/5 px-4 py-2 text-left text-sm text-foreground hover:border-accent/30 hover:bg-accent/5 transition"
                >
                  "What's my current ETH balance?"
                </button>
                <button
                  onClick={() => setInput("Send 0.01 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")}
                  className="block w-full rounded-lg border border-white/5 bg-white/5 px-4 py-2 text-left text-sm text-foreground hover:border-accent/30 hover:bg-accent/5 transition"
                >
                  "Send 0.01 ETH to 0x742d..."
                </button>
                <button
                  onClick={() => setInput("What transactions did I make today?")}
                  className="block w-full rounded-lg border border-white/5 bg-white/5 px-4 py-2 text-left text-sm text-foreground hover:border-accent/30 hover:bg-accent/5 transition"
                >
                  "What transactions did I make today?"
                </button>
              </div>
            </motion.div>
          )}

          {messages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ delay: index * 0.05 }}
            >
              <MessageBubble
                message={message}
                onApprove={onApprove}
                onReject={onReject}
                clarificationInput={clarificationInput[message.decision?.decision_id || ""]}
                onClarificationChange={(value) =>
                  setClarificationInput(prev => ({
                    ...prev,
                    [message.decision?.decision_id || ""]: value
                  }))
                }
                onClarificationSubmit={() => handleClarificationSubmit(message.decision?.decision_id || "")}
              />
            </motion.div>
          ))}

          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-start gap-3"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-accent/40 bg-accent/10">
                <Brain className="h-4 w-4 text-accent" />
              </div>
              <div className="flex items-center gap-2 rounded-2xl border border-white/5 bg-black/30 px-4 py-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-accent" style={{ animationDelay: "0ms" }} />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-accent" style={{ animationDelay: "150ms" }} />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-accent" style={{ animationDelay: "300ms" }} />
                </div>
                <span className="text-xs text-muted">Agent is thinking...</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-white/5 p-4">
        <div className="flex gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Ask your agent anything... (Shift+Enter for new line)"
            className="flex-1 resize-none rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-foreground placeholder:text-muted focus:border-accent/40 focus:outline-none focus:ring-2 focus:ring-accent/20"
            rows={2}
            disabled={isLoading}
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || isLoading}
            className="h-auto w-12 rounded-xl"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>
        <p className="mt-2 text-xs text-muted/70">
          Your agent can execute transactions, check balances, and provide insights. High-risk actions will require your approval.
        </p>
      </form>
    </div>
  );
}

interface MessageBubbleProps {
  message: ChatMessage;
  onApprove: (decisionId: string) => void;
  onReject: (decisionId: string, reason?: string) => void;
  clarificationInput?: string;
  onClarificationChange: (value: string) => void;
  onClarificationSubmit: () => void;
}

function MessageBubble({
  message,
  onApprove,
  onReject,
  clarificationInput,
  onClarificationChange,
  onClarificationSubmit,
}: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  return (
    <div className={cn("flex items-start gap-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      {!isUser && (
        <div className={cn(
          "flex h-8 w-8 items-center justify-center rounded-full border",
          isSystem ? "border-gold/40 bg-gold/10" : "border-accent/40 bg-accent/10"
        )}>
          {isSystem ? (
            <Sparkles className="h-4 w-4 text-gold" />
          ) : (
            <Brain className="h-4 w-4 text-accent" />
          )}
        </div>
      )}

      <div className={cn("flex-1 space-y-2", isUser && "flex flex-col items-end")}>
        {/* Message content */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm",
            isUser
              ? "border border-accent/40 bg-accent/10 text-foreground"
              : isSystem
              ? "border border-gold/25 bg-gold/10 text-gold"
              : "border border-white/5 bg-black/30 text-foreground"
          )}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>

          {/* Decision details */}
          {message.decision && (
            <div className="mt-3 space-y-2 border-t border-white/5 pt-3">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase tracking-wider text-muted">Decision Details</span>
                <Badge variant={message.decision.risk_score > 0.7 ? "warning" : "outline"}>
                  Risk: {(message.decision.risk_score * 100).toFixed(0)}%
                </Badge>
              </div>
              <div className="space-y-1 text-xs">
                <p><span className="text-muted">Intent:</span> <span className="text-foreground">{message.decision.intent}</span></p>
                <p><span className="text-muted">Action:</span> <span className="text-foreground">{message.decision.action_type}</span></p>
                {message.decision.estimated_cost !== null && message.decision.estimated_cost !== undefined && (
                  <p><span className="text-muted">Est. Cost:</span> <span className="text-accent">{message.decision.estimated_cost.toFixed(6)} ETH</span></p>
                )}
                <p className="text-muted/70 italic">{message.decision.reasoning}</p>
              </div>
            </div>
          )}
        </div>

        {/* Approval buttons */}
        {message.needsApproval && message.decision && (
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="primary"
              onClick={() => onApprove(message.decision!.decision_id)}
              className="gap-2"
            >
              <CheckCircle className="h-4 w-4" />
              Approve & Execute
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onReject(message.decision!.decision_id, "User rejected")}
              className="gap-2"
            >
              <XCircle className="h-4 w-4" />
              Reject
            </Button>
          </div>
        )}

        {/* Clarification input */}
        {message.needsClarification && message.decision && (
          <div className="space-y-2">
            <div className="flex gap-2">
              <input
                type="text"
                value={clarificationInput || ""}
                onChange={(e) => onClarificationChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    onClarificationSubmit();
                  }
                }}
                placeholder="Provide clarification..."
                className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-foreground placeholder:text-muted focus:border-accent/40 focus:outline-none focus:ring-2 focus:ring-accent/20"
              />
              <Button
                size="sm"
                onClick={onClarificationSubmit}
                disabled={!clarificationInput?.trim()}
              >
                Send
              </Button>
            </div>
            <p className="text-xs text-muted/70">
              <AlertCircle className="inline h-3 w-3 mr-1" />
              The agent needs more information to proceed
            </p>
          </div>
        )}

        {/* Timestamp */}
        <p className="text-[11px] text-muted/70">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  );
}
