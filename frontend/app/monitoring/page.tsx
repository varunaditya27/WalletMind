"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { useAccount } from "wagmi";
import { Activity, Clock, CheckCircle, XCircle, TrendingUp, Zap } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAppStore } from "@/store/app-store";
import { formatAddress, formatDate } from "@/lib/utils";

export default function MonitoringPage() {
  const { isConnected } = useAccount();
  const { transactions, decisions } = useAppStore();

  if (!isConnected) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
        <Card variant="glass" className="max-w-md text-center">
          <CardContent className="pt-6">
            <Activity className="h-16 w-16 text-secondary mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Connect Wallet</h2>
            <p className="text-secondary">
              Please connect your wallet to monitor activity
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const pendingTransactions = transactions.filter(tx => tx.status === "pending");
  const completedTransactions = transactions.filter(tx => tx.status === "confirmed");
  const failedTransactions = transactions.filter(tx => tx.status === "failed");

  return (
    <div className="min-h-[calc(100vh-4rem)] px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-2">Real-Time Monitoring</h1>
          <p className="text-secondary">
            Live feed of autonomous agent decisions and transactions
          </p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <Card variant="glass" hoverable>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <Clock className="h-8 w-8 text-yellow-400" />
                  <span className="text-3xl font-bold">{pendingTransactions.length}</span>
                </div>
                <p className="text-sm text-secondary">Pending</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <Card variant="glass" hoverable>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <CheckCircle className="h-8 w-8 text-green-400" />
                  <span className="text-3xl font-bold">{completedTransactions.length}</span>
                </div>
                <p className="text-sm text-secondary">Completed</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <Card variant="glass" hoverable>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <XCircle className="h-8 w-8 text-red-400" />
                  <span className="text-3xl font-bold">{failedTransactions.length}</span>
                </div>
                <p className="text-sm text-secondary">Failed</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <Card variant="glass" hoverable>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <Activity className="h-8 w-8 text-indigo-400" />
                  <span className="text-3xl font-bold">{transactions.length}</span>
                </div>
                <p className="text-sm text-secondary">Total Activity</p>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Activity Feed */}
        <Tabs defaultValue="all" className="space-y-6">
          <TabsList>
            <TabsTrigger value="all">All Activity</TabsTrigger>
            <TabsTrigger value="pending">Pending</TabsTrigger>
            <TabsTrigger value="decisions">Decisions</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4">
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Transaction History</CardTitle>
                <CardDescription>Complete log of all blockchain transactions</CardDescription>
              </CardHeader>
              <CardContent>
                {transactions.length === 0 ? (
                  <div className="text-center py-12">
                    <Activity className="h-12 w-12 text-secondary mx-auto mb-4" />
                    <p className="text-secondary">No transactions yet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {transactions.map((tx, index) => (
                      <motion.div
                        key={tx.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            {tx.status === "confirmed" && <CheckCircle className="h-5 w-5 text-green-400" />}
                            {tx.status === "pending" && <Clock className="h-5 w-5 text-yellow-400 animate-pulse" />}
                            {tx.status === "failed" && <XCircle className="h-5 w-5 text-red-400" />}
                            <div>
                              <p className="font-medium">{formatAddress(tx.to)}</p>
                              <p className="text-xs text-secondary">{formatDate(tx.timestamp)}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-bold">{parseFloat(tx.value).toFixed(4)} ETH</p>
                            <Badge
                              size="sm"
                              variant={
                                tx.status === "confirmed" ? "success" :
                                tx.status === "pending" ? "warning" : "error"
                              }
                            >
                              {tx.status}
                            </Badge>
                          </div>
                        </div>
                        {tx.hash && (
                          <div className="mt-3 pt-3 border-t border-white/10">
                            <p className="text-xs text-secondary">
                              Hash: <span className="font-mono">{formatAddress(tx.hash, 6)}</span>
                            </p>
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="pending" className="space-y-4">
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Pending Transactions</CardTitle>
                <CardDescription>Transactions currently being processed</CardDescription>
              </CardHeader>
              <CardContent>
                {pendingTransactions.length === 0 ? (
                  <div className="text-center py-12">
                    <Clock className="h-12 w-12 text-secondary mx-auto mb-4" />
                    <p className="text-secondary">No pending transactions</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {pendingTransactions.map((tx) => (
                      <div key={tx.id} className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/30">
                        <div className="flex items-center gap-3">
                          <Clock className="h-5 w-5 text-yellow-400 animate-pulse" />
                          <div className="flex-1">
                            <p className="font-medium">{formatAddress(tx.to)}</p>
                            <p className="text-xs text-secondary">{formatDate(tx.timestamp)}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold">{parseFloat(tx.value).toFixed(4)} ETH</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="decisions" className="space-y-4">
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Agent Decisions</CardTitle>
                <CardDescription>Cryptographically logged AI decisions</CardDescription>
              </CardHeader>
              <CardContent>
                {decisions.length === 0 ? (
                  <div className="text-center py-12">
                    <Zap className="h-12 w-12 text-secondary mx-auto mb-4" />
                    <p className="text-secondary">No decisions logged yet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {decisions.map((decision) => (
                      <div key={decision.id} className="p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all">
                        <div className="flex items-center justify-between mb-3">
                          <p className="font-medium">{decision.description}</p>
                          <Badge
                            variant={
                              decision.status === "executed" ? "success" :
                              decision.status === "pending" ? "warning" : "error"
                            }
                          >
                            {decision.status}
                          </Badge>
                        </div>
                        <div className="text-xs text-secondary space-y-1">
                          <p>Hash: <span className="font-mono">{formatAddress(decision.hash, 8)}</span></p>
                          <p>IPFS: <span className="font-mono">{formatAddress(decision.ipfsProof, 8)}</span></p>
                          <p>{formatDate(decision.timestamp)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
