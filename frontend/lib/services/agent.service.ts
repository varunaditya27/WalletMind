/**
 * Agent API Service
 * Handles all agent-related API calls
 */

import { apiClient, API_ENDPOINTS } from '@/lib/api-client';
import type {
  AgentRequest,
  AgentResponse,
  CreateAgentRequest,
  AgentInfo,
  AgentDecision,
  AgentMemoryQuery,
  AgentMemoryResponse,
  AgentHealth,
} from '@/lib/api-types';

export const agentService = {
  /**
   * Process a natural language request through an agent
   */
  processRequest: async (request: AgentRequest): Promise<AgentResponse> => {
    const { data } = await apiClient.post<AgentResponse>(
      API_ENDPOINTS.AGENTS.REQUEST,
      request
    );
    return data;
  },

  /**
   * Create a new agent instance
   */
  createAgent: async (request: CreateAgentRequest): Promise<AgentInfo> => {
    const { data } = await apiClient.post<AgentInfo>(
      API_ENDPOINTS.AGENTS.CREATE,
      request
    );
    return data;
  },

  /**
   * Get agent information by ID
   */
  getAgent: async (agentId: string): Promise<AgentInfo> => {
    const { data } = await apiClient.get<AgentInfo>(
      API_ENDPOINTS.AGENTS.GET(agentId)
    );
    return data;
  },

  /**
   * Delete/stop an agent
   */
  deleteAgent: async (agentId: string): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.AGENTS.DELETE(agentId));
  },

  /**
   * Reset agent state
   */
  resetAgent: async (agentId: string): Promise<AgentInfo> => {
    const { data } = await apiClient.post<AgentInfo>(
      API_ENDPOINTS.AGENTS.RESET(agentId)
    );
    return data;
  },

  /**
   * Get decision details
   */
  getDecision: async (decisionId: string): Promise<AgentDecision> => {
    const { data } = await apiClient.get<AgentDecision>(
      API_ENDPOINTS.AGENTS.DECISION(decisionId)
    );
    return data;
  },

  /**
   * Query agent memory
   */
  queryMemory: async (query: AgentMemoryQuery): Promise<AgentMemoryResponse> => {
    const { data } = await apiClient.post<AgentMemoryResponse>(
      API_ENDPOINTS.AGENTS.MEMORY_QUERY,
      query
    );
    return data;
  },

  /**
   * Store data in agent memory
   */
  storeMemory: async (content: string, metadata: Record<string, unknown>): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.AGENTS.MEMORY_STORE, {
      content,
      metadata,
    });
  },

  /**
   * Get agent health metrics
   */
  getHealth: async (): Promise<AgentHealth[]> => {
    const { data } = await apiClient.get<AgentHealth[]>(
      API_ENDPOINTS.AGENTS.HEALTH
    );
    return data;
  },
};
