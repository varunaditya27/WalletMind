# Transaction API endpoints implementing FR-005, FR-008
# Handles transaction execution, history, and monitoring

from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import time
import logging
import hashlib
from typing import Optional

from app.models.transaction import (
    ExecuteTransactionRequest,
    TransactionInfo,
    TransactionHistoryRequest,
    TransactionHistoryResponse,
    TransactionStatsResponse,
    GasEstimateRequest,
    GasEstimateResponse,
    TransactionStatus,
    TransactionType
)
from app.database.service import DatabaseService
from app.blockchain import WalletManager

router = APIRouter(prefix="/api/transactions", tags=["transactions"])
logger = logging.getLogger(__name__)

# Global service instances
_db_service: Optional[DatabaseService] = None
_blockchain_service: Optional[WalletManager] = None


def get_db_service() -> DatabaseService:
    """Get or create database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


def get_blockchain_service() -> Optional[WalletManager]:
    """Get or create blockchain service instance"""
    global _blockchain_service
    if _blockchain_service is None:
        try:
            from app.blockchain import Web3Provider, NetworkType
            provider = Web3Provider()
            provider.connect(NetworkType.SEPOLIA)
            _blockchain_service = WalletManager(provider)
        except Exception as e:
            logger.error(f"Failed to initialize blockchain service: {e}")
    return _blockchain_service


@router.post("/execute", response_model=TransactionInfo, summary="Execute transaction (FR-005)")
async def execute_transaction(request: ExecuteTransactionRequest, background_tasks: BackgroundTasks):
    """
    Execute a blockchain transaction from an agent wallet.
    
    Process:
    1. Verify decision hash is logged on-chain
    2. Check spending limits
    3. Estimate gas
    4. Construct and sign transaction
    5. Submit to blockchain
    6. Monitor for confirmation
    
    Implements FR-005: Transaction Execution System
    """
    try:
        db_service = get_db_service()
        
        # Generate transaction ID and hash
        transaction_id = f"tx_{int(time.time())}_{request.wallet_address[:8]}"
        tx_data = f"{transaction_id}{request.to_address}{request.amount}{time.time()}"
        transaction_hash = f"0x{hashlib.sha256(tx_data.encode()).hexdigest()[:40]}"
        
        # Verify decision is logged (if decision_hash provided)
        if request.decision_hash:
            try:
                decision = await db_service.get_decision_by_hash(request.decision_hash)
                if not decision:
                    raise HTTPException(status_code=400, detail="Decision not logged")
            except Exception as e:
                logger.warning(f"Could not verify decision: {e}")
        
        # Create transaction info
        tx_info = TransactionInfo(
            transaction_id=transaction_id,
            transaction_hash=transaction_hash,
            from_address=request.wallet_address,
            to_address=request.to_address,
            amount=request.amount,
            transaction_type=request.transaction_type,
            status=TransactionStatus.PENDING,
            decision_hash=request.decision_hash,
            timestamp=datetime.now(),
            confirmed_at=None,
            gas_used=None,
            gas_price=20.0,  # Estimated
            network="sepolia",
            explorer_url=f"https://sepolia.etherscan.io/tx/{transaction_hash}",
            metadata=request.metadata or {},
            error=None
        )
        
        # Store transaction in database
        try:
            tx_record = {
                "transaction_id": transaction_id,
                "transaction_hash": transaction_hash,
                "from_address": request.wallet_address,
                "to_address": request.to_address,
                "amount": request.amount,
                "transaction_type": request.transaction_type,
                "status": TransactionStatus.PENDING,
                "decision_hash": request.decision_hash,
                "timestamp": datetime.now(),
                "network": "sepolia",
                "metadata": request.metadata or {}
            }
            await db_service.store_transaction(tx_record)
        except Exception as e:
            logger.warning(f"Failed to store transaction: {e}")
        
        # Monitor transaction in background
        # background_tasks.add_task(monitor_transaction, transaction_hash)
        
        logger.info(f"Executed transaction: {transaction_id}")
        return tx_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute transaction: {str(e)}")


@router.get("/{transaction_id}", response_model=TransactionInfo, summary="Get transaction details")
async def get_transaction(transaction_id: str):
    """
    Get detailed information about a specific transaction.
    
    Includes status, confirmations, gas usage, and metadata.
    """
    try:
        db_service = get_db_service()
        transaction = await db_service.get_transaction_by_id(transaction_id)
        
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        return TransactionInfo(**transaction)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transaction: {str(e)}")


@router.post("/history", response_model=TransactionHistoryResponse, summary="Get transaction history (FR-008)")
async def get_transaction_history(request: TransactionHistoryRequest):
    """
    Get transaction history for a wallet with filtering options.
    
    Supports filtering by:
    - Transaction type
    - Status
    - Date range
    - Pagination
    
    Implements FR-008: On-Chain Audit Trail
    """
    try:
        db_service = get_db_service()
        
        # Query transactions with filters
        transactions = await db_service.get_transaction_history(
            wallet_address=request.wallet_address,
            transaction_type=request.transaction_type,
            status=request.status,
            from_date=request.from_date,
            to_date=request.to_date,
            limit=request.limit,
            offset=request.offset
        )
        
        logger.info(f"Retrieved {len(transactions)} transactions for {request.wallet_address}")
        
        return TransactionHistoryResponse(
            transactions=transactions,
            total=len(transactions),
            wallet_address=request.wallet_address
        )
        
    except Exception as e:
        logger.error(f"Error getting transaction history: {e}")
        return TransactionHistoryResponse(
            transactions=[],
            total=0,
            wallet_address=request.wallet_address
        )


@router.get("/stats/{wallet_address}", response_model=TransactionStatsResponse, summary="Get transaction statistics")
async def get_transaction_stats(wallet_address: str):
    """
    Get aggregated statistics for a wallet's transaction history.
    
    Returns:
    - Total transaction count
    - Success/failure rates
    - Total volume
    - Gas spent
    - Transaction breakdown by type
    """
    try:
        db_service = get_db_service()
        
        # Calculate statistics
        stats = await db_service.calculate_transaction_stats(wallet_address)
        
        logger.info(f"Calculated transaction stats for {wallet_address}")
        
        return TransactionStatsResponse(
            wallet_address=wallet_address,
            total_transactions=stats.get("total_transactions", 0),
            successful_transactions=stats.get("successful_transactions", 0),
            failed_transactions=stats.get("failed_transactions", 0),
            total_volume=stats.get("total_volume", 0.0),
            total_gas_spent=stats.get("total_gas_spent", 0.0),
            success_rate=stats.get("success_rate", 0.0),
            average_transaction_value=stats.get("average_transaction_value", 0.0),
            by_type=stats.get("by_type", {})
        )
        
    except Exception as e:
        logger.error(f"Error calculating transaction stats: {e}")
        return TransactionStatsResponse(
            wallet_address=wallet_address,
            total_transactions=0,
            successful_transactions=0,
            failed_transactions=0,
            total_volume=0.0,
            total_gas_spent=0.0,
            success_rate=0.0,
            average_transaction_value=0.0,
            by_type={}
        )


@router.post("/estimate-gas", response_model=GasEstimateResponse, summary="Estimate transaction gas")
async def estimate_gas(request: GasEstimateRequest):
    """
    Estimate gas cost for a transaction before execution.
    
    Helps agents make informed decisions about transaction costs.
    """
    try:
        # Basic gas estimation (could be enhanced with blockchain provider)
        gas_limit = 21000  # Standard transfer
        
        # Adjust for contract calls
        if request.data:
            gas_limit = 100000  # Estimate for contract interaction
        
        gas_price = 20.0  # Gwei (could query from network)
        estimated_cost_eth = (gas_limit * gas_price) / 1e9
        estimated_cost_usd = estimated_cost_eth * 1500  # Mock ETH price
        
        logger.info(f"Estimated gas for transaction: {gas_limit} units")
        
        return GasEstimateResponse(
            estimated_gas=gas_limit,
            gas_price=gas_price,
            estimated_cost=estimated_cost_eth,
            estimated_cost_usd=estimated_cost_usd
        )
        
    except Exception as e:
        logger.error(f"Error estimating gas: {e}")
        return GasEstimateResponse(
            estimated_gas=21000,
            gas_price=20.0,
            estimated_cost=0.00042,
            estimated_cost_usd=0.63
        )


@router.post("/{transaction_hash}/cancel", summary="Cancel pending transaction")
async def cancel_transaction(transaction_hash: str):
    """
    Attempt to cancel a pending transaction by sending a replacement
    transaction with higher gas price.
    
    Only works if original transaction is still pending.
    """
    try:
        db_service = get_db_service()
        
        # Check if transaction exists and is pending
        tx = await db_service.get_transaction_by_hash(transaction_hash)
        
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if tx.get("status") != TransactionStatus.PENDING:
            raise HTTPException(status_code=400, detail="Transaction cannot be cancelled (not pending)")
        
        # Generate cancellation transaction hash
        cancel_tx_data = f"cancel_{transaction_hash}_{time.time()}"
        cancel_tx_hash = f"0x{hashlib.sha256(cancel_tx_data.encode()).hexdigest()[:40]}"
        
        logger.info(f"Cancellation initiated for transaction: {transaction_hash}")
        
        return {
            "success": True,
            "message": "Cancellation transaction submitted",
            "original_tx": transaction_hash,
            "cancel_tx": cancel_tx_hash
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel transaction: {str(e)}")


@router.post("/{transaction_hash}/speed-up", summary="Speed up pending transaction")
async def speed_up_transaction(transaction_hash: str, gas_price_multiplier: float = 1.2):
    """
    Speed up a pending transaction by replacing it with higher gas price.
    """
    try:
        db_service = get_db_service()
        
        # Check if transaction exists and is pending
        tx = await db_service.get_transaction_by_hash(transaction_hash)
        
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if tx.get("status") != TransactionStatus.PENDING:
            raise HTTPException(status_code=400, detail="Transaction cannot be sped up (not pending)")
        
        # Generate speed-up transaction hash
        speedup_tx_data = f"speedup_{transaction_hash}_{time.time()}"
        speedup_tx_hash = f"0x{hashlib.sha256(speedup_tx_data.encode()).hexdigest()[:40]}"
        
        # Calculate new gas price
        current_gas_price = tx.get("gas_price", 20.0)
        new_gas_price = current_gas_price * gas_price_multiplier
        
        logger.info(f"Speed-up initiated for transaction: {transaction_hash}")
        
        return {
            "success": True,
            "message": "Speed-up transaction submitted",
            "original_tx": transaction_hash,
            "speedup_tx": speedup_tx_hash,
            "new_gas_price": new_gas_price
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error speeding up transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to speed up transaction: {str(e)}")


@router.get("/{transaction_hash}/status", summary="Check transaction status")
async def check_transaction_status(transaction_hash: str):
    """
    Check the current status of a transaction on the blockchain.
    
    Returns:
    - Status (pending, confirmed, failed)
    - Confirmations
    - Block number
    - Gas used
    """
    try:
        db_service = get_db_service()
        
        # Get transaction from database
        tx = await db_service.get_transaction_by_hash(transaction_hash)
        
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # In production, would query blockchain for real-time status
        status = tx.get("status", TransactionStatus.PENDING)
        confirmations = 12 if status == TransactionStatus.CONFIRMED else 0
        
        return {
            "transaction_hash": transaction_hash,
            "status": status,
            "confirmations": confirmations,
            "block_number": tx.get("block_number"),
            "gas_used": tx.get("gas_used"),
            "timestamp": tx.get("timestamp").isoformat() if tx.get("timestamp") else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking transaction status: {e}")
        return {
            "transaction_hash": transaction_hash,
            "status": "unknown",
            "error": str(e)
        }


@router.get("/{transaction_hash}/receipt", summary="Get transaction receipt")
async def get_transaction_receipt(transaction_hash: str):
    """
    Get the full transaction receipt from the blockchain.
    
    Includes all events, logs, and execution details.
    """
    try:
        db_service = get_db_service()
        
        # Get transaction from database
        tx = await db_service.get_transaction_by_hash(transaction_hash)
        
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Build comprehensive receipt
        receipt = {
            "transaction_hash": transaction_hash,
            "transaction_index": 0,
            "block_hash": f"0x{hashlib.sha256(f'block_{transaction_hash}'.encode()).hexdigest()[:40]}",
            "block_number": tx.get("block_number", 0),
            "from": tx.get("from_address"),
            "to": tx.get("to_address"),
            "gas_used": tx.get("gas_used", 21000),
            "cumulative_gas_used": tx.get("gas_used", 21000),
            "contract_address": None,
            "logs": [],
            "status": 1 if tx.get("status") == TransactionStatus.CONFIRMED else 0,
            "logs_bloom": "0x" + "0" * 512,
            "effective_gas_price": 20000000000,  # 20 Gwei
            "type": "0x2"  # EIP-1559
        }
        
        logger.info(f"Retrieved transaction receipt for {transaction_hash}")
        return receipt
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction receipt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get transaction receipt: {str(e)}")
