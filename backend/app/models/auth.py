"""
Authentication and Onboarding Models
Handles wallet-based authentication and user registration
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    """User registration request with MetaMask wallet"""
    wallet_address: str = Field(..., description="MetaMask wallet address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: Optional[str] = Field(None, description="Optional email address")
    signature: str = Field(..., description="Signed message from wallet")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    
    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid Ethereum wallet address')
        return v.lower()
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, hyphens, and underscores')
        return v.lower()


class LoginRequest(BaseModel):
    """Wallet-based login request"""
    wallet_address: str = Field(..., description="MetaMask wallet address")
    signature: str = Field(..., description="Signed nonce from wallet")
    
    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid Ethereum wallet address')
        return v.lower()


class NonceRequest(BaseModel):
    """Request for authentication nonce"""
    wallet_address: str = Field(..., description="MetaMask wallet address")
    
    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid Ethereum wallet address')
        return v.lower()


class NonceResponse(BaseModel):
    """Authentication nonce response"""
    nonce: str = Field(..., description="Random nonce for wallet signing")
    message: str = Field(..., description="Message to sign with wallet")


class AuthResponse(BaseModel):
    """Authentication response with tokens"""
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional['UserProfile'] = None
    onboarding_complete: bool = False


class UserProfile(BaseModel):
    """User profile information"""
    id: str
    username: str
    wallet_address: str
    email: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    role: str
    onboarding_complete: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UpdateProfileRequest(BaseModel):
    """Update user profile"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    profile_picture: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, hyphens, and underscores')
        return v.lower() if v else None


class CompleteOnboardingRequest(BaseModel):
    """Complete onboarding process"""
    accepted_terms: bool = Field(..., description="User accepted terms of service")
    preferred_network: str = Field(default="sepolia", description="Preferred blockchain network")
    enable_notifications: bool = Field(default=True, description="Enable push notifications")
