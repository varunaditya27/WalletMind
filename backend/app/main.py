# Main FastAPI application for WalletMind backend
# Orchestrates all API endpoints, middleware, and WebSocket connections

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import logging
import os

# Import routers
from app.api import agents, wallet, transactions, decisions, verification, external, websocket, auth

# Import configuration
from app.config import get_settings

# Import services
from app.services import (
    get_verification_service,
    get_payment_service,
    get_oracle_service
)

# Import security
from app.security import (
    get_key_manager,
    get_crypto_service,
    get_auth_service
)

# Load configuration
settings = get_settings()

# Configure logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=getattr(logging, settings.monitoring.log_level.upper()),
    format=log_format
)
logger = logging.getLogger(__name__)

# Service registry for dependency injection
services = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup/shutdown)"""
    # Startup
    logger.info("🚀 WalletMind Backend starting up...")
    
    # Initialize Security Services (NFR-004, FR-007, NFR-006)
    logger.info("🔐 Initializing security services...")
    try:
        # Key Manager - Secure key management
        key_manager = get_key_manager(
            master_password=settings.security.master_password,
            key_rotation_days=settings.security.key_rotation_days,
            enable_key_rotation=settings.security.enable_key_rotation
        )
        services["key_manager"] = key_manager
        logger.info("✅ KeyManager initialized")
        
        # Crypto Service - Cryptographic operations
        crypto_service = get_crypto_service(
            nonce_validity_seconds=settings.security.nonce_validity_seconds
        )
        services["crypto"] = crypto_service
        logger.info("✅ CryptoService initialized")
        
        # Auth Service - Authentication and authorization
        auth_service = get_auth_service(
            jwt_secret=settings.security.jwt_secret,
            access_token_expiry_minutes=settings.security.access_token_expiry_minutes,
            refresh_token_expiry_days=settings.security.refresh_token_expiry_days
        )
        services["auth"] = auth_service
        logger.info("✅ AuthService initialized")
        
    except Exception as e:
        logger.error(f"❌ Error initializing security services: {e}")
        raise
    
    # Initialize Infrastructure Services (FR-007, FR-010, FR-011)
    logger.info("⚙️  Initializing infrastructure services...")
    try:
        # Verification Service - Decision provenance
        verification_service = get_verification_service()
        services["verification"] = verification_service
        logger.info("✅ VerificationService initialized")
        
        # Payment Service - API payment automation
        payment_service = get_payment_service()
        services["payment"] = payment_service
        logger.info("✅ PaymentService initialized")
        
        # Oracle Service - External data queries
        oracle_service = get_oracle_service(
            cache_ttl_seconds=settings.infrastructure.oracle_cache_ttl
        )
        services["oracle"] = oracle_service
        logger.info("✅ OracleService initialized")
        
    except Exception as e:
        logger.error(f"❌ Error initializing infrastructure services: {e}")
        raise
    
    # TODO: Initialize other services
    # - ChromaDB connection (Memory services)
    # - Blockchain provider connections
    # - IPFS client
    # - Database connections
    # - Cache (Redis)
    
    logger.info("✅ All services initialized successfully")
    
    # Store service registry in app state
    app.state.services = services
    
    yield
    
    # Shutdown
    logger.info("🛑 WalletMind Backend shutting down...")
    
    # Cleanup security services
    logger.info("🔐 Cleaning up security services...")
    try:
        # Clean up expired sessions and rate limits
        if "auth" in services:
            services["auth"].cleanup_expired()
            logger.info("✅ AuthService cleaned up")
        
        # Clear crypto nonce cache
        if "crypto" in services:
            logger.info("✅ CryptoService cleaned up")
        
        logger.info("✅ Security services cleanup complete")
        
    except Exception as e:
        logger.error(f"❌ Error during security cleanup: {e}")
    
    # Cleanup infrastructure services
    logger.info("⚙️  Cleaning up infrastructure services...")
    try:
        # Clear oracle cache
        if "oracle" in services:
            services["oracle"].clear_cache()
            logger.info("✅ OracleService cache cleared")
        
        logger.info("✅ Infrastructure services cleanup complete")
        
    except Exception as e:
        logger.error(f"❌ Error during infrastructure cleanup: {e}")
    
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WalletMind API",
    description="AI Agent Autonomous Wallet System - Backend API",
    version="1.0.0",
    docs_url="/api/docs" if settings.features.enable_swagger_docs else None,
    redoc_url="/api/redoc" if settings.features.enable_swagger_docs else None,
    openapi_url="/api/openapi.json" if settings.features.enable_swagger_docs else None,
    lifespan=lifespan,
    debug=settings.debug
)


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=settings.api.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if app.debug else "An error occurred"
        }
    )


# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(wallet.router)
app.include_router(transactions.router)
app.include_router(decisions.router)
app.include_router(verification.router)
app.include_router(external.router)
app.include_router(websocket.router)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time()
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "WalletMind API",
        "version": "1.0.0",
        "description": "AI Agent Autonomous Wallet System",
        "documentation": "/api/docs",
        "health": "/health",
        "websocket": "/ws",
        "endpoints": {
            "agents": "/api/agents",
            "wallet": "/api/wallet",
            "transactions": "/api/transactions",
            "decisions": "/api/decisions",
            "verification": "/api/verification",
            "external": "/api/external"
        }
    }


# API info endpoint
@app.get("/api", tags=["root"])
async def api_info():
    """
    Detailed API information and available endpoints.
    """
    return {
        "title": "WalletMind API",
        "version": "1.0.0",
        "features": {
            "FR-001": "LangChain Agent Orchestration",
            "FR-002": "Decision Logic Framework",
            "FR-003": "Memory and Context Management",
            "FR-004": "ERC-4337 Smart Account Integration",
            "FR-005": "Transaction Execution System",
            "FR-006": "Multi-Network Support",
            "FR-007": "Decision Provenance Logging",
            "FR-008": "On-Chain Audit Trail",
            "FR-009": "Real-Time Verification Dashboard",
            "FR-010": "API Payment Automation",
            "FR-011": "Oracle and Data Services",
            "FR-012": "Inter-Agent Communication"
        },
        "endpoints": {
            "agents": {
                "POST /api/agents/request": "Process agent request",
                "POST /api/agents/memory/query": "Query agent memory",
                "GET /api/agents/health": "Get agent health"
            },
            "wallet": {
                "POST /api/wallet/create": "Create new wallet",
                "POST /api/wallet/balance": "Check balance",
                "PUT /api/wallet/spending-limit": "Update spending limit"
            },
            "transactions": {
                "POST /api/transactions/execute": "Execute transaction",
                "POST /api/transactions/history": "Get transaction history",
                "GET /api/transactions/stats/{wallet}": "Get statistics"
            },
            "decisions": {
                "POST /api/decisions/log": "Log decision",
                "POST /api/decisions/verify": "Verify decision"
            },
            "verification": {
                "POST /api/verification/audit-trail": "Get audit trail",
                "GET /api/verification/statistics/autonomy": "Get autonomy stats"
            },
            "external": {
                "POST /api/external/api-payment": "Pay for API",
                "POST /api/external/data-purchase": "Purchase data",
                "POST /api/external/agent-transaction": "Agent-to-agent transaction"
            },
            "websocket": {
                "WS /ws": "General WebSocket",
                "WS /ws/agents": "Agent updates",
                "WS /ws/transactions": "Transaction updates",
                "WS /ws/decisions": "Decision updates"
            }
        },
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc",
            "openapi": "/api/openapi.json"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
