# Agent API endpoints implementing FR-001, FR-002, FR-003
# Handles agent orchestration, decision-making, and memory management

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any, AsyncGenerator
import time
from datetime import datetime
import logging
import hashlib
import json
import os
import asyncio


def serialize_for_json(obj):
    """Recursively serialize objects for JSON, converting datetime to ISO format"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return serialize_for_json(obj.__dict__)
    else:
        return obj

from app.models.agent import (
    AgentRequest,
    AgentResponse,
    AgentDecision,
    AgentMemoryQuery,
    AgentMemoryResponse,
    AgentHealth,
    CreateAgentRequest,
    AgentInfo,
    AgentStatus,
    AgentType
)
from app.agents.orchestrator import OrchestratorAgent
from app.agents.planner import PlannerAgent
from app.agents.executor import ExecutorAgent
from app.agents.evaluator import EvaluatorAgent
from app.agents.communicator import CommunicatorAgent
from app.agents.base import AgentConfig, DecisionContext
from app.agents.tools import get_planner_tools, get_executor_tools, get_evaluator_tools, get_communicator_tools
from app.memory.vector_store import MemoryService
from app.database.service import DatabaseService
from app.blockchain import WalletManager, Web3Provider, NetworkType
from app.config import get_settings
from app.services.payment_service import PaymentService
from app.api.websocket import ConnectionManager

# LangChain imports for LLM initialization
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

# Load configuration
settings = get_settings()

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Global agent instances (in production, use dependency injection)
_orchestrator: Optional[OrchestratorAgent] = None
_memory_service: Optional[MemoryService] = None
_db_service: Optional[DatabaseService] = None
_blockchain_service: Optional[WalletManager] = None
_llm: Optional[BaseChatModel] = None
_payment_service: Optional[PaymentService] = None
_websocket_manager: Optional[ConnectionManager] = None
_agent_registry: Dict[str, Any] = {}
_agent_metrics: Dict[str, Dict[str, Any]] = {
    "planner": {"requests": 0, "successes": 0, "start_time": time.time()},
    "executor": {"requests": 0, "successes": 0, "start_time": time.time()},
    "evaluator": {"requests": 0, "successes": 0, "start_time": time.time()},
    "communicator": {"requests": 0, "successes": 0, "start_time": time.time()},
}


def get_llm() -> BaseChatModel:
    """Get or create LLM instance based on configuration"""
    global _llm
    if _llm is None:
        llm_config = settings.llm
        
        if llm_config.provider.lower() == "groq":
            if not llm_config.groq_api_key:
                raise ValueError("GROQ_API_KEY not set in environment")
            _llm = ChatGroq(
                groq_api_key=llm_config.groq_api_key,
                model_name=llm_config.model,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens
            )
            logger.info(f"Initialized Groq LLM with model: {llm_config.model}")
        elif llm_config.provider.lower() == "google":
            if not llm_config.google_api_key:
                raise ValueError("GOOGLE_API_KEY not set in environment")
            _llm = ChatGoogleGenerativeAI(
                google_api_key=llm_config.google_api_key,
                model=llm_config.model,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens
            )
            logger.info(f"Initialized Google LLM with model: {llm_config.model}")
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_config.provider}")
    
    if _llm is None:
        raise RuntimeError("Failed to initialize LLM")
    
    return _llm


def get_blockchain_service() -> Optional[WalletManager]:
    """Get or create blockchain service instance"""
    global _blockchain_service
    if _blockchain_service is None:
        try:
            # Get settings
            settings = get_settings()
            
            # Initialize Web3 provider for Sepolia (default testnet)
            provider = Web3Provider()
            provider.connect(
                NetworkType.SEPOLIA,
                rpc_url=settings.blockchain.sepolia_rpc_url
            )
            
            # Create WalletManager from private key if available
            if settings.blockchain.agent_private_key:
                _blockchain_service = WalletManager.from_private_key(
                    settings.blockchain.agent_private_key
                )
                logger.info(f"Initialized blockchain service with Sepolia testnet (RPC: {settings.blockchain.sepolia_rpc_url[:50]}...)")
            else:
                logger.warning("No agent private key configured, blockchain service will not be available")
                _blockchain_service = None
                
        except Exception as e:
            logger.error(f"Failed to initialize blockchain service: {e}")
            # Return None for development - some features may not work without blockchain
            _blockchain_service = None
    return _blockchain_service


def get_payment_service() -> PaymentService:
    """Get or create payment service instance"""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
        logger.info("Initialized payment service")
    return _payment_service


def get_websocket_manager() -> ConnectionManager:
    """Get or create websocket manager instance"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = ConnectionManager()
        logger.info("Initialized WebSocket manager")
    return _websocket_manager


def get_orchestrator() -> OrchestratorAgent:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        try:
            # Get shared services
            llm = get_llm()
            memory_service = get_memory_service()
            blockchain_service = get_blockchain_service()
            payment_service = get_payment_service()
            websocket_manager = get_websocket_manager()
            
            # Initialize tools for each agent type
            planner_tools = get_planner_tools(blockchain_service)
            executor_tools = get_executor_tools(blockchain_service)
            evaluator_tools = get_evaluator_tools(blockchain_service)
            communicator_tools = get_communicator_tools(payment_service)
            
            # Create sub-agents with proper initialization
            planner = PlannerAgent(
                llm=llm,
                tools=planner_tools,
                config=AgentConfig(
                    agent_type="planner",
                    temperature=0.3,
                    max_iterations=8
                ),
                memory_service=memory_service
            )
            
            executor = ExecutorAgent(
                llm=llm,
                tools=executor_tools,
                config=AgentConfig(
                    agent_type="executor",
                    temperature=0.1,
                    max_iterations=5
                ),
                memory_service=memory_service,
                blockchain_service=blockchain_service
            )
            
            evaluator = EvaluatorAgent(
                llm=llm,
                tools=evaluator_tools,
                config=AgentConfig(
                    agent_type="evaluator",
                    temperature=0.2,
                    max_iterations=5
                ),
                memory_service=memory_service,
                blockchain_service=blockchain_service
            )
            
            communicator = CommunicatorAgent(
                llm=llm,
                tools=communicator_tools,
                config=AgentConfig(
                    agent_type="communicator",
                    temperature=0.5,
                    max_iterations=8
                ),
                memory_service=memory_service,
                payment_service=payment_service
            )
            
            # Create orchestrator with all sub-agents
            _orchestrator = OrchestratorAgent(
                planner=planner,
                executor=executor,
                evaluator=evaluator,
                communicator=communicator,
                blockchain_service=blockchain_service,
                memory_service=memory_service,
                websocket_manager=websocket_manager
            )
            
            logger.info("Initialized OrchestratorAgent with all sub-agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to initialize agent system: {str(e)}")
    
    return _orchestrator


def get_memory_service() -> MemoryService:
    """Get or create memory service instance"""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service


def get_db_service() -> DatabaseService:
    """Get or create database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


@router.post("/request", response_model=AgentResponse, summary="Process agent request (FR-001)")
async def process_agent_request(request: AgentRequest, background_tasks: BackgroundTasks):
    """
    Process a natural language request through the LangChain agent system.
    
    The agent will:
    1. Check if the request is clear (if not, request clarification)
    2. Parse the natural language input
    3. Determine the appropriate action
    4. Evaluate risk
    5. For high-risk: request manual approval
    6. For low-risk: execute automatically
    7. Return the decision/result
    
    Implements FR-001: LangChain Agent Orchestration
    """
    start_time = time.time()
    
    try:
        # Get services
        orchestrator = get_orchestrator()
        memory_service = get_memory_service()
        blockchain_service = get_blockchain_service()
        
        # Update metrics
        _agent_metrics["planner"]["requests"] += 1
        
        # Process request through orchestrator
        logger.info(f"Processing agent request: {request.request[:100]}")
        
        # Step 1: Check request clarity using the orchestrator's communicator
        communicator = orchestrator.communicator
        
        is_clear, missing_info = await communicator.check_request_clarity(request.request)
        
        if not is_clear:
            # Request clarification
            question = await communicator.formulate_clarifying_question(
                context=DecisionContext(
                    user_id=request.user_id or "default",
                    wallet_address=getattr(request, "wallet_address", "default"),
                    request=request.request
                ),
                ambiguous_request=request.request,
                missing_information=missing_info
            )
            
            execution_time = time.time() - start_time
            
            return AgentResponse(
                success=False,
                message="Request requires clarification",
                decision=AgentDecision(
                    decision_id=f"clarify_{int(time.time())}",
                    intent="clarification_required",
                    action_type="clarification",
                    parameters={"question": question, "missing": missing_info},
                    reasoning=f"The request is ambiguous. Missing: {', '.join(missing_info)}",
                    risk_score=0.0,
                    estimated_cost=0.0,
                    requires_approval=False
                ),
                execution_time=execution_time,
                agent_status=AgentStatus.WAITING
            )
        
        # Step 2: Use planner agent from orchestrator for initial decision
        planner = orchestrator.planner
        
        # Prepare context from request
        decision_context = DecisionContext(
            user_id=request.user_id or "default",
            wallet_address=getattr(request, "wallet_address", "default"),
            request=request.request,
            metadata=request.context or {}
        )
        
        # Process the request through the planner agent (this calls the LLM)
        planner_response = await planner.process(decision_context)
        
        if not planner_response.success:
            execution_time = time.time() - start_time
            return AgentResponse(
                success=False,
                message=f"Planner failed: {planner_response.error}",
                decision=None,
                execution_time=execution_time,
                agent_status=AgentStatus.ERROR
            )
        
        # Extract decision details from planner response
        planner_result = planner_response.result.get("response", "")
        
        # Parse the planner's output to determine risk and action
        # For now, use simple heuristics - TODO: improve with structured output
        risk_score = 0.3  # Default medium-low risk
        if any(word in planner_result.lower() for word in ["high risk", "dangerous", "unsafe", "warning"]):
            risk_score = 0.8
        elif any(word in planner_result.lower() for word in ["medium risk", "caution", "careful"]):
            risk_score = 0.5
        
        # Determine if it's a transaction
        is_transaction = any(word in request.request.lower() for word in ["send", "transfer", "pay", "swap"])
        
        # Calculate accurate estimated cost if it's a transaction
        estimated_cost = 0.0
        if is_transaction:
            # Extract amount from request (simple regex for now)
            import re
            amount_match = re.search(r'(\d+\.?\d*)\s*(eth|ether|sepolia|token)?', request.request.lower())
            transaction_amount = float(amount_match.group(1)) if amount_match else 0.0
            
            # Estimate gas cost (21000 gas for simple transfer)
            base_gas = 21000
            # Get current gas price from blockchain service if available
            try:
                if blockchain_service and hasattr(blockchain_service, 'web3_provider'):
                    provider = blockchain_service.web3_provider
                    if provider and hasattr(provider, '_connections') and NetworkType.SEPOLIA in provider._connections:
                        web3 = provider._connections[NetworkType.SEPOLIA]
                        gas_price_wei = web3.eth.gas_price
                        gas_cost_eth = (base_gas * gas_price_wei) / 1e18
                        estimated_cost = transaction_amount + gas_cost_eth
                        logger.info(f"Calculated gas cost: {gas_cost_eth} ETH (gas price: {gas_price_wei} wei)")
                    else:
                        # Fallback: estimate ~20 Gwei gas price
                        gas_cost_eth = (base_gas * 20e9) / 1e18  # 20 Gwei
                        estimated_cost = transaction_amount + gas_cost_eth
                else:
                    # Fallback: estimate ~20 Gwei gas price
                    gas_cost_eth = (base_gas * 20e9) / 1e18  # 20 Gwei
                    estimated_cost = transaction_amount + gas_cost_eth
            except Exception as gas_error:
                logger.warning(f"Could not fetch gas price: {gas_error}, using fallback")
                gas_cost_eth = (base_gas * 20e9) / 1e18  # 20 Gwei fallback
                estimated_cost = transaction_amount + gas_cost_eth
        
        # Create decision hash for tracking
        decision_id = f"dec_{int(time.time())}_{hashlib.md5(request.request.encode()).hexdigest()[:8]}"
        
        # Prepare decision response
        agent_decision = AgentDecision(
            decision_id=decision_id,
            intent=f"Process: {request.request[:50]}",
            action_type="transaction" if is_transaction else "query",
            parameters={
                "query": request.request,
                "risk_score": risk_score,
                "planner_analysis": planner_result[:500],
                "estimated_gas_cost": gas_cost_eth if is_transaction else 0.0,
                "transaction_amount": transaction_amount if is_transaction else 0.0
            },
            reasoning=planner_response.reasoning,
            risk_score=risk_score,
            estimated_cost=estimated_cost,
            requires_approval=risk_score > 0.6
        )
        
        # If high-risk, return decision for manual approval
        if agent_decision.requires_approval:
            logger.info(f"High-risk transaction detected: {decision_id}")
            
            execution_time = time.time() - start_time
            
            return AgentResponse(
                success=True,
                message="High-risk transaction requires manual approval",
                decision=agent_decision,
                execution_time=execution_time,
                agent_status=AgentStatus.WAITING
            )
        
        # Low-risk transaction - execute automatically using the executor agent
        if is_transaction:
            logger.info(f"Executing low-risk transaction: {decision_id}")
            
            executor = orchestrator.executor
            
            # Execute the transaction through the executor agent
            executor_response = await executor.process(
                decision_context,
                additional_input=f"Execute this transaction based on planner's analysis: {planner_result[:200]}"
            )
            
            if not executor_response.success:
                execution_time = time.time() - start_time
                return AgentResponse(
                    success=False,
                    message=f"Transaction execution failed: {executor_response.error}",
                    decision=agent_decision,
                    execution_time=execution_time,
                    agent_status=AgentStatus.ERROR
                )
            
            # Extract executor response and format it nicely
            executor_result = executor_response.result.get('response', '')
            
            # Update decision with execution results
            agent_decision.parameters["execution_result"] = {
                "raw_response": executor_result,
                "status": "executed",
                "agent_response": executor_response.result
            }
            
            # Format a structured message for the frontend
            message = f"""**Transaction Executed Successfully**

{executor_result}

**Summary:**
- Transaction submitted to blockchain
- Decision ID: {decision_id}
- Risk Level: {int(risk_score * 100)}%
- Estimated Total Cost: {estimated_cost:.6f} ETH

The transaction has been processed by the Executor agent and submitted to the blockchain. Check the execution details above for transaction hash and confirmation status."""
            
            agent_status = AgentStatus.IDLE
            
        else:
            # Query/informational request - just return the planner's analysis
            message = f"""**Request Processed**

{planner_result}

**Summary:**
- Request Type: Informational Query
- Decision ID: {decision_id}
- Processing Time: {time.time() - start_time:.2f}s

The Planner agent has analyzed your request and provided the response above."""
            agent_status = AgentStatus.IDLE
        
        # Store in memory
        try:
            await memory_service.store(
                wallet_address=decision_context.wallet_address or "default",
                agent_type="planner",
                request=request.request,
                response=agent_decision.dict(),
                reasoning=agent_decision.reasoning,
                timestamp=datetime.now()
            )
        except Exception as mem_error:
            logger.warning(f"Failed to store in memory: {mem_error}")
        
        execution_time = time.time() - start_time
        _agent_metrics["planner"]["successes"] += 1
        
        logger.info(f"Request processed successfully in {execution_time:.3f}s")
        
        return AgentResponse(
            success=True,
            message=message,
            decision=agent_decision,
            execution_time=execution_time,
            agent_status=agent_status
        )
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        execution_time = time.time() - start_time
        return AgentResponse(
            success=False,
            message=f"Error processing request: {str(e)}",
            decision=None,
            execution_time=execution_time,
            agent_status=AgentStatus.ERROR
        )


@router.post("/request/stream", summary="Process agent request with streaming (FR-001)")
async def process_agent_request_stream(request: AgentRequest):
    """
    Process a natural language request with streaming response.
    
    Returns Server-Sent Events (SSE) stream with:
    - status: Progress updates
    - chunk: Message chunks as they're generated
    - decision: Final decision object
    - done: Final completion
    """
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        start_time = time.time()
        
        try:
            # Get services
            orchestrator = get_orchestrator()
            memory_service = get_memory_service()
            blockchain_service = get_blockchain_service()
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing your request...'})}\n\n"
            await asyncio.sleep(0.1)  # Small delay for better UX
            
            # Step 1: Check request clarity
            communicator = orchestrator.communicator
            is_clear, missing_info = await communicator.check_request_clarity(request.request)
            
            if not is_clear:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Request needs clarification...'})}\n\n"
                
                question = await communicator.formulate_clarifying_question(
                    context=DecisionContext(
                        user_id=request.user_id or "default",
                        wallet_address=getattr(request, "wallet_address", "default"),
                        request=request.request
                    ),
                    ambiguous_request=request.request,
                    missing_information=missing_info
                )
                
                # Send clarification needed
                clarification_response = {
                    'type': 'done',
                    'success': False,
                    'message': 'Request requires clarification',
                    'decision': {
                        'decision_id': f"clarify_{int(time.time())}",
                        'requires_approval': False,
                        'parameters': {'question': question, 'missing': missing_info}
                    }
                }
                yield f"data: {json.dumps(clarification_response)}\n\n"
                return
            
            # Step 2: Process with planner
            yield f"data: {json.dumps({'type': 'status', 'message': 'Planning your request...'})}\n\n"
            
            planner = orchestrator.planner
            decision_context = DecisionContext(
                user_id=request.user_id or "default",
                wallet_address=getattr(request, "wallet_address", "default"),
                request=request.request,
                metadata=request.context or {}
            )
            
            planner_response = await planner.process(decision_context)
            
            if not planner_response.success:
                error_response = {
                    'type': 'done',
                    'success': False,
                    'message': f"Planner failed: {planner_response.error}",
                    'execution_time': time.time() - start_time
                }
                yield f"data: {json.dumps(error_response)}\n\n"
                return
            
            planner_result = planner_response.result.get("response", "")
            
            # Calculate risk and cost
            yield f"data: {json.dumps({'type': 'status', 'message': 'Evaluating risk...'})}\n\n"
            
            risk_score = 0.3
            if any(word in planner_result.lower() for word in ["high risk", "dangerous", "unsafe", "warning"]):
                risk_score = 0.8
            elif any(word in planner_result.lower() for word in ["medium risk", "caution", "careful"]):
                risk_score = 0.5
            
            is_transaction = any(word in request.request.lower() for word in ["send", "transfer", "pay", "swap"])
            
            # Calculate cost
            estimated_cost = 0.0
            transaction_amount = 0.0
            gas_cost_eth = 0.0
            
            if is_transaction:
                import re
                amount_match = re.search(r'(\d+\.?\d*)\s*(eth|ether|sepolia|token)?', request.request.lower())
                transaction_amount = float(amount_match.group(1)) if amount_match else 0.0
                
                base_gas = 21000
                try:
                    if blockchain_service and hasattr(blockchain_service, 'web3_provider'):
                        provider = blockchain_service.web3_provider
                        if provider and hasattr(provider, '_connections') and NetworkType.SEPOLIA in provider._connections:
                            web3 = provider._connections[NetworkType.SEPOLIA]
                            gas_price_wei = web3.eth.gas_price
                            gas_cost_eth = (base_gas * gas_price_wei) / 1e18
                            estimated_cost = transaction_amount + gas_cost_eth
                        else:
                            gas_cost_eth = (base_gas * 20e9) / 1e18
                            estimated_cost = transaction_amount + gas_cost_eth
                    else:
                        gas_cost_eth = (base_gas * 20e9) / 1e18
                        estimated_cost = transaction_amount + gas_cost_eth
                except Exception:
                    gas_cost_eth = (base_gas * 20e9) / 1e18
                    estimated_cost = transaction_amount + gas_cost_eth
            
            decision_id = f"dec_{int(time.time())}_{hashlib.md5(request.request.encode()).hexdigest()[:8]}"
            
            agent_decision = {
                'decision_id': decision_id,
                'intent': f"Process: {request.request[:50]}",
                'action_type': "transaction" if is_transaction else "query",
                'parameters': {
                    'query': request.request,
                    'risk_score': risk_score,
                    'planner_analysis': planner_result[:500],
                    'estimated_gas_cost': gas_cost_eth,
                    'transaction_amount': transaction_amount
                },
                'reasoning': planner_response.reasoning,
                'risk_score': risk_score,
                'estimated_cost': estimated_cost,
                'requires_approval': risk_score > 0.6
            }
            
            # Check if approval needed
            if agent_decision['requires_approval']:
                yield f"data: {json.dumps({'type': 'status', 'message': 'High-risk transaction detected...'})}\n\n"
                
                # Stream the planner result in chunks
                for i in range(0, len(planner_result), 50):
                    chunk = planner_result[i:i+50]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.03)  # Simulate streaming
                
                final_message = f"\n\n**Summary:**\n- Decision ID: {decision_id}\n- Risk Level: {int(risk_score * 100)}%\n- Estimated Cost: {estimated_cost:.6f} ETH\n\n⚠️ This transaction requires manual approval."
                
                for i in range(0, len(final_message), 50):
                    chunk = final_message[i:i+50]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.03)
                
                done_response = {
                    'type': 'done',
                    'success': True,
                    'decision': serialize_for_json(agent_decision),
                    'execution_time': time.time() - start_time
                }
                yield f"data: {json.dumps(done_response)}\n\n"
                return
            
            # Low-risk - execute if transaction
            if is_transaction:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Executing transaction...'})}\n\n"
                
                executor = orchestrator.executor
                executor_response = await executor.process(
                    decision_context,
                    additional_input=f"Execute this transaction based on planner's analysis: {planner_result[:200]}"
                )
                
                if not executor_response.success:
                    error_response = {
                        'type': 'done',
                        'success': False,
                        'message': f"Transaction execution failed: {executor_response.error}",
                        'decision': agent_decision,
                        'execution_time': time.time() - start_time
                    }
                    yield f"data: {json.dumps(error_response)}\n\n"
                    return
                
                executor_result = executor_response.result.get('response', '')
                
                # Update decision
                agent_decision['parameters']['execution_result'] = {
                    'raw_response': executor_result,
                    'status': 'executed',
                    'agent_response': executor_response.result
                }
                
                # Stream the response
                header = "**Transaction Executed Successfully**\n\n"
                for i in range(0, len(header), 20):
                    chunk = header[i:i+20]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.02)
                
                for i in range(0, len(executor_result), 50):
                    chunk = executor_result[i:i+50]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.03)
                
                summary = f"\n\n**Summary:**\n- Transaction submitted to blockchain\n- Decision ID: {decision_id}\n- Risk Level: {int(risk_score * 100)}%\n- Estimated Total Cost: {estimated_cost:.6f} ETH\n\nThe transaction has been processed by the Executor agent and submitted to the blockchain."
                
                for i in range(0, len(summary), 50):
                    chunk = summary[i:i+50]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.03)
                
            else:
                # Query - stream planner result
                header = "**Request Processed**\n\n"
                for i in range(0, len(header), 20):
                    chunk = header[i:i+20]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.02)
                
                for i in range(0, len(planner_result), 50):
                    chunk = planner_result[i:i+50]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.03)
                
                summary = f"\n\n**Summary:**\n- Request Type: Informational Query\n- Decision ID: {decision_id}\n- Processing Time: {time.time() - start_time:.2f}s"
                
                for i in range(0, len(summary), 50):
                    chunk = summary[i:i+50]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.03)
            
            # Store in memory
            try:
                await memory_service.store(
                    wallet_address=decision_context.wallet_address or "default",
                    agent_type="planner",
                    request=request.request,
                    response=agent_decision,
                    reasoning=agent_decision['reasoning'],
                    timestamp=datetime.now()
                )
            except Exception as mem_error:
                logger.warning(f"Failed to store in memory: {mem_error}")
            
            # Send final done event
            done_response = {
                'type': 'done',
                'success': True,
                'decision': serialize_for_json(agent_decision),
                'execution_time': time.time() - start_time
            }
            yield f"data: {json.dumps(done_response)}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=True)
            error_response = {
                'type': 'done',
                'success': False,
                'message': f"Error processing request: {str(e)}",
                'execution_time': time.time() - start_time
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/decision/{decision_id}", response_model=AgentDecision, summary="Get decision details (FR-002)")
async def get_decision(decision_id: str):
    """
    Retrieve details of a specific agent decision.
    
    Implements FR-002: Decision Logic Framework
    """
    try:
        db_service = get_db_service()
        await db_service.connect()
        
        # Query decision from database - decisions is an async property
        decision_repo_coro = db_service.decisions
        decision_repo = await decision_repo_coro
        decision = await decision_repo.find_by_id(decision_id)
        
        if not decision:
            raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
        
        # Convert to response model
        return AgentDecision(
            decision_id=decision.id,
            intent=decision.action,
            action_type=decision.action.split(":")[0] if ":" in decision.action else "transaction",
            parameters=decision.parameters or {},
            reasoning=decision.reasoning,
            risk_score=decision.confidence / 100.0,  # Convert confidence to risk score
            estimated_cost=0.001,  # Could be stored in parameters
            requires_approval=decision.status == "PENDING"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving decision: {str(e)}")
    finally:
        await db_service.disconnect()


@router.post("/memory/query", response_model=AgentMemoryResponse, summary="Query agent memory (FR-003)")
async def query_agent_memory(query: AgentMemoryQuery):
    """
    Query the agent's memory system using ChromaDB vector search.
    
    Returns relevant past interactions and decisions based on semantic similarity.
    
    Implements FR-003: Memory and Context Management
    """
    try:
        memory_service = get_memory_service()
        
        # Query memory with filters
        results = await memory_service.query(
            query=query.query,
            wallet_address=getattr(query, "wallet_address", None),
            agent_type=query.agent_type.value if query.agent_type else None,
            limit=query.limit or 5
        )
        
        # Convert to response format
        from app.models.agent import AgentMemoryEntry
        memories = []
        for result in results:
            memories.append(AgentMemoryEntry(
                entry_id=result["metadata"].get("id", "unknown"),
                content=result["content"],
                agent_type=AgentType(result["metadata"].get("agent_type", "planner")),
                timestamp=datetime.fromisoformat(result["metadata"]["timestamp"]),
                metadata=result.get("metadata", {})
            ))
        
        return AgentMemoryResponse(
            memories=memories,
            total=len(memories)
        )
        
    except Exception as e:
        logger.error(f"Error querying memory: {e}", exc_info=True)
        return AgentMemoryResponse(
            memories=[],
            total=0
        )


@router.post("/memory/store", summary="Store in agent memory (FR-003)")
async def store_in_memory(content: str, agent_type: AgentType, metadata: Optional[dict] = None):
    """
    Store a new entry in the agent's memory system.
    
    Implements FR-003: Memory and Context Management
    """
    try:
        memory_service = get_memory_service()
        
        # Store in memory
        entry_id = await memory_service.store(
            wallet_address=metadata.get("wallet_address", "default") if metadata else "default",
            agent_type=agent_type.value,
            request=content,
            response={"stored": True},
            reasoning="Manual memory storage",
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        return {
            "success": True,
            "entry_id": entry_id,
            "message": "Memory stored successfully"
        }
        
    except Exception as e:
        logger.error(f"Error storing memory: {e}", exc_info=True)
        return {
            "success": False,
            "entry_id": f"mem_{int(time.time())}",
            "message": f"Error storing memory: {str(e)}"
        }


@router.get("/health", response_model=List[AgentHealth], summary="Get agent health status")
async def get_agent_health():
    """
    Get health and status information for all active agents.
    
    Returns metrics including uptime, request count, and success rate.
    """
    try:
        health_status = []
        
        for agent_name, metrics in _agent_metrics.items():
            uptime = time.time() - metrics["start_time"]
            total_requests = metrics["requests"]
            success_rate = metrics["successes"] / total_requests if total_requests > 0 else 1.0
            
            health_status.append(AgentHealth(
                agent_type=AgentType(agent_name),
                status=AgentStatus.IDLE,
                uptime=uptime,
                total_requests=total_requests,
                success_rate=success_rate,
                last_active=datetime.now()
            ))
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error getting agent health: {e}", exc_info=True)
        # Return default health for all agents
        return [
            AgentHealth(
                agent_type=agent_type,
                status=AgentStatus.IDLE,
                uptime=0.0,
                total_requests=0,
                success_rate=1.0,
                last_active=datetime.now()
            )
            for agent_type in [AgentType.PLANNER, AgentType.EXECUTOR, AgentType.EVALUATOR, AgentType.COMMUNICATOR]
        ]


@router.post("/create", response_model=AgentInfo, summary="Create new agent instance")
async def create_agent(request: CreateAgentRequest):
    """
    Create a new agent instance with specified configuration.
    
    Useful for spinning up specialized agents for specific tasks.
    """
    try:
        agent_id = f"agent_{int(time.time())}_{request.agent_type.value}"
        
        # Register agent in global registry
        _agent_registry[agent_id] = {
            "type": request.agent_type,
            "name": request.name,
            "config": request.config,
            "created_at": datetime.now(),
            "status": AgentStatus.IDLE
        }
        
        # Initialize metrics for this agent if needed
        if request.agent_type.value not in _agent_metrics:
            _agent_metrics[request.agent_type.value] = {
                "requests": 0,
                "successes": 0,
                "start_time": time.time()
            }
        
        logger.info(f"Created new agent: {agent_id} ({request.agent_type.value})")
        
        return AgentInfo(
            agent_id=agent_id,
            agent_type=request.agent_type,
            name=request.name,
            status=AgentStatus.IDLE,
            created_at=datetime.now(),
            config=request.config
        )
        
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")


@router.get("/{agent_id}", response_model=AgentInfo, summary="Get agent information")
async def get_agent_info(agent_id: str):
    """
    Get detailed information about a specific agent instance.
    """
    try:
        if agent_id not in _agent_registry:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        agent_data = _agent_registry[agent_id]
        
        return AgentInfo(
            agent_id=agent_id,
            agent_type=agent_data["type"],
            name=agent_data["name"],
            status=agent_data["status"],
            created_at=agent_data["created_at"],
            config=agent_data["config"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving agent info: {str(e)}")


@router.delete("/{agent_id}", summary="Stop agent instance")
async def stop_agent(agent_id: str):
    """
    Stop and remove an agent instance.
    """
    try:
        if agent_id not in _agent_registry:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Remove from registry
        agent_data = _agent_registry.pop(agent_id)
        
        logger.info(f"Stopped agent: {agent_id} ({agent_data['type'].value})")
        
        return {
            "success": True,
            "message": f"Agent {agent_id} stopped successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error stopping agent: {str(e)}")


@router.post("/{agent_id}/reset", summary="Reset agent state")
async def reset_agent(agent_id: str):
    """
    Reset an agent's state and clear its memory.
    """
    try:
        if agent_id not in _agent_registry:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Reset agent status
        _agent_registry[agent_id]["status"] = AgentStatus.IDLE
        
        # Reset metrics for this agent type
        agent_type = _agent_registry[agent_id]["type"].value
        if agent_type in _agent_metrics:
            _agent_metrics[agent_type] = {
                "requests": 0,
                "successes": 0,
                "start_time": time.time()
            }
        
        logger.info(f"Reset agent: {agent_id}")
        
        return {
            "success": True,
            "message": f"Agent {agent_id} reset successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error resetting agent: {str(e)}")


@router.post("/approval/respond", summary="Respond to manual approval request")
async def respond_to_approval(
    approval_id: str,
    approved: bool,
    user_id: str
):
    """
    Handle user's response to a high-risk transaction approval request.
    
    Implements workflow: "If the user approves, they click an 'Approve' button,
    which sends a confirmation to the backend. The workflow then proceeds as
    described in the 'happy path'. If the user rejects, they click a 'Reject'
    button. The backend cancels the transaction."
    """
    try:
        orchestrator = get_orchestrator()
        
        result = await orchestrator.handle_approval_response(
            approval_id=approval_id,
            approved=approved,
            user_id=user_id
        )
        
        return {
            "success": result.get("success", False),
            "message": "Approved and executed" if approved else "Rejected by user",
            "result": result.get("result"),
            "execution": result.get("execution")
        }
        
    except Exception as e:
        logger.error(f"Error handling approval response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/clarification/respond", summary="Respond to clarification request")
async def respond_to_clarification(
    clarification_id: str,
    answer: str,
    user_id: str
):
    """
    Handle user's response to a clarification request for an ambiguous request.
    
    Implements workflow: "The user provides more information, and the workflow
    restarts."
    """
    try:
        orchestrator = get_orchestrator()
        
        result = await orchestrator.handle_clarification_response(
            clarification_id=clarification_id,
            answer=answer,
            user_id=user_id
        )
        
        return {
            "success": result.get("success", False),
            "message": "Request clarified and processing restarted",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error handling clarification response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
