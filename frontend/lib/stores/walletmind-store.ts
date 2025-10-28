"use client";

import { create } from "zustand";

import { PRIMARY_WALLET_ADDRESS, WS_BASE_URL } from "@/lib/env";
import {
  fetchAgentActivity,
  fetchAgentHealth,
  fetchAuditTrail,
  fetchBalance,
  fetchNetworks,
  fetchProviders,
  fetchTransactionHistory,
  fetchTransactionStats,
  fetchWalletStatus,
  pauseWallet,
  toggleNetworkRouting,
  toggleTelemetrySharing,
  updateSpendingGuard,
  unpauseWallet,
} from "@/lib/services/walletmind-service";
import type {
  AgentHealth,
  AuditEntry,
  BalanceResponse,
  NetworkInfo,
  TransactionHistoryResponse,
  TransactionInfo,
  TransactionStatsResponse,
  WalletStatusResponse,
  WebsocketEvent,
} from "@/lib/types";

interface LoadingState {
  dashboard: boolean;
  agent: boolean;
  transactions: boolean;
  settings: boolean;
}

interface InitializedState {
  dashboard: boolean;
  agent: boolean;
  transactions: boolean;
  settings: boolean;
}

interface ErrorState {
  dashboard?: string;
  agent?: string;
  transactions?: string;
  settings?: string;
}

interface WalletMindState {
  networks: NetworkInfo[];
  balances: BalanceResponse[];
  transactionHistory: TransactionInfo[];
  transactionStats: TransactionStatsResponse | null;
  agentHealth: AgentHealth[];
  auditTrail: AuditEntry[];
  agentActivity: Array<Record<string, unknown>>;
  providers: Array<{ provider: string; name: string; base_url: string; cost_per_request: number; supported: boolean }>;
  walletStatus: WalletStatusResponse | null;
  websocketConnected: boolean;
  websocketMessages: WebsocketEvent[];
  websocketError?: string;
  lastSyncedAt?: string;
  preferences: {
    spendingGuard: boolean;
    multiNetwork: boolean;
    telemetry: boolean;
  };
  loading: LoadingState;
  initialized: InitializedState;
  errors: ErrorState;
  initializeDashboard: (force?: boolean) => Promise<void>;
  initializeAgentConsole: (force?: boolean) => Promise<void>;
  initializeTransactions: (force?: boolean) => Promise<void>;
  initializeSettings: (force?: boolean) => Promise<void>;
  refreshAll: () => Promise<void>;
  connectWebsocket: () => void;
  disconnectWebsocket: () => void;
  toggleSpendingGuard: (value: boolean) => Promise<void>;
  toggleMultiNetwork: (value: boolean) => Promise<void>;
  toggleTelemetry: (value: boolean) => Promise<void>;
  pauseWallet: () => Promise<void>;
  unpauseWallet: () => Promise<void>;
}

let socket: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

const MAX_MESSAGES = 30;

export const useWalletMindStore = create<WalletMindState>((set, get) => ({
  networks: [],
  balances: [],
  transactionHistory: [],
  transactionStats: null,
  agentHealth: [],
  auditTrail: [],
  agentActivity: [],
  providers: [],
  walletStatus: null,
  websocketConnected: false,
  websocketMessages: [],
  websocketError: undefined,
  lastSyncedAt: undefined,
  preferences: {
    spendingGuard: true,
    multiNetwork: true,
    telemetry: false,
  },
  loading: {
    dashboard: false,
    agent: false,
    transactions: false,
    settings: false,
  },
  initialized: {
    dashboard: false,
    agent: false,
    transactions: false,
    settings: false,
  },
  errors: {},
  initializeDashboard: async (force = false) => {
    const state = get();
    if (state.loading.dashboard || (state.initialized.dashboard && !force)) {
      return;
    }

    set((current) => ({
      loading: { ...current.loading, dashboard: true },
      errors: { ...current.errors, dashboard: undefined },
    }));

    try {
      const [networks, historyResponse, stats, agentHealth, audit] = await Promise.all([
        fetchNetworks().catch(() => []),
        fetchTransactionHistory(PRIMARY_WALLET_ADDRESS, 12).catch(() => ({
          transactions: [],
          total: 0,
          wallet_address: "",
        }) as TransactionHistoryResponse),
        fetchTransactionStats().catch(() => null),
        fetchAgentHealth().catch(() => []),
        fetchAuditTrail(PRIMARY_WALLET_ADDRESS, 12).catch(() => ({ entries: [], total: 0, wallet_address: "" })),
      ]);

      const networkList = networks.length ? networks : state.networks;
      const balances = await Promise.all(
        networkList.map(async (network) => {
          try {
            return await fetchBalance(network.network);
          } catch (error) {
            console.warn("Failed to load balance for", network.network, error);
            return null;
          }
        })
      );

      set((current) => ({
        networks: networkList.length ? networkList : current.networks,
        balances: balances.filter(Boolean) as BalanceResponse[],
        transactionHistory: historyResponse.transactions,
        transactionStats: stats,
        agentHealth,
        auditTrail: "entries" in audit ? audit.entries : [],
        lastSyncedAt: new Date().toISOString(),
        initialized: { ...current.initialized, dashboard: true },
      }));
    } catch (error) {
      console.error("Dashboard initialization error", error);
      set((current) => ({
        errors: { ...current.errors, dashboard: (error as Error).message ?? "Failed to load dashboard" },
      }));
    } finally {
      set((current) => ({
        loading: { ...current.loading, dashboard: false },
      }));
    }
  },
  initializeAgentConsole: async (force = false) => {
    const state = get();
    if (state.loading.agent || (state.initialized.agent && !force)) {
      return;
    }

    set((current) => ({
      loading: { ...current.loading, agent: true },
      errors: { ...current.errors, agent: undefined },
    }));

    try {
      const [activity, audit] = await Promise.all([
        fetchAgentActivity().catch(() => ({ activities: [], total: 0 })),
        fetchAuditTrail(PRIMARY_WALLET_ADDRESS, 20).catch(() => ({ entries: [], total: 0 })),
      ]);

      set((current) => ({
        agentActivity: activity.activities ?? [],
        auditTrail: "entries" in audit ? audit.entries : current.auditTrail,
        initialized: { ...current.initialized, agent: true },
        lastSyncedAt: new Date().toISOString(),
      }));
    } catch (error) {
      console.error("Agent console initialization error", error);
      set((current) => ({
        errors: { ...current.errors, agent: (error as Error).message ?? "Failed to load agent console" },
      }));
    } finally {
      set((current) => ({ loading: { ...current.loading, agent: false } }));
    }
  },
  initializeTransactions: async (force = false) => {
    const state = get();
    if (state.loading.transactions || (state.initialized.transactions && !force)) {
      return;
    }

    set((current) => ({
      loading: { ...current.loading, transactions: true },
      errors: { ...current.errors, transactions: undefined },
    }));

    try {
      const [historyResponse, stats] = await Promise.all([
        fetchTransactionHistory(PRIMARY_WALLET_ADDRESS, 50).catch(() => ({
          transactions: [],
          total: 0,
          wallet_address: "",
        }) as TransactionHistoryResponse),
        fetchTransactionStats().catch(() => null),
      ]);

      set((current) => ({
        transactionHistory: historyResponse.transactions,
        transactionStats: stats,
        initialized: { ...current.initialized, transactions: true },
        lastSyncedAt: new Date().toISOString(),
      }));
    } catch (error) {
      console.error("Transaction initialization error", error);
      set((current) => ({
        errors: { ...current.errors, transactions: (error as Error).message ?? "Failed to load transactions" },
      }));
    } finally {
      set((current) => ({ loading: { ...current.loading, transactions: false } }));
    }
  },
  initializeSettings: async (force = false) => {
    const state = get();
    if (state.loading.settings || (state.initialized.settings && !force)) {
      return;
    }

    set((current) => ({
      loading: { ...current.loading, settings: true },
      errors: { ...current.errors, settings: undefined },
    }));

    try {
      const [providers, walletStatus] = await Promise.all([
        fetchProviders().catch(() => []),
        fetchWalletStatus().catch(() => null),
      ]);

      set((current) => ({
        providers,
        walletStatus,
        initialized: { ...current.initialized, settings: true },
        lastSyncedAt: new Date().toISOString(),
      }));
    } catch (error) {
      console.error("Settings initialization error", error);
      set((current) => ({
        errors: { ...current.errors, settings: (error as Error).message ?? "Failed to load settings" },
      }));
    } finally {
      set((current) => ({ loading: { ...current.loading, settings: false } }));
    }
  },
  refreshAll: async () => {
    await Promise.all([
      get().initializeDashboard(true),
      get().initializeAgentConsole(true),
      get().initializeTransactions(true),
      get().initializeSettings(true),
    ]);
  },
  connectWebsocket: () => {
    if (typeof window === "undefined") {
      return;
    }

    if (socket || get().websocketConnected) {
      return;
    }

    const wsUrl = `${WS_BASE_URL}/ws`;
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      set({ websocketConnected: true, websocketError: undefined });
      ["agents", "transactions", "decisions", "verification"].forEach((channel) => {
        socket?.send(
          JSON.stringify({
            action: "subscribe",
            channel,
          })
        );
      });
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebsocketEvent;
        set((current) => {
          const nextMessages = [data, ...current.websocketMessages].slice(0, MAX_MESSAGES);
          return { websocketMessages: nextMessages };
        });
      } catch (error) {
        console.warn("Unable to parse websocket message", error);
      }
    };

    socket.onerror = (event) => {
      console.error("Websocket error", event);
      set({ websocketError: "Realtime connection error" });
    };

    socket.onclose = () => {
      set({ websocketConnected: false });
      socket = null;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      reconnectTimer = setTimeout(() => {
        get().connectWebsocket();
      }, 4000);
    };
  },
  disconnectWebsocket: () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (socket) {
      socket.close();
      socket = null;
    }
    set({ websocketConnected: false });
  },
  toggleSpendingGuard: async (value: boolean) => {
    set((current) => ({ preferences: { ...current.preferences, spendingGuard: value } }));
    try {
      await updateSpendingGuard(value);
      await get().initializeSettings(true);
    } catch (error) {
      console.error("Spending guard toggle failed", error);
      set((current) => ({ preferences: { ...current.preferences, spendingGuard: !value }, errors: { ...current.errors, settings: "Failed to update spending guard" } }));
    }
  },
  toggleMultiNetwork: async (value: boolean) => {
    set((current) => ({ preferences: { ...current.preferences, multiNetwork: value } }));
    try {
      await toggleNetworkRouting(value);
      await get().initializeDashboard(true);
    } catch (error) {
      console.error("Network routing toggle failed", error);
      set((current) => ({ preferences: { ...current.preferences, multiNetwork: !value }, errors: { ...current.errors, dashboard: "Failed to switch networks" } }));
    }
  },
  toggleTelemetry: async (value: boolean) => {
    set((current) => ({ preferences: { ...current.preferences, telemetry: value } }));
    try {
      await toggleTelemetrySharing(value);
    } catch (error) {
      console.error("Telemetry toggle failed", error);
      set((current) => ({ preferences: { ...current.preferences, telemetry: !value }, errors: { ...current.errors, settings: "Failed to update telemetry" } }));
    }
  },
  pauseWallet: async () => {
    await pauseWallet();
    await get().initializeSettings(true);
  },
  unpauseWallet: async () => {
    await unpauseWallet();
    await get().initializeSettings(true);
  },
}));
