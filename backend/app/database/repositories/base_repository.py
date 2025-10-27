"""
Base repository pattern with generic CRUD operations

Provides common database operations for all repositories.
"""

import logging
from typing import TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime
from prisma import Prisma

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations.
    
    Generic repository pattern for type-safe database operations.
    """
    
    def __init__(self, db: Prisma, model_name: str):
        """
        Initialize repository.
        
        Args:
            db: Prisma database client
            model_name: Name of the Prisma model (e.g., 'user', 'wallet')
        """
        self.db = db
        self.model_name = model_name
        self._model = getattr(db, model_name)
    
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create new record.
        
        Args:
            data: Record data
            
        Returns:
            Created record
        """
        try:
            record = await self._model.create(data=data)
            logger.debug(f"Created {self.model_name}: {record.id}")
            return record
        except Exception as e:
            logger.error(f"Error creating {self.model_name}: {e}")
            raise
    
    async def find_by_id(self, id: str) -> Optional[T]:
        """
        Find record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Record if found, None otherwise
        """
        try:
            return await self._model.find_unique(where={"id": id})
        except Exception as e:
            logger.error(f"Error finding {self.model_name} by ID: {e}")
            raise
    
    async def find_many(
        self,
        where: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        take: int = 100,
        order_by: Optional[Dict[str, str]] = None
    ) -> List[T]:
        """
        Find multiple records with pagination.
        
        Args:
            where: Filter conditions
            skip: Number of records to skip (offset)
            take: Number of records to return (limit)
            order_by: Sorting configuration
            
        Returns:
            List of records
        """
        try:
            return await self._model.find_many(
                where=where or {},
                skip=skip,
                take=take,
                order=order_by
            )
        except Exception as e:
            logger.error(f"Error finding {self.model_name} records: {e}")
            raise
    
    async def find_first(
        self,
        where: Dict[str, Any],
        order_by: Optional[Dict[str, str]] = None
    ) -> Optional[T]:
        """
        Find first matching record.
        
        Args:
            where: Filter conditions
            order_by: Sorting configuration
            
        Returns:
            First matching record or None
        """
        try:
            return await self._model.find_first(
                where=where,
                order=order_by
            )
        except Exception as e:
            logger.error(f"Error finding first {self.model_name}: {e}")
            raise
    
    async def update(
        self,
        id: str,
        data: Dict[str, Any]
    ) -> Optional[T]:
        """
        Update record by ID.
        
        Args:
            id: Record ID
            data: Update data
            
        Returns:
            Updated record if found
        """
        try:
            record = await self._model.update(
                where={"id": id},
                data=data
            )
            logger.debug(f"Updated {self.model_name}: {id}")
            return record
        except Exception as e:
            logger.error(f"Error updating {self.model_name}: {e}")
            raise
    
    async def delete(self, id: str) -> Optional[T]:
        """
        Delete record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Deleted record if found
        """
        try:
            record = await self._model.delete(where={"id": id})
            logger.debug(f"Deleted {self.model_name}: {id}")
            return record
        except Exception as e:
            logger.error(f"Error deleting {self.model_name}: {e}")
            raise
    
    async def count(self, where: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records matching criteria.
        
        Args:
            where: Filter conditions
            
        Returns:
            Count of matching records
        """
        try:
            return await self._model.count(where=where or {})
        except Exception as e:
            logger.error(f"Error counting {self.model_name} records: {e}")
            raise
    
    async def exists(self, where: Dict[str, Any]) -> bool:
        """
        Check if record exists.
        
        Args:
            where: Filter conditions
            
        Returns:
            True if record exists
        """
        try:
            count = await self._model.count(where=where)
            return count > 0
        except Exception as e:
            logger.error(f"Error checking {self.model_name} existence: {e}")
            raise
    
    async def upsert(
        self,
        where: Dict[str, Any],
        create: Dict[str, Any],
        update: Dict[str, Any]
    ) -> T:
        """
        Create or update record.
        
        Args:
            where: Unique identifier
            create: Data for creation
            update: Data for update
            
        Returns:
            Created or updated record
        """
        try:
            record = await self._model.upsert(
                where=where,
                data={"create": create, "update": update}
            )
            logger.debug(f"Upserted {self.model_name}")
            return record
        except Exception as e:
            logger.error(f"Error upserting {self.model_name}: {e}")
            raise


class PaginatedResult(Generic[T]):
    """
    Paginated result container.
    """
    
    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        self.has_next = page < self.total_pages
        self.has_prev = page > 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev
        }
