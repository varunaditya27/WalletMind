"""
Web3 provider management and connection pooling for multiple networks

Handles Web3 connections with automatic retry, health checks, and network switching.
"""

import logging
from typing import Dict, Optional, Any
from web3 import Web3
from web3.providers import HTTPProvider
try:
    # web3.py v7+ uses ExtraDataToPOAMiddleware
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except ImportError:
    # Fallback for older web3.py versions
    from web3.middleware import geth_poa_middleware  # type: ignore
from eth_account import Account
import time
from dataclasses import dataclass

from .networks import NetworkType, NetworkConfig, get_network_config

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """Statistics for Web3 connection"""
    total_requests: int = 0
    failed_requests: int = 0
    last_successful_request: float = 0
    last_failed_request: float = 0
    is_healthy: bool = True


class Web3Provider:
    """
    Manages Web3 connections across multiple networks with health checking and retry logic.
    
    Features:
    - Connection pooling (one connection per network)
    - Automatic reconnection on failure
    - Health monitoring
    - Request statistics
    - Network switching
    """
    
    def __init__(self):
        """Initialize Web3Provider with empty connection pool"""
        self._connections: Dict[NetworkType, Web3] = {}
        self._stats: Dict[NetworkType, ConnectionStats] = {}
        self._current_network: Optional[NetworkType] = None
        logger.info("Web3Provider initialized")
    
    def connect(
        self,
        network: NetworkType,
        rpc_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ) -> Web3:
        """
        Connect to a blockchain network.
        
        Args:
            network: Network to connect to
            rpc_url: Optional custom RPC URL (overrides config)
            timeout: Request timeout in seconds
            max_retries: Maximum connection retry attempts
            
        Returns:
            Web3 instance
            
        Raises:
            ConnectionError: If unable to connect after retries
        """
        # Check if already connected
        if network in self._connections:
            web3 = self._connections[network]
            if web3.is_connected():
                logger.debug(f"Reusing existing connection to {network.value}")
                return web3
            else:
                logger.warning(f"Existing connection to {network.value} is dead, reconnecting...")
                del self._connections[network]
        
        # Get network configuration
        config = get_network_config(network, rpc_url)
        
        # Attempt connection with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to {config.name} (attempt {attempt + 1}/{max_retries})...")
                
                # Create HTTP provider with timeout
                provider = HTTPProvider(
                    config.rpc_url,
                    request_kwargs={'timeout': timeout}
                )
                
                # Create Web3 instance
                web3 = Web3(provider)
                
                # Add PoA middleware for testnets (required for some networks)
                if config.is_testnet:
                    try:
                        # web3.py v7+ syntax
                        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    except (TypeError, AttributeError):
                        # web3.py v7+ alternative syntax if inject doesn't work
                        web3.middleware_onion.add(geth_poa_middleware)
                
                # Test connection
                if not web3.is_connected():
                    raise ConnectionError(f"Failed to connect to {config.name}")
                
                # Verify chain ID
                chain_id = web3.eth.chain_id
                if chain_id != config.chain_id:
                    raise ValueError(
                        f"Chain ID mismatch: expected {config.chain_id}, got {chain_id}"
                    )
                
                # Store connection
                self._connections[network] = web3
                self._stats[network] = ConnectionStats(is_healthy=True)
                self._current_network = network
                
                logger.info(
                    f"✅ Connected to {config.name} "
                    f"(Chain ID: {chain_id}, Block: {web3.eth.block_number})"
                )
                
                return web3
                
            except Exception as e:
                last_error = e
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        # All retries failed
        error_msg = f"Failed to connect to {network.value} after {max_retries} attempts: {last_error}"
        logger.error(error_msg)
        raise ConnectionError(error_msg)
    
    def get_web3(self, network: Optional[NetworkType] = None) -> Web3:
        """
        Get Web3 instance for network.
        
        Args:
            network: Network to get connection for (defaults to current)
            
        Returns:
            Web3 instance
            
        Raises:
            ValueError: If network not connected
        """
        target_network = network or self._current_network
        
        if not target_network:
            raise ValueError("No network specified and no current network set")
        
        if target_network not in self._connections:
            raise ValueError(f"Not connected to {target_network.value}. Call connect() first.")
        
        web3 = self._connections[target_network]
        
        # Health check
        if not web3.is_connected():
            logger.warning(f"Connection to {target_network.value} lost, attempting reconnect...")
            return self.connect(target_network)
        
        return web3
    
    def switch_network(self, network: NetworkType, rpc_url: Optional[str] = None) -> Web3:
        """
        Switch to a different network.
        
        Args:
            network: Network to switch to
            rpc_url: Optional custom RPC URL
            
        Returns:
            Web3 instance for new network
        """
        logger.info(f"Switching network from {self._current_network} to {network.value}")
        
        if network in self._connections:
            self._current_network = network
            return self._connections[network]
        else:
            return self.connect(network, rpc_url)
    
    def is_connected(self, network: Optional[NetworkType] = None) -> bool:
        """
        Check if connected to network.
        
        Args:
            network: Network to check (defaults to current)
            
        Returns:
            True if connected
        """
        target_network = network or self._current_network
        
        if not target_network or target_network not in self._connections:
            return False
        
        return self._connections[target_network].is_connected()
    
    def get_current_network(self) -> Optional[NetworkType]:
        """Get currently active network"""
        return self._current_network
    
    def get_block_number(self, network: Optional[NetworkType] = None) -> int:
        """
        Get current block number.
        
        Args:
            network: Network to query (defaults to current)
            
        Returns:
            Latest block number
        """
        web3 = self.get_web3(network)
        return web3.eth.block_number
    
    def get_balance(
        self,
        address: str,
        network: Optional[NetworkType] = None,
        block: str = "latest"
    ) -> int:
        """
        Get account balance in wei.
        
        Args:
            address: Account address
            network: Network to query (defaults to current)
            block: Block number or 'latest'
            
        Returns:
            Balance in wei
        """
        web3 = self.get_web3(network)
        checksum_address = web3.to_checksum_address(address)
        return web3.eth.get_balance(checksum_address, block)
    
    def get_gas_price(self, network: Optional[NetworkType] = None) -> int:
        """
        Get current gas price.
        
        Args:
            network: Network to query (defaults to current)
            
        Returns:
            Gas price in wei
        """
        web3 = self.get_web3(network)
        return web3.eth.gas_price
    
    def estimate_gas(
        self,
        transaction: Dict[str, Any],
        network: Optional[NetworkType] = None
    ) -> int:
        """
        Estimate gas for transaction.
        
        Args:
            transaction: Transaction dict
            network: Network to use (defaults to current)
            
        Returns:
            Estimated gas units
        """
        web3 = self.get_web3(network)
        return web3.eth.estimate_gas(transaction)
    
    def wait_for_transaction(
        self,
        tx_hash: str,
        network: Optional[NetworkType] = None,
        timeout: int = 120,
        poll_latency: float = 0.1
    ) -> Dict[str, Any]:
        """
        Wait for transaction to be mined.
        
        Args:
            tx_hash: Transaction hash
            network: Network to use (defaults to current)
            timeout: Maximum wait time in seconds
            poll_latency: Polling interval in seconds
            
        Returns:
            Transaction receipt
            
        Raises:
            TimeoutError: If transaction not mined within timeout
        """
        web3 = self.get_web3(network)
        
        try:
            receipt = web3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=timeout,
                poll_latency=poll_latency
            )
            
            # Update stats
            target_network = network or self._current_network
            if target_network and target_network in self._stats:
                self._stats[target_network].total_requests += 1
                self._stats[target_network].last_successful_request = time.time()
            
            return receipt
            
        except Exception as e:
            # Update stats
            target_network = network or self._current_network
            if target_network and target_network in self._stats:
                self._stats[target_network].failed_requests += 1
                self._stats[target_network].last_failed_request = time.time()
            
            raise
    
    def get_stats(self, network: Optional[NetworkType] = None) -> Optional[ConnectionStats]:
        """
        Get connection statistics.
        
        Args:
            network: Network to get stats for (defaults to current)
            
        Returns:
            ConnectionStats or None if not connected
        """
        target_network = network or self._current_network
        
        if not target_network:
            return None
        
        return self._stats.get(target_network)
    
    def disconnect(self, network: Optional[NetworkType] = None):
        """
        Disconnect from network.
        
        Args:
            network: Network to disconnect from (defaults to all if None)
        """
        if network:
            if network in self._connections:
                del self._connections[network]
                del self._stats[network]
                logger.info(f"Disconnected from {network.value}")
                
                if self._current_network == network:
                    self._current_network = None
        else:
            # Disconnect all
            self._connections.clear()
            self._stats.clear()
            self._current_network = None
            logger.info("Disconnected from all networks")
    
    def disconnect_all(self):
        """Disconnect from all networks"""
        self.disconnect()


# Singleton instance
_provider: Optional[Web3Provider] = None


def get_web3_provider() -> Web3Provider:
    """
    Get or create singleton Web3Provider instance.
    
    Returns:
        Web3Provider instance
    """
    global _provider
    
    if _provider is None:
        _provider = Web3Provider()
    
    return _provider
