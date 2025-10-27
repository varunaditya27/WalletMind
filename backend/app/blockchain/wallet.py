"""
Wallet management with security.KeyManager integration

Provides high-level wallet operations with secure key storage.
"""

import logging
from typing import Dict, Optional
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3

from ..security.key_manager import KeyManager, KeyDerivationPath
from .provider import Web3Provider
from .networks import NetworkType

logger = logging.getLogger(__name__)


class WalletManager:
    """
    Wallet management with secure key storage.
    
    Features:
    - BIP39 mnemonic generation (via KeyManager)
    - BIP44 key derivation (via KeyManager)
    - AES-256-GCM encrypted key storage
    - Multi-network support
    - Nonce tracking per network
    - Balance queries
    """
    
    def __init__(
        self,
        account: LocalAccount,
        key_manager: Optional[KeyManager] = None,
        web3_provider: Optional[Web3Provider] = None
    ):
        """
        Initialize wallet manager.
        
        Args:
            account: Ethereum account
            key_manager: Optional KeyManager for secure storage
            web3_provider: Optional Web3Provider for multi-network
        """
        self.account = account
        self.key_manager = key_manager
        self.web3_provider = web3_provider or Web3Provider.get_instance()
        
        # Nonce tracking per network
        self._nonce_cache: Dict[NetworkType, int] = {}
        
        logger.info(f"WalletManager initialized for {self.account.address}")
    
    # ========== Static Factory Methods ==========
    
    @staticmethod
    def create_wallet(
        master_password: str,
        wallet_id: str,
        mnemonic: Optional[str] = None,
        passphrase: str = "",
        account_index: int = 0
    ) -> 'WalletManager':
        """
        Create new wallet with secure key storage.
        
        Args:
            master_password: Master password for encryption
            wallet_id: Unique wallet identifier
            mnemonic: Optional existing mnemonic (generates new if None)
            passphrase: Optional BIP39 passphrase
            account_index: BIP44 account index
            
        Returns:
            WalletManager instance
        """
        # Initialize KeyManager
        key_manager = KeyManager(master_password)
        
        # Generate or use mnemonic
        if mnemonic is None:
            mnemonic = key_manager.generate_mnemonic()
            logger.info("Generated new mnemonic")
        else:
            logger.info("Using provided mnemonic")
        
        # Store mnemonic securely
        key_manager.store_mnemonic(wallet_id, mnemonic)
        
        # Derive Ethereum key (m/44'/60'/0'/0/{account_index})
        derivation_path = KeyDerivationPath.ethereum(account_index=account_index)
        private_key = key_manager.derive_key_from_mnemonic(
            mnemonic,
            derivation_path,
            passphrase
        )
        
        # Create Ethereum account
        account = Account.from_key(private_key)
        
        # Store encrypted private key
        key_manager.store_key(
            f"{wallet_id}_private_key",
            private_key.hex()
        )
        
        logger.info(f"Created wallet: {account.address}")
        
        return WalletManager(account, key_manager)
    
    @staticmethod
    def load_wallet(
        master_password: str,
        wallet_id: str,
        account_index: int = 0,
        passphrase: str = ""
    ) -> 'WalletManager':
        """
        Load existing wallet from secure storage.
        
        Args:
            master_password: Master password for decryption
            wallet_id: Wallet identifier
            account_index: BIP44 account index
            passphrase: Optional BIP39 passphrase
            
        Returns:
            WalletManager instance
        """
        # Initialize KeyManager
        key_manager = KeyManager(master_password)
        
        # Try loading private key first (faster)
        try:
            private_key_hex = key_manager.retrieve_key(f"{wallet_id}_private_key")
            account = Account.from_key(private_key_hex)
            
            logger.info(f"Loaded wallet from stored key: {account.address}")
            
            return WalletManager(account, key_manager)
        
        except Exception as e:
            logger.warning(f"Failed to load from stored key: {e}, trying mnemonic")
        
        # Fallback to mnemonic derivation
        mnemonic = key_manager.retrieve_mnemonic(wallet_id)
        
        # Derive key
        derivation_path = KeyDerivationPath.ethereum(account_index=account_index)
        private_key = key_manager.derive_key_from_mnemonic(
            mnemonic,
            derivation_path,
            passphrase
        )
        
        # Create account
        account = Account.from_key(private_key)
        
        # Store private key for faster loading next time
        key_manager.store_key(
            f"{wallet_id}_private_key",
            private_key.hex()
        )
        
        logger.info(f"Loaded wallet from mnemonic: {account.address}")
        
        return WalletManager(account, key_manager)
    
    @staticmethod
    def from_private_key(
        private_key: str,
        key_manager: Optional[KeyManager] = None
    ) -> 'WalletManager':
        """
        Create wallet from raw private key.
        
        Args:
            private_key: Hex-encoded private key
            key_manager: Optional KeyManager
            
        Returns:
            WalletManager instance
        """
        account = Account.from_key(private_key)
        
        logger.info(f"Created wallet from private key: {account.address}")
        
        return WalletManager(account, key_manager)
    
    # ========== Instance Methods ==========
    
    def get_address(self) -> str:
        """Get wallet address"""
        return self.account.address
    
    def get_balance(
        self,
        network: Optional[NetworkType] = None
    ) -> int:
        """
        Get wallet balance in wei.
        
        Args:
            network: Network to query (uses current if None)
            
        Returns:
            Balance in wei
        """
        if network:
            self.web3_provider.switch_network(network)
        
        web3 = self.web3_provider.get_web3()
        balance = web3.eth.get_balance(self.account.address)
        
        logger.debug(f"Balance: {balance} wei on {self.web3_provider.current_network}")
        
        return balance
    
    def get_balance_ether(
        self,
        network: Optional[NetworkType] = None
    ) -> float:
        """
        Get wallet balance in ether.
        
        Args:
            network: Network to query (uses current if None)
            
        Returns:
            Balance in ether
        """
        balance_wei = self.get_balance(network)
        web3 = self.web3_provider.get_web3()
        
        return float(web3.from_wei(balance_wei, 'ether'))
    
    def get_nonce(
        self,
        network: Optional[NetworkType] = None,
        use_cache: bool = True
    ) -> int:
        """
        Get current nonce for transactions.
        
        Args:
            network: Network to query (uses current if None)
            use_cache: Use cached nonce if available
            
        Returns:
            Transaction nonce
        """
        if network:
            self.web3_provider.switch_network(network)
        
        current_network = self.web3_provider.current_network
        
        # Check cache
        if use_cache and current_network in self._nonce_cache:
            cached_nonce = self._nonce_cache[current_network]
            logger.debug(f"Using cached nonce: {cached_nonce}")
            return cached_nonce
        
        # Query network
        web3 = self.web3_provider.get_web3()
        nonce = web3.eth.get_transaction_count(self.account.address)
        
        # Update cache
        self._nonce_cache[current_network] = nonce
        
        logger.debug(f"Nonce: {nonce} on {current_network}")
        
        return nonce
    
    def increment_nonce(self, network: Optional[NetworkType] = None) -> None:
        """
        Increment cached nonce (call after sending transaction).
        
        Args:
            network: Network to update (uses current if None)
        """
        if network:
            current_network = network
        else:
            current_network = self.web3_provider.current_network
        
        if current_network in self._nonce_cache:
            self._nonce_cache[current_network] += 1
            logger.debug(f"Incremented nonce to {self._nonce_cache[current_network]}")
    
    def reset_nonce(self, network: Optional[NetworkType] = None) -> None:
        """
        Reset nonce cache (call if transaction failed).
        
        Args:
            network: Network to reset (uses current if None)
        """
        if network:
            current_network = network
        else:
            current_network = self.web3_provider.current_network
        
        if current_network in self._nonce_cache:
            del self._nonce_cache[current_network]
            logger.debug(f"Reset nonce cache for {current_network}")
    
    def sign_transaction(self, transaction: Dict) -> str:
        """
        Sign transaction.
        
        Args:
            transaction: Transaction dict
            
        Returns:
            Signed raw transaction hex
        """
        signed_tx = self.account.sign_transaction(transaction)
        
        logger.debug(f"Signed transaction: {signed_tx.hash.hex()}")
        
        return signed_tx.raw_transaction.hex()
    
    def sign_message(self, message: str) -> str:
        """
        Sign arbitrary message.
        
        Args:
            message: Message to sign
            
        Returns:
            Signature hex
        """
        from eth_account.messages import encode_defunct
        
        message_hash = encode_defunct(text=message)
        signed_message = self.account.sign_message(message_hash)
        
        logger.debug(f"Signed message: {message}")
        
        return signed_message.signature.hex()
    
    # ========== KeyManager Integration ==========
    
    def store_in_key_manager(
        self,
        wallet_id: str,
        master_password: Optional[str] = None
    ) -> None:
        """
        Store wallet in KeyManager.
        
        Args:
            wallet_id: Wallet identifier
            master_password: Master password (required if no KeyManager)
        """
        if self.key_manager is None:
            if master_password is None:
                raise ValueError("master_password required when no KeyManager")
            
            self.key_manager = KeyManager(master_password)
        
        # Store private key
        self.key_manager.store_key(
            f"{wallet_id}_private_key",
            self.account.key.hex()
        )
        
        logger.info(f"Stored wallet {wallet_id} in KeyManager")
    
    @classmethod
    def load_from_key_manager(
        cls,
        wallet_id: str,
        master_password: str
    ) -> 'WalletManager':
        """
        Load wallet from KeyManager.
        
        Args:
            wallet_id: Wallet identifier
            master_password: Master password
            
        Returns:
            WalletManager instance
        """
        return cls.load_wallet(master_password, wallet_id)
    
    # ========== Utility Methods ==========
    
    def __repr__(self) -> str:
        return f"WalletManager(address={self.account.address})"

