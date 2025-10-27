"""
ChromaDB Manager - Advanced Vector Database Operations

Extends vector_store.py with advanced ChromaDB features:
- Collection management
- Metadata filtering
- Batch operations
- Index optimization
"""

from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class ChromaDBManager:
    """
    Advanced ChromaDB management for agent memory.
    
    Provides:
    - Multi-collection support
    - Advanced querying
    - Batch operations
    - Collection statistics
    - Data cleanup and maintenance
    """
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize ChromaDB manager
        
        Args:
            persist_directory: Directory to persist data
            embedding_model: Model for embeddings
        """
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        logger.info(f"ChromaDB manager initialized at {persist_directory}")
    
    def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> chromadb.Collection:
        """
        Get existing collection or create new one
        
        Args:
            name: Collection name
            metadata: Collection metadata
        
        Returns:
            ChromaDB collection
        """
        try:
            collection = self.client.get_collection(
                name=name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Retrieved existing collection: {name}")
            return collection
        except Exception:
            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {},
                embedding_function=self.embedding_function
            )
            logger.info(f"Created new collection: {name}")
            return collection
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add multiple documents to collection
        
        Args:
            collection_name: Collection name
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: Optional list of document IDs
        
        Returns:
            List of document IDs
        """
        collection = self.get_or_create_collection(collection_name)
        
        # Generate IDs if not provided
        if ids is None:
            timestamp = int(datetime.utcnow().timestamp() * 1000)
            ids = [f"{collection_name}_{timestamp}_{i}" for i in range(len(documents))]
        
        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to {collection_name}")
            return ids
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def query_collection(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Query collection with advanced filters
        
        Args:
            collection_name: Collection name
            query_texts: Query text(s)
            n_results: Number of results per query
            where: Metadata filter
            where_document: Document content filter
        
        Returns:
            Query results with documents, metadatas, distances
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            
            logger.info(f"Query returned {len(results.get('ids', [[]])[0])} results")
            return results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def update_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Update existing documents
        
        Args:
            collection_name: Collection name
            ids: Document IDs to update
            documents: New document texts (optional)
            metadatas: New metadata (optional)
        
        Returns:
            Success status
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            collection.update(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Updated {len(ids)} documents in {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False
    
    def delete_documents(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Delete documents by ID or filter
        
        Args:
            collection_name: Collection name
            ids: Document IDs to delete
            where: Metadata filter for deletion
        
        Returns:
            Success status
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            if ids:
                collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} documents from {collection_name}")
            elif where:
                collection.delete(where=where)
                logger.info(f"Deleted documents matching filter from {collection_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Deletion failed: {e}")
            return False
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection
        
        Args:
            collection_name: Collection name
        
        Returns:
            Collection statistics
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            count = collection.count()
            
            # Get sample documents
            sample = collection.peek(limit=5)
            
            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata,
                "sample_ids": sample.get("ids", []),
                "has_data": count > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
    
    def cleanup_old_data(
        self,
        collection_name: str,
        days_old: int = 30,
        timestamp_field: str = "timestamp"
    ) -> int:
        """
        Clean up old data from collection
        
        Args:
            collection_name: Collection name
            days_old: Delete data older than this many days
            timestamp_field: Metadata field containing timestamp
        
        Returns:
            Number of documents deleted
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Calculate cutoff date
            cutoff = datetime.utcnow() - timedelta(days=days_old)
            cutoff_iso = cutoff.isoformat()
            
            # Get all documents
            all_docs = collection.get(include=["metadatas"])
            
            if not all_docs or not all_docs.get("ids"):
                return 0
            
            # Find old documents
            old_ids = []
            for i, metadata in enumerate(all_docs.get("metadatas", [])):
                doc_timestamp = metadata.get(timestamp_field)
                if doc_timestamp and doc_timestamp < cutoff_iso:
                    old_ids.append(all_docs["ids"][i])
            
            # Delete old documents
            if old_ids:
                collection.delete(ids=old_ids)
                logger.info(f"Cleaned up {len(old_ids)} old documents from {collection_name}")
                return len(old_ids)
            
            return 0
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0
    
    def list_collections(self) -> List[str]:
        """List all collections"""
        try:
            collections = self.client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete entire collection"""
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
    
    def backup_collection(
        self,
        collection_name: str,
        backup_path: str
    ) -> bool:
        """
        Backup collection to JSON file
        
        Args:
            collection_name: Collection to backup
            backup_path: Path to save backup
        
        Returns:
            Success status
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Get all data
            all_data = collection.get(include=["documents", "metadatas"])
            
            # Save to JSON
            with open(backup_path, 'w') as f:
                json.dump({
                    "collection_name": collection_name,
                    "backup_date": datetime.utcnow().isoformat(),
                    "data": all_data
                }, f, indent=2)
            
            logger.info(f"Backed up collection {collection_name} to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def restore_collection(
        self,
        backup_path: str,
        new_collection_name: Optional[str] = None
    ) -> bool:
        """
        Restore collection from backup
        
        Args:
            backup_path: Path to backup file
            new_collection_name: Optional new name for collection
        
        Returns:
            Success status
        """
        try:
            # Load backup
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            collection_name = new_collection_name or backup_data["collection_name"]
            data = backup_data["data"]
            
            # Restore data
            if data.get("ids"):
                self.add_documents(
                    collection_name=collection_name,
                    documents=data["documents"],
                    metadatas=data["metadatas"],
                    ids=data["ids"]
                )
            
            logger.info(f"Restored collection from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False


# Singleton instance
_chromadb_manager: Optional[ChromaDBManager] = None


def get_chromadb_manager(
    persist_directory: str = "./chroma_db"
) -> ChromaDBManager:
    """Get or create singleton ChromaDB manager"""
    global _chromadb_manager
    
    if _chromadb_manager is None:
        _chromadb_manager = ChromaDBManager(persist_directory=persist_directory)
    
    return _chromadb_manager