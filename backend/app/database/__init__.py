"""
Database layer - Prisma ORM with PostgreSQL (Supabase)

Provides high-level interface for:
- User and authentication management
- Wallet and agent storage
- Decision and transaction logging
- Service offerings and API keys
- Audit logging and compliance
"""

from .connection import get_db, init_db, close_db, DatabaseManager
from .repositories.user_repository import UserRepository
from .repositories.wallet_repository import WalletRepository
from .repositories.agent_repository import AgentRepository
from .repositories.transaction_repository import TransactionRepository
from .repositories.decision_repository import DecisionRepository
from .repositories.audit_repository import AuditRepository
from .service import DatabaseService

__all__ = [
    # Connection management
    'get_db',
    'init_db',
    'close_db',
    'DatabaseManager',
    
    # Repositories
    'UserRepository',
    'WalletRepository',
    'AgentRepository',
    'TransactionRepository',
    'DecisionRepository',
    'AuditRepository',
    
    # Service layer
    'DatabaseService',
]

__version__ = '1.0.0'
