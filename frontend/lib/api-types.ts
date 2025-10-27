/**
 * API Type Definitions
 * TypeScript types for all API requests and responses
 */

// ============= Agent Types =============

export enum AgentType {
  PLANNER = 'planner',
  EXECUTOR = 'executor',
  MONITOR = 'monitor',
  ANALYZER = 'analyzer',
}

export enum AgentStatus {
  IDLE = 'idle',
  THINKING = 'thinking',
  EXECUTING = 'executing',
  WAITING = 'waiting',
  ERROR = 'error',
}

export interface AgentRequest {
  user_id: string;
  request: string;
  agent_type: AgentType;
  context?: Record<string, any>;
}

export interface AgentResponse {
  agent_id: string;
  response: string;
  action_taken?: string;
  status: AgentStatus;
  timestamp: string;
}

export interface CreateAgentRequest {
  name: string;
  agent_type: AgentType;
  user_id: string;
  config?: Record<string, any>;
}

export interface AgentInfo {
  agent_id: string;
  name: string;
  agent_type: AgentType;
  status: AgentStatus;
  created_at: string;
  last_active: string;
  config: Record<string, any>;
}

export interface AgentDecision {
  decision_id: string;
  agent_id: string;
  decision_type: string;
  reasoning: string;
  action: string;
  timestamp: string;
}

export interface AgentMemoryQuery {
  query: string;
  agent_id?: string;
  limit?: number;
}

export interface AgentMemoryEntry {
  id: string;
  content: string;
  metadata: Record<string, any>;
  timestamp: string;
}

export interface AgentMemoryResponse {
  results: AgentMemoryEntry[];
  total: number;
}

export interface AgentHealth {
  agent_id: string;
  status: AgentStatus;
  uptime_seconds: number;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  average_response_time_ms: number;
  last_error?: string;
}

// ============= Wallet Types =============

export enum WalletType {
  SMART_CONTRACT = 'smart_contract',
  EOA = 'eoa',
}

export enum NetworkType {
  ETHEREUM = 'ethereum',
  POLYGON = 'polygon',
  ARBITRUM = 'arbitrum',
  OPTIMISM = 'optimism',
  BASE = 'base',
}

export interface CreateWalletRequest {
  owner_address: string;
  wallet_type: WalletType;
  network: NetworkType;
  initial_deposit?: number;
}

export interface WalletInfo {
  wallet_address: string;
  owner_address: string;
  wallet_type: WalletType;
  network: NetworkType;
  balance: string;
  nonce: number;
  is_deployed: boolean;
  created_at: string;
}

export interface BalanceRequest {
  wallet_address: string;
  network?: NetworkType;
}

export interface BalanceResponse {
  wallet_address: string;
  balance: string;
  balance_usd: number;
  network: NetworkType;
  timestamp: string;
}

export interface NetworkSwitchRequest {
  wallet_address: string;
  target_network: NetworkType;
}

export interface NetworkInfo {
  network: NetworkType;
  chain_id: number;
  rpc_url: string;
  explorer_url: string;
  native_currency: {
    name: string;
    symbol: string;
    decimals: number;
  };
}

export interface UpdateSpendingLimitRequest {
  wallet_address: string;
  daily_limit: number;
  transaction_limit: number;
}

export interface SpendingLimitResponse {
  wallet_address: string;
  daily_limit: number;
  transaction_limit: number;
  current_spent: number;
  reset_time: string;
}

// ============= Transaction Types =============

export enum TransactionType {
  TRANSFER = 'transfer',
  CONTRACT_CALL = 'contract_call',
  API_PAYMENT = 'api_payment',
  DATA_PURCHASE = 'data_purchase',
  AGENT_SERVICE = 'agent_service',
}

export enum TransactionStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export interface ExecuteTransactionRequest {
  wallet_address: string;
  to_address: string;
  amount: number;
  transaction_type: TransactionType;
  data?: string;
  gas_limit?: number;
  gas_price?: number;
  decision_hash?: string;
}

export interface TransactionInfo {
  transaction_id: string;
  transaction_hash: string;
  from_address: string;
  to_address: string;
  amount: string;
  transaction_type: TransactionType;
  status: TransactionStatus;
  network: NetworkType;
  gas_used?: number;
  gas_price?: string;
  block_number?: number;
  timestamp: string;
  decision_hash?: string;
}

export interface TransactionHistoryRequest {
  wallet_address: string;
  start_date?: string;
  end_date?: string;
  transaction_type?: TransactionType;
  status?: TransactionStatus;
  limit?: number;
  offset?: number;
}

export interface TransactionHistoryResponse {
  transactions: TransactionInfo[];
  total: number;
  has_more: boolean;
}

export interface TransactionStatsResponse {
  wallet_address: string;
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  total_volume: string;
  total_gas_spent: string;
  average_gas_price: string;
  period_start: string;
  period_end: string;
}

export interface GasEstimateRequest {
  from_address: string;
  to_address: string;
  amount: number;
  data?: string;
  network: NetworkType;
}

export interface GasEstimateResponse {
  estimated_gas: number;
  gas_price: string;
  estimated_cost: string;
  estimated_cost_usd: number;
}

// ============= Decision Types =============

export enum DecisionStatus {
  LOGGED = 'logged',
  EXECUTED = 'executed',
  VERIFIED = 'verified',
  DISPUTED = 'disputed',
}

export interface LogDecisionRequest {
  wallet_address: string;
  decision_content: string;
  decision_context: Record<string, any>;
  timestamp: string;
  agent_type: AgentType;
}

export interface DecisionLogResponse {
  decision_id: string;
  decision_hash: string;
  ipfs_hash: string;
  transaction_hash: string;
  timestamp: string;
}

export interface DecisionInfo {
  decision_id: string;
  decision_hash: string;
  ipfs_hash: string;
  wallet_address: string;
  decision_content: string;
  decision_context: Record<string, any>;
  agent_type: AgentType;
  status: DecisionStatus;
  timestamp: string;
  transaction_hash?: string;
  block_number?: number;
}

export interface VerificationRequest {
  decision_hash: string;
  expected_content?: string;
}

export interface VerificationResult {
  is_valid: boolean;
  decision_hash: string;
  ipfs_hash: string;
  on_chain_hash?: string;
  timestamp: string;
  discrepancies?: string[];
}

export interface ProvenanceChain {
  decision_hash: string;
  chain: Array<{
    event_type: string;
    timestamp: string;
    transaction_hash?: string;
    block_number?: number;
    details: Record<string, any>;
  }>;
}

// ============= Verification Types =============

export interface AuditTrailRequest {
  wallet_address: string;
  start_date?: string;
  end_date?: string;
  include_decisions?: boolean;
  include_transactions?: boolean;
}

export interface AuditEntry {
  entry_id: string;
  entry_type: 'decision' | 'transaction' | 'wallet_action';
  timestamp: string;
  hash: string;
  content: Record<string, any>;
  verified: boolean;
}

export interface AuditTrailResponse {
  wallet_address: string;
  entries: AuditEntry[];
  total: number;
  period_start: string;
  period_end: string;
}

export interface TimelineEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  description: string;
  transaction_hash?: string;
  decision_hash?: string;
  status: string;
}

export interface AgentActivity {
  agent_type: AgentType;
  total_decisions: number;
  successful_decisions: number;
  failed_decisions: number;
  total_transactions: number;
  total_value_transferred: string;
  average_decision_time_ms: number;
  last_active: string;
}

export interface AutonomyStatistics {
  total_autonomous_actions: number;
  human_interventions: number;
  autonomy_rate: number;
  average_confidence_score: number;
  agent_breakdown: Array<{
    agent_type: AgentType;
    autonomous_actions: number;
    success_rate: number;
  }>;
}

export interface ChronologyValidation {
  is_valid: boolean;
  earliest_timestamp: string;
  latest_timestamp: string;
  total_events: number;
  inconsistencies: Array<{
    event_id: string;
    issue: string;
    timestamp: string;
  }>;
}

export interface IntegrityCheck {
  wallet_address: string;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  issues: Array<{
    check_type: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
  }>;
  overall_status: 'healthy' | 'warning' | 'critical';
}

// ============= External Integration Types =============

export enum PaymentStatus {
  PENDING = 'pending',
  COMPLETED = 'completed',
  FAILED = 'failed',
  REFUNDED = 'refunded',
}

export interface APIPaymentRequest {
  wallet_address: string;
  api_provider: string;
  amount: number;
  plan_type: string;
  billing_period: 'monthly' | 'yearly' | 'one_time';
}

export interface APIPaymentResponse {
  payment_id: string;
  transaction_hash: string;
  api_provider: string;
  amount: string;
  status: PaymentStatus;
  access_token?: string;
  expires_at?: string;
}

export interface APIProvider {
  provider_id: string;
  name: string;
  description: string;
  base_url: string;
  payment_address: string;
  plans: Array<{
    plan_id: string;
    name: string;
    price: number;
    billing_period: string;
    features: string[];
  }>;
}

export interface DataPurchaseRequest {
  wallet_address: string;
  data_provider: string;
  data_type: string;
  query_parameters: Record<string, any>;
  max_price: number;
}

export interface DataPurchaseResponse {
  purchase_id: string;
  transaction_hash: string;
  data_provider: string;
  data_url: string;
  ipfs_hash?: string;
  amount_paid: string;
  timestamp: string;
}

export interface OracleDataRequest {
  oracle_address: string;
  query: string;
  parameters?: Record<string, any>;
}

export interface OracleDataResponse {
  oracle_address: string;
  data: any;
  timestamp: string;
  signature: string;
  is_verified: boolean;
}

export interface AgentServiceOffering {
  service_id: string;
  agent_address: string;
  service_name: string;
  service_type: string;
  description: string;
  price_per_call: number;
  is_available: boolean;
  reputation_score: number;
  total_calls: number;
  successful_calls: number;
  endpoints: Array<{
    method: string;
    path: string;
    description: string;
  }>;
}

export interface RegisterServiceRequest {
  agent_address: string;
  service_name: string;
  service_type: string;
  description: string;
  price_per_call: number;
  endpoints: Array<{
    method: string;
    path: string;
    description: string;
  }>;
}

export interface ServiceDiscoveryRequest {
  service_type?: string;
  min_reputation?: number;
  max_price?: number;
  is_available?: boolean;
}

export interface ServiceDiscoveryResponse {
  services: AgentServiceOffering[];
  total: number;
}

export interface InterAgentTransactionRequest {
  from_agent_address: string;
  to_agent_address: string;
  service_id: string;
  amount: number;
  parameters: Record<string, any>;
}

export interface InterAgentTransactionResponse {
  transaction_id: string;
  transaction_hash: string;
  from_agent: string;
  to_agent: string;
  service_id: string;
  amount: string;
  status: TransactionStatus;
  result?: any;
  timestamp: string;
}

// ============= WebSocket Types =============

export enum WebSocketMessageType {
  AGENT_EVENT = 'agent_event',
  TRANSACTION_EVENT = 'transaction_event',
  DECISION_EVENT = 'decision_event',
  VERIFICATION_EVENT = 'verification_event',
  ERROR = 'error',
  PING = 'ping',
  PONG = 'pong',
}

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
  timestamp: string;
}

export interface AgentEvent {
  agent_id: string;
  event_type: 'status_change' | 'decision_made' | 'action_executed';
  data: Record<string, any>;
  timestamp: string;
}

export interface TransactionEvent {
  transaction_hash: string;
  event_type: 'submitted' | 'confirmed' | 'failed';
  data: Partial<TransactionInfo>;
  timestamp: string;
}

export interface DecisionEvent {
  decision_id: string;
  event_type: 'logged' | 'executed' | 'verified';
  data: Partial<DecisionInfo>;
  timestamp: string;
}

export interface VerificationEvent {
  verification_id: string;
  event_type: 'verification_complete' | 'integrity_check' | 'audit_update';
  data: Record<string, any>;
  timestamp: string;
}
