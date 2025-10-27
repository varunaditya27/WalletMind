# Transaction-related Pydantic models for API request/response validation
# Implements FR-005, FR-008

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TransactionStatus(str, Enum):
    """Transaction status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    

class TransactionType(str, Enum):
    """Type of transaction (FR-008)"""
    API_PAYMENT = "api_payment"
    DATA_PURCHASE = "data_purchase"
    AGENT_TO_AGENT = "agent_to_agent"
    INTERNAL_TRANSFER = "internal_transfer"
    CONTRACT_INTERACTION = "contract_interaction"
    

class ExecuteTransactionRequest(BaseModel):
    """Request to execute transaction (FR-005)"""
    wallet_address: str = Field(..., description="Source wallet address")
    to_address: str = Field(..., description="Destination address")
    amount: float = Field(..., gt=0, description="Amount in ETH")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    decision_hash: str = Field(..., description="Associated decision hash for verification")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional transaction metadata")
    gas_limit: Optional[int] = Field(default=None, description="Custom gas limit")
    

class TransactionInfo(BaseModel):
    """Transaction information (FR-008)"""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    transaction_hash: Optional[str] = Field(default=None, description="Blockchain transaction hash")
    from_address: str = Field(..., description="Source address")
    to_address: str = Field(..., description="Destination address")
    amount: float = Field(..., description="Amount in ETH")
    transaction_type: TransactionType = Field(..., description="Transaction type")
    status: TransactionStatus = Field(..., description="Current status")
    decision_hash: str = Field(..., description="Associated decision hash")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    confirmed_at: Optional[datetime] = Field(default=None, description="Confirmation timestamp")
    gas_used: Optional[int] = Field(default=None, description="Gas used")
    gas_price: Optional[float] = Field(default=None, description="Gas price in Gwei")
    network: str = Field(..., description="Network name")
    explorer_url: Optional[str] = Field(default=None, description="Block explorer URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    

class TransactionHistoryRequest(BaseModel):
    """Request transaction history"""
    wallet_address: str = Field(..., description="Wallet address")
    transaction_type: Optional[TransactionType] = Field(default=None, description="Filter by type")
    status: Optional[TransactionStatus] = Field(default=None, description="Filter by status")
    from_date: Optional[datetime] = Field(default=None, description="Start date filter")
    to_date: Optional[datetime] = Field(default=None, description="End date filter")
    limit: int = Field(default=50, ge=1, le=1000, description="Number of results")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    

class TransactionHistoryResponse(BaseModel):
    """Transaction history response"""
    transactions: List[TransactionInfo] = Field(..., description="Transaction list")
    total: int = Field(..., description="Total number of transactions")
    wallet_address: str = Field(..., description="Wallet address")
    

class TransactionStatsResponse(BaseModel):
    """Transaction statistics"""
    wallet_address: str = Field(..., description="Wallet address")
    total_transactions: int = Field(..., description="Total number of transactions")
    successful_transactions: int = Field(..., description="Number of successful transactions")
    failed_transactions: int = Field(..., description="Number of failed transactions")
    total_volume: float = Field(..., description="Total transaction volume in ETH")
    total_gas_spent: float = Field(..., description="Total gas spent in ETH")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate")
    average_transaction_value: float = Field(..., description="Average transaction value in ETH")
    by_type: Dict[str, int] = Field(..., description="Transaction count by type")
    

class GasEstimateRequest(BaseModel):
    """Request gas estimate"""
    from_address: str = Field(..., description="Source address")
    to_address: str = Field(..., description="Destination address")
    amount: float = Field(..., gt=0, description="Amount in ETH")
    data: Optional[str] = Field(default=None, description="Transaction data")
    

class GasEstimateResponse(BaseModel):
    """Gas estimate response"""
    estimated_gas: int = Field(..., description="Estimated gas units")
    gas_price: float = Field(..., description="Current gas price in Gwei")
    estimated_cost: float = Field(..., description="Estimated cost in ETH")
    estimated_cost_usd: Optional[float] = Field(default=None, description="Estimated cost in USD")
