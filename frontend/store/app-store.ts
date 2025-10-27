import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface Agent {
  id: string;
  name: string;
  type: string;
  walletAddress: string;
  reputation: number;
  autonomyLevel: number;
  transactionCount: number;
  successRate: number;
  status: "active" | "inactive" | "paused";
  createdAt: Date;
}

export interface Transaction {
  id: string;
  hash: string;
  from: string;
  to: string;
  value: string;
  status: "pending" | "confirmed" | "failed";
  timestamp: Date;
  network: string;
  gasUsed?: string;
}

export interface Decision {
  id: string;
  agentId: string;
  description: string;
  hash: string;
  ipfsProof: string;
  status: "pending" | "executed" | "failed";
  timestamp: Date;
  transactionHash?: string;
}

interface AppState {
  agents: Agent[];
  transactions: Transaction[];
  decisions: Decision[];
  selectedNetwork: string;
  
  // Actions
  addAgent: (agent: Agent) => void;
  updateAgent: (id: string, agent: Partial<Agent>) => void;
  removeAgent: (id: string) => void;
  
  addTransaction: (transaction: Transaction) => void;
  updateTransaction: (id: string, transaction: Partial<Transaction>) => void;
  
  addDecision: (decision: Decision) => void;
  updateDecision: (id: string, decision: Partial<Decision>) => void;
  
  setSelectedNetwork: (network: string) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      agents: [],
      transactions: [],
      decisions: [],
      selectedNetwork: "sepolia",
      
      addAgent: (agent) =>
        set((state) => ({ agents: [...state.agents, agent] })),
      
      updateAgent: (id, updatedAgent) =>
        set((state) => ({
          agents: state.agents.map((agent) =>
            agent.id === id ? { ...agent, ...updatedAgent } : agent
          ),
        })),
      
      removeAgent: (id) =>
        set((state) => ({
          agents: state.agents.filter((agent) => agent.id !== id),
        })),
      
      addTransaction: (transaction) =>
        set((state) => ({ transactions: [transaction, ...state.transactions] })),
      
      updateTransaction: (id, updatedTransaction) =>
        set((state) => ({
          transactions: state.transactions.map((tx) =>
            tx.id === id ? { ...tx, ...updatedTransaction } : tx
          ),
        })),
      
      addDecision: (decision) =>
        set((state) => ({ decisions: [decision, ...state.decisions] })),
      
      updateDecision: (id, updatedDecision) =>
        set((state) => ({
          decisions: state.decisions.map((dec) =>
            dec.id === id ? { ...dec, ...updatedDecision } : dec
          ),
        })),
      
      setSelectedNetwork: (network) =>
        set({ selectedNetwork: network }),
    }),
    {
      name: "walletmind-storage",
    }
  )
);
