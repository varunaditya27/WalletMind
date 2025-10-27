"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { useAccount, useBalance } from "wagmi";
import {
  Wallet,
  Bot,
  Activity,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle,
  Clock,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAppStore } from "@/store/app-store";
import { formatAddress, formatCurrency, formatDate } from "@/lib/utils";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export default function Home() {
  const { address, isConnected } = useAccount();
  const { data: balance } = useBalance({ address });
  const { agents, transactions, decisions } = useAppStore();

  const stats = React.useMemo(() => {
    const activeAgents = agents.filter((a) => a.status === "active").length;
    const pendingTx = transactions.filter((t) => t.status === "pending").length;
    const successfulTx = transactions.filter((t) => t.status === "confirmed").length;
    const totalValue = transactions.reduce((acc, tx) => acc + parseFloat(tx.value || "0"), 0);
    
    return {
      totalAgents: agents.length,
      activeAgents,
      totalTransactions: transactions.length,
      pendingTransactions: pendingTx,
      successRate: transactions.length > 0 ? (successfulTx / transactions.length) * 100 : 0,
      totalValue,
    };
  }, [agents, transactions]);

  if (!isConnected) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-2xl"
        >
          <div className="mb-8 inline-flex p-6 rounded-3xl bg-gradient-to-br from-indigo-600 to-purple-600 glow">
            <Wallet className="h-16 w-16 text-white" />
          </div>
          <h1 className="text-4xl md:text-6xl font-bold mb-6 gradient-text">
            Welcome to WalletMind
          </h1>
          <p className="text-xl text-secondary mb-8 leading-relaxed">
            Next-generation blockchain platform merging AI autonomy with decentralized finance.
            Connect your wallet to get started with autonomous AI agents.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="gap-2">
              <ArrowUpRight className="h-5 w-5" />
              Get Started
            </Button>
            <Button size="lg" variant="outline">
              Learn More
            </Button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl md:text-4xl font-bold mb-2">Dashboard</h1>
          <p className="text-secondary">
            Welcome back! Here's an overview of your autonomous AI agents.
          </p>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <motion.div variants={item}>
            <Card variant="glass" hoverable>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 rounded-xl bg-indigo-500/20">
                    <Bot className="h-6 w-6 text-indigo-400" />
                  </div>
                  <Badge variant="primary">{stats.activeAgents} Active</Badge>
                </div>
                <p className="text-3xl font-bold mb-1">{stats.totalAgents}</p>
                <p className="text-sm text-secondary">Total Agents</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={item}>
            <Card variant="glass" hoverable>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 rounded-xl bg-purple-500/20">
                    <Activity className="h-6 w-6 text-purple-400" />
                  </div>
                  <Badge variant="warning">{stats.pendingTransactions} Pending</Badge>
                </div>
                <p className="text-3xl font-bold mb-1">{stats.totalTransactions}</p>
                <p className="text-sm text-secondary">Transactions</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={item}>
            <Card variant="glass" hoverable>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 rounded-xl bg-green-500/20">
                    <TrendingUp className="h-6 w-6 text-green-400" />
                  </div>
                  <div className="flex items-center gap-1 text-green-400 text-sm">
                    <ArrowUpRight className="h-4 w-4" />
                    <span>+12.5%</span>
                  </div>
                </div>
                <p className="text-3xl font-bold mb-1">{stats.successRate.toFixed(1)}%</p>
                <p className="text-sm text-secondary">Success Rate</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={item}>
            <Card variant="glass" hoverable>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 rounded-xl bg-blue-500/20">
                    <Wallet className="h-6 w-6 text-blue-400" />
                  </div>
                  <Badge variant="neutral">ETH</Badge>
                </div>
                <p className="text-3xl font-bold mb-1">
                  {balance ? parseFloat(balance.formatted).toFixed(4) : "0.0000"}
                </p>
                <p className="text-sm text-secondary">Wallet Balance</p>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Transactions */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Recent Transactions</CardTitle>
                <CardDescription>Latest blockchain activity from your agents</CardDescription>
              </CardHeader>
              <CardContent>
                {transactions.length === 0 ? (
                  <div className="text-center py-12">
                    <Activity className="h-12 w-12 text-secondary mx-auto mb-4" />
                    <p className="text-secondary">No transactions yet</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {transactions.slice(0, 5).map((tx) => (
                      <div key={tx.id} className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
                        <div className="flex items-center gap-3">
                          {tx.status === "confirmed" && <CheckCircle className="h-5 w-5 text-green-400" />}
                          {tx.status === "pending" && <Clock className="h-5 w-5 text-yellow-400 animate-pulse" />}
                          {tx.status === "failed" && <AlertCircle className="h-5 w-5 text-red-400" />}
                          <div>
                            <p className="font-medium text-sm">{formatAddress(tx.to)}</p>
                            <p className="text-xs text-secondary">{formatDate(tx.timestamp)}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold">{parseFloat(tx.value).toFixed(4)} ETH</p>
                          <Badge size="sm" variant={
                            tx.status === "confirmed" ? "success" :
                            tx.status === "pending" ? "warning" : "error"
                          }>
                            {tx.status}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Active Agents */}
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Active Agents</CardTitle>
                <CardDescription>Your autonomous AI agents currently running</CardDescription>
              </CardHeader>
              <CardContent>
                {agents.length === 0 ? (
                  <div className="text-center py-12">
                    <Bot className="h-12 w-12 text-secondary mx-auto mb-4" />
                    <p className="text-secondary mb-4">No agents created yet</p>
                    <Button size="sm">Create Your First Agent</Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {agents.slice(0, 5).map((agent) => (
                      <div key={agent.id} className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-600">
                            <Bot className="h-5 w-5 text-white" />
                          </div>
                          <div>
                            <p className="font-medium">{agent.name}</p>
                            <p className="text-xs text-secondary">{agent.type}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge variant={agent.status === "active" ? "success" : "neutral"} size="sm">
                            {agent.status}
                          </Badge>
                          <p className="text-xs text-secondary mt-1">
                            {agent.transactionCount} transactions
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
