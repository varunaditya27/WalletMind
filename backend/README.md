<div align="center">

# WalletMind Backend

> Autonomous AI wallet backend powered by FastAPI, LangChain, and ChromaDB

</div>

The WalletMind backend is a production-grade FastAPI application that orchestrates LangChain AI agents to make autonomous, verifiable on-chain decisions. It features real-time WebSocket communication, vector-based memory, and comprehensive audit trails.

---

## 🏗️ Architecture

```
backend/
├── app/
│   ├── agents/              # LangChain AI agents
│   │   ├── base.py         # Base agent class
│   │   ├── planner.py      # Financial planning & risk assessment
│   │   ├── executor.py     # Transaction execution
│   │   ├── evaluator.py    # Post-execution evaluation
│   │   ├── communicator.py # External API & agent communication
│   │   ├── orchestrator.py # Multi-agent coordination
│   │   └── tools/          # Agent tool implementations
│   │       ├── blockchain_tools.py  # Wallet, tx, oracle tools
│   │       ├── data_tools.py        # Data provider tools
│   │       └── payment_tools.py     # API payment tools
│   │
│   ├── api/                 # FastAPI route handlers
│   │   ├── agents.py       # Agent orchestration endpoints ✅
│   │   ├── decisions.py    # Decision logging & retrieval
│   │   ├── transactions.py # Transaction management
│   │   ├── wallet.py       # Wallet operations
│   │   ├── verification.py # Audit trail & verification
│   │   ├── external.py     # External API integration
│   │   └── websocket.py    # Real-time WebSocket
│   │
│   ├── blockchain/          # Web3 integration
│   │   ├── provider.py     # Multi-chain RPC providers
│   │   ├── wallet.py       # Wallet management
│   │   ├── transaction.py  # Transaction building
│   │   └── networks.py     # Network configurations
│   │
│   ├── database/            # Prisma ORM
│   │   ├── service.py      # Database service
│   │   ├── connection.py   # Connection management
│   │   └── repositories/   # Data access layer
│   │       ├── decision_repository.py
│   │       ├── transaction_repository.py
│   │       └── agent_repository.py
│   │
│   ├── memory/              # Vector memory system
│   │   ├── vector_store.py # ChromaDB integration ✅
│   │   ├── context_manager.py  # Context management
│   │   └── chromadb_manager.py # DB lifecycle
│   │
│   ├── services/            # Business logic
│   │   ├── oracle_service.py      # Price feeds & oracles
│   │   ├── payment_service.py     # API payment processing
│   │   └── verification_service.py # Proof verification
│   │
│   ├── security/            # Security layer
│   │   ├── encryption.py   # Data encryption
│   │   ├── auth.py         # Authentication
│   │   └── rate_limit.py   # Rate limiting
│   │
│   ├── storage/             # IPFS storage
│   │   └── ipfs_client.py  # Pinata integration
│   │
│   ├── models/              # Pydantic models
│   │   ├── agent.py        # Agent request/response models
│   │   ├── transaction.py  # Transaction models
│   │   └── decision.py     # Decision models
│   │
│   ├── config.py            # Configuration management
│   └── main.py              # FastAPI application
│
├── docs/                    # Additional documentation
├── prisma/                  # Database schema
│   └── schema.prisma
├── requirements.txt         # Python dependencies
└── .env.example            # Environment template
```

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.11 or higher
- **PostgreSQL**: 14+ (local or cloud)
- **Redis**: (optional, for caching)
- **Node.js**: 18+ (for Prisma CLI)

### Installation

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Unix/MacOS
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Prisma
npm install -g prisma

# 5. Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# 6. Generate Prisma client
prisma generate

# 7. Run database migrations
prisma migrate dev
```

### Running the Server

```bash
# Development (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will be available at:
- **HTTP**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=info

# API Keys (Required)
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_ai_studio_key

# Database (Required)
DATABASE_URL=postgresql://user:password@localhost:5432/walletmind

# Redis (Optional)
REDIS_URL=redis://localhost:6379

# Blockchain RPC URLs
ETHEREUM_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY
POLYGON_RPC_URL=https://polygon-amoy.g.alchemy.com/v2/YOUR_KEY
BASE_RPC_URL=https://base-goerli.g.alchemy.com/v2/YOUR_KEY

# Private Keys (Development only - use KMS in production)
DEPLOYER_PRIVATE_KEY=your_private_key_here

# IPFS Storage
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_KEY=your_pinata_secret_key

# Security
SECRET_KEY=your_secret_key_for_encryption
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION=agent_memory

# Logging
LOG_FILE=logs/walletmind.log
```

### Database Setup

```bash
# Create database
createdb walletmind

# Run migrations
prisma migrate dev --name init

# Seed data (optional)
python scripts/seed_database.py

# View database
prisma studio
```

---

## 🤖 Agent System

The backend's core is a multi-agent system orchestrated by a central `OrchestratorAgent`. This design allows for a clear separation of concerns and robust, extensible workflows.

```mermaid
graph TD
    A[User Request] --> B{Orchestrator};
    B --> C[PlannerAgent];
    C -- "Plan & Risk Analysis" --> B;
    B -- "Approved Plan" --> D[ExecutorAgent];
    D -- "Executes Transaction" --> E[Blockchain];
    D -- "Execution Result" --> B;
    B --> F[EvaluatorAgent];
    F -- "Performance Metrics" --> B;
    subgraph External Communication
        G[CommunicatorAgent];
    end
    B -- "Needs External Data" --> G;
    G -- "Fetches Data (Oracles, APIs)" --> B;
    B -- "Final Response" --> H[User];
```

### Agent Types

1.  **PlannerAgent** (`planner.py`): Analyzes user requests, assesses risk, and creates multi-step execution plans.
2.  **ExecutorAgent** (`executor.py`): Executes approved plans, constructs blockchain transactions, and manages the transaction lifecycle.
3.  **EvaluatorAgent** (`evaluator.py`): Performs post-execution analysis, gathers performance metrics, and suggests optimizations.
4.  **CommunicatorAgent** (`communicator.py`): Handles all external communication, including querying oracles and interacting with third-party APIs.
5.  **OrchestratorAgent** (`orchestrator.py`): The central coordinator that manages the workflow, state, and error handling between all other agents.

### Agent Tools

Located in `app/agents/tools/`:

**Blockchain Tools** (`blockchain_tools.py`):
- `GetWalletBalanceTool`: Query wallet balances across chains
- `GetTransactionStatusTool`: Check transaction confirmation status
- `QueryOracleTool`: Fetch external oracle data

**Data Tools** (`data_tools.py`):
- `QueryDataProviderTool`: Query external data providers (Groq, Google AI)
- `AssessDataQualityTool`: Validate and score data quality

**Payment Tools** (`payment_tools.py`):
- `ExecutePaymentTool`: Process automated API payments
- `GetPaymentStatusTool`: Track payment transaction status

### Usage Example

```python
from app.agents.planner import PlannerAgent
from langchain_groq import ChatGroq

# Initialize LLM
llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize planner with tools
from app.agents.tools.blockchain_tools import GetWalletBalanceTool
planner = PlannerAgent(llm=llm, tools=[GetWalletBalanceTool()])

# Create context
from app.models.agent import DecisionContext
context = DecisionContext(
    request="Send 0.1 ETH to alice.eth",
    wallet_address="0x...",
    metadata={"known_addresses": ["0x..."]}
)

# Evaluate risk
result = await planner.evaluate_risk(context)
# {'risk_score': 0.3, 'reasoning': '...', 'estimated_cost': 0.001}
```

---

## 📡 API Reference

### API Endpoint Summary

| Category | Endpoint | Method | Description |
|---|---|---|---|
| **Agents** | `/api/agents/request` | `POST` | Processes a natural language request through the agent system. |
| | `/api/agents/health` | `GET` | Retrieves the health status of all agents. |
| | `/api/agents/decision/{id}`| `GET` | Fetches the details of a specific agent decision. |
| | `/api/agents/memory/query` | `POST` | Queries the agent's vector memory for relevant context. |
| | `/api/agents/memory/store` | `POST` | Stores a new interaction in the agent's memory. |
| **Transactions**| `/api/transactions/submit` | `POST` | Submits a new transaction to the blockchain. |
| | `/api/transactions/{hash}` | `GET` | Retrieves the status and details of a transaction. |
| | `/api/transactions/history`| `GET` | Gets the transaction history for a specific wallet. |
| **Wallet** | `/api/wallet/{address}/balance`| `GET` | Fetches the token balances for a wallet across all supported networks. |
| | `/api/wallet/{address}/status` | `GET` | Retrieves the current configuration and status of a wallet. |
| **Verification**| `/api/verification/audit-trail`| `GET` | Gets the complete, verifiable audit trail for a wallet. |
| | `/api/verification/timeline` | `GET` | Retrieves a chronological timeline of all decisions and transactions. |

### Core Endpoints

#### Agents (`/api/agents`)

**POST** `/api/agents/request`
- Process natural language request through agent system
- **Body**: `AgentRequest` (request: str, context: dict)
- **Returns**: `AgentResponse` with decision
- **Example**:
```bash
curl -X POST http://localhost:8000/api/agents/request \
  -H "Content-Type: application/json" \
  -d '{"request": "Send 0.1 ETH to alice.eth", "context": {"wallet_address": "0x..."}}'
```

**GET** `/api/agents/health`
- Get health status of all agents
- **Returns**: `List[AgentHealth]`
- **Example**:
```bash
curl http://localhost:8000/api/agents/health
```

**GET** `/api/agents/decision/{decision_id}`
- Retrieve specific decision details
- **Returns**: `AgentDecision`

**POST** `/api/agents/memory/query`
- Query agent memory using ChromaDB semantic search
- **Body**: `AgentMemoryQuery` (query: str, agent_type: str, limit: int)
- **Returns**: `AgentMemoryResponse` with relevant memories

**POST** `/api/agents/memory/store`
- Store interaction in agent memory
- **Body**: content: str, agent_type: AgentType, metadata: dict
- **Returns**: entry_id

**POST** `/api/agents/create`
- Create new agent instance
- **Body**: `CreateAgentRequest` (agent_type, name, config)
- **Returns**: `AgentInfo`

**DELETE** `/api/agents/{agent_id}`
- Stop and remove agent instance

**POST** `/api/agents/{agent_id}/reset`
- Reset agent state and clear memory

#### Transactions (`/api/transactions`)

**POST** `/api/transactions/submit`
- Submit new transaction
- **Body**: `TransactionRequest`
- **Returns**: Transaction hash

**GET** `/api/transactions/{tx_hash}`
- Get transaction details
- **Returns**: `Transaction`

**GET** `/api/transactions/history`
- Get transaction history
- **Query**: wallet_address, network, status, limit
- **Returns**: List of transactions

#### Wallet (`/api/wallet`)

**GET** `/api/wallet/{address}/balance`
- Get wallet balance across networks
- **Returns**: `BalanceResponse` with balances per chain

**GET** `/api/wallet/{address}/status`
- Get wallet configuration and status
- **Returns**: `WalletStatus` with spending limits, guardians

#### Verification (`/api/verification`)

**GET** `/api/verification/audit-trail`
- Get complete audit trail
- **Query**: wallet_address, start_date, end_date
- **Returns**: List of `AuditEntry`

**GET** `/api/verification/timeline`
- Get decision timeline
- **Returns**: Chronological event timeline

### WebSocket (`/ws`)

**Connect**: `ws://localhost:8000/ws`

**Subscribe to channels**:
```json
{
  "action": "subscribe",
  "channels": ["agents", "transactions", "decisions", "verification"]
}
```

**Receive real-time events**:
```json
{
  "channel": "agents",
  "event": "agent_decision",
  "data": {
    "decision_id": "dec_123",
    "agent_type": "planner",
    "status": "pending",
    "risk_score": 0.3
  },
  "timestamp": "2024-10-29T10:30:00Z"
}
```

---

## 💾 Database Schema

Key entities in `prisma/schema.prisma`:

### Decision
```prisma
model Decision {
  id            String   @id @default(cuid())
  agentId       String
  decisionHash  String   @unique
  reasoning     String
  action        String
  parameters    Json
  confidence    Int
  status        String   // PENDING, EXECUTED, FAILED
  createdAt     DateTime @default(now())
  executedAt    DateTime?
  onChainTxHash String?
  ipfsHash      String?
}
```

### Transaction
```prisma
model Transaction {
  id           String   @id @default(cuid())
  txHash       String   @unique
  fromAddress  String
  toAddress    String
  value        String
  network      String
  status       String   // PENDING, CONFIRMED, FAILED
  gasUsed      String?
  decisionId   String?
  createdAt    DateTime @default(now())
  confirmedAt  DateTime?
}
```

### AgentActivity
```prisma
model AgentActivity {
  id         String   @id @default(cuid())
  agentType  String   // planner, executor, evaluator, communicator
  action     String
  status     String
  metadata   Json
  walletId   String
  createdAt  DateTime @default(now())
}
```

---

## 🧠 Memory System

### ChromaDB Integration

The backend uses ChromaDB for agent memory and context management:

```python
from app.memory.vector_store import MemoryService

# Initialize
memory = MemoryService(
    persist_directory="./chroma_db",
    collection_name="agent_memory"
)

# Store interaction
await memory.store(
    wallet_address="0x...",
    agent_type="planner",
    request="Send 0.1 ETH",
    response={"decision_id": "dec_123"},
    reasoning="Low risk transaction to known address",
    timestamp=datetime.now()
)

# Query similar interactions
results = await memory.query(
    query="ETH transfer transactions",
    wallet_address="0x...",
    limit=5
)

# Results include semantically similar past decisions
for result in results:
    print(result["content"])  # Full interaction context
    print(result["metadata"])  # Timestamps, agent type, etc.
```

### Benefits

- **Semantic Search**: Find similar past decisions using vector similarity
- **Context Retention**: Agents learn from historical interactions
- **Pattern Recognition**: Identify recurring transaction patterns
- **Persistent Memory**: Survives server restarts with disk persistence

---

## 🔐 Security

### Implemented Features

✅ **Environment Variables**: All secrets in .env  
✅ **Input Validation**: Pydantic model validation on all endpoints  
✅ **CORS**: Configurable allowed origins  
✅ **Private Key Encryption**: Database-stored keys encrypted  
✅ **Audit Logging**: All agent actions logged  
⏳ **Rate Limiting**: In development  
⏳ **API Authentication**: Planned for v1.1  

### Best Practices

```python
# ❌ Don't hardcode secrets
API_KEY = "sk-abc123..."

# ✅ Use environment variables
import os
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY not set")

# ✅ Validate inputs with Pydantic
from pydantic import BaseModel, validator

class TransactionRequest(BaseModel):
    to_address: str
    amount: float
    
    @validator('to_address')
    def validate_address(cls, v):
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid Ethereum address')
        return v
```

### Production Checklist

- [ ] Use AWS KMS or similar for private keys
- [ ] Enable rate limiting on all endpoints
- [ ] Add JWT-based API authentication
- [ ] Configure firewall rules (whitelist IPs)
- [ ] Enable HTTPS only (no HTTP)
- [ ] Regular dependency security scans
- [ ] Monitor for anomalous activity

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_agents.py

# With coverage
pytest --cov=app --cov-report=html

# Integration tests
pytest tests/integration/

# Watch mode (auto-rerun on changes)
ptw
```

### Writing Tests

```python
# tests/test_agents.py
import pytest
from app.agents.planner import PlannerAgent
from app.models.agent import DecisionContext

@pytest.mark.asyncio
async def test_planner_risk_assessment():
    """Test that planner correctly assesses high-value transaction risk"""
    planner = PlannerAgent()
    
    context = DecisionContext(
        request="Send 100 ETH to unknown address",
        wallet_address="0x123...",
        metadata={"known_addresses": []}
    )
    
    result = await planner.evaluate_risk(context)
    
    assert result["risk_score"] > 0.7  # High risk expected
    assert "high value" in result["reasoning"].lower()
    assert result["requires_approval"] is True
```

---

## 🔧 Development

### Code Style

We follow PEP 8 with Black formatting:

```bash
# Format code
black app/

# Lint
pylint app/

# Type checking
mypy app/

# Sort imports
isort app/

# All checks
black app/ && isort app/ && pylint app/ && mypy app/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use breakpoints
import pdb; pdb.set_trace()

# Or with ipdb (better interface)
import ipdb; ipdb.set_trace()

# FastAPI debug mode
uvicorn app.main:app --reload --log-level debug
```

---

## 📊 Monitoring

### Logging

Structured logging throughout the application:

```python
import logging

logger = logging.getLogger(__name__)

# Structured log with context
logger.info("Agent decision processed", extra={
    "agent_type": "planner",
    "decision_id": "dec_123",
    "risk_score": 0.3,
    "execution_time_ms": 245
})
```

### Key Metrics

Monitor these metrics in production:

- **Agent Response Time**: Target <500ms
- **Decision Approval Rate**: Track auto vs manual approvals
- **Transaction Success Rate**: Should be >95%
- **Memory Query Latency**: Target <100ms
- **API Error Rate**: Should be <1%
- **WebSocket Connection Count**: Monitor for limits

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Agent system health
curl http://localhost:8000/api/agents/health

# Database connectivity
curl http://localhost:8000/health/db

# Memory system
curl http://localhost:8000/health/memory
```

---

## 🐛 Troubleshooting

### Common Issues

**1. ChromaDB Connection Error**
```
ERROR: chromadb.errors.ChromaError: Could not connect to ChromaDB
```
**Solution**:
```bash
mkdir -p chroma_db
chmod 755 chroma_db
# Restart server
```

**2. Database Connection Failed**
```
ERROR: Could not connect to PostgreSQL
```
**Solution**:
```bash
# Check PostgreSQL is running
pg_isready
# Verify DATABASE_URL in .env
echo $DATABASE_URL
# Test connection
psql $DATABASE_URL
```

**3. Import Errors After Schema Change**
```
ERROR: Cannot import name 'Decision' from 'prisma.models'
```
**Solution**:
```bash
# Regenerate Prisma client
prisma generate
# Restart server
```

**4. Agent Timeout**
```
ERROR: Agent took too long to respond
```
**Solution**:
```python
# Increase timeout in config.py
AGENT_TIMEOUT = 60  # seconds

# Or in specific agent call
result = await planner.evaluate_risk(context, timeout=120)
```

**5. Memory Full / OOM**
```
ERROR: MemoryError: Cannot allocate memory
```
**Solution**:
```bash
# Check memory usage
free -h
# Reduce batch sizes in config.py
BATCH_SIZE = 10  # Reduce from 50
# Restart with more workers
uvicorn app.main:app --workers 2  # Reduce from 4
```

---

## 📚 Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Python Docs](https://python.langchain.com/)
- [Prisma Python Client](https://prisma-client-py.readthedocs.io/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

### Tutorials
- [Building LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Vector Databases Guide](https://www.pinecone.io/learn/vector-database/)

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Workflow

1. **Fork the repository**
```bash
git clone https://github.com/yourusername/WalletMind.git
cd WalletMind/backend
```

2. **Create feature branch**
```bash
git checkout -b feature/amazing-feature
```

3. **Make changes and test**
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black app/
```

4. **Commit and push**
```bash
git commit -m 'feat: Add amazing feature'
git push origin feature/amazing-feature
```

5. **Open Pull Request**

### Coding Guidelines

- ✅ Write tests for new features
- ✅ Update documentation
- ✅ Follow PEP 8 style guide
- ✅ Add type hints to functions
- ✅ Keep functions focused and small (<50 lines)
- ✅ Use descriptive variable names
- ✅ Add docstrings to public APIs

### Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add new agent tool
fix: Resolve memory leak in ChromaDB
docs: Update API documentation
test: Add integration tests for planner
refactor: Simplify risk scoring logic
```

---

## 📄 License

MIT License - See [LICENSE](../LICENSE) for details

---

## 📞 Support

Need help?

- **Issues**: [GitHub Issues](https://github.com/yourusername/WalletMind/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/WalletMind/discussions)

---

## 🙏 Acknowledgments

Built with these amazing technologies:

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [LangChain](https://python.langchain.com/) - AI agent orchestration
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Prisma](https://www.prisma.io/) - Next-generation ORM
- [Web3.py](https://web3py.readthedocs.io/) - Ethereum integration

---

**Built with ❤️ by the WalletMind Team**

*Making AI agents verifiable economic actors on-chain*
