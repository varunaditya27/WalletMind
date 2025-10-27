"""
User repository for authentication and user management (FR-007)

Handles user CRUD operations, authentication, and session management.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from prisma import Prisma
from passlib.hash import bcrypt

from .base_repository import BaseRepository, PaginatedResult

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    User repository with authentication support.
    
    Features:
    - User registration and profile management
    - Password hashing and verification
    - Session management
    - Role-based access control
    """
    
    def __init__(self, db: Prisma):
        super().__init__(db, "user")
    
    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        role: str = "USER"
    ):
        """
        Create new user with hashed password.
        
        Args:
            email: User email
            username: Unique username
            password: Plain text password (will be hashed)
            role: User role
            
        Returns:
            Created user (without password hash)
        """
        password_hash = bcrypt.hash(password)
        
        user = await self.create({
            "email": email,
            "username": username,
            "passwordHash": password_hash,
            "role": role
        })
        
        logger.info(f"User created: {user.email}")
        
        return user
    
    async def find_by_email(self, email: str):
        """Find user by email"""
        return await self._model.find_unique(where={"email": email})
    
    async def find_by_username(self, username: str):
        """Find user by username"""
        return await self._model.find_unique(where={"username": username})
    
    async def verify_password(self, user, password: str) -> bool:
        """
        Verify user password.
        
        Args:
            user: User object with passwordHash
            password: Plain text password to verify
            
        Returns:
            True if password matches
        """
        return bcrypt.verify(password, user.passwordHash)
    
    async def update_password(self, user_id: str, new_password: str):
        """
        Update user password.
        
        Args:
            user_id: User ID
            new_password: New plain text password
            
        Returns:
            Updated user
        """
        password_hash = bcrypt.hash(new_password)
        
        return await self.update(user_id, {
            "passwordHash": password_hash,
            "updatedAt": datetime.utcnow()
        })
    
    async def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        return await self.update(user_id, {
            "lastLoginAt": datetime.utcnow()
        })
    
    async def verify_email(self, user_id: str):
        """Mark user email as verified"""
        return await self.update(user_id, {
            "emailVerified": True,
            "updatedAt": datetime.utcnow()
        })
    
    async def deactivate_user(self, user_id: str):
        """Deactivate user account"""
        return await self.update(user_id, {
            "isActive": False,
            "updatedAt": datetime.utcnow()
        })
    
    async def activate_user(self, user_id: str):
        """Activate user account"""
        return await self.update(user_id, {
            "isActive": True,
            "updatedAt": datetime.utcnow()
        })
    
    async def get_paginated_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> PaginatedResult:
        """
        Get paginated list of users.
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            role: Filter by role
            is_active: Filter by active status
            
        Returns:
            PaginatedResult with users
        """
        where = {}
        if role:
            where["role"] = role
        if is_active is not None:
            where["isActive"] = is_active
        
        skip = (page - 1) * page_size
        
        users = await self.find_many(
            where=where,
            skip=skip,
            take=page_size,
            order_by={"createdAt": "desc"}
        )
        
        total = await self.count(where=where)
        
        return PaginatedResult(
            items=users,
            total=total,
            page=page,
            page_size=page_size
        )
    
    # ========== Session Management ==========
    
    async def create_session(
        self,
        user_id: str,
        token: str,
        expires_in_hours: int = 24,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Create user session.
        
        Args:
            user_id: User ID
            token: Session token (JWT)
            expires_in_hours: Session duration
            ip_address: Client IP
            user_agent: Client user agent
            
        Returns:
            Created session
        """
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        session = await self.db.session.create(data={
            "userId": user_id,
            "token": token,
            "expiresAt": expires_at,
            "ipAddress": ip_address,
            "userAgent": user_agent
        })
        
        logger.debug(f"Session created for user: {user_id}")
        
        return session
    
    async def find_session(self, token: str):
        """Find session by token"""
        return await self.db.session.find_unique(where={"token": token})
    
    async def delete_session(self, token: str):
        """Delete session (logout)"""
        try:
            await self.db.session.delete(where={"token": token})
            logger.debug(f"Session deleted: {token[:10]}...")
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
    
    async def delete_expired_sessions(self):
        """Delete all expired sessions"""
        result = await self.db.session.delete_many(
            where={"expiresAt": {"lt": datetime.utcnow()}}
        )
        logger.info(f"Deleted {result} expired sessions")
        return result
    
    async def get_user_sessions(self, user_id: str):
        """Get all active sessions for user"""
        return await self.db.session.find_many(
            where={
                "userId": user_id,
                "expiresAt": {"gt": datetime.utcnow()}
            },
            order={"createdAt": "desc"}
        )
