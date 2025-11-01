# Agent API endpoints implementing FR-001, FR-002, FR-003
# Handles agent orchestration, decision-making, and memory management

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
import time
from datetime import datetime
import logging
import hashlib
import json
import os

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
            # Initialize Web3 provider for Sepolia (default testnet)
            provider = Web3Provider()
            provider.connect(NetworkType.SEPOLIA)
            _blockchain_service = WalletManager(provider)
            logger.info("Initialized blockchain service with Sepolia testnet")
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
            
            # TODO: Initialize tools for each agent type
            # For now, use empty tool lists - tools should be added based on agent requirements
            tools: List[BaseTool] = []
            
            # Create sub-agents with proper initialization
            planner = PlannerAgent(
                llm=llm,
                tools=tools,
                config=AgentConfig(
                    agent_type="planner",
                    temperature=0.3,
                    max_iterations=8
                ),
                memory_service=memory_service
            )
            
            executor = ExecutorAgent(
                llm=llm,
                tools=tools,
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
                tools=tools,
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
                tools=tools,
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
        
        # Generate decision
        decision_result = await planner.evaluate_risk(decision_context)
        
        # Create decision hash for tracking
        decision_id = f"dec_{int(time.time())}_{hashlib.md5(request.request.encode()).hexdigest()[:8]}"
        
        # Prepare decision response
        agent_decision = AgentDecision(
            decision_id=decision_id,
            intent=f"Process: {request.request[:50]}",
            action_type="transaction" if "send" in request.request.lower() or "transfer" in request.request.lower() else "query",
            parameters={"query": request.request, "risk_score": decision_result.get("risk_score", 0.5)},
            reasoning=decision_result.get("reasoning", "Analyzed request and determined appropriate action"),
            risk_score=decision_result.get("risk_score", 0.5),
            estimated_cost=decision_result.get("estimated_cost", 0.001),
            requires_approval=decision_result.get("risk_score", 0.5) > 0.5 or decision_result.get("requires_approval", False)
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
            message="Request processed successfully by Planner agent",
            decision=agent_decision,
            execution_time=execution_time,
            agent_status=AgentStatus.IDLE
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
