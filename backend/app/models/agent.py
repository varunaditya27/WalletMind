# Agent-related Pydantic models for API request/response validation
# Implements FR-001, FR-002, FR-003

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AgentStatus(str, Enum):
    """Agent operational status"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"


class AgentType(str, Enum):
    """Types of agents in the system"""
    PLANNER = "planner"
    EXECUTOR = "executor"
    EVALUATOR = "evaluator"
    COMMUNICATOR = "communicator"


class AgentRequest(BaseModel):
    """Natural language request to agent (FR-001)"""
    user_id: str = Field(..., description="User identifier")
    request: str = Field(..., min_length=1, max_length=5000, description="Natural language request")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the request")
    agent_type: Optional[AgentType] = Field(default=AgentType.PLANNER, description="Type of agent to use")
    

class AgentDecision(BaseModel):
    """Structured decision output from agent (FR-002)"""
    decision_id: str = Field(..., description="Unique decision identifier")
    intent: str = Field(..., description="Parsed user intent")
    action_type: str = Field(..., description="Type of action to perform")
    parameters: Dict[str, Any] = Field(..., description="Action parameters")
    reasoning: str = Field(..., description="Agent's reasoning for the decision")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk assessment score")
    estimated_cost: Optional[float] = Field(default=None, description="Estimated cost in ETH")
    requires_approval: bool = Field(default=False, description="Whether decision needs user approval")
    

class AgentResponse(BaseModel):
    """Response from agent processing (FR-001)"""
    success: bool = Field(..., description="Whether request was successful")
    message: str = Field(..., description="Human-readable response")
    decision: Optional[AgentDecision] = Field(default=None, description="Decision if applicable")
    execution_time: float = Field(..., description="Processing time in seconds")
    agent_status: AgentStatus = Field(..., description="Current agent status")
    

class AgentMemoryEntry(BaseModel):
    """Single memory entry for agent context (FR-003)"""
    entry_id: str = Field(..., description="Unique entry identifier")
    timestamp: datetime = Field(..., description="When the entry was created")
    agent_type: AgentType = Field(..., description="Which agent created this entry")
    content: str = Field(..., description="Memory content")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    

class AgentMemoryQuery(BaseModel):
    """Query for retrieving agent memories (FR-003)"""
    query: str = Field(..., min_length=1, description="Query string")
    agent_type: Optional[AgentType] = Field(default=None, description="Filter by agent type")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results")
    

class AgentMemoryResponse(BaseModel):
    """Response containing agent memories"""
    memories: List[AgentMemoryEntry] = Field(..., description="Retrieved memory entries")
    total: int = Field(..., description="Total number of matching memories")
    

class AgentHealth(BaseModel):
    """Agent health status"""
    agent_type: AgentType = Field(..., description="Agent type")
    status: AgentStatus = Field(..., description="Current status")
    uptime: float = Field(..., description="Uptime in seconds")
    total_requests: int = Field(..., description="Total requests processed")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate")
    last_active: datetime = Field(..., description="Last activity timestamp")
    

class CreateAgentRequest(BaseModel):
    """Request to create a new agent instance"""
    agent_type: AgentType = Field(..., description="Type of agent to create")
    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")
    

class AgentInfo(BaseModel):
    """Agent information"""
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: AgentType = Field(..., description="Agent type")
    name: str = Field(..., description="Agent name")
    status: AgentStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    config: Dict[str, Any] = Field(..., description="Agent configuration")
