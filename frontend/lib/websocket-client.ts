/**
 * WebSocket Client
 * Handles real-time connections to the backend
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import type {
  WebSocketMessage,
  AgentEvent,
  TransactionEvent,
  DecisionEvent,
  VerificationEvent,
} from '@/lib/api-types';
import { WebSocketMessageType } from '@/lib/api-types';

const WS_BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws') || 'ws://localhost:8000';

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers = new Map<WebSocketMessageType, Set<(data: any) => void>>();
  private isIntentionallyClosed = false;

  constructor(private endpoint: string) {}

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    this.isIntentionallyClosed = false;
    const url = `${WS_BASE_URL}${this.endpoint}`;
    
    console.log('[WebSocket] Connecting to:', url);
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('[WebSocket] Connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
    };

    this.ws.onclose = (event) => {
      console.log('[WebSocket] Closed:', event.code, event.reason);
      this.ws = null;

      // Attempt to reconnect unless intentionally closed
      if (!this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`[WebSocket] Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        
        setTimeout(() => {
          this.connect();
        }, this.reconnectDelay);

        // Exponential backoff
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
      }
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message.data);
        } catch (error) {
          console.error('[WebSocket] Handler error:', error);
        }
      });
    }
  }

  on(messageType: WebSocketMessageType, handler: (data: any) => void): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, new Set());
    }
    this.messageHandlers.get(messageType)!.add(handler);
  }

  off(messageType: WebSocketMessageType, handler: (data: any) => void): void {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('[WebSocket] Cannot send - not connected');
    }
  }

  disconnect(): void {
    this.isIntentionallyClosed = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// ============= React Hooks =============

/**
 * Hook to connect to a WebSocket endpoint
 */
export function useWebSocket(endpoint: string) {
  const clientRef = useRef<WebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Create client
    clientRef.current = new WebSocketClient(endpoint);
    
    // Connect
    clientRef.current.connect();

    // Check connection status
    const checkConnection = setInterval(() => {
      setIsConnected(clientRef.current?.isConnected() ?? false);
    }, 1000);

    // Cleanup
    return () => {
      clearInterval(checkConnection);
      clientRef.current?.disconnect();
      clientRef.current = null;
    };
  }, [endpoint]);

  const send = useCallback((data: any) => {
    clientRef.current?.send(data);
  }, []);

  return { client: clientRef.current, isConnected, send };
}

/**
 * Hook to listen for specific WebSocket message types
 */
export function useWebSocketMessage<T = any>(
  messageType: WebSocketMessageType,
  handler: (data: T) => void,
  endpoint: string = '/ws'
) {
  const { client, isConnected } = useWebSocket(endpoint);

  useEffect(() => {
    if (client) {
      client.on(messageType, handler);
      return () => {
        client.off(messageType, handler);
      };
    }
  }, [client, messageType, handler]);

  return { isConnected };
}

/**
 * Hook for agent events
 */
export function useAgentEvents(handler: (event: AgentEvent) => void) {
  return useWebSocketMessage<AgentEvent>(WebSocketMessageType.AGENT_EVENT, handler, '/ws/agents');
}

/**
 * Hook for transaction events
 */
export function useTransactionEvents(handler: (event: TransactionEvent) => void) {
  return useWebSocketMessage<TransactionEvent>(WebSocketMessageType.TRANSACTION_EVENT, handler, '/ws/transactions');
}

/**
 * Hook for decision events
 */
export function useDecisionEvents(handler: (event: DecisionEvent) => void) {
  return useWebSocketMessage<DecisionEvent>(WebSocketMessageType.DECISION_EVENT, handler, '/ws/decisions');
}

/**
 * Hook for verification events
 */
export function useVerificationEvents(handler: (event: VerificationEvent) => void) {
  return useWebSocketMessage<VerificationEvent>(WebSocketMessageType.VERIFICATION_EVENT, handler, '/ws/verification');
}
