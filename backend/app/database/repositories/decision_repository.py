"""
Decision repository for decision logging (FR-007, NFR-006)

Handles decision CRUD operations and execution tracking.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from prisma import Prisma

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DecisionRepository(BaseRepository):
    """Decision repository with execution tracking"""
    
    def __init__(self, db: Prisma):
        super().__init__(db, "decision")
    
    async def create_decision(
        self,
        agent_id: str,
        decision_hash: str,
        reasoning: str,
        action: str,
        parameters: dict,
        confidence: int,
        context: Optional[dict] = None,
        ipfs_hash: Optional[str] = None
    ):
        """Create new decision record"""
        return await self.create({
            "agentId": agent_id,
            "decisionHash": decision_hash,
            "reasoning": reasoning,
            "action": action,
            "parameters": parameters,
            "confidence": confidence,
            "context": context or {},
            "ipfsHash": ipfs_hash,
            "status": "PENDING"
        })
    
    async def update_status(
        self,
        decision_id: str,
        status: str,
        on_chain_tx_hash: Optional[str] = None
    ):
        """Update decision status"""
        update_data = {
            "status": status,
        }
        
        if on_chain_tx_hash:
            update_data["onChainTxHash"] = on_chain_tx_hash
        if status == "EXECUTED":
            update_data["executedAt"] = datetime.utcnow()
        
        return await self.update(decision_id, update_data)
    
    async def find_by_hash(self, decision_hash: str):
        """Find decision by hash"""
        return await self._model.find_unique(where={"decisionHash": decision_hash})
    
    async def find_by_agent(
        self,
        agent_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List:
        """Find decisions for agent"""
        where = {"agentId": agent_id}
        if status:
            where["status"] = status
        
        return await self.find_many(
            where=where,
            take=limit,
            order_by={"createdAt": "desc"}
        )
    
    async def get_pending_decisions(self, agent_id: Optional[str] = None) -> List:
        """Get pending decisions"""
        where = {"status": "PENDING"}
        if agent_id:
            where["agentId"] = agent_id
        
        return await self.find_many(
            where=where,
            order_by={"createdAt": "asc"}
        )
    
    async def get_decision_stats(
        self,
        agent_id: Optional[str] = None,
        days: int = 30
    ) -> dict:
        """Get decision statistics"""
        since = datetime.utcnow() - timedelta(days=days)
        
        where = {"createdAt": {"gte": since}}
        if agent_id:
            where["agentId"] = agent_id
        
        total = await self.count(where=where)
        executed = await self.count(where={**where, "status": "EXECUTED"})
        failed = await self.count(where={**where, "status": "FAILED"})
        pending = await self.count(where={**where, "status": "PENDING"})
        
        return {
            "total": total,
            "executed": executed,
            "failed": failed,
            "pending": pending,
            "execution_rate": (executed / total * 100) if total > 0 else 0,
            "period_days": days
        }
