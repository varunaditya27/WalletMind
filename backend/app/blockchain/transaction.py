"""
Transaction building and execution with retry logic

Provides high-level transaction management with EIP-1559 support.
"""

import logging
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from web3 import Web3
from web3.types import TxParams
from eth_account.signers.local import LocalAccount

from .provider import Web3Provider
from .networks import NetworkType

logger = logging.getLogger(__name__)


@dataclass
class TransactionConfig:
    """Transaction configuration"""
    gas_limit: Optional[int] = None
    max_priority_fee: Optional[int] = None  # EIP-1559
    max_fee_per_gas: Optional[int] = None   # EIP-1559
    gas_price: Optional[int] = None          # Legacy
    nonce: Optional[int] = None
    value: int = 0
    chain_id: Optional[int] = None


@dataclass
class TransactionReceipt:
    """Transaction receipt wrapper"""
    tx_hash: str
    block_number: int
    status: int  # 1 = success, 0 = failure
    gas_used: int
    effective_gas_price: int
    from_address: str
    to_address: Optional[str]
    contract_address: Optional[str]
    logs: list


class TransactionBuilder:
    """
    Transaction builder with EIP-1559 support.
    
    Features:
    - Automatic gas estimation
    - EIP-1559 (Type 2) transaction support
    - Legacy (Type 0) transaction fallback
    - Chain ID detection
    """
    
    def __init__(self, web3_provider: Optional[Web3Provider] = None):
        """
        Initialize transaction builder.
        
        Args:
            web3_provider: Optional Web3Provider (uses singleton if None)
        """
        self.web3_provider = web3_provider or Web3Provider.get_instance()
    
    def build_transfer(
        self,
        from_address: str,
        to_address: str,
        amount_wei: int,
        config: Optional[TransactionConfig] = None
    ) -> Dict[str, Any]:
        """
        Build simple ETH transfer transaction.
        
        Args:
            from_address: Sender address
            to_address: Recipient address
            amount_wei: Amount in wei
            config: Optional transaction configuration
            
        Returns:
            Transaction dict ready to sign
        """
        config = config or TransactionConfig()
        web3 = self.web3_provider.get_web3()
        
        # Base transaction
        tx: Dict[str, Any] = {
            'from': web3.to_checksum_address(from_address),
            'to': web3.to_checksum_address(to_address),
            'value': amount_wei,
        }
        
        # Add nonce
        if config.nonce is not None:
            tx['nonce'] = config.nonce
        else:
            tx['nonce'] = web3.eth.get_transaction_count(from_address)
        
        # Add chain ID
        if config.chain_id is not None:
            tx['chainId'] = config.chain_id
        else:
            tx['chainId'] = web3.eth.chain_id
        
        # Try EIP-1559 first
        if self._supports_eip1559():
            self._add_eip1559_gas(tx, config)
        else:
            self._add_legacy_gas(tx, config)
        
        # Estimate gas if not provided
        if config.gas_limit is not None:
            tx['gas'] = config.gas_limit
        else:
            tx['gas'] = self.estimate_gas(tx)
        
        logger.debug(f"Built transfer tx: {amount_wei} wei to {to_address}")
        
        return tx
    
    def build_contract_call(
        self,
        from_address: str,
        contract_address: str,
        function_call,
        config: Optional[TransactionConfig] = None
    ) -> Dict[str, Any]:
        """
        Build contract function call transaction.
        
        Args:
            from_address: Caller address
            contract_address: Contract address
            function_call: Contract function call object (from web3.py)
            config: Optional transaction configuration
            
        Returns:
            Transaction dict ready to sign
        """
        config = config or TransactionConfig()
        web3 = self.web3_provider.get_web3()
        
        # Build base transaction from function call
        tx = function_call.build_transaction({
            'from': web3.to_checksum_address(from_address),
            'value': config.value,
        })
        
        # Add nonce
        if config.nonce is not None:
            tx['nonce'] = config.nonce
        else:
            tx['nonce'] = web3.eth.get_transaction_count(from_address)
        
        # Add chain ID
        if config.chain_id is not None:
            tx['chainId'] = config.chain_id
        else:
            tx['chainId'] = web3.eth.chain_id
        
        # Try EIP-1559 first
        if self._supports_eip1559():
            self._add_eip1559_gas(tx, config)
        else:
            self._add_legacy_gas(tx, config)
        
        # Override gas if provided
        if config.gas_limit is not None:
            tx['gas'] = config.gas_limit
        
        logger.debug(f"Built contract call tx to {contract_address}")
        
        return tx
    
    def estimate_gas(self, transaction: Dict[str, Any]) -> int:
        """
        Estimate gas for transaction.
        
        Args:
            transaction: Transaction dict
            
        Returns:
            Estimated gas limit
        """
        web3 = self.web3_provider.get_web3()
        
        # Remove gas fields for estimation
        tx_copy = transaction.copy()
        tx_copy.pop('gas', None)
        tx_copy.pop('gasPrice', None)
        tx_copy.pop('maxFeePerGas', None)
        tx_copy.pop('maxPriorityFeePerGas', None)
        
        estimated = web3.eth.estimate_gas(tx_copy)
        
        # Add 20% buffer
        gas_limit = int(estimated * 1.2)
        
        logger.debug(f"Estimated gas: {estimated}, with buffer: {gas_limit}")
        
        return gas_limit
    
    def set_eip1559_gas(
        self,
        transaction: Dict[str, Any],
        max_priority_fee: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None
    ) -> None:
        """
        Set EIP-1559 gas parameters.
        
        Args:
            transaction: Transaction dict to modify
            max_priority_fee: Max priority fee (tip) in wei
            max_fee_per_gas: Max fee per gas in wei
        """
        web3 = self.web3_provider.get_web3()
        
        # Get base fee from latest block
        latest_block = web3.eth.get_block('latest')
        base_fee = latest_block.get('baseFeePerGas', 0)
        
        # Set priority fee (tip)
        if max_priority_fee is None:
            max_priority_fee = web3.eth.max_priority_fee
        
        transaction['maxPriorityFeePerGas'] = max_priority_fee
        
        # Set max fee
        if max_fee_per_gas is None:
            # Max fee = 2 * base fee + priority fee (common heuristic)
            max_fee_per_gas = (2 * base_fee) + max_priority_fee
        
        transaction['maxFeePerGas'] = max_fee_per_gas
        
        # Remove legacy gas price if present
        transaction.pop('gasPrice', None)
        
        logger.debug(f"Set EIP-1559 gas: priority={max_priority_fee}, max={max_fee_per_gas}")
    
    def _supports_eip1559(self) -> bool:
        """Check if network supports EIP-1559"""
        try:
            web3 = self.web3_provider.get_web3()
            latest_block = web3.eth.get_block('latest')
            return 'baseFeePerGas' in latest_block
        except Exception as e:
            logger.warning(f"Failed to check EIP-1559 support: {e}")
            return False
    
    def _add_eip1559_gas(
        self,
        tx: Dict[str, Any],
        config: TransactionConfig
    ) -> None:
        """Add EIP-1559 gas parameters to transaction"""
        web3 = self.web3_provider.get_web3()
        
        # Get base fee
        latest_block = web3.eth.get_block('latest')
        base_fee = latest_block.get('baseFeePerGas', 0)
        
        # Set priority fee
        if config.max_priority_fee is not None:
            tx['maxPriorityFeePerGas'] = config.max_priority_fee
        else:
            tx['maxPriorityFeePerGas'] = web3.eth.max_priority_fee
        
        # Set max fee
        if config.max_fee_per_gas is not None:
            tx['maxFeePerGas'] = config.max_fee_per_gas
        else:
            tx['maxFeePerGas'] = (2 * base_fee) + tx['maxPriorityFeePerGas']
    
    def _add_legacy_gas(
        self,
        tx: Dict[str, Any],
        config: TransactionConfig
    ) -> None:
        """Add legacy gas price to transaction"""
        web3 = self.web3_provider.get_web3()
        
        if config.gas_price is not None:
            tx['gasPrice'] = config.gas_price
        else:
            tx['gasPrice'] = web3.eth.gas_price


class TransactionExecutor:
    """
    Transaction executor with retry logic.
    
    Features:
    - Automatic retry with exponential backoff
    - Transaction confirmation waiting
    - Status verification
    - Nonce management
    """
    
    def __init__(
        self,
        web3_provider: Optional[Web3Provider] = None,
        max_retries: int = 3,
        initial_wait: int = 2
    ):
        """
        Initialize transaction executor.
        
        Args:
            web3_provider: Optional Web3Provider (uses singleton if None)
            max_retries: Maximum retry attempts
            initial_wait: Initial wait time in seconds (doubles each retry)
        """
        self.web3_provider = web3_provider or Web3Provider.get_instance()
        self.max_retries = max_retries
        self.initial_wait = initial_wait
    
    def execute(
        self,
        transaction: Dict[str, Any],
        account: LocalAccount
    ) -> str:
        """
        Execute transaction (sign and send).
        
        Args:
            transaction: Built transaction dict
            account: Account to sign with
            
        Returns:
            Transaction hash
        """
        web3 = self.web3_provider.get_web3()
        
        # Sign transaction
        signed_tx = account.sign_transaction(transaction)
        
        # Send transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Transaction sent: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    def execute_with_retry(
        self,
        transaction: Dict[str, Any],
        account: LocalAccount
    ) -> str:
        """
        Execute transaction with retry logic.
        
        Args:
            transaction: Built transaction dict
            account: Account to sign with
            
        Returns:
            Transaction hash
        """
        last_error = None
        wait_time = self.initial_wait
        
        for attempt in range(self.max_retries):
            try:
                return self.execute(transaction, account)
            
            except Exception as e:
                last_error = e
                logger.warning(f"Transaction attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    wait_time *= 2
        
        # All retries failed
        raise Exception(f"Transaction failed after {self.max_retries} attempts: {last_error}")
    
    def wait_for_confirmation(
        self,
        tx_hash: str,
        timeout: int = 120,
        poll_interval: float = 1.0
    ) -> TransactionReceipt:
        """
        Wait for transaction confirmation.
        
        Args:
            tx_hash: Transaction hash
            timeout: Maximum wait time in seconds
            poll_interval: Polling interval in seconds
            
        Returns:
            TransactionReceipt
        """
        web3 = self.web3_provider.get_web3()
        
        receipt = web3.eth.wait_for_transaction_receipt(
            tx_hash,
            timeout=timeout,
            poll_latency=poll_interval
        )
        
        # Convert to TransactionReceipt
        tx_receipt = TransactionReceipt(
            tx_hash=receipt['transactionHash'].hex(),
            block_number=receipt['blockNumber'],
            status=receipt['status'],
            gas_used=receipt['gasUsed'],
            effective_gas_price=receipt.get('effectiveGasPrice', 0),
            from_address=receipt['from'],
            to_address=receipt.get('to'),
            contract_address=receipt.get('contractAddress'),
            logs=list(receipt['logs'])
        )
        
        logger.info(f"Transaction confirmed: {tx_hash}, status={tx_receipt.status}")
        
        return tx_receipt
    
    def verify_success(self, receipt: TransactionReceipt) -> bool:
        """
        Verify transaction succeeded.
        
        Args:
            receipt: Transaction receipt
            
        Returns:
            True if successful
        """
        return receipt.status == 1

