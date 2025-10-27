/**
 * Wallet API Hooks
 * React Query hooks for wallet-related API calls
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { walletService } from '@/lib/services';
import type {
  CreateWalletRequest,
  BalanceRequest,
  NetworkSwitchRequest,
  UpdateSpendingLimitRequest,
} from '@/lib/api-types';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/api-client';

// Query keys
export const walletKeys = {
  all: ['wallets'] as const,
  lists: () => [...walletKeys.all, 'list'] as const,
  list: (filters: string) => [...walletKeys.lists(), { filters }] as const,
  details: () => [...walletKeys.all, 'detail'] as const,
  detail: (address: string) => [...walletKeys.details(), address] as const,
  balance: (address: string) => [...walletKeys.all, 'balance', address] as const,
  networks: () => [...walletKeys.all, 'networks'] as const,
  spendingLimit: (address: string) => [...walletKeys.all, 'spending-limit', address] as const,
};

/**
 * Hook to create wallet
 */
export function useCreateWallet() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (request: CreateWalletRequest) => walletService.createWallet(request),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: walletKeys.lists() });
      toast({
        title: 'Wallet Created',
        description: `Smart wallet ${data.wallet_address.slice(0, 10)}... has been deployed.`,
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Wallet Creation Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to get wallet info
 */
export function useWallet(address: string | undefined) {
  return useQuery({
    queryKey: walletKeys.detail(address || ''),
    queryFn: () => walletService.getWallet(address!),
    enabled: !!address,
  });
}

/**
 * Hook to get wallet status
 */
export function useWalletStatus(address: string | undefined) {
  return useQuery({
    queryKey: [...walletKeys.detail(address || ''), 'status'],
    queryFn: () => walletService.getWalletStatus(address!),
    enabled: !!address,
    refetchInterval: 10000, // Refetch every 10 seconds
  });
}

/**
 * Hook to get wallet balance
 */
export function useWalletBalance(request: BalanceRequest) {
  return useQuery({
    queryKey: walletKeys.balance(request.wallet_address),
    queryFn: () => walletService.getBalance(request),
    enabled: !!request.wallet_address,
    refetchInterval: 15000, // Refetch every 15 seconds
  });
}

/**
 * Hook to pause wallet
 */
export function usePauseWallet() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (walletAddress: string) => walletService.pauseWallet(walletAddress),
    onSuccess: (_data, walletAddress) => {
      queryClient.invalidateQueries({ queryKey: walletKeys.detail(walletAddress) });
      toast({
        title: 'Wallet Paused',
        description: 'Wallet has been paused successfully. No transactions can be executed.',
        variant: 'warning',
      });
    },
    onError: (error) => {
      toast({
        title: 'Pause Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to unpause wallet
 */
export function useUnpauseWallet() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (walletAddress: string) => walletService.unpauseWallet(walletAddress),
    onSuccess: (_data, walletAddress) => {
      queryClient.invalidateQueries({ queryKey: walletKeys.detail(walletAddress) });
      toast({
        title: 'Wallet Unpaused',
        description: 'Wallet has been unpaused. Transactions can now be executed.',
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Unpause Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to switch network
 */
export function useSwitchNetwork() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (request: NetworkSwitchRequest) => walletService.switchNetwork(request),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: walletKeys.detail(variables.wallet_address) });
      toast({
        title: 'Network Switched',
        description: `Wallet is now connected to ${data.network}.`,
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Network Switch Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to get available networks
 */
export function useNetworks() {
  return useQuery({
    queryKey: walletKeys.networks(),
    queryFn: () => walletService.getNetworks(),
    staleTime: Infinity, // Networks don't change often
  });
}

/**
 * Hook to update spending limit
 */
export function useUpdateSpendingLimit() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (request: UpdateSpendingLimitRequest) =>
      walletService.updateSpendingLimit(request),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: walletKeys.spendingLimit(variables.wallet_address),
      });
      toast({
        title: 'Spending Limit Updated',
        description: `New daily limit: ${data.daily_limit} ETH`,
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Update Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to get spending limit
 */
export function useSpendingLimit(address: string | undefined) {
  return useQuery({
    queryKey: walletKeys.spendingLimit(address || ''),
    queryFn: () => walletService.getSpendingLimit(address!),
    enabled: !!address,
  });
}

/**
 * Hook to reset spent amount
 */
export function useResetSpent() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (walletAddress: string) => walletService.resetSpent(walletAddress),
    onSuccess: (_data, walletAddress) => {
      queryClient.invalidateQueries({ queryKey: walletKeys.spendingLimit(walletAddress) });
      toast({
        title: 'Spent Amount Reset',
        description: 'Spending counter has been reset.',
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
