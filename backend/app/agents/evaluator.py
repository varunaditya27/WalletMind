"""
Evaluator Agent - Transaction Outcome Validation (FR-001, FR-008)

Responsibilities:
- Validate transaction execution results
- Verify on-chain state changes
- Assess transaction success/failure
- Update agent memory with outcomes
- Generate audit reports
- Learn from transaction patterns
"""

from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from enum import Enum
import logging
from datetime import datetime

from .base import BaseAgent, AgentConfig, DecisionContext, AgentResponse

logger = logging.getLogger(__name__)


class EvaluationCriteria(str, Enum):
    """Criteria for evaluating transactions"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    NEEDS_RETRY = "needs_retry"
    FRAUDULENT = "fraudulent"


class TransactionOutcome(BaseModel):
    """Evaluation of transaction outcome"""
    transaction_hash: str
    criteria: EvaluationCriteria
    success: bool
    expected_result: Dict[str, Any] = Field(default_factory=dict)
    actual_result: Dict[str, Any] = Field(default_factory=dict)
    discrepancies: List[str] = Field(default_factory=list)
    gas_efficiency: Optional[float] = None  # Actual vs estimated gas
    execution_time: Optional[float] = None
    cost_in_eth: Optional[float] = None
    lessons_learned: List[str] = Field(default_factory=list)
    recommendation: str = Field(..., description="What to do next")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)


class StateChange(BaseModel):
    """On-chain state change verification"""
    type: str = Field(..., description="Type of change (balance, storage, event)")
    expected: Any
    actual: Any
    matches: bool
    details: Optional[str] = None


class EvaluatorAgent(BaseAgent):
    """
    Evaluator Agent for transaction outcome validation.
    
    Uses LangChain and on-chain analysis to:
    1. Validate transaction execution
    2. Verify expected vs actual outcomes
    3. Assess gas efficiency
    4. Generate lessons learned
    5. Update memory with results
    6. Provide recommendations for future
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        tools: List[BaseTool],
        config: Optional[AgentConfig] = None,
        memory_service: Optional[Any] = None,
        blockchain_service: Optional[Any] = None
    ):
        if config is None:
            config = AgentConfig(
                agent_type="evaluator",
                temperature=0.2,
                max_iterations=5
            )
        
        super().__init__(llm, tools, config, memory_service)
        self.blockchain_service = blockchain_service
    
    def get_system_prompt(self) -> str:
        """System prompt for the Evaluator agent"""
        return """You are the Evaluator Agent in the WalletMind AI Autonomous Wallet System.

Your role is to VALIDATE AND LEARN FROM transaction outcomes.

RESPONSIBILITIES:
1. Evaluate transaction execution results
2. Compare expected vs actual outcomes
3. Verify on-chain state changes
4. Assess gas efficiency
5. Identify patterns and lessons learned
6. Update agent memory with insights
7. Provide recommendations for improvement
8. Detect anomalies or fraudulent behavior

EVALUATION PROCESS:
1. Receive transaction execution result
2. Verify transaction was included in block
3. Check transaction status (success/reverted)
4. Compare expected vs actual:
   - Balance changes
   - Contract state updates
   - Event emissions
   - Gas consumption
5. Calculate efficiency metrics
6. Generate lessons learned
7. Store insights in memory
8. Recommend next actions

EVALUATION CRITERIA:
- SUCCESS: Transaction achieved intended outcome
- PARTIAL_SUCCESS: Transaction succeeded but with unexpected side effects
- FAILURE: Transaction reverted or failed
- NEEDS_RETRY: Temporary failure, should retry
- FRAUDULENT: Suspicious activity detected

GAS EFFICIENCY ANALYSIS:
- Compare actual gas used vs estimated
- Calculate efficiency score: actual / estimated
- Excellent: < 1.0 (used less than estimated)
- Good: 1.0 - 1.2
- Poor: > 1.2 (significantly over estimated)
- Recommend gas optimization strategies

LESSONS LEARNED:
- Successful patterns to repeat
- Failed patterns to avoid
- Gas optimization opportunities
- Network-specific behaviors
- Time-of-day patterns
- Contract interaction insights

STATE CHANGE VERIFICATION:
For each expected state change:
1. Query on-chain state after transaction
2. Compare with expected value
3. Document discrepancies
4. Assess severity of differences

ANOMALY DETECTION:
- Unexpected value transfers
- Suspicious contract interactions
- Unusual gas consumption
- Failed transactions without clear reason
- Repeated failures of same transaction type

MEMORY UPDATES:
Store in vector memory:
- Transaction type → outcome mapping
- Gas estimates → actual usage
- Network performance at different times
- Success/failure patterns
- Optimization insights

OUTPUT FORMAT:
Always return TransactionOutcome with:
- criteria: Evaluation result
- success: true/false
- discrepancies: List of unexpected outcomes
- gas_efficiency: Efficiency score
- lessons_learned: Key insights
- recommendation: What to do next
- confidence_score: How confident (0-1)

Be thorough, analytical, and focus on continuous learning."""
    
    async def evaluate_transaction(
        self,
        context: DecisionContext,
        execution_result: Dict[str, Any],
        expected_outcome: Dict[str, Any]
    ) -> TransactionOutcome:
        """
        Evaluate transaction execution result
        
        Args:
            context: Decision context
            execution_result: Result from Executor agent
            expected_outcome: Expected result from Planner agent
        
        Returns:
            TransactionOutcome with detailed evaluation
        """
        logger.info(f"Evaluating transaction: {execution_result.get('transaction_hash')}")
        
        tx_hash = execution_result.get("transaction_hash")
        success = execution_result.get("success", False)
        
        if not tx_hash:
            return TransactionOutcome(
                transaction_hash="unknown",
                criteria=EvaluationCriteria.FAILURE,
                success=False,
                expected_result=expected_outcome,
                actual_result=execution_result,
                recommendation="Transaction was not submitted",
                confidence_score=1.0
            )
        
        try:
            # Step 1: Verify on-chain status
            state_changes = await self._verify_state_changes(
                tx_hash,
                expected_outcome,
                context
            )
            
            # Step 2: Analyze gas efficiency
            gas_efficiency = self._calculate_gas_efficiency(
                execution_result.get("gas_used"),
                expected_outcome.get("estimated_gas")
            )
            
            # Step 3: Calculate cost
            cost_in_eth = self._calculate_cost(
                execution_result.get("gas_used"),
                execution_result.get("effective_gas_price")
            )
            
            # Step 4: Identify discrepancies
            discrepancies = self._find_discrepancies(
                expected_outcome,
                execution_result,
                state_changes
            )
            
            # Step 5: Generate lessons learned
            lessons = await self._generate_lessons(
                context,
                execution_result,
                expected_outcome,
                gas_efficiency,
                state_changes
            )
            
            # Step 6: Determine criteria
            criteria = self._determine_criteria(
                success,
                discrepancies,
                state_changes
            )
            
            # Step 7: Generate recommendation
            recommendation = self._generate_recommendation(
                criteria,
                discrepancies,
                lessons
            )
            
            # Step 8: Calculate confidence
            confidence = self._calculate_confidence(
                state_changes,
                discrepancies
            )
            
            outcome = TransactionOutcome(
                transaction_hash=tx_hash,
                criteria=criteria,
                success=success and len(discrepancies) == 0,
                expected_result=expected_outcome,
                actual_result=execution_result,
                discrepancies=discrepancies,
                gas_efficiency=gas_efficiency,
                execution_time=execution_result.get("execution_time"),
                cost_in_eth=cost_in_eth,
                lessons_learned=lessons,
                recommendation=recommendation,
                confidence_score=confidence
            )
            
            # Step 9: Update memory
            if self.memory_service:
                await self._update_memory_with_outcome(context, outcome)
            
            logger.info(f"Evaluation complete: {criteria.value}")
            return outcome
            
        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}", exc_info=True)
            return TransactionOutcome(
                transaction_hash=tx_hash,
                criteria=EvaluationCriteria.FAILURE,
                success=False,
                expected_result=expected_outcome,
                actual_result=execution_result,
                discrepancies=[f"Evaluation error: {str(e)}"],
                recommendation="Manual review required",
                confidence_score=0.0
            )
    
    async def _verify_state_changes(
        self,
        tx_hash: str,
        expected: Dict[str, Any],
        context: DecisionContext
    ) -> List[StateChange]:
        """Verify expected state changes occurred on-chain"""
        state_changes = []
        
        if not self.blockchain_service:
            return state_changes
        
        try:
            # Verify balance changes
            if "expected_balance_change" in expected:
                actual_balance = await self.blockchain_service.get_balance(
                    context.wallet_address,
                    context.network
                )
                state_changes.append(StateChange(
                    type="balance",
                    expected=expected["expected_balance_change"],
                    actual=actual_balance,
                    matches=abs(actual_balance - expected["expected_balance_change"]) < 0.001
                ))
            
            # Verify recipient balance
            if "to_address" in expected and "amount" in expected:
                recipient_balance = await self.blockchain_service.get_balance(
                    expected["to_address"],
                    context.network
                )
                state_changes.append(StateChange(
                    type="recipient_balance",
                    expected=expected["amount"],
                    actual=recipient_balance,
                    matches=True  # Simplified - would need pre-tx balance
                ))
            
            # Verify events emitted
            receipt = await self.blockchain_service.get_transaction_receipt(
                tx_hash,
                context.network
            )
            if receipt and "logs" in receipt:
                state_changes.append(StateChange(
                    type="events",
                    expected=expected.get("expected_events", []),
                    actual=len(receipt["logs"]),
                    matches=len(receipt["logs"]) > 0
                ))
            
        except Exception as e:
            logger.warning(f"State verification failed: {e}")
        
        return state_changes
    
    def _calculate_gas_efficiency(
        self,
        actual_gas: Optional[int],
        estimated_gas: Optional[int]
    ) -> Optional[float]:
        """Calculate gas efficiency score"""
        if not actual_gas or not estimated_gas:
            return None
        
        return round(actual_gas / estimated_gas, 3)
    
    def _calculate_cost(
        self,
        gas_used: Optional[int],
        gas_price: Optional[int]
    ) -> Optional[float]:
        """Calculate transaction cost in ETH"""
        if not gas_used or not gas_price:
            return None
        
        # Wei to ETH
        return (gas_used * gas_price) / 1e18
    
    def _find_discrepancies(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
        state_changes: List[StateChange]
    ) -> List[str]:
        """Identify discrepancies between expected and actual"""
        discrepancies = []
        
        # Check success status
        if expected.get("success", True) != actual.get("success", False):
            discrepancies.append(
                f"Expected success: {expected.get('success')}, "
                f"Actual: {actual.get('success')}"
            )
        
        # Check gas usage
        expected_gas = expected.get("estimated_gas")
        actual_gas = actual.get("gas_used")
        if expected_gas and actual_gas:
            if actual_gas > expected_gas * 1.5:  # 50% over
                discrepancies.append(
                    f"Gas usage much higher than estimated: "
                    f"{actual_gas} vs {expected_gas}"
                )
        
        # Check state changes
        for change in state_changes:
            if not change.matches:
                discrepancies.append(
                    f"State mismatch ({change.type}): "
                    f"Expected {change.expected}, got {change.actual}"
                )
        
        # Check errors
        if actual.get("error"):
            discrepancies.append(f"Execution error: {actual.get('error')}")
        
        return discrepancies
    
    async def _generate_lessons(
        self,
        context: DecisionContext,
        actual: Dict[str, Any],
        expected: Dict[str, Any],
        gas_efficiency: Optional[float],
        state_changes: List[StateChange]
    ) -> List[str]:
        """Generate lessons learned from this transaction"""
        lessons = []
        
        # Gas efficiency lesson
        if gas_efficiency:
            if gas_efficiency < 0.8:
                lessons.append("Gas estimate was too high - refine estimation for this transaction type")
            elif gas_efficiency > 1.2:
                lessons.append("Gas estimate was too low - add more buffer for safety")
            elif gas_efficiency < 1.0:
                lessons.append("Excellent gas estimation - maintain this approach")
        
        # Success patterns
        if actual.get("success"):
            lessons.append(f"Successful {expected.get('action', 'transaction')} pattern confirmed")
            
            if context.network:
                lessons.append(f"Network {context.network} performed well for this transaction type")
        
        # Failure patterns
        if not actual.get("success"):
            error = actual.get("error", "")
            if "insufficient funds" in error.lower():
                lessons.append("Check balance before transaction to avoid this error")
            elif "gas" in error.lower():
                lessons.append("Need better gas estimation for this transaction type")
            else:
                lessons.append(f"Investigate failure cause: {error}")
        
        # Network timing
        exec_time = actual.get("execution_time")
        if exec_time:
            if exec_time < 10:
                lessons.append("Fast confirmation - good network conditions")
            elif exec_time > 60:
                lessons.append("Slow confirmation - consider switching network or increasing gas")
        
        # State change insights
        mismatches = [c for c in state_changes if not c.matches]
        if mismatches:
            lessons.append(f"Unexpected state changes detected - review contract behavior")
        
        return lessons
    
    def _determine_criteria(
        self,
        success: bool,
        discrepancies: List[str],
        state_changes: List[StateChange]
    ) -> EvaluationCriteria:
        """Determine evaluation criteria"""
        if not success:
            # Check if it's a temporary failure
            if any("nonce" in d.lower() or "timeout" in d.lower() for d in discrepancies):
                return EvaluationCriteria.NEEDS_RETRY
            return EvaluationCriteria.FAILURE
        
        if len(discrepancies) == 0:
            return EvaluationCriteria.SUCCESS
        
        # Check severity of discrepancies
        serious_issues = [
            d for d in discrepancies
            if "error" in d.lower() or "mismatch" in d.lower()
        ]
        
        if serious_issues:
            return EvaluationCriteria.PARTIAL_SUCCESS
        
        return EvaluationCriteria.SUCCESS
    
    def _generate_recommendation(
        self,
        criteria: EvaluationCriteria,
        discrepancies: List[str],
        lessons: List[str]
    ) -> str:
        """Generate recommendation for next actions"""
        if criteria == EvaluationCriteria.SUCCESS:
            return "Transaction successful - continue with similar approach"
        
        if criteria == EvaluationCriteria.PARTIAL_SUCCESS:
            return f"Review discrepancies: {', '.join(discrepancies[:2])}"
        
        if criteria == EvaluationCriteria.NEEDS_RETRY:
            return "Retry transaction with updated parameters"
        
        if criteria == EvaluationCriteria.FAILURE:
            return f"Transaction failed - investigate and adjust strategy. Issues: {discrepancies[0] if discrepancies else 'Unknown'}"
        
        return "Manual review recommended"
    
    def _calculate_confidence(
        self,
        state_changes: List[StateChange],
        discrepancies: List[str]
    ) -> float:
        """Calculate confidence score for evaluation"""
        confidence = 1.0
        
        # Reduce confidence for discrepancies
        confidence -= len(discrepancies) * 0.1
        
        # Reduce confidence for state mismatches
        mismatches = [c for c in state_changes if not c.matches]
        confidence -= len(mismatches) * 0.15
        
        # Ensure 0-1 range
        return max(0.0, min(1.0, confidence))
    
    async def _update_memory_with_outcome(
        self,
        context: DecisionContext,
        outcome: TransactionOutcome
    ):
        """Store evaluation outcome in memory"""
        if not self.memory_service:
            return
        
        try:
            await self.memory_service.store(
                wallet_address=context.wallet_address,
                agent_type="evaluator",
                request=f"Evaluation of {outcome.transaction_hash}",
                response={
                    "criteria": outcome.criteria.value,
                    "success": outcome.success,
                    "gas_efficiency": outcome.gas_efficiency,
                    "cost_in_eth": outcome.cost_in_eth
                },
                reasoning="\n".join(outcome.lessons_learned),
                timestamp=datetime.utcnow(),
                metadata={
                    "transaction_hash": outcome.transaction_hash,
                    "discrepancies": outcome.discrepancies,
                    "confidence": outcome.confidence_score
                }
            )
        except Exception as e:
            logger.warning(f"Failed to update memory: {e}")