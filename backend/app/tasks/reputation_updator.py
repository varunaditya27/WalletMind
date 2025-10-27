"""
Reputation Updator - Agent Performance Tracking and On-Chain Reputation

Tracks agent performance and updates reputation:
- Calculate agent success rates
- Track decision quality metrics
- Update on-chain reputation scores
- Generate performance reports
- Trigger reputation contract updates
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class AgentMetric(str, Enum):
    """Agent performance metrics"""
    SUCCESS_RATE = "success_rate"
    GAS_EFFICIENCY = "gas_efficiency"
    RESPONSE_TIME = "response_time"
    DECISION_QUALITY = "decision_quality"
    USER_SATISFACTION = "user_satisfaction"


class ReputationTier(str, Enum):
    """Reputation tiers"""
    NOVICE = "novice"        # 0-20
    BEGINNER = "beginner"    # 21-40
    INTERMEDIATE = "intermediate"  # 41-60
    ADVANCED = "advanced"    # 61-80
    EXPERT = "expert"        # 81-100


class AgentPerformance:
    """Agent performance tracking"""
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.created_at = datetime.utcnow()
        
        # Performance metrics
        self.total_decisions = 0
        self.successful_decisions = 0
        self.failed_decisions = 0
        
        self.total_gas_estimated = 0.0
        self.total_gas_actual = 0.0
        
        self.total_response_time = 0.0
        
        # Quality scores (0-100)
        self.decision_quality_scores: List[float] = []
        self.user_satisfaction_scores: List[float] = []
        
        # Reputation
        self.current_reputation: float = 50.0  # Start at intermediate
        self.reputation_history: List[Dict[str, Any]] = []
        
        # Last update
        self.last_updated = datetime.utcnow()
        self.last_on_chain_update: Optional[datetime] = None
    
    def calculate_success_rate(self) -> float:
        """Calculate success rate (0-100)"""
        if self.total_decisions == 0:
            return 0.0
        return (self.successful_decisions / self.total_decisions) * 100
    
    def calculate_gas_efficiency(self) -> float:
        """Calculate gas efficiency (actual/estimated, lower is better)"""
        if self.total_gas_estimated == 0:
            return 1.0
        return self.total_gas_actual / self.total_gas_estimated
    
    def calculate_avg_response_time(self) -> float:
        """Calculate average response time in seconds"""
        if self.total_decisions == 0:
            return 0.0
        return self.total_response_time / self.total_decisions
    
    def calculate_avg_quality(self) -> float:
        """Calculate average decision quality (0-100)"""
        if not self.decision_quality_scores:
            return 50.0
        return sum(self.decision_quality_scores) / len(self.decision_quality_scores)
    
    def calculate_avg_satisfaction(self) -> float:
        """Calculate average user satisfaction (0-100)"""
        if not self.user_satisfaction_scores:
            return 50.0
        return sum(self.user_satisfaction_scores) / len(self.user_satisfaction_scores)
    
    def get_reputation_tier(self) -> ReputationTier:
        """Get reputation tier based on current score"""
        score = self.current_reputation
        
        if score <= 20:
            return ReputationTier.NOVICE
        elif score <= 40:
            return ReputationTier.BEGINNER
        elif score <= 60:
            return ReputationTier.INTERMEDIATE
        elif score <= 80:
            return ReputationTier.ADVANCED
        else:
            return ReputationTier.EXPERT


class ReputationUpdator:
    """
    Background service for tracking agent performance and updating reputation.
    
    Features:
    - Performance metric tracking
    - Reputation score calculation
    - On-chain reputation updates
    - Performance reports
    - Metric aggregation
    """
    
    def __init__(
        self,
        blockchain_service: Any,
        memory_service: Optional[Any] = None,
        update_interval: int = 300,  # 5 minutes
        on_chain_interval: int = 3600,  # 1 hour
        min_decisions_for_update: int = 10
    ):
        """
        Initialize reputation updator
        
        Args:
            blockchain_service: Blockchain service for on-chain updates
            memory_service: Memory service for historical data
            update_interval: Seconds between local updates
            on_chain_interval: Seconds between on-chain updates
            min_decisions_for_update: Minimum decisions before on-chain update
        """
        self.blockchain_service = blockchain_service
        self.memory_service = memory_service
        self.update_interval = update_interval
        self.on_chain_interval = on_chain_interval
        self.min_decisions_for_update = min_decisions_for_update
        
        # Agent performance tracking
        self.performances: Dict[str, AgentPerformance] = {}
        
        # Update state
        self.is_running = False
        self.update_task: Optional[asyncio.Task] = None
        
        logger.info("Reputation updator initialized")
    
    async def start(self):
        """Start update loop"""
        if self.is_running:
            logger.warning("Updator already running")
            return
        
        self.is_running = True
        self.update_task = asyncio.create_task(self._update_loop())
        logger.info("Reputation updator started")
    
    async def stop(self):
        """Stop update loop"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Reputation updator stopped")
    
    def get_or_create_performance(
        self,
        agent_id: str,
        agent_type: str
    ) -> AgentPerformance:
        """
        Get or create agent performance tracker
        
        Args:
            agent_id: Agent ID
            agent_type: Agent type
        
        Returns:
            AgentPerformance instance
        """
        if agent_id not in self.performances:
            self.performances[agent_id] = AgentPerformance(agent_id, agent_type)
            logger.info(f"Created performance tracker for agent {agent_id}")
        
        return self.performances[agent_id]
    
    def record_decision(
        self,
        agent_id: str,
        agent_type: str,
        success: bool,
        response_time: float,
        gas_estimated: Optional[float] = None,
        gas_actual: Optional[float] = None,
        quality_score: Optional[float] = None,
        satisfaction_score: Optional[float] = None
    ):
        """
        Record agent decision
        
        Args:
            agent_id: Agent ID
            agent_type: Agent type
            success: Decision success
            response_time: Response time in seconds
            gas_estimated: Estimated gas
            gas_actual: Actual gas used
            quality_score: Decision quality (0-100)
            satisfaction_score: User satisfaction (0-100)
        """
        perf = self.get_or_create_performance(agent_id, agent_type)
        
        perf.total_decisions += 1
        if success:
            perf.successful_decisions += 1
        else:
            perf.failed_decisions += 1
        
        perf.total_response_time += response_time
        
        if gas_estimated is not None:
            perf.total_gas_estimated += gas_estimated
        if gas_actual is not None:
            perf.total_gas_actual += gas_actual
        
        if quality_score is not None:
            perf.decision_quality_scores.append(quality_score)
        if satisfaction_score is not None:
            perf.user_satisfaction_scores.append(satisfaction_score)
        
        perf.last_updated = datetime.utcnow()
        
        logger.debug(f"Recorded decision for agent {agent_id}: success={success}")
    
    def get_performance(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent performance metrics
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Performance metrics or None
        """
        perf = self.performances.get(agent_id)
        
        if not perf:
            return None
        
        return {
            "agent_id": agent_id,
            "agent_type": perf.agent_type,
            "total_decisions": perf.total_decisions,
            "successful_decisions": perf.successful_decisions,
            "failed_decisions": perf.failed_decisions,
            "success_rate": round(perf.calculate_success_rate(), 2),
            "gas_efficiency": round(perf.calculate_gas_efficiency(), 2),
            "avg_response_time": round(perf.calculate_avg_response_time(), 2),
            "avg_quality": round(perf.calculate_avg_quality(), 2),
            "avg_satisfaction": round(perf.calculate_avg_satisfaction(), 2),
            "current_reputation": perf.current_reputation,
            "reputation_tier": perf.get_reputation_tier().value,
            "created_at": perf.created_at.isoformat(),
            "last_updated": perf.last_updated.isoformat(),
            "last_on_chain_update": perf.last_on_chain_update.isoformat() if perf.last_on_chain_update else None
        }
    
    def get_all_performances(
        self,
        agent_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all agent performances
        
        Args:
            agent_type: Filter by agent type
        
        Returns:
            List of performance metrics
        """
        results = []
        
        for agent_id, perf in self.performances.items():
            if agent_type and perf.agent_type != agent_type:
                continue
            
            metrics = self.get_performance(agent_id)
            if metrics:
                results.append(metrics)
        
        return results
    
    async def _update_loop(self):
        """Main update loop"""
        logger.info("Update loop started")
        
        last_on_chain_update = datetime.utcnow()
        
        while self.is_running:
            try:
                # Calculate updated reputation scores
                await self._update_all_reputations()
                
                # Check if on-chain update needed
                if (datetime.utcnow() - last_on_chain_update).total_seconds() >= self.on_chain_interval:
                    await self._update_on_chain_reputations()
                    last_on_chain_update = datetime.utcnow()
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in update loop: {e}", exc_info=True)
                await asyncio.sleep(self.update_interval)
        
        logger.info("Update loop stopped")
    
    async def _update_all_reputations(self):
        """Update reputation scores for all agents"""
        if not self.performances:
            return
        
        logger.debug(f"Updating reputations for {len(self.performances)} agents")
        
        for agent_id, perf in self.performances.items():
            try:
                await self._calculate_reputation(perf)
            except Exception as e:
                logger.error(f"Error updating reputation for {agent_id}: {e}")
    
    async def _calculate_reputation(self, perf: AgentPerformance):
        """
        Calculate reputation score based on performance metrics
        
        Args:
            perf: Agent performance
        """
        if perf.total_decisions == 0:
            return
        
        # Weighted reputation calculation
        weights = {
            AgentMetric.SUCCESS_RATE: 0.35,
            AgentMetric.GAS_EFFICIENCY: 0.20,
            AgentMetric.RESPONSE_TIME: 0.10,
            AgentMetric.DECISION_QUALITY: 0.20,
            AgentMetric.USER_SATISFACTION: 0.15
        }
        
        # Calculate component scores (0-100)
        success_score = perf.calculate_success_rate()
        
        # Gas efficiency: 1.0 = 100, lower is better
        gas_eff = perf.calculate_gas_efficiency()
        gas_score = max(0, 100 - (abs(gas_eff - 1.0) * 100))
        
        # Response time: 1s = 100, 10s = 0
        response_time = perf.calculate_avg_response_time()
        response_score = max(0, 100 - (response_time * 10))
        
        quality_score = perf.calculate_avg_quality()
        satisfaction_score = perf.calculate_avg_satisfaction()
        
        # Weighted sum
        new_reputation = (
            success_score * weights[AgentMetric.SUCCESS_RATE] +
            gas_score * weights[AgentMetric.GAS_EFFICIENCY] +
            response_score * weights[AgentMetric.RESPONSE_TIME] +
            quality_score * weights[AgentMetric.DECISION_QUALITY] +
            satisfaction_score * weights[AgentMetric.USER_SATISFACTION]
        )
        
        # Smooth transition (exponential moving average)
        alpha = 0.3
        new_reputation = (alpha * new_reputation) + ((1 - alpha) * perf.current_reputation)
        
        # Clamp to 0-100
        new_reputation = max(0, min(100, new_reputation))
        
        # Update if changed significantly
        if abs(new_reputation - perf.current_reputation) >= 1.0:
            old_reputation = perf.current_reputation
            perf.current_reputation = round(new_reputation, 2)
            
            # Record history
            perf.reputation_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "old_reputation": old_reputation,
                "new_reputation": perf.current_reputation,
                "tier": perf.get_reputation_tier().value
            })
            
            logger.info(
                f"Agent {perf.agent_id} reputation: {old_reputation:.2f} → {perf.current_reputation:.2f} "
                f"({perf.get_reputation_tier().value})"
            )
    
    async def _update_on_chain_reputations(self):
        """Update reputation scores on-chain"""
        logger.info("Updating on-chain reputations")
        
        updates = []
        
        for agent_id, perf in self.performances.items():
            # Only update if enough decisions and changed since last update
            if perf.total_decisions < self.min_decisions_for_update:
                continue
            
            if perf.last_on_chain_update:
                # Check if reputation changed significantly since last update
                time_since = datetime.utcnow() - perf.last_on_chain_update
                if time_since.total_seconds() < self.on_chain_interval:
                    continue
            
            updates.append({
                "agent_id": agent_id,
                "reputation": int(perf.current_reputation),
                "tier": perf.get_reputation_tier().value,
                "total_decisions": perf.total_decisions,
                "success_rate": int(perf.calculate_success_rate())
            })
        
        if not updates:
            logger.debug("No on-chain updates needed")
            return
        
        # Call blockchain service to update reputation contract
        try:
            result = await self.blockchain_service.update_agent_reputations(updates)
            
            if result.get("success"):
                # Mark as updated
                for update in updates:
                    agent_id = update["agent_id"]
                    perf = self.performances[agent_id]
                    perf.last_on_chain_update = datetime.utcnow()
                
                logger.info(f"Updated {len(updates)} on-chain reputations")
            else:
                logger.error(f"On-chain update failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error updating on-chain reputations: {e}")
    
    def generate_report(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        include_history: bool = False
    ) -> Dict[str, Any]:
        """
        Generate performance report
        
        Args:
            agent_id: Specific agent ID
            agent_type: Filter by agent type
            include_history: Include reputation history
        
        Returns:
            Performance report
        """
        if agent_id:
            perfs = [self.performances.get(agent_id)]
            perfs = [p for p in perfs if p is not None]
        elif agent_type:
            perfs = [p for p in self.performances.values() if p.agent_type == agent_type]
        else:
            perfs = list(self.performances.values())
        
        if not perfs:
            return {
                "error": "No performance data found",
                "agent_id": agent_id,
                "agent_type": agent_type
            }
        
        # Aggregate metrics
        total_decisions = sum(p.total_decisions for p in perfs)
        total_successful = sum(p.successful_decisions for p in perfs)
        avg_reputation = sum(p.current_reputation for p in perfs) / len(perfs)
        
        # Tier distribution
        tier_counts = defaultdict(int)
        for p in perfs:
            tier = p.get_reputation_tier().value
            tier_counts[tier] += 1
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "agent_type": agent_type,
            "summary": {
                "total_agents": len(perfs),
                "total_decisions": total_decisions,
                "total_successful": total_successful,
                "overall_success_rate": round((total_successful / total_decisions * 100) if total_decisions > 0 else 0, 2),
                "avg_reputation": round(avg_reputation, 2),
                "tier_distribution": dict(tier_counts)
            },
            "agents": []
        }
        
        # Individual agent metrics
        for p in perfs:
            agent_data = self.get_performance(p.agent_id)
            
            if agent_data and include_history:
                agent_data["reputation_history"] = p.reputation_history
            
            if agent_data:
                report["agents"].append(agent_data)
        
        return report
    
    def get_stats(self) -> Dict[str, Any]:
        """Get updator statistics"""
        tier_counts = defaultdict(int)
        for perf in self.performances.values():
            tier = perf.get_reputation_tier().value
            tier_counts[tier] += 1
        
        return {
            "total_agents": len(self.performances),
            "tier_distribution": dict(tier_counts),
            "is_running": self.is_running,
            "update_interval": self.update_interval,
            "on_chain_interval": self.on_chain_interval,
            "min_decisions_for_update": self.min_decisions_for_update
        }


# Singleton instance
_reputation_updator: Optional[ReputationUpdator] = None


def get_reputation_updator(
    blockchain_service: Any,
    memory_service: Optional[Any] = None
) -> ReputationUpdator:
    """Get or create singleton ReputationUpdator instance"""
    global _reputation_updator
    
    if _reputation_updator is None:
        _reputation_updator = ReputationUpdator(
            blockchain_service=blockchain_service,
            memory_service=memory_service
        )
    
    return _reputation_updator