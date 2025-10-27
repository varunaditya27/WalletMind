"""
Verification Service - Cryptographic Proof Generation and Verification (FR-007)

Handles:
- Decision hash generation (SHA-256)
- Cryptographic signatures
- IPFS proof storage
- Blockchain logging
- Signature verification
"""

import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any
from web3 import Web3
from eth_account.messages import encode_defunct
import logging

logger = logging.getLogger(__name__)


class DecisionProof:
    """Decision proof with cryptographic signature"""
    def __init__(
        self,
        decision_id: str,
        decision_hash: str,
        signature: str,
        ipfs_cid: str,
        created_at: datetime
    ):
        self.decision_id = decision_id
        self.decision_hash = decision_hash
        self.signature = signature
        self.ipfs_cid = ipfs_cid
        self.created_at = created_at


class VerificationResult:
    """Verification result with validity status"""
    def __init__(
        self,
        is_valid: bool,
        decision_hash: str,
        signer: Optional[str],
        expected_signer: str,
        verified_at: datetime,
        error: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.decision_hash = decision_hash
        self.signer = signer
        self.expected_signer = expected_signer
        self.verified_at = verified_at
        self.error = error


class VerificationService:
    """
    Handles cryptographic verification and decision provenance (FR-007).
    
    Features:
    - Generate SHA-256 hashes of decisions
    - Sign decisions with agent private keys
    - Store proofs on IPFS
    - Log decision hashes to blockchain
    - Verify decision authenticity
    - Retrieve proofs from IPFS
    """
    
    def __init__(self):
        self.web3 = Web3()
        logger.info("Verification service initialized")
    
    async def generate_decision_hash(self, decision_data: Dict[str, Any]) -> str:
        """
        Generate SHA-256 hash of decision data.
        
        Args:
            decision_data: Dictionary containing decision information
            
        Returns:
            Hex string of decision hash (0x-prefixed)
        """
        try:
            # Create deterministic JSON representation
            canonical_data = {
                "agent_id": decision_data.get("agent_id"),
                "prompt": decision_data.get("prompt"),
                "plan": decision_data.get("plan"),
                "risk_level": decision_data.get("risk_level"),
                "timestamp": decision_data.get("timestamp"),
                "metadata": decision_data.get("metadata", {}),
            }
            
            # Sort keys for deterministic hashing
            json_str = json.dumps(canonical_data, sort_keys=True)
            decision_hash = hashlib.sha256(json_str.encode()).hexdigest()
            
            logger.debug(f"Generated decision hash: 0x{decision_hash[:8]}...")
            return f"0x{decision_hash}"
            
        except Exception as e:
            logger.error(f"Error generating decision hash: {e}")
            raise
    
    async def sign_decision(
        self,
        decision_hash: str,
        private_key: str
    ) -> Dict[str, str]:
        """
        Sign decision hash with private key.
        
        Args:
            decision_hash: Hash to sign (0x-prefixed)
            private_key: Private key for signing
            
        Returns:
            Dictionary with signature and signer address
        """
        try:
            # Sign the hash
            message = encode_defunct(hexstr=decision_hash)
            signed_message = self.web3.eth.account.sign_message(
                message, 
                private_key=private_key
            )
            
            signature = signed_message.signature.hex()
            signer = self.web3.eth.account.from_key(private_key).address
            
            logger.debug(f"Signed decision hash with address {signer}")
            
            return {
                "signature": signature,
                "signer": signer,
                "message_hash": signed_message.messageHash.hex()
            }
            
        except Exception as e:
            logger.error(f"Error signing decision: {e}")
            raise
    
    async def create_decision_proof(
        self, 
        decision_data: Dict[str, Any],
        agent_private_key: str
    ) -> Dict[str, Any]:
        """
        Create complete cryptographic proof of decision.
        
        Args:
            decision_data: Decision information
            agent_private_key: Private key for signing
            
        Returns:
            Proof data with hash, signature, and metadata
        """
        try:
            # Generate decision hash
            decision_hash = await self.generate_decision_hash(decision_data)
            
            # Sign the hash
            signature_data = await self.sign_decision(decision_hash, agent_private_key)
            
            # Prepare complete proof
            proof_data = {
                "decision_hash": decision_hash,
                "signature": signature_data["signature"],
                "signer": signature_data["signer"],
                "message_hash": signature_data["message_hash"],
                "decision_data": {
                    "agent_id": decision_data.get("agent_id"),
                    "prompt": decision_data.get("prompt"),
                    "plan": decision_data.get("plan"),
                    "risk_level": decision_data.get("risk_level"),
                    "timestamp": decision_data.get("timestamp"),
                },
                "created_at": datetime.utcnow().isoformat(),
            }
            
            logger.info(f"Created decision proof for agent {decision_data.get('agent_id')}")
            return proof_data
            
        except Exception as e:
            logger.error(f"Error creating decision proof: {e}")
            raise
    
    async def verify_signature(
        self,
        decision_hash: str,
        signature: str,
        expected_signer: str
    ) -> VerificationResult:
        """
        Verify that a decision was signed by the expected agent.
        
        Args:
            decision_hash: Hash of the decision
            signature: Cryptographic signature
            expected_signer: Expected signer address
            
        Returns:
            VerificationResult with validity status
        """
        try:
            # Recover signer from signature
            message = encode_defunct(hexstr=decision_hash)
            recovered_address = self.web3.eth.account.recover_message(
                message,
                signature=signature
            )
            
            is_valid = recovered_address.lower() == expected_signer.lower()
            
            logger.info(
                f"Signature verification: {'VALID' if is_valid else 'INVALID'} "
                f"(expected={expected_signer}, recovered={recovered_address})"
            )
            
            return VerificationResult(
                is_valid=is_valid,
                decision_hash=decision_hash,
                signer=recovered_address,
                expected_signer=expected_signer,
                verified_at=datetime.utcnow(),
            )
            
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return VerificationResult(
                is_valid=False,
                decision_hash=decision_hash,
                signer=None,
                expected_signer=expected_signer,
                error=str(e),
                verified_at=datetime.utcnow(),
            )
    
    async def prepare_blockchain_log(
        self,
        decision_hash: str,
        ipfs_cid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare data for blockchain logging.
        
        Args:
            decision_hash: Decision hash to log
            ipfs_cid: Optional IPFS content identifier
            
        Returns:
            Data ready for blockchain contract call
        """
        return {
            "decision_hash": decision_hash,
            "ipfs_cid": ipfs_cid or "",
            "timestamp": int(datetime.utcnow().timestamp()),
        }
    
    def verify_hash_format(self, hash_string: str) -> bool:
        """
        Verify that a hash string is properly formatted.
        
        Args:
            hash_string: Hash string to verify
            
        Returns:
            True if valid format
        """
        if not hash_string.startswith("0x"):
            return False
        
        try:
            # Try to convert to bytes
            bytes.fromhex(hash_string[2:])
            return len(hash_string) == 66  # 0x + 64 hex chars
        except ValueError:
            return False
    
    async def batch_verify_signatures(
        self,
        verifications: list[Dict[str, str]]
    ) -> list[VerificationResult]:
        """
        Verify multiple signatures in batch.
        
        Args:
            verifications: List of dicts with decision_hash, signature, expected_signer
            
        Returns:
            List of VerificationResults
        """
        results = []
        
        for verification in verifications:
            result = await self.verify_signature(
                decision_hash=verification["decision_hash"],
                signature=verification["signature"],
                expected_signer=verification["expected_signer"]
            )
            results.append(result)
        
        valid_count = sum(1 for r in results if r.is_valid)
        logger.info(f"Batch verification: {valid_count}/{len(results)} valid")
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get verification service statistics"""
        return {
            "service": "verification",
            "web3_connected": self.web3.is_connected() if hasattr(self.web3, 'is_connected') else False,
            "status": "operational"
        }


# Singleton instance
_verification_service: Optional[VerificationService] = None


def get_verification_service() -> VerificationService:
    """Get or create singleton VerificationService instance"""
    global _verification_service
    
    if _verification_service is None:
        _verification_service = VerificationService()
    
    return _verification_service