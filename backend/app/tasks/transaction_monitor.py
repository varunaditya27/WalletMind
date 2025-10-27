"""
Transaction Monitor - Background Transaction Status Monitoring

Monitors pending transactions and updates status:
- Check transaction confirmation status
- Detect failed transactions
- Trigger retries for recoverable failures
- Update WebSocket clients with status changes
- Store final results in memory
"""

from typing import Dict, Any, List, Optional, Set
import asyncio
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class TransactionStatus(str, Enum):
    """Transaction status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PendingTransaction:
    """Pending transaction tracking"""
    def __init__(
        self,
        tx_hash: str,
        wallet_address: str,
        network: str,
        submitted_at: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.tx_hash = tx_hash
        self.wallet_address = wallet_address
        self.network = network
        self.submitted_at = submitted_at
        self.status = TransactionStatus.SUBMITTED
        self.confirmations = 0
        self.checked_count = 0
        self.last_checked = submitted_at
        self.metadata = metadata or {}
        self.error: Optional[str] = None


class TransactionMonitor:
    """
    Background service for monitoring transaction status.
    
    Features:
    - Periodic status checks
    - Confirmation tracking
    - Failure detection
    - Retry triggering
    - WebSocket notifications
    - Memory storage
    """
    
    def __init__(
        self,
        blockchain_service: Any,
        memory_service: Optional[Any] = None,
        websocket_manager: Optional[Any] = None,
        check_interval: int = 10,
        max_confirmations: int = 3,
        timeout_minutes: int = 30
    ):
        """
        Initialize transaction monitor
        
        Args:
            blockchain_service: Blockchain service for status checks
            memory_service: Memory service for storing results
            websocket_manager: WebSocket manager for notifications
            check_interval: Seconds between checks
            max_confirmations: Confirmations needed
            timeout_minutes: Transaction timeout
        """
        self.blockchain_service = blockchain_service
        self.memory_service = memory_service
        self.websocket_manager = websocket_manager
        self.check_interval = check_interval
        self.max_confirmations = max_confirmations
        self.timeout = timedelta(minutes=timeout_minutes)
        
        # Pending transactions
        self.pending: Dict[str, PendingTransaction] = {}
        
        # Monitoring state
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        logger.info("Transaction monitor initialized")
    
    async def start(self):
        """Start monitoring loop"""
        if self.is_running:
            logger.warning("Monitor already running")
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Transaction monitor started")
    
    async def stop(self):
        """Stop monitoring loop"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Transaction monitor stopped")
    
    def add_transaction(
        self,
        tx_hash: str,
        wallet_address: str,
        network: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add transaction to monitoring
        
        Args:
            tx_hash: Transaction hash
            wallet_address: Wallet address
            network: Blockchain network
            metadata: Additional metadata
        """
        if tx_hash in self.pending:
            logger.warning(f"Transaction {tx_hash} already being monitored")
            return
        
        pending_tx = PendingTransaction(
            tx_hash=tx_hash,
            wallet_address=wallet_address,
            network=network,
            submitted_at=datetime.utcnow(),
            metadata=metadata
        )
        
        self.pending[tx_hash] = pending_tx
        logger.info(f"Added transaction {tx_hash} to monitoring")
    
    def remove_transaction(self, tx_hash: str) -> Optional[PendingTransaction]:
        """
        Remove transaction from monitoring
        
        Args:
            tx_hash: Transaction hash
        
        Returns:
            Removed transaction or None
        """
        return self.pending.pop(tx_hash, None)
    
    def get_status(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction status
        
        Args:
            tx_hash: Transaction hash
        
        Returns:
            Status information or None
        """
        pending_tx = self.pending.get(tx_hash)
        
        if not pending_tx:
            return None
        
        return {
            "tx_hash": tx_hash,
            "wallet_address": pending_tx.wallet_address,
            "network": pending_tx.network,
            "status": pending_tx.status.value,
            "confirmations": pending_tx.confirmations,
            "submitted_at": pending_tx.submitted_at.isoformat(),
            "checked_count": pending_tx.checked_count,
            "last_checked": pending_tx.last_checked.isoformat(),
            "error": pending_tx.error
        }
    
    def get_all_pending(
        self,
        wallet_address: Optional[str] = None,
        network: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all pending transactions with optional filters
        
        Args:
            wallet_address: Filter by wallet
            network: Filter by network
        
        Returns:
            List of pending transaction statuses
        """
        results = []
        
        for tx_hash, pending_tx in self.pending.items():
            if wallet_address and pending_tx.wallet_address != wallet_address:
                continue
            if network and pending_tx.network != network:
                continue
            
            status = self.get_status(tx_hash)
            if status:
                results.append(status)
        
        return results
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Monitoring loop started")
        
        while self.is_running:
            try:
                await self._check_all_transactions()
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Monitoring loop stopped")
    
    async def _check_all_transactions(self):
        """Check status of all pending transactions"""
        if not self.pending:
            return
        
        logger.debug(f"Checking {len(self.pending)} pending transactions")
        
        # Get list of tx hashes (avoid dict change during iteration)
        tx_hashes = list(self.pending.keys())
        
        for tx_hash in tx_hashes:
            try:
                await self._check_transaction(tx_hash)
            except Exception as e:
                logger.error(f"Error checking transaction {tx_hash}: {e}")
    
    async def _check_transaction(self, tx_hash: str):
        """
        Check single transaction status
        
        Args:
            tx_hash: Transaction hash
        """
        pending_tx = self.pending.get(tx_hash)
        
        if not pending_tx:
            return
        
        # Update check metadata
        pending_tx.checked_count += 1
        pending_tx.last_checked = datetime.utcnow()
        
        # Check for timeout
        if datetime.utcnow() - pending_tx.submitted_at > self.timeout:
            logger.warning(f"Transaction {tx_hash} timed out")
            await self._handle_timeout(pending_tx)
            return
        
        try:
            # Get transaction receipt
            receipt = await self.blockchain_service.get_transaction_receipt(
                tx_hash,
                pending_tx.network
            )
            
            if not receipt:
                # Still pending
                pending_tx.status = TransactionStatus.PENDING
                return
            
            # Transaction is mined
            status = receipt.get("status")
            block_number = receipt.get("blockNumber")
            
            if status == 1:
                # Success
                await self._handle_success(pending_tx, receipt)
            else:
                # Failed
                await self._handle_failure(pending_tx, receipt)
                
        except Exception as e:
            logger.error(f"Error checking transaction {tx_hash}: {e}")
            pending_tx.error = str(e)
    
    async def _handle_success(
        self,
        pending_tx: PendingTransaction,
        receipt: Dict[str, Any]
    ):
        """
        Handle successful transaction
        
        Args:
            pending_tx: Pending transaction
            receipt: Transaction receipt
        """
        # Get current block to calculate confirmations
        try:
            current_block = await self.blockchain_service.get_block_number(
                pending_tx.network
            )
            tx_block = receipt.get("blockNumber", 0)
            confirmations = current_block - tx_block + 1
            
            pending_tx.confirmations = confirmations
            
            if confirmations >= self.max_confirmations:
                pending_tx.status = TransactionStatus.CONFIRMED
                logger.info(
                    f"Transaction {pending_tx.tx_hash} confirmed "
                    f"with {confirmations} confirmations"
                )
                
                # Finalize
                await self._finalize_transaction(pending_tx, receipt, success=True)
            else:
                pending_tx.status = TransactionStatus.CONFIRMING
                logger.debug(
                    f"Transaction {pending_tx.tx_hash} has {confirmations} confirmations "
                    f"(need {self.max_confirmations})"
                )
                
                # Notify of confirmation progress
                await self._notify_status_change(pending_tx)
                
        except Exception as e:
            logger.error(f"Error handling success: {e}")
    
    async def _handle_failure(
        self,
        pending_tx: PendingTransaction,
        receipt: Dict[str, Any]
    ):
        """
        Handle failed transaction
        
        Args:
            pending_tx: Pending transaction
            receipt: Transaction receipt
        """
        pending_tx.status = TransactionStatus.FAILED
        pending_tx.error = "Transaction reverted on-chain"
        
        logger.warning(f"Transaction {pending_tx.tx_hash} failed")
        
        await self._finalize_transaction(pending_tx, receipt, success=False)
    
    async def _handle_timeout(self, pending_tx: PendingTransaction):
        """
        Handle transaction timeout
        
        Args:
            pending_tx: Pending transaction
        """
        pending_tx.status = TransactionStatus.FAILED
        pending_tx.error = f"Transaction timed out after {self.timeout.total_seconds() / 60} minutes"
        
        logger.warning(f"Transaction {pending_tx.tx_hash} timed out")
        
        await self._finalize_transaction(pending_tx, receipt=None, success=False)
    
    async def _finalize_transaction(
        self,
        pending_tx: PendingTransaction,
        receipt: Optional[Dict[str, Any]],
        success: bool
    ):
        """
        Finalize transaction monitoring
        
        Args:
            pending_tx: Pending transaction
            receipt: Transaction receipt (if available)
            success: Success status
        """
        # Store in memory
        if self.memory_service:
            try:
                await self.memory_service.store(
                    wallet_address=pending_tx.wallet_address,
                    agent_type="transaction_monitor",
                    request=f"Monitor transaction {pending_tx.tx_hash}",
                    response={
                        "tx_hash": pending_tx.tx_hash,
                        "status": pending_tx.status.value,
                        "confirmations": pending_tx.confirmations,
                        "success": success,
                        "receipt": receipt
                    },
                    reasoning=f"Transaction {'confirmed' if success else 'failed'} after {pending_tx.checked_count} checks",
                    timestamp=datetime.utcnow(),
                    metadata={
                        "network": pending_tx.network,
                        "submitted_at": pending_tx.submitted_at.isoformat(),
                        "finalized_at": datetime.utcnow().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to store in memory: {e}")
        
        # Notify via WebSocket
        await self._notify_status_change(pending_tx, final=True)
        
        # Remove from pending
        self.remove_transaction(pending_tx.tx_hash)
    
    async def _notify_status_change(
        self,
        pending_tx: PendingTransaction,
        final: bool = False
    ):
        """
        Notify WebSocket clients of status change
        
        Args:
            pending_tx: Pending transaction
            final: Whether this is final status
        """
        if not self.websocket_manager:
            return
        
        try:
            message = {
                "type": "transaction_update",
                "tx_hash": pending_tx.tx_hash,
                "wallet_address": pending_tx.wallet_address,
                "network": pending_tx.network,
                "status": pending_tx.status.value,
                "confirmations": pending_tx.confirmations,
                "final": final,
                "error": pending_tx.error,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Broadcast to transaction channel
            await self.websocket_manager.broadcast_transaction_event(message)
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics"""
        status_counts = {}
        for pending_tx in self.pending.values():
            status = pending_tx.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_pending": len(self.pending),
            "status_distribution": status_counts,
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "max_confirmations": self.max_confirmations,
            "timeout_minutes": self.timeout.total_seconds() / 60
        }


# Singleton instance
_transaction_monitor: Optional[TransactionMonitor] = None


def get_transaction_monitor(
    blockchain_service: Any,
    memory_service: Optional[Any] = None,
    websocket_manager: Optional[Any] = None
) -> TransactionMonitor:
    """Get or create singleton TransactionMonitor instance"""
    global _transaction_monitor
    
    if _transaction_monitor is None:
        _transaction_monitor = TransactionMonitor(
            blockchain_service=blockchain_service,
            memory_service=memory_service,
            websocket_manager=websocket_manager
        )
    
    return _transaction_monitor