# Wallet-related Pydantic models for API request/response validation
# Implements FR-004, FR-005, FR-006

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class NetworkType(str, Enum):
    """Supported blockchain networks (FR-006)"""
    ETHEREUM_SEPOLIA = "ethereum_sepolia"
    POLYGON_AMOY = "polygon_amoy"
    BASE_GOERLI = "base_goerli"
    

class WalletType(str, Enum):
    """Type of wallet"""
    ERC4337_SMART_ACCOUNT = "erc4337_smart_account"
    EOA = "eoa"
    

class CreateWalletRequest(BaseModel):
    """Request to create new wallet (FR-004)"""
    owner_address: str = Field(..., description="Owner address")
    wallet_type: WalletType = Field(default=WalletType.ERC4337_SMART_ACCOUNT, description="Type of wallet")
    network: NetworkType = Field(..., description="Network to deploy on")
    initial_spending_limit: Optional[float] = Field(default=0.1, description="Initial spending limit in ETH")
    

class WalletInfo(BaseModel):
    """Wallet information"""
    wallet_id: str = Field(..., description="Unique wallet identifier")
    address: str = Field(..., description="Wallet address")
    wallet_type: WalletType = Field(..., description="Type of wallet")
    network: NetworkType = Field(..., description="Current network")
    owner: str = Field(..., description="Owner address")
    balance: float = Field(..., description="Current balance in ETH")
    spending_limit: float = Field(..., description="Spending limit in ETH")
    total_spent: float = Field(..., description="Total spent in ETH")
    created_at: datetime = Field(..., description="Creation timestamp")
    

class BalanceRequest(BaseModel):
    """Request to check wallet balance"""
    wallet_address: str = Field(..., description="Wallet address to check")
    network: NetworkType = Field(..., description="Network to check on")
    

class BalanceResponse(BaseModel):
    """Wallet balance information"""
    address: str = Field(..., description="Wallet address")
    network: NetworkType = Field(..., description="Network")
    balance: float = Field(..., description="Balance in ETH")
    balance_usd: Optional[float] = Field(default=None, description="Balance in USD")
    tokens: List[Dict[str, Any]] = Field(default_factory=list, description="Token balances")
    

class UpdateSpendingLimitRequest(BaseModel):
    """Request to update spending limit"""
    wallet_address: str = Field(..., description="Wallet address")
    new_limit: float = Field(..., gt=0, description="New spending limit in ETH")
    

class SpendingLimitResponse(BaseModel):
    """Spending limit information"""
    wallet_address: str = Field(..., description="Wallet address")
    spending_limit: float = Field(..., description="Current spending limit in ETH")
    total_spent: float = Field(..., description="Total spent in ETH")
    remaining: float = Field(..., description="Remaining allowance in ETH")
    reset_at: Optional[datetime] = Field(default=None, description="When spending resets")
    

class NetworkSwitchRequest(BaseModel):
    """Request to switch network (FR-006)"""
    wallet_address: str = Field(..., description="Wallet address")
    target_network: NetworkType = Field(..., description="Network to switch to")
    

class NetworkInfo(BaseModel):
    """Network information"""
    network: NetworkType = Field(..., description="Network identifier")
    name: str = Field(..., description="Network name")
    chain_id: int = Field(..., description="Chain ID")
    rpc_url: str = Field(..., description="RPC endpoint")
    explorer_url: str = Field(..., description="Block explorer URL")
    native_currency: str = Field(..., description="Native currency symbol")
    is_testnet: bool = Field(..., description="Whether this is a testnet")
    

class WalletOperationResponse(BaseModel):
    """Generic wallet operation response"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    transaction_hash: Optional[str] = Field(default=None, description="Transaction hash if applicable")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional response data")
