"""
Python wrapper for AgentRegistry.sol smart contract (FR-012)

Provides high-level interface for agent registration, reputation, and discovery.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from web3 import Web3
from web3.contract import Contract
from eth_account.signers.local import LocalAccount

logger = logging.getLogger(__name__)


@dataclass
class Agent:
    """Agent information from contract"""
    wallet: str
    metadata: str
    reputation: int
    transaction_count: int
    successful_tx_count: int
    registered_at: int
    active: bool
    services: List[str]


@dataclass
class ServiceOffering:
    """Service offering from contract"""
    service_id: str
    provider: str
    price: int
    description: str
    available: bool


class AgentRegistryContract:
    """
    Python wrapper for AgentRegistry smart contract.
    
    Features:
    - Agent registration and discovery (FR-012)
    - Reputation tracking and updates
    - Service offering management
    - Agent status management
    """
    
    def __init__(
        self,
        web3: Web3,
        contract_address: str,
        abi_path: Optional[Path] = None
    ):
        """
        Initialize AgentRegistry contract wrapper.
        
        Args:
            web3: Web3 instance connected to network
            contract_address: Deployed contract address
            abi_path: Path to ABI JSON file (defaults to packaged ABI)
        """
        self.web3 = web3
        self.contract_address = web3.to_checksum_address(contract_address)
        
        # Load ABI
        if abi_path is None:
            abi_path = Path(__file__).parent / "abis" / "AgentRegistry.json"
        
        with open(abi_path, 'r') as f:
            artifact = json.load(f)
            self.abi = artifact['abi']
        
        # Create contract instance
        self.contract: Contract = web3.eth.contract(
            address=self.contract_address,
            abi=self.abi
        )
        
        logger.info(f"AgentRegistry contract initialized at {self.contract_address}")
    
    # ========== Read Methods ==========
    
    def get_admin(self) -> str:
        """Get contract admin address"""
        return self.contract.functions.admin().call()
    
    def get_agent_count(self) -> int:
        """Get total number of registered agents"""
        return self.contract.functions.agentCount().call()
    
    def get_service_count(self) -> int:
        """Get total number of registered services"""
        return self.contract.functions.serviceCount().call()
    
    def get_agent(self, agent_address: str) -> Agent:
        """
        Get agent information.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Agent object
        """
        checksum_address = self.web3.to_checksum_address(agent_address)
        result = self.contract.functions.agents(checksum_address).call()
        
        return Agent(
            wallet=result[0],
            metadata=result[1],
            reputation=result[2],
            transaction_count=result[3],
            successful_tx_count=result[4],
            registered_at=result[5],
            active=result[6],
            services=list(result[7])
        )
    
    def is_agent_registered(self, agent_address: str) -> bool:
        """
        Check if agent is registered.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            True if registered
        """
        checksum_address = self.web3.to_checksum_address(agent_address)
        agent = self.contract.functions.agents(checksum_address).call()
        return agent[0] != '0x0000000000000000000000000000000000000000'
    
    def get_all_agents(self) -> List[str]:
        """
        Get all registered agent addresses.
        
        Returns:
            List of agent addresses
        """
        return self.contract.functions.getAllAgents().call()
    
    def get_active_agents(self) -> List[str]:
        """
        Get all active agent addresses.
        
        Returns:
            List of active agent addresses
        """
        return self.contract.functions.getActiveAgents().call()
    
    def get_agent_info(self, agent_address: str) -> Dict[str, Any]:
        """
        Get full agent information including success rate.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Dict with agent details and success rate
        """
        checksum_address = self.web3.to_checksum_address(agent_address)
        result = self.contract.functions.getAgentInfo(checksum_address).call()
        
        return {
            'address': result[0],
            'metadata': result[1],
            'reputation': result[2],
            'transaction_count': result[3],
            'success_rate': result[4],  # In basis points (0-10000)
            'active': result[5]
        }
    
    def get_service(self, service_id: str) -> ServiceOffering:
        """
        Get service offering details.
        
        Args:
            service_id: Service identifier
            
        Returns:
            ServiceOffering object
        """
        service_hash = self.web3.keccak(text=service_id)
        result = self.contract.functions.services(service_hash).call()
        
        return ServiceOffering(
            service_id=result[0],
            provider=result[1],
            price=result[2],
            description=result[3],
            available=result[4]
        )
    
    def get_provider_services(self, provider_address: str) -> List[bytes]:
        """
        Get all service IDs offered by provider.
        
        Args:
            provider_address: Provider's wallet address
            
        Returns:
            List of service ID hashes
        """
        checksum_address = self.web3.to_checksum_address(provider_address)
        return self.contract.functions.getProviderServices(checksum_address).call()
    
    # ========== Write Methods ==========
    
    def register_agent(
        self,
        metadata: str,
        account: LocalAccount,
        gas_limit: Optional[int] = None
    ) -> str:
        """
        Register new agent (FR-012).
        
        Args:
            metadata: JSON metadata string (services, capabilities, etc.)
            account: Account to register as agent
            gas_limit: Optional gas limit override
            
        Returns:
            Transaction hash
        """
        # Build transaction
        tx = self.contract.functions.registerAgent(metadata).build_transaction({
            'from': account.address,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': gas_limit or 200000,
            'gasPrice': self.web3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Agent registered: {account.address}, tx: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    def update_agent_metadata(
        self,
        metadata: str,
        account: LocalAccount,
        gas_limit: Optional[int] = None
    ) -> str:
        """
        Update agent metadata.
        
        Args:
            metadata: New metadata string
            account: Registered agent account
            gas_limit: Optional gas limit override
            
        Returns:
            Transaction hash
        """
        # Build transaction
        tx = self.contract.functions.updateAgentMetadata(metadata).build_transaction({
            'from': account.address,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': gas_limit or 150000,
            'gasPrice': self.web3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Agent metadata updated: {account.address}, tx: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    def update_reputation(
        self,
        agent_address: str,
        success: bool,
        account: LocalAccount,
        gas_limit: Optional[int] = None
    ) -> str:
        """
        Update agent reputation based on transaction outcome.
        
        Args:
            agent_address: Agent to update
            success: Whether transaction was successful
            account: Account with update permission
            gas_limit: Optional gas limit override
            
        Returns:
            Transaction hash
        """
        checksum_agent = self.web3.to_checksum_address(agent_address)
        
        # Build transaction
        tx = self.contract.functions.updateReputation(
            checksum_agent,
            success
        ).build_transaction({
            'from': account.address,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': gas_limit or 100000,
            'gasPrice': self.web3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Reputation updated for {agent_address}: success={success}, tx: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    def register_service(
        self,
        service_id: str,
        price: int,
        description: str,
        account: LocalAccount,
        gas_limit: Optional[int] = None
    ) -> str:
        """
        Register service offering.
        
        Args:
            service_id: Unique service identifier
            price: Service price in wei
            description: Service description
            account: Registered agent account
            gas_limit: Optional gas limit override
            
        Returns:
            Transaction hash
        """
        # Build transaction
        tx = self.contract.functions.registerService(
            service_id,
            price,
            description
        ).build_transaction({
            'from': account.address,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': gas_limit or 200000,
            'gasPrice': self.web3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Service registered: {service_id} by {account.address}, tx: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    def update_service_availability(
        self,
        service_id: str,
        available: bool,
        account: LocalAccount,
        gas_limit: Optional[int] = None
    ) -> str:
        """
        Update service availability status.
        
        Args:
            service_id: Service identifier
            available: Availability status
            account: Service provider account
            gas_limit: Optional gas limit override
            
        Returns:
            Transaction hash
        """
        # Build transaction
        tx = self.contract.functions.updateServiceAvailability(
            service_id,
            available
        ).build_transaction({
            'from': account.address,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': gas_limit or 80000,
            'gasPrice': self.web3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Service availability updated: {service_id} = {available}, tx: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    def set_agent_status(
        self,
        active: bool,
        account: LocalAccount,
        gas_limit: Optional[int] = None
    ) -> str:
        """
        Set agent active/inactive status.
        
        Args:
            active: Active status
            account: Registered agent account
            gas_limit: Optional gas limit override
            
        Returns:
            Transaction hash
        """
        # Build transaction
        tx = self.contract.functions.setAgentStatus(active).build_transaction({
            'from': account.address,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': gas_limit or 50000,
            'gasPrice': self.web3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Agent status updated: {account.address} active={active}, tx: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    # ========== Event Filtering ==========
    
    def get_agent_registered_events(
        self,
        from_block: int = 0,
        to_block: str = 'latest'
    ) -> List[Dict[str, Any]]:
        """Get AgentRegistered events"""
        event_filter = self.contract.events.AgentRegistered.create_filter(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        return event_filter.get_all_entries()
    
    def get_reputation_updated_events(
        self,
        from_block: int = 0,
        to_block: str = 'latest',
        agent_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get ReputationUpdated events, optionally filtered by agent"""
        if agent_address:
            checksum_address = self.web3.to_checksum_address(agent_address)
            event_filter = self.contract.events.ReputationUpdated.create_filter(
                fromBlock=from_block,
                toBlock=to_block,
                argument_filters={'agentAddress': checksum_address}
            )
        else:
            event_filter = self.contract.events.ReputationUpdated.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
        
        return event_filter.get_all_entries()
    
    def get_service_registered_events(
        self,
        from_block: int = 0,
        to_block: str = 'latest'
    ) -> List[Dict[str, Any]]:
        """Get ServiceRegistered events"""
        event_filter = self.contract.events.ServiceRegistered.create_filter(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        return event_filter.get_all_entries()
    
    # ========== Utility Methods ==========
    
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
    
    def calculate_success_rate(self, agent_address: str) -> float:
        """
        Calculate agent success rate as percentage.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Success rate (0.0 to 100.0)
        """
        agent = self.get_agent(agent_address)
        
        if agent.transaction_count == 0:
            return 0.0
        
        return (agent.successful_tx_count / agent.transaction_count) * 100.0
