/**
 * MetaMask Wallet Connection Hook
 * Handles wallet connection, account management, and signature requests
 */

import { useState, useEffect, useCallback } from 'react';

declare global {
  interface Window {
    ethereum?: any;
  }
}

export interface WalletState {
  address: string | null;
  isConnected: boolean;
  isConnecting: boolean;
  chainId: number | null;
  error: string | null;
}

export const useMetaMask = () => {
  const [walletState, setWalletState] = useState<WalletState>({
    address: null,
    isConnected: false,
    isConnecting: false,
    chainId: null,
    error: null,
  });

  // Check if MetaMask is installed
  const isMetaMaskInstalled = useCallback(() => {
    return typeof window !== 'undefined' && Boolean(window.ethereum?.isMetaMask);
  }, []);

  // Connect to MetaMask
  const connect = useCallback(async () => {
    if (!isMetaMaskInstalled()) {
      setWalletState(prev => ({
        ...prev,
        error: 'MetaMask is not installed. Please install it from metamask.io',
      }));
      return null;
    }

    setWalletState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      // Request account access
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts',
      });

      if (accounts.length === 0) {
        throw new Error('No accounts found');
      }

      const address = accounts[0];

      // Get chain ID
      const chainId = await window.ethereum.request({
        method: 'eth_chainId',
      });

      setWalletState({
        address,
        isConnected: true,
        isConnecting: false,
        chainId: parseInt(chainId, 16),
        error: null,
      });

      return address;
    } catch (error: any) {
      console.error('Error connecting to MetaMask:', error);
      setWalletState({
        address: null,
        isConnected: false,
        isConnecting: false,
        chainId: null,
        error: error.message || 'Failed to connect to MetaMask',
      });
      return null;
    }
  }, [isMetaMaskInstalled]);

  // Disconnect wallet
  const disconnect = useCallback(() => {
    setWalletState({
      address: null,
      isConnected: false,
      isConnecting: false,
      chainId: null,
      error: null,
    });
  }, []);

  // Sign a message with MetaMask
  const signMessage = useCallback(async (message: string, address?: string): Promise<string | null> => {
    const signingAddress = address || walletState.address;
    
    if (!signingAddress) {
      throw new Error('Wallet not connected');
    }

    try {
      const signature = await window.ethereum.request({
        method: 'personal_sign',
        params: [message, signingAddress],
      });

      return signature;
    } catch (error: any) {
      console.error('Error signing message:', error);
      throw new Error(error.message || 'Failed to sign message');
    }
  }, [walletState.address]);

  // Listen for account changes
  useEffect(() => {
    if (!isMetaMaskInstalled()) return;

    const handleAccountsChanged = (accounts: string[]) => {
      if (accounts.length === 0) {
        // User disconnected wallet
        disconnect();
      } else {
        // User switched accounts
        setWalletState(prev => ({
          ...prev,
          address: accounts[0],
          isConnected: true,
        }));
      }
    };

    const handleChainChanged = (chainId: string) => {
      setWalletState(prev => ({
        ...prev,
        chainId: parseInt(chainId, 16),
      }));
    };

    window.ethereum.on('accountsChanged', handleAccountsChanged);
    window.ethereum.on('chainChanged', handleChainChanged);

    return () => {
      if (window.ethereum.removeListener) {
        window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
        window.ethereum.removeListener('chainChanged', handleChainChanged);
      }
    };
  }, [isMetaMaskInstalled, disconnect]);

  // Check if already connected on mount
  useEffect(() => {
    if (!isMetaMaskInstalled()) return;

    const checkConnection = async () => {
      try {
        const accounts = await window.ethereum.request({
          method: 'eth_accounts',
        });

        if (accounts.length > 0) {
          const chainId = await window.ethereum.request({
            method: 'eth_chainId',
          });

          setWalletState({
            address: accounts[0],
            isConnected: true,
            isConnecting: false,
            chainId: parseInt(chainId, 16),
            error: null,
          });
        }
      } catch (error) {
        console.error('Error checking connection:', error);
      }
    };

    checkConnection();
  }, [isMetaMaskInstalled]);

  return {
    ...walletState,
    connect,
    disconnect,
    signMessage,
    isMetaMaskInstalled: isMetaMaskInstalled(),
  };
};
