/**
 * Wallet API Service
 * Handles all wallet-related API calls
 */

import { apiClient, API_ENDPOINTS } from '@/lib/api-client';
import type {
  CreateWalletRequest,
  WalletInfo,
  BalanceRequest,
  BalanceResponse,
  NetworkSwitchRequest,
  NetworkInfo,
  UpdateSpendingLimitRequest,
  SpendingLimitResponse,
} from '@/lib/api-types';

export const walletService = {
  /**
   * Create a new smart contract wallet
   */
  createWallet: async (request: CreateWalletRequest): Promise<WalletInfo> => {
    const { data } = await apiClient.post<WalletInfo>(
      API_ENDPOINTS.WALLET.CREATE,
      request
    );
    return data;
  },

  /**
   * Get wallet information
   */
  getWallet: async (address: string): Promise<WalletInfo> => {
    const { data } = await apiClient.get<WalletInfo>(
      API_ENDPOINTS.WALLET.GET(address)
    );
    return data;
  },

  /**
   * Get wallet status
   */
  getWalletStatus: async (address: string): Promise<WalletInfo> => {
    const { data } = await apiClient.get<WalletInfo>(
      API_ENDPOINTS.WALLET.STATUS(address)
    );
    return data;
  },

  /**
   * Get wallet balance
   */
  getBalance: async (request: BalanceRequest): Promise<BalanceResponse> => {
    const { data } = await apiClient.post<BalanceResponse>(
      API_ENDPOINTS.WALLET.BALANCE,
      request
    );
    return data;
  },

  /**
   * Emergency pause wallet
   */
  pauseWallet: async (walletAddress: string): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.WALLET.PAUSE, { wallet_address: walletAddress });
  },

  /**
   * Unpause wallet
   */
  unpauseWallet: async (walletAddress: string): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.WALLET.UNPAUSE, { wallet_address: walletAddress });
  },

  /**
   * Switch blockchain network
   */
  switchNetwork: async (request: NetworkSwitchRequest): Promise<NetworkInfo> => {
    const { data } = await apiClient.post<NetworkInfo>(
      API_ENDPOINTS.WALLET.SWITCH_NETWORK,
      request
    );
    return data;
  },

  /**
   * Get list of available networks
   */
  getNetworks: async (): Promise<NetworkInfo[]> => {
    const { data } = await apiClient.get<NetworkInfo[]>(
      API_ENDPOINTS.WALLET.NETWORKS
    );
    return data;
  },

  /**
   * Update spending limits
   */
  updateSpendingLimit: async (
    request: UpdateSpendingLimitRequest
  ): Promise<SpendingLimitResponse> => {
    const { data } = await apiClient.put<SpendingLimitResponse>(
      API_ENDPOINTS.WALLET.SPENDING_LIMIT,
      request
    );
    return data;
  },

  /**
   * Get current spending limits
   */
  getSpendingLimit: async (address: string): Promise<SpendingLimitResponse> => {
    const { data } = await apiClient.get<SpendingLimitResponse>(
      API_ENDPOINTS.WALLET.GET_SPENDING_LIMIT(address)
    );
    return data;
  },

  /**
   * Reset spent amount for the period
   */
  resetSpent: async (walletAddress: string): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.WALLET.RESET_SPENT, {
      wallet_address: walletAddress,
    });
  },
};
