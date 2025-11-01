"""
Base Agent Class for WalletMind AI Agents

Provides common functionality for all specialized agents:
- Planner, Executor, Evaluator, Communicator

Each agent inherits from this base to access LLM, memory, and tools.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages.base import BaseMessage
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.system import SystemMessage
from langchain_core.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools.base import BaseTool
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
    
    def _create_agent_executor(self):
        """Create agent executor with tool calling capability"""
        # Get tool names for the system prompt
        tool_names = ", ".join([tool.name for tool in self.tools]) if self.tools else "None"
        
        # Create system prompt
        system_prompt = self.get_system_prompt()
        
        # Format the system prompt with tool names if it has the placeholder
        if "{tool_names}" in system_prompt:
            system_prompt = system_prompt.replace("{tool_names}", tool_names)
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}")
        ])
        
        # Bind tools to LLM if available
        if self.tools:
            try:
                logger.info(f"Binding {len(self.tools)} tools to LLM for {self.agent_type} agent")
                self.llm_with_tools = self.llm.bind_tools(self.tools)
            except Exception as e:
                logger.warning(f"Failed to bind tools to LLM: {e}. Will use direct invocation.")
                self.llm_with_tools = None
        else:
            self.llm_with_tools = None
        
        return None
    
    async def process(
        self,
        context: DecisionContext,
        additional_input: Optional[str] = None
    ) -> AgentResponse:
        """
        Process a request with this agent using LLM with optional tool calling
        
        Args:
            context: Decision context with user request and metadata
            additional_input: Additional instructions for this specific call
        
        Returns:
            AgentResponse with result and reasoning
        """
        try:
            logger.info(f"[{self.agent_type.upper()}] Processing: {context.request[:100]}...")
            
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
            
            # Format the prompt
            formatted_prompt = self.prompt.format_messages(
                input=input_text,
                chat_history=chat_history
            )
            
            # Process with tools if available
            tool_calls_made = []
            final_output = ""
            
            if self.llm_with_tools and self.tools:
                logger.info(f"[{self.agent_type.upper()}] Using LLM with {len(self.tools)} tools available")
                
                # First LLM call - agent decides what to do
                response_message = await self.llm_with_tools.ainvoke(formatted_prompt)
                
                # Check if LLM wants to use tools
                if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
                    logger.info(f"[{self.agent_type.upper()}] LLM requested {len(response_message.tool_calls)} tool call(s)")
                    
                    # Execute each tool call
                    tool_results = []
                    for tool_call in response_message.tool_calls:
                        tool_name = tool_call.get('name', '')
                        tool_input = tool_call.get('args', {})
                        
                        logger.info(f"[{self.agent_type.upper()}] Executing tool: {tool_name}")
                        logger.debug(f"Tool input: {tool_input}")
                        
                        # Find and execute the tool
                        tool = next((t for t in self.tools if t.name == tool_name), None)
                        if tool:
                            try:
                                # Execute tool (prefer async)
                                if hasattr(tool, '_arun'):
                                    tool_output = await tool._arun(**tool_input)
                                else:
                                    tool_output = tool._run(**tool_input)
                                
                                logger.info(f"[{self.agent_type.upper()}] Tool '{tool_name}' executed successfully")
                                logger.debug(f"Tool output (truncated): {str(tool_output)[:200]}")
                                
                                tool_calls_made.append({
                                    'tool': tool_name,
                                    'input': tool_input,
                                    'output': str(tool_output),
                                    'success': True
                                })
                                tool_results.append(f"**Tool: {tool_name}**\nResult: {tool_output}")
                                
                            except Exception as tool_error:
                                logger.error(f"[{self.agent_type.upper()}] Tool '{tool_name}' failed: {tool_error}", exc_info=True)
                                error_msg = f"Error: {str(tool_error)}"
                                tool_calls_made.append({
                                    'tool': tool_name,
                                    'input': tool_input,
                                    'error': error_msg,
                                    'success': False
                                })
                                tool_results.append(f"**Tool: {tool_name}**\nError: {error_msg}")
                        else:
                            logger.error(f"[{self.agent_type.upper()}] Tool '{tool_name}' not found")
                            tool_results.append(f"**Tool: {tool_name}**\nError: Tool not available")
                    
                    # Second LLM call - synthesize final response from tool results
                    if tool_results:
                        tool_results_text = "\n\n".join(tool_results)
                        synthesis_prompt = f"""Original request: {input_text}

You called tools and received these results:

{tool_results_text}

Based on these tool results, provide a clear, concise final response to the user. 
Include all relevant information from the tool outputs.
Format your response with proper markdown for readability."""
                        
                        synthesis_messages = self.prompt.format_messages(
                            input=synthesis_prompt,
                            chat_history=[]
                        )
                        
                        final_response = await self.llm.ainvoke(synthesis_messages)
                        final_output = final_response.content
                        
                        logger.info(f"[{self.agent_type.upper()}] Synthesized final response from {len(tool_calls_made)} tool call(s)")
                    else:
                        final_output = response_message.content
                else:
                    # No tools called - use direct response
                    final_output = response_message.content
                    logger.info(f"[{self.agent_type.upper()}] No tools called, using direct LLM response")
            else:
                # No tools available - direct LLM invocation
                logger.info(f"[{self.agent_type.upper()}] Using direct LLM (no tools)")
                response_message = await self.llm.ainvoke(formatted_prompt)
                final_output = response_message.content
            
            # Build response
            reasoning = f"{self.agent_type.capitalize()} agent processed request"
            if tool_calls_made:
                successful = sum(1 for tc in tool_calls_made if tc.get('success', False))
                reasoning += f" with {successful}/{len(tool_calls_made)} successful tool call(s)"
            
            response = AgentResponse(
                agent_type=self.agent_type,
                success=True,
                result={
                    "response": final_output,
                    "context": context.dict(),
                    "tool_calls": tool_calls_made
                },
                reasoning=reasoning,
                metadata={
                    "model": self.config.llm_model,
                    "temperature": self.config.temperature,
                    "tool_count": len(tool_calls_made),
                    "tools_available": len(self.tools) if self.tools else 0
                }
            )
            
            # Store in memory
            if self.memory_service and context.wallet_address:
                try:
                    await self._store_in_memory(context, response)
                except Exception as mem_error:
                    logger.warning(f"[{self.agent_type.upper()}] Failed to store in memory: {mem_error}")
            
            logger.info(f"[{self.agent_type.upper()}] ✓ Completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"[{self.agent_type.upper()}] ✗ Error: {str(e)}", exc_info=True)
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
        formatted_prompt = self.prompt.format_messages(input=input_text, chat_history=[])
        response_message = self.llm.invoke(formatted_prompt)
        return {"response": response_message.content}

    async def ainvoke(self, input_text: str, chat_history: Optional[List[BaseMessage]] = None) -> Dict[str, Any]:
        """Async invocation with optional chat history"""
        formatted_prompt = self.prompt.format_messages(input=input_text, chat_history=chat_history or [])
        response_message = await self.llm.ainvoke(formatted_prompt)
        return {"response": response_message.content}