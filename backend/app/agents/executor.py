"""
Executor Agent - Blockchain Transaction Execution (FR-001, FR-005)

Responsibilities:
- Execute blockchain transactions
- Handle transaction signing
- Optimize gas costs
- Manage transaction lifecycle
- Handle retries and error recovery
- Multi-network support
"""

from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from enum import Enum
import logging
from datetime import datetime

from .base import BaseAgent, AgentConfig, DecisionContext, AgentResponse

logger = logging.getLogger(__name__)


class NetworkType(str, Enum):
    """Supported blockchain networks"""
    SEPOLIA = "sepolia"
    POLYGON_AMOY = "polygon_amoy"
    BASE_GOERLI = "base_goerli"


class TransactionStatus(str, Enum):
    """Transaction lifecycle states"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionPlan(BaseModel):
    """Plan for executing a transaction"""
    transaction_type: str = Field(..., description="Type of transaction")
    to_address: str = Field(..., description="Recipient address")
    amount: float = Field(..., description="Amount in ETH")
    network: NetworkType = Field(default=NetworkType.SEPOLIA)
    gas_limit: Optional[int] = Field(None, description="Gas limit")
    gas_price: Optional[int] = Field(None, description="Gas price in gwei")
    nonce: Optional[int] = Field(None, description="Transaction nonce")
    data: Optional[str] = Field(None, description="Transaction data for contract calls")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout: int = Field(default=120, description="Timeout in seconds")


class ExecutionResult(BaseModel):
    """Result of transaction execution"""
    success: bool
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    effective_gas_price: Optional[int] = None
    status: TransactionStatus
    error: Optional[str] = None
    receipt: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time: Optional[float] = None  # Seconds


class ExecutorAgent(BaseAgent):
    """
    Executor Agent for blockchain transaction execution.
    
    Uses Web3 and LangChain to:
    1. Execute approved transactions
    2. Sign transactions with agent wallet
    3. Optimize gas costs
    4. Handle transaction lifecycle
    5. Implement retry logic
    6. Support multiple networks
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        tools: List[BaseTool],
        config: Optional[AgentConfig] = None,
        memory_service: Optional[Any] = None,
        blockchain_service: Optional[Any] = None
    ):
        if config is None:
            config = AgentConfig(
                agent_type="executor",
                temperature=0.1,  # Very low temperature for deterministic execution
                max_iterations=5
            )
        
        super().__init__(llm, tools, config, memory_service)
        self.blockchain_service = blockchain_service
    
    def get_system_prompt(self) -> str:
        """System prompt for the Executor agent"""
        return """You are the Executor Agent in the WalletMind AI Autonomous Wallet System.

Your role is to EXECUTE BLOCKCHAIN TRANSACTIONS safely and efficiently.

RESPONSIBILITIES:
1. Execute approved transaction plans from the Planner Agent
2. Sign transactions using the agent's private key (securely managed)
3. Estimate and optimize gas costs
4. Submit transactions to the blockchain
5. Monitor transaction status until confirmation
6. Handle failures and implement retry logic
7. Support multiple blockchain networks (Sepolia, Polygon Amoy, Base Goerli)
8. Ensure transaction finality

EXECUTION WORKFLOW:
1. Receive approved transaction plan
2. Estimate gas cost and optimize
3. Construct transaction with proper nonce
4. Sign transaction with agent wallet
5. Submit to network via Web3 provider
6. Monitor transaction status
7. Wait for confirmation (1-3 blocks)
8. Return execution result with receipt

GAS OPTIMIZATION:
- Check current network gas prices
- Use EIP-1559 when available (maxFeePerGas, maxPriorityFeePerGas)
- Suggest network switching if gas is too high
- Implement gas limit estimation with 20% buffer
- Handle gas price spikes with retry logic

ERROR HANDLING:
- Insufficient gas: Re-estimate and retry
- Nonce too low: Fetch latest nonce and retry
- Transaction underpriced: Increase gas price and retry
- Network timeout: Switch RPC provider and retry
- Max retries reached: Return failure with detailed error

MULTI-NETWORK SUPPORT:
- Sepolia: Primary testnet for Ethereum
- Polygon Amoy: Low-cost alternative
- Base Goerli: Layer 2 for fast transactions
- Automatically switch based on:
  * Gas costs
  * Network congestion
  * Required confirmation time
  * Asset availability

SECURITY:
- Never expose private keys in logs
- Validate all addresses before sending
- Double-check amounts before signing
- Use hardware wallet integration when available
- Implement transaction limits at code level

TRANSACTION LIFECYCLE:
1. PENDING: Transaction created but not submitted
2. SUBMITTED: Sent to mempool
3. CONFIRMED: Included in block and confirmed
4. FAILED: Transaction reverted or rejected
5. CANCELLED: Manually cancelled by replacing with 0 ETH tx

OUTPUT:
Always return ExecutionResult with:
- success: true/false
- transaction_hash: Blockchain tx hash
- gas_used: Actual gas consumed
- status: Current transaction status
- error: Error message if failed
- receipt: Full transaction receipt

Be precise, secure, and efficient in all blockchain operations."""
    
    async def execute_transaction(
        self,
        context: DecisionContext,
        plan: ExecutionPlan,
        wallet_address: str
    ) -> ExecutionResult:
        """
        Execute a blockchain transaction
        
        Args:
            context: Decision context
            plan: Execution plan with transaction details
            wallet_address: Agent wallet address
        
        Returns:
            ExecutionResult with transaction receipt
        """
        logger.info(f"Executing transaction: {plan.transaction_type} on {plan.network}")
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Validate inputs
            self._validate_execution_plan(plan)
            
            # Step 2: Estimate gas
            gas_estimate = await self._estimate_gas(plan, wallet_address)
            if plan.gas_limit is None:
                plan.gas_limit = int(gas_estimate * 1.2)  # 20% buffer
            
            # Step 3: Get optimal gas price
            if plan.gas_price is None:
                plan.gas_price = await self._get_optimal_gas_price(plan.network)
            
            # Step 4: Get current nonce
            if plan.nonce is None:
                plan.nonce = await self._get_nonce(wallet_address, plan.network)
            
            # Step 5: Construct transaction
            tx_data = self._construct_transaction(plan, wallet_address)
            
            # Step 6: Sign transaction
            signed_tx = await self._sign_transaction(tx_data, wallet_address)
            
            # Step 7: Submit to network
            tx_hash = await self._submit_transaction(signed_tx, plan.network)
            logger.info(f"Transaction submitted: {tx_hash}")
            
            # Step 8: Wait for confirmation
            receipt = await self._wait_for_confirmation(
                tx_hash,
                plan.network,
                timeout=plan.timeout
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            if receipt and receipt.get("status") == 1:
                return ExecutionResult(
                    success=True,
                    transaction_hash=tx_hash,
                    block_number=receipt.get("blockNumber"),
                    gas_used=receipt.get("gasUsed"),
                    effective_gas_price=receipt.get("effectiveGasPrice"),
                    status=TransactionStatus.CONFIRMED,
                    receipt=receipt,
                    execution_time=execution_time
                )
            else:
                return ExecutionResult(
                    success=False,
                    transaction_hash=tx_hash,
                    status=TransactionStatus.FAILED,
                    error="Transaction reverted on-chain",
                    receipt=receipt,
                    execution_time=execution_time
                )
                
        except Exception as e:
            logger.error(f"Transaction execution failed: {str(e)}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ExecutionResult(
                success=False,
                status=TransactionStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )
    
    async def execute_with_retry(
        self,
        context: DecisionContext,
        plan: ExecutionPlan,
        wallet_address: str
    ) -> ExecutionResult:
        """
        Execute transaction with automatic retry logic
        """
        last_error = None
        
        for attempt in range(plan.max_retries):
            try:
                logger.info(f"Execution attempt {attempt + 1}/{plan.max_retries}")
                
                result = await self.execute_transaction(context, plan, wallet_address)
                
                if result.success:
                    return result
                
                # Handle specific errors
                last_error = result.error
                
                if "insufficient funds" in (last_error or "").lower():
                    # Can't retry - not enough balance
                    break
                
                if "nonce too low" in (last_error or "").lower():
                    # Update nonce and retry
                    plan.nonce = await self._get_nonce(wallet_address, plan.network)
                    continue
                
                if "underpriced" in (last_error or "").lower():
                    # Increase gas price by 20% and retry
                    plan.gas_price = int((plan.gas_price or 0) * 1.2)
                    continue
                
                # Generic retry with backoff
                await self._backoff(attempt)
                
            except Exception as e:
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                last_error = str(e)
                await self._backoff(attempt)
        
        # All retries exhausted
        return ExecutionResult(
            success=False,
            status=TransactionStatus.FAILED,
            error=f"Max retries ({plan.max_retries}) reached. Last error: {last_error}"
        )
    
    async def cancel_transaction(
        self,
        transaction_hash: str,
        wallet_address: str,
        network: NetworkType
    ) -> ExecutionResult:
        """
        Cancel a pending transaction by replacing it with 0 ETH tx
        """
        logger.info(f"Attempting to cancel transaction: {transaction_hash}")
        
        # Get original transaction
        original_tx = await self._get_transaction(transaction_hash, network)
        
        if not original_tx:
            return ExecutionResult(
                success=False,
                status=TransactionStatus.FAILED,
                error="Transaction not found"
            )
        
        # Create cancellation transaction with same nonce
        cancel_plan = ExecutionPlan(
            transaction_type="cancel",
            to_address=wallet_address,  # Send to self
            amount=0.0,
            network=network,
            nonce=original_tx.get("nonce"),
            gas_price=int(original_tx.get("gasPrice", 0) * 1.1)  # 10% higher
        )
        
        return await self.execute_transaction(
            DecisionContext(
                user_id="system",
                wallet_address=wallet_address,
                request="Cancel pending transaction"
            ),
            cancel_plan,
            wallet_address
        )
    
    async def speed_up_transaction(
        self,
        transaction_hash: str,
        wallet_address: str,
        network: NetworkType,
        gas_price_multiplier: float = 1.5
    ) -> ExecutionResult:
        """
        Speed up a pending transaction by resubmitting with higher gas
        """
        logger.info(f"Attempting to speed up transaction: {transaction_hash}")
        
        original_tx = await self._get_transaction(transaction_hash, network)
        
        if not original_tx:
            return ExecutionResult(
                success=False,
                status=TransactionStatus.FAILED,
                error="Transaction not found"
            )
        
        # Resubmit with higher gas price
        speedup_plan = ExecutionPlan(
            transaction_type="speedup",
            to_address=original_tx.get("to"),
            amount=float(original_tx.get("value", 0)) / 1e18,  # Wei to ETH
            network=network,
            nonce=original_tx.get("nonce"),
            gas_price=int(original_tx.get("gasPrice", 0) * gas_price_multiplier),
            data=original_tx.get("input")
        )
        
        return await self.execute_transaction(
            DecisionContext(
                user_id="system",
                wallet_address=wallet_address,
                request="Speed up pending transaction"
            ),
            speedup_plan,
            wallet_address
        )
    
    # Helper methods (implementations delegated to blockchain service)
    
    def _validate_execution_plan(self, plan: ExecutionPlan):
        """Validate execution plan parameters"""
        if not plan.to_address.startswith("0x") or len(plan.to_address) != 42:
            raise ValueError(f"Invalid address: {plan.to_address}")
        
        if plan.amount < 0:
            raise ValueError("Amount cannot be negative")
    
    async def _estimate_gas(self, plan: ExecutionPlan, from_address: str) -> int:
        """Estimate gas for transaction"""
        if self.blockchain_service:
            return await self.blockchain_service.estimate_gas(plan, from_address)
        return 21000  # Default for simple transfer
    
    async def _get_optimal_gas_price(self, network: NetworkType) -> int:
        """Get optimal gas price for network"""
        if self.blockchain_service:
            return await self.blockchain_service.get_gas_price(network)
        return 1000000000  # Default 1 gwei
    
    async def _get_nonce(self, address: str, network: NetworkType) -> int:
        """Get current nonce for address"""
        if self.blockchain_service:
            return await self.blockchain_service.get_nonce(address, network)
        return 0
    
    def _construct_transaction(self, plan: ExecutionPlan, from_address: str) -> Dict[str, Any]:
        """Construct transaction dictionary"""
        return {
            "from": from_address,
            "to": plan.to_address,
            "value": int(plan.amount * 1e18),  # ETH to Wei
            "gas": plan.gas_limit,
            "gasPrice": plan.gas_price,
            "nonce": plan.nonce,
            "data": plan.data or "0x"
        }
    
    async def _sign_transaction(self, tx_data: Dict[str, Any], wallet_address: str) -> str:
        """Sign transaction with agent wallet"""
        if self.blockchain_service:
            return await self.blockchain_service.sign_transaction(tx_data, wallet_address)
        raise NotImplementedError("Blockchain service required for signing")
    
    async def _submit_transaction(self, signed_tx: str, network: NetworkType) -> str:
        """Submit signed transaction to network"""
        if self.blockchain_service:
            return await self.blockchain_service.submit_transaction(signed_tx, network)
        raise NotImplementedError("Blockchain service required for submission")
    
    async def _wait_for_confirmation(
        self,
        tx_hash: str,
        network: NetworkType,
        timeout: int = 120,
        confirmations: int = 1
    ) -> Optional[Dict[str, Any]]:
        """Wait for transaction confirmation"""
        if self.blockchain_service:
            return await self.blockchain_service.wait_for_confirmation(
                tx_hash, network, timeout, confirmations
            )
        return None
    
    async def _get_transaction(self, tx_hash: str, network: NetworkType) -> Optional[Dict[str, Any]]:
        """Get transaction details"""
        if self.blockchain_service:
            return await self.blockchain_service.get_transaction(tx_hash, network)
        return None
    
    async def _backoff(self, attempt: int):
        """Exponential backoff between retries"""
        import asyncio
        wait_time = min(2 ** attempt, 30)  # Max 30 seconds
        logger.info(f"Waiting {wait_time}s before retry...")
        await asyncio.sleep(wait_time)