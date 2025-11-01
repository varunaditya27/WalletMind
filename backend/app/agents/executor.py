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

Your role is to EXECUTE BLOCKCHAIN TRANSACTIONS safely and efficiently using real blockchain operations.

CRITICAL: You have access to the 'execute_blockchain_transaction' tool which performs REAL transactions on the blockchain. You MUST use this tool to execute transactions - never return mock or placeholder data.

RESPONSIBILITIES:
1. Execute approved transaction plans from the Planner Agent using the execute_blockchain_transaction tool
2. Parse transaction requests to extract: recipient address, amount in ETH, and network
3. Call execute_blockchain_transaction with the correct parameters
4. Return the ACTUAL transaction hash, gas used, and receipt from the blockchain
5. Handle any errors returned by the tool

EXECUTION WORKFLOW:
1. Receive approved transaction plan from Planner
2. Extract recipient address (must be valid Ethereum address starting with 0x)
3. Extract amount in ETH (e.g., 0.005)
4. Determine network (sepolia, polygon_amoy, or base_goerli)
5. Call execute_blockchain_transaction tool with these parameters
6. Tool will handle: gas estimation, signing, submission, and confirmation
7. Return the tool's response which contains REAL blockchain data

IMPORTANT - NEVER FABRICATE DATA:
- DO NOT return placeholder transaction hashes like "0x1234567890abcdef..."
- DO NOT make up block numbers like "12345"
- DO NOT return mock gas values like "20000"
- ALWAYS use the execute_blockchain_transaction tool for real transactions
- Return the EXACT response from the tool, which contains real blockchain data

EXAMPLE FLOW:
User request: "send 0.005 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb27"
1. Extract: to_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb27", amount_eth=0.005, network="sepolia"
2. Call: execute_blockchain_transaction(to_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb27", amount_eth=0.005, network="sepolia")
3. Wait for tool response with REAL transaction data
4. Return the tool's response verbatim

ERROR HANDLING:
- If tool returns error: Report it clearly to the user
- If address is invalid: Tool will reject it - explain to user
- If insufficient balance: Tool will report it - suggest checking balance
- If network error: Tool will timeout - suggest retrying

TRANSACTION VERIFICATION:
- Tool returns actual tx hash that can be verified on blockchain explorer
- Tool returns real block number from blockchain
- Tool returns actual gas used from receipt
- Tool returns real contract addresses (or null for simple transfers)

OUTPUT FORMAT:
Return the JSON response from the execute_blockchain_transaction tool, which includes:
- success: boolean
- transaction_hash: Real blockchain transaction hash
- gas_used: Actual gas consumed
- status: CONFIRMED, SUBMITTED, or FAILED
- receipt: Full blockchain receipt with real data
- from_address: Agent wallet address
- to_address: Recipient address
- amount_eth: Amount sent
- network: Network used

Be precise, secure, and use ONLY real blockchain data from the tools."""
    
    async def log_decision_on_chain(
        self,
        decision_data: Dict[str, Any],
        agent_wallet_address: str,
        network: NetworkType = NetworkType.SEPOLIA
    ) -> tuple[str, str, bool]:
        """
        Log decision to IPFS and then on-chain before execution.
        
        Implements the workflow step:
        "The ExecutorAgent creates a detailed JSON object containing the transaction plan,
        the risk analysis, and a timestamp. It then computes a Keccak-256 hash of this data
        and uploads the JSON object to IPFS, receiving a unique content identifier (CID) in return."
        
        Args:
            decision_data: Dictionary with transaction plan, risk analysis, timestamp
            agent_wallet_address: Address of the AgentWallet contract
            network: Blockchain network to use
            
        Returns:
            Tuple of (decision_hash, ipfs_cid, success)
        """
        logger.info("Logging decision to IPFS and blockchain...")
        
        try:
            # Step 1: Upload to IPFS
            from app.storage.ipfs import get_ipfs_service
            ipfs_service = get_ipfs_service()
            
            ipfs_cid, decision_hash = await ipfs_service.upload_decision(decision_data)
            logger.info(f"Decision uploaded to IPFS: CID={ipfs_cid}, Hash={decision_hash}")
            
            # Step 2: Call logDecision on AgentWallet contract
            if self.blockchain_service:
                tx_success = await self.blockchain_service.log_decision(
                    agent_wallet_address=agent_wallet_address,
                    decision_hash=decision_hash,
                    ipfs_cid=ipfs_cid,
                    network=network
                )
                
                if tx_success:
                    logger.info(f"Decision logged on-chain: {decision_hash}")
                    return decision_hash, ipfs_cid, True
                else:
                    logger.error("Failed to log decision on-chain")
                    return decision_hash, ipfs_cid, False
            else:
                logger.warning("Blockchain service not available, skipping on-chain logging")
                return decision_hash, ipfs_cid, False
                
        except Exception as e:
            logger.error(f"Error logging decision: {e}", exc_info=True)
            return "", "", False
    
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