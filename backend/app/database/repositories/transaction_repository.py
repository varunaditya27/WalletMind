"""
Transaction repository for transaction management (FR-005)

Handles transaction CRUD operations, status tracking, and analytics.
"""

import logging
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
from prisma import Prisma

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TransactionRepository(BaseRepository):
    """Transaction repository with status tracking and analytics"""
    
    def __init__(self, db: Prisma):
        super().__init__(db, "transaction")
    
    async def create_transaction(
        self,
        wallet_id: str,
        from_address: str,
        to_address: Optional[str],
        value: int,  # Wei
        network: str,
        tx_type: str,
        decision_id: Optional[str] = None,
        contract_address: Optional[str] = None,
        function_name: Optional[str] = None,
        nonce: Optional[int] = None
    ):
        """Create new transaction record"""
        return await self.create({
            "walletId": wallet_id,
            "decisionId": decision_id,
            "from": from_address,
            "to": to_address,
            "value": Decimal(value),
            "network": network,
            "txType": tx_type,
            "contractAddress": contract_address,
            "functionName": function_name,
            "nonce": nonce,
            "status": "PENDING"
        })
    
    async def update_status(
        self,
        tx_id: str,
        status: str,
        tx_hash: Optional[str] = None,
        block_number: Optional[int] = None,
        gas_used: Optional[int] = None,
        effective_gas_price: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Update transaction status with blockchain data"""
        update_data = {
            "status": status,
            "updatedAt": datetime.utcnow()
        }
        
        if tx_hash:
            update_data["txHash"] = tx_hash
        if block_number:
            update_data["blockNumber"] = block_number
        if gas_used:
            update_data["gasUsed"] = Decimal(gas_used)
        if effective_gas_price:
            update_data["effectiveGasPrice"] = Decimal(effective_gas_price)
        if error:
            update_data["error"] = error
        if status == "CONFIRMED":
            update_data["confirmedAt"] = datetime.utcnow()
        
        return await self.update(tx_id, update_data)
    
    async def increment_retry_count(self, tx_id: str):
        """Increment transaction retry counter"""
        tx = await self.find_by_id(tx_id)
        if not tx:
            raise ValueError(f"Transaction not found: {tx_id}")
        
        return await self.update(tx_id, {
            "retryCount": tx.retryCount + 1,
            "updatedAt": datetime.utcnow()
        })
    
    async def find_by_tx_hash(self, tx_hash: str):
        """Find transaction by blockchain hash"""
        return await self._model.find_unique(where={"txHash": tx_hash})
    
    async def find_by_wallet(
        self,
        wallet_id: str,
        status: Optional[str] = None,
        tx_type: Optional[str] = None,
        limit: int = 50
    ) -> List:
        """Find transactions for wallet"""
        where = {"walletId": wallet_id}
        if status:
            where["status"] = status
        if tx_type:
            where["txType"] = tx_type
        
        return await self.find_many(
            where=where,
            take=limit,
            order_by={"createdAt": "desc"}
        )
    
    async def find_by_decision(self, decision_id: str) -> List:
        """Find all transactions for decision"""
        return await self.find_many(
            where={"decisionId": decision_id},
            order_by={"createdAt": "asc"}
        )
    
    async def get_pending_transactions(
        self,
        network: Optional[str] = None
    ) -> List:
        """Get all pending transactions"""
        where = {"status": "PENDING"}
        if network:
            where["network"] = network
        
        return await self.find_many(
            where=where,
            order_by={"createdAt": "asc"}
        )
    
    async def get_transaction_stats(
        self,
        wallet_id: Optional[str] = None,
        days: int = 30
    ) -> dict:
        """Get transaction statistics"""
        since = datetime.utcnow() - timedelta(days=days)
        
        where = {"createdAt": {"gte": since}}
        if wallet_id:
            where["walletId"] = wallet_id
        
        total = await self.count(where=where)
        confirmed = await self.count(where={**where, "status": "CONFIRMED"})
        failed = await self.count(where={**where, "status": "FAILED"})
        pending = await self.count(where={**where, "status": "PENDING"})
        
        return {
            "total": total,
            "confirmed": confirmed,
            "failed": failed,
            "pending": pending,
            "success_rate": (confirmed / total * 100) if total > 0 else 0,
            "period_days": days
        }
