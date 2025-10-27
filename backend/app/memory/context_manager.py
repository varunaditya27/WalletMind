"""
Context Manager - Agent Conversation Context Tracking

Manages conversation context and session state for agents:
- Track ongoing conversations
- Maintain session state
- Provide relevant context window
- Handle context compression
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import logging
import json
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Single message in conversation"""
    role: str = Field(..., description="Role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationContext(BaseModel):
    """Conversation context for an agent session"""
    session_id: str
    wallet_address: str
    agent_type: str
    messages: List[Message] = Field(default_factory=list)
    context_window: int = Field(default=10, description="Number of messages to keep in context")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class ContextManager:
    """
    Manages conversation context for AI agents.
    
    Features:
    - Session management
    - Context window management
    - Message history
    - Context compression
    - Session persistence
    """
    
    def __init__(
        self,
        max_sessions: int = 100,
        default_context_window: int = 10,
        session_timeout_minutes: int = 60
    ):
        """
        Initialize context manager
        
        Args:
            max_sessions: Maximum number of concurrent sessions
            default_context_window: Default number of messages in context
            session_timeout_minutes: Session timeout in minutes
        """
        self.max_sessions = max_sessions
        self.default_context_window = default_context_window
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        
        # Active sessions
        self.sessions: Dict[str, ConversationContext] = {}
        
        # Session access order for LRU eviction
        self.session_access_order = deque(maxlen=max_sessions)
        
        logger.info(f"Context manager initialized (max_sessions={max_sessions})")
    
    def create_session(
        self,
        session_id: str,
        wallet_address: str,
        agent_type: str,
        context_window: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """
        Create new conversation session
        
        Args:
            session_id: Unique session identifier
            wallet_address: Wallet address
            agent_type: Type of agent
            context_window: Number of messages in context
            metadata: Additional metadata
        
        Returns:
            ConversationContext instance
        """
        # Cleanup expired sessions first
        self._cleanup_expired_sessions()
        
        # Check if session exists
        if session_id in self.sessions:
            logger.info(f"Session {session_id} already exists, returning existing")
            return self.sessions[session_id]
        
        # Create new session
        context = ConversationContext(
            session_id=session_id,
            wallet_address=wallet_address,
            agent_type=agent_type,
            context_window=context_window or self.default_context_window,
            metadata=metadata or {}
        )
        
        # Add to sessions
        self.sessions[session_id] = context
        self.session_access_order.append(session_id)
        
        # Evict oldest session if at capacity
        if len(self.sessions) > self.max_sessions:
            self._evict_oldest_session()
        
        logger.info(f"Created session {session_id} for {agent_type}")
        return context
    
    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        """
        Get existing session
        
        Args:
            session_id: Session identifier
        
        Returns:
            ConversationContext or None if not found
        """
        session = self.sessions.get(session_id)
        
        if session:
            # Update access order
            if session_id in self.session_access_order:
                self.session_access_order.remove(session_id)
            self.session_access_order.append(session_id)
            
            # Update last access time
            session.last_updated = datetime.utcnow()
        
        return session
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add message to session
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        
        Returns:
            Success status
        """
        session = self.get_session(session_id)
        
        if not session:
            logger.warning(f"Session {session_id} not found")
            return False
        
        # Create message
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        # Add to session
        session.messages.append(message)
        session.last_updated = datetime.utcnow()
        
        # Trim if exceeds context window
        if len(session.messages) > session.context_window * 2:
            session.messages = session.messages[-session.context_window:]
        
        logger.debug(f"Added {role} message to session {session_id}")
        return True
    
    def get_context_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get context messages for session
        
        Args:
            session_id: Session identifier
            limit: Optional limit (defaults to context_window)
        
        Returns:
            List of messages in context window
        """
        session = self.get_session(session_id)
        
        if not session:
            return []
        
        limit = limit or session.context_window
        return session.messages[-limit:]
    
    def get_formatted_context(
        self,
        session_id: str,
        limit: Optional[int] = None,
        include_system: bool = True
    ) -> str:
        """
        Get formatted context string for LLM
        
        Args:
            session_id: Session identifier
            limit: Optional message limit
            include_system: Include system messages
        
        Returns:
            Formatted context string
        """
        messages = self.get_context_messages(session_id, limit)
        
        formatted = []
        for msg in messages:
            if not include_system and msg.role == "system":
                continue
            
            formatted.append(f"{msg.role.upper()}: {msg.content}")
        
        return "\n\n".join(formatted)
    
    def get_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get session summary
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session summary with statistics
        """
        session = self.get_session(session_id)
        
        if not session:
            return {"error": "Session not found"}
        
        # Count messages by role
        role_counts = {}
        for msg in session.messages:
            role_counts[msg.role] = role_counts.get(msg.role, 0) + 1
        
        # Calculate session duration
        duration = (session.last_updated - session.created_at).total_seconds()
        
        return {
            "session_id": session_id,
            "wallet_address": session.wallet_address,
            "agent_type": session.agent_type,
            "total_messages": len(session.messages),
            "role_distribution": role_counts,
            "context_window": session.context_window,
            "duration_seconds": duration,
            "created_at": session.created_at.isoformat(),
            "last_updated": session.last_updated.isoformat(),
            "metadata": session.metadata
        }
    
    def compress_context(
        self,
        session_id: str,
        summarizer_func: Optional[callable] = None
    ) -> bool:
        """
        Compress session context using summarization
        
        Args:
            session_id: Session identifier
            summarizer_func: Optional function to summarize messages
        
        Returns:
            Success status
        """
        session = self.get_session(session_id)
        
        if not session or len(session.messages) < session.context_window:
            return False
        
        try:
            # Get messages to compress (older than context window)
            messages_to_compress = session.messages[:-session.context_window]
            
            if not messages_to_compress:
                return False
            
            # Create summary
            if summarizer_func:
                summary = summarizer_func(messages_to_compress)
            else:
                # Default summarization: just concatenate
                summary_parts = []
                for msg in messages_to_compress:
                    summary_parts.append(f"{msg.role}: {msg.content[:100]}...")
                summary = "CONTEXT SUMMARY:\n" + "\n".join(summary_parts)
            
            # Replace old messages with summary
            summary_message = Message(
                role="system",
                content=summary,
                metadata={"compressed": True, "original_count": len(messages_to_compress)}
            )
            
            session.messages = [summary_message] + session.messages[-session.context_window:]
            
            logger.info(f"Compressed {len(messages_to_compress)} messages in session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Context compression failed: {e}")
            return False
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear session messages
        
        Args:
            session_id: Session identifier
        
        Returns:
            Success status
        """
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        session.messages.clear()
        session.last_updated = datetime.utcnow()
        
        logger.info(f"Cleared session {session_id}")
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session completely
        
        Args:
            session_id: Session identifier
        
        Returns:
            Success status
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            
            if session_id in self.session_access_order:
                self.session_access_order.remove(session_id)
            
            logger.info(f"Deleted session {session_id}")
            return True
        
        return False
    
    def list_sessions(
        self,
        wallet_address: Optional[str] = None,
        agent_type: Optional[str] = None
    ) -> List[str]:
        """
        List session IDs with optional filters
        
        Args:
            wallet_address: Filter by wallet address
            agent_type: Filter by agent type
        
        Returns:
            List of session IDs
        """
        sessions = []
        
        for session_id, session in self.sessions.items():
            if wallet_address and session.wallet_address != wallet_address:
                continue
            if agent_type and session.agent_type != agent_type:
                continue
            sessions.append(session_id)
        
        return sessions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context manager statistics"""
        total_messages = sum(len(s.messages) for s in self.sessions.values())
        
        agent_distribution = {}
        for session in self.sessions.values():
            agent_distribution[session.agent_type] = \
                agent_distribution.get(session.agent_type, 0) + 1
        
        return {
            "total_sessions": len(self.sessions),
            "total_messages": total_messages,
            "max_sessions": self.max_sessions,
            "default_context_window": self.default_context_window,
            "agent_distribution": agent_distribution,
            "session_timeout_minutes": self.session_timeout.total_seconds() / 60
        }
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.utcnow()
        expired = []
        
        for session_id, session in self.sessions.items():
            if now - session.last_updated > self.session_timeout:
                expired.append(session_id)
        
        for session_id in expired:
            self.delete_session(session_id)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def _evict_oldest_session(self):
        """Evict least recently used session"""
        if self.session_access_order:
            oldest_session_id = self.session_access_order[0]
            self.delete_session(oldest_session_id)
            logger.info(f"Evicted oldest session {oldest_session_id}")


# Singleton instance
_context_manager: Optional[ContextManager] = None


def get_context_manager(
    max_sessions: int = 100,
    default_context_window: int = 10
) -> ContextManager:
    """Get or create singleton ContextManager instance"""
    global _context_manager
    
    if _context_manager is None:
        _context_manager = ContextManager(
            max_sessions=max_sessions,
            default_context_window=default_context_window
        )
    
    return _context_manager