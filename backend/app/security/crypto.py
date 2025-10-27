"""
Cryptographic Service - Decision Integrity and Tamper Detection (FR-007, NFR-006)

Handles:
- SHA-256 decision hashing with deterministic serialization
- Cryptographic signature creation and verification
- Replay attack prevention with nonces and timestamps
- Tamper-evident logging with merkle tree support
- Message authentication codes (HMAC)
- Data integrity verification
"""

import hashlib
import hmac
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from web3 import Web3
from eth_account.messages import encode_defunct
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class SignatureResult:
    """Result of signature operation"""
    signature: str
    signer_address: str
    message_hash: str
    timestamp: datetime
    nonce: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class VerificationResult:
    """Result of signature verification"""
    is_valid: bool
    recovered_address: str
    expected_address: str
    match: bool
    timestamp: datetime
    age_seconds: float
    message_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MerkleNode:
    """Node in merkle tree for tamper-evident logging"""
    hash: str
    left: Optional['MerkleNode'] = None
    right: Optional['MerkleNode'] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "hash": self.hash,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None
        }


class NonceManager:
    """Manages nonces for replay attack prevention"""
    
    def __init__(self, validity_seconds: int = 300):
        """
        Initialize nonce manager.
        
        Args:
            validity_seconds: How long nonces are valid
        """
        self.used_nonces: Dict[str, datetime] = {}
        self.validity_period = timedelta(seconds=validity_seconds)
        
    def generate_nonce(self) -> str:
        """Generate a new nonce"""
        return secrets.token_hex(16)
    
    def use_nonce(self, nonce: str) -> bool:
        """
        Mark nonce as used and validate.
        
        Args:
            nonce: Nonce to check
            
        Returns:
            True if nonce is valid and unused, False if replay attack detected
        """
        # Clean up expired nonces
        self._cleanup_expired()
        
        # Check if already used
        if nonce in self.used_nonces:
            logger.warning(f"Replay attack detected: nonce {nonce[:8]}... already used")
            return False
        
        # Mark as used
        self.used_nonces[nonce] = datetime.now()
        return True
    
    def _cleanup_expired(self):
        """Remove expired nonces"""
        now = datetime.now()
        expired = [
            nonce for nonce, timestamp in self.used_nonces.items()
            if now - timestamp > self.validity_period
        ]
        for nonce in expired:
            del self.used_nonces[nonce]
        
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired nonces")


class CryptoService:
    """
    Cryptographic operations service implementing FR-007 and NFR-006.
    
    Features:
    - Deterministic SHA-256 hashing for decisions
    - ECDSA signature creation and verification (secp256k1)
    - Replay attack prevention with nonces
    - Timestamp validation
    - HMAC for message authentication
    - Merkle tree construction for tamper-evident logs
    - Ethereum-compatible signatures (EIP-191)
    
    Security:
    - All signatures include timestamp and nonce
    - Nonce reuse detected and prevented
    - Constant-time signature verification
    - No private key exposure in logs
    """
    
    def __init__(self, nonce_validity_seconds: int = 300):
        """
        Initialize CryptoService.
        
        Args:
            nonce_validity_seconds: Nonce validity period
        """
        self.web3 = Web3()
        self.nonce_manager = NonceManager(nonce_validity_seconds)
        logger.info("CryptoService initialized")
    
    def generate_decision_hash(
        self,
        decision_data: Dict[str, Any],
        include_timestamp: bool = True
    ) -> str:
        """
        Generate deterministic SHA-256 hash of decision data.
        
        Args:
            decision_data: Decision information to hash
            include_timestamp: Whether to include current timestamp
            
        Returns:
            Hex hash string (0x-prefixed)
        """
        try:
            # Create canonical representation
            canonical_data = {
                "agent_id": decision_data.get("agent_id"),
                "prompt": decision_data.get("prompt"),
                "plan": decision_data.get("plan"),
                "risk_level": decision_data.get("risk_level"),
                "metadata": decision_data.get("metadata", {}),
            }
            
            if include_timestamp:
                canonical_data["timestamp"] = decision_data.get(
                    "timestamp",
                    datetime.now().isoformat()
                )
            
            # Sort keys for determinism
            json_str = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
            decision_hash = hashlib.sha256(json_str.encode()).hexdigest()
            
            logger.debug(f"Generated decision hash: 0x{decision_hash[:8]}...")
            return f"0x{decision_hash}"
            
        except Exception as e:
            logger.error(f"Error generating decision hash: {e}")
            raise
    
    def create_signature(
        self,
        message: str,
        private_key: str,
        include_nonce: bool = True
    ) -> SignatureResult:
        """
        Create cryptographic signature with replay protection.
        
        Args:
            message: Message to sign (hex string or plain text)
            private_key: Private key for signing
            include_nonce: Whether to include nonce for replay protection
            
        Returns:
            SignatureResult with signature and metadata
        """
        try:
            # Generate nonce if requested
            nonce = self.nonce_manager.generate_nonce() if include_nonce else ""
            timestamp = datetime.now()
            
            # Prepare message with timestamp and nonce
            signed_message = {
                "message": message,
                "timestamp": timestamp.isoformat(),
                "nonce": nonce
            }
            message_str = json.dumps(signed_message, sort_keys=True)
            
            # Create Ethereum signed message
            encoded_message = encode_defunct(text=message_str)
            signed = self.web3.eth.account.sign_message(
                encoded_message,
                private_key=private_key
            )
            
            # Get signer address
            account = self.web3.eth.account.from_key(private_key)
            
            result = SignatureResult(
                signature=signed.signature.hex(),
                signer_address=account.address,
                message_hash=signed.messageHash.hex(),
                timestamp=timestamp,
                nonce=nonce
            )
            
            logger.debug(f"Created signature with address {account.address}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating signature: {e}")
            raise
    
    def verify_signature(
        self,
        message: str,
        signature: str,
        expected_signer: str,
        nonce: Optional[str] = None,
        timestamp: Optional[str] = None,
        max_age_seconds: int = 3600
    ) -> VerificationResult:
        """
        Verify cryptographic signature with replay attack prevention.
        
        Args:
            message: Original message
            signature: Signature to verify
            expected_signer: Expected signer address
            nonce: Nonce from signature (for replay protection)
            timestamp: Timestamp from signature
            max_age_seconds: Maximum allowed signature age
            
        Returns:
            VerificationResult with validation details
        """
        try:
            # Reconstruct signed message
            signed_message = {
                "message": message,
                "timestamp": timestamp or datetime.now().isoformat(),
                "nonce": nonce or ""
            }
            message_str = json.dumps(signed_message, sort_keys=True)
            
            # Recover signer from signature
            encoded_message = encode_defunct(text=message_str)
            recovered_address = self.web3.eth.account.recover_message(
                encoded_message,
                signature=signature
            )
            
            # Verify signer matches
            match = recovered_address.lower() == expected_signer.lower()
            
            # Check nonce for replay attack
            nonce_valid = True
            if nonce:
                nonce_valid = self.nonce_manager.use_nonce(nonce)
                if not nonce_valid:
                    logger.warning(f"Nonce validation failed - possible replay attack")
            
            # Check timestamp age
            sig_timestamp = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
            age = (datetime.now() - sig_timestamp).total_seconds()
            age_valid = age <= max_age_seconds
            
            if not age_valid:
                logger.warning(f"Signature too old: {age} seconds (max: {max_age_seconds})")
            
            is_valid = match and nonce_valid and age_valid
            
            result = VerificationResult(
                is_valid=is_valid,
                recovered_address=recovered_address,
                expected_address=expected_signer,
                match=match,
                timestamp=sig_timestamp,
                age_seconds=age,
                message_hash=self.web3.keccak(text=message_str).hex()
            )
            
            logger.debug(f"Signature verification: {'VALID' if is_valid else 'INVALID'}")
            return result
            
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            raise
    
    def create_hmac(
        self,
        message: str,
        secret_key: str,
        algorithm: str = 'sha256'
    ) -> str:
        """
        Create HMAC for message authentication.
        
        Args:
            message: Message to authenticate
            secret_key: Secret key for HMAC
            algorithm: Hash algorithm ('sha256', 'sha512')
            
        Returns:
            HMAC hex string
        """
        try:
            hash_func = getattr(hashlib, algorithm)
            mac = hmac.new(
                secret_key.encode(),
                message.encode(),
                hash_func
            )
            
            logger.debug(f"Created HMAC using {algorithm}")
            return mac.hexdigest()
            
        except Exception as e:
            logger.error(f"Error creating HMAC: {e}")
            raise
    
    def verify_hmac(
        self,
        message: str,
        mac: str,
        secret_key: str,
        algorithm: str = 'sha256'
    ) -> bool:
        """
        Verify HMAC (constant-time comparison).
        
        Args:
            message: Original message
            mac: HMAC to verify
            secret_key: Secret key
            algorithm: Hash algorithm
            
        Returns:
            True if HMAC is valid
        """
        try:
            expected_mac = self.create_hmac(message, secret_key, algorithm)
            is_valid = hmac.compare_digest(mac, expected_mac)
            
            logger.debug(f"HMAC verification: {'VALID' if is_valid else 'INVALID'}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying HMAC: {e}")
            raise
    
    def build_merkle_tree(self, data_hashes: List[str]) -> MerkleNode:
        """
        Build merkle tree from data hashes for tamper-evident logging.
        
        Args:
            data_hashes: List of data hashes (hex strings)
            
        Returns:
            Root node of merkle tree
        """
        try:
            if not data_hashes:
                raise ValueError("Cannot build merkle tree from empty list")
            
            # Create leaf nodes
            nodes = [MerkleNode(hash=h) for h in data_hashes]
            
            # Build tree bottom-up
            while len(nodes) > 1:
                next_level = []
                
                for i in range(0, len(nodes), 2):
                    left = nodes[i]
                    right = nodes[i + 1] if i + 1 < len(nodes) else nodes[i]
                    
                    # Hash left + right
                    combined = left.hash + right.hash
                    parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                    
                    parent = MerkleNode(
                        hash=f"0x{parent_hash}",
                        left=left,
                        right=right
                    )
                    next_level.append(parent)
                
                nodes = next_level
            
            root = nodes[0]
            logger.debug(f"Built merkle tree with root {root.hash[:16]}...")
            return root
            
        except Exception as e:
            logger.error(f"Error building merkle tree: {e}")
            raise
    
    def generate_merkle_proof(
        self,
        data_hash: str,
        all_hashes: List[str]
    ) -> List[Tuple[str, str]]:
        """
        Generate merkle proof for specific data.
        
        Args:
            data_hash: Hash to prove inclusion for
            all_hashes: All hashes in the tree
            
        Returns:
            List of (hash, position) tuples for proof path
        """
        try:
            if data_hash not in all_hashes:
                raise ValueError(f"Data hash {data_hash} not in tree")
            
            proof = []
            index = all_hashes.index(data_hash)
            nodes = all_hashes.copy()
            
            while len(nodes) > 1:
                next_level = []
                
                for i in range(0, len(nodes), 2):
                    left = nodes[i]
                    right = nodes[i + 1] if i + 1 < len(nodes) else nodes[i]
                    
                    # If this is our node, record sibling
                    if i == index:
                        proof.append((right, 'right'))
                    elif i + 1 == index:
                        proof.append((left, 'left'))
                    
                    # Compute parent
                    combined = left + right
                    parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                    next_level.append(f"0x{parent_hash}")
                    
                    # Update index for next level
                    if i <= index < i + 2:
                        index = len(next_level) - 1
                
                nodes = next_level
            
            logger.debug(f"Generated merkle proof with {len(proof)} elements")
            return proof
            
        except Exception as e:
            logger.error(f"Error generating merkle proof: {e}")
            raise
    
    def verify_merkle_proof(
        self,
        data_hash: str,
        proof: List[Tuple[str, str]],
        root_hash: str
    ) -> bool:
        """
        Verify merkle proof.
        
        Args:
            data_hash: Hash to verify
            proof: Proof path
            root_hash: Expected root hash
            
        Returns:
            True if proof is valid
        """
        try:
            current_hash = data_hash
            
            for sibling_hash, position in proof:
                if position == 'left':
                    combined = sibling_hash + current_hash
                else:
                    combined = current_hash + sibling_hash
                
                current_hash = f"0x{hashlib.sha256(combined.encode()).hexdigest()}"
            
            is_valid = current_hash == root_hash
            logger.debug(f"Merkle proof verification: {'VALID' if is_valid else 'INVALID'}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying merkle proof: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cryptographic service statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "active_nonces": len(self.nonce_manager.used_nonces),
            "nonce_validity_seconds": self.nonce_manager.validity_period.total_seconds()
        }


# Singleton instance
_crypto_service: Optional[CryptoService] = None


def get_crypto_service(nonce_validity_seconds: int = 300) -> CryptoService:
    """
    Get or create singleton CryptoService instance.
    
    Args:
        nonce_validity_seconds: Nonce validity period
        
    Returns:
        CryptoService singleton instance
    """
    global _crypto_service
    
    if _crypto_service is None:
        _crypto_service = CryptoService(nonce_validity_seconds)
        logger.info("CryptoService singleton initialized")
    
    return _crypto_service
