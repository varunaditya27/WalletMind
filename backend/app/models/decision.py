# Decision and verification-related Pydantic models
# Implements FR-007, FR-008, FR-009

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DecisionStatus(str, Enum):
    """Decision status"""
    LOGGED = "logged"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    

class LogDecisionRequest(BaseModel):
    """Request to log decision before execution (FR-007)"""
    wallet_address: str = Field(..., description="Wallet making the decision")
    decision_content: str = Field(..., description="Full decision rationale")
    decision_context: Dict[str, Any] = Field(..., description="Decision context and parameters")
    timestamp: datetime = Field(..., description="Decision timestamp")
    agent_type: str = Field(..., description="Type of agent making decision")
    

class DecisionLogResponse(BaseModel):
    """Response after logging decision (FR-007)"""
    decision_id: str = Field(..., description="Unique decision identifier")
    decision_hash: str = Field(..., description="Cryptographic hash of decision")
    ipfs_cid: str = Field(..., description="IPFS CID where full decision is stored")
    blockchain_tx: Optional[str] = Field(default=None, description="Blockchain transaction hash")
    logged_at: datetime = Field(..., description="When decision was logged")
    

class DecisionInfo(BaseModel):
    """Complete decision information (FR-008)"""
    decision_id: str = Field(..., description="Unique decision identifier")
    decision_hash: str = Field(..., description="Decision hash")
    wallet_address: str = Field(..., description="Wallet address")
    decision_content: str = Field(..., description="Decision rationale")
    decision_context: Dict[str, Any] = Field(..., description="Decision context")
    agent_type: str = Field(..., description="Agent type")
    status: DecisionStatus = Field(..., description="Current status")
    logged_at: datetime = Field(..., description="Logging timestamp")
    executed_at: Optional[datetime] = Field(default=None, description="Execution timestamp")
    ipfs_cid: str = Field(..., description="IPFS storage CID")
    blockchain_tx: Optional[str] = Field(default=None, description="Blockchain transaction")
    execution_tx: Optional[str] = Field(default=None, description="Execution transaction hash")
    

class VerificationRequest(BaseModel):
    """Request to verify decision authenticity (FR-007)"""
    decision_hash: str = Field(..., description="Decision hash to verify")
    transaction_hash: Optional[str] = Field(default=None, description="Transaction hash to verify against")
    

class VerificationResult(BaseModel):
    """Verification result (FR-007)"""
    is_valid: bool = Field(..., description="Whether verification passed")
    decision_hash: str = Field(..., description="Verified decision hash")
    decision_timestamp: datetime = Field(..., description="When decision was logged")
    execution_timestamp: Optional[datetime] = Field(default=None, description="When executed")
    chronology_valid: bool = Field(..., description="Decision logged before execution")
    hash_match: bool = Field(..., description="Hash matches stored content")
    signature_valid: bool = Field(..., description="Cryptographic signature valid")
    ipfs_cid: str = Field(..., description="IPFS CID for full data")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional verification details")
    

class AuditTrailRequest(BaseModel):
    """Request audit trail for wallet (FR-008)"""
    wallet_address: str = Field(..., description="Wallet address")
    from_date: Optional[datetime] = Field(default=None, description="Start date")
    to_date: Optional[datetime] = Field(default=None, description="End date")
    include_decisions: bool = Field(default=True, description="Include decision logs")
    include_transactions: bool = Field(default=True, description="Include transactions")
    limit: int = Field(default=100, ge=1, le=1000, description="Number of results")
    

class AuditEntry(BaseModel):
    """Single audit trail entry"""
    entry_id: str = Field(..., description="Entry identifier")
    timestamp: datetime = Field(..., description="Entry timestamp")
    entry_type: str = Field(..., description="Type of entry (decision/transaction)")
    decision_hash: Optional[str] = Field(default=None, description="Decision hash if applicable")
    transaction_hash: Optional[str] = Field(default=None, description="Transaction hash if applicable")
    action: str = Field(..., description="Action performed")
    agent_type: Optional[str] = Field(default=None, description="Agent type")
    status: str = Field(..., description="Entry status")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    

class AuditTrailResponse(BaseModel):
    """Complete audit trail (FR-008)"""
    wallet_address: str = Field(..., description="Wallet address")
    entries: List[AuditEntry] = Field(..., description="Audit entries")
    total: int = Field(..., description="Total number of entries")
    from_date: Optional[datetime] = Field(default=None, description="Start date")
    to_date: Optional[datetime] = Field(default=None, description="End date")
    

class ProvenanceChain(BaseModel):
    """Provenance chain for a transaction (FR-007)"""
    transaction_hash: str = Field(..., description="Transaction hash")
    decision_hash: str = Field(..., description="Associated decision hash")
    decision_logged_at: datetime = Field(..., description="Decision log time")
    transaction_executed_at: datetime = Field(..., description="Transaction execution time")
    time_delta: float = Field(..., description="Time between decision and execution (seconds)")
    ipfs_proof: str = Field(..., description="IPFS CID with full proof")
    blockchain_proof: str = Field(..., description="Blockchain transaction for decision log")
    is_autonomous: bool = Field(..., description="Verified as autonomous decision")
    verification_url: str = Field(..., description="URL to verify independently")
