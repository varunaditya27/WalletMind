# Verification and Audit Trail API endpoints implementing FR-008, FR-009
# Handles on-chain audit trails and transparency

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timedelta
import logging

from app.models.decision import (
    AuditTrailRequest,
    AuditTrailResponse,
    AuditEntry
)
from app.database.service import DatabaseService

router = APIRouter(prefix="/api/verification", tags=["verification"])
logger = logging.getLogger(__name__)

# Service instances
_db_service: DatabaseService = None

def get_db_service() -> DatabaseService:
    """Get or create DatabaseService instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


@router.post("/audit-trail", response_model=AuditTrailResponse, summary="Get audit trail (FR-008)")
async def get_audit_trail(request: AuditTrailRequest):
    """
    Get complete audit trail for a wallet.
    
    Returns chronological record of:
    - All decisions made by agents
    - All transactions executed
    - Decision → execution linkages
    - Timestamps and verification data
    
    This provides complete transparency of agent financial activity.
    
    Implements FR-008: On-Chain Audit Trail
    """
    try:
        db_service = get_db_service()
        
        # Query database for audit entries
        entries = await db_service.get_audit_trail(
            wallet_address=request.wallet_address,
            from_date=request.from_date,
            to_date=request.to_date,
            include_decisions=request.include_decisions,
            include_transactions=request.include_transactions,
            limit=request.limit
        )
        
        logger.info(f"Retrieved {len(entries)} audit entries for wallet {request.wallet_address}")
        
        return AuditTrailResponse(
            wallet_address=request.wallet_address,
            entries=entries,
            total=len(entries),
            from_date=request.from_date,
            to_date=request.to_date
        )
    except Exception as e:
        logger.error(f"Error getting audit trail: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit trail: {str(e)}")


@router.get("/wallet/{wallet_address}/timeline", summary="Get wallet timeline")
async def get_wallet_timeline(wallet_address: str, limit: int = 50):
    """
    Get chronological timeline of all wallet activities.
    
    Useful for dashboard visualization of agent behavior.
    """
    try:
        db_service = get_db_service()
        
        # Build timeline from decisions and transactions
        timeline = await db_service.get_wallet_timeline(wallet_address, limit=limit)
        
        logger.info(f"Retrieved timeline with {len(timeline)} events for wallet {wallet_address}")
        
        return {
            "wallet_address": wallet_address,
            "timeline": timeline,
            "total_events": len(timeline)
        }
    except Exception as e:
        logger.error(f"Error getting wallet timeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get wallet timeline: {str(e)}")


@router.get("/agent/{agent_type}/activity", summary="Get agent activity log")
async def get_agent_activity(agent_type: str, limit: int = 100):
    """
    Get activity log for a specific agent type across all wallets.
    
    Helps track agent behavior patterns and performance.
    """
    try:
        db_service = get_db_service()
        
        # Query agent-specific activity
        activities = await db_service.get_agent_activity(agent_type, limit=limit)
        
        logger.info(f"Retrieved {len(activities)} activities for agent type {agent_type}")
        
        return {
            "agent_type": agent_type,
            "activities": activities,
            "total": len(activities)
        }
    except Exception as e:
        logger.error(f"Error getting agent activity: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent activity: {str(e)}")


@router.get("/statistics/autonomy", summary="Get autonomy statistics")
async def get_autonomy_statistics():
    """
    Get system-wide statistics on autonomous operations.
    
    Returns:
    - Total autonomous decisions
    - Decision → execution success rate
    - Average decision-to-execution time
    - Verification success rate
    
    Proves the system's autonomous nature.
    """
    try:
        db_service = get_db_service()
        
        # Calculate autonomy statistics
        stats = await db_service.get_autonomy_statistics()
        
        total_decisions = stats.get("total_decisions", 0)
        total_executions = stats.get("total_executions", 0)
        autonomy_rate = stats.get("autonomy_rate", 0.0)
        average_decision_time = stats.get("average_decision_time", 0.0)
        verification_success_rate = stats.get("verification_success_rate", 0.0)
        
        logger.info(f"Retrieved autonomy statistics: {total_decisions} decisions, {autonomy_rate}% autonomy rate")
        
        return {
            "total_decisions": total_decisions,
            "total_executions": total_executions,
            "autonomy_rate": autonomy_rate,
            "average_decision_time": average_decision_time,
            "verification_success_rate": verification_success_rate
        }
    except Exception as e:
        logger.error(f"Error getting autonomy statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get autonomy statistics: {str(e)}")


@router.post("/validate-chronology", summary="Validate decision chronology")
async def validate_chronology(decision_hash: str, transaction_hash: str):
    """
    Validate that a decision was logged before its execution.
    
    Critical for proving autonomous operation.
    """
    try:
        db_service = get_db_service()
        
        # Get decision and transaction timestamps
        decision = await db_service.get_decision_by_hash(decision_hash)
        transaction = await db_service.get_transaction_by_hash(transaction_hash)
        
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        decision_time = decision.get("logged_at")
        execution_time = transaction.get("timestamp")
        
        # Validate chronology
        is_valid = decision_time < execution_time if decision_time and execution_time else False
        time_delta = (execution_time - decision_time).total_seconds() if is_valid else 0
        
        logger.info(f"Chronology validation: decision {decision_hash} vs tx {transaction_hash} = {is_valid}")
        
        return {
            "valid": is_valid,
            "decision_hash": decision_hash,
            "transaction_hash": transaction_hash,
            "decision_time": decision_time.isoformat() if decision_time else None,
            "execution_time": execution_time.isoformat() if execution_time else None,
            "time_delta_seconds": time_delta
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating chronology: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate chronology: {str(e)}")


@router.get("/integrity-check/{wallet_address}", summary="Perform integrity check")
async def perform_integrity_check(wallet_address: str):
    """
    Perform comprehensive integrity check on a wallet's decision history.
    
    Verifies:
    - All transactions have logged decisions
    - No timestamp inconsistencies
    - All IPFS data is accessible
    - All blockchain proofs are valid
    """
    try:
        db_service = get_db_service()
        
        # Comprehensive integrity check
        results = await db_service.perform_integrity_check(wallet_address)
        
        checks_performed = results.get("checks_performed", 0)
        checks_passed = results.get("checks_passed", 0)
        checks_failed = results.get("checks_failed", 0)
        issues = results.get("issues", [])
        passed = checks_failed == 0
        
        logger.info(f"Integrity check for {wallet_address}: {checks_passed}/{checks_performed} passed")
        
        return {
            "wallet_address": wallet_address,
            "passed": passed,
            "checks_performed": checks_performed,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "issues": issues
        }
    except Exception as e:
        logger.error(f"Error performing integrity check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to perform integrity check: {str(e)}")


@router.get("/export/{wallet_address}", summary="Export verification data")
async def export_verification_data(wallet_address: str, format: str = "json"):
    """
    Export complete verification data for external auditing.
    
    Supports formats: json, csv
    """
    try:
        db_service = get_db_service()
        
        # Generate export
        export_data = await db_service.export_verification_data(wallet_address, format=format)
        
        # In production, would upload to S3/IPFS and return URL
        export_url = f"https://api.walletmind.com/exports/{wallet_address}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        
        logger.info(f"Generated verification data export for {wallet_address} in {format} format")
        
        return {
            "wallet_address": wallet_address,
            "export_url": export_url,
            "format": format,
            "data": export_data  # Include data in response for now
        }
    except Exception as e:
        logger.error(f"Error exporting verification data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export verification data: {str(e)}")
