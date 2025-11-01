<div align="center">

# WalletMind: Autonomous AI Agent Wallet System

</div>

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node-20+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-_1CC.svg)](https://fastapi.tiangolo.com/)
[![Next.js](httpshttps://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3+-38B2AC.svg)](https://tailwindcss.com/)
[![Hardhat](https://img.shields.io/badge/Hardhat-2+-blue.svg)](https://hardhat.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-yellow.svg)](https://www.langchain.com/)

</div>

<div align="center">

**WalletMind** is a production-grade, autonomous AI agent wallet system engineered to empower AI agents as verifiable, auditable economic actors on the blockchain. It integrates LangChain, FastAPI, Next.js, and ERC-4337 smart accounts to deliver a robust platform for autonomous operations.

</div>

## 🌟 Features

### Core Capabilities
- **🤖 Multi-Agent Orchestration**: A sophisticated multi-agent system (Planner, Executor, Evaluator, Communicator) coordinates complex tasks using LangChain.
- **🔐 ERC-4337 Smart Accounts**: Leverages Safe SDK for programmable, secure smart accounts with customizable guardrails.
- **📝 On-Chain Provenance**: Implements a "decision-first" workflow where every agent decision is hashed, timestamped, and logged on-chain *before* execution.
- **💰 Autonomous Payments**: Natively supports automated payments for services like Groq, Google AI Studio, and other x402-compliant APIs.
- **🌐 Multi-Network Support**: Production-ready for Ethereum Sepolia, Polygon Amoy, and Base Goerli.
- **📊 Real-Time Dashboard**: A sleek, WebSocket-powered dashboard provides live telemetry and operational insights.
- **🔍 Verifiable Audits**: Guarantees a complete, immutable audit trail by anchoring proofs to IPFS and the blockchain.

## 🏗️ System Architecture

WalletMind is a full-stack, three-part system composed of a frontend, backend, and blockchain component that work in concert to deliver autonomous agent capabilities.

```mermaid
graph TD
    subgraph User Interface
        A[Next.js Frontend]
    end

    subgraph Backend Services
        B[FastAPI Server]
        C[Multi-Agent System]
        D[PostgreSQL Database]
        E[ChromaDB Vector Memory]
    end

    subgraph Blockchain Network
        F[AgentWallet & AgentRegistry Contracts]
        G[EVM-Compatible Chain]
    end

    A -- "REST & WebSocket" --> B
    B -- "Orchestrates" --> C
    C -- "Stores & Retrieves Data" --> D
    C -- "Accesses Contextual Memory" --> E
    B -- "Submits Transactions" --> F
    F -- "Deployed on" --> G
```

| Component | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js, TypeScript, Tailwind | Provides a real-time user interface for monitoring and managing agents. |
| **Backend** | FastAPI, Python, LangChain | Orchestrates the multi-agent system, handles business logic, and serves the API. |
| **Blockchain** | Solidity, Hardhat, Viem | Implements the on-chain decision logging and agent registry for security and auditability. |

## 🚀 Quick Start

### Prerequisites

- **Node.js** 20+ and npm/yarn/pnpm
- **Python** 3.11+ and pip
- **PostgreSQL** (optional, for production)
- **API Keys**: Groq, Google AI Studio (optional)

### 1. Clone Repository

```bash
git clone https://github.com/varunaditya27/WalletMind.git
cd WalletMind
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend runs at**: `http://localhost:8000`  
**API docs**: `http://localhost:8000/api/docs`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install  # or: yarn / pnpm install

# Configure environment
cp .env.example .env.local
# Edit .env.local if needed (defaults work for local dev)

# Run frontend
npm run dev
```

**Frontend runs at**: `http://localhost:3000`

### 4. Blockchain Setup (Optional)

```bash
cd blockchain

# Install dependencies
npm install

# Compile contracts
npx hardhat compile

# Deploy to Sepolia testnet
npx hardhat run scripts/deploy.ts --network sepolia
```


## 🔧 Configuration

### Environment Variables

#### Backend (`backend/.env`)

```bash
# Required
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key

# Optional
DATABASE_URL=postgresql://user:password@localhost:5432/walletmind
REDIS_URL=redis://localhost:6379
PINATA_API_KEY=your_pinata_key
PRIVATE_KEY=your_wallet_private_key
```

#### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_PRIMARY_WALLET_ADDRESS=0x1234000000000000000000000000000000001234
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/                  # Run all tests
pytest tests/test_agents.py   # Run specific test
pytest --cov                   # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test              # Run tests
npm run test:watch   # Watch mode
npm run build        # Production build test
```

## 📊 Usage Examples

### Process Natural Language Request

```bash
curl -X POST http://localhost:8000/api/agents/request \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "request": "Send 0.01 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "agent_type": "planner"
  }'
```

### Execute Transaction

```bash
curl -X POST http://localhost:8000/api/transactions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "0x...",
    "to_address": "0x...",
    "amount": 0.01,
    "transaction_type": "internal_transfer"
  }'
```

### Query Audit Trail

```bash
curl -X POST http://localhost:8000/api/verification/audit-trail \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "0x...",
    "limit": 20
  }'
```

## 🛡️ Security

WalletMind implements multiple security layers:

- **Key Management**: AES-256 encryption for private keys
- **Spending Limits**: Configurable per-transaction and daily limits
- **Emergency Pause**: Immediate wallet freeze capability
- **Audit Trail**: Complete on-chain provenance log
- **Decision Verification**: Pre-execution decision hashing
- **Multi-Signature Support**: Safe smart account integration

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - Agent orchestration
- [Safe](https://safe.global/) - Smart account infrastructure
- [Hardhat](https://hardhat.org/) - Ethereum development
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Next.js](https://nextjs.org/) - Frontend framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/varunaditya27/WalletMind/issues)

---

**Built with ❤️ for the autonomous agent future**

*Making AI agents trustworthy economic actors, one transaction at a time.*
