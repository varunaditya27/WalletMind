"""
Blockchain layer - Python wrapper for smart contracts

Provides high-level interface for:
- Multi-network Web3 connectivity (Sepolia, Polygon Amoy, Base Goerli)
- AgentWallet and AgentRegistry contract interaction
- Secure wallet management with KeyManager integration
- Transaction building and execution with EIP-1559 support
"""

from .networks import NetworkType, NetworkConfig, get_network_config
from .provider import Web3Provider, ConnectionStats
from .wallet import WalletManager
from .transaction import (
    TransactionBuilder,
    TransactionExecutor,
    TransactionConfig,
    TransactionReceipt
)
from .contracts.agent_wallet import AgentWalletContract, Decision, TransactionRecord
from .contracts.agent_registry import AgentRegistryContract, Agent, ServiceOffering

__all__ = [
    # Networks
    'NetworkType',
    'NetworkConfig',
    'get_network_config',
    
    # Provider
    'Web3Provider',
    'ConnectionStats',
    
    # Wallet
    'WalletManager',
    
    # Transactions
    'TransactionBuilder',
    'TransactionExecutor',
    'TransactionConfig',
    'TransactionReceipt',
    
    # AgentWallet Contract
    'AgentWalletContract',
    'Decision',
    'TransactionRecord',
    
    # AgentRegistry Contract
    'AgentRegistryContract',
    'Agent',
    'ServiceOffering',
]

__version__ = '1.0.0'

