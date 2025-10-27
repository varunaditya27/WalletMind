/**
 * Decision API Hooks
 * React Query hooks for decision logging and verification
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { decisionService } from '@/lib/services';
import type {
  LogDecisionRequest,
  VerificationRequest,
} from '@/lib/api-types';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/api-client';

// Query keys
export const decisionKeys = {
  all: ['decisions'] as const,
  lists: () => [...decisionKeys.all, 'list'] as const,
  list: (filters: string) => [...decisionKeys.lists(), { filters }] as const,
  details: () => [...decisionKeys.all, 'detail'] as const,
  detail: (id: string) => [...decisionKeys.details(), id] as const,
  byHash: (hash: string) => [...decisionKeys.all, 'hash', hash] as const,
  provenance: (txHash: string) => [...decisionKeys.all, 'provenance', txHash] as const,
};

/**
 * Hook to log decision
 */
export function useLogDecision() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (request: LogDecisionRequest) => decisionService.logDecision(request),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: decisionKeys.lists() });
      toast({
        title: 'Decision Logged',
        description: `Decision ${data.decision_hash.slice(0, 10)}... has been logged to blockchain and IPFS.`,
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Logging Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to get decision details
 */
export function useDecision(decisionId: string | undefined) {
  return useQuery({
    queryKey: decisionKeys.detail(decisionId || ''),
    queryFn: () => decisionService.getDecision(decisionId!),
    enabled: !!decisionId,
  });
}

/**
 * Hook to get decision by hash
 */
export function useDecisionByHash(decisionHash: string | undefined) {
  return useQuery({
    queryKey: decisionKeys.byHash(decisionHash || ''),
    queryFn: () => decisionService.getDecisionByHash(decisionHash!),
    enabled: !!decisionHash,
  });
}

/**
 * Hook to verify decision
 */
export function useVerifyDecision() {
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (request: VerificationRequest) => decisionService.verifyDecision(request),
    onSuccess: (data) => {
      if (data.is_valid) {
        toast({
          title: 'Verification Successful',
          description: 'Decision has been verified as authentic.',
          variant: 'success',
        });
      } else {
        toast({
          title: 'Verification Failed',
          description: 'Decision could not be verified. Please check the hash.',
          variant: 'error',
        });
      }
    },
    onError: (error) => {
      toast({
        title: 'Verification Error',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to get decision provenance
 */
export function useDecisionProvenance(txHash: string | undefined) {
  return useQuery({
    queryKey: decisionKeys.provenance(txHash || ''),
    queryFn: () => decisionService.getProvenance(txHash!),
    enabled: !!txHash,
  });
}

/**
 * Hook to batch verify decisions
 */
export function useBatchVerifyDecisions() {
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (decisionHashes: string[]) => decisionService.batchVerify(decisionHashes),
    onSuccess: (results) => {
      const validCount = results.filter((r) => r.is_valid).length;
      toast({
        title: 'Batch Verification Complete',
        description: `${validCount} of ${results.length} decisions verified successfully.`,
        variant: validCount === results.length ? 'success' : 'warning',
      });
    },
    onError: (error) => {
      toast({
        title: 'Batch Verification Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}
