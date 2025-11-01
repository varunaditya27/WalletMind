"""
Multi-network configuration for Ethereum Sepolia, Polygon Amoy, Base Goerli testnets (FR-006)

Provides NetworkConfig dataclass and pre-configured network settings.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


class NetworkType(str, Enum):
    """Supported blockchain networks"""
    SEPOLIA = "sepolia"
    POLYGON_AMOY = "polygon_amoy"
    BASE_GOERLI = "base_goerli"


@dataclass
class NetworkConfig:
    """
    Configuration for a blockchain network.
    
    Attributes:
        name: Human-readable network name
        chain_id: EIP-155 chain ID
        rpc_url: HTTP RPC endpoint URL
        explorer_url: Block explorer base URL
        currency: Native currency symbol
        is_testnet: Whether this is a testnet
        gas_price_multiplier: Multiplier for gas price (for faster inclusion)
        max_gas_price_gwei: Maximum gas price in Gwei
        confirmation_blocks: Number of blocks for confirmation
        block_time_seconds: Average block time
    """
    name: str
    chain_id: int
    rpc_url: str
    explorer_url: str
    currency: str
    is_testnet: bool = True
    gas_price_multiplier: float = 1.1
    max_gas_price_gwei: int = 50
    confirmation_blocks: int = 3
    block_time_seconds: int = 12


# Ethereum Sepolia Testnet
SEPOLIA_CONFIG = NetworkConfig(
    name="Sepolia Testnet",
    chain_id=11155111,
    # RPC URL will be loaded from config at runtime
    rpc_url="https://rpc.sepolia.org",  # Fallback default
    explorer_url="https://sepolia.etherscan.io",
    currency="ETH",
    is_testnet=True,
    gas_price_multiplier=1.1,
    max_gas_price_gwei=50,
    confirmation_blocks=3,
    block_time_seconds=12
)

# Polygon Amoy Testnet
POLYGON_AMOY_CONFIG = NetworkConfig(
    name="Polygon Amoy Testnet",
    chain_id=80002,
    rpc_url="https://rpc-amoy.polygon.technology",  # Fallback default
    explorer_url="https://amoy.polygonscan.com",
    currency="MATIC",
    is_testnet=True,
    gas_price_multiplier=1.2,
    max_gas_price_gwei=200,
    confirmation_blocks=5,
    block_time_seconds=2
)

# Base Goerli Testnet
BASE_GOERLI_CONFIG = NetworkConfig(
    name="Base Goerli Testnet",
    chain_id=84531,
    rpc_url="https://goerli.base.org",  # Fallback default
    explorer_url="https://goerli.basescan.org",
    currency="ETH",
    is_testnet=True,
    gas_price_multiplier=1.1,
    max_gas_price_gwei=30,
    confirmation_blocks=3,
    block_time_seconds=2
)

# Network registry
NETWORKS: Dict[NetworkType, NetworkConfig] = {
    NetworkType.SEPOLIA: SEPOLIA_CONFIG,
    NetworkType.POLYGON_AMOY: POLYGON_AMOY_CONFIG,
    NetworkType.BASE_GOERLI: BASE_GOERLI_CONFIG,
}


def get_network_config(network: NetworkType, rpc_url: Optional[str] = None) -> NetworkConfig:
    """
    Get network configuration by type.
    
    Args:
        network: Network type enum
        rpc_url: Optional custom RPC URL to override default
        
    Returns:
        NetworkConfig instance
        
    Raises:
        ValueError: If network type is not supported
    """
    if network not in NETWORKS:
        raise ValueError(f"Unsupported network: {network}")
    
    config = NETWORKS[network]
    
    # Override RPC URL if provided
    if rpc_url:
        config = NetworkConfig(
            name=config.name,
            chain_id=config.chain_id,
            rpc_url=rpc_url,
            explorer_url=config.explorer_url,
            currency=config.currency,
            is_testnet=config.is_testnet,
            gas_price_multiplier=config.gas_price_multiplier,
            max_gas_price_gwei=config.max_gas_price_gwei,
            confirmation_blocks=config.confirmation_blocks,
            block_time_seconds=config.block_time_seconds
        )
    
    return config


def get_network_by_chain_id(chain_id: int) -> Optional[NetworkType]:
    """
    Get network type by chain ID.
    
    Args:
        chain_id: EIP-155 chain ID
        
    Returns:
        NetworkType if found, None otherwise
    """
    for network_type, config in NETWORKS.items():
        if config.chain_id == chain_id:
            return network_type
    return None


def get_explorer_url(network: NetworkType, tx_hash: Optional[str] = None, address: Optional[str] = None) -> str:
    """
    Get block explorer URL for transaction or address.
    
    Args:
        network: Network type
        tx_hash: Transaction hash (optional)
        address: Address to view (optional)
        
    Returns:
        Full explorer URL
    """
    config = get_network_config(network)
    base_url = config.explorer_url
    
    if tx_hash:
        return f"{base_url}/tx/{tx_hash}"
    elif address:
        return f"{base_url}/address/{address}"
    else:
        return base_url


def is_testnet(network: NetworkType) -> bool:
    """Check if network is a testnet"""
    return get_network_config(network).is_testnet


def get_all_networks() -> Dict[NetworkType, NetworkConfig]:
    """Get all available network configurations"""
    return NETWORKS.copy()
