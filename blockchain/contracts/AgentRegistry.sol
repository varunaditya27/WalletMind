// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title AgentRegistry
 * @notice Registry for AI agent discovery, reputation tracking, and inter-agent communication
 * @dev Implements FR-012 from PRD
 * 
 * Key Features:
 * - Agent registration and discovery (FR-012)
 * - Reputation scoring based on transaction success
 * - Service metadata for agent-to-agent negotiation
 * - Agent status tracking (active/inactive)
 */
contract AgentRegistry {
    /// @notice Structure to store agent information
    struct Agent {
        address wallet;             // Agent's wallet address
        string metadata;            // JSON metadata (services, capabilities, etc.)
        uint256 reputation;         // Reputation score (0-1000)
        uint256 transactionCount;   // Total transactions executed
        uint256 successfulTxCount;  // Successful transactions
        uint256 registeredAt;       // Registration timestamp
        bool active;                // Whether agent is currently active
        string[] services;          // List of services offered
    }

    /// @notice Structure for service offerings
    struct ServiceOffering {
        string serviceId;           // Unique service identifier
        address provider;           // Agent providing the service
        uint256 price;              // Price in wei
        string description;         // Service description
        bool available;             // Service availability
    }

    // State variables
    address public admin;
    uint256 public agentCount;
    uint256 public serviceCount;
    
    /// @notice Mapping of agent addresses to agent data
    mapping(address => Agent) public agents;
    
    /// @notice Array of all registered agent addresses (for discovery)
    address[] public agentList;
    
    /// @notice Mapping of service IDs to service offerings
    mapping(bytes32 => ServiceOffering) public services;
    
    /// @notice Mapping of provider address to their service IDs
    mapping(address => bytes32[]) public providerServices;

    // Events
    event AgentRegistered(
        address indexed agentAddress,
        string metadata,
        uint256 timestamp
    );
    
    event AgentUpdated(
        address indexed agentAddress,
        string metadata
    );
    
    event ReputationUpdated(
        address indexed agentAddress,
        uint256 oldReputation,
        uint256 newReputation
    );
    
    event TransactionRecorded(
        address indexed agentAddress,
        bool success,
        uint256 newTxCount
    );
    
    event ServiceRegistered(
        bytes32 indexed serviceId,
        address indexed provider,
        uint256 price
    );
    
    event ServiceUpdated(
        bytes32 indexed serviceId,
        bool available
    );
    
    event AgentStatusChanged(
        address indexed agentAddress,
        bool active
    );

    modifier onlyAdmin() {
        require(msg.sender == admin, "AgentRegistry: caller is not admin");
        _;
    }
    
    modifier onlyRegistered() {
        require(agents[msg.sender].wallet != address(0), "AgentRegistry: agent not registered");
        _;
    }

    constructor() {
        admin = msg.sender;
        agentCount = 0;
        serviceCount = 0;
    }

    /**
     * @notice Register a new AI agent (FR-012)
     * @param metadata JSON string containing agent capabilities and info
     */
    function registerAgent(string memory metadata) external {
        require(agents[msg.sender].wallet == address(0), "AgentRegistry: already registered");
        require(bytes(metadata).length > 0, "AgentRegistry: metadata required");
        
        agents[msg.sender] = Agent({
            wallet: msg.sender,
            metadata: metadata,
            reputation: 500, // Start with neutral reputation (0-1000 scale)
            transactionCount: 0,
            successfulTxCount: 0,
            registeredAt: block.timestamp,
            active: true,
            services: new string[](0)
        });
        
        agentList.push(msg.sender);
        agentCount++;
        
        emit AgentRegistered(msg.sender, metadata, block.timestamp);
    }

    /**
     * @notice Update agent metadata
     * @param metadata New metadata JSON string
     */
    function updateMetadata(string memory metadata) external onlyRegistered {
        require(bytes(metadata).length > 0, "AgentRegistry: metadata required");
        agents[msg.sender].metadata = metadata;
        emit AgentUpdated(msg.sender, metadata);
    }

    /**
     * @notice Update agent reputation based on transaction outcome
     * @param agentAddress Agent whose reputation to update
     * @param success Whether the transaction was successful
     */
    function updateReputation(address agentAddress, bool success) external {
        Agent storage agent = agents[agentAddress];
        require(agent.wallet != address(0), "AgentRegistry: agent not found");
        
        uint256 oldReputation = agent.reputation;
        agent.transactionCount++;
        
        if (success) {
            agent.successfulTxCount++;
            // Increase reputation (max 1000)
            if (agent.reputation < 1000) {
                agent.reputation = agent.reputation + 10 > 1000 ? 1000 : agent.reputation + 10;
            }
        } else {
            // Decrease reputation (min 0)
            agent.reputation = agent.reputation < 20 ? 0 : agent.reputation - 20;
        }
        
        emit ReputationUpdated(agentAddress, oldReputation, agent.reputation);
        emit TransactionRecorded(agentAddress, success, agent.transactionCount);
    }

    /**
     * @notice Register a service offering
     * @param serviceId Unique service identifier
     * @param price Price in wei
     * @param description Service description
     */
    function registerService(
        string memory serviceId,
        uint256 price,
        string memory description
    ) external onlyRegistered {
        bytes32 serviceHash = keccak256(abi.encodePacked(msg.sender, serviceId));
        require(services[serviceHash].provider == address(0), "AgentRegistry: service exists");
        
        services[serviceHash] = ServiceOffering({
            serviceId: serviceId,
            provider: msg.sender,
            price: price,
            description: description,
            available: true
        });
        
        providerServices[msg.sender].push(serviceHash);
        agents[msg.sender].services.push(serviceId);
        serviceCount++;
        
        emit ServiceRegistered(serviceHash, msg.sender, price);
    }

    /**
     * @notice Update service availability
     * @param serviceId Service identifier
     * @param available New availability status
     */
    function updateServiceAvailability(string memory serviceId, bool available) external onlyRegistered {
        bytes32 serviceHash = keccak256(abi.encodePacked(msg.sender, serviceId));
        require(services[serviceHash].provider == msg.sender, "AgentRegistry: not service owner");
        
        services[serviceHash].available = available;
        emit ServiceUpdated(serviceHash, available);
    }

    /**
     * @notice Set agent active status
     * @param active New active status
     */
    function setActiveStatus(bool active) external onlyRegistered {
        agents[msg.sender].active = active;
        emit AgentStatusChanged(msg.sender, active);
    }

    /**
     * @notice Get agent information
     * @param agentAddress Agent address to query
     */
    function getAgent(address agentAddress) external view returns (Agent memory) {
        require(agents[agentAddress].wallet != address(0), "AgentRegistry: agent not found");
        return agents[agentAddress];
    }

    /**
     * @notice Get all registered agents (for discovery)
     */
    function getAllAgents() external view returns (address[] memory) {
        return agentList;
    }

    /**
     * @notice Get active agents only
     */
    function getActiveAgents() external view returns (address[] memory) {
        uint256 activeCount = 0;
        
        // Count active agents
        for (uint256 i = 0; i < agentList.length; i++) {
            if (agents[agentList[i]].active) {
                activeCount++;
            }
        }
        
        // Create array of active agents
        address[] memory activeAgents = new address[](activeCount);
        uint256 index = 0;
        
        for (uint256 i = 0; i < agentList.length; i++) {
            if (agents[agentList[i]].active) {
                activeAgents[index] = agentList[i];
                index++;
            }
        }
        
        return activeAgents;
    }

    /**
     * @notice Get agent's services
     * @param provider Agent address
     */
    function getAgentServices(address provider) external view returns (bytes32[] memory) {
        return providerServices[provider];
    }

    /**
     * @notice Get service details
     * @param provider Service provider address
     * @param serviceId Service identifier
     */
    function getService(address provider, string memory serviceId) 
        external 
        view 
        returns (ServiceOffering memory) 
    {
        bytes32 serviceHash = keccak256(abi.encodePacked(provider, serviceId));
        return services[serviceHash];
    }

    /**
     * @notice Get agent reputation score
     * @param agentAddress Agent to query
     */
    function getReputation(address agentAddress) external view returns (uint256) {
        return agents[agentAddress].reputation;
    }

    /**
     * @notice Get agent success rate (percentage)
     * @param agentAddress Agent to query
     */
    function getSuccessRate(address agentAddress) external view returns (uint256) {
        Agent memory agent = agents[agentAddress];
        if (agent.transactionCount == 0) return 0;
        return (agent.successfulTxCount * 100) / agent.transactionCount;
    }

    /**
     * @notice Transfer admin role
     * @param newAdmin New admin address
     */
    function transferAdmin(address newAdmin) external onlyAdmin {
        require(newAdmin != address(0), "AgentRegistry: invalid admin address");
        admin = newAdmin;
    }
}
