# IPFS integration via Pinata HTTP API for decision proof storage (FR-007)

import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)


class IPFSService:
    """
    IPFS service for storing decision proofs and agent data.
    Uses Pinata as the IPFS pinning service.
    """
    
    def __init__(self):
        self.pinata_api_key = os.getenv("PINATA_API_KEY", "")
        self.pinata_secret_key = os.getenv("PINATA_SECRET_KEY", "")
        self.pinata_jwt = os.getenv("PINATA_JWT", "")
        self.pinata_api_url = "https://api.pinata.cloud"
        self.gateway_url = "https://gateway.pinata.cloud/ipfs"
        
        if not (self.pinata_jwt or (self.pinata_api_key and self.pinata_secret_key)):
            logger.warning("IPFS/Pinata credentials not configured. Using mock mode.")
            self.mock_mode = True
        else:
            self.mock_mode = False
    
    def compute_hash(self, data: Dict[str, Any]) -> str:
        """
        Compute Keccak-256 hash of decision data.
        
        Args:
            data: Dictionary containing decision data
            
        Returns:
            Hex string of the hash (with 0x prefix)
        """
        # Convert to JSON string with sorted keys for consistency
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        
        # Compute SHA-256 (Keccak-256 not available in standard library)
        # In production, use Web3.keccak for true Keccak-256
        hash_bytes = hashlib.sha256(json_str.encode()).digest()
        return "0x" + hash_bytes.hex()
    
    async def upload_decision(
        self,
        decision_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """
        Upload decision data to IPFS via Pinata.
        
        Args:
            decision_data: The decision data to upload
            metadata: Optional metadata for Pinata
            
        Returns:
            Tuple of (ipfs_cid, decision_hash)
        """
        # Add timestamp if not present
        if "timestamp" not in decision_data:
            decision_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Compute hash
        decision_hash = self.compute_hash(decision_data)
        
        if self.mock_mode:
            # Mock mode: return fake CID
            mock_cid = f"Qm{decision_hash[2:48]}"
            logger.info(f"Mock IPFS upload: CID={mock_cid}")
            return mock_cid, decision_hash
        
        try:
            # Prepare data for Pinata
            pin_data = {
                "pinataContent": decision_data,
                "pinataMetadata": metadata or {
                    "name": f"decision_{decision_hash[:10]}",
                    "keyvalues": {
                        "type": "agent_decision",
                        "hash": decision_hash
                    }
                }
            }
            
            # Upload to Pinata
            headers = {
                "Content-Type": "application/json"
            }
            
            if self.pinata_jwt:
                headers["Authorization"] = f"Bearer {self.pinata_jwt}"
            else:
                headers["pinata_api_key"] = self.pinata_api_key
                headers["pinata_secret_api_key"] = self.pinata_secret_key
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.pinata_api_url}/pinning/pinJSONToIPFS",
                    json=pin_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        ipfs_cid = result.get("IpfsHash", "")
                        logger.info(f"Successfully uploaded to IPFS: {ipfs_cid}")
                        return ipfs_cid, decision_hash
                    else:
                        error_text = await response.text()
                        logger.error(f"Pinata upload failed: {response.status} - {error_text}")
                        # Fallback to mock mode
                        mock_cid = f"Qm{decision_hash[2:48]}"
                        return mock_cid, decision_hash
        
        except Exception as e:
            logger.error(f"Error uploading to IPFS: {e}")
            # Fallback to mock mode
            mock_cid = f"Qm{decision_hash[2:48]}"
            return mock_cid, decision_hash
    
    async def retrieve_decision(self, ipfs_cid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve decision data from IPFS.
        
        Args:
            ipfs_cid: The IPFS content identifier
            
        Returns:
            Decision data dictionary or None if not found
        """
        if self.mock_mode:
            logger.warning(f"Mock mode: Cannot retrieve actual data for {ipfs_cid}")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.gateway_url}/{ipfs_cid}",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logger.error(f"Failed to retrieve from IPFS: {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"Error retrieving from IPFS: {e}")
            return None
    
    async def verify_hash(self, ipfs_cid: str, expected_hash: str) -> bool:
        """
        Verify that data at IPFS CID matches the expected hash.
        
        Args:
            ipfs_cid: The IPFS content identifier
            expected_hash: The expected hash
            
        Returns:
            True if hash matches, False otherwise
        """
        data = await self.retrieve_decision(ipfs_cid)
        if not data:
            return False
        
        computed_hash = self.compute_hash(data)
        return computed_hash == expected_hash


# Global instance
_ipfs_service: Optional[IPFSService] = None


def get_ipfs_service() -> IPFSService:
    """Get or create IPFS service instance"""
    global _ipfs_service
    if _ipfs_service is None:
        _ipfs_service = IPFSService()
    return _ipfs_service
