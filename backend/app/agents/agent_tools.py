"""
Agent Tools - LangChain tools for WalletMind agents

This module provides tools that agents can use to interact with:
- Blockchain networks
- Wallet operations
- External APIs
- Data queries
"""

from typing import Optional, Any, Dict, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class WalletBalanceInput(BaseModel):
    """Input schema for wallet balance tool"""
    wallet_address: str = Field(..., description="Ethereum wallet address to check balance")
    network: str = Field(default="sepolia", description="Network name (sepolia, mainnet, etc.)")


class WalletBalanceTool(BaseTool):
    """Tool to check wallet balance"""
    name: str = "check_wallet_balance"
    description: str = "Check the ETH balance of a wallet address on specified network"
    args_schema: type[BaseModel] = WalletBalanceInput
    blockchain_service: Optional[Any] = None
    
    def _run(self, wallet_address: str, network: str = "sepolia") -> str:
        """Synchronous execution"""
        try:
            if self.blockchain_service:
                balance = self.blockchain_service.get_balance(wallet_address)
                return f"Balance: {balance} ETH on {network}"
            return "Blockchain service not available"
        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return f"Error: {str(e)}"
    
    async def _arun(self, wallet_address: str, network: str = "sepolia") -> str:
        """Async execution"""
        return self._run(wallet_address, network)


class GasEstimateInput(BaseModel):
    """Input schema for gas estimation tool"""
    to_address: str = Field(..., description="Destination address")
    amount: float = Field(..., description="Amount in ETH")
    network: str = Field(default="sepolia", description="Network name")


class GasEstimateTool(BaseTool):
    """Tool to estimate gas costs"""
    name: str = "estimate_gas"
    description: str = "Estimate gas cost for a transaction"
    args_schema: type[BaseModel] = GasEstimateInput
    blockchain_service: Optional[Any] = None
    
    def _run(self, to_address: str, amount: float, network: str = "sepolia") -> str:
        """Synchronous execution"""
        try:
            # Basic gas estimation (21000 for simple transfer)
            gas_limit = 21000
            gas_price = 20.0  # Gwei
            gas_cost_eth = (gas_limit * gas_price) / 1e9
            return f"Estimated gas: {gas_limit} units, cost: {gas_cost_eth:.6f} ETH"
        except Exception as e:
            logger.error(f"Error estimating gas: {e}")
            return f"Error: {str(e)}"
    
    async def _arun(self, to_address: str, amount: float, network: str = "sepolia") -> str:
        """Async execution"""
        return self._run(to_address, amount, network)


class TransactionHistoryInput(BaseModel):
    """Input schema for transaction history tool"""
    wallet_address: str = Field(..., description="Wallet address to get history for")
    limit: int = Field(default=10, description="Number of transactions to retrieve")


class TransactionHistoryTool(BaseTool):
    """Tool to get transaction history"""
    name: str = "get_transaction_history"
    description: str = "Get recent transaction history for a wallet"
    args_schema: type[BaseModel] = TransactionHistoryInput
    blockchain_service: Optional[Any] = None
    
    def _run(self, wallet_address: str, limit: int = 10) -> str:
        """Synchronous execution"""
        try:
            # This would query blockchain or database
            return f"Retrieved {limit} recent transactions for {wallet_address}"
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return f"Error: {str(e)}"
    
    async def _arun(self, wallet_address: str, limit: int = 10) -> str:
        """Async execution"""
        return self._run(wallet_address, limit)


class ValidateAddressInput(BaseModel):
    """Input schema for address validation tool"""
    address: str = Field(..., description="Ethereum address to validate")


class ValidateAddressTool(BaseTool):
    """Tool to validate Ethereum addresses"""
    name: str = "validate_address"
    description: str = "Validate if a string is a valid Ethereum address"
    args_schema: type[BaseModel] = ValidateAddressInput
    
    def _run(self, address: str) -> str:
        """Synchronous execution"""
        try:
            # Basic validation
            if address.startswith("0x") and len(address) == 42:
                return f"Valid Ethereum address: {address}"
            return f"Invalid Ethereum address: {address}"
        except Exception as e:
            logger.error(f"Error validating address: {e}")
            return f"Error: {str(e)}"
    
    async def _arun(self, address: str) -> str:
        """Async execution"""
        return self._run(address)


class APICallInput(BaseModel):
    """Input schema for API call tool"""
    provider: str = Field(..., description="API provider name (groq, google_ai, etc.)")
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(default="GET", description="HTTP method")


class APICallTool(BaseTool):
    """Tool to make external API calls"""
    name: str = "call_external_api"
    description: str = "Make HTTP requests to external APIs"
    args_schema: type[BaseModel] = APICallInput
    payment_service: Optional[Any] = None
    
    def _run(self, provider: str, endpoint: str, method: str = "GET") -> str:
        """Synchronous execution"""
        try:
            return f"API call to {provider}/{endpoint} using {method}"
        except Exception as e:
            logger.error(f"Error calling API: {e}")
            return f"Error: {str(e)}"
    
    async def _arun(self, provider: str, endpoint: str, method: str = "GET") -> str:
        """Async execution"""
        return self._run(provider, endpoint, method)


def get_planner_tools(blockchain_service: Optional[Any] = None) -> List[BaseTool]:
    """Get tools for the Planner agent"""
    return [
        WalletBalanceTool(blockchain_service=blockchain_service),
        GasEstimateTool(blockchain_service=blockchain_service),
        ValidateAddressTool(),
    ]


def get_executor_tools(blockchain_service: Optional[Any] = None) -> List[BaseTool]:
    """Get tools for the Executor agent"""
    return [
        WalletBalanceTool(blockchain_service=blockchain_service),
        GasEstimateTool(blockchain_service=blockchain_service),
        TransactionHistoryTool(blockchain_service=blockchain_service),
    ]


def get_evaluator_tools(blockchain_service: Optional[Any] = None) -> List[BaseTool]:
    """Get tools for the Evaluator agent"""
    return [
        TransactionHistoryTool(blockchain_service=blockchain_service),
        ValidateAddressTool(),
    ]


def get_communicator_tools(payment_service: Optional[Any] = None) -> List[BaseTool]:
    """Get tools for the Communicator agent"""
    return [
        APICallTool(payment_service=payment_service),
        ValidateAddressTool(),
    ]
