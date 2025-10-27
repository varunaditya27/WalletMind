"""
Database connection management with Prisma Client

Handles Prisma client lifecycle, connection pooling, and health checks.
"""

import logging
from typing import Optional
from contextlib import asynccontextmanager
from prisma import Prisma
from prisma.errors import PrismaError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Singleton database manager for Prisma client.
    
    Features:
    - Connection pooling
    - Automatic reconnection
    - Health checks
    - Lifecycle management
    """
    
    _instance: Optional['DatabaseManager'] = None
    _client: Optional[Prisma] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self) -> Prisma:
        """
        Connect to database and return Prisma client.
        
        Returns:
            Connected Prisma client
        """
        if self._client is None or not self._client.is_connected():
            self._client = Prisma(auto_register=True)
            await self._client.connect()
            logger.info("Database connected successfully")
        
        return self._client
    
    async def disconnect(self) -> None:
        """Disconnect from database"""
        if self._client and self._client.is_connected():
            await self._client.disconnect()
            logger.info("Database disconnected")
    
    async def health_check(self) -> bool:
        """
        Check database connection health.
        
        Returns:
            True if database is accessible
        """
        try:
            if self._client and self._client.is_connected():
                # Simple query to test connection
                await self._client.query_raw("SELECT 1")
                return True
            return False
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_client(self) -> Optional[Prisma]:
        """
        Get current Prisma client without connecting.
        
        Returns:
            Prisma client if connected, None otherwise
        """
        return self._client if self._client and self._client.is_connected() else None


# Global database manager instance
_db_manager = DatabaseManager()


async def init_db() -> Prisma:
    """
    Initialize database connection.
    
    Usage:
        ```python
        # In FastAPI startup
        @app.on_event("startup")
        async def startup():
            await init_db()
        ```
    
    Returns:
        Connected Prisma client
    """
    return await _db_manager.connect()


async def close_db() -> None:
    """
    Close database connection.
    
    Usage:
        ```python
        # In FastAPI shutdown
        @app.on_event("shutdown")
        async def shutdown():
            await close_db()
        ```
    """
    await _db_manager.disconnect()


async def get_db() -> Prisma:
    """
    Get database connection (dependency injection).
    
    Usage:
        ```python
        # In FastAPI route
        @app.get("/users")
        async def get_users(db: Prisma = Depends(get_db)):
            users = await db.user.find_many()
            return users
        ```
    
    Returns:
        Connected Prisma client
    
    Raises:
        RuntimeError: If database is not connected
    """
    client = _db_manager.get_client()
    if client is None:
        # Auto-connect if not connected
        client = await _db_manager.connect()
    
    return client


@asynccontextmanager
async def get_db_context():
    """
    Context manager for database operations.
    
    Usage:
        ```python
        async with get_db_context() as db:
            user = await db.user.create(data={"email": "test@example.com"})
        ```
    
    Yields:
        Connected Prisma client
    """
    client = await get_db()
    try:
        yield client
    finally:
        # Don't disconnect - managed by DatabaseManager
        pass


async def health_check() -> dict:
    """
    Comprehensive database health check.
    
    Returns:
        Health status dictionary
    """
    try:
        is_healthy = await _db_manager.health_check()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "connected": _db_manager.get_client() is not None,
            "database": "postgresql",
            "orm": "prisma"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


# Transaction helper
@asynccontextmanager
async def transaction():
    """
    Create database transaction context.
    
    Usage:
        ```python
        async with transaction() as tx:
            await tx.user.create(data={"email": "test@example.com"})
            await tx.wallet.create(data={"address": "0x..."})
        ```
    
    Note: Prisma Python client doesn't support interactive transactions yet.
    This is a placeholder for future support.
    """
    client = await get_db()
    # TODO: Implement when Prisma Python adds transaction support
    # For now, just yield the client
    yield client
