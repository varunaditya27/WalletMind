'use client';

import { AlertCircle, AlertTriangle, CheckCircle, TrendingUp, X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type ErrorType = 
  | 'insufficient_funds'
  | 'network_congestion'
  | 'gas_spike'
  | 'transaction_failed'
  | 'high_risk'
  | 'clarification_needed'
  | 'generic';

interface ErrorNotificationProps {
  type: ErrorType;
  message: string;
  details?: {
    required?: number;
    available?: number;
    deficit?: number;
    gasPrice?: number;
    error?: string;
  };
  onDismiss?: () => void;
  actionLabel?: string;
  onAction?: () => void;
}

export function ErrorNotification({
  type,
  message,
  details,
  onDismiss,
  actionLabel,
  onAction,
}: ErrorNotificationProps) {
  const config = {
    insufficient_funds: {
      icon: AlertCircle,
      color: 'text-red-500',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/20',
      title: 'Insufficient Funds',
    },
    network_congestion: {
      icon: TrendingUp,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10',
      borderColor: 'border-yellow-500/20',
      title: 'Network Congestion',
    },
    gas_spike: {
      icon: TrendingUp,
      color: 'text-orange-500',
      bgColor: 'bg-orange-500/10',
      borderColor: 'border-orange-500/20',
      title: 'High Gas Prices',
    },
    transaction_failed: {
      icon: AlertCircle,
      color: 'text-red-500',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/20',
      title: 'Transaction Failed',
    },
    high_risk: {
      icon: AlertTriangle,
      color: 'text-orange-500',
      bgColor: 'bg-orange-500/10',
      borderColor: 'border-orange-500/20',
      title: 'High-Risk Transaction',
    },
    clarification_needed: {
      icon: AlertTriangle,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/20',
      title: 'Clarification Needed',
    },
    generic: {
      icon: AlertCircle,
      color: 'text-muted',
      bgColor: 'bg-accent/20',
      borderColor: 'border-border',
      title: 'Notice',
    },
  }[type];

  const Icon = config.icon;

  return (
    <div
      className={cn(
        'relative rounded-lg border p-4',
        config.bgColor,
        config.borderColor,
        'animate-in slide-in-from-top-2 duration-300'
      )}
    >
      {onDismiss && (
        <Button
          variant="ghost"
          size="sm"
          className="absolute top-2 right-2 h-6 w-6 p-0 hover:bg-background/50"
          onClick={onDismiss}
        >
          <X className="h-4 w-4" />
        </Button>
      )}

      <div className="flex items-start gap-3 pr-8">
        <div className={cn('p-1 rounded', config.bgColor)}>
          <Icon className={cn('h-5 w-5', config.color)} />
        </div>

        <div className="flex-1 space-y-2">
          <div>
            <h4 className={cn('font-semibold text-sm', config.color)}>{config.title}</h4>
            <p className="text-sm text-foreground mt-1">{message}</p>
          </div>

          {/* Details for insufficient funds */}
          {type === 'insufficient_funds' && details && (
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="bg-background/50 px-2 py-1 rounded">
                <div className="text-muted">Required</div>
                <div className="font-medium">{details.required?.toFixed(6)} ETH</div>
              </div>
              <div className="bg-background/50 px-2 py-1 rounded">
                <div className="text-muted">Available</div>
                <div className="font-medium">{details.available?.toFixed(6)} ETH</div>
              </div>
              <div className="bg-background/50 px-2 py-1 rounded">
                <div className="text-muted">Deficit</div>
                <div className="font-medium text-red-400">
                  -{details.deficit?.toFixed(6)} ETH
                </div>
              </div>
            </div>
          )}

          {/* Details for gas spike */}
          {type === 'gas_spike' && details?.gasPrice && (
            <div className="bg-background/50 px-3 py-2 rounded text-xs">
              <span className="text-muted">Current gas price: </span>
              <span className="font-medium">{details.gasPrice} gwei</span>
            </div>
          )}

          {/* Details for transaction failed */}
          {type === 'transaction_failed' && details?.error && (
            <div className="bg-background/50 px-3 py-2 rounded text-xs font-mono">
              {details.error}
            </div>
          )}

          {/* Action button */}
          {actionLabel && onAction && (
            <Button
              size="sm"
              variant="outline"
              onClick={onAction}
              className="mt-2 text-xs"
            >
              {actionLabel}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

interface NetworkStatusProps {
  network: string;
  gasPrice?: number;
  congestion?: 'low' | 'medium' | 'high';
  blockTime?: number;
}

export function NetworkStatus({ network, gasPrice, congestion = 'low', blockTime }: NetworkStatusProps) {
  const congestionConfig = {
    low: {
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      label: 'Normal',
    },
    medium: {
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10',
      label: 'Moderate',
    },
    high: {
      color: 'text-red-500',
      bgColor: 'bg-red-500/10',
      label: 'High',
    },
  }[congestion];

  return (
    <div className="flex items-center gap-4 text-xs">
      <div className="flex items-center gap-2">
        <span className="text-muted">Network:</span>
        <Badge variant="outline" className="capitalize">
          {network}
        </Badge>
      </div>

      {gasPrice !== undefined && (
        <div className="flex items-center gap-2">
          <span className="text-muted">Gas:</span>
          <span className="font-mono">{gasPrice} gwei</span>
        </div>
      )}

      <div className="flex items-center gap-2">
        <span className="text-muted">Congestion:</span>
        <div className={cn('flex items-center gap-1 px-2 py-0.5 rounded', congestionConfig.bgColor)}>
          <div className={cn('h-1.5 w-1.5 rounded-full', congestionConfig.color)} />
          <span className={congestionConfig.color}>{congestionConfig.label}</span>
        </div>
      </div>

      {blockTime && (
        <div className="flex items-center gap-2">
          <span className="text-muted">Block time:</span>
          <span>{blockTime}s</span>
        </div>
      )}
    </div>
  );
}
