export type NetworkType =
  | "ethereum_sepolia"
  | "polygon_amoy"
  | "base_goerli";

export interface NetworkInfo {
  network: NetworkType;
  name: string;
  chain_id: number;
  rpc_url: string;
  explorer_url: string;
  native_currency: string;
  is_testnet: boolean;
}

export interface TokenBalance {
  symbol: string;
  amount: number;
  amount_usd?: number;
  decimals?: number;
}

export interface BalanceResponse {
  address: string;
  network: NetworkType;
  balance: number;
  balance_usd?: number;
  tokens: TokenBalance[];
}

export type TransactionStatus =
  | "pending"
  | "confirmed"
  | "failed"
  | "cancelled";

export type TransactionType =
  | "api_payment"
  | "data_purchase"
  | "agent_to_agent"
  | "internal_transfer"
  | "contract_interaction";

export interface TransactionInfo {
  transaction_id: string;
  transaction_hash?: string | null;
  from_address: string;
  to_address: string;
  amount: number;
  transaction_type: TransactionType;
  status: TransactionStatus;
  decision_hash: string;
  timestamp: string;
  confirmed_at?: string | null;
  gas_used?: number | null;
  gas_price?: number | null;
  network: string;
  explorer_url?: string | null;
  metadata: Record<string, unknown>;
  error?: string | null;
}

export interface TransactionHistoryResponse {
  transactions: TransactionInfo[];
  total: number;
  wallet_address: string;
}

export interface TransactionStatsResponse {
  wallet_address: string;
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  total_volume: number;
  total_gas_spent: number;
  success_rate: number;
  average_transaction_value: number;
  by_type: Record<string, number>;
}

export type AgentStatus = "idle" | "thinking" | "executing" | "waiting" | "error";
export type AgentType = "planner" | "executor" | "evaluator" | "communicator";

export interface AgentHealth {
  agent_type: AgentType;
  status: AgentStatus;
  uptime: number;
  total_requests: number;
  success_rate: number;
  last_active: string;
}

export interface CreateAgentRequest {
  agent_type: AgentType;
  name: string;
  config?: Record<string, unknown>;
}

export interface AgentInfo {
  agent_id: string;
  agent_type: AgentType;
  name: string;
  status: AgentStatus;
  created_at: string;
  config?: Record<string, unknown>;
}

export interface AgentDecision {
  decision_id: string;
  intent: string;
  action_type: string;
  parameters: Record<string, unknown>;
  reasoning: string;
  risk_score: number;
  estimated_cost?: number | null;
  requires_approval: boolean;
}

export interface AgentRequest {
  user_id: string;
  request: string;
  context?: Record<string, unknown> | null;
  agent_type?: AgentType;
}

export interface AgentResponse {
  success: boolean;
  message: string;
  decision?: AgentDecision | null;
  execution_time?: number;
  agent_status?: AgentStatus;
  transaction_hash?: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "agent" | "system";
  content: string;
  timestamp: string;
  decision?: AgentDecision;
  needsApproval?: boolean;
  needsClarification?: boolean;
}

export interface AuditEntry {
  entry_id: string;
  timestamp: string;
  entry_type: string;
  decision_hash?: string | null;
  transaction_hash?: string | null;
  action: string;
  agent_type?: string | null;
  status: string;
  details: Record<string, unknown>;
}

export interface AuditTrailResponse {
  wallet_address: string;
  entries: AuditEntry[];
  total: number;
  from_date?: string | null;
  to_date?: string | null;
}

export interface APIProviderInfo {
  provider: string;
  name: string;
  base_url: string;
  cost_per_request: number;
  supported: boolean;
}

export interface WalletStatusResponse {
  wallet_address: string;
  is_paused: boolean;
  is_active: boolean;
  owner: string;
  last_transaction?: string | null;
}

export interface WebsocketEvent {
  type: string;
  event?: string;
  channel?: string;
  status?: string;
  timestamp?: string;
  data?: Record<string, unknown>;
  [key: string]: unknown;
}
