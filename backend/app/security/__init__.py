"""
Security Layer - Key Management, Cryptography, and Authentication

Provides comprehensive security services for the WalletMind backend:

1. **KeyManager** (NFR-004):
   - BIP39 mnemonic generation
   - BIP44 key derivation
   - AES-256-GCM encrypted storage
   - Key rotation and backup
   - Zero private key exposure in logs

2. **CryptoService** (FR-007, NFR-006):
   - SHA-256 decision hashing
   - ECDSA signature creation/verification
   - Replay attack prevention with nonces
   - HMAC message authentication
   - Merkle tree for tamper-evident logging

3. **AuthService**:
   - API key generation and management
   - JWT token creation/validation
   - Role-based access control (RBAC)
   - Session management
   - Rate limiting

All services use singleton pattern for shared state management.
"""

from app.security.key_manager import (
    KeyManager,
    KeyMetadata,
    SensitiveDataFilter,
    get_key_manager
)

from app.security.crypto import (
    CryptoService,
    SignatureResult,
    VerificationResult,
    MerkleNode,
    NonceManager,
    get_crypto_service
)

from app.security.auth import (
    AuthService,
    UserRole,
    TokenType,
    APIKey,
    Session,
    RateLimitStatus,
    get_auth_service
)

__all__ = [
    # Key Manager
    "KeyManager",
    "KeyMetadata",
    "SensitiveDataFilter",
    "get_key_manager",
    
    # Crypto Service
    "CryptoService",
    "SignatureResult",
    "VerificationResult",
    "MerkleNode",
    "NonceManager",
    "get_crypto_service",
    
    # Auth Service
    "AuthService",
    "UserRole",
    "TokenType",
    "APIKey",
    "Session",
    "RateLimitStatus",
    "get_auth_service",
]
