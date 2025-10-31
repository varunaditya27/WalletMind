# WebSocket endpoints for real-time monitoring implementing FR-009
# Provides real-time updates for agent decisions, transactions, and verification

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
from datetime import datetime

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "agents": set(),
            "transactions": set(),
            "decisions": set(),
            "verification": set(),
        }

    async def connect(self, websocket: WebSocket, channel: str = "agents"):
        """Register a new WebSocket connection (accept must be called before)"""
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str = "agents"):
        """Remove a WebSocket connection"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
    
    async def broadcast(self, message: dict, channel: str = "all"):
        """Broadcast message to all connections in a channel"""
        if channel not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        dead_connections = set()
        
        for connection in set(self.active_connections[channel]):
            try:
                await connection.send_text(message_json)
            except Exception:
                dead_connections.add(connection)

        for connection in dead_connections:
            self.disconnect(connection, channel)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            pass


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for all real-time updates.
    
    Implements FR-009: Real-Time Verification Dashboard
    """
    await websocket.accept()
    channels = {
        "agents": False,
        "transactions": False,
        "decisions": False,
        "verification": False,
    }
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.now().isoformat(),
            "channels": ["agents", "transactions", "decisions", "verification"]
        }, websocket)
        
        while True:
            # Receive messages from client (e.g., subscribe to specific channels)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "subscribe":
                channel = message.get("channel", "agents")
                if channel not in channels:
                    await manager.send_personal_message({
                        "type": "subscription",
                        "channel": channel,
                        "status": "unsupported",
                    }, websocket)
                    continue

                if not channels[channel]:
                    await manager.connect(websocket, channel)
                    channels[channel] = True
                await manager.send_personal_message({
                    "type": "subscription",
                    "channel": channel,
                    "status": "subscribed"
                }, websocket)
            
            elif message.get("action") == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
    
    except WebSocketDisconnect:
        for channel, subscribed in channels.items():
            if subscribed:
                manager.disconnect(websocket, channel)


@router.websocket("/ws/agents")
async def agent_updates(websocket: WebSocket):
    """
    WebSocket endpoint for agent activity updates.
    
    Broadcasts:
    - Agent status changes
    - Decision-making progress
    - Agent health metrics
    """
    await websocket.accept()
    await manager.connect(websocket, "agents")
    
    try:
        while True:
            data = await websocket.receive_text()
            # Echo for now (client-side messages)
            await manager.send_personal_message({
                "type": "agent_update",
                "echo": data
            }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, "agents")


@router.websocket("/ws/transactions")
async def transaction_updates(websocket: WebSocket):
    """
    WebSocket endpoint for transaction updates.
    
    Broadcasts:
    - Transaction submitted
    - Transaction confirmed
    - Transaction failed
    - Gas price updates
    """
    await websocket.accept()
    await manager.connect(websocket, "transactions")
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message({
                "type": "transaction_update",
                "echo": data
            }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, "transactions")


@router.websocket("/ws/decisions")
async def decision_updates(websocket: WebSocket):
    """
    WebSocket endpoint for decision logging updates.
    
    Broadcasts:
    - Decision logged
    - Decision approved
    - Decision executed
    - Decision verification results
    """
    await websocket.accept()
    await manager.connect(websocket, "decisions")
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message({
                "type": "decision_update",
                "echo": data
            }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, "decisions")


@router.websocket("/ws/verification")
async def verification_updates(websocket: WebSocket):
    """
    WebSocket endpoint for verification updates.
    
    Broadcasts:
    - Verification checks performed
    - Integrity results
    - Provenance chain updates
    """
    await websocket.accept()
    await manager.connect(websocket, "verification")
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message({
                "type": "verification_update",
                "echo": data
            }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, "verification")


# Helper functions for broadcasting events from other parts of the app

async def broadcast_agent_event(event_type: str, data: dict):
    """Broadcast an agent event to all subscribed clients"""
    message = {
        "type": "agent_event",
        "event": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message, "agents")


async def broadcast_transaction_event(event_type: str, data: dict):
    """Broadcast a transaction event to all subscribed clients"""
    message = {
        "type": "transaction_event",
        "event": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message, "transactions")


async def broadcast_decision_event(event_type: str, data: dict):
    """Broadcast a decision event to all subscribed clients"""
    message = {
        "type": "decision_event",
        "event": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message, "decisions")


async def broadcast_verification_event(event_type: str, data: dict):
    """Broadcast a verification event to all subscribed clients"""
    message = {
        "type": "verification_event",
        "event": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message, "verification")

