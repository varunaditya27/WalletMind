"""
Agent repository for agent management (FR-003, FR-012)

Handles agent CRUD operations, status management, and performance tracking.
"""

import logging
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from prisma import Prisma

from .base_repository import BaseRepository, PaginatedResult

logger = logging.getLogger(__name__)


class AgentRepository(BaseRepository):
    """
    Agent repository with performance tracking.
    
    Features:
    - Agent registration and management
    - Status and reputation tracking
    - Performance metrics
    - Service offering management
    """
    
    def __init__(self, db: Prisma):
        super().__init__(db, "agent")
    
    async def create_agent(
        self,
        wallet_id: str,
        name: str,
        agent_type: str,
        metadata: Optional[dict] = None,
        spending_limit: int = 0,
        daily_spending_limit: int = 0,
        is_autonomous: bool = False
    ):
        """
        Create new agent.
        
        Args:
            wallet_id: Associated wallet ID
            name: Agent name
            agent_type: Agent type (PLANNER, EXECUTOR, etc.)
            metadata: Agent capabilities and configuration
            spending_limit: Total spending limit in wei
            daily_spending_limit: Daily spending limit in wei
            is_autonomous: Whether agent can operate autonomously
            
        Returns:
            Created agent
        """
        agent = await self.create({
            "walletId": wallet_id,
            "name": name,
            "agentType": agent_type,
            "metadata": metadata or {},
            "spendingLimit": Decimal(spending_limit),
            "dailySpendingLimit": Decimal(daily_spending_limit),
            "isAutonomous": is_autonomous
        })
        
        logger.info(f"Agent created: {name} ({agent_type})")
        
        return agent
    
    async def find_by_wallet(self, wallet_id: str) -> List:
        """Find all agents for wallet"""
        return await self.find_many(
            where={"walletId": wallet_id},
            order_by={"createdAt": "desc"}
        )
    
    async def find_by_type(
        self,
        agent_type: str,
        status: Optional[str] = "ACTIVE"
    ) -> List:
        """
        Find agents by type.
        
        Args:
            agent_type: Agent type
            status: Filter by status
            
        Returns:
            List of agents
        """
        where = {"agentType": agent_type}
        if status:
            where["status"] = status
        
        return await self.find_many(
            where=where,
            order_by={"reputation": "desc"}
        )
    
    async def update_status(
        self,
        agent_id: str,
        new_status: str
    ):
        """
        Update agent status.
        
        Args:
            agent_id: Agent ID
            new_status: New status (ACTIVE, INACTIVE, PAUSED, etc.)
            
        Returns:
            Updated agent
        """
        return await self.update(agent_id, {
            "status": new_status,
            "updatedAt": datetime.utcnow(),
            "lastActiveAt": datetime.utcnow() if new_status == "ACTIVE" else None
        })
    
    async def update_reputation(
        self,
        agent_id: str,
        change: int
    ):
        """
        Update agent reputation.
        
        Args:
            agent_id: Agent ID
            change: Reputation change (positive or negative)
            
        Returns:
            Updated agent
        """
        agent = await self.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        new_reputation = max(0, agent.reputation + change)
        
        return await self.update(agent_id, {
            "reputation": new_reputation,
            "updatedAt": datetime.utcnow()
        })
    
    async def increment_transaction_count(
        self,
        agent_id: str,
        successful: bool = True
    ):
        """
        Increment agent transaction counters.
        
        Args:
            agent_id: Agent ID
            successful: Whether transaction was successful
            
        Returns:
            Updated agent
        """
        agent = await self.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        update_data = {
            "totalTransactions": agent.totalTransactions + 1,
            "updatedAt": datetime.utcnow()
        }
        
        if successful:
            update_data["successfulTxCount"] = agent.successfulTxCount + 1
        
        return await self.update(agent_id, update_data)
    
    async def update_spending_limit(
        self,
        agent_id: str,
        spending_limit: int,
        daily_limit: Optional[int] = None
    ):
        """
        Update agent spending limits.
        
        Args:
            agent_id: Agent ID
            spending_limit: Total spending limit in wei
            daily_limit: Daily spending limit in wei
            
        Returns:
            Updated agent
        """
        update_data = {
            "spendingLimit": Decimal(spending_limit),
            "updatedAt": datetime.utcnow()
        }
        
        if daily_limit is not None:
            update_data["dailySpendingLimit"] = Decimal(daily_limit)
        
        return await self.update(agent_id, update_data)
    
    async def mark_registered_on_chain(
        self,
        agent_id: str,
        on_chain_address: str
    ):
        """
        Mark agent as registered on blockchain.
        
        Args:
            agent_id: Agent ID
            on_chain_address: AgentRegistry contract address
            
        Returns:
            Updated agent
        """
        return await self.update(agent_id, {
            "registeredOnChain": True,
            "onChainAddress": on_chain_address,
            "updatedAt": datetime.utcnow()
        })
    
    async def get_agent_performance(self, agent_id: str) -> dict:
        """
        Get agent performance metrics.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Performance metrics dictionary
        """
        agent = await self.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # Calculate success rate
        success_rate = 0
        if agent.totalTransactions > 0:
            success_rate = (agent.successfulTxCount / agent.totalTransactions) * 100
        
        # Count decisions
        decision_count = await self.db.decision.count(where={"agentId": agent_id})
        executed_decisions = await self.db.decision.count(
            where={
                "agentId": agent_id,
                "status": "EXECUTED"
            }
        )
        
        return {
            "agent_id": agent_id,
            "name": agent.name,
            "type": agent.agentType,
            "status": agent.status,
            "reputation": agent.reputation,
            "total_transactions": agent.totalTransactions,
            "successful_transactions": agent.successfulTxCount,
            "success_rate": round(success_rate, 2),
            "decision_count": decision_count,
            "executed_decisions": executed_decisions,
            "spending_limit": str(agent.spendingLimit),
            "daily_spending_limit": str(agent.dailySpendingLimit),
            "is_autonomous": agent.isAutonomous,
            "registered_on_chain": agent.registeredOnChain,
            "created_at": agent.createdAt,
            "last_active_at": agent.lastActiveAt
        }
    
    async def get_active_agents(
        self,
        agent_type: Optional[str] = None
    ) -> List:
        """
        Get all active agents.
        
        Args:
            agent_type: Filter by agent type
            
        Returns:
            List of active agents
        """
        where = {"status": "ACTIVE"}
        if agent_type:
            where["agentType"] = agent_type
        
        return await self.find_many(
            where=where,
            order_by={"reputation": "desc"}
        )
    
    async def get_top_performers(
        self,
        limit: int = 10,
        agent_type: Optional[str] = None
    ) -> List:
        """
        Get top performing agents by reputation.
        
        Args:
            limit: Number of agents to return
            agent_type: Filter by agent type
            
        Returns:
            List of top agents
        """
        where = {"status": "ACTIVE"}
        if agent_type:
            where["agentType"] = agent_type
        
        return await self.find_many(
            where=where,
            take=limit,
            order_by={"reputation": "desc"}
        )
    
    # ========== Service Offering Management ==========
    
    async def create_service(
        self,
        agent_id: str,
        service_id: str,
        name: str,
        description: str,
        price: int,  # Wei
        metadata: Optional[dict] = None
    ):
        """
        Create service offering for agent.
        
        Args:
            agent_id: Agent ID
            service_id: Unique service identifier
            name: Service name
            description: Service description
            price: Service price in wei
            metadata: Additional service details
            
        Returns:
            Created service offering
        """
        service = await self.db.serviceoffering.create(data={
            "agentId": agent_id,
            "serviceId": service_id,
            "name": name,
            "description": description,
            "price": Decimal(price),
            "metadata": metadata or {}
        })
        
        logger.info(f"Service created: {name} for agent {agent_id}")
        
        return service
    
    async def get_agent_services(
        self,
        agent_id: str,
        is_available: Optional[bool] = True
    ) -> List:
        """
        Get all services offered by agent.
        
        Args:
            agent_id: Agent ID
            is_available: Filter by availability
            
        Returns:
            List of service offerings
        """
        where = {"agentId": agent_id}
        if is_available is not None:
            where["isAvailable"] = is_available
        
        return await self.db.serviceoffering.find_many(
            where=where,
            order={"createdAt": "desc"}
        )
    
    async def update_service_availability(
        self,
        service_id: str,
        is_available: bool
    ):
        """Update service availability status"""
        return await self.db.serviceoffering.update(
            where={"serviceId": service_id},
            data={
                "isAvailable": is_available,
                "updatedAt": datetime.utcnow()
            }
        )
