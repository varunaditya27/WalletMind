# External integration-related Pydantic models
# Implements FR-010, FR-011, FR-012

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class APIProvider(str, Enum):
    """Supported API providers (FR-010)"""
    GROQ = "groq"
    GOOGLE_AI = "google_ai"
    CUSTOM = "custom"
    

class PaymentStatus(str, Enum):
    """API payment status"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    

class APIPaymentRequest(BaseModel):
    """Request to pay for API access (FR-010)"""
    wallet_address: str = Field(..., description="Wallet making payment")
    provider: APIProvider = Field(..., description="API provider")
    api_endpoint: str = Field(..., description="API endpoint URL")
    estimated_cost: float = Field(..., gt=0, description="Estimated cost in ETH")
    request_payload: Dict[str, Any] = Field(..., description="API request payload")
    

class APIPaymentResponse(BaseModel):
    """Response from API payment (FR-010)"""
    payment_id: str = Field(..., description="Payment identifier")
    status: PaymentStatus = Field(..., description="Payment status")
    transaction_hash: Optional[str] = Field(default=None, description="Payment transaction hash")
    api_response: Optional[Dict[str, Any]] = Field(default=None, description="API response data")
    cost: float = Field(..., description="Actual cost in ETH")
    timestamp: datetime = Field(..., description="Payment timestamp")
    

class DataPurchaseRequest(BaseModel):
    """Request to purchase data (FR-011)"""
    wallet_address: str = Field(..., description="Wallet making purchase")
    data_source: str = Field(..., description="Data source identifier")
    data_type: str = Field(..., description="Type of data to purchase")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    max_price: float = Field(..., gt=0, description="Maximum price willing to pay in ETH")
    

class DataPurchaseResponse(BaseModel):
    """Response from data purchase"""
    purchase_id: str = Field(..., description="Purchase identifier")
    status: str = Field(..., description="Purchase status")
    transaction_hash: Optional[str] = Field(default=None, description="Transaction hash")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Purchased data")
    ipfs_cid: Optional[str] = Field(default=None, description="IPFS CID if data stored")
    cost: float = Field(..., description="Actual cost in ETH")
    data_source: str = Field(..., description="Data source")
    timestamp: datetime = Field(..., description="Purchase timestamp")
    

class AgentServiceOffering(BaseModel):
    """Agent service offering (FR-012)"""
    service_id: str = Field(..., description="Service identifier")
    agent_address: str = Field(..., description="Agent wallet address")
    service_name: str = Field(..., description="Service name")
    service_description: str = Field(..., description="Service description")
    price: float = Field(..., gt=0, description="Service price in ETH")
    available: bool = Field(default=True, description="Service availability")
    category: str = Field(..., description="Service category")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    

class RegisterServiceRequest(BaseModel):
    """Request to register agent service (FR-012)"""
    agent_address: str = Field(..., description="Agent wallet address")
    service_name: str = Field(..., description="Service name")
    service_description: str = Field(..., description="Service description")
    price: float = Field(..., gt=0, description="Service price in ETH")
    category: str = Field(..., description="Service category")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    

class ServiceDiscoveryRequest(BaseModel):
    """Request to discover agent services (FR-012)"""
    category: Optional[str] = Field(default=None, description="Filter by category")
    max_price: Optional[float] = Field(default=None, description="Maximum price filter")
    search_query: Optional[str] = Field(default=None, description="Search query")
    limit: int = Field(default=20, ge=1, le=100, description="Number of results")
    

class ServiceDiscoveryResponse(BaseModel):
    """Response with discovered services"""
    services: List[AgentServiceOffering] = Field(..., description="Available services")
    total: int = Field(..., description="Total number of services")
    

class InterAgentTransactionRequest(BaseModel):
    """Request for agent-to-agent transaction (FR-012)"""
    from_agent: str = Field(..., description="Source agent address")
    to_agent: str = Field(..., description="Destination agent address")
    service_id: str = Field(..., description="Service being purchased")
    amount: float = Field(..., gt=0, description="Transaction amount in ETH")
    service_parameters: Dict[str, Any] = Field(default_factory=dict, description="Service parameters")
    

class InterAgentTransactionResponse(BaseModel):
    """Response from inter-agent transaction"""
    transaction_id: str = Field(..., description="Transaction identifier")
    status: str = Field(..., description="Transaction status")
    from_agent: str = Field(..., description="Source agent")
    to_agent: str = Field(..., description="Destination agent")
    service_id: str = Field(..., description="Service purchased")
    amount: float = Field(..., description="Amount in ETH")
    transaction_hash: Optional[str] = Field(default=None, description="Blockchain transaction hash")
    service_result: Optional[Dict[str, Any]] = Field(default=None, description="Service execution result")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    

class OracleDataRequest(BaseModel):
    """Request oracle data (FR-011)"""
    data_feed: str = Field(..., description="Oracle data feed identifier")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    

class OracleDataResponse(BaseModel):
    """Oracle data response"""
    data_feed: str = Field(..., description="Data feed identifier")
    data: Dict[str, Any] = Field(..., description="Oracle data")
    timestamp: datetime = Field(..., description="Data timestamp")
    source: str = Field(..., description="Data source")
