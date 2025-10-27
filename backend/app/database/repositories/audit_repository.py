"""
Audit repository for audit logging (NFR-006)

Handles audit log CRUD operations and compliance tracking.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from prisma import Prisma

from .base_repository import BaseRepository, PaginatedResult

logger = logging.getLogger(__name__)


class AuditRepository(BaseRepository):
    """Audit log repository for compliance and security"""
    
    def __init__(self, db: Prisma):
        super().__init__(db, "auditlog")
    
    async def log_action(
        self,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Log audit event.
        
        Args:
            action: Action type (e.g., USER_LOGIN, TRANSACTION_SUBMIT)
            resource: Resource type (wallet, agent, transaction)
            user_id: User ID (optional for system actions)
            resource_id: ID of affected resource
            details: Additional details as JSON
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether action succeeded
            error_message: Error message if failed
            
        Returns:
            Created audit log
        """
        log = await self.create({
            "userId": user_id,
            "action": action,
            "resource": resource,
            "resourceId": resource_id,
            "details": details or {},
            "ipAddress": ip_address,
            "userAgent": user_agent,
            "success": success,
            "errorMessage": error_message
        })
        
        logger.debug(f"Audit log: {action} on {resource} (success={success})")
        
        return log
    
    async def find_by_user(
        self,
        user_id: str,
        action: Optional[str] = None,
        days: int = 30,
        limit: int = 100
    ) -> List:
        """Get audit logs for user"""
        since = datetime.utcnow() - timedelta(days=days)
        
        where = {
            "userId": user_id,
            "createdAt": {"gte": since}
        }
        if action:
            where["action"] = action
        
        return await self.find_many(
            where=where,
            take=limit,
            order_by={"createdAt": "desc"}
        )
    
    async def find_by_resource(
        self,
        resource: str,
        resource_id: Optional[str] = None,
        days: int = 30
    ) -> List:
        """Get audit logs for resource"""
        since = datetime.utcnow() - timedelta(days=days)
        
        where = {
            "resource": resource,
            "createdAt": {"gte": since}
        }
        if resource_id:
            where["resourceId"] = resource_id
        
        return await self.find_many(
            where=where,
            order_by={"createdAt": "desc"}
        )
    
    async def find_failed_actions(
        self,
        user_id: Optional[str] = None,
        days: int = 7
    ) -> List:
        """Get failed actions for security monitoring"""
        since = datetime.utcnow() - timedelta(days=days)
        
        where = {
            "success": False,
            "createdAt": {"gte": since}
        }
        if user_id:
            where["userId"] = user_id
        
        return await self.find_many(
            where=where,
            order_by={"createdAt": "desc"}
        )
    
    async def get_audit_stats(
        self,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> dict:
        """Get audit statistics"""
        since = datetime.utcnow() - timedelta(days=days)
        
        where = {"createdAt": {"gte": since}}
        if user_id:
            where["userId"] = user_id
        
        total = await self.count(where=where)
        successful = await self.count(where={**where, "success": True})
        failed = await self.count(where={**where, "success": False})
        
        # Count by action type
        login_count = await self.count(where={**where, "action": "USER_LOGIN"})
        tx_count = await self.count(where={**where, "action": "TRANSACTION_SUBMIT"})
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 100,
            "login_count": login_count,
            "transaction_count": tx_count,
            "period_days": days
        }
