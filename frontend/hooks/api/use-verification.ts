/**
 * Verification API Hooks
 * React Query hooks for verification and audit trail
 */

import { useMutation, useQuery } from '@tanstack/react-query';
import { verificationService } from '@/lib/services';
import type { AuditTrailRequest } from '@/lib/api-types';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/api-client';

// Query keys
export const verificationKeys = {
  all: ['verification'] as const,
  auditTrail: (walletAddress: string) => [...verificationKeys.all, 'audit-trail', walletAddress] as const,
  timeline: (walletAddress: string) => [...verificationKeys.all, 'timeline', walletAddress] as const,
  agentActivity: (agentType: string) => [...verificationKeys.all, 'agent-activity', agentType] as const,
  autonomyStats: () => [...verificationKeys.all, 'autonomy-stats'] as const,
  integrityCheck: (walletAddress: string) => [...verificationKeys.all, 'integrity', walletAddress] as const,
};

/**
 * Hook to get audit trail
 */
export function useAuditTrail(request: AuditTrailRequest) {
  return useQuery({
    queryKey: verificationKeys.auditTrail(request.wallet_address),
    queryFn: () => verificationService.getAuditTrail(request),
    enabled: !!request.wallet_address,
  });
}

/**
 * Hook to get wallet timeline
 */
export function useWalletTimeline(walletAddress: string | undefined) {
  return useQuery({
    queryKey: verificationKeys.timeline(walletAddress || ''),
    queryFn: () => verificationService.getTimeline(walletAddress!),
    enabled: !!walletAddress,
  });
}

/**
 * Hook to get agent activity
 */
export function useAgentActivity(agentType: string | undefined) {
  return useQuery({
    queryKey: verificationKeys.agentActivity(agentType || ''),
    queryFn: () => verificationService.getAgentActivity(agentType!),
    enabled: !!agentType,
  });
}

/**
 * Hook to get autonomy statistics
 */
export function useAutonomyStats() {
  return useQuery({
    queryKey: verificationKeys.autonomyStats(),
    queryFn: () => verificationService.getAutonomyStats(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

/**
 * Hook to validate chronology
 */
export function useValidateChronology() {
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: ({
      walletAddress,
      startDate,
      endDate,
    }: {
      walletAddress: string;
      startDate?: string;
      endDate?: string;
    }) => verificationService.validateChronology(walletAddress, startDate, endDate),
    onSuccess: (data) => {
      if (data.is_valid) {
        toast({
          title: 'Chronology Valid',
          description: 'All events are in correct chronological order.',
          variant: 'success',
        });
      } else {
        toast({
          title: 'Chronology Issues Found',
          description: `Found ${data.inconsistencies.length} timestamp inconsistencies.`,
          variant: 'warning',
        });
      }
    },
    onError: (error) => {
      toast({
        title: 'Validation Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to run integrity check
 */
export function useIntegrityCheck(walletAddress: string | undefined) {
  return useQuery({
    queryKey: verificationKeys.integrityCheck(walletAddress || ''),
    queryFn: () => verificationService.integrityCheck(walletAddress!),
    enabled: !!walletAddress,
    staleTime: 60000, // Data stays fresh for 1 minute
  });
}

/**
 * Hook to export verification data
 */
export function useExportVerificationData() {
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (walletAddress: string) => verificationService.exportData(walletAddress),
    onSuccess: (blob, walletAddress) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `verification-${walletAddress.slice(0, 8)}-${Date.now()}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: 'Export Complete',
        description: 'Verification data has been downloaded.',
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Export Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}
