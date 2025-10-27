/**
 * Agent API Hooks
 * React Query hooks for agent-related API calls
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { agentService } from '@/lib/services';
import type {
  AgentRequest,
  CreateAgentRequest,
  AgentMemoryQuery,
} from '@/lib/api-types';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/api-client';

// Query keys
export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (filters: string) => [...agentKeys.lists(), { filters }] as const,
  details: () => [...agentKeys.all, 'detail'] as const,
  detail: (id: string) => [...agentKeys.details(), id] as const,
  health: () => [...agentKeys.all, 'health'] as const,
  decision: (id: string) => [...agentKeys.all, 'decision', id] as const,
};

/**
 * Hook to process agent request
 */
export function useProcessAgentRequest() {
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (request: AgentRequest) => agentService.processRequest(request),
    onSuccess: () => {
      toast({
        title: 'Request Processed',
        description: 'Agent has successfully processed your request.',
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Request Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to create agent
 */
export function useCreateAgent() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (request: CreateAgentRequest) => agentService.createAgent(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      toast({
        title: 'Agent Created',
        description: 'Your new agent has been created successfully.',
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Creation Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to get agent details
 */
export function useAgent(agentId: string | undefined) {
  return useQuery({
    queryKey: agentKeys.detail(agentId || ''),
    queryFn: () => agentService.getAgent(agentId!),
    enabled: !!agentId,
  });
}

/**
 * Hook to delete agent
 */
export function useDeleteAgent() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (agentId: string) => agentService.deleteAgent(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      toast({
        title: 'Agent Deleted',
        description: 'Agent has been removed successfully.',
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Deletion Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to reset agent
 */
export function useResetAgent() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (agentId: string) => agentService.resetAgent(agentId),
    onSuccess: (_data, agentId) => {
      queryClient.invalidateQueries({ queryKey: agentKeys.detail(agentId) });
      toast({
        title: 'Agent Reset',
        description: 'Agent state has been reset successfully.',
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Reset Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to get decision details
 */
export function useAgentDecision(decisionId: string | undefined) {
  return useQuery({
    queryKey: agentKeys.decision(decisionId || ''),
    queryFn: () => agentService.getDecision(decisionId!),
    enabled: !!decisionId,
  });
}

/**
 * Hook to query agent memory
 */
export function useQueryMemory() {
  return useMutation({
    mutationFn: (query: AgentMemoryQuery) => agentService.queryMemory(query),
  });
}

/**
 * Hook to store in agent memory
 */
export function useStoreMemory() {
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: ({ content, metadata }: { content: string; metadata: Record<string, unknown> }) =>
      agentService.storeMemory(content, metadata),
    onSuccess: () => {
      toast({
        title: 'Memory Stored',
        description: 'Data has been stored in agent memory.',
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Storage Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to get agent health
 */
export function useAgentHealth() {
  return useQuery({
    queryKey: agentKeys.health(),
    queryFn: () => agentService.getHealth(),
    refetchInterval: 10000, // Refetch every 10 seconds
  });
}
