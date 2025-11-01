'use client';

import { useState } from 'react';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface ApprovalModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  approvalData: {
    approval_id: string;
    request_id: string;
    user_request: string;
    plan?: {
      action: string;
      to_address?: string;
      amount?: number;
      risk_level: string;
      reasoning: string;
      estimated_gas?: number;
    };
    reason: string;
    wallet_address: string;
  };
  onApprove: (approvalId: string) => void;
  onReject: (approvalId: string) => void;
  loading?: boolean;
}

export function ApprovalModal({
  open,
  onOpenChange,
  approvalData,
  onApprove,
  onReject,
  loading = false,
}: ApprovalModalProps) {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApprove = async () => {
    setIsProcessing(true);
    try {
      await onApprove(approvalData.approval_id);
    } finally {
      setIsProcessing(false);
      onOpenChange(false);
    }
  };

  const handleReject = async () => {
    setIsProcessing(true);
    try {
      await onReject(approvalData.approval_id);
    } finally {
      setIsProcessing(false);
      onOpenChange(false);
    }
  };

  const riskColor = {
    low: 'text-green-500',
    medium: 'text-yellow-500',
    high: 'text-red-500',
  }[approvalData.plan?.risk_level || 'medium'];

  const riskBgColor = {
    low: 'bg-green-500/10 border-green-500/20',
    medium: 'bg-yellow-500/10 border-yellow-500/20',
    high: 'bg-red-500/10 border-red-500/20',
  }[approvalData.plan?.risk_level || 'medium'];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] bg-background border-border">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className={cn('p-2 rounded-lg', riskBgColor)}>
              <AlertTriangle className={cn('h-5 w-5', riskColor)} />
            </div>
            <div>
              <DialogTitle className="text-xl">Manual Approval Required</DialogTitle>
              <DialogDescription className="text-muted">
                This transaction requires your review and approval
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* User Request */}
          <div>
            <label className="text-xs font-medium text-muted uppercase tracking-wider">
              Original Request
            </label>
            <p className="mt-1 text-sm text-foreground bg-accent/30 px-3 py-2 rounded-md">
              {approvalData.user_request}
            </p>
          </div>

          {/* Transaction Details */}
          {approvalData.plan && (
            <div className="space-y-3">
              <label className="text-xs font-medium text-muted uppercase tracking-wider">
                Transaction Details
              </label>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-accent/20 px-3 py-2 rounded-md">
                  <div className="text-xs text-muted">Action</div>
                  <div className="text-sm font-medium">{approvalData.plan.action}</div>
                </div>

                {approvalData.plan.amount !== undefined && (
                  <div className="bg-accent/20 px-3 py-2 rounded-md">
                    <div className="text-xs text-muted">Amount</div>
                    <div className="text-sm font-medium">{approvalData.plan.amount} ETH</div>
                  </div>
                )}

                {approvalData.plan.to_address && (
                  <div className="col-span-2 bg-accent/20 px-3 py-2 rounded-md">
                    <div className="text-xs text-muted">Recipient</div>
                    <div className="text-sm font-mono truncate">
                      {approvalData.plan.to_address}
                    </div>
                  </div>
                )}

                <div className="bg-accent/20 px-3 py-2 rounded-md">
                  <div className="text-xs text-muted">Risk Level</div>
                  <Badge variant="outline" className={cn('mt-1', riskBgColor, riskColor)}>
                    {approvalData.plan.risk_level.toUpperCase()}
                  </Badge>
                </div>

                {approvalData.plan.estimated_gas !== undefined && (
                  <div className="bg-accent/20 px-3 py-2 rounded-md">
                    <div className="text-xs text-muted">Estimated Gas</div>
                    <div className="text-sm font-medium">
                      {approvalData.plan.estimated_gas.toFixed(6)} ETH
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Risk Analysis */}
          <div>
            <label className="text-xs font-medium text-muted uppercase tracking-wider">
              Risk Analysis
            </label>
            <div className={cn('mt-1 text-sm px-3 py-2 rounded-md border', riskBgColor)}>
              <p className="text-foreground">{approvalData.reason}</p>
              {approvalData.plan?.reasoning && (
                <p className="mt-2 text-muted text-xs">{approvalData.plan.reasoning}</p>
              )}
            </div>
          </div>

          {/* Warning Notice */}
          <div className="bg-yellow-500/10 border border-yellow-500/20 px-4 py-3 rounded-md">
            <p className="text-sm text-yellow-200">
              ⚠️ Please carefully review the transaction details before approving. This action
              cannot be undone once executed.
            </p>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={handleReject}
            disabled={isProcessing || loading}
            className="gap-2"
          >
            <XCircle className="h-4 w-4" />
            Reject
          </Button>
          <Button
            onClick={handleApprove}
            disabled={isProcessing || loading}
            className="gap-2 bg-primary hover:bg-primary/90"
          >
            <CheckCircle className="h-4 w-4" />
            {isProcessing ? 'Processing...' : 'Approve & Execute'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
