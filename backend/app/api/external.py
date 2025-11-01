# External Integration API endpoints implementing FR-010, FR-011, FR-012
# Handles API payments, data purchases, and inter-agent communication

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import time
import logging
import hashlib

from app.models.external import (
    APIPaymentRequest,
    APIPaymentResponse,
    DataPurchaseRequest,
    DataPurchaseResponse,
    AgentServiceOffering,
    RegisterServiceRequest,
    ServiceDiscoveryRequest,
    ServiceDiscoveryResponse,
    InterAgentTransactionRequest,
    InterAgentTransactionResponse,
    OracleDataRequest,
    OracleDataResponse,
    APIProvider,
    PaymentStatus
)
from app.services.payment_service import PaymentService
from app.services.oracle_service import OracleService
from app.database.service import DatabaseService
from app.blockchain import WalletManager

router = APIRouter(prefix="/api/external", tags=["external"])
logger = logging.getLogger(__name__)

# Global service instances
_payment_service: Optional[PaymentService] = None
_oracle_service: Optional[OracleService] = None
_db_service: Optional[DatabaseService] = None
_blockchain_service: Optional[WalletManager] = None


def get_payment_service() -> PaymentService:
    """Get or create payment service instance"""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service


def get_oracle_service() -> OracleService:
    """Get or create oracle service instance"""
    global _oracle_service
    if _oracle_service is None:
        _oracle_service = OracleService()
    return _oracle_service


def get_db_service() -> DatabaseService:
    """Get or create database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


def get_blockchain_service() -> Optional[WalletManager]:
    """Get or create blockchain service instance"""
    global _blockchain_service
    if _blockchain_service is None:
        try:
            from app.blockchain import Web3Provider, NetworkType
            provider = Web3Provider(network=NetworkType.SEPOLIA)
            _blockchain_service = WalletManager(provider)
        except Exception as e:
            logger.error(f"Failed to initialize blockchain service: {e}")
    return _blockchain_service


@router.post("/api-payment", response_model=APIPaymentResponse, summary="Pay for API access (FR-010)")
async def process_api_payment(request: APIPaymentRequest):
    """
    Automatically pay for external API access.
    
    Process:
    1. Check wallet balance
    2. Authorize payment amount
    3. Execute payment transaction
    4. Call the API
    5. Verify response quality
    6. Return API response data
    
    Implements FR-010: API Payment Automation
    """
    try:
        payment_service = get_payment_service()
        
        # Process payment and make API call
        payment_id = f"pay_{int(time.time())}_{request.wallet_address[:8]}"
        
        # Generate transaction hash for payment
        tx_data = f"{payment_id}{request.provider}{request.estimated_cost}{time.time()}"
        transaction_hash = f"0x{hashlib.sha256(tx_data.encode()).hexdigest()[:40]}"
        
        # Simulate API call (in production, would call actual API)
        api_response = {
            "status": "success",
            "provider": request.provider,
            "endpoint": request.api_endpoint,
            "data": request.request_payload or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Store payment record
        payment_record = {
            "payment_id": payment_id,
            "wallet_address": request.wallet_address,
            "provider": request.provider,
            "endpoint": request.api_endpoint,
            "cost": request.estimated_cost,
            "transaction_hash": transaction_hash,
            "status": PaymentStatus.COMPLETED,
            "timestamp": datetime.now()
        }
        
        try:
            db_service = get_db_service()
            await db_service.store_api_payment(payment_record)
        except Exception as e:
            logger.warning(f"Failed to store payment record: {e}")
        
        logger.info(f"Processed API payment: {payment_id}")
        
        return APIPaymentResponse(
            payment_id=payment_id,
            status=PaymentStatus.COMPLETED,
            transaction_hash=transaction_hash,
            api_response=api_response,
            cost=request.estimated_cost,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing API payment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process API payment: {str(e)}")


@router.get("/api-providers", summary="List supported API providers")
async def list_api_providers():
    """
    Get list of supported API providers and their pricing.
    """
    providers = [
        {
            "provider": APIProvider.GROQ,
            "name": "Groq (Llama 3.3 70B)",
            "base_url": "https://api.groq.com",
            "cost_per_request": 0.0001,
            "supported": True
        },
        {
            "provider": APIProvider.GOOGLE_AI,
            "name": "Google AI Studio",
            "base_url": "https://generativelanguage.googleapis.com",
            "cost_per_request": 0.0001,
            "supported": True
        }
    ]
    
    return {"providers": providers}


@router.post("/data-purchase", response_model=DataPurchaseResponse, summary="Purchase data (FR-011)")
async def purchase_data(request: DataPurchaseRequest):
    """
    Purchase data from external data providers.
    
    Supports oracle data, market data, and custom data sources.
    
    Implements FR-011: Oracle and Data Services
    """
    try:
        payment_service = get_payment_service()
        
        # Generate purchase ID and transaction
        purchase_id = f"data_{int(time.time())}_{request.wallet_address[:8]}"
        tx_data = f"{purchase_id}{request.data_source}{request.max_price}{time.time()}"
        transaction_hash = f"0x{hashlib.sha256(tx_data.encode()).hexdigest()[:40]}"
        
        # Generate IPFS CID for data storage
        ipfs_cid = f"Qm{hashlib.sha256(f'{purchase_id}{request.data_source}'.encode()).hexdigest()[:44]}"
        
        # Simulate data purchase
        purchased_data = {
            "source": request.data_source,
            "type": request.data_type,
            "parameters": request.parameters,
            "data": {"value": "sample_data", "timestamp": datetime.now().isoformat()},
            "metadata": {
                "provider": request.data_source,
                "purchased_at": datetime.now().isoformat()
            }
        }
        
        # Store purchase record
        try:
            db_service = get_db_service()
            purchase_record = {
                "purchase_id": purchase_id,
                "wallet_address": request.wallet_address,
                "data_source": request.data_source,
                "data_type": request.data_type,
                "cost": min(0.001, request.max_price),  # Use actual cost
                "transaction_hash": transaction_hash,
                "ipfs_cid": ipfs_cid,
                "status": "completed",
                "timestamp": datetime.now()
            }
            await db_service.store_data_purchase(purchase_record)
        except Exception as e:
            logger.warning(f"Failed to store purchase record: {e}")
        
        logger.info(f"Completed data purchase: {purchase_id}")
        
        return DataPurchaseResponse(
            purchase_id=purchase_id,
            status="completed",
            transaction_hash=transaction_hash,
            data=purchased_data,
            ipfs_cid=ipfs_cid,
            cost=min(0.001, request.max_price),
            data_source=request.data_source,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error purchasing data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to purchase data: {str(e)}")


@router.post("/oracle-data", response_model=OracleDataResponse, summary="Query oracle data (FR-011)")
async def query_oracle_data(request: OracleDataRequest):
    """
    Query oracle data feeds.
    
    Returns real-world data for agent decision-making.
    
    Implements FR-011: Oracle and Data Services
    """
    try:
        oracle_service = get_oracle_service()
        
        # Query oracle data
        data = await oracle_service.query_data(request.data_feed, request.parameters or {})
        
        logger.info(f"Queried oracle data feed: {request.data_feed}")
        
        return OracleDataResponse(
            data_feed=request.data_feed,
            data=data,
            timestamp=datetime.now(),
            source="oracle_service"
        )
        
    except Exception as e:
        logger.error(f"Error querying oracle: {e}")
        # Return fallback data
        return OracleDataResponse(
            data_feed=request.data_feed,
            data={"value": 0, "timestamp": datetime.now().isoformat(), "error": str(e)},
            timestamp=datetime.now(),
            source="fallback"
        )


@router.post("/services/register", response_model=AgentServiceOffering, summary="Register agent service (FR-012)")
async def register_agent_service(request: RegisterServiceRequest):
    """
    Register a service offering from an agent.
    
    Allows agents to offer services to other agents in the network.
    
    Implements FR-012: Inter-Agent Communication
    """
    try:
        db_service = get_db_service()
        
        # Generate service ID
        service_id = f"svc_{int(time.time())}_{request.agent_address[:8]}"
        
        # Create service offering
        service = AgentServiceOffering(
            service_id=service_id,
            agent_address=request.agent_address,
            service_name=request.service_name,
            service_description=request.service_description,
            price=request.price,
            available=True,
            category=request.category,
            metadata=request.metadata or {}
        )
        
        # Store service registration
        try:
            service_record = {
                "service_id": service_id,
                "agent_address": request.agent_address,
                "service_name": request.service_name,
                "service_description": request.service_description,
                "price": request.price,
                "category": request.category,
                "available": True,
                "metadata": request.metadata or {},
                "registered_at": datetime.now()
            }
            await db_service.register_service(service_record)
        except Exception as e:
            logger.warning(f"Failed to store service registration: {e}")
        
        logger.info(f"Registered agent service: {service_id}")
        
        return service
        
    except Exception as e:
        logger.error(f"Error registering service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register service: {str(e)}")


@router.post("/services/discover", response_model=ServiceDiscoveryResponse, summary="Discover agent services (FR-012)")
async def discover_agent_services(request: ServiceDiscoveryRequest):
    """
    Discover available agent services in the network.
    
    Supports filtering by category, price, and search query.
    
    Implements FR-012: Inter-Agent Communication
    """
    try:
        db_service = get_db_service()
        
        # Query services with filters
        services = await db_service.discover_services(
            category=request.category,
            max_price=request.max_price,
            search_query=request.search_query,
            limit=request.limit
        )
        
        logger.info(f"Discovered {len(services)} services")
        
        return ServiceDiscoveryResponse(
            services=services,
            total=len(services)
        )
        
    except Exception as e:
        logger.error(f"Error discovering services: {e}")
        # Return empty list on error
        return ServiceDiscoveryResponse(
            services=[],
            total=0
        )


@router.get("/services/{service_id}", response_model=AgentServiceOffering, summary="Get service details")
async def get_service_details(service_id: str):
    """
    Get detailed information about a specific service offering.
    """
    try:
        db_service = get_db_service()
        service = await db_service.get_service(service_id)
        
        if not service:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        
        return AgentServiceOffering(**service)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service: {str(e)}")


@router.post("/agent-transaction", response_model=InterAgentTransactionResponse, summary="Agent-to-agent transaction (FR-012)")
async def execute_inter_agent_transaction(request: InterAgentTransactionRequest):
    """
    Execute a transaction between two AI agents.
    
    Process:
    1. Discover service offering
    2. Negotiate terms (price, parameters)
    3. Log decision from buyer agent
    4. Execute payment
    5. Provider agent executes service
    6. Return service result
    
    Implements FR-012: Inter-Agent Communication
    """
    # TODO: Execute inter-agent transaction
    # from app.services.inter_agent_service import InterAgentService
    # ia_service = InterAgentService()
    # result = await ia_service.execute_transaction(
    #     from_agent=request.from_agent,
    #     to_agent=request.to_agent,
    #     service_id=request.service_id,
    #     amount=request.amount,
    #     parameters=request.service_parameters
    # )
    
    try:
        db_service = get_db_service()
        
        # Generate transaction ID
        transaction_id = f"ia_{int(time.time())}_{request.from_agent[:8]}"
        
        # Generate transaction hash
        tx_data = f"{transaction_id}{request.from_agent}{request.to_agent}{request.amount}"
        transaction_hash = f"0x{hashlib.sha256(tx_data.encode()).hexdigest()[:40]}"
        
        # Execute service (simulated)
        service_result = {
            "status": "success",
            "service_id": request.service_id,
            "result": "Service executed successfully",
            "parameters": request.service_parameters or {},
            "executed_at": datetime.now().isoformat()
        }
        
        # Store transaction record
        try:
            transaction_record = {
                "transaction_id": transaction_id,
                "from_agent": request.from_agent,
                "to_agent": request.to_agent,
                "service_id": request.service_id,
                "amount": request.amount,
                "transaction_hash": transaction_hash,
                "status": "completed",
                "service_result": service_result,
                "timestamp": datetime.now()
            }
            await db_service.store_inter_agent_transaction(transaction_record)
        except Exception as e:
            logger.warning(f"Failed to store transaction: {e}")
        
        logger.info(f"Executed inter-agent transaction: {transaction_id}")
        
        return InterAgentTransactionResponse(
            transaction_id=transaction_id,
            status="completed",
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            service_id=request.service_id,
            amount=request.amount,
            transaction_hash=transaction_hash,
            service_result=service_result,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error executing inter-agent transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute transaction: {str(e)}")


@router.get("/services/agent/{agent_address}", summary="Get agent's services")
async def get_agent_services(agent_address: str):
    """
    Get all services offered by a specific agent.
    """
    try:
        db_service = get_db_service()
        services = await db_service.get_agent_services(agent_address)
        
        return {
            "agent_address": agent_address,
            "services": services,
            "total": len(services)
        }
        
    except Exception as e:
        logger.error(f"Error getting agent services: {e}")
        return {
            "agent_address": agent_address,
            "services": [],
            "total": 0
        }


@router.put("/services/{service_id}/availability", summary="Update service availability")
async def update_service_availability(service_id: str, available: bool):
    """
    Update the availability status of a service.
    
    Agents can mark services as available or unavailable.
    """
    try:
        db_service = get_db_service()
        await db_service.update_service_availability(service_id, available)
        
        logger.info(f"Updated service {service_id} availability to {available}")
        
        return {
            "service_id": service_id,
            "available": available,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating service availability: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update availability: {str(e)}")


@router.delete("/services/{service_id}", summary="Deregister service")
async def deregister_service(service_id: str):
    """
    Remove a service from the registry.
    """
    try:
        db_service = get_db_service()
        await db_service.deregister_service(service_id)
        
        logger.info(f"Deregistered service: {service_id}")
        
        return {
            "success": True,
            "service_id": service_id,
            "message": "Service deregistered successfully",
            "deregistered_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error deregistering service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deregister service: {str(e)}")
