"""
Authentication API Endpoints
Handles wallet-based registration, login, and user onboarding
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from eth_account.messages import encode_defunct
from eth_account import Account

from app.models.auth import (
    RegisterRequest,
    LoginRequest,
    NonceRequest,
    NonceResponse,
    AuthResponse,
    UserProfile,
    UpdateProfileRequest,
    CompleteOnboardingRequest
)
from app.database.service import DatabaseService
from app.security.auth import get_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# In-memory nonce storage (in production, use Redis)
_nonce_store = {}


def generate_nonce() -> str:
    """Generate a secure random nonce"""
    return secrets.token_hex(32)


def get_sign_message(wallet_address: str, nonce: str) -> str:
    """Generate the message to be signed by the wallet"""
    return f"Sign this message to authenticate with WalletMind.\n\nWallet: {wallet_address}\nNonce: {nonce}\n\nThis request will not trigger a blockchain transaction or cost any gas fees."


def verify_signature(wallet_address: str, signature: str, message: str) -> bool:
    """Verify the wallet signature"""
    try:
        # Encode the message
        message_hash = encode_defunct(text=message)
        
        # Recover the address from the signature
        recovered_address = Account.recover_message(message_hash, signature=signature)
        
        # Compare addresses (case-insensitive)
        return recovered_address.lower() == wallet_address.lower()
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


@router.post("/nonce", response_model=NonceResponse, summary="Get authentication nonce")
async def get_nonce(request: NonceRequest):
    """
    Get a nonce for wallet authentication.
    The user must sign this nonce with their wallet to prove ownership.
    """
    try:
        wallet_address = request.wallet_address.lower()
        
        # Generate a new nonce
        nonce = generate_nonce()
        
        # Store nonce with expiration (5 minutes)
        _nonce_store[wallet_address] = {
            "nonce": nonce,
            "expires_at": datetime.utcnow() + timedelta(minutes=5)
        }
        
        # Generate the message to sign
        message = get_sign_message(wallet_address, nonce)
        
        logger.info(f"Generated nonce for wallet: {wallet_address}")
        
        return NonceResponse(
            nonce=nonce,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error generating nonce: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate nonce")


@router.post("/register", response_model=AuthResponse, summary="Register new user")
async def register_user(request: RegisterRequest):
    """
    Register a new user with MetaMask wallet.
    
    Flow:
    1. User requests nonce
    2. User signs nonce with MetaMask
    3. Backend verifies signature
    4. User account is created
    """
    try:
        wallet_address = request.wallet_address.lower()
        
        # Check if nonce exists and is valid
        if wallet_address not in _nonce_store:
            raise HTTPException(status_code=400, detail="No nonce found. Please request a nonce first.")
        
        nonce_data = _nonce_store[wallet_address]
        if datetime.utcnow() > nonce_data["expires_at"]:
            del _nonce_store[wallet_address]
            raise HTTPException(status_code=400, detail="Nonce expired. Please request a new nonce.")
        
        # Verify the signature
        message = get_sign_message(wallet_address, nonce_data["nonce"])
        if not verify_signature(wallet_address, request.signature, message):
            raise HTTPException(status_code=401, detail="Invalid signature. Wallet verification failed.")
        
        # Clear the used nonce
        del _nonce_store[wallet_address]
        
        # Connect to database
        db = DatabaseService()
        await db.connect()
        
        try:
            # Check if user already exists
            existing_user = await db.prisma.user.find_first(
                where={
                    "OR": [
                        {"walletAddress": wallet_address},
                        {"username": request.username.lower()}
                    ]
                }
            )
            
            if existing_user:
                if existing_user.walletAddress == wallet_address:
                    raise HTTPException(status_code=400, detail="Wallet address already registered")
                else:
                    raise HTTPException(status_code=400, detail="Username already taken")
            
            # Create new user with a new nonce for future logins
            new_nonce = generate_nonce()
            new_user = await db.prisma.user.create(
                data={
                    "username": request.username.lower(),
                    "walletAddress": wallet_address,
                    "email": request.email,
                    "bio": request.bio,
                    "profilePicture": request.profile_picture,
                    "nonce": new_nonce,
                    "onboardingComplete": False,
                    "role": "USER",
                    "isActive": True
                }
            )
            
            # Generate access and refresh tokens
            auth_service = get_auth_service()
            from app.security.auth import UserRole, TokenType
            
            access_token = auth_service.create_jwt_token(
                user_id=new_user.id,
                role=UserRole.USER,
                token_type=TokenType.ACCESS,
                additional_claims={"username": new_user.username}
            )
            refresh_token = auth_service.create_jwt_token(
                user_id=new_user.id,
                role=UserRole.USER,
                token_type=TokenType.REFRESH,
                additional_claims={"username": new_user.username}
            )
            
            # Create session
            await db.prisma.session.create(
                data={
                    "userId": new_user.id,
                    "token": access_token,
                    "expiresAt": datetime.utcnow() + timedelta(hours=24)
                }
            )
            
            logger.info(f"New user registered: {new_user.username} ({wallet_address})")
            
            return AuthResponse(
                success=True,
                message="Registration successful",
                access_token=access_token,
                refresh_token=refresh_token,
                user=UserProfile(
                    id=new_user.id,
                    username=new_user.username,
                    wallet_address=new_user.walletAddress,
                    email=new_user.email,
                    bio=new_user.bio,
                    profile_picture=new_user.profilePicture,
                    role=new_user.role,
                    onboarding_complete=new_user.onboardingComplete,
                    created_at=new_user.createdAt,
                    last_login_at=new_user.lastLoginAt
                ),
                onboarding_complete=False
            )
            
        finally:
            await db.disconnect()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=AuthResponse, summary="Login with wallet")
async def login_user(request: LoginRequest):
    """
    Login with MetaMask wallet.
    
    Flow:
    1. User requests nonce for their wallet
    2. User signs nonce with MetaMask
    3. Backend verifies signature and issues tokens
    """
    try:
        wallet_address = request.wallet_address.lower()
        
        # Connect to database
        db = DatabaseService()
        await db.connect()
        
        try:
            # Find user by wallet address
            user = await db.prisma.user.find_unique(
                where={"walletAddress": wallet_address}
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found. Please register first.")
            
            if not user.isActive:
                raise HTTPException(status_code=403, detail="Account is disabled")
            
            # Check if nonce exists
            if wallet_address not in _nonce_store:
                raise HTTPException(status_code=400, detail="No nonce found. Please request a nonce first.")
            
            nonce_data = _nonce_store[wallet_address]
            if datetime.utcnow() > nonce_data["expires_at"]:
                del _nonce_store[wallet_address]
                raise HTTPException(status_code=400, detail="Nonce expired. Please request a new nonce.")
            
            # Verify the signature
            message = get_sign_message(wallet_address, nonce_data["nonce"])
            if not verify_signature(wallet_address, request.signature, message):
                raise HTTPException(status_code=401, detail="Invalid signature. Wallet verification failed.")
            
            # Clear the used nonce
            del _nonce_store[wallet_address]
            
            # Generate new nonce for next login
            new_nonce = generate_nonce()
            
            # Update user's last login and nonce
            updated_user = await db.prisma.user.update(
                where={"id": user.id},
                data={
                    "lastLoginAt": datetime.utcnow(),
                    "nonce": new_nonce
                }
            )
            
            # Generate tokens
            auth_service = get_auth_service()
            from app.security.auth import UserRole, TokenType
            
            access_token = auth_service.create_jwt_token(
                user_id=user.id,
                role=UserRole.USER,
                token_type=TokenType.ACCESS,
                additional_claims={"username": user.username}
            )
            refresh_token = auth_service.create_jwt_token(
                user_id=user.id,
                role=UserRole.USER,
                token_type=TokenType.REFRESH,
                additional_claims={"username": user.username}
            )
            
            # Create session
            await db.prisma.session.create(
                data={
                    "userId": user.id,
                    "token": access_token,
                    "expiresAt": datetime.utcnow() + timedelta(hours=24)
                }
            )
            
            logger.info(f"User logged in: {user.username} ({wallet_address})")
            
            return AuthResponse(
                success=True,
                message="Login successful",
                access_token=access_token,
                refresh_token=refresh_token,
                user=UserProfile(
                    id=updated_user.id,
                    username=updated_user.username,
                    wallet_address=updated_user.walletAddress,
                    email=updated_user.email,
                    bio=updated_user.bio,
                    profile_picture=updated_user.profilePicture,
                    role=updated_user.role,
                    onboarding_complete=updated_user.onboardingComplete,
                    created_at=updated_user.createdAt,
                    last_login_at=updated_user.lastLoginAt
                ),
                onboarding_complete=updated_user.onboardingComplete
            )
            
        finally:
            await db.disconnect()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/me", response_model=UserProfile, summary="Get current user")
async def get_current_user(request: Request):
    """
    Get the current authenticated user's profile.
    Requires valid access token in Authorization header.
    """
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization token")
        
        token = auth_header.split(" ")[1]
        
        # Verify token
        auth_service = get_auth_service()
        payload = auth_service.validate_jwt_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_id = payload.get("sub")
        
        # Connect to database
        db = DatabaseService()
        await db.connect()
        
        try:
            user = await db.prisma.user.find_unique(
                where={"id": user_id}
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return UserProfile(
                id=user.id,
                username=user.username,
                wallet_address=user.walletAddress,
                email=user.email,
                bio=user.bio,
                profile_picture=user.profilePicture,
                role=user.role,
                onboarding_complete=user.onboardingComplete,
                created_at=user.createdAt,
                last_login_at=user.lastLoginAt
            )
            
        finally:
            await db.disconnect()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve user")


@router.put("/profile", response_model=UserProfile, summary="Update profile")
async def update_user_profile(update_request: UpdateProfileRequest, request: Request):
    """
    Update the current user's profile.
    """
    try:
        # Extract and verify token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization token")
        
        token = auth_header.split(" ")[1]
        auth_service = get_auth_service()
        payload = auth_service.validate_jwt_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_id = payload.get("sub")
        
        # Connect to database
        db = DatabaseService()
        await db.connect()
        
        try:
            # Build update data
            update_data = {}
            if update_request.username:
                # Check if username is taken
                existing = await db.prisma.user.find_first(
                    where={
                        "username": update_request.username,
                        "NOT": {"id": user_id}
                    }
                )
                if existing:
                    raise HTTPException(status_code=400, detail="Username already taken")
                update_data["username"] = update_request.username
            
            if update_request.email is not None:
                update_data["email"] = update_request.email
            if update_request.bio is not None:
                update_data["bio"] = update_request.bio
            if update_request.profile_picture is not None:
                update_data["profilePicture"] = update_request.profile_picture
            
            # Update user
            updated_user = await db.prisma.user.update(
                where={"id": user_id},
                data=update_data
            )
            
            logger.info(f"User profile updated: {updated_user.username}")
            
            return UserProfile(
                id=updated_user.id,
                username=updated_user.username,
                wallet_address=updated_user.walletAddress,
                email=updated_user.email,
                bio=updated_user.bio,
                profile_picture=updated_user.profilePicture,
                role=updated_user.role,
                onboarding_complete=updated_user.onboardingComplete,
                created_at=updated_user.createdAt,
                last_login_at=updated_user.lastLoginAt
            )
            
        finally:
            await db.disconnect()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.post("/onboarding/complete", response_model=AuthResponse, summary="Complete onboarding")
async def complete_onboarding(onboarding_request: CompleteOnboardingRequest, request: Request):
    """
    Mark user onboarding as complete after they've accepted terms and configured preferences.
    """
    try:
        if not onboarding_request.accepted_terms:
            raise HTTPException(status_code=400, detail="Must accept terms of service")
        
        # Extract and verify token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization token")
        
        token = auth_header.split(" ")[1]
        auth_service = get_auth_service()
        payload = auth_service.validate_jwt_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_id = payload.get("sub")
        
        # Connect to database
        db = DatabaseService()
        await db.connect()
        
        try:
            # Update user onboarding status
            updated_user = await db.prisma.user.update(
                where={"id": user_id},
                data={"onboardingComplete": True}
            )
            
            logger.info(f"User completed onboarding: {updated_user.username}")
            
            return AuthResponse(
                success=True,
                message="Onboarding completed successfully",
                user=UserProfile(
                    id=updated_user.id,
                    username=updated_user.username,
                    wallet_address=updated_user.walletAddress,
                    email=updated_user.email,
                    bio=updated_user.bio,
                    profile_picture=updated_user.profilePicture,
                    role=updated_user.role,
                    onboarding_complete=True,
                    created_at=updated_user.createdAt,
                    last_login_at=updated_user.lastLoginAt
                ),
                onboarding_complete=True
            )
            
        finally:
            await db.disconnect()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete onboarding error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to complete onboarding")


@router.post("/logout", summary="Logout user")
async def logout_user(request: Request):
    """
    Logout the current user and invalidate their session.
    """
    try:
        # Extract token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"success": True, "message": "Already logged out"}
        
        token = auth_header.split(" ")[1]
        
        # Verify token
        auth_service = get_auth_service()
        payload = auth_service.validate_jwt_token(token)
        if payload:
            user_id = payload.get("sub")
            
            # Connect to database
            db = DatabaseService()
            await db.connect()
            
            try:
                # Delete session
                await db.prisma.session.delete_many(
                    where={"token": token}
                )
                
                logger.info(f"User logged out: {user_id}")
                
            finally:
                await db.disconnect()
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        return {"success": True, "message": "Logged out"}
