"""
Orchestrator Agent- LangGraph Multi-Agent Workflow (FR-002)

Implements the decision tree logic:
User Request → Analyze Intent → Check Wallet Balance → 
Calculate Gas → Evaluate Risk → Execute/Reject → Log Outcome

Uses LangGraph to coordinate:
- Planner Agent
- Executor Agent
- Evaluator Agent  
- Communicator Agent
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
import logging
from datetime import datetime

from .base import DecisionContext, AgentResponse
from .planner import PlannerAgent, TransactionPlan
from .executor import ExecutorAgent, ExecutionPlan, ExecutionResult
from .evaluator import EvaluatorAgent, TransactionOutcome
from .communicator import CommunicatorAgent

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State shared between agents in the workflow"""
    # Input
    user_request: str
    user_id: str
    wallet_address: str
    network: str
    
    # Context
    wallet_balance: Optional[float]
    spending_limit: Optional[float]
    daily_spent: float
    previous_decisions: List[Dict[str, Any]]
    
    # Workflow state
    current_step: str
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Agent outputs
    plan: Optional[Dict[str, Any]]
    execution_result: Optional[Dict[str, Any]]
    evaluation: Optional[Dict[str, Any]]
    api_responses: List[Dict[str, Any]]
    
    # Decision
    approved: bool
    final_result: Optional[Dict[str, Any]]
    error: Optional[str]


class OrchestratorAgent:
    """
    Orchestrates multi-agent workflow using LangGraph.
    
    Implements the decision framework from FR-002:
    1. Analyze user intent (Planner)
    2. Check wallet balance (Planner)
    3. Calculate gas costs (Planner)
    4. Evaluate risk (Planner)
    5. Execute transaction (Executor) or Reject
    6. Evaluate outcome (Evaluator)
    7. Log to memory
    """
    
    def __init__(
        self,
        planner: PlannerAgent,
        executor: ExecutorAgent,
        evaluator: EvaluatorAgent,
        communicator: CommunicatorAgent,
        blockchain_service: Any,
        memory_service: Any,
        websocket_manager: Optional[Any] = None
    ):
        self.planner = planner
        self.executor = executor
        self.evaluator = evaluator
        self.communicator = communicator
        self.blockchain_service = blockchain_service
        self.memory_service = memory_service
        self.websocket_manager = websocket_manager
        
        # Track pending approvals
        self.pending_approvals: Dict[str, AgentState] = {}
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow with decision tree logic.
        
        Workflow:
        START → analyze_intent → check_balance → calculate_gas → 
        evaluate_risk → [approve/reject] → execute_transaction → 
        evaluate_outcome → log_decision → END
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes for each step
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("check_balance", self._check_balance)
        workflow.add_node("calculate_gas", self._calculate_gas)
        workflow.add_node("evaluate_risk", self._evaluate_risk)
        workflow.add_node("execute_transaction", self._execute_transaction)
        workflow.add_node("evaluate_outcome", self._evaluate_outcome)
        workflow.add_node("log_decision", self._log_decision)
        workflow.add_node("reject_transaction", self._reject_transaction)
        
        # Define edges (workflow flow)
        workflow.set_entry_point("analyze_intent")
        
        workflow.add_edge("analyze_intent", "check_balance")
        workflow.add_edge("check_balance", "calculate_gas")
        workflow.add_edge("calculate_gas", "evaluate_risk")
        
        # Conditional edge: approve or reject
        workflow.add_conditional_edges(
            "evaluate_risk",
            self._should_approve,
            {
                "approve": "execute_transaction",
                "reject": "reject_transaction"
            }
        )
        
        workflow.add_edge("execute_transaction", "evaluate_outcome")
        workflow.add_edge("evaluate_outcome", "log_decision")
        workflow.add_edge("reject_transaction", "log_decision")
        workflow.add_edge("log_decision", END)
        
        return workflow
    
    async def _broadcast_update(self, event_type: str, data: Dict[str, Any]):
        """Broadcast workflow updates via WebSocket"""
        if self.websocket_manager:
            try:
                await self.websocket_manager.broadcast({
                    "type": event_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }, channel="agents")
            except Exception as e:
                logger.warning(f"Failed to broadcast update: {e}")
    
    async def request_manual_approval(
        self,
        request_id: str,
        state: AgentState,
        reason: str
    ) -> str:
        """
        Request manual approval for high-risk transaction.
        
        Implements workflow: "The OrchestratorAgent sees the high-risk score and flags
        the transaction for manual approval."
        
        Args:
            request_id: Unique identifier for this request
            state: Current workflow state
            reason: Reason for requiring approval
            
        Returns:
            approval_id that can be used to approve/reject
        """
        approval_id = f"approval_{request_id}_{int(datetime.now().timestamp())}"
        
        # Store pending approval
        self.pending_approvals[approval_id] = state
        
        # Broadcast approval request via WebSocket
        await self._broadcast_update("approval_required", {
            "approval_id": approval_id,
            "request_id": request_id,
            "user_request": state.get("user_request"),
            "plan": state.get("plan"),
            "reason": reason,
            "wallet_address": state.get("wallet_address")
        })
        
        logger.info(f"Manual approval requested: {approval_id}")
        return approval_id
    
    async def handle_approval_response(
        self,
        approval_id: str,
        approved: bool,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Handle user's response to approval request.
        
        Args:
            approval_id: The approval request ID
            approved: Whether user approved or rejected
            user_id: User making the decision
            
        Returns:
            Result of continuing workflow or rejection
        """
        if approval_id not in self.pending_approvals:
            return {
                "success": False,
                "error": "Approval request not found or expired"
            }
        
        state = self.pending_approvals[approval_id]
        
        # Broadcast approval response
        await self._broadcast_update("approval_response", {
            "approval_id": approval_id,
            "approved": approved,
            "user_id": user_id
        })
        
        if approved:
            logger.info(f"Transaction approved by user: {approval_id}")
            # Update state and continue workflow
            state["approved"] = True
            
            # Continue from execution step
            state = await self._execute_transaction(state)
            state = await self._evaluate_outcome(state)
            state = await self._log_decision(state)
            
            # Clean up
            del self.pending_approvals[approval_id]
            
            return {
                "success": True,
                "result": state.get("final_result"),
                "execution": state.get("execution_result")
            }
        else:
            logger.info(f"Transaction rejected by user: {approval_id}")
            state["approved"] = False
            state = await self._reject_transaction(state)
            state = await self._log_decision(state)
            
            # Clean up
            del self.pending_approvals[approval_id]
            
            return {
                "success": False,
                "result": state.get("final_result"),
                "reason": "Rejected by user"
            }
    
    async def request_clarification(
        self,
        request_id: str,
        state: AgentState,
        question: str
    ) -> str:
        """
        Request clarification from user for ambiguous requests.
        
        Implements workflow: "Instead of proceeding, the CommunicatorAgent is invoked.
        It formulates a clarifying question."
        
        Args:
            request_id: Unique identifier for this request
            state: Current workflow state
            question: Clarifying question to ask user
            
        Returns:
            clarification_id that can be used to provide answer
        """
        clarification_id = f"clarify_{request_id}_{int(datetime.now().timestamp())}"
        
        # Store pending clarification
        self.pending_approvals[clarification_id] = state
        
        # Broadcast clarification request
        await self._broadcast_update("clarification_required", {
            "clarification_id": clarification_id,
            "request_id": request_id,
            "question": question,
            "original_request": state.get("user_request")
        })
        
        logger.info(f"Clarification requested: {clarification_id}")
        return clarification_id
    
    async def handle_clarification_response(
        self,
        clarification_id: str,
        answer: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Handle user's clarification response and restart workflow.
        
        Args:
            clarification_id: The clarification request ID
            answer: User's answer to the question
            user_id: User providing the answer
            
        Returns:
            Result of restarting workflow with clarified request
        """
        if clarification_id not in self.pending_approvals:
            return {
                "success": False,
                "error": "Clarification request not found or expired"
            }
        
        state = self.pending_approvals[clarification_id]
        
        # Update request with clarification
        original_request = state.get("user_request", "")
        clarified_request = f"{original_request}. {answer}"
        
        # Clean up
        del self.pending_approvals[clarification_id]
        
        # Restart workflow with clarified request
        return await self.process_request(
            user_request=clarified_request,
            user_id=user_id,
            wallet_address=state.get("wallet_address", ""),
            network=state.get("network", "sepolia"),
            spending_limit=state.get("spending_limit")
        )
    
    async def process_request(
        self,
        user_request: str,
        user_id: str,
        wallet_address: str,
        network: str = "sepolia",
        spending_limit: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process user request through multi-agent workflow.
        
        Args:
            user_request: Natural language request
            user_id: User identifier
            wallet_address: Agent wallet address
            network: Target blockchain network
            spending_limit: Optional spending limit
        
        Returns:
            Final result with transaction outcome or rejection reason
        """
        logger.info(f"Orchestrating request: {user_request[:100]}...")
        
        # Initialize state
        initial_state: AgentState = {
            "user_request": user_request,
            "user_id": user_id,
            "wallet_address": wallet_address,
            "network": network,
            "wallet_balance": None,
            "spending_limit": spending_limit,
            "daily_spent": 0.0,
            "previous_decisions": [],
            "current_step": "start",
            "messages": [],
            "plan": None,
            "execution_result": None,
            "evaluation": None,
            "api_responses": [],
            "approved": False,
            "final_result": None,
            "error": None
        }
        
        # Run workflow
        try:
            final_state = await self.app.ainvoke(initial_state)
            
            return {
                "success": final_state.get("approved", False),
                "result": final_state.get("final_result"),
                "plan": final_state.get("plan"),
                "execution": final_state.get("execution_result"),
                "evaluation": final_state.get("evaluation"),
                "error": final_state.get("error"),
                "steps": [msg.content for msg in final_state.get("messages", [])]
            }
            
        except Exception as e:
            logger.error(f"Orchestration failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    # Workflow node implementations
    
    async def _analyze_intent(self, state: AgentState) -> AgentState:
        """Step 1: Analyze user intent with Planner"""
        logger.info("Step 1: Analyzing intent...")
        
        state["current_step"] = "analyze_intent"
        state["messages"].append(HumanMessage(content=f"Analyzing: {state['user_request']}"))
        
        try:
            context = DecisionContext(
                user_id=state["user_id"],
                wallet_address=state["wallet_address"],
                request=state["user_request"],
                network=state["network"],
                wallet_balance=state.get("wallet_balance")
            )
            
            response = await self.planner.process(context)
            
            state["messages"].append(AIMessage(content=f"Intent analyzed: {response.reasoning}"))
            
            return state
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            state["error"] = str(e)
            return state
    
    async def _check_balance(self, state: AgentState) -> AgentState:
        """Step 2: Check wallet balance"""
        logger.info("Step 2: Checking balance...")
        
        state["current_step"] = "check_balance"
        
        try:
            balance = await self.blockchain_service.get_balance(
                state["wallet_address"],
                state["network"]
            )
            
            state["wallet_balance"] = balance
            state["messages"].append(AIMessage(content=f"Balance: {balance} ETH"))
            
            logger.info(f"Wallet balance: {balance} ETH")
            
        except Exception as e:
            logger.warning(f"Balance check failed: {e}")
            state["wallet_balance"] = 0.0
        
        return state
    
    async def _calculate_gas(self, state: AgentState) -> AgentState:
        """Step 3: Calculate gas costs with Planner"""
        logger.info("Step 3: Calculating gas...")
        
        state["current_step"] = "calculate_gas"
        
        try:
            context = DecisionContext(
                user_id=state["user_id"],
                wallet_address=state["wallet_address"],
                request=state["user_request"],
                network=state["network"],
                wallet_balance=state["wallet_balance"]
            )
            
            plan = await self.planner.plan_transaction(
                context,
                wallet_balance=state["wallet_balance"],
                spending_limit=state.get("spending_limit")
            )
            
            state["plan"] = plan.dict()
            state["messages"].append(
                AIMessage(content=f"Plan: {plan.action}, Gas: {plan.estimated_gas} ETH, Risk: {plan.risk_level}")
            )
            
            logger.info(f"Transaction plan: {plan.action} with {plan.risk_level} risk")
            
        except Exception as e:
            logger.error(f"Gas calculation failed: {e}")
            state["error"] = str(e)
        
        return state
    
    async def _evaluate_risk(self, state: AgentState) -> AgentState:
        """Step 4: Evaluate risk with Planner"""
        logger.info("Step 4: Evaluating risk...")
        
        state["current_step"] = "evaluate_risk"
        
        if not state.get("plan"):
            state["approved"] = False
            state["error"] = "No plan available for risk evaluation"
            return state
        
        try:
            plan_dict = state["plan"]
            if not isinstance(plan_dict, dict):
                state["approved"] = False
                state["error"] = "Invalid plan format"
                return state
            
            plan = TransactionPlan(**plan_dict)
            
            # Broadcast risk evaluation update
            await self._broadcast_update("risk_evaluation", {
                "request": state["user_request"],
                "risk_level": plan.risk_level,
                "amount": plan.amount,
                "requires_approval": plan.requires_approval
            })
            
            # Analyze financial feasibility
            analysis = await self.planner.analyze_financial_feasibility(
                plan,
                wallet_balance=state.get("wallet_balance") or 0.0,
                spending_limit=state.get("spending_limit"),
                daily_spent=state.get("daily_spent", 0.0)
            )
            
            # Check for insufficient funds
            if not analysis.balance_sufficient:
                await self._broadcast_update("insufficient_funds", {
                    "required": (plan.amount or 0) + (plan.estimated_gas or 0),
                    "available": state.get("wallet_balance", 0),
                    "deficit": (plan.amount or 0) + (plan.estimated_gas or 0) - (state.get("wallet_balance") or 0)
                })
                state["approved"] = False
                state["error"] = f"Insufficient funds: need {(plan.amount or 0) + (plan.estimated_gas or 0)} ETH, have {state.get('wallet_balance', 0)} ETH"
                return state
            
            # Check if manual approval required (high-risk transaction)
            if plan.requires_approval or plan.risk_level == "high":
                reason = f"High-risk transaction: {plan.risk_level} risk level"
                if analysis.warnings:
                    reason += f". Warnings: {', '.join(analysis.warnings)}"
                
                # Don't auto-approve, let the API handler deal with manual approval
                state["approved"] = False
                state["requires_manual_approval"] = True
                state["approval_reason"] = reason
                
                state["messages"].append(AIMessage(content=f"Manual approval required: {reason}"))
                logger.info(f"Manual approval required: {reason}")
                return state
            
            # Auto-approve low-risk transactions
            state["approved"] = analysis.can_execute
            
            reasoning = f"Risk: {plan.risk_level}, Can execute: {analysis.can_execute}"
            if analysis.warnings:
                reasoning += f", Warnings: {', '.join(analysis.warnings)}"
            
            state["messages"].append(AIMessage(content=reasoning))
            
            await self._broadcast_update("risk_evaluated", {
                "approved": state["approved"],
                "risk_level": plan.risk_level,
                "reasoning": reasoning
            })
            
            logger.info(f"Risk evaluation: {'Approved' if state['approved'] else 'Rejected'}")
            
        except Exception as e:
            logger.error(f"Risk evaluation failed: {e}")
            state["approved"] = False
            state["error"] = str(e)
        
        return state
    
    def _should_approve(self, state: AgentState) -> str:
        """Conditional edge: determine if transaction should be approved"""
        return "approve" if state.get("approved", False) else "reject"
    
    async def _execute_transaction(self, state: AgentState) -> AgentState:
        """Step 5: Execute transaction with Executor"""
        logger.info("Step 5: Executing transaction...")
        
        state["current_step"] = "execute_transaction"
        
        if not state.get("plan"):
            state["error"] = "No plan available for execution"
            return state
        
        try:
            plan_dict = state["plan"]
            if not isinstance(plan_dict, dict):
                state["error"] = "Invalid plan format"
                return state
                
            plan = TransactionPlan(**plan_dict)
            
            # Broadcast execution start
            await self._broadcast_update("execution_started", {
                "action": plan.action,
                "to_address": plan.to_address,
                "amount": plan.amount
            })
            
            # Step 1: Log decision to IPFS and blockchain (FR-007)
            logger.info("Logging decision to IPFS and blockchain...")
            decision_data = {
                "transaction_plan": plan_dict,
                "risk_analysis": {
                    "risk_level": plan.risk_level,
                    "reasoning": plan.reasoning,
                    "estimated_gas": plan.estimated_gas
                },
                "timestamp": datetime.utcnow().isoformat(),
                "wallet_address": state["wallet_address"],
                "user_request": state["user_request"]
            }
            
            decision_hash, ipfs_cid, log_success = await self.executor.log_decision_on_chain(
                decision_data=decision_data,
                agent_wallet_address=state["wallet_address"],
                network=plan.network
            )
            
            if log_success:
                await self._broadcast_update("decision_logged", {
                    "decision_hash": decision_hash,
                    "ipfs_cid": ipfs_cid
                })
                logger.info(f"Decision logged: hash={decision_hash}, ipfs={ipfs_cid}")
            else:
                logger.warning("Decision logging failed, continuing anyway")
            
            # Step 2: Execute transaction
            exec_plan = ExecutionPlan(
                transaction_type=plan.action,
                to_address=plan.to_address or "0x0000000000000000000000000000000000000000",
                amount=plan.amount or 0.0,
                network=plan.network,
                gas_limit=int((plan.estimated_gas or 0.001) * 1e9)  # Convert to gas units
            )
            
            context = DecisionContext(
                user_id=state["user_id"],
                wallet_address=state["wallet_address"],
                request=state["user_request"],
                network=state["network"]
            )
            
            result = await self.executor.execute_with_retry(
                context,
                exec_plan,
                state["wallet_address"]
            )
            
            state["execution_result"] = {
                "success": result.success,
                "transaction_hash": result.transaction_hash,
                "gas_used": result.gas_used,
                "status": result.status.value,
                "error": result.error,
                "decision_hash": decision_hash if log_success else None,
                "ipfs_cid": ipfs_cid if log_success else None
            }
            
            if result.success:
                await self._broadcast_update("transaction_confirmed", {
                    "transaction_hash": result.transaction_hash,
                    "gas_used": result.gas_used,
                    "decision_hash": decision_hash,
                    "ipfs_cid": ipfs_cid
                })
                state["messages"].append(
                    AIMessage(content=f"Transaction executed: {result.transaction_hash}")
                )
                logger.info(f"Transaction successful: {result.transaction_hash}")
            else:
                await self._broadcast_update("transaction_failed", {
                    "error": result.error,
                    "status": result.status.value
                })
                state["messages"].append(
                    AIMessage(content=f"Transaction failed: {result.error}")
                )
                logger.warning(f"Transaction failed: {result.error}")
            
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            await self._broadcast_update("execution_error", {
                "error": str(e)
            })
            state["execution_result"] = {
                "success": False,
                "error": str(e)
            }
        
        return state
    
    async def _evaluate_outcome(self, state: AgentState) -> AgentState:
        """Step 6: Evaluate outcome with Evaluator"""
        logger.info("Step 6: Evaluating outcome...")
        
        state["current_step"] = "evaluate_outcome"
        
        if not state.get("execution_result") or not state.get("plan"):
            return state
        
        try:
            context = DecisionContext(
                user_id=state["user_id"],
                wallet_address=state["wallet_address"],
                request=state["user_request"],
                network=state["network"]
            )
            
            outcome = await self.evaluator.evaluate_transaction(
                context,
                state["execution_result"],
                state["plan"]
            )
            
            state["evaluation"] = {
                "criteria": outcome.criteria.value,
                "success": outcome.success,
                "gas_efficiency": outcome.gas_efficiency,
                "lessons_learned": outcome.lessons_learned,
                "recommendation": outcome.recommendation
            }
            
            state["messages"].append(
                AIMessage(content=f"Evaluation: {outcome.criteria.value}, {outcome.recommendation}")
            )
            
            logger.info(f"Evaluation: {outcome.criteria.value}")
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            state["evaluation"] = {"error": str(e)}
        
        return state
    
    async def _reject_transaction(self, state: AgentState) -> AgentState:
        """Handle transaction rejection"""
        logger.info("Transaction rejected")
        
        state["current_step"] = "reject_transaction"
        
        plan = state.get("plan", {})
        reason = plan.get("reasoning", "Risk too high or insufficient funds")
        
        state["final_result"] = {
            "action": "rejected",
            "reason": reason,
            "plan": plan
        }
        
        state["messages"].append(
            AIMessage(content=f"Transaction rejected: {reason}")
        )
        
        return state
    
    async def _log_decision(self, state: AgentState) -> AgentState:
        """Step 7: Log decision to memory and blockchain"""
        logger.info("Step 7: Logging decision...")
        
        state["current_step"] = "log_decision"
        
        try:
            # Compile final result
            if not state.get("final_result"):
                state["final_result"] = {
                    "action": "executed" if state.get("execution_result", {}).get("success") else "failed",
                    "plan": state.get("plan"),
                    "execution": state.get("execution_result"),
                    "evaluation": state.get("evaluation"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Store in memory
            if self.memory_service:
                await self.memory_service.store(
                    wallet_address=state["wallet_address"],
                    agent_type="orchestrator",
                    request=state["user_request"],
                    response=state["final_result"],
                    reasoning="\n".join([msg.content for msg in state["messages"]]),
                    timestamp=datetime.utcnow()
                )
            
            state["messages"].append(AIMessage(content="Decision logged"))
            logger.info("Decision logged successfully")
            
        except Exception as e:
            logger.error(f"Logging failed: {e}")
        
        return state