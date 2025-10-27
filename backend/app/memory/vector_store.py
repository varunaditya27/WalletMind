"""
Vector Store Service - ChromaDB Integration (FR-003)

Persistent memory and context management for AI agents:
- Store agent decisions and interactions
- Query relevant context using semantic search
- Track decision patterns for learning
- Enable agent memory across sessions
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Memory Service using ChromaDB for vector storage.
    
    Features:
    - Semantic search over agent history
    - Persistent storage of decisions
    - Context retrieval for improved decision-making
    - Pattern learning from past actions
    """
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "agent_memory",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize ChromaDB vector store
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection
            embedding_model: Model for generating embeddings
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize embeddings
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "AI Agent memory and context"}
            )
            logger.info(f"Created new collection: {collection_name}")
        
        # Initialize LangChain Chroma wrapper
        self.vector_store = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )
    
    async def store(
        self,
        wallet_address: str,
        agent_type: str,
        request: str,
        response: Any,
        reasoning: str,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store an agent interaction in memory
        
        Args:
            wallet_address: Wallet address of the agent
            agent_type: Type of agent (planner, executor, evaluator, communicator)
            request: User request or trigger
            response: Agent response
            reasoning: Agent's reasoning process
            timestamp: When the interaction occurred
            metadata: Additional metadata
        
        Returns:
            ID of the stored memory
        """
        try:
            # Prepare document content
            content = f"""
Agent: {agent_type}
Wallet: {wallet_address}
Request: {request}
Response: {json.dumps(response) if isinstance(response, dict) else str(response)}
Reasoning: {reasoning}
Timestamp: {timestamp.isoformat()}
"""
            
            # Prepare metadata
            doc_metadata = {
                "wallet_address": wallet_address,
                "agent_type": agent_type,
                "timestamp": timestamp.isoformat(),
                "request": request[:200],  # Truncate for metadata
                **(metadata or {})
            }
            
            # Create document
            doc = Document(
                page_content=content,
                metadata=doc_metadata
            )
            
            # Add to vector store
            ids = self.vector_store.add_documents([doc])
            
            logger.info(f"Stored memory for {agent_type} agent: {ids[0]}")
            return ids[0]
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}", exc_info=True)
            raise
    
    async def query(
        self,
        query: str,
        wallet_address: Optional[str] = None,
        agent_type: Optional[str] = None,
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query memory using semantic search
        
        Args:
            query: Search query
            wallet_address: Filter by wallet address
            agent_type: Filter by agent type
            limit: Maximum number of results
            filter_metadata: Additional filter criteria
        
        Returns:
            List of relevant memories
        """
        try:
            # Build filter
            where_filter = filter_metadata or {}
            if wallet_address:
                where_filter["wallet_address"] = wallet_address
            if agent_type:
                where_filter["agent_type"] = agent_type
            
            # Search
            if where_filter:
                results = self.vector_store.similarity_search(
                    query,
                    k=limit,
                    filter=where_filter
                )
            else:
                results = self.vector_store.similarity_search(query, k=limit)
            
            # Format results
            memories = []
            for doc in results:
                memories.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance": "high"  # Could add similarity scores
                })
            
            logger.info(f"Found {len(memories)} relevant memories for query: {query[:100]}")
            return memories
            
        except Exception as e:
            logger.error(f"Memory query failed: {e}", exc_info=True)
            return []
    
    async def get_recent(
        self,
        wallet_address: str,
        limit: int = 10,
        agent_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent memories for a wallet
        
        Args:
            wallet_address: Wallet address
            limit: Maximum number of results
            agent_type: Optional filter by agent type
        
        Returns:
            List of recent memories
        """
        try:
            # Query all memories for this wallet
            where_filter = {"wallet_address": wallet_address}
            if agent_type:
                where_filter["agent_type"] = agent_type
            
            results = self.collection.get(
                where=where_filter,
                limit=limit,
                include=["metadatas", "documents"]
            )
            
            # Format and sort by timestamp
            memories = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"]):
                    metadata = results["metadatas"][i] if results.get("metadatas") else {}
                    memories.append({
                        "content": doc,
                        "metadata": metadata
                    })
                
                # Sort by timestamp (most recent first)
                memories.sort(
                    key=lambda x: x["metadata"].get("timestamp", ""),
                    reverse=True
                )
            
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent memories: {e}")
            return []
    
    async def get_decision_patterns(
        self,
        wallet_address: str,
        decision_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze decision patterns for learning
        
        Args:
            wallet_address: Wallet address
            decision_type: Optional filter by decision type
        
        Returns:
            Analysis of decision patterns
        """
        try:
            # Get all decisions for this wallet
            memories = await self.get_recent(wallet_address, limit=100)
            
            # Analyze patterns
            patterns = {
                "total_decisions": len(memories),
                "agent_distribution": {},
                "common_requests": [],
                "success_rate": 0.0,
                "average_gas_efficiency": 0.0
            }
            
            # Count by agent type
            for memory in memories:
                agent = memory["metadata"].get("agent_type", "unknown")
                patterns["agent_distribution"][agent] = \
                    patterns["agent_distribution"].get(agent, 0) + 1
            
            # TODO: More sophisticated pattern analysis
            # - Transaction success rates
            # - Gas efficiency trends
            # - Common failure reasons
            # - Time-of-day patterns
            
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return {"error": str(e)}
    
    async def clear_wallet_memory(self, wallet_address: str) -> bool:
        """
        Clear all memories for a specific wallet
        
        Args:
            wallet_address: Wallet address
        
        Returns:
            Success status
        """
        try:
            # Delete all documents for this wallet
            results = self.collection.get(
                where={"wallet_address": wallet_address}
            )
            
            if results and results.get("ids"):
                self.collection.delete(ids=results["ids"])
                logger.info(f"Cleared {len(results['ids'])} memories for {wallet_address}")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory collection"""
        try:
            count = self.collection.count()
            
            return {
                "total_memories": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory,
                "embedding_model": self.embeddings.model_name
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}


# Singleton instance
_memory_service: Optional[MemoryService] = None


def get_memory_service(
    persist_directory: str = "./chroma_db",
    collection_name: str = "agent_memory"
) -> MemoryService:
    """Get or create singleton MemoryService instance"""
    global _memory_service
    
    if _memory_service is None:
        _memory_service = MemoryService(
            persist_directory=persist_directory,
            collection_name=collection_name
        )
    
    return _memory_service