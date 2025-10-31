# WalletMind - AI Agent Autonomous Wallet System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Node](https://img.shields.io/badge/Node-20+-green.svg)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)

**WalletMind** is a production-ready autonomous AI agent wallet system that enables AI agents to make verifiable, auditable blockchain transactions. Built with LangChain, FastAPI, Next.js, and ERC-4337 smart accounts.

## 🌟 Features

### Core Capabilities
- **🤖 Multi-Agent Orchestration**: Planner, Executor, Evaluator, and Communicator agents coordinate via LangChain
- **🔐 ERC-4337 Smart Accounts**: Safe SDK integration with programmable guardrails
- **📝 On-Chain Provenance**: Every decision is hashed, timestamped, and logged before execution
- **💰 API Payment Automation**: Autonomous payments for Groq, Google AI Studio, and x402 APIs
- **🌐 Multi-Network Support**: Ethereum Sepolia, Polygon Amoy, Base Goerli
- **📊 Real-Time Dashboard**: WebSocket-powered live updates and telemetry
- **🔍 Verification & Audit**: Complete audit trail with IPFS storage and blockchain anchoring

## 🏗️ Architecture

```
WalletMind/
├── backend/                 # FastAPI + LangChain backend
│   ├── app/
│   │   ├── agents/         # AI agents (Planner, Executor, Evaluator, Communicator)
│   │   ├── api/            # REST & WebSocket endpoints
│   │   ├── blockchain/     # Web3 integration
│   │   ├── services/       # Business logic
│   │   └── models/         # Pydantic schemas
├── frontend/                # Next.js 15 + React dashboard
│   ├── app/                # App router pages
│   ├── components/         # UI components
│   └── lib/                # Services, stores, utilities
└── blockchain/             # Hardhat smart contracts
    ├── contracts/          # AgentWallet, AgentRegistry
    └── scripts/            # Deployment scripts
```

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

## 📚 Documentation

### API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Full API Guide**: [backend/docs/API_IMPLEMENTATION_COMPLETE.md](backend/docs/API_IMPLEMENTATION_COMPLETE.md)

### Architecture Guides

- **Agent Implementation**: [backend/docs/AGENT_IMPLEMENTATION.md](backend/docs/AGENT_IMPLEMENTATION.md)
- **Blockchain Integration**: [backend/docs/BLOCKCHAIN_COMPLETE.md](backend/docs/BLOCKCHAIN_COMPLETE.md)
- **Security**: [backend/docs/SECURITY_COMPLETE.md](backend/docs/SECURITY_COMPLETE.md)

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

## 📈 Roadmap

### v1.0 (Current)
- ✅ Multi-agent orchestration
- ✅ ERC-4337 smart accounts
- ✅ On-chain decision logging
- ✅ Real-time dashboard
- ✅ API payment automation

### v1.1 (Planned)
- [ ] Mainnet deployment
- [ ] Additional LLM providers
- [ ] Advanced spending strategies
- [ ] Mobile app

### v2.0 (Future)
- [ ] Cross-chain operations
- [ ] DeFi protocol integration
- [ ] Agent marketplace
- [ ] Reputation system

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
- **Documentation**: [Full docs](https://github.com/varunaditya27/WalletMind/wiki)

---

**Built with ❤️ for the autonomous agent future**

*Making AI agents trustworthy economic actors, one transaction at a time.*
