/**
 * Verification API Service
 * Handles all verification and audit trail API calls
 */

import { apiClient, API_ENDPOINTS } from '@/lib/api-client';
import type {
  AuditTrailRequest,
  AuditTrailResponse,
  TimelineEvent,
  AgentActivity,
  AutonomyStatistics,
  ChronologyValidation,
  IntegrityCheck,
} from '@/lib/api-types';

export const verificationService = {
  /**
   * Get complete audit trail for a wallet
   */
  getAuditTrail: async (request: AuditTrailRequest): Promise<AuditTrailResponse> => {
    const { data } = await apiClient.post<AuditTrailResponse>(
      API_ENDPOINTS.VERIFICATION.AUDIT_TRAIL,
      request
    );
    return data;
  },

  /**
   * Get wallet timeline
   */
  getTimeline: async (walletAddress: string): Promise<TimelineEvent[]> => {
    const { data } = await apiClient.get<TimelineEvent[]>(
      API_ENDPOINTS.VERIFICATION.TIMELINE(walletAddress)
    );
    return data;
  },

  /**
   * Get agent activity by type
   */
  getAgentActivity: async (agentType: string): Promise<AgentActivity> => {
    const { data } = await apiClient.get<AgentActivity>(
      API_ENDPOINTS.VERIFICATION.AGENT_ACTIVITY(agentType)
    );
    return data;
  },

  /**
   * Get autonomy statistics
   */
  getAutonomyStats: async (): Promise<AutonomyStatistics> => {
    const { data } = await apiClient.get<AutonomyStatistics>(
      API_ENDPOINTS.VERIFICATION.AUTONOMY_STATS
    );
    return data;
  },

  /**
   * Validate chronology of events
   */
  validateChronology: async (
    walletAddress: string,
    startDate?: string,
    endDate?: string
  ): Promise<ChronologyValidation> => {
    const { data } = await apiClient.post<ChronologyValidation>(
      API_ENDPOINTS.VERIFICATION.VALIDATE_CHRONOLOGY,
      { wallet_address: walletAddress, start_date: startDate, end_date: endDate }
    );
    return data;
  },

  /**
   * Run integrity check on wallet
   */
  integrityCheck: async (walletAddress: string): Promise<IntegrityCheck> => {
    const { data } = await apiClient.get<IntegrityCheck>(
      API_ENDPOINTS.VERIFICATION.INTEGRITY_CHECK(walletAddress)
    );
    return data;
  },

  /**
   * Export verification data
   */
  exportData: async (walletAddress: string): Promise<Blob> => {
    const { data } = await apiClient.get(
      API_ENDPOINTS.VERIFICATION.EXPORT(walletAddress),
      { responseType: 'blob' }
    );
    return data;
  },
};
