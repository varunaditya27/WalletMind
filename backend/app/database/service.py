"""
Database service layer - High-level business logic

Provides transaction management and cross-repository operations.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from .connection import get_db, close_db
from .repositories import (
    UserRepository,
    WalletRepository,
    AgentRepository,
    TransactionRepository,
    DecisionRepository,
    AuditRepository
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    High-level database service with business logic.
    
    Coordinates multiple repositories for complex operations.
    """
    
    def __init__(self):
        """Initialize service (repositories created on demand)"""
        self._db = None
        self._user_repo = None
        self._wallet_repo = None
        self._agent_repo = None
        self._transaction_repo = None
        self._decision_repo = None
        self._audit_repo = None
    
    async def _get_db(self):
        """Get database connection"""
        if self._db is None:
            self._db = await get_db()
        return self._db

    # --- Compatibility helpers ---
    async def connect(self):
        """Compatibility: ensure prisma client is connected and available as `prisma`."""
        await self._get_db()
        return self._db

    async def disconnect(self):
        """Compatibility: disconnect the prisma client (delegates to connection.close_db)."""
        try:
            if self._db is not None:
                await close_db()
        finally:
            self._db = None

    @property
    def prisma(self):
        """Expose the underlying Prisma client (requires connect() called first)."""
        if self._db is None:
            raise RuntimeError("Prisma client not initialized. Call 'await DatabaseService.connect()' first.")
        return self._db
    
    @property
    async def users(self) -> UserRepository:
        """Get user repository"""
        if self._user_repo is None:
            db = await self._get_db()
            self._user_repo = UserRepository(db)
        return self._user_repo
    
    @property
    async def wallets(self) -> WalletRepository:
        """Get wallet repository"""
        if self._wallet_repo is None:
            db = await self._get_db()
            self._wallet_repo = WalletRepository(db)
        return self._wallet_repo
    
    @property
    async def agents(self) -> AgentRepository:
        """Get agent repository"""
        if self._agent_repo is None:
            db = await self._get_db()
            self._agent_repo = AgentRepository(db)
        return self._agent_repo
    
    @property
    async def transactions(self) -> TransactionRepository:
        """Get transaction repository"""
        if self._transaction_repo is None:
            db = await self._get_db()
            self._transaction_repo = TransactionRepository(db)
        return self._transaction_repo
    
    @property
    async def decisions(self) -> DecisionRepository:
        """Get decision repository"""
        if self._decision_repo is None:
            db = await self._get_db()
            self._decision_repo = DecisionRepository(db)
        return self._decision_repo
    
    @property
    async def audit(self) -> AuditRepository:
        """Get audit repository"""
        if self._audit_repo is None:
            db = await self._get_db()
            self._audit_repo = AuditRepository(db)
        return self._audit_repo
    
    # ========== High-Level Operations ==========
    
    async def create_user_with_wallet(
        self,
        email: str,
        username: str,
        password: str,
        wallet_address: str,
        network: str = "SEPOLIA",
        wallet_type: str = "SMART_CONTRACT",
        encrypted_key: Optional[str] = None,
        mnemonic_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create user and associated wallet in single operation.
        
        Args:
            email: User email
            username: Unique username
            password: User password
            wallet_address: Wallet address
            network: Blockchain network
            wallet_type: Wallet type
            encrypted_key: Encrypted private key
            mnemonic_id: KeyManager mnemonic ID
            
        Returns:
            Dict with user and wallet objects
        """
        try:
            # Create user
            user_repo = await self.users
            user = await user_repo.create_user(
                email=email,
                username=username,
                password=password
            )
            
            # Create wallet
            wallet_repo = await self.wallets
            wallet = await wallet_repo.create_wallet(
                user_id=user.id,
                address=wallet_address,
                wallet_type=wallet_type,
                network=network,
                encrypted_key=encrypted_key,
                mnemonic_id=mnemonic_id
            )
            
            # Audit log
            audit_repo = await self.audit
            await audit_repo.log_action(
                action="USER_REGISTER",
                resource="user",
                user_id=user.id,
                resource_id=user.id,
                details={"wallet_id": wallet.id, "network": network}
            )
            
            logger.info(f"User created with wallet: {email} ({wallet_address})")
            
            return {
                "user": user,
                "wallet": wallet
            }
        
        except Exception as e:
            logger.error(f"Error creating user with wallet: {e}")
            raise
    
    async def create_agent_for_wallet(
        self,
        wallet_id: str,
        name: str,
        agent_type: str,
        user_id: str,
        metadata: Optional[dict] = None,
        spending_limit: int = 0,
        is_autonomous: bool = False
    ) -> Dict[str, Any]:
        """
        Create agent for existing wallet with validation.
        
        Args:
            wallet_id: Wallet ID
            name: Agent name
            agent_type: Agent type
            user_id: User ID (for audit)
            metadata: Agent metadata
            spending_limit: Spending limit in wei
            is_autonomous: Autonomous flag
            
        Returns:
            Dict with agent and wallet
        """
        try:
            # Verify wallet exists
            wallet_repo = await self.wallets
            wallet = await wallet_repo.find_by_id(wallet_id)
            if not wallet:
                raise ValueError(f"Wallet not found: {wallet_id}")
            
            # Create agent
            agent_repo = await self.agents
            agent = await agent_repo.create_agent(
                wallet_id=wallet_id,
                name=name,
                agent_type=agent_type,
                metadata=metadata,
                spending_limit=spending_limit,
                is_autonomous=is_autonomous
            )
            
            # Audit log
            audit_repo = await self.audit
            await audit_repo.log_action(
                action="AGENT_CREATE",
                resource="agent",
                user_id=user_id,
                resource_id=agent.id,
                details={"wallet_id": wallet_id, "agent_type": agent_type}
            )
            
            logger.info(f"Agent created: {name} for wallet {wallet_id}")
            
            return {
                "agent": agent,
                "wallet": wallet
            }
        
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            raise
    
    async def log_and_execute_decision(
        self,
        agent_id: str,
        decision_hash: str,
        reasoning: str,
        action: str,
        parameters: dict,
        confidence: int,
        user_id: Optional[str] = None,
        context: Optional[dict] = None,
        ipfs_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log decision and prepare for execution.
        
        Args:
            agent_id: Agent ID
            decision_hash: Cryptographic decision hash
            reasoning: AI reasoning
            action: Action type
            parameters: Action parameters
            confidence: Confidence score (0-100)
            user_id: User ID (for audit)
            context: Decision context
            ipfs_hash: IPFS proof hash
            
        Returns:
            Dict with decision object
        """
        try:
            # Create decision
            decision_repo = await self.decisions
            decision = await decision_repo.create_decision(
                agent_id=agent_id,
                decision_hash=decision_hash,
                reasoning=reasoning,
                action=action,
                parameters=parameters,
                confidence=confidence,
                context=context,
                ipfs_hash=ipfs_hash
            )
            
            # Audit log
            audit_repo = await self.audit
            await audit_repo.log_action(
                action="DECISION_CREATE",
                resource="decision",
                user_id=user_id,
                resource_id=decision.id,
                details={
                    "agent_id": agent_id,
                    "action": action,
                    "confidence": confidence
                }
            )
            
            logger.info(f"Decision logged: {decision_hash[:16]}... for agent {agent_id}")
            
            return {
                "decision": decision
            }
        
        except Exception as e:
            logger.error(f"Error logging decision: {e}")
            raise
    
    async def record_transaction(
        self,
        wallet_id: str,
        from_address: str,
        to_address: Optional[str],
        value: int,
        network: str,
        tx_type: str,
        user_id: Optional[str] = None,
        decision_id: Optional[str] = None,
        tx_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record transaction and update wallet balance.
        
        Args:
            wallet_id: Wallet ID
            from_address: Sender address
            to_address: Recipient address
            value: Transaction value in wei
            network: Network name
            tx_type: Transaction type
            user_id: User ID (for audit)
            decision_id: Associated decision ID
            tx_hash: Blockchain transaction hash
            
        Returns:
            Dict with transaction object
        """
        try:
            # Create transaction
            tx_repo = await self.transactions
            transaction = await tx_repo.create_transaction(
                wallet_id=wallet_id,
                from_address=from_address,
                to_address=to_address,
                value=value,
                network=network,
                tx_type=tx_type,
                decision_id=decision_id
            )
            
            # Update with hash if provided
            if tx_hash:
                transaction = await tx_repo.update_status(
                    tx_id=transaction.id,
                    status="SUBMITTED",
                    tx_hash=tx_hash
                )
            
            # Audit log
            audit_repo = await self.audit
            await audit_repo.log_action(
                action="TRANSACTION_SUBMIT",
                resource="transaction",
                user_id=user_id,
                resource_id=transaction.id,
                details={
                    "wallet_id": wallet_id,
                    "value": str(value),
                    "network": network,
                    "tx_type": tx_type
                }
            )
            
            logger.info(f"Transaction recorded: {tx_hash or transaction.id}")
            
            return {
                "transaction": transaction
            }
        
        except Exception as e:
            logger.error(f"Error recording transaction: {e}")
            raise
    
    async def confirm_transaction(
        self,
        tx_id: str,
        block_number: int,
        gas_used: int,
        effective_gas_price: int,
        success: bool = True,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Confirm transaction and update related records.
        
        Args:
            tx_id: Transaction ID
            block_number: Block number
            gas_used: Gas used
            effective_gas_price: Effective gas price
            success: Whether transaction succeeded
            error: Error message if failed
            
        Returns:
            Dict with updated transaction and agent performance
        """
        try:
            tx_repo = await self.transactions
            
            # Update transaction status
            status = "CONFIRMED" if success else "FAILED"
            transaction = await tx_repo.update_status(
                tx_id=tx_id,
                status=status,
                block_number=block_number,
                gas_used=gas_used,
                effective_gas_price=effective_gas_price,
                error=error
            )
            
            # Update decision status if linked
            if transaction.decisionId:
                decision_repo = await self.decisions
                decision_status = "EXECUTED" if success else "FAILED"
                await decision_repo.update_status(
                    decision_id=transaction.decisionId,
                    status=decision_status
                )
            
            # Update agent performance if decision exists
            if transaction.decisionId:
                decision = await (await self.decisions).find_by_id(transaction.decisionId)
                if decision:
                    agent_repo = await self.agents
                    await agent_repo.increment_transaction_count(
                        agent_id=decision.agentId,
                        successful=success
                    )
                    
                    # Update reputation
                    reputation_change = 10 if success else -5
                    await agent_repo.update_reputation(
                        agent_id=decision.agentId,
                        change=reputation_change
                    )
            
            logger.info(f"Transaction confirmed: {tx_id} (success={success})")
            
            return {
                "transaction": transaction,
                "success": success
            }
        
        except Exception as e:
            logger.error(f"Error confirming transaction: {e}")
            raise
    
    async def get_dashboard_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive dashboard statistics for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dashboard statistics
        """
        try:
            # Get user's wallets
            wallet_repo = await self.wallets
            wallets = await wallet_repo.find_user_wallets(user_id)
            
            total_balance = sum(int(w.balance) for w in wallets)
            
            # Get agents
            agent_repo = await self.agents
            agent_count = 0
            active_agents = 0
            
            for wallet in wallets:
                agents = await agent_repo.find_by_wallet(wallet.id)
                agent_count += len(agents)
                active_agents += sum(1 for a in agents if a.status == "ACTIVE")
            
            # Get transaction stats
            tx_repo = await self.transactions
            tx_stats = {}
            for wallet in wallets:
                stats = await tx_repo.get_transaction_stats(wallet.id)
                for key, value in stats.items():
                    tx_stats[key] = tx_stats.get(key, 0) + value
            
            return {
                "user_id": user_id,
                "wallet_count": len(wallets),
                "total_balance_wei": total_balance,
                "agent_count": agent_count,
                "active_agents": active_agents,
                "transaction_stats": tx_stats
            }
        
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            raise
    
    async def get_audit_trail(
        self,
        wallet_address: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        include_decisions: bool = True,
        include_transactions: bool = True,
        limit: int = 100
    ) -> list:
        """
        Get audit trail for a wallet (FR-008).
        
        Args:
            wallet_address: Wallet address
            from_date: Start date filter
            to_date: End date filter
            include_decisions: Include decision records
            include_transactions: Include transaction records
            limit: Maximum number of entries
            
        Returns:
            List of audit trail entries
        """
        try:
            entries = []
            
            # Get wallet
            wallet_repo = await self.wallets
            wallet = await wallet_repo.find_by_address(wallet_address)
            if not wallet:
                logger.warning(f"Wallet not found: {wallet_address}")
                return []
            
            # Get decisions if requested
            if include_decisions:
                decision_repo = await self.decisions
                # Get agents for this wallet
                agent_repo = await self.agents
                agents = await agent_repo.find_by_wallet(wallet.id)
                
                for agent in agents:
                    decisions = await decision_repo.find_by_agent(
                        agent_id=agent.id,
                        limit=limit
                    )
                    
                    for decision in decisions:
                        entry = {
                            "type": "decision",
                            "id": decision.id,
                            "timestamp": decision.createdAt.isoformat() if decision.createdAt else None,
                            "agent_type": agent.agentType,
                            "action": decision.action,
                            "reasoning": decision.reasoning,
                            "status": decision.status,
                            "confidence": decision.confidence,
                            "decision_hash": decision.decisionHash,
                            "on_chain_tx_hash": decision.onChainTxHash
                        }
                        
                        # Apply date filters
                        if from_date and decision.createdAt and decision.createdAt < from_date:
                            continue
                        if to_date and decision.createdAt and decision.createdAt > to_date:
                            continue
                            
                        entries.append(entry)
            
            # Get transactions if requested
            if include_transactions:
                tx_repo = await self.transactions
                transactions = await tx_repo.find_by_wallet(
                    wallet_id=wallet.id,
                    limit=limit
                )
                
                for tx in transactions:
                    entry = {
                        "type": "transaction",
                        "id": tx.id,
                        "timestamp": tx.createdAt.isoformat() if tx.createdAt else None,
                        "tx_hash": tx.txHash,
                        "from_address": tx.fromAddress,
                        "to_address": tx.toAddress,
                        "value": str(tx.value),
                        "status": tx.status,
                        "gas_used": str(tx.gasUsed) if tx.gasUsed else None,
                        "decision_id": tx.decisionId
                    }
                    
                    # Apply date filters
                    if from_date and tx.createdAt and tx.createdAt < from_date:
                        continue
                    if to_date and tx.createdAt and tx.createdAt > to_date:
                        continue
                        
                    entries.append(entry)
            
            # Sort by timestamp (newest first)
            entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Apply limit
            entries = entries[:limit]
            
            logger.info(f"Retrieved {len(entries)} audit trail entries for {wallet_address}")
            return entries
        
        except Exception as e:
            logger.error(f"Error getting audit trail: {e}")
            raise
    
    async def get_agent_activity(
        self,
        agent_type: str,
        limit: int = 100
    ) -> list:
        """
        Get activity log for a specific agent type.
        
        Args:
            agent_type: Agent type (planner, executor, evaluator, communicator)
            limit: Maximum number of activities
            
        Returns:
            List of agent activities
        """
        try:
            activities = []
            
            # Get all agents of this type
            agent_repo = await self.agents
            db = await self._get_db()
            
            # Query agents by type
            agents = await db.agent.find_many(
                where={"agentType": agent_type.upper()},
                take=50  # Limit number of agents
            )
            
            if not agents:
                logger.info(f"No agents found for type: {agent_type}")
                return []
            
            # Get decisions for each agent
            decision_repo = await self.decisions
            for agent in agents:
                decisions = await decision_repo.find_by_agent(
                    agent_id=agent.id,
                    limit=limit // len(agents) if len(agents) > 0 else limit
                )
                
                for decision in decisions:
                    activity = {
                        "agent_id": agent.id,
                        "agent_type": agent.agentType,
                        "wallet_id": agent.walletId,
                        "decision_id": decision.id,
                        "action": decision.action,
                        "reasoning": decision.reasoning[:200] if decision.reasoning else None,  # Truncate
                        "confidence": decision.confidence,
                        "status": decision.status,
                        "timestamp": decision.createdAt.isoformat() if decision.createdAt else None,
                        "executed_at": decision.executedAt.isoformat() if decision.executedAt else None,
                        "on_chain_tx_hash": decision.onChainTxHash
                    }
                    activities.append(activity)
            
            # Sort by timestamp (newest first)
            activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Apply limit
            activities = activities[:limit]
            
            logger.info(f"Retrieved {len(activities)} activities for agent type {agent_type}")
            return activities
        
        except Exception as e:
            logger.error(f"Error getting agent activity: {e}")
            raise
    
    async def get_wallet_timeline(
        self,
        wallet_address: str,
        limit: int = 50
    ) -> list:
        """
        Get chronological timeline of wallet activities.
        
        Args:
            wallet_address: Wallet address
            limit: Maximum number of events
            
        Returns:
            List of timeline events
        """
        try:
            # Get wallet
            wallet_repo = await self.wallets
            wallet = await wallet_repo.find_by_address(wallet_address)
            if not wallet:
                logger.warning(f"Wallet not found: {wallet_address}")
                return []
            
            timeline = []
            
            # Get transactions
            tx_repo = await self.transactions
            transactions = await tx_repo.find_by_wallet(
                wallet_id=wallet.id,
                limit=limit
            )
            
            for tx in transactions:
                timeline.append({
                    "type": "transaction",
                    "timestamp": tx.createdAt.isoformat() if tx.createdAt else None,
                    "tx_hash": tx.txHash,
                    "from": tx.fromAddress,
                    "to": tx.toAddress,
                    "value": str(tx.value),
                    "status": tx.status
                })
            
            # Get agent activities
            agent_repo = await self.agents
            agents = await agent_repo.find_by_wallet(wallet.id)
            
            decision_repo = await self.decisions
            for agent in agents:
                decisions = await decision_repo.find_by_agent(
                    agent_id=agent.id,
                    limit=limit // len(agents) if len(agents) > 0 else limit
                )
                
                for decision in decisions:
                    timeline.append({
                        "type": "decision",
                        "timestamp": decision.createdAt.isoformat() if decision.createdAt else None,
                        "agent_type": agent.agentType,
                        "action": decision.action,
                        "status": decision.status,
                        "confidence": decision.confidence
                    })
            
            # Sort by timestamp (newest first)
            timeline.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Apply limit
            timeline = timeline[:limit]
            
            logger.info(f"Retrieved timeline with {len(timeline)} events for {wallet_address}")
            return timeline
        
        except Exception as e:
            logger.error(f"Error getting wallet timeline: {e}")
            raise


# Global service instance
_service = DatabaseService()


def get_database_service() -> DatabaseService:
    """Get global database service instance"""
    return _service
