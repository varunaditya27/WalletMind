"""
Python wrapper for AgentWallet.sol smart contract (FR-004, FR-007, FR-008, NFR-005)

Provides high-level interface for interacting with deployed AgentWallet contracts.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from web3 import Web3
from web3.contract import Contract
from eth_account.signers.local import LocalAccount

logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """Decision structure from contract"""
    decision_hash: bytes
    timestamp: int
    executor: str
    ipfs_proof: str
    executed: bool
    amount: int
    payee: str


@dataclass
class TransactionRecord:
    """Transaction record from contract"""
    decision_hash: bytes
    timestamp: int
    to: str
    value: int
    data: bytes
    success: bool
    category: str


class AgentWalletContract:
    """
    Python wrapper for AgentWallet smart contract.
    
    Features:
    - Decision logging before execution (FR-007)
    - Transaction verification and execution (FR-004)
    - Spending limit management (NFR-005)
    - Transaction history retrieval (FR-008)
    - Emergency pause controls
    """
    
    def __init__(
        self,
        web3: Web3,
        contract_address: str,
        abi_path: Optional[Path] = None
    ):
        """
        Initialize AgentWallet contract wrapper.
        
        Args:
            web3: Web3 instance connected to network
            contract_address: Deployed contract address
            abi_path: Path to ABI JSON file (defaults to packaged ABI)
        """
        self.web3 = web3
        self.contract_address = web3.to_checksum_address(contract_address)
        
        # Load ABI
        if abi_path is None:
            abi_path = Path(__file__).parent / "abis" / "AgentWallet.json"
        
        with open(abi_path, 'r') as f:
            artifact = json.load(f)
            self.abi = artifact['abi']
        
        # Create contract instance
        self.contract: Contract = web3.eth.contract(
            address=self.contract_address,
            abi=self.abi
        )
        
        logger.info(f"AgentWallet contract initialized at {self.contract_address}")
    
    # ========== Read Methods ==========
    
    def get_owner(self) -> str:
        """Get contract owner address"""
        return self.contract.functions.owner().call()
    
    def is_paused(self) -> bool:
        """Check if contract is paused"""
        return self.contract.functions.paused().call()
    
    def get_decision(self, decision_hash: bytes) -> Decision:
        """
        Get decision data by hash.
        
        Args:
            decision_hash: 32-byte decision hash
            
        Returns:
            Decision object
        """
        result = self.contract.functions.decisions(decision_hash).call()
        
        return Decision(
            decision_hash=result[0],
            timestamp=result[1],
            executor=result[2],
            ipfs_proof=result[3],
            executed=result[4],
            amount=result[5],
            payee=result[6]
        )
    
    def get_spending_limit(self, token_address: str = "0x0000000000000000000000000000000000000000") -> int:
        """
        Get spending limit for token.
        
        Args:
            token_address: Token address (0x0 for ETH)
            
        Returns:
            Spending limit in wei
        """
        checksum_address = self.web3.to_checksum_address(token_address)
        return self.contract.functions.spendingLimits(checksum_address).call()
    
    def get_transaction_count(self) -> int:
        """Get total number of transactions"""
        return self.contract.functions.getTransactionCount().call()
    
    def get_transaction_history(
        self,
        start_index: int = 0,
        count: int = 10
    ) -> List[TransactionRecord]:
        """
        Get transaction history.
        
        Args:
            start_index: Starting index
            count: Number of records to retrieve
            
        Returns:
            List of TransactionRecord objects
        """
        total_count = self.get_transaction_count()
        end_index = min(start_index + count, total_count)
        
        records = []
        for i in range(start_index, end_index):
            result = self.contract.functions.transactionHistory(i).call()
            
            records.append(TransactionRecord(
                decision_hash=result[0],
                timestamp=result[1],
                to=result[2],
                value=result[3],
                data=result[4],
                success=result[5],
                category=result[6]
            ))
        
        return records
    
    def get_latest_transactions(self, count: int = 10) -> List[TransactionRecord]:
        """
        Get most recent transactions.
        
        Args:
            count: Number of recent transactions
            
        Returns:
            List of TransactionRecord objects
        """
        total_count = self.get_transaction_count()
        start_index = max(0, total_count - count)
        
        return self.get_transaction_history(start_index, count)
    
    # ========== Write Methods ==========
    
    def log_decision(
        self,
        decision_hash: bytes,
        ipfs_cid: str,
        amount: int,
        payee: str,
        account: LocalAccount,
        gas_limit: Optional[int] = None
    ) -> str:
        """
        Log AI decision before execution (FR-007).
        
        Args:
            decision_hash: 32-byte hash of decision
            ipfs_cid: IPFS CID containing full decision data
            amount: Transaction amount in wei
            payee: Recipient address
            account: Account to sign transaction
            gas_limit: Optional gas limit override
            
        Returns:
            Transaction hash
        """
        checksum_payee = self.web3.to_checksum_address(payee)
        
        # Build transaction
        tx = self.contract.functions.logDecision(
            decision_hash,
            ipfs_cid,
            amount,
            checksum_payee
        ).build_transaction({
            'from': account.address,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': gas_limit or 200000,
            'gasPrice': self.web3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Decision logged: {decision_hash.hex()}, tx: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    def verify_and_execute(
        self,
        decision_hash: bytes,
        payee: str,
        amount: int,
        account: LocalAccount,
        gas_limit: Optional[int] = None
    ) -> str:
        """
        Verify and execute pre-logged decision (FR-004).
        
        Args:
            decision_hash: 32-byte decision hash
            payee: Recipient address
            amount: Amount to transfer in wei
            account: Account to sign transaction
            gas_limit: Optional gas limit override
            
        Returns:
            Transaction hash
        """
        checksum_payee = self.web3.to_checksum_address(payee)
        
        # Build transaction
        tx = self.contract.functions.verifyAndExecute(
            decision_hash,
            checksum_payee,
            amount
        ).build_transaction({
            'from': account.address,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': gas_limit or 300000,
            'gasPrice': self.web3.eth.gas_price,
            'value': amount  # Send ETH with transaction
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Decision executed: {decision_hash.hex()}, tx: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    def set_spending_limit(
        self,
        token_address: str,
        limit: int,
        account: LocalAccount,
        gas_limit: Optional[int] = None
    ) -> str:
        """
        Set spending limit for token (NFR-005).
        
        Args:
            token_address: Token address (0x0 for ETH)
            limit: Spending limit in wei
            account: Owner account to sign transaction
            gas_limit: Optional gas limit override
            
        Returns:
            Transaction hash
        """
        checksum_token = self.web3.to_checksum_address(token_address)
        
        # Build transaction
        tx = self.contract.functions.setSpendingLimit(
            checksum_token,
            limit
        ).build_transaction({
            'from': account.address,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': gas_limit or 100000,
            'gasPrice': self.web3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Spending limit set for {token_address}: {limit} wei, tx: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    def set_paused(
        self,
        paused: bool,
        account: LocalAccount,
        gas_limit: Optional[int] = None
    ) -> str:
        """
        Set contract pause state (emergency control).
        
        Args:
            paused: True to pause, False to unpause
            account: Owner account to sign transaction
            gas_limit: Optional gas limit override
            
        Returns:
            Transaction hash
        """
        # Build transaction
        tx = self.contract.functions.setPaused(paused).build_transaction({
            'from': account.address,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': gas_limit or 50000,
            'gasPrice': self.web3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Contract paused={paused}, tx: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    def fund_wallet(
        self,
        account: LocalAccount,
        amount: int
    ) -> str:
        """
        Send ETH to contract wallet.
        
        Args:
            account: Account to send from
            amount: Amount in wei
            
        Returns:
            Transaction hash
        """
        tx = {
            'from': account.address,
            'to': self.contract_address,
            'value': amount,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': 21000,
            'gasPrice': self.web3.eth.gas_price
        }
        
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Wallet funded with {amount} wei, tx: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    # ========== Event Filtering ==========
    
    def get_decision_logged_events(
        self,
        from_block: int = 0,
        to_block: str = 'latest'
    ) -> List[Dict[str, Any]]:
        """
        Get DecisionLogged events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block ('latest' for current)
            
        Returns:
            List of event dicts
        """
        event_filter = self.contract.events.DecisionLogged.create_filter(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        return event_filter.get_all_entries()
    
    def get_decision_executed_events(
        self,
        from_block: int = 0,
        to_block: str = 'latest'
    ) -> List[Dict[str, Any]]:
        """
        Get DecisionExecuted events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block ('latest' for current)
            
        Returns:
            List of event dicts
        """
        event_filter = self.contract.events.DecisionExecuted.create_filter(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        return event_filter.get_all_entries()
    
    # ========== Utility Methods ==========
    
    def get_contract_balance(self) -> int:
        """Get contract's ETH balance in wei"""
        return self.web3.eth.get_balance(self.contract_address)
    
    def wait_for_transaction(
        self,
        tx_hash: str,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Wait for transaction to be mined.
        
        Args:
            tx_hash: Transaction hash
            timeout: Maximum wait time in seconds
            
        Returns:
            Transaction receipt
        """
        receipt = self.web3.eth.wait_for_transaction_receipt(
            tx_hash,
            timeout=timeout
        )
        
        return dict(receipt)
