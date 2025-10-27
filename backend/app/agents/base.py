"""
Base Agent Class for WalletMind AI Agents

Provides common functionality for all specialized agents:
- Planner, Executor, Evaluator, Communicator

Each agent inherits from this base to access LLM, memory, and tools.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from pydantic import BaseModel, Field
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Configuration for agent initialization"""
    agent_type: str = Field(..., description="Type of agent (planner, executor, evaluator, communicator)")
    llm_model: str = Field(default="llama-3.3-70b-versatile", description="LLM model name")
    temperature: float = Field(default=0.7, description="LLM temperature")
    max_tokens: int = Field(default=2000, description="Max tokens for response")
    max_iterations: int = Field(default=10, description="Max agent iterations")
    verbose: bool = Field(default=True, description="Enable verbose logging")


class DecisionContext(BaseModel):
    """Context for agent decision-making"""
    user_id: str
    wallet_address: Optional[str] = None
    request: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    previous_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    wallet_balance: Optional[float] = None
    network: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Standardized response from agents"""
    agent_type: str
    success: bool
    result: Dict[str, Any]
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """
    Abstract base class for all WalletMind agents.
    
    Provides:
    - LLM interaction
    - Memory access
    - Tool execution
    - Logging and error handling
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        tools: List[BaseTool],
        config: AgentConfig,
        memory_service: Optional[Any] = None
    ):
        """
        Initialize base agent
        
        Args:
            llm: LangChain LLM instance (Groq/Gemini)
            tools: List of tools available to this agent
            config: Agent configuration
            memory_service: Memory service for context retrieval
        """
        self.llm = llm
        self.tools = tools
        self.config = config
        self.memory_service = memory_service
        self.agent_type = config.agent_type
        
        # Initialize agent executor
        self.agent_executor = self._create_agent_executor()
        
        logger.info(f"{self.agent_type.capitalize()} agent initialized with {len(tools)} tools")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent type.
        Must be implemented by each specialized agent.
        """
        pass
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Create LangChain agent executor with tools"""
        system_prompt = self.get_system_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent with tools
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.config.verbose,
            max_iterations=self.config.max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
    
    async def process(
        self,
        context: DecisionContext,
        additional_input: Optional[str] = None
    ) -> AgentResponse:
        """
        Process a request with this agent
        
        Args:
            context: Decision context with user request and metadata
            additional_input: Additional instructions for this specific call
        
        Returns:
            AgentResponse with result and reasoning
        """
        try:
            logger.info(f"{self.agent_type} processing request: {context.request[:100]}...")
            
            # Retrieve relevant memory if available
            chat_history = []
            if self.memory_service and context.wallet_address:
                memory_context = await self._get_memory_context(context)
                if memory_context:
                    chat_history.append(SystemMessage(content=f"Relevant context: {memory_context}"))
            
            # Build input
            input_text = context.request
            if additional_input:
                input_text = f"{input_text}\n\nAdditional instructions: {additional_input}"
            
            # Execute agent
            result = await self.agent_executor.ainvoke({
                "input": input_text,
                "chat_history": chat_history
            })
            
            # Extract reasoning from intermediate steps
            reasoning = self._extract_reasoning(result.get("intermediate_steps", []))
            
            response = AgentResponse(
                agent_type=self.agent_type,
                success=True,
                result=result.get("output", {}),
                reasoning=reasoning,
                metadata={
                    "iterations": len(result.get("intermediate_steps", [])),
                    "tools_used": [step[0].tool for step in result.get("intermediate_steps", [])]
                }
            )
            
            # Store in memory
            if self.memory_service and context.wallet_address:
                await self._store_in_memory(context, response)
            
            logger.info(f"{self.agent_type} completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"{self.agent_type} error: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_type=self.agent_type,
                success=False,
                result={},
                reasoning=f"Error occurred: {str(e)}",
                error=str(e)
            )
    
    def _extract_reasoning(self, intermediate_steps: List[tuple]) -> str:
        """Extract reasoning from agent's intermediate steps"""
        reasoning_parts = []
        for i, (action, observation) in enumerate(intermediate_steps, 1):
            reasoning_parts.append(f"Step {i}: Used {action.tool}")
            reasoning_parts.append(f"  Thought: {action.log}")
            reasoning_parts.append(f"  Result: {observation[:200]}...")
        
        return "\n".join(reasoning_parts) if reasoning_parts else "Direct response without tool use"
    
    async def _get_memory_context(self, context: DecisionContext) -> Optional[str]:
        """Retrieve relevant context from memory"""
        if not self.memory_service:
            return None
        
        try:
            # Query memory for relevant past decisions
            results = await self.memory_service.query(
                query=context.request,
                wallet_address=context.wallet_address,
                limit=3
            )
            
            if results:
                return f"Previous relevant interactions: {results}"
            
        except Exception as e:
            logger.warning(f"Failed to retrieve memory: {e}")
        
        return None
    
    async def _store_in_memory(self, context: DecisionContext, response: AgentResponse):
        """Store interaction in memory"""
        if not self.memory_service:
            return
        
        try:
            await self.memory_service.store(
                wallet_address=context.wallet_address,
                agent_type=self.agent_type,
                request=context.request,
                response=response.result,
                reasoning=response.reasoning,
                timestamp=response.timestamp
            )
        except Exception as e:
            logger.warning(f"Failed to store in memory: {e}")
    
    def invoke_sync(self, input_text: str) -> Dict[str, Any]:
        """Synchronous invocation for simple cases"""
        result = self.agent_executor.invoke({"input": input_text})
        return result
    
    async def ainvoke(self, input_text: str, chat_history: Optional[List[BaseMessage]] = None) -> Dict[str, Any]:
        """Async invocation with optional chat history"""
        result = await self.agent_executor.ainvoke({
            "input": input_text,
            "chat_history": chat_history or []
        })
        return result