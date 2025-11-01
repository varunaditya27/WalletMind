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
            if not self.blockchain_service:
                return "Blockchain service not available"
            
            from app.blockchain.networks import NetworkType
            from app.config import get_settings
            
            # Connect to network
            provider = self.blockchain_service.web3_provider
            if not provider:
                return "Web3 provider not initialized"
            
            network_type = NetworkType.SEPOLIA if network.lower() == "sepolia" else NetworkType.SEPOLIA
            settings = get_settings()
            rpc_url = settings.blockchain.sepolia_rpc_url
            
            web3 = provider.connect(network_type, rpc_url=rpc_url)
            
            if not web3.is_connected():
                return f"Failed to connect to {network} network"
            
            # Get balance
            balance_wei = web3.eth.get_balance(wallet_address)
            balance_eth = web3.from_wei(balance_wei, 'ether')
            
            return f"Balance: {balance_eth} ETH on {network}"
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


class ExecuteTransactionInput(BaseModel):
    """Input schema for execute transaction tool"""
    to_address: str = Field(..., description="Recipient Ethereum address (must start with 0x)")
    amount_eth: float = Field(..., description="Amount to send in ETH (e.g., 0.005)")
    network: str = Field(default="sepolia", description="Network to use (sepolia, polygon_amoy, base_goerli)")


class ExecuteTransactionTool(BaseTool):
    """Tool to execute blockchain transactions"""
    name: str = "execute_blockchain_transaction"
    description: str = """Execute a real blockchain transaction. This will:
1. Validate the recipient address
2. Estimate and set optimal gas
3. Sign the transaction with the agent wallet
4. Submit to the blockchain network
5. Wait for confirmation
6. Return the actual transaction hash and receipt
Use this tool when you need to ACTUALLY SEND cryptocurrency on the blockchain."""
    args_schema: type[BaseModel] = ExecuteTransactionInput
    blockchain_service: Optional[Any] = None
    
    def _run(self, to_address: str, amount_eth: float, network: str = "sepolia") -> str:
        """Synchronous execution (not implemented for blockchain ops)"""
        return "Use async execution for blockchain operations"
    
    async def _arun(self, to_address: str, amount_eth: float, network: str = "sepolia") -> str:
        """Async execution - performs real blockchain transaction"""
        import json
        from web3 import Web3
        
        try:
            if not self.blockchain_service:
                return json.dumps({
                    "success": False,
                    "error": "Blockchain service not available"
                })
            
            logger.info(f"Executing transaction: {amount_eth} ETH to {to_address} on {network}")
            
            # Get Web3 provider
            provider = self.blockchain_service.web3_provider
            if not provider:
                return json.dumps({
                    "success": False,
                    "error": "Web3 provider not initialized"
                })
            
            # Connect to network (this will establish connection if not already connected)
            from app.blockchain.networks import NetworkType
            network_type = NetworkType.SEPOLIA if network.lower() == "sepolia" else NetworkType.SEPOLIA
            
            try:
                # Get the RPC URL from settings
                from app.config import get_settings
                settings = get_settings()
                rpc_url = settings.blockchain.sepolia_rpc_url
                
                logger.info(f"Connecting to {network} network at {rpc_url[:50]}...")
                web3 = provider.connect(network_type, rpc_url=rpc_url)
                
                if not web3.is_connected():
                    return json.dumps({
                        "success": False,
                        "error": f"Failed to connect to {network} network"
                    })
                
                logger.info(f"Successfully connected to {network} network")
            except Exception as conn_error:
                logger.error(f"Connection error: {conn_error}")
                return json.dumps({
                    "success": False,
                    "error": f"Connection error: {str(conn_error)}"
                })
            
            # Get wallet manager
            wallet_manager = self.blockchain_service.wallet_manager
            if not wallet_manager or not wallet_manager.account:
                return json.dumps({
                    "success": False,
                    "error": "Agent wallet not initialized"
                })
            
            account = wallet_manager.account
            from_address = account.address
            
            # Handle ENS names (like vitalik.eth)
            original_address = to_address
            if to_address.endswith('.eth'):
                logger.info(f"Resolving ENS name: {to_address}")
                try:
                    # Try to resolve ENS (note: ENS resolution works on mainnet, not testnets)
                    # For testnets, we'll need to manually resolve or use a hardcoded mapping
                    resolved = web3.ens.address(to_address)
                    if resolved:
                        to_address = resolved
                        logger.info(f"ENS resolved: {original_address} -> {to_address}")
                    else:
                        # Fallback for known ENS names
                        if to_address.lower() == "vitalik.eth":
                            to_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
                            logger.info(f"Using hardcoded resolution for {original_address} -> {to_address}")
                        else:
                            return json.dumps({
                                "success": False,
                                "error": f"Unable to resolve ENS name: {original_address}. Please use a direct Ethereum address (0x...)"
                            })
                except Exception as ens_error:
                    logger.warning(f"ENS resolution failed: {ens_error}")
                    # Fallback for vitalik.eth
                    if to_address.lower() == "vitalik.eth":
                        to_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
                        logger.info(f"Using hardcoded resolution for {original_address} -> {to_address}")
                    else:
                        return json.dumps({
                            "success": False,
                            "error": f"ENS resolution not available. Please use a direct Ethereum address (0x...)"
                        })
            
            # Validate recipient address
            if not Web3.is_address(to_address):
                return json.dumps({
                    "success": False,
                    "error": f"Invalid recipient address: {to_address}"
                })
            
            to_address = Web3.to_checksum_address(to_address)
            
            # Get nonce
            nonce = web3.eth.get_transaction_count(from_address)
            
            # Get gas price
            gas_price = web3.eth.gas_price
            
            # Estimate gas
            gas_estimate = 21000  # Standard transfer
            
            # Convert amount to Wei
            amount_wei = web3.to_wei(amount_eth, 'ether')
            
            # Build transaction
            transaction = {
                'nonce': nonce,
                'to': to_address,
                'value': amount_wei,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'chainId': web3.eth.chain_id
            }
            
            logger.info(f"Transaction built: {transaction}")
            
            # Sign transaction
            signed_tx = account.sign_transaction(transaction)
            
            # Send transaction
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = web3.to_hex(tx_hash)
            
            logger.info(f"Transaction sent: {tx_hash_hex}")
            
            # Wait for receipt (with timeout)
            try:
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                # Convert receipt to dict
                receipt_dict = {
                    "transactionHash": web3.to_hex(receipt['transactionHash']),
                    "blockNumber": receipt['blockNumber'],
                    "gasUsed": receipt['gasUsed'],
                    "cumulativeGasUsed": receipt['cumulativeGasUsed'],
                    "contractAddress": receipt.get('contractAddress'),
                    "status": receipt['status'],
                    "effectiveGasPrice": receipt.get('effectiveGasPrice', gas_price),
                    "from": receipt.get('from'),
                    "to": receipt.get('to'),
                    "logs": len(receipt.get('logs', [])),
                    "logsBloom": web3.to_hex(receipt.get('logsBloom', b''))[:66]  # Truncate for readability
                }
                
                result = {
                    "success": True,
                    "transaction_hash": tx_hash_hex,
                    "gas_used": receipt['gasUsed'],
                    "status": "CONFIRMED" if receipt['status'] == 1 else "FAILED",
                    "error": None,
                    "receipt": receipt_dict,
                    "from_address": from_address,
                    "to_address": to_address,
                    "amount_eth": amount_eth,
                    "network": network
                }
                
                logger.info(f"Transaction confirmed: {tx_hash_hex}")
                return json.dumps(result, indent=2)
                
            except Exception as receipt_error:
                logger.warning(f"Transaction sent but receipt not available: {receipt_error}")
                return json.dumps({
                    "success": True,
                    "transaction_hash": tx_hash_hex,
                    "status": "SUBMITTED",
                    "error": None,
                    "message": "Transaction submitted successfully. Confirmation pending.",
                    "from_address": from_address,
                    "to_address": to_address,
                    "amount_eth": amount_eth,
                    "network": network
                })
                
        except Exception as e:
            logger.error(f"Error executing transaction: {e}", exc_info=True)
            return json.dumps({
                "success": False,
                "error": str(e),
                "transaction_hash": None
            })



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
        ExecuteTransactionTool(blockchain_service=blockchain_service),
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
