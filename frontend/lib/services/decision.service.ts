/**
 * Decision API Service
 * Handles all decision logging and verification API calls
 */

import { apiClient, API_ENDPOINTS } from '@/lib/api-client';
import type {
  LogDecisionRequest,
  DecisionLogResponse,
  DecisionInfo,
  VerificationRequest,
  VerificationResult,
  ProvenanceChain,
} from '@/lib/api-types';

export const decisionService = {
  /**
   * Log a decision to blockchain and IPFS
   */
  logDecision: async (request: LogDecisionRequest): Promise<DecisionLogResponse> => {
    const { data } = await apiClient.post<DecisionLogResponse>(
      API_ENDPOINTS.DECISIONS.LOG,
      request
    );
    return data;
  },

  /**
   * Get decision details by ID
   */
  getDecision: async (decisionId: string): Promise<DecisionInfo> => {
    const { data } = await apiClient.get<DecisionInfo>(
      API_ENDPOINTS.DECISIONS.GET(decisionId)
    );
    return data;
  },

  /**
   * Get decision by hash
   */
  getDecisionByHash: async (decisionHash: string): Promise<DecisionInfo> => {
    const { data } = await apiClient.get<DecisionInfo>(
      API_ENDPOINTS.DECISIONS.GET_BY_HASH(decisionHash)
    );
    return data;
  },

  /**
   * Verify decision authenticity
   */
  verifyDecision: async (request: VerificationRequest): Promise<VerificationResult> => {
    const { data } = await apiClient.post<VerificationResult>(
      API_ENDPOINTS.DECISIONS.VERIFY,
      request
    );
    return data;
  },

  /**
   * Get decision provenance chain
   */
  getProvenance: async (txHash: string): Promise<ProvenanceChain> => {
    const { data } = await apiClient.get<ProvenanceChain>(
      API_ENDPOINTS.DECISIONS.PROVENANCE(txHash)
    );
    return data;
  },

  /**
   * Verify multiple decisions in batch
   */
  batchVerify: async (
    decisionHashes: string[]
  ): Promise<VerificationResult[]> => {
    const { data } = await apiClient.post<VerificationResult[]>(
      API_ENDPOINTS.DECISIONS.BATCH_VERIFY,
      { decision_hashes: decisionHashes }
    );
    return data;
  },
};
