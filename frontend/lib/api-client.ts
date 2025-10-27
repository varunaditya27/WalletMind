/**
 * API Client Configuration
 * Axios instance with interceptors for the WalletMind backend
 */

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

// API Base URL from environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add timestamp to prevent caching
    config.headers['X-Request-Time'] = new Date().toISOString();
    
    // Add auth token if available (for future use)
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config?.url,
      });
      
      // Handle specific status codes
      switch (error.response.status) {
        case 401:
          // Unauthorized - clear auth and redirect
          if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
            // Could trigger a toast notification here
          }
          break;
        case 403:
          console.error('Forbidden: Insufficient permissions');
          break;
        case 404:
          console.error('Resource not found');
          break;
        case 500:
          console.error('Server error');
          break;
      }
    } else if (error.request) {
      // Request made but no response
      console.error('No response from server:', error.message);
    } else {
      // Something else happened
      console.error('Request error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Helper function to extract error message
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
    return (
      axiosError.response?.data?.detail ||
      axiosError.response?.data?.message ||
      axiosError.message ||
      'An unexpected error occurred'
    );
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
};

// API endpoints configuration
export const API_ENDPOINTS = {
  // Agent endpoints
  AGENTS: {
    REQUEST: '/api/agents/request',
    CREATE: '/api/agents/create',
    GET: (id: string) => `/api/agents/${id}`,
    DELETE: (id: string) => `/api/agents/${id}`,
    RESET: (id: string) => `/api/agents/${id}/reset`,
    DECISION: (id: string) => `/api/agents/decision/${id}`,
    MEMORY_QUERY: '/api/agents/memory/query',
    MEMORY_STORE: '/api/agents/memory/store',
    HEALTH: '/api/agents/health',
  },
  
  // Wallet endpoints
  WALLET: {
    CREATE: '/api/wallet/create',
    GET: (address: string) => `/api/wallet/${address}`,
    STATUS: (address: string) => `/api/wallet/status/${address}`,
    BALANCE: '/api/wallet/balance',
    PAUSE: '/api/wallet/pause',
    UNPAUSE: '/api/wallet/unpause',
    SWITCH_NETWORK: '/api/wallet/switch-network',
    NETWORKS: '/api/wallet/networks',
    SPENDING_LIMIT: '/api/wallet/spending-limit',
    GET_SPENDING_LIMIT: (address: string) => `/api/wallet/spending-limit/${address}`,
    RESET_SPENT: '/api/wallet/reset-spent',
  },
  
  // Transaction endpoints
  TRANSACTIONS: {
    EXECUTE: '/api/transactions/execute',
    GET: (id: string) => `/api/transactions/${id}`,
    ESTIMATE_GAS: '/api/transactions/estimate-gas',
    CANCEL: (hash: string) => `/api/transactions/${hash}/cancel`,
    SPEED_UP: (hash: string) => `/api/transactions/${hash}/speed-up`,
    HISTORY: '/api/transactions/history',
    STATS: (address: string) => `/api/transactions/stats/${address}`,
    STATUS: (hash: string) => `/api/transactions/${hash}/status`,
    RECEIPT: (hash: string) => `/api/transactions/${hash}/receipt`,
  },
  
  // Decision endpoints
  DECISIONS: {
    LOG: '/api/decisions/log',
    GET: (id: string) => `/api/decisions/${id}`,
    GET_BY_HASH: (hash: string) => `/api/decisions/hash/${hash}`,
    VERIFY: '/api/decisions/verify',
    PROVENANCE: (hash: string) => `/api/decisions/provenance/${hash}`,
    BATCH_VERIFY: '/api/decisions/batch-verify',
  },
  
  // Verification endpoints
  VERIFICATION: {
    AUDIT_TRAIL: '/api/verification/audit-trail',
    TIMELINE: (address: string) => `/api/verification/wallet/${address}/timeline`,
    AGENT_ACTIVITY: (type: string) => `/api/verification/agent/${type}/activity`,
    AUTONOMY_STATS: '/api/verification/statistics/autonomy',
    VALIDATE_CHRONOLOGY: '/api/verification/validate-chronology',
    INTEGRITY_CHECK: (wallet: string) => `/api/verification/integrity-check/${wallet}`,
    EXPORT: (wallet: string) => `/api/verification/export/${wallet}`,
  },
  
  // External integration endpoints
  EXTERNAL: {
    API_PAYMENT: '/api/external/api-payment',
    API_PROVIDERS: '/api/external/api-providers',
    DATA_PURCHASE: '/api/external/data-purchase',
    ORACLE_DATA: '/api/external/oracle-data',
    REGISTER_SERVICE: '/api/external/services/register',
    DISCOVER_SERVICES: '/api/external/services/discover',
    GET_SERVICE: (id: string) => `/api/external/services/${id}`,
    AGENT_TRANSACTION: '/api/external/agent-transaction',
    AGENT_SERVICES: (address: string) => `/api/external/services/agent/${address}`,
    UPDATE_AVAILABILITY: (id: string) => `/api/external/services/${id}/availability`,
    DEREGISTER_SERVICE: (id: string) => `/api/external/services/${id}`,
  },
  
  // WebSocket endpoints
  WEBSOCKET: {
    GENERAL: '/ws',
    AGENTS: '/ws/agents',
    TRANSACTIONS: '/ws/transactions',
    DECISIONS: '/ws/decisions',
    VERIFICATION: '/ws/verification',
  },
};

export default apiClient;
