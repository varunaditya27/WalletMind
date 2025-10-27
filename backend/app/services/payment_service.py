"""
Payment Service - API Payment Automation (FR-010)

Handles:
- Blockchain payments for API services
- Cost calculation and tracking
- Payment verification
- Spending analytics
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class APIPayment:
    """API payment record"""
    def __init__(
        self,
        agent_address: str,
        service_name: str,
        recipient_address: str,
        amount_eth: Decimal,
        api_endpoint: str,
        status: PaymentStatus = PaymentStatus.PENDING,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ):
        self.agent_address = agent_address
        self.service_name = service_name
        self.recipient_address = recipient_address
        self.amount_eth = amount_eth
        self.api_endpoint = api_endpoint
        self.status = status
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
        self.tx_hash: Optional[str] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None


class PaymentService:
    """
    Handles automated API payments for AI services (FR-010).
    
    Features:
    - Execute blockchain payments for API access
    - Calculate API costs based on usage
    - Track payment history per agent
    - Verify payment completion
    - Generate spending reports
    """
    
    def __init__(self):
        self.payment_history: Dict[str, List[APIPayment]] = {}
        self.pricing_table = self._initialize_pricing()
        logger.info("Payment service initialized")
    
    def _initialize_pricing(self) -> Dict[str, Dict[str, Decimal]]:
        """Initialize API pricing table"""
        return {
            "Groq": {
                "llm_query": Decimal("0.0001"),  # per 1k tokens
                "embedding": Decimal("0.00005"),
            },
            "Google AI Studio": {
                "llm_query": Decimal("0.00015"),
                "embedding": Decimal("0.00005"),
                "vision": Decimal("0.0002"),
            },
            "Chainlink": {
                "price_feed": Decimal("0.001"),  # per query
                "vrf": Decimal("0.002"),  # per request
            },
            "The Graph": {
                "query": Decimal("0.0001"),  # per 1k queries
            },
        }
    
    async def calculate_cost(
        self, 
        service_name: str,
        operation: str,
        estimated_tokens: int = 1000,
        estimated_queries: int = 1
    ) -> Decimal:
        """
        Calculate estimated cost for API operation.
        
        Args:
            service_name: API service name
            operation: Type of operation
            estimated_tokens: Estimated token usage
            estimated_queries: Number of queries
            
        Returns:
            Estimated cost in ETH
        """
        try:
            base_cost = self.pricing_table.get(service_name, {}).get(
                operation, 
                Decimal("0.0001")
            )
            
            # Calculate based on usage type
            if "token" in operation or "llm" in operation or "embedding" in operation:
                cost = base_cost * (estimated_tokens / 1000)
            elif "query" in operation:
                cost = base_cost * estimated_queries
            else:
                cost = base_cost
            
            logger.debug(f"Calculated cost for {service_name}.{operation}: {cost} ETH")
            return cost
            
        except Exception as e:
            logger.error(f"Error calculating cost: {e}")
            return Decimal("0.0001")  # Default fallback
    
    async def execute_payment(
        self,
        agent_address: str,
        service_name: str,
        recipient_address: str,
        amount_eth: Decimal,
        api_endpoint: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> APIPayment:
        """
        Execute blockchain payment for API service.
        
        Args:
            agent_address: Agent's wallet address
            service_name: Name of API service
            recipient_address: Service provider's wallet address
            amount_eth: Payment amount in ETH
            api_endpoint: API endpoint being paid for
            metadata: Additional payment metadata
            
        Returns:
            APIPayment record
        """
        payment = APIPayment(
            agent_address=agent_address,
            service_name=service_name,
            recipient_address=recipient_address,
            amount_eth=amount_eth,
            api_endpoint=api_endpoint,
            status=PaymentStatus.PENDING,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
        )
        
        try:
            # TODO: Execute actual blockchain transaction via blockchain service
            # For now, simulate successful payment
            payment.tx_hash = f"0x{'0' * 64}"  # Mock tx hash
            payment.status = PaymentStatus.CONFIRMED
            payment.completed_at = datetime.utcnow()
            
            # Track payment history
            if agent_address not in self.payment_history:
                self.payment_history[agent_address] = []
            self.payment_history[agent_address].append(payment)
            
            logger.info(
                f"Payment executed: {service_name} - {amount_eth} ETH "
                f"(agent={agent_address[:8]}...)"
            )
            
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.error_message = str(e)
            logger.error(f"Payment failed: {e}")
        
        return payment
    
    async def verify_payment(
        self, 
        tx_hash: str,
        min_confirmations: int = 3
    ) -> Dict[str, Any]:
        """
        Verify that payment transaction has been confirmed.
        
        Args:
            tx_hash: Transaction hash to verify
            min_confirmations: Minimum confirmations required
            
        Returns:
            Verification result with status
        """
        # TODO: Integrate with blockchain service for actual verification
        # For now, return mock verification
        return {
            "tx_hash": tx_hash,
            "confirmed": True,
            "confirmations": min_confirmations,
            "status": "confirmed",
            "verified_at": datetime.utcnow().isoformat()
        }
    
    async def get_spending_summary(
        self, 
        agent_address: str,
        time_period_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get spending summary for an agent.
        
        Args:
            agent_address: Agent's wallet address
            time_period_hours: Time period to analyze
            
        Returns:
            Spending summary with totals by service
        """
        payments = self.payment_history.get(agent_address, [])
        
        if not payments:
            return {
                "agent_address": agent_address,
                "time_period_hours": time_period_hours,
                "total_spent_eth": 0.0,
                "by_service": {},
                "payment_count": 0,
            }
        
        # Filter by time period
        cutoff_time = datetime.utcnow() - timedelta(hours=time_period_hours)
        recent_payments = [
            p for p in payments 
            if p.created_at >= cutoff_time
        ]
        
        # Calculate totals
        total_spent = sum(p.amount_eth for p in recent_payments)
        
        by_service = {}
        for payment in recent_payments:
            service = payment.service_name
            if service not in by_service:
                by_service[service] = Decimal("0")
            by_service[service] += payment.amount_eth
        
        logger.debug(
            f"Spending summary for {agent_address[:8]}...: "
            f"{total_spent} ETH in {len(recent_payments)} payments"
        )
        
        return {
            "agent_address": agent_address,
            "time_period_hours": time_period_hours,
            "total_spent_eth": float(total_spent),
            "by_service": {k: float(v) for k, v in by_service.items()},
            "payment_count": len(recent_payments),
            "recent_payments": [
                {
                    "service": p.service_name,
                    "amount_eth": float(p.amount_eth),
                    "status": p.status.value,
                    "created_at": p.created_at.isoformat()
                }
                for p in recent_payments[:10]  # Last 10 payments
            ]
        }
    
    async def get_payment_history(
        self,
        agent_address: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get payment history for an agent.
        
        Args:
            agent_address: Agent's wallet address
            limit: Maximum number of payments to return
            
        Returns:
            List of payment records
        """
        payments = self.payment_history.get(agent_address, [])
        
        # Sort by created_at descending
        sorted_payments = sorted(
            payments, 
            key=lambda p: p.created_at, 
            reverse=True
        )[:limit]
        
        return [
            {
                "service_name": p.service_name,
                "amount_eth": float(p.amount_eth),
                "recipient_address": p.recipient_address,
                "api_endpoint": p.api_endpoint,
                "status": p.status.value,
                "tx_hash": p.tx_hash,
                "created_at": p.created_at.isoformat(),
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                "metadata": p.metadata
            }
            for p in sorted_payments
        ]
    
    async def estimate_monthly_cost(
        self,
        agent_address: str
    ) -> Dict[str, Any]:
        """
        Estimate monthly API costs based on recent usage.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Monthly cost estimate
        """
        # Get last 7 days of spending
        summary_7d = await self.get_spending_summary(agent_address, 24 * 7)
        
        # Extrapolate to 30 days
        daily_avg = summary_7d["total_spent_eth"] / 7
        monthly_estimate = daily_avg * 30
        
        return {
            "agent_address": agent_address,
            "estimated_monthly_cost_eth": round(monthly_estimate, 6),
            "based_on_days": 7,
            "daily_average_eth": round(daily_avg, 6),
            "current_7d_total_eth": summary_7d["total_spent_eth"],
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get payment service statistics"""
        total_agents = len(self.payment_history)
        total_payments = sum(len(payments) for payments in self.payment_history.values())
        
        all_payments = [
            payment 
            for payments in self.payment_history.values() 
            for payment in payments
        ]
        
        total_volume = sum(p.amount_eth for p in all_payments)
        confirmed_count = sum(1 for p in all_payments if p.status == PaymentStatus.CONFIRMED)
        
        return {
            "service": "payment",
            "total_agents": total_agents,
            "total_payments": total_payments,
            "confirmed_payments": confirmed_count,
            "total_volume_eth": float(total_volume),
            "supported_services": list(self.pricing_table.keys()),
            "status": "operational"
        }


# Singleton instance
_payment_service: Optional[PaymentService] = None


def get_payment_service() -> PaymentService:
    """Get or create singleton PaymentService instance"""
    global _payment_service
    
    if _payment_service is None:
        _payment_service = PaymentService()
    
    return _payment_service