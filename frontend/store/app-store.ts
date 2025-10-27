/**
 * App Store
 * Global state management with Zustand
 * Integrated with API services and WebSocket real-time updates
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  AgentInfo,
  TransactionInfo,
  DecisionInfo,
  AgentEvent,
  TransactionEvent,
  DecisionEvent,
} from '@/lib/api-types';

// Simplified Agent interface for UI
export interface Agent {
  id: string;
  name: string;
  type: string;
  walletAddress?: string;
  reputation: number;
  autonomyLevel: number;
  transactionCount: number;
  successRate: number;
  status: 'active' | 'inactive' | 'paused';
  createdAt: Date;
}

// Simplified Transaction interface for UI
export interface Transaction {
  id: string;
  hash: string;
  from: string;
  to: string;
  value: string;
  status: 'pending' | 'confirmed' | 'failed';
  timestamp: Date;
  network: string;
  gasUsed?: string;
  decisionHash?: string;
}

// Simplified Decision interface for UI
export interface Decision {
  id: string;
  agentId?: string;
  description: string;
  hash: string;
  ipfsProof: string;
  status: 'pending' | 'executed' | 'failed' | 'verified';
  timestamp: Date;
  transactionHash?: string;
}

interface AppState {
  // State
  agents: Agent[];
  transactions: Transaction[];
  decisions: Decision[];
  selectedNetwork: string;
  isWebSocketConnected: boolean;
  
  // Actions
  addAgent: (agent: Agent) => void;
  updateAgent: (id: string, agent: Partial<Agent>) => void;
  removeAgent: (id: string) => void;
  setAgents: (agents: Agent[]) => void;
  
  addTransaction: (transaction: Transaction) => void;
  updateTransaction: (id: string, transaction: Partial<Transaction>) => void;
  setTransactions: (transactions: Transaction[]) => void;
  
  addDecision: (decision: Decision) => void;
  updateDecision: (id: string, decision: Partial<Decision>) => void;
  setDecisions: (decisions: Decision[]) => void;
  
  setSelectedNetwork: (network: string) => void;
  setWebSocketConnected: (connected: boolean) => void;
  
  // WebSocket event handlers
  handleAgentEvent: (event: AgentEvent) => void;
  handleTransactionEvent: (event: TransactionEvent) => void;
  handleDecisionEvent: (event: DecisionEvent) => void;
  
  // Utility actions
  clearAll: () => void;
}

// Helper function to convert API AgentInfo to UI Agent
export function apiAgentToUIAgent(apiAgent: AgentInfo): Agent {
  return {
    id: apiAgent.agent_id,
    name: apiAgent.name,
    type: apiAgent.agent_type,
    walletAddress: undefined,
    reputation: 0,
    autonomyLevel: 75,
    transactionCount: 0,
    successRate: 0,
    status: apiAgent.status === 'idle' || apiAgent.status === 'thinking' ? 'active' : 'inactive',
    createdAt: new Date(apiAgent.created_at),
  };
}

// Helper function to convert API TransactionInfo to UI Transaction
export function apiTransactionToUITransaction(apiTx: TransactionInfo): Transaction {
  return {
    id: apiTx.transaction_id,
    hash: apiTx.transaction_hash,
    from: apiTx.from_address,
    to: apiTx.to_address,
    value: apiTx.amount,
    status: apiTx.status as 'pending' | 'confirmed' | 'failed',
    timestamp: new Date(apiTx.timestamp),
    network: apiTx.network,
    gasUsed: apiTx.gas_used?.toString(),
    decisionHash: apiTx.decision_hash,
  };
}

// Helper function to convert API DecisionInfo to UI Decision
export function apiDecisionToUIDecision(apiDecision: DecisionInfo): Decision {
  return {
    id: apiDecision.decision_id,
    agentId: undefined,
    description: apiDecision.decision_content,
    hash: apiDecision.decision_hash,
    ipfsProof: apiDecision.ipfs_hash,
    status: apiDecision.status === 'logged' ? 'pending' : apiDecision.status as 'executed' | 'verified',
    timestamp: new Date(apiDecision.timestamp),
    transactionHash: apiDecision.transaction_hash,
  };
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      agents: [],
      transactions: [],
      decisions: [],
      selectedNetwork: 'sepolia',
      isWebSocketConnected: false,
      
      // Agent actions
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
      
      setAgents: (agents) =>
        set({ agents }),
      
      // Transaction actions
      addTransaction: (transaction) =>
        set((state) => ({ transactions: [transaction, ...state.transactions] })),
      
      updateTransaction: (id, updatedTransaction) =>
        set((state) => ({
          transactions: state.transactions.map((tx) =>
            tx.id === id ? { ...tx, ...updatedTransaction } : tx
          ),
        })),
      
      setTransactions: (transactions) =>
        set({ transactions }),
      
      // Decision actions
      addDecision: (decision) =>
        set((state) => ({ decisions: [decision, ...state.decisions] })),
      
      updateDecision: (id, updatedDecision) =>
        set((state) => ({
          decisions: state.decisions.map((dec) =>
            dec.id === id ? { ...dec, ...updatedDecision } : dec
          ),
        })),
      
      setDecisions: (decisions) =>
        set({ decisions }),
      
      // Network actions
      setSelectedNetwork: (network) =>
        set({ selectedNetwork: network }),
      
      // WebSocket actions
      setWebSocketConnected: (connected) =>
        set({ isWebSocketConnected: connected }),
      
      // WebSocket event handlers
      handleAgentEvent: (event) => {
        console.log('[Store] Agent event:', event);
        const { agents } = get();
        
        if (event.event_type === 'status_change') {
          const agentId = event.agent_id;
          const existingAgent = agents.find((a) => a.id === agentId);
          
          if (existingAgent) {
            set((state) => ({
              agents: state.agents.map((agent) =>
                agent.id === agentId
                  ? {
                      ...agent,
                      status: event.data.status === 'active' ? 'active' : 'inactive',
                    }
                  : agent
              ),
            }));
          }
        } else if (event.event_type === 'decision_made') {
          set((state) => ({
            agents: state.agents.map((agent) =>
              agent.id === event.agent_id
                ? { ...agent, transactionCount: agent.transactionCount + 1 }
                : agent
            ),
          }));
        }
      },
      
      handleTransactionEvent: (event) => {
        console.log('[Store] Transaction event:', event);
        const { transactions } = get();
        const existingTx = transactions.find((tx) => tx.hash === event.transaction_hash);
        
        if (event.event_type === 'submitted' && !existingTx) {
          const newTx: Transaction = {
            id: event.data.transaction_id || event.transaction_hash,
            hash: event.transaction_hash,
            from: event.data.from_address || '',
            to: event.data.to_address || '',
            value: event.data.amount || '0',
            status: 'pending',
            timestamp: new Date(event.timestamp),
            network: event.data.network || 'sepolia',
            decisionHash: event.data.decision_hash,
          };
          get().addTransaction(newTx);
        } else if (existingTx) {
          const status = event.event_type === 'confirmed' ? 'confirmed' : event.event_type === 'failed' ? 'failed' : existingTx.status;
          get().updateTransaction(existingTx.id, {
            status: status as 'pending' | 'confirmed' | 'failed',
            gasUsed: event.data.gas_used?.toString(),
          });
        }
      },
      
      handleDecisionEvent: (event) => {
        console.log('[Store] Decision event:', event);
        const { decisions } = get();
        const existingDecision = decisions.find((d) => d.id === event.decision_id);
        
        if (event.event_type === 'logged' && !existingDecision) {
          const newDecision: Decision = {
            id: event.decision_id,
            description: event.data.decision_content || '',
            hash: event.data.decision_hash || '',
            ipfsProof: event.data.ipfs_hash || '',
            status: 'pending',
            timestamp: new Date(event.timestamp),
            transactionHash: event.data.transaction_hash,
          };
          get().addDecision(newDecision);
        } else if (existingDecision) {
          const status = event.event_type === 'executed' ? 'executed' : event.event_type === 'verified' ? 'verified' : existingDecision.status;
          get().updateDecision(existingDecision.id, {
            status: status as 'pending' | 'executed' | 'verified',
            transactionHash: event.data.transaction_hash || existingDecision.transactionHash,
          });
        }
      },
      
      // Utility actions
      clearAll: () =>
        set({
          agents: [],
          transactions: [],
          decisions: [],
        }),
    }),
    {
      name: 'walletmind-storage',
      partialize: (state) => ({
        agents: state.agents,
        selectedNetwork: state.selectedNetwork,
      }),
    }
  )
);
