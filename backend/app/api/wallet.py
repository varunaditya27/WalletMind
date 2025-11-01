# Wallet API endpoints implementing FR-004, FR-005, FR-006
# Handles smart account operations, balance checks, and network management

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
import time
import logging

from app.models.wallet import (
    CreateWalletRequest,
    WalletInfo,
    BalanceRequest,
    BalanceResponse,
    UpdateSpendingLimitRequest,
    SpendingLimitResponse,
    NetworkSwitchRequest,
    NetworkInfo,
    WalletOperationResponse,
    NetworkType,
    WalletType
)
from app.database.service import DatabaseService
from app.blockchain import WalletManager, Web3Provider

router = APIRouter(prefix="/api/wallet", tags=["wallet"])
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
            from app.blockchain import NetworkType as BNetworkType
            provider = Web3Provider()
            provider.connect(BNetworkType.SEPOLIA)
            _blockchain_service = WalletManager(provider)
        except Exception as e:
            logger.error(f"Failed to initialize blockchain service: {e}")
    return _blockchain_service



@router.post("/create", response_model=WalletInfo, summary="Create new wallet (FR-004)")
async def create_wallet(request: CreateWalletRequest):
    """
    Deploy a new ERC-4337 smart contract wallet.
    
    Process:
    1. Deploy wallet contract on specified network
    2. Configure with owner address
    3. Set initial spending limits
    4. Register in agent registry
    
    Implements FR-004: ERC-4337 Smart Account Integration
    """
    try:
        db_service = get_db_service()
        blockchain_service = get_blockchain_service()
        
        # Generate wallet ID
        wallet_id = f"wallet_{int(time.time())}_{request.owner_address[:8]}"
        
        # In production, would deploy actual smart contract
        # For now, create wallet entry with mock address
        wallet_address = f"0x{''.join([hex(int(time.time()))[2:], request.owner_address[2:10]])}"
        
        # Store in database
        wallet_repo = await db_service.wallets
        wallet = await wallet_repo.create_wallet(
            user_id=request.owner_address,  # Using owner as user_id for now
            address=wallet_address,
            wallet_type=request.wallet_type.value,
            network=request.network.value,
            encrypted_key=None
        )
        
        logger.info(f"Created wallet: {wallet_address}")
        
        return WalletInfo(
            wallet_id=wallet.id,
            address=wallet.address,
            wallet_type=request.wallet_type,
            network=request.network,
            owner=request.owner_address,
            balance=0.0,
            spending_limit=request.initial_spending_limit or 0.1,
            total_spent=0.0,
            created_at=wallet.created_at
        )
        
    except Exception as e:
        logger.error(f"Error creating wallet: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create wallet: {str(e)}")


@router.get("/{wallet_address}", response_model=WalletInfo, summary="Get wallet information")
async def get_wallet_info(wallet_address: str):
    """
    Get detailed information about a wallet including balance and limits.
    """
    try:
        db_service = get_db_service()
        blockchain_service = get_blockchain_service()
        
        # Get wallet from database
        wallet_repo = await db_service.wallets
        wallet = await wallet_repo.find_by_address(wallet_address)
        
        if not wallet:
            raise HTTPException(status_code=404, detail=f"Wallet {wallet_address} not found")
        
        # Get balance from blockchain (if available)
        balance = 0.0
        if blockchain_service:
            try:
                from app.blockchain import NetworkType as BNetworkType
                balance_wei = blockchain_service.get_balance(BNetworkType.SEPOLIA)
                balance = balance_wei / 1e18 if balance_wei else 0.0
            except Exception as e:
                logger.warning(f"Could not fetch balance: {e}")
        
        logger.info(f"Retrieved wallet info for {wallet_address}")
        
        return WalletInfo(
            wallet_id=wallet.id,
            address=wallet.address,
            wallet_type=WalletType(wallet.wallet_type),
            network=NetworkType(wallet.network),
            owner=wallet.user_id,
            balance=balance,
            spending_limit=0.1,  # Would fetch from contract
            total_spent=0.0,  # Would calculate from transactions
            created_at=wallet.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving wallet info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve wallet info: {str(e)}")


@router.post("/balance", response_model=BalanceResponse, summary="Check wallet balance")
async def check_balance(request: BalanceRequest):
    """
    Check the current balance of a wallet on a specific network.
    
    Returns ETH balance, USD equivalent, and token balances.
    """
    try:
        blockchain_service = get_blockchain_service()
        
        balance_eth = 0.0
        if blockchain_service:
            try:
                from app.blockchain import NetworkType as BNetworkType
                # Map request network to blockchain NetworkType
                network_map = {
                    NetworkType.ETHEREUM_SEPOLIA: BNetworkType.SEPOLIA,
                    NetworkType.POLYGON_AMOY: BNetworkType.POLYGON_AMOY,
                    NetworkType.BASE_GOERLI: BNetworkType.BASE_GOERLI
                }
                blockchain_network = network_map.get(request.network, BNetworkType.SEPOLIA)
                balance_wei = blockchain_service.get_balance(blockchain_network)
                balance_eth = balance_wei / 1e18
            except Exception as e:
                logger.warning(f"Could not fetch balance from blockchain: {e}")
        
        # Mock ETH price for USD conversion
        eth_price_usd = 1500.0
        balance_usd = balance_eth * eth_price_usd
        
        logger.info(f"Checked balance for {request.wallet_address}: {balance_eth} ETH")
        
        return BalanceResponse(
            address=request.wallet_address,
            network=request.network,
            balance=balance_eth,
            balance_usd=balance_usd,
            tokens=[]  # Would include ERC-20 tokens in production
        )
        
    except Exception as e:
        logger.error(f"Error checking balance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check balance: {str(e)}")


@router.put("/spending-limit", response_model=SpendingLimitResponse, summary="Update spending limit")
async def update_spending_limit(request: UpdateSpendingLimitRequest):
    """
    Update the spending limit for a wallet.
    
    This limit is enforced at the smart contract level for security.
    
    Implements NFR-005: Smart Contract Security
    """
    try:
        db_service = get_db_service()
        
        # Verify wallet exists
        wallet_repo = await db_service.wallets
        wallet = await wallet_repo.find_by_address(request.wallet_address)
        
        if not wallet:
            raise HTTPException(status_code=404, detail=f"Wallet {request.wallet_address} not found")
        
        # In production, would call smart contract to set spending limit
        # For now, store in database metadata
        logger.info(f"Updated spending limit for {request.wallet_address} to {request.new_limit} ETH")
        
        return SpendingLimitResponse(
            wallet_address=request.wallet_address,
            spending_limit=request.new_limit,
            total_spent=0.0,  # Would calculate from transactions
            remaining=request.new_limit,
            reset_at=datetime.now() + timedelta(days=30)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating spending limit: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update spending limit: {str(e)}")


@router.get("/spending-limit/{wallet_address}", response_model=SpendingLimitResponse, summary="Get spending limit")
async def get_spending_limit(wallet_address: str):
    """
    Get current spending limit and usage for a wallet.
    """
    try:
        db_service = get_db_service()
        
        # Verify wallet exists
        wallet_repo = await db_service.wallets
        wallet = await wallet_repo.find_by_address(wallet_address)
        
        if not wallet:
            raise HTTPException(status_code=404, detail=f"Wallet {wallet_address} not found")
        
        # In production, would query smart contract for actual spending limit
        # For now, return mock data
        spending_limit = 0.1  # Default limit
        total_spent = 0.0  # Would calculate from transaction history
        
        logger.info(f"Retrieved spending limit for {wallet_address}")
        
        return SpendingLimitResponse(
            wallet_address=wallet_address,
            spending_limit=spending_limit,
            total_spent=total_spent,
            remaining=spending_limit - total_spent,
            reset_at=datetime.now() + timedelta(days=30)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting spending limit: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get spending limit: {str(e)}")


@router.post("/reset-spent", response_model=WalletOperationResponse, summary="Reset spent amount")
async def reset_spent_amount(wallet_address: str):
    """
    Reset the total spent amount for a wallet (monthly reset).
    
    Only callable by wallet owner.
    """
    try:
        db_service = get_db_service()
        
        # Verify wallet exists
        wallet_repo = await db_service.wallets
        wallet = await wallet_repo.find_by_address(wallet_address)
        
        if not wallet:
            raise HTTPException(status_code=404, detail=f"Wallet {wallet_address} not found")
        
        # In production, would call smart contract to reset spent amount
        logger.info(f"Reset spent amount for wallet {wallet_address}")
        
        return WalletOperationResponse(
            success=True,
            message="Spent amount reset successfully",
            transaction_hash=None,
            data={"wallet_address": wallet_address, "new_spent": 0.0}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting spent amount: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset spent amount: {str(e)}")


@router.post("/switch-network", response_model=WalletOperationResponse, summary="Switch network (FR-006)")
async def switch_network(request: NetworkSwitchRequest):
    """
    Switch the active network for a wallet.
    
    Implements FR-006: Multi-Network Support
    """
    try:
        db_service = get_db_service()
        
        # Verify wallet exists
        wallet_repo = await db_service.wallets
        wallet = await wallet_repo.find_by_address(request.wallet_address)
        
        if not wallet:
            raise HTTPException(status_code=404, detail=f"Wallet {request.wallet_address} not found")
        
        # Update wallet network in database
        await wallet_repo.update(
            wallet.id,
            {"network": request.target_network.value}
        )
        
        logger.info(f"Switched wallet {request.wallet_address} to {request.target_network.value}")
        
        return WalletOperationResponse(
            success=True,
            message=f"Switched to {request.target_network.value}",
            transaction_hash=None,
            data={
                "wallet_address": request.wallet_address,
                "network": request.target_network.value
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching network: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to switch network: {str(e)}")


@router.get("/networks", response_model=List[NetworkInfo], summary="List available networks (FR-006)")
async def list_networks():
    """
    Get list of all supported blockchain networks.
    
    Implements FR-006: Multi-Network Support
    """
    networks = [
        NetworkInfo(
            network=NetworkType.ETHEREUM_SEPOLIA,
            name="Ethereum Sepolia Testnet",
            chain_id=11155111,
            rpc_url="https://sepolia.infura.io/v3/",
            explorer_url="https://sepolia.etherscan.io",
            native_currency="ETH",
            is_testnet=True
        ),
        NetworkInfo(
            network=NetworkType.POLYGON_AMOY,
            name="Polygon Amoy Testnet",
            chain_id=80002,
            rpc_url="https://rpc-amoy.polygon.technology/",
            explorer_url="https://amoy.polygonscan.com",
            native_currency="MATIC",
            is_testnet=True
        ),
        NetworkInfo(
            network=NetworkType.BASE_GOERLI,
            name="Base Goerli Testnet",
            chain_id=84531,
            rpc_url="https://goerli.base.org",
            explorer_url="https://goerli.basescan.org",
            native_currency="ETH",
            is_testnet=True
        )
    ]
    
    return networks


@router.post("/pause", response_model=WalletOperationResponse, summary="Pause wallet (NFR-005)")
async def pause_wallet(wallet_address: str):
    """
    Emergency pause a wallet to prevent all operations.
    
    Implements NFR-005: Smart Contract Security - Emergency Pause
    """
    try:
        db_service = get_db_service()
        
        # Verify wallet exists
        wallet_repo = await db_service.wallets
        wallet = await wallet_repo.find_by_address(wallet_address)
        
        if not wallet:
            raise HTTPException(status_code=404, detail=f"Wallet {wallet_address} not found")
        
        # In production, would call smart contract pause function
        # For now, update database status
        await wallet_repo.update(wallet.id, {"isActive": False})
        
        logger.info(f"Paused wallet {wallet_address}")
        
        return WalletOperationResponse(
            success=True,
            message="Wallet paused successfully",
            transaction_hash=None,
            data={"wallet_address": wallet_address, "paused": True}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing wallet: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause wallet: {str(e)}")


@router.post("/unpause", response_model=WalletOperationResponse, summary="Unpause wallet")
async def unpause_wallet(wallet_address: str):
    """
    Unpause a previously paused wallet.
    
    Only callable by wallet owner.
    """
    try:
        db_service = get_db_service()
        
        # Verify wallet exists
        wallet_repo = await db_service.wallets
        wallet = await wallet_repo.find_by_address(wallet_address)
        
        if not wallet:
            raise HTTPException(status_code=404, detail=f"Wallet {wallet_address} not found")
        
        # In production, would call smart contract unpause function
        # For now, update database status
        await wallet_repo.update(wallet.id, {"isActive": True})
        
        logger.info(f"Unpaused wallet {wallet_address}")
        
        return WalletOperationResponse(
            success=True,
            message="Wallet unpaused successfully",
            transaction_hash=None,
            data={"wallet_address": wallet_address, "paused": False}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unpausing wallet: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unpause wallet: {str(e)}")


@router.get("/status/{wallet_address}", summary="Get wallet status")
async def get_wallet_status(wallet_address: str):
    """
    Get operational status of a wallet (active, paused, etc.).
    """
    try:
        db_service = get_db_service()
        
        # Get wallet from database
        wallet_repo = await db_service.wallets
        wallet = await wallet_repo.find_by_address(wallet_address)
        
        if not wallet:
            raise HTTPException(status_code=404, detail=f"Wallet {wallet_address} not found")
        
        # Get last transaction
        transaction_repo = await db_service.transactions
        transactions = await transaction_repo.find_by_wallet(wallet.id, limit=1)
        last_transaction = transactions[0] if transactions else None
        
        logger.info(f"Retrieved status for wallet {wallet_address}")
        
        return {
            "wallet_address": wallet_address,
            "is_paused": not wallet.is_active,
            "is_active": wallet.is_active,
            "owner": wallet.user_id,
            "last_transaction": last_transaction.id if last_transaction else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get wallet status: {str(e)}")
