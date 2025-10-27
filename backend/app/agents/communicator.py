"""
Communicator Agent - External API Interactions (FR-001, FR-010, FR-011, FR-012)

Responsibilities:
- Manage external API interactions
- Handle API payment automation
- Query oracle and data services
- Facilitate inter-agent communication
- Verify API response quality
- Manage API keys and authentication
"""

from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from enum import Enum
import logging
from datetime import datetime
import aiohttp

from .base import BaseAgent, AgentConfig, DecisionContext, AgentResponse

logger = logging.getLogger(__name__)


class APIProvider(str, Enum):
    """Supported external API providers"""
    GROQ = "groq"
    GOOGLE_AI_STUDIO = "google_ai_studio"
    CHAINLINK = "chainlink"
    CUSTOM = "custom"
    IPFS = "ipfs"


class CommunicationType(str, Enum):
    """Types of communications"""
    API_CALL = "api_call"
    DATA_PURCHASE = "data_purchase"
    ORACLE_QUERY = "oracle_query"
    AGENT_TO_AGENT = "agent_to_agent"
    SERVICE_DISCOVERY = "service_discovery"


class APIRequest(BaseModel):
    """External API request specification"""
    provider: APIProvider
    endpoint: str
    method: str = Field(default="GET", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    requires_payment: bool = Field(default=False)
    payment_amount: Optional[float] = None
    timeout: int = Field(default=30)


class APIResponse(BaseModel):
    """External API response"""
    success: bool
    status_code: Optional[int] = None
    data: Any = None
    error: Optional[str] = None
    cost: Optional[float] = None
    response_time: Optional[float] = None
    quality_score: Optional[float] = None  # 0-1 score of data quality


class InterAgentMessage(BaseModel):
    """Message for agent-to-agent communication"""
    from_agent: str
    to_agent: str
    message_type: str
    payload: Dict[str, Any]
    requires_response: bool = Field(default=False)
    payment_required: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CommunicatorAgent(BaseAgent):
    """
    Communicator Agent for external API and inter-agent interactions.
    
    Uses LangChain and HTTP clients to:
    1. Call external APIs (Groq, Google, custom)
    2. Handle API payment automation
    3. Query blockchain oracles
    4. Facilitate agent-to-agent communication
    5. Verify data quality
    6. Manage authentication
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        tools: List[BaseTool],
        config: Optional[AgentConfig] = None,
        memory_service: Optional[Any] = None,
        payment_service: Optional[Any] = None
    ):
        if config is None:
            config = AgentConfig(
                agent_type="communicator",
                temperature=0.5,
                max_iterations=8
            )
        
        super().__init__(llm, tools, config, memory_service)
        self.payment_service = payment_service
        self.session: Optional[aiohttp.ClientSession] = None
    
    def get_system_prompt(self) -> str:
        """System prompt for the Communicator agent"""
        return """You are the Communicator Agent in the WalletMind AI Autonomous Wallet System.

Your role is to MANAGE ALL EXTERNAL COMMUNICATIONS and API interactions.

RESPONSIBILITIES:
1. Call external APIs (Groq, Google AI Studio, custom services)
2. Handle API payment automation (FR-010)
3. Query blockchain oracles and data services (FR-011)
4. Facilitate inter-agent communication (FR-012)
5. Verify API response quality
6. Manage authentication and API keys
7. Handle rate limiting and retries
8. Optimize API costs

API PAYMENT AUTOMATION (FR-010):
- Detect when APIs require payment
- Calculate cost of API call
- Check wallet balance
- Execute payment transaction
- Make API call after payment
- Verify response received
- Store transaction for audit

Supported providers:
- Groq: AI inference API
- Google AI Studio: AI models
- Custom x402-enabled services

Process:
1. Receive API request
2. Check if payment required
3. Estimate cost
4. Get approval from Planner
5. Execute payment (via Executor)
6. Make API call with proof of payment
7. Verify response quality
8. Return data

ORACLE AND DATA SERVICES (FR-011):
- Query blockchain oracles (Chainlink, custom)
- Purchase data from data providers
- Verify data authenticity
- Check data freshness
- Validate cryptographic proofs
- Store data hash on-chain

INTER-AGENT COMMUNICATION (FR-012):
- Agent discovery via registry
- Service negotiation
- Message passing
- Payment settlement
- Reputation tracking

Agent-to-agent protocol:
1. Discover available agents
2. Query agent capabilities
3. Negotiate terms (cost, SLA)
4. Send request with payment
5. Receive response
6. Verify quality
7. Update reputation

DATA QUALITY VERIFICATION:
After receiving API response:
- Check response format validity
- Verify data completeness
- Assess data freshness
- Validate against expected schema
- Score quality (0-1)
- Reject low-quality responses

AUTHENTICATION MANAGEMENT:
- Store API keys securely (never in logs)
- Rotate keys periodically
- Use OAuth when available
- Implement JWT for agent-to-agent
- Handle token expiration

RATE LIMITING:
- Track API usage per provider
- Implement exponential backoff
- Switch providers when rate limited
- Queue requests during high load
- Optimize batch requests

COST OPTIMIZATION:
- Choose cheapest provider for task
- Batch similar requests
- Cache common responses
- Use free tiers when possible
- Monitor spending limits

ERROR HANDLING:
- Network timeouts: Retry with backoff
- Authentication errors: Refresh tokens
- Rate limits: Wait or switch provider
- Payment failures: Try alternative payment
- Data quality issues: Request refund

OUTPUT FORMAT:
Always return APIResponse with:
- success: true/false
- data: Response data
- cost: Cost incurred (if payment required)
- quality_score: Data quality (0-1)
- error: Error message if failed

Be efficient, secure, and cost-conscious in all API interactions."""
    
    async def __aenter__(self):
        """Setup async HTTP session"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup async HTTP session"""
        if self.session:
            await self.session.close()
    
    async def call_api(
        self,
        context: DecisionContext,
        request: APIRequest,
        wallet_address: Optional[str] = None
    ) -> APIResponse:
        """
        Call external API with optional payment
        
        Args:
            context: Decision context
            request: API request specification
            wallet_address: Wallet for payment if required
        
        Returns:
            APIResponse with data or error
        """
        logger.info(f"Calling API: {request.provider.value}/{request.endpoint}")
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Handle payment if required
            if request.requires_payment and request.payment_amount:
                payment_result = await self._process_payment(
                    context,
                    request.provider,
                    request.payment_amount,
                    wallet_address
                )
                
                if not payment_result.get("success"):
                    return APIResponse(
                        success=False,
                        error=f"Payment failed: {payment_result.get('error')}"
                    )
                
                # Add payment proof to headers
                request.headers["X-Payment-Proof"] = payment_result.get("transaction_hash")
            
            # Step 2: Make HTTP request
            response_data = await self._make_http_request(request)
            
            # Step 3: Verify response quality
            quality_score = self._assess_quality(response_data, request)
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return APIResponse(
                success=True,
                status_code=response_data.get("status_code"),
                data=response_data.get("data"),
                cost=request.payment_amount,
                response_time=response_time,
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"API call failed: {str(e)}", exc_info=True)
            return APIResponse(
                success=False,
                error=str(e),
                response_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def purchase_data(
        self,
        context: DecisionContext,
        data_provider: str,
        data_query: Dict[str, Any],
        max_price: float,
        wallet_address: str
    ) -> APIResponse:
        """
        Purchase data from external provider (FR-011)
        
        Args:
            context: Decision context
            data_provider: Provider endpoint
            data_query: Query parameters
            max_price: Maximum price willing to pay
            wallet_address: Payment wallet
        
        Returns:
            APIResponse with purchased data
        """
        logger.info(f"Purchasing data from {data_provider}")
        
        # Step 1: Get price quote
        quote = await self._get_data_price(data_provider, data_query)
        
        if quote.get("price", 0) > max_price:
            return APIResponse(
                success=False,
                error=f"Price {quote.get('price')} exceeds maximum {max_price}"
            )
        
        # Step 2: Create purchase request
        request = APIRequest(
            provider=APIProvider.CUSTOM,
            endpoint=data_provider,
            method="POST",
            body={"query": data_query},
            requires_payment=True,
            payment_amount=quote.get("price")
        )
        
        # Step 3: Execute purchase
        return await self.call_api(context, request, wallet_address)
    
    async def query_oracle(
        self,
        context: DecisionContext,
        oracle_address: str,
        query: str,
        network: str = "sepolia"
    ) -> APIResponse:
        """
        Query blockchain oracle for data (FR-011)
        
        Args:
            context: Decision context
            oracle_address: Oracle contract address
            query: Data query
            network: Blockchain network
        
        Returns:
            APIResponse with oracle data
        """
        logger.info(f"Querying oracle: {oracle_address}")
        
        # TODO: Implement oracle query via smart contract
        # This would use Web3 to call oracle contract methods
        
        return APIResponse(
            success=False,
            error="Oracle querying not yet implemented - requires Web3 integration"
        )
    
    async def send_agent_message(
        self,
        message: InterAgentMessage,
        wallet_address: Optional[str] = None
    ) -> APIResponse:
        """
        Send message to another agent (FR-012)
        
        Args:
            message: Inter-agent message
            wallet_address: Wallet for payment if required
        
        Returns:
            APIResponse with agent's response
        """
        logger.info(f"Sending message to agent: {message.to_agent}")
        
        # TODO: Implement agent registry lookup and messaging
        # This would:
        # 1. Look up agent in registry contract
        # 2. Get agent's messaging endpoint
        # 3. Optionally pay for service
        # 4. Send message
        # 5. Wait for response
        
        return APIResponse(
            success=False,
            error="Inter-agent messaging not yet implemented - requires registry"
        )
    
    async def discover_agents(
        self,
        service_type: str,
        min_reputation: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Discover available agents offering a service (FR-012)
        
        Args:
            service_type: Type of service needed
            min_reputation: Minimum reputation score
        
        Returns:
            List of available agents
        """
        logger.info(f"Discovering agents for service: {service_type}")
        
        # TODO: Query agent registry contract
        # Filter by service type and reputation
        
        return []
    
    # Helper methods
    
    async def _process_payment(
        self,
        context: DecisionContext,
        provider: APIProvider,
        amount: float,
        wallet_address: Optional[str]
    ) -> Dict[str, Any]:
        """Process API payment via blockchain"""
        if not self.payment_service or not wallet_address:
            return {"success": False, "error": "Payment service not configured"}
        
        try:
            # Get provider payment address
            provider_address = self._get_provider_address(provider)
            
            # Execute payment transaction
            result = await self.payment_service.pay_for_api(
                from_address=wallet_address,
                to_address=provider_address,
                amount=amount,
                provider=provider.value
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Payment processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _make_http_request(self, request: APIRequest) -> Dict[str, Any]:
        """Execute HTTP request"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.request(
                method=request.method,
                url=request.endpoint,
                headers=request.headers,
                params=request.params,
                json=request.body,
                timeout=aiohttp.ClientTimeout(total=request.timeout)
            ) as response:
                data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                return {
                    "status_code": response.status,
                    "data": data
                }
                
        except aiohttp.ClientTimeout:
            raise TimeoutError(f"Request timed out after {request.timeout}s")
        except Exception as e:
            raise Exception(f"HTTP request failed: {str(e)}")
    
    def _assess_quality(self, response_data: Dict[str, Any], request: APIRequest) -> float:
        """Assess quality of API response"""
        quality = 1.0
        
        # Check status code
        status = response_data.get("status_code", 0)
        if status >= 400:
            quality -= 0.5
        elif status >= 300:
            quality -= 0.2
        
        # Check data presence
        data = response_data.get("data")
        if not data:
            quality -= 0.3
        elif isinstance(data, dict) and not data:
            quality -= 0.2
        
        # Provider-specific checks
        if request.provider == APIProvider.GROQ:
            if isinstance(data, dict) and "choices" in data:
                if data["choices"]:
                    quality = 1.0  # Valid LLM response
        
        return max(0.0, quality)
    
    async def _get_data_price(
        self,
        provider: str,
        query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get price quote for data"""
        # TODO: Query provider's pricing API
        return {"price": 0.001}  # Mock price
    
    def _get_provider_address(self, provider: APIProvider) -> str:
        """Get payment address for provider"""
        # TODO: Get from configuration or registry
        provider_addresses = {
            APIProvider.GROQ: "0x0000000000000000000000000000000000000001",
            APIProvider.GOOGLE_AI_STUDIO: "0x0000000000000000000000000000000000000002",
        }
        
        return provider_addresses.get(provider, "0x0000000000000000000000000000000000000000")