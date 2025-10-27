/**
 * External Integration API Service
 * Handles API payments, oracle data, and inter-agent communication
 */

import { apiClient, API_ENDPOINTS } from '@/lib/api-client';
import type {
  APIPaymentRequest,
  APIPaymentResponse,
  APIProvider,
  DataPurchaseRequest,
  DataPurchaseResponse,
  OracleDataRequest,
  OracleDataResponse,
  RegisterServiceRequest,
  AgentServiceOffering,
  ServiceDiscoveryRequest,
  ServiceDiscoveryResponse,
  InterAgentTransactionRequest,
  InterAgentTransactionResponse,
} from '@/lib/api-types';

export const externalService = {
  // ============= API Payment =============

  /**
   * Pay for API access
   */
  payForAPI: async (request: APIPaymentRequest): Promise<APIPaymentResponse> => {
    const { data } = await apiClient.post<APIPaymentResponse>(
      API_ENDPOINTS.EXTERNAL.API_PAYMENT,
      request
    );
    return data;
  },

  /**
   * Get list of supported API providers
   */
  getAPIProviders: async (): Promise<APIProvider[]> => {
    const { data } = await apiClient.get<APIProvider[]>(
      API_ENDPOINTS.EXTERNAL.API_PROVIDERS
    );
    return data;
  },

  // ============= Data Services =============

  /**
   * Purchase data from provider
   */
  purchaseData: async (request: DataPurchaseRequest): Promise<DataPurchaseResponse> => {
    const { data } = await apiClient.post<DataPurchaseResponse>(
      API_ENDPOINTS.EXTERNAL.DATA_PURCHASE,
      request
    );
    return data;
  },

  /**
   * Query oracle for data
   */
  queryOracle: async (request: OracleDataRequest): Promise<OracleDataResponse> => {
    const { data } = await apiClient.post<OracleDataResponse>(
      API_ENDPOINTS.EXTERNAL.ORACLE_DATA,
      request
    );
    return data;
  },

  // ============= Inter-Agent Services =============

  /**
   * Register an agent service
   */
  registerService: async (request: RegisterServiceRequest): Promise<AgentServiceOffering> => {
    const { data } = await apiClient.post<AgentServiceOffering>(
      API_ENDPOINTS.EXTERNAL.REGISTER_SERVICE,
      request
    );
    return data;
  },

  /**
   * Discover available agent services
   */
  discoverServices: async (
    request: ServiceDiscoveryRequest
  ): Promise<ServiceDiscoveryResponse> => {
    const { data } = await apiClient.post<ServiceDiscoveryResponse>(
      API_ENDPOINTS.EXTERNAL.DISCOVER_SERVICES,
      request
    );
    return data;
  },

  /**
   * Get service details by ID
   */
  getService: async (serviceId: string): Promise<AgentServiceOffering> => {
    const { data } = await apiClient.get<AgentServiceOffering>(
      API_ENDPOINTS.EXTERNAL.GET_SERVICE(serviceId)
    );
    return data;
  },

  /**
   * Get services offered by an agent
   */
  getAgentServices: async (agentAddress: string): Promise<AgentServiceOffering[]> => {
    const { data } = await apiClient.get<AgentServiceOffering[]>(
      API_ENDPOINTS.EXTERNAL.AGENT_SERVICES(agentAddress)
    );
    return data;
  },

  /**
   * Update service availability
   */
  updateServiceAvailability: async (
    serviceId: string,
    isAvailable: boolean
  ): Promise<AgentServiceOffering> => {
    const { data } = await apiClient.put<AgentServiceOffering>(
      API_ENDPOINTS.EXTERNAL.UPDATE_AVAILABILITY(serviceId),
      { is_available: isAvailable }
    );
    return data;
  },

  /**
   * Deregister a service
   */
  deregisterService: async (serviceId: string): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.EXTERNAL.DEREGISTER_SERVICE(serviceId));
  },

  /**
   * Execute inter-agent transaction
   */
  agentTransaction: async (
    request: InterAgentTransactionRequest
  ): Promise<InterAgentTransactionResponse> => {
    const { data } = await apiClient.post<InterAgentTransactionResponse>(
      API_ENDPOINTS.EXTERNAL.AGENT_TRANSACTION,
      request
    );
    return data;
  },
};
