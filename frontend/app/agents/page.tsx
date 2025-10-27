"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { useAccount } from "wagmi";
import { Bot, Plus, TrendingUp, Zap, Brain, Star, Settings, Trash2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { useAppStore, type Agent } from "@/store/app-store";

const agentTypes = [
  { value: "trading", label: "Trading Agent", icon: TrendingUp, color: "from-green-600 to-emerald-600" },
  { value: "defi", label: "DeFi Agent", icon: Zap, color: "from-blue-600 to-cyan-600" },
  { value: "analytics", label: "Analytics Agent", icon: Brain, color: "from-purple-600 to-pink-600" },
  { value: "governance", label: "Governance Agent", icon: Star, color: "from-yellow-600 to-orange-600" },
];

export default function AgentsPage() {
  const { address, isConnected } = useAccount();
  const { agents, addAgent, removeAgent } = useAppStore();
  const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
  const [formData, setFormData] = React.useState({
    name: "",
    type: "trading",
    autonomyLevel: 50,
  });

  const handleCreateAgent = () => {
    if (!formData.name || !address) return;

    const newAgent: Agent = {
      id: `agent-${Date.now()}`,
      name: formData.name,
      type: formData.type,
      walletAddress: address,
      reputation: 100,
      autonomyLevel: formData.autonomyLevel,
      transactionCount: 0,
      successRate: 0,
      status: "active",
      createdAt: new Date(),
    };

    addAgent(newAgent);
    setCreateDialogOpen(false);
    setFormData({ name: "", type: "trading", autonomyLevel: 50 });
  };

  if (!isConnected) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
        <Card variant="glass" className="max-w-md text-center">
          <CardContent className="pt-6">
            <Bot className="h-16 w-16 text-secondary mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Connect Wallet</h2>
            <p className="text-secondary">
              Please connect your wallet to manage AI agents
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold mb-2">AI Agents</h1>
            <p className="text-secondary">
              Create and manage your autonomous AI agents
            </p>
          </div>
          
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-5 w-5" />
                Create Agent
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Agent</DialogTitle>
                <DialogDescription>
                  Deploy a new autonomous AI agent to handle blockchain operations
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 mt-4">
                <Input
                  label="Agent Name"
                  placeholder="e.g., Trading Bot Alpha"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />

                <div>
                  <label className="block text-sm font-medium mb-3">Agent Type</label>
                  <div className="grid grid-cols-2 gap-3">
                    {agentTypes.map((type) => {
                      const Icon = type.icon;
                      return (
                        <button
                          key={type.value}
                          onClick={() => setFormData({ ...formData, type: type.value })}
                          className={`p-4 rounded-xl border-2 transition-all ${
                            formData.type === type.value
                              ? "border-indigo-500 bg-indigo-500/10"
                              : "border-white/10 hover:border-white/20 bg-white/5"
                          }`}
                        >
                          <Icon className="h-6 w-6 mx-auto mb-2" />
                          <p className="text-sm font-medium">{type.label}</p>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Autonomy Level: {formData.autonomyLevel}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={formData.autonomyLevel}
                    onChange={(e) => setFormData({ ...formData, autonomyLevel: parseInt(e.target.value) })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-secondary mt-1">
                    <span>Supervised</span>
                    <span>Fully Autonomous</span>
                  </div>
                </div>

                <Button onClick={handleCreateAgent} className="w-full" size="lg">
                  Deploy Agent
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Agents Grid */}
        {agents.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card variant="glass" className="text-center py-16">
              <CardContent>
                <div className="max-w-md mx-auto">
                  <div className="p-6 rounded-3xl bg-gradient-to-br from-indigo-600 to-purple-600 inline-flex mb-6 glow">
                    <Bot className="h-16 w-16 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold mb-3">No Agents Yet</h2>
                  <p className="text-secondary mb-6">
                    Create your first AI agent to start autonomous blockchain operations
                  </p>
                  <Button onClick={() => setCreateDialogOpen(true)} size="lg" className="gap-2">
                    <Plus className="h-5 w-5" />
                    Create Your First Agent
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((agent, index) => (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card variant="glass" hoverable className="relative overflow-hidden">
                  {/* Background Gradient */}
                  <div className={`absolute inset-0 bg-gradient-to-br ${
                    agentTypes.find(t => t.value === agent.type)?.color || "from-indigo-600 to-purple-600"
                  } opacity-10`} />
                  
                  <CardHeader className="relative">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-3 rounded-xl bg-gradient-to-br ${
                          agentTypes.find(t => t.value === agent.type)?.color || "from-indigo-600 to-purple-600"
                        }`}>
                          <Bot className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <CardTitle className="text-xl">{agent.name}</CardTitle>
                          <CardDescription className="capitalize">{agent.type}</CardDescription>
                        </div>
                      </div>
                      <Badge variant={agent.status === "active" ? "success" : "neutral"}>
                        {agent.status}
                      </Badge>
                    </div>
                  </CardHeader>

                  <CardContent className="relative space-y-4">
                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 rounded-xl bg-white/5">
                        <p className="text-xs text-secondary mb-1">Reputation</p>
                        <div className="flex items-center gap-2">
                          <Star className="h-4 w-4 text-yellow-400" />
                          <p className="text-lg font-bold">{agent.reputation}</p>
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-white/5">
                        <p className="text-xs text-secondary mb-1">Success Rate</p>
                        <p className="text-lg font-bold">{agent.successRate.toFixed(1)}%</p>
                      </div>
                    </div>

                    {/* Autonomy Level */}
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-secondary">Autonomy Level</span>
                        <span className="font-medium">{agent.autonomyLevel}%</span>
                      </div>
                      <Progress value={agent.autonomyLevel} />
                    </div>

                    {/* Transactions */}
                    <div className="p-3 rounded-xl bg-white/5">
                      <p className="text-xs text-secondary mb-1">Total Transactions</p>
                      <p className="text-2xl font-bold">{agent.transactionCount}</p>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-2">
                      <Button variant="secondary" size="sm" className="flex-1 gap-2">
                        <Settings className="h-4 w-4" />
                        Configure
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => removeAgent(agent.id)}
                        className="gap-2"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
