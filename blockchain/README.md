# WalletMind - Smart Contracts

Blockchain infrastructure for the WalletMind AI Agent Autonomous Wallet System.

## 📋 Overview

This directory contains Solidity smart contracts implementing:

- **AgentWallet**: Decision provenance logging and autonomous transaction execution (FR-004, FR-007, FR-008)
- **AgentRegistry**: Agent discovery, reputation tracking, and service offerings (FR-012)

**Network:** Ethereum Sepolia Testnet only

**Stack:** Hardhat 3.0 + TypeScript + Viem + Node Test Runner

## 🏗️ Architecture

### Smart Contracts

#### **AgentWallet.sol**
Main wallet contract for AI agents featuring:
- ✅ Decision logging before execution (FR-007)
- ✅ On-chain audit trail (FR-008)
- ✅ Spending limits enforcement (NFR-005)
- ✅ Emergency pause functionality
- ✅ Transaction history tracking

#### **AgentRegistry.sol**
Registry for agent discovery and reputation:
- ✅ Agent registration and metadata (FR-012)
- ✅ Reputation scoring (0-1000 scale)
- ✅ Service offerings and discovery
- ✅ Success rate tracking

## 🚀 Quick Start

### Prerequisites

```bash
node >= 18.0.0
npm >= 9.0.0
```

### Installation

```bash
# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit .env with your keys
```

### Configuration

Edit `.env` file with your Metamask wallet and Alchemy credentials:

```env
SEPOLIA_PRIVATE_KEY=your_metamask_private_key_here
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_API_KEY
ETHERSCAN_API_KEY=your_etherscan_api_key_here
```

**How to get these:**

- **Metamask Private Key**: Open Metamask → Account Details → Export Private Key
- **Alchemy API Key**: Sign up at [alchemy.com](https://www.alchemy.com/) → Create App → Copy API Key
- **Etherscan API Key**: Sign up at [etherscan.io](https://etherscan.io/myapikey) → Create API Key

### Compile Contracts

```bash
npm run compile
```

### Run Tests

```bash
# Run all tests
npm test

# Run with verbose output
npm run test:verbose
```

## 📦 Deployment

### Get Sepolia Testnet ETH

```bash
# Show faucet information
npm run testnet:fund
```

Visit faucets:

- **Alchemy Sepolia Faucet**: <https://sepoliafaucet.com/> (Recommended - 0.5 ETH)
- **QuickNode Faucet**: <https://faucet.quicknode.com/ethereum/sepolia>
- **Google Cloud Faucet**: <https://cloud.google.com/application/web3/faucet/ethereum/sepolia>
- **Infura Faucet**: <https://www.infura.io/faucet/sepolia>

### Check Balance

```bash
npm run check:balance
```

### Deploy to Sepolia

```bash
npm run deploy:sepolia
```

Deployment info is saved to `../deployed-contracts.json`

## 🧪 Testing

### Test Coverage

Comprehensive tests using Viem and Hardhat:

```bash
AgentWallet
  ✓ Should set the right owner
  ✓ Should log decisions (FR-007)
  ✓ Should enforce spending limits (NFR-005)
  ✓ Should prevent execution without decision logging
  ✓ Should track transaction history (FR-008)
  ...

AgentRegistry
  ✓ Should register agents (FR-012)
  ✓ Should update reputation
  ✓ Should track success rates
  ✓ Should enable agent discovery
  ...
```

### Run Specific Tests

```bash
# Test specific contract
npx hardhat test test/AgentWallet.ts
npx hardhat test test/AgentRegistry.ts
```

## 🔧 Scripts

### Deployment

```bash
npm run deploy:sepolia          # Deploy to Sepolia testnet
npm run deploy:local            # Deploy to local hardhat network
```

### Interaction

```bash
# Interact with AgentWallet
npx hardhat run scripts/interact-wallet.ts --network sepolia

# Interact with AgentRegistry
npx hardhat run scripts/interact-registry.ts --network sepolia
```

### Utilities

```bash
npm run check:balance          # Check Sepolia balance
npm run testnet:fund          # Show faucet information
npm run clean                 # Clean artifacts
npm run typecheck            # TypeScript type checking
```

## 📁 Directory Structure

```
blockchain/
├── contracts/
│   ├── AgentWallet.sol        # Main agent wallet contract
│   └── AgentRegistry.sol      # Agent registry contract
├── ignition/modules/
│   ├── AgentWallet.ts         # Deployment module
│   ├── AgentRegistry.ts       # Deployment module
│   └── WalletMind.ts          # Combined deployment
├── scripts/
│   ├── deploy.ts              # Main deployment script
│   ├── interact-wallet.ts     # Wallet interaction examples
│   ├── interact-registry.ts   # Registry interaction examples
│   ├── check-balance.ts       # Balance checker
│   └── get-testnet-funds.ts   # Faucet info
├── test/
│   ├── AgentWallet.ts         # Wallet tests (Viem)
│   └── AgentRegistry.ts       # Registry tests (Viem)
├── hardhat.config.ts          # Hardhat configuration
├── package.json               # Dependencies & scripts
└── README.md                  # This file
```

## 🔐 Security Considerations

### Private Key Management

- ❌ **NEVER** commit private keys to git
- ✅ Use `.env` file (gitignored)
- ✅ Export from Metamask: Account Details → Export Private Key
- ✅ Use hardware wallets for mainnet (Ledger, Trezor)

### Smart Contract Security
- ✅ Spending limits enforced at contract level
- ✅ Emergency pause functionality
- ✅ Owner-only critical functions
- ✅ Reentrancy protection (Checks-Effects-Interactions pattern)

### Recommendations

- 🔒 Audit contracts before mainnet deployment
- 🔄 Test thoroughly on Sepolia testnet
- 📊 Monitor transactions on Etherscan
- 🚨 Set up alerts for unusual activity
- 🔑 Keep your Metamask seed phrase secure

## 📖 Contract Interfaces

### AgentWallet

```solidity
// Log AI decision before execution
function logDecision(bytes32 hash, string memory ipfs) external;

// Execute pre-logged decision
function verifyAndExecute(
    bytes32 hash,
    address payee,
    uint256 amount
) external returns (bool);

// Set spending limit
function setSpendingLimit(address token, uint256 limit) external;

// Emergency pause
function setPaused(bool _paused) external;
```

### AgentRegistry

```solidity
// Register agent
function registerAgent(string memory metadata) external;

// Update reputation
function updateReputation(address agent, bool success) external;

// Register service
function registerService(
    string memory serviceId,
    uint256 price,
    string memory description
) external;

// Get all agents
function getAllAgents() external view returns (address[] memory);
```

## 🌐 Networks

### Ethereum Sepolia Testnet

| Property | Value |
|---------|-------|
| **Chain ID** | 11155111 |
| **RPC URL** | https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY |
| **Explorer** | <https://sepolia.etherscan.io> |
| **Faucet** | <https://sepoliafaucet.com/> |
| **Currency** | SepoliaETH (testnet ETH) |

### Add Sepolia to Metamask

1. Open Metamask
2. Click network dropdown → "Add Network"
3. Search for "Sepolia" or add manually:
   - Network Name: Sepolia
   - RPC URL: https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY
   - Chain ID: 11155111
   - Currency Symbol: ETH
   - Block Explorer: https://sepolia.etherscan.io

## 📚 Additional Resources

- [Hardhat Documentation](https://hardhat.org/docs)
- [Viem Documentation](https://viem.sh/)
- [Solidity Documentation](https://docs.soliditylang.org/)
- [Metamask Documentation](https://docs.metamask.io/)
- [Alchemy Documentation](https://docs.alchemy.com/)
- [Etherscan API Documentation](https://docs.etherscan.io/)
- [Sepolia Testnet Info](https://sepolia.dev/)

## 🤝 Integration with Backend

Contract ABIs are automatically synced to the Python backend:

```bash
# From backend/ directory
python scripts/sync_contracts.py
```

This copies ABIs from `blockchain/artifacts/` to `backend/app/blockchain/contracts/abis/`

## 📝 License

MIT - See LICENSE file

## 👥 Contributing

1. Create feature branch
2. Write tests
3. Ensure all tests pass: `npm test`
4. Submit pull request

---

**Built with ❤️ for WalletMind AI Agent System**

## Project Overview

This example project includes:

- A simple Hardhat configuration file.
- Foundry-compatible Solidity unit tests.
- TypeScript integration tests using [`node:test`](nodejs.org/api/test.html), the new Node.js native test runner, and [`viem`](https://viem.sh/).
- Examples demonstrating how to connect to different types of networks, including locally simulating OP mainnet.

## Usage

### Running Tests

To run all the tests in the project, execute the following command:

```shell
npx hardhat test
```

You can also selectively run the Solidity or `node:test` tests:

```shell
npx hardhat test solidity
npx hardhat test nodejs
```

### Make a deployment to Sepolia

This project includes an example Ignition module to deploy the contract. You can deploy this module to a locally simulated chain or to Sepolia.

To run the deployment to a local chain:

```shell
npx hardhat ignition deploy ignition/modules/Counter.ts
```

To run the deployment to Sepolia, you need an account with funds to send the transaction. The provided Hardhat configuration includes a Configuration Variable called `SEPOLIA_PRIVATE_KEY`, which you can use to set the private key of the account you want to use.

You can set the `SEPOLIA_PRIVATE_KEY` variable using the `hardhat-keystore` plugin or by setting it as an environment variable.

To set the `SEPOLIA_PRIVATE_KEY` config variable using `hardhat-keystore`:

```shell
npx hardhat keystore set SEPOLIA_PRIVATE_KEY
```

After setting the variable, you can run the deployment with the Sepolia network:

```shell
npx hardhat ignition deploy --network sepolia ignition/modules/Counter.ts
```
