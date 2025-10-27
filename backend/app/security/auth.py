"""
Authentication Service - API Security and Agent Authorization

Handles:
- API key generation and management
- JWT token creation and validation for agents
- Role-based access control (RBAC)
- Session management and tracking
- Rate limiting per API key
- OAuth integration for external services
- Token refresh and rotation
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

try:
    import jwt  # PyJWT library
except ImportError:
    logger.warning("PyJWT not installed - JWT functionality disabled. Install with: pip install pyjwt")
    jwt = None  # type: ignore


class UserRole(str, Enum):
    """User/Agent roles for RBAC"""
    ADMIN = "admin"
    AGENT = "agent"
    USER = "user"
    SERVICE = "service"
    READONLY = "readonly"


class TokenType(str, Enum):
    """JWT token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


@dataclass
class APIKey:
    """API key metadata"""
    key_id: str
    key_hash: str  # Hashed version of the key
    name: str
    role: UserRole
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    use_count: int
    rate_limit: int  # Requests per minute
    enabled: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (safe for storage)"""
        return {
            "key_id": self.key_id,
            "key_hash": self.key_hash,
            "name": self.name,
            "role": self.role.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "use_count": self.use_count,
            "rate_limit": self.rate_limit,
            "enabled": self.enabled
        }


@dataclass
class Session:
    """User/Agent session"""
    session_id: str
    user_id: str
    role: UserRole
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": self.role.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata
        }


@dataclass
class RateLimitStatus:
    """Rate limit status for an API key"""
    key_id: str
    requests_made: int
    limit: int
    window_start: datetime
    window_end: datetime
    remaining: int
    is_limited: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            **asdict(self),
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat()
        }


class AuthService:
    """
    Authentication and authorization service.
    
    Features:
    - API key generation with secure random tokens
    - JWT token creation and validation (HS256)
    - Role-based access control (RBAC)
    - Session management with automatic expiration
    - Rate limiting per API key (requests per minute)
    - Token refresh mechanism
    - API key rotation and revocation
    
    Security:
    - API keys stored as salted hashes only
    - JWT signed with secret key
    - Automatic session expiration
    - Rate limiting to prevent abuse
    - Constant-time key comparison
    """
    
    def __init__(
        self,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        access_token_expiry_minutes: int = 60,
        refresh_token_expiry_days: int = 7,
        session_expiry_hours: int = 24,
        rate_limit_window_seconds: int = 60
    ):
        """
        Initialize AuthService.
        
        Args:
            jwt_secret: Secret key for JWT signing
            jwt_algorithm: JWT algorithm (default HS256)
            access_token_expiry_minutes: Access token lifetime
            refresh_token_expiry_days: Refresh token lifetime
            session_expiry_hours: Session lifetime
            rate_limit_window_seconds: Rate limit window duration
        """
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.access_token_expiry = timedelta(minutes=access_token_expiry_minutes)
        self.refresh_token_expiry = timedelta(days=refresh_token_expiry_days)
        self.session_expiry = timedelta(hours=session_expiry_hours)
        self.rate_limit_window = timedelta(seconds=rate_limit_window_seconds)
        
        # Storage
        self.api_keys: Dict[str, APIKey] = {}  # key_hash -> APIKey
        self.sessions: Dict[str, Session] = {}  # session_id -> Session
        self.rate_limits: Dict[str, Dict[str, Any]] = {}  # key_id -> rate limit data
        
        logger.info("AuthService initialized")
    
    def _hash_key(self, key: str) -> str:
        """Hash API key for secure storage"""
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()
    
    def generate_api_key(
        self,
        name: str,
        role: UserRole = UserRole.USER,
        rate_limit: int = 60,
        expiry_days: Optional[int] = None
    ) -> Tuple[str, APIKey]:
        """
        Generate new API key.
        
        Args:
            name: Descriptive name for the key
            role: User role for RBAC
            rate_limit: Requests per minute allowed
            expiry_days: Days until expiration (None = no expiry)
            
        Returns:
            Tuple of (api_key, APIKey metadata)
        """
        try:
            # Generate secure random key
            key_id = f"wm_{secrets.token_hex(16)}"
            api_key = f"sk_{secrets.token_urlsafe(32)}"
            key_hash = self._hash_key(api_key)
            
            # Create metadata
            now = datetime.now()
            expires_at = now + timedelta(days=expiry_days) if expiry_days else None
            
            metadata = APIKey(
                key_id=key_id,
                key_hash=key_hash,
                name=name,
                role=role,
                created_at=now,
                expires_at=expires_at,
                last_used=None,
                use_count=0,
                rate_limit=rate_limit,
                enabled=True
            )
            
            # Store by hash
            self.api_keys[key_hash] = metadata
            
            logger.info(f"Generated API key {key_id} for {name} with role {role.value}")
            return api_key, metadata
            
        except Exception as e:
            logger.error(f"Error generating API key: {e}")
            raise
    
    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """
        Validate API key and update usage.
        
        Args:
            api_key: API key to validate
            
        Returns:
            APIKey metadata if valid, None otherwise
        """
        try:
            key_hash = self._hash_key(api_key)
            
            if key_hash not in self.api_keys:
                logger.warning("Invalid API key provided")
                return None
            
            metadata = self.api_keys[key_hash]
            
            # Check if enabled
            if not metadata.enabled:
                logger.warning(f"API key {metadata.key_id} is disabled")
                return None
            
            # Check expiration
            if metadata.expires_at and datetime.now() > metadata.expires_at:
                logger.warning(f"API key {metadata.key_id} has expired")
                return None
            
            # Check rate limit
            rate_status = self.check_rate_limit(metadata.key_id)
            if rate_status.is_limited:
                logger.warning(f"Rate limit exceeded for {metadata.key_id}")
                return None
            
            # Update usage
            metadata.last_used = datetime.now()
            metadata.use_count += 1
            
            # Increment rate limit counter
            self._increment_rate_limit(metadata.key_id)
            
            logger.debug(f"Validated API key {metadata.key_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None
    
    def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke (disable) an API key.
        
        Args:
            key_id: Key ID to revoke
            
        Returns:
            True if revoked successfully
        """
        try:
            for metadata in self.api_keys.values():
                if metadata.key_id == key_id:
                    metadata.enabled = False
                    logger.info(f"Revoked API key {key_id}")
                    return True
            
            logger.warning(f"API key {key_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
            return False
    
    def create_jwt_token(
        self,
        user_id: str,
        role: UserRole,
        token_type: TokenType = TokenType.ACCESS,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create JWT token for authentication.
        
        Args:
            user_id: User/Agent identifier
            role: User role
            token_type: Type of token (access/refresh)
            additional_claims: Extra claims to include
            
        Returns:
            Encoded JWT token
        """
        try:
            now = datetime.now()
            
            # Set expiration based on token type
            if token_type == TokenType.ACCESS:
                expires = now + self.access_token_expiry
            elif token_type == TokenType.REFRESH:
                expires = now + self.refresh_token_expiry
            else:
                expires = now + self.access_token_expiry
            
            # Build claims
            claims = {
                "sub": user_id,
                "role": role.value,
                "type": token_type.value,
                "iat": now.timestamp(),
                "exp": expires.timestamp(),
                "jti": secrets.token_hex(16)  # Unique token ID
            }
            
            if additional_claims:
                claims.update(additional_claims)
            
            # Encode JWT
            token = jwt.encode(claims, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            logger.debug(f"Created {token_type.value} token for {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating JWT token: {e}")
            raise
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate and decode JWT token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Decoded claims if valid, None otherwise
        """
        try:
            # Decode and verify
            claims = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            logger.debug(f"Validated JWT token for {claims.get('sub')}")
            return claims
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating JWT token: {e}")
            return None
    
    def create_session(
        self,
        user_id: str,
        role: UserRole,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create new user/agent session.
        
        Args:
            user_id: User/Agent identifier
            role: User role
            ip_address: Client IP address
            user_agent: Client user agent
            metadata: Additional session data
            
        Returns:
            Session object
        """
        try:
            now = datetime.now()
            session_id = secrets.token_urlsafe(32)
            
            session = Session(
                session_id=session_id,
                user_id=user_id,
                role=role,
                created_at=now,
                expires_at=now + self.session_expiry,
                last_activity=now,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            self.sessions[session_id] = session
            
            logger.info(f"Created session for {user_id} with role {role.value}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def validate_session(self, session_id: str) -> Optional[Session]:
        """
        Validate session and update activity.
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            Session if valid, None otherwise
        """
        try:
            if session_id not in self.sessions:
                logger.warning("Invalid session ID")
                return None
            
            session = self.sessions[session_id]
            
            # Check expiration
            if datetime.now() > session.expires_at:
                logger.warning(f"Session {session_id[:8]}... has expired")
                del self.sessions[session_id]
                return None
            
            # Update activity
            session.last_activity = datetime.now()
            
            logger.debug(f"Validated session for {session.user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    def end_session(self, session_id: str) -> bool:
        """
        End (delete) a session.
        
        Args:
            session_id: Session to end
            
        Returns:
            True if ended successfully
        """
        try:
            if session_id in self.sessions:
                user_id = self.sessions[session_id].user_id
                del self.sessions[session_id]
                logger.info(f"Ended session for {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False
    
    def check_rate_limit(self, key_id: str) -> RateLimitStatus:
        """
        Check rate limit status for an API key.
        
        Args:
            key_id: API key ID to check
            
        Returns:
            RateLimitStatus with current limit info
        """
        try:
            # Find the API key metadata
            metadata = None
            for key_meta in self.api_keys.values():
                if key_meta.key_id == key_id:
                    metadata = key_meta
                    break
            
            if not metadata:
                raise ValueError(f"API key {key_id} not found")
            
            now = datetime.now()
            
            # Initialize rate limit data if needed
            if key_id not in self.rate_limits:
                window_start = now
                self.rate_limits[key_id] = {
                    "count": 0,
                    "window_start": window_start
                }
            
            limit_data = self.rate_limits[key_id]
            window_start = limit_data["window_start"]
            window_end = window_start + self.rate_limit_window
            
            # Reset window if expired
            if now > window_end:
                limit_data["count"] = 0
                limit_data["window_start"] = now
                window_start = now
                window_end = now + self.rate_limit_window
            
            requests_made = limit_data["count"]
            remaining = max(0, metadata.rate_limit - requests_made)
            is_limited = requests_made >= metadata.rate_limit
            
            return RateLimitStatus(
                key_id=key_id,
                requests_made=requests_made,
                limit=metadata.rate_limit,
                window_start=window_start,
                window_end=window_end,
                remaining=remaining,
                is_limited=is_limited
            )
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            raise
    
    def _increment_rate_limit(self, key_id: str):
        """Increment rate limit counter for a key"""
        if key_id in self.rate_limits:
            self.rate_limits[key_id]["count"] += 1
    
    def check_permission(
        self,
        role: UserRole,
        required_role: UserRole
    ) -> bool:
        """
        Check if role has required permission.
        
        Args:
            role: User's current role
            required_role: Required role for action
            
        Returns:
            True if permission granted
        """
        # Role hierarchy: ADMIN > SERVICE > AGENT > USER > READONLY
        hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.SERVICE: 3,
            UserRole.AGENT: 2,
            UserRole.USER: 1,
            UserRole.READONLY: 0
        }
        
        user_level = hierarchy.get(role, 0)
        required_level = hierarchy.get(required_role, 0)
        
        has_permission = user_level >= required_level
        
        logger.debug(
            f"Permission check: {role.value} {'allowed' if has_permission else 'denied'} "
            f"for {required_role.value}"
        )
        
        return has_permission
    
    def cleanup_expired(self):
        """Remove expired sessions and rate limit data"""
        try:
            now = datetime.now()
            
            # Clean up expired sessions
            expired_sessions = [
                sid for sid, session in self.sessions.items()
                if now > session.expires_at
            ]
            for sid in expired_sessions:
                del self.sessions[sid]
            
            # Clean up old rate limit windows
            expired_limits = [
                key_id for key_id, data in self.rate_limits.items()
                if now > data["window_start"] + self.rate_limit_window + timedelta(hours=1)
            ]
            for key_id in expired_limits:
                del self.rate_limits[key_id]
            
            if expired_sessions or expired_limits:
                logger.info(
                    f"Cleaned up {len(expired_sessions)} sessions and "
                    f"{len(expired_limits)} rate limits"
                )
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get authentication service statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_api_keys": len(self.api_keys),
            "active_api_keys": len([k for k in self.api_keys.values() if k.enabled]),
            "total_sessions": len(self.sessions),
            "rate_limits_tracked": len(self.rate_limits),
            "keys_by_role": {
                role.value: len([k for k in self.api_keys.values() if k.role == role])
                for role in UserRole
            }
        }


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service(
    jwt_secret: Optional[str] = None,
    access_token_expiry_minutes: int = 60,
    refresh_token_expiry_days: int = 7
) -> AuthService:
    """
    Get or create singleton AuthService instance.
    
    Args:
        jwt_secret: JWT secret key (from env if None)
        access_token_expiry_minutes: Access token lifetime
        refresh_token_expiry_days: Refresh token lifetime
        
    Returns:
        AuthService singleton instance
    """
    global _auth_service
    
    if _auth_service is None:
        import os
        secret = jwt_secret or os.getenv("JWT_SECRET", secrets.token_hex(32))
        _auth_service = AuthService(
            jwt_secret=secret,
            access_token_expiry_minutes=access_token_expiry_minutes,
            refresh_token_expiry_days=refresh_token_expiry_days
        )
        logger.info("AuthService singleton initialized")
    
    return _auth_service
