/**
 * Transaction API Hooks
 * React Query hooks for transaction-related API calls
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { transactionService } from '@/lib/services';
import type {
  ExecuteTransactionRequest,
  TransactionHistoryRequest,
  GasEstimateRequest,
} from '@/lib/api-types';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/api-client';

// Query keys
export const transactionKeys = {
  all: ['transactions'] as const,
  lists: () => [...transactionKeys.all, 'list'] as const,
  list: (filters: string) => [...transactionKeys.lists(), { filters }] as const,
  details: () => [...transactionKeys.all, 'detail'] as const,
  detail: (id: string) => [...transactionKeys.details(), id] as const,
  history: (walletAddress: string) => [...transactionKeys.all, 'history', walletAddress] as const,
  stats: (walletAddress: string) => [...transactionKeys.all, 'stats', walletAddress] as const,
  status: (txHash: string) => [...transactionKeys.all, 'status', txHash] as const,
};

/**
 * Hook to execute transaction
 */
export function useExecuteTransaction() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (request: ExecuteTransactionRequest) =>
      transactionService.executeTransaction(request),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: transactionKeys.history(data.from_address) });
      queryClient.invalidateQueries({ queryKey: transactionKeys.stats(data.from_address) });
      toast({
        title: 'Transaction Submitted',
        description: `Transaction ${data.transaction_hash?.slice(0, 10)}... has been submitted.`,
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Transaction Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to get transaction details
 */
export function useTransaction(transactionId: string | undefined) {
  return useQuery({
    queryKey: transactionKeys.detail(transactionId || ''),
    queryFn: () => transactionService.getTransaction(transactionId!),
    enabled: !!transactionId,
  });
}

/**
 * Hook to estimate gas
 */
export function useEstimateGas() {
  return useMutation({
    mutationFn: (request: GasEstimateRequest) => transactionService.estimateGas(request),
  });
}

/**
 * Hook to cancel transaction
 */
export function useCancelTransaction() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: (txHash: string) => transactionService.cancelTransaction(txHash),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: transactionKeys.all });
      toast({
        title: 'Transaction Cancelled',
        description: 'Transaction cancellation request has been submitted.',
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Cancellation Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to speed up transaction
 */
export function useSpeedUpTransaction() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: ({ txHash, newGasPrice }: { txHash: string; newGasPrice: number }) =>
      transactionService.speedUpTransaction(txHash, newGasPrice),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: transactionKeys.all });
      toast({
        title: 'Transaction Speed Up',
        description: 'Transaction has been resubmitted with higher gas price.',
        variant: 'success',
      });
    },
    onError: (error) => {
      toast({
        title: 'Speed Up Failed',
        description: getErrorMessage(error),
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to get transaction history
 */
export function useTransactionHistory(request: TransactionHistoryRequest) {
  return useQuery({
    queryKey: transactionKeys.history(request.wallet_address),
    queryFn: () => transactionService.getHistory(request),
    enabled: !!request.wallet_address,
  });
}

/**
 * Hook to get transaction statistics
 */
export function useTransactionStats(walletAddress: string | undefined) {
  return useQuery({
    queryKey: transactionKeys.stats(walletAddress || ''),
    queryFn: () => transactionService.getStats(walletAddress!),
    enabled: !!walletAddress,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

/**
 * Hook to check transaction status
 */
export function useTransactionStatus(txHash: string | undefined) {
  return useQuery({
    queryKey: transactionKeys.status(txHash || ''),
    queryFn: () => transactionService.getStatus(txHash!),
    enabled: !!txHash,
    refetchInterval: (query) => {
      // Stop refetching if transaction is confirmed or failed
      const status = query.state.data?.status;
      return status === 'confirmed' || status === 'failed' ? false : 3000;
    },
  });
}

/**
 * Hook to get transaction receipt
 */
export function useTransactionReceipt(txHash: string | undefined) {
  return useQuery({
    queryKey: transactionKeys.detail(txHash || ''),
    queryFn: () => transactionService.getReceipt(txHash!),
    enabled: !!txHash,
  });
}
