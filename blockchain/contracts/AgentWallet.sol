// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title AgentWallet
 * @notice Main smart contract wallet for AI agents with decision logging and verification
 * @dev Implements FR-004, FR-007, FR-008, NFR-005 from PRD
 * 
 * Key Features:
 * - Decision provenance logging before execution (FR-007)
 * - On-chain audit trail of all agent actions (FR-008)
 * - Spending limits enforced at contract level (NFR-005)
 * - Emergency pause functionality for security
 * - Cryptographic verification of autonomous decisions
 */
contract AgentWallet {
    /// @notice Structure to store decision provenance data (FR-007)
    struct Decision {
        bytes32 decisionHash;      // Hash of decision rationale + context + timestamp
        uint256 timestamp;         // When decision was logged
        address executor;          // Agent address that made decision
        string ipfsProof;          // IPFS CID containing full decision data
        bool executed;             // Whether decision has been executed
        uint256 amount;            // Transaction amount (if applicable)
        address payee;             // Recipient address (if applicable)
    }

    /// @notice Structure to track transaction execution results (FR-008)
    struct TransactionRecord {
        bytes32 decisionHash;      // Link to decision that triggered this
        uint256 timestamp;         // Execution timestamp
        address to;                // Recipient address
        uint256 value;             // Amount transferred
        bytes data;                // Transaction data
        bool success;              // Execution success status
        string category;           // Transaction type (API payment, data purchase, etc.)
    }

    // State variables
    address public owner;
    bool public paused;            // Emergency pause flag (NFR-005)
    
    /// @notice Mapping of decision hashes to decision data
    mapping(bytes32 => Decision) public decisions;
    
    /// @notice Spending limits per token address (address(0) = ETH) (NFR-005)
    mapping(address => uint256) public spendingLimits;
    
    /// @notice Transaction records for audit trail (FR-008)
    TransactionRecord[] public transactionHistory;
    
    /// @notice Track total spent per token to enforce limits
    mapping(address => uint256) public totalSpent;

    // Events for on-chain audit trail (FR-008)
    event DecisionLogged(
        bytes32 indexed decisionHash,
        address indexed executor,
        string ipfsProof,
        uint256 timestamp
    );
    
    event DecisionExecuted(
        bytes32 indexed decisionHash,
        address indexed payee,
        uint256 amount,
        bool success
    );
    
    event TransactionRecorded(
        uint256 indexed recordId,
        bytes32 indexed decisionHash,
        address indexed to,
        uint256 value,
        string category,
        bool success
    );
    
    event SpendingLimitSet(
        address indexed token,
        uint256 limit
    );
    
    event EmergencyPause(bool paused);
    
    event OwnershipTransferred(
        address indexed previousOwner,
        address indexed newOwner
    );

    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "AgentWallet: caller is not the owner");
        _;
    }
    
    modifier whenNotPaused() {
        require(!paused, "AgentWallet: contract is paused");
        _;
    }

    constructor() {
        owner = msg.sender;
        paused = false;
        
        // Set default spending limits (0.1 ETH for hackathon demo)
        spendingLimits[address(0)] = 0.1 ether;
    }

    /**
     * @notice Log an AI agent decision before execution (FR-007)
     * @dev Creates cryptographic proof of autonomous decision-making
     * @param hash Hash of decision rationale + context + timestamp
     * @param ipfs IPFS CID containing full decision data
     */
    function logDecision(bytes32 hash, string memory ipfs) external whenNotPaused {
        require(hash != bytes32(0), "AgentWallet: invalid decision hash");
        require(bytes(ipfs).length > 0, "AgentWallet: IPFS CID required");
        require(decisions[hash].timestamp == 0, "AgentWallet: decision already logged");
        
        decisions[hash] = Decision({
            decisionHash: hash,
            timestamp: block.timestamp,
            executor: msg.sender,
            ipfsProof: ipfs,
            executed: false,
            amount: 0,
            payee: address(0)
        });
        
        emit DecisionLogged(hash, msg.sender, ipfs, block.timestamp);
    }

    /**
     * @notice Verify and execute a pre-logged decision (FR-007)
     * @dev Ensures decision was logged before execution for provenance
     * @param hash Decision hash to execute
     * @param payee Recipient address
     * @param amount Amount to transfer
     */
    function verifyAndExecute(
        bytes32 hash,
        address payee,
        uint256 amount
    ) external onlyOwner whenNotPaused returns (bool) {
        Decision storage decision = decisions[hash];
        
        require(decision.timestamp > 0, "AgentWallet: decision not logged");
        require(!decision.executed, "AgentWallet: decision already executed");
        require(payee != address(0), "AgentWallet: invalid payee");
        
        // Enforce spending limits (NFR-005)
        require(
            totalSpent[address(0)] + amount <= spendingLimits[address(0)],
            "AgentWallet: spending limit exceeded"
        );
        
        // Update decision record
        decision.executed = true;
        decision.amount = amount;
        decision.payee = payee;
        
        // Update spending tracker
        totalSpent[address(0)] += amount;
        
        // Execute transfer
        (bool success, ) = payee.call{value: amount}("");
        
        // Record transaction (FR-008)
        transactionHistory.push(TransactionRecord({
            decisionHash: hash,
            timestamp: block.timestamp,
            to: payee,
            value: amount,
            data: "",
            success: success,
            category: "autonomous_payment"
        }));
        
        emit DecisionExecuted(hash, payee, amount, success);
        emit TransactionRecorded(
            transactionHistory.length - 1,
            hash,
            payee,
            amount,
            "autonomous_payment",
            success
        );
        
        return success;
    }

    /**
     * @notice Set spending limit for a token (NFR-005)
     * @param token Token address (address(0) for ETH)
     * @param limit Maximum spendable amount
     */
    function setSpendingLimit(address token, uint256 limit) external onlyOwner {
        spendingLimits[token] = limit;
        emit SpendingLimitSet(token, limit);
    }

    /**
     * @notice Reset spending counter for a token
     * @param token Token address to reset
     */
    function resetSpentAmount(address token) external onlyOwner {
        totalSpent[token] = 0;
    }

    /**
     * @notice Emergency pause function (NFR-005)
     * @param _paused True to pause, false to unpause
     */
    function setPaused(bool _paused) external onlyOwner {
        paused = _paused;
        emit EmergencyPause(_paused);
    }

    /**
     * @notice Get decision details by hash
     * @param hash Decision hash to query
     */
    function getDecision(bytes32 hash) external view returns (Decision memory) {
        return decisions[hash];
    }

    /**
     * @notice Get transaction history length
     */
    function getTransactionCount() external view returns (uint256) {
        return transactionHistory.length;
    }

    /**
     * @notice Get transaction record by index
     * @param index Transaction index
     */
    function getTransaction(uint256 index) external view returns (TransactionRecord memory) {
        require(index < transactionHistory.length, "AgentWallet: invalid index");
        return transactionHistory[index];
    }

    /**
     * @notice Transfer ownership of the wallet
     * @param newOwner New owner address
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "AgentWallet: new owner is zero address");
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }

    /**
     * @notice Fund the wallet (receive ETH)
     */
    receive() external payable {}

    /**
     * @notice Withdraw funds (emergency only)
     * @param amount Amount to withdraw
     */
    function withdraw(uint256 amount) external onlyOwner {
        require(address(this).balance >= amount, "AgentWallet: insufficient balance");
        (bool success, ) = owner.call{value: amount}("");
        require(success, "AgentWallet: withdrawal failed");
    }

    /**
     * @notice Get wallet balance
     */
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
