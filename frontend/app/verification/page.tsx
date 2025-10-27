"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Shield, CheckCircle2, FileSearch, Hash, Clock, ExternalLink, Copy, Check } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAppStore } from "@/store/app-store";
import { formatAddress, formatDate } from "@/lib/utils";

export default function VerificationPage() {
  const { decisions, transactions } = useAppStore();
  const [searchHash, setSearchHash] = React.useState("");
  const [copiedHash, setCopiedHash] = React.useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(id);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const filteredDecisions = React.useMemo(() => {
    if (!searchHash) return decisions;
    return decisions.filter(
      (d) =>
        d.hash.toLowerCase().includes(searchHash.toLowerCase()) ||
        d.ipfsProof.toLowerCase().includes(searchHash.toLowerCase())
    );
  }, [decisions, searchHash]);

  return (
    <div className="min-h-[calc(100vh-4rem)] px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-2">Cryptographic Verification</h1>
          <p className="text-secondary">
            Verify autonomous AI decisions with cryptographic proof and IPFS provenance
          </p>
        </div>

        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Card variant="gradient" className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl" />
            <CardContent className="pt-6 relative">
              <div className="flex flex-col md:flex-row items-center gap-6">
                <div className="p-6 rounded-3xl bg-white/10 backdrop-blur-xl">
                  <Shield className="h-16 w-16 text-indigo-300" />
                </div>
                <div className="flex-1 text-center md:text-left">
                  <h2 className="text-2xl font-bold mb-2">Trustless Verification</h2>
                  <p className="text-secondary leading-relaxed">
                    Every AI decision is cryptographically logged on-chain before execution,
                    providing immutable proof of autonomous operation. Verify decision provenance
                    using blockchain timestamps and IPFS content hashes.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Search */}
        <div className="mb-8">
          <Input
            placeholder="Search by decision hash or IPFS proof..."
            value={searchHash}
            onChange={(e) => setSearchHash(e.target.value)}
            icon={<FileSearch className="h-5 w-5" />}
          />
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <Card variant="glass" hoverable>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4 mb-3">
                  <div className="p-3 rounded-xl bg-indigo-500/20">
                    <Hash className="h-6 w-6 text-indigo-400" />
                  </div>
                  <div>
                    <p className="text-3xl font-bold">{decisions.length}</p>
                    <p className="text-sm text-secondary">Total Decisions</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <Card variant="glass" hoverable>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4 mb-3">
                  <div className="p-3 rounded-xl bg-green-500/20">
                    <CheckCircle2 className="h-6 w-6 text-green-400" />
                  </div>
                  <div>
                    <p className="text-3xl font-bold">
                      {decisions.filter((d) => d.status === "executed").length}
                    </p>
                    <p className="text-sm text-secondary">Verified & Executed</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <Card variant="glass" hoverable>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4 mb-3">
                  <div className="p-3 rounded-xl bg-yellow-500/20">
                    <Clock className="h-6 w-6 text-yellow-400" />
                  </div>
                  <div>
                    <p className="text-3xl font-bold">
                      {decisions.filter((d) => d.status === "pending").length}
                    </p>
                    <p className="text-sm text-secondary">Pending Verification</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Decision List */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle>Decision Provenance Log</CardTitle>
            <CardDescription>
              Cryptographically verified autonomous AI decisions with IPFS proof
            </CardDescription>
          </CardHeader>
          <CardContent>
            {filteredDecisions.length === 0 ? (
              <div className="text-center py-12">
                <Shield className="h-12 w-12 text-secondary mx-auto mb-4" />
                <p className="text-secondary">
                  {searchHash ? "No decisions match your search" : "No decisions logged yet"}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredDecisions.map((decision, index) => {
                  const relatedTx = transactions.find((tx) => tx.hash === decision.transactionHash);
                  
                  return (
                    <motion.div
                      key={decision.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-6 rounded-xl bg-white/5 hover:bg-white/10 transition-all border border-white/10"
                    >
                      {/* Header */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="font-semibold text-lg mb-1">{decision.description}</h3>
                          <p className="text-xs text-secondary">{formatDate(decision.timestamp)}</p>
                        </div>
                        <Badge
                          variant={
                            decision.status === "executed" ? "success" :
                            decision.status === "pending" ? "warning" : "error"
                          }
                        >
                          {decision.status}
                        </Badge>
                      </div>

                      {/* Cryptographic Details */}
                      <div className="space-y-3">
                        {/* Decision Hash */}
                        <div className="p-4 rounded-lg bg-black/20 border border-white/5">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-secondary uppercase tracking-wider">
                              Decision Hash
                            </span>
                            <button
                              onClick={() => copyToClipboard(decision.hash, `hash-${decision.id}`)}
                              className="p-1 hover:bg-white/10 rounded transition-colors"
                            >
                              {copiedHash === `hash-${decision.id}` ? (
                                <Check className="h-4 w-4 text-green-400" />
                              ) : (
                                <Copy className="h-4 w-4" />
                              )}
                            </button>
                          </div>
                          <p className="font-mono text-sm break-all">{decision.hash}</p>
                        </div>

                        {/* IPFS Proof */}
                        <div className="p-4 rounded-lg bg-black/20 border border-white/5">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-secondary uppercase tracking-wider">
                              IPFS Proof
                            </span>
                            <div className="flex gap-2">
                              <button
                                onClick={() => copyToClipboard(decision.ipfsProof, `ipfs-${decision.id}`)}
                                className="p-1 hover:bg-white/10 rounded transition-colors"
                              >
                                {copiedHash === `ipfs-${decision.id}` ? (
                                  <Check className="h-4 w-4 text-green-400" />
                                ) : (
                                  <Copy className="h-4 w-4" />
                                )}
                              </button>
                              <a
                                href={`https://ipfs.io/ipfs/${decision.ipfsProof}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-1 hover:bg-white/10 rounded transition-colors"
                              >
                                <ExternalLink className="h-4 w-4" />
                              </a>
                            </div>
                          </div>
                          <p className="font-mono text-sm break-all">{decision.ipfsProof}</p>
                        </div>

                        {/* Transaction Link */}
                        {decision.transactionHash && relatedTx && (
                          <div className="p-4 rounded-lg bg-black/20 border border-indigo-500/20">
                            <div className="flex items-center justify-between">
                              <div>
                                <span className="text-xs font-medium text-secondary uppercase tracking-wider block mb-1">
                                  Executed Transaction
                                </span>
                                <p className="font-mono text-sm">{formatAddress(decision.transactionHash, 8)}</p>
                              </div>
                              <Badge variant="success" size="sm">
                                <CheckCircle2 className="h-3 w-3 mr-1" />
                                Verified
                              </Badge>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Verification Info */}
                      <div className="mt-4 pt-4 border-t border-white/10">
                        <div className="flex items-center gap-2 text-xs text-secondary">
                          <CheckCircle2 className="h-4 w-4 text-green-400" />
                          <span>
                            Decision cryptographically logged {relatedTx ? "before" : "and awaiting"} execution
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
