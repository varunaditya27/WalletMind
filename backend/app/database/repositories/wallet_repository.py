"""
Wallet repository for wallet management (FR-002)

Handles wallet CRUD operations, balance tracking, and network management.
"""

import logging
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from prisma import Prisma

from .base_repository import BaseRepository, PaginatedResult

logger = logging.getLogger(__name__)


class WalletRepository(BaseRepository):
    """
    Wallet repository with balance and network management.
    
    Features:
    - Wallet creation and management
    - Balance tracking
    - Multi-network support
    - Transaction history
    """
    
    def __init__(self, db: Prisma):
        super().__init__(db, "wallet")
    
    async def create_wallet(
        self,
        user_id: str,
        address: str,
        wallet_type: str = "SMART_CONTRACT",
        network: str = "SEPOLIA",
        encrypted_key: Optional[str] = None,
        mnemonic_id: Optional[str] = None,
        account_index: int = 0
    ):
        """
        Create new wallet.
        
        Args:
            user_id: Owner user ID
            address: Wallet address
            wallet_type: Wallet type (SMART_CONTRACT, EOA, MULTISIG)
            network: Blockchain network
            encrypted_key: Encrypted private key
            mnemonic_id: Reference to KeyManager mnemonic storage
            account_index: BIP44 account index
            
        Returns:
            Created wallet
        """
        wallet = await self.create({
            "userId": user_id,
            "address": address,
            "walletType": wallet_type,
            "network": network,
            "encryptedKey": encrypted_key,
            "mnemonicId": mnemonic_id,
            "accountIndex": account_index,
            "balance": Decimal(0)
        })
        
        logger.info(f"Wallet created: {address} on {network}")
        
        return wallet
    
    async def find_by_address(self, address: str):
        """Find wallet by address"""
        return await self._model.find_unique(where={"address": address})
    
    async def find_user_wallets(
        self,
        user_id: str,
        network: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> List:
        """
        Find all wallets for user.
        
        Args:
            user_id: User ID
            network: Filter by network
            is_active: Filter by active status
            
        Returns:
            List of wallets
        """
        where = {"userId": user_id}
        
        if network:
            where["network"] = network
        if is_active is not None:
            where["isActive"] = is_active
        
        return await self.find_many(
            where=where,
            order_by={"createdAt": "desc"}
        )
    
    async def update_balance(
        self,
        wallet_id: str,
        new_balance: int  # Wei
    ):
        """
        Update wallet balance.
        
        Args:
            wallet_id: Wallet ID
            new_balance: New balance in wei
            
        Returns:
            Updated wallet
        """
        return await self.update(wallet_id, {
            "balance": Decimal(new_balance),
            "updatedAt": datetime.utcnow()
        })
    
    async def increment_balance(
        self,
        wallet_id: str,
        amount: int  # Wei
    ):
        """
        Increment wallet balance.
        
        Args:
            wallet_id: Wallet ID
            amount: Amount to add in wei
            
        Returns:
            Updated wallet
        """
        wallet = await self.find_by_id(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {wallet_id}")
        
        new_balance = int(wallet.balance) + amount
        
        return await self.update_balance(wallet_id, new_balance)
    
    async def decrement_balance(
        self,
        wallet_id: str,
        amount: int  # Wei
    ):
        """
        Decrement wallet balance.
        
        Args:
            wallet_id: Wallet ID
            amount: Amount to subtract in wei
            
        Returns:
            Updated wallet
            
        Raises:
            ValueError: If insufficient balance
        """
        wallet = await self.find_by_id(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {wallet_id}")
        
        current_balance = int(wallet.balance)
        if current_balance < amount:
            raise ValueError(f"Insufficient balance: {current_balance} < {amount}")
        
        new_balance = current_balance - amount
        
        return await self.update_balance(wallet_id, new_balance)
    
    async def deactivate_wallet(self, wallet_id: str):
        """Deactivate wallet"""
        return await self.update(wallet_id, {
            "isActive": False,
            "updatedAt": datetime.utcnow()
        })
    
    async def activate_wallet(self, wallet_id: str):
        """Activate wallet"""
        return await self.update(wallet_id, {
            "isActive": True,
            "updatedAt": datetime.utcnow()
        })
    
    async def get_wallet_stats(self, wallet_id: str) -> dict:
        """
        Get wallet statistics.
        
        Args:
            wallet_id: Wallet ID
            
        Returns:
            Statistics dictionary
        """
        wallet = await self.find_by_id(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {wallet_id}")
        
        # Count related records
        agent_count = await self.db.agent.count(where={"walletId": wallet_id})
        tx_count = await self.db.transaction.count(where={"walletId": wallet_id})
        successful_tx = await self.db.transaction.count(
            where={
                "walletId": wallet_id,
                "status": "CONFIRMED"
            }
        )
        
        return {
            "wallet_id": wallet_id,
            "address": wallet.address,
            "balance": str(wallet.balance),
            "network": wallet.network,
            "agent_count": agent_count,
            "transaction_count": tx_count,
            "successful_transactions": successful_tx,
            "success_rate": (successful_tx / tx_count * 100) if tx_count > 0 else 0,
            "created_at": wallet.createdAt,
            "is_active": wallet.isActive
        }
    
    async def get_wallets_by_network(
        self,
        network: str,
        is_active: Optional[bool] = True
    ) -> List:
        """
        Get all wallets on specific network.
        
        Args:
            network: Network name
            is_active: Filter by active status
            
        Returns:
            List of wallets
        """
        where = {"network": network}
        if is_active is not None:
            where["isActive"] = is_active
        
        return await self.find_many(
            where=where,
            order_by={"balance": "desc"}
        )
