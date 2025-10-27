/**
 * Transaction API Service
 * Handles all transaction-related API calls
 */

import { apiClient, API_ENDPOINTS } from '@/lib/api-client';
import type {
  ExecuteTransactionRequest,
  TransactionInfo,
  TransactionHistoryRequest,
  TransactionHistoryResponse,
  TransactionStatsResponse,
  GasEstimateRequest,
  GasEstimateResponse,
} from '@/lib/api-types';

export const transactionService = {
  /**
   * Execute a blockchain transaction
   */
  executeTransaction: async (
    request: ExecuteTransactionRequest
  ): Promise<TransactionInfo> => {
    const { data } = await apiClient.post<TransactionInfo>(
      API_ENDPOINTS.TRANSACTIONS.EXECUTE,
      request
    );
    return data;
  },

  /**
   * Get transaction details by ID
   */
  getTransaction: async (transactionId: string): Promise<TransactionInfo> => {
    const { data } = await apiClient.get<TransactionInfo>(
      API_ENDPOINTS.TRANSACTIONS.GET(transactionId)
    );
    return data;
  },

  /**
   * Estimate gas for a transaction
   */
  estimateGas: async (request: GasEstimateRequest): Promise<GasEstimateResponse> => {
    const { data } = await apiClient.post<GasEstimateResponse>(
      API_ENDPOINTS.TRANSACTIONS.ESTIMATE_GAS,
      request
    );
    return data;
  },

  /**
   * Cancel a pending transaction
   */
  cancelTransaction: async (txHash: string): Promise<TransactionInfo> => {
    const { data } = await apiClient.post<TransactionInfo>(
      API_ENDPOINTS.TRANSACTIONS.CANCEL(txHash)
    );
    return data;
  },

  /**
   * Speed up a pending transaction
   */
  speedUpTransaction: async (txHash: string, newGasPrice: number): Promise<TransactionInfo> => {
    const { data } = await apiClient.post<TransactionInfo>(
      API_ENDPOINTS.TRANSACTIONS.SPEED_UP(txHash),
      { new_gas_price: newGasPrice }
    );
    return data;
  },

  /**
   * Get transaction history
   */
  getHistory: async (
    request: TransactionHistoryRequest
  ): Promise<TransactionHistoryResponse> => {
    const { data } = await apiClient.post<TransactionHistoryResponse>(
      API_ENDPOINTS.TRANSACTIONS.HISTORY,
      request
    );
    return data;
  },

  /**
   * Get transaction statistics for a wallet
   */
  getStats: async (walletAddress: string): Promise<TransactionStatsResponse> => {
    const { data } = await apiClient.get<TransactionStatsResponse>(
      API_ENDPOINTS.TRANSACTIONS.STATS(walletAddress)
    );
    return data;
  },

  /**
   * Check transaction status
   */
  getStatus: async (txHash: string): Promise<{ status: string; confirmations: number }> => {
    const { data } = await apiClient.get<{ status: string; confirmations: number }>(
      API_ENDPOINTS.TRANSACTIONS.STATUS(txHash)
    );
    return data;
  },

  /**
   * Get transaction receipt
   */
  getReceipt: async (txHash: string): Promise<TransactionInfo> => {
    const { data } = await apiClient.get<TransactionInfo>(
      API_ENDPOINTS.TRANSACTIONS.RECEIPT(txHash)
    );
    return data;
  },
};
