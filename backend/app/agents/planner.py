"""
Planner Agent - High-level Financial Decision Making (FR-001, FR-002)

Responsibilities:
- Analyze natural language requests
- Make high-level financial decisions
- Evaluate risk and feasibility
- Generate structured transaction plans
- Check wallet balance and spending limits
"""

from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import logging

from .base import BaseAgent, AgentConfig, DecisionContext, AgentResponse

logger = logging.getLogger(__name__)


class TransactionPlan(BaseModel):
    """Structured output for planned transactions"""
    action: str = Field(..., description="Action to take (transfer, contract_call, api_payment, data_purchase)")
    to_address: Optional[str] = Field(None, description="Recipient address if applicable")
    amount: Optional[float] = Field(None, description="Amount in ETH/tokens")
    token: str = Field(default="ETH", description="Token symbol")
    network: str = Field(default="sepolia", description="Target network")
    risk_level: str = Field(..., description="Risk assessment (low, medium, high)")
    estimated_gas: Optional[float] = Field(None, description="Estimated gas cost in ETH")
    reasoning: str = Field(..., description="Explanation of decision")
    requires_approval: bool = Field(default=False, description="Whether user approval needed")
    contingencies: List[str] = Field(default_factory=list, description="Fallback plans")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class FinancialAnalysis(BaseModel):
    """Analysis of financial feasibility"""
    can_execute: bool
    balance_sufficient: bool
    within_spending_limit: bool
    estimated_total_cost: float
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class PlannerAgent(BaseAgent):
    """
    Planner Agent for high-level financial decision-making.
    
    Uses LangChain with Groq/Gemini to:
    1. Understand natural language requests
    2. Analyze financial feasibility
    3. Assess risks
    4. Generate structured transaction plans
    5. Check balances and limits
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        tools: List[BaseTool],
        config: Optional[AgentConfig] = None,
        memory_service: Optional[Any] = None
    ):
        if config is None:
            config = AgentConfig(
                agent_type="planner",
                temperature=0.3,  # Lower temperature for more deterministic financial decisions
                max_iterations=8
            )
        
        super().__init__(llm, tools, config, memory_service)
        self.output_parser = PydanticOutputParser(pydantic_object=TransactionPlan)
    
    def get_system_prompt(self) -> str:
        """System prompt for the Planner agent"""
        return """You are the Planner Agent in the WalletMind AI Autonomous Wallet System.

Your role is to make HIGH-LEVEL FINANCIAL DECISIONS based on user requests.

RESPONSIBILITIES:
1. Analyze natural language requests to understand user intent
2. Check wallet balance and verify fund availability
3. Evaluate transaction feasibility and calculate costs
4. Assess risk level (low/medium/high) based on:
   - Transaction amount relative to balance
   - Recipient address reputation (if available)
   - Smart contract interaction complexity
   - Network gas costs
5. Generate structured transaction plans with reasoning
6. Determine if user approval is required (high-risk or large amounts)
7. Propose contingency plans for edge cases

DECISION FRAMEWORK:
- User Request → Analyze Intent → Check Wallet Balance → 
- Calculate Gas → Evaluate Risk → Execute/Reject → Log Outcome

RISK LEVELS:
- LOW: Transfers <1% of balance, known addresses, simple transactions
- MEDIUM: Transfers 1-10% of balance, standard transactions
- HIGH: Transfers >10% of balance, unknown addresses, complex contracts

SPENDING LIMITS:
- Respect pre-configured daily/transaction spending limits
- Reject transactions that exceed limits
- Suggest splitting large transactions if beneficial

OUTPUT FORMAT:
Always provide structured JSON output with:
- action: Type of transaction
- to_address: Recipient (if applicable)
- amount: Amount to transfer
- network: Target blockchain network
- risk_level: Your risk assessment
- estimated_gas: Gas cost estimate
- reasoning: Clear explanation of your decision
- requires_approval: true/false based on risk
- contingencies: Alternative plans if main plan fails

IMPORTANT:
- Be conservative with financial decisions
- Always explain your reasoning clearly
- Prioritize user safety and fund security
- Consider gas optimization across networks
- Never execute high-risk transactions without explicit approval

Available tools: {tool_names}

Think step-by-step and make well-reasoned financial decisions."""
    
    async def plan_transaction(
        self,
        context: DecisionContext,
        wallet_balance: Optional[float] = None,
        spending_limit: Optional[float] = None
    ) -> TransactionPlan:
        """
        Generate a structured transaction plan from user request
        
        Args:
            context: Decision context with user request
            wallet_balance: Current wallet balance in ETH
            spending_limit: Daily spending limit
        
        Returns:
            TransactionPlan with detailed decision
        """
        logger.info(f"Planning transaction for request: {context.request}")
        
        # Add financial context to the request
        enhanced_input = f"""User Request: {context.request}

Financial Context:
- Wallet Balance: {wallet_balance or 'Unknown'} ETH
- Daily Spending Limit: {spending_limit or 'No limit'} ETH
- Network: {context.network or 'sepolia'}
- Previous Decisions: {len(context.previous_decisions)} transactions in history

Analyze this request and generate a structured transaction plan."""
        
        # Create new context with enhanced input
        planning_context = DecisionContext(
            user_id=context.user_id,
            wallet_address=context.wallet_address,
            request=enhanced_input,
            wallet_balance=wallet_balance,
            network=context.network,
            previous_decisions=context.previous_decisions,
            metadata=context.metadata
        )
        
        # Process with agent
        response = await self.process(planning_context)
        
        # Parse response into TransactionPlan
        try:
            # Extract structured data from response
            result = response.result
            
            # If result is already a dict with transaction plan
            if isinstance(result, dict):
                plan = TransactionPlan(**result)
            else:
                # Try to parse from output text
                plan = self.output_parser.parse(str(result))
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to parse transaction plan: {e}")
            # Return safe fallback plan
            return TransactionPlan(
                action="reject",
                risk_level="high",
                reasoning=f"Could not generate safe plan: {str(e)}",
                requires_approval=True
            )
    
    async def analyze_financial_feasibility(
        self,
        plan: TransactionPlan,
        wallet_balance: float,
        spending_limit: Optional[float] = None,
        daily_spent: float = 0.0
    ) -> FinancialAnalysis:
        """
        Analyze if a transaction plan is financially feasible
        
        Args:
            plan: Proposed transaction plan
            wallet_balance: Current balance in ETH
            spending_limit: Daily spending limit
            daily_spent: Amount already spent today
        
        Returns:
            FinancialAnalysis with feasibility assessment
        """
        total_cost = (plan.amount or 0) + (plan.estimated_gas or 0.001)
        
        balance_sufficient = wallet_balance >= total_cost
        
        within_limit = True
        if spending_limit:
            remaining_limit = spending_limit - daily_spent
            within_limit = total_cost <= remaining_limit
        
        warnings = []
        recommendations = []
        
        # Generate warnings
        if not balance_sufficient:
            warnings.append(f"Insufficient balance: {wallet_balance} ETH < {total_cost} ETH required")
        
        if not within_limit:
            warnings.append(f"Exceeds daily spending limit: {total_cost} ETH > {spending_limit - daily_spent} ETH remaining")
        
        if total_cost > wallet_balance * 0.5:
            warnings.append("Transaction uses >50% of wallet balance - high risk")
        
        # Generate recommendations
        if not balance_sufficient:
            recommendations.append("Add funds to wallet or reduce transaction amount")
        
        if not within_limit:
            recommendations.append("Wait for daily limit to reset or increase spending limit")
        
        if plan.risk_level == "high":
            recommendations.append("Consider requesting human approval for high-risk transaction")
        
        # Suggest network switching if gas is high
        if plan.estimated_gas and plan.estimated_gas > 0.01:
            recommendations.append("Consider switching to a cheaper network (Polygon/Base)")
        
        can_execute = balance_sufficient and within_limit and plan.risk_level != "high"
        
        return FinancialAnalysis(
            can_execute=can_execute,
            balance_sufficient=balance_sufficient,
            within_spending_limit=within_limit,
            estimated_total_cost=total_cost,
            warnings=warnings,
            recommendations=recommendations
        )
    
    async def evaluate_risk(
        self,
        context: DecisionContext,
        to_address: Optional[str] = None,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluate risk level for a proposed transaction
        
        Returns risk assessment with score and factors
        """
        risk_factors = []
        risk_score = 0.0
        
        # Amount-based risk
        if amount and context.wallet_balance:
            percentage = (amount / context.wallet_balance) * 100
            if percentage > 50:
                risk_factors.append("High percentage of balance (>50%)")
                risk_score += 0.4
            elif percentage > 10:
                risk_factors.append("Significant percentage of balance (>10%)")
                risk_score += 0.2
        
        # Address-based risk
        if to_address:
            # Check if address is in known addresses (TODO: implement registry)
            if not to_address.startswith("0x") or len(to_address) != 42:
                risk_factors.append("Invalid address format")
                risk_score += 0.5
        
        # History-based risk
        if len(context.previous_decisions) < 5:
            risk_factors.append("Limited transaction history")
            risk_score += 0.1
        
        # Determine risk level
        if risk_score >= 0.5:
            risk_level = "high"
        elif risk_score >= 0.25:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "requires_approval": risk_level == "high"
        }