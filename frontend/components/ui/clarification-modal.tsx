'use client';

import { useState } from 'react';
import { HelpCircle, Send } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

interface ClarificationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clarificationData: {
    clarification_id: string;
    request_id: string;
    question: string;
    original_request: string;
  };
  onSubmit: (clarificationId: string, answer: string) => void;
  loading?: boolean;
}

export function ClarificationModal({
  open,
  onOpenChange,
  clarificationData,
  onSubmit,
  loading = false,
}: ClarificationModalProps) {
  const [answer, setAnswer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!answer.trim()) return;
    
    setIsSubmitting(true);
    try {
      await onSubmit(clarificationData.clarification_id, answer);
      setAnswer('');
    } finally {
      setIsSubmitting(false);
      onOpenChange(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px] bg-background border-border">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <HelpCircle className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <DialogTitle className="text-xl">Clarification Needed</DialogTitle>
              <DialogDescription className="text-muted">
                Please provide additional information
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Original Request */}
          <div>
            <label className="text-xs font-medium text-muted uppercase tracking-wider">
              Your Original Request
            </label>
            <p className="mt-1 text-sm text-muted-foreground bg-accent/20 px-3 py-2 rounded-md italic">
              "{clarificationData.original_request}"
            </p>
          </div>

          {/* Clarification Question */}
          <div>
            <label className="text-xs font-medium text-muted uppercase tracking-wider">
              Agent's Question
            </label>
            <div className="mt-1 bg-blue-500/10 border border-blue-500/20 px-4 py-3 rounded-md">
              <p className="text-sm text-foreground">{clarificationData.question}</p>
            </div>
          </div>

          {/* Answer Input */}
          <div>
            <label className="text-xs font-medium text-muted uppercase tracking-wider">
              Your Answer
            </label>
            <Textarea
              value={answer}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setAnswer(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your answer here... (Press Enter to submit)"
              className="mt-1 min-h-[100px] resize-none bg-background border-border"
              disabled={isSubmitting || loading}
            />
            <p className="mt-1 text-xs text-muted">
              Tip: Be as specific as possible to help the agent process your request.
            </p>
          </div>

          {/* Examples (Optional) */}
          {clarificationData.question.toLowerCase().includes('address') && (
            <div className="bg-accent/20 px-3 py-2 rounded-md text-xs">
              <div className="font-medium text-muted mb-1">Example format:</div>
              <code className="text-primary">0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb</code>
              <span className="text-muted"> or </span>
              <code className="text-primary">vitalik.eth</code>
            </div>
          )}

          {clarificationData.question.toLowerCase().includes('amount') && (
            <div className="bg-accent/20 px-3 py-2 rounded-md text-xs">
              <div className="font-medium text-muted mb-1">Example format:</div>
              <code className="text-primary">0.1 ETH</code>
              <span className="text-muted"> or </span>
              <code className="text-primary">100 USDC</code>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={() => {
              setAnswer('');
              onOpenChange(false);
            }}
            disabled={isSubmitting || loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || loading || !answer.trim()}
            className="gap-2 bg-primary hover:bg-primary/90"
          >
            <Send className="h-4 w-4" />
            {isSubmitting ? 'Submitting...' : 'Submit Answer'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
