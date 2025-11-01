import { apiGet, apiPost, apiPut, apiPostQuery } from "@/lib/api-client";
import {
  APIProviderInfo,
  AgentHealth,
  AgentInfo,
  AgentRequest,
  AgentResponse,
  AuditTrailResponse,
  BalanceResponse,
  CreateAgentRequest,
  NetworkInfo,
  NetworkType,
  TransactionHistoryResponse,
  TransactionStatsResponse,
  WalletStatusResponse,
} from "@/lib/types";
import { PRIMARY_AGENT_TYPE, PRIMARY_WALLET_ADDRESS, SECONDARY_NETWORK } from "@/lib/env";

export async function fetchNetworks(): Promise<NetworkInfo[]> {
  return apiGet<NetworkInfo[]>("/api/wallet/networks");
}

export async function fetchBalance(
  network: NetworkType,
  walletAddress: string = PRIMARY_WALLET_ADDRESS
): Promise<BalanceResponse> {
  return apiPost<BalanceResponse>("/api/wallet/balance", {
    wallet_address: walletAddress,
    network,
  });
}

export async function fetchTransactionHistory(
  walletAddress: string = PRIMARY_WALLET_ADDRESS,
  limit = 10
): Promise<TransactionHistoryResponse> {
  return apiPost<TransactionHistoryResponse>("/api/transactions/history", {
    wallet_address: walletAddress,
    limit,
  });
}

export async function fetchTransactionStats(
  walletAddress: string = PRIMARY_WALLET_ADDRESS
): Promise<TransactionStatsResponse> {
  return apiGet<TransactionStatsResponse>(`/api/transactions/stats/${walletAddress}`);
}

export async function fetchAgentHealth(): Promise<AgentHealth[]> {
  return apiGet<AgentHealth[]>("/api/agents/health");
}

export async function fetchAuditTrail(
  walletAddress: string = PRIMARY_WALLET_ADDRESS,
  limit = 12
): Promise<AuditTrailResponse> {
  return apiPost<AuditTrailResponse>("/api/verification/audit-trail", {
    wallet_address: walletAddress,
    limit,
  });
}

export interface AgentActivityResponse {
  agent_type: string;
  activities: Array<Record<string, unknown>>;
  total: number;
}

export async function fetchAgentActivity(
  agentType: string = PRIMARY_AGENT_TYPE,
  limit = 20
): Promise<AgentActivityResponse> {
  return apiGet<AgentActivityResponse>(
    `/api/verification/agent/${encodeURIComponent(agentType)}/activity?limit=${limit}`
  );
}

export interface ProviderResponse {
  providers: APIProviderInfo[];
}

export async function fetchProviders(): Promise<APIProviderInfo[]> {
  const response = await apiGet<ProviderResponse>("/api/external/api-providers");
  return response.providers ?? [];
}

export async function fetchWalletStatus(
  walletAddress: string = PRIMARY_WALLET_ADDRESS
): Promise<WalletStatusResponse> {
  return apiGet<WalletStatusResponse>(`/api/wallet/status/${walletAddress}`);
}

export async function updateSpendingGuard(
  enabled: boolean,
  walletAddress = PRIMARY_WALLET_ADDRESS
): Promise<Record<string, unknown>> {
  const newLimit = enabled ? 0.5 : 10_000;
  return apiPut("/api/wallet/spending-limit", {
    wallet_address: walletAddress,
    new_limit: newLimit,
  });
}

export async function toggleNetworkRouting(
  enable: boolean,
  walletAddress = PRIMARY_WALLET_ADDRESS
) : Promise<Record<string, unknown>> {
  const targetNetwork = enable ? SECONDARY_NETWORK : "ethereum_sepolia";
  return apiPost("/api/wallet/switch-network", {
    wallet_address: walletAddress,
    target_network: targetNetwork,
  });
}

export async function toggleTelemetrySharing(enabled: boolean) {
  const content = enabled
    ? "Telemetry sharing enabled via dashboard toggle"
    : "Telemetry sharing disabled via dashboard toggle";
  return apiPostQuery("/api/agents/memory/store", {
    content,
    agent_type: PRIMARY_AGENT_TYPE,
    metadata: JSON.stringify({ source: "frontend_toggle", enabled }),
  });
}

export async function pauseWallet(
  walletAddress = PRIMARY_WALLET_ADDRESS
): Promise<Record<string, unknown>> {
  return apiPostQuery("/api/wallet/pause", { wallet_address: walletAddress });
}

export async function unpauseWallet(
  walletAddress = PRIMARY_WALLET_ADDRESS
): Promise<Record<string, unknown>> {
  return apiPostQuery("/api/wallet/unpause", { wallet_address: walletAddress });
}

export async function createAgent(request: CreateAgentRequest): Promise<AgentInfo> {
  return apiPost<AgentInfo>("/api/agents/create", request);
}

export async function sendAgentRequest(request: AgentRequest): Promise<AgentResponse> {
  return apiPost<AgentResponse>("/api/agents/request", request);
}

export async function respondToApproval(
  decisionId: string,
  approved: boolean,
  reason?: string
): Promise<AgentResponse> {
  return apiPost<AgentResponse>("/api/agents/approval/respond", {
    decision_id: decisionId,
    approved,
    reason,
  });
}

export async function respondToClarification(
  decisionId: string,
  clarification: string
): Promise<AgentResponse> {
  return apiPost<AgentResponse>("/api/agents/clarification/respond", {
    decision_id: decisionId,
    clarification,
  });
}
