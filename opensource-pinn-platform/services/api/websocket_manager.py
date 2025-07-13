"""
WebSocket Manager for Real-time PINN Workflow Updates
Provides live updates for training progress, metrics, and visualizations
"""

import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.workflow_subscribers: Dict[str, List[str]] = {}  # workflow_id -> [connection_ids]
        
    async def connect(self, websocket: WebSocket, connection_id: str = None) -> str:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if not connection_id:
            connection_id = str(uuid.uuid4())
            
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connection established: {connection_id}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
        # Remove from workflow subscriptions
        for workflow_id, subscribers in self.workflow_subscribers.items():
            if connection_id in subscribers:
                subscribers.remove(connection_id)
                
        logger.info(f"WebSocket connection closed: {connection_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_to_workflow(self, message: Dict[str, Any], workflow_id: str):
        """Send message to all connections subscribed to a workflow"""
        if workflow_id in self.workflow_subscribers:
            disconnected = []
            
            for connection_id in self.workflow_subscribers[workflow_id]:
                try:
                    await self.send_personal_message(message, connection_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
                    disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for conn_id in disconnected:
                self.disconnect(conn_id)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Send message to all active connections"""
        disconnected = []
        
        for connection_id in list(self.active_connections.keys()):
            try:
                await self.send_personal_message(message, connection_id)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for conn_id in disconnected:
            self.disconnect(conn_id)
    
    def subscribe_to_workflow(self, connection_id: str, workflow_id: str):
        """Subscribe a connection to workflow updates"""
        if workflow_id not in self.workflow_subscribers:
            self.workflow_subscribers[workflow_id] = []
            
        if connection_id not in self.workflow_subscribers[workflow_id]:
            self.workflow_subscribers[workflow_id].append(connection_id)
            logger.info(f"Connection {connection_id} subscribed to workflow {workflow_id}")
    
    def unsubscribe_from_workflow(self, connection_id: str, workflow_id: str):
        """Unsubscribe a connection from workflow updates"""
        if workflow_id in self.workflow_subscribers:
            if connection_id in self.workflow_subscribers[workflow_id]:
                self.workflow_subscribers[workflow_id].remove(connection_id)
                logger.info(f"Connection {connection_id} unsubscribed from workflow {workflow_id}")

# Global connection manager instance
manager = ConnectionManager()

class WorkflowUpdater:
    """Handles real-time workflow updates"""
    
    @staticmethod
    async def send_workflow_progress(workflow_id: str, step_index: int, progress: float, metrics: Dict[str, Any] = None):
        """Send workflow progress update"""
        message = {
            "type": "workflow_progress",
            "payload": {
                "workflow_id": workflow_id,
                "step_index": step_index,
                "progress": progress,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await manager.broadcast_to_workflow(message, workflow_id)
    
    @staticmethod
    async def send_training_metrics(workflow_id: str, metrics: Dict[str, Any]):
        """Send real-time training metrics"""
        message = {
            "type": "training_metrics",
            "payload": {
                "workflow_id": workflow_id,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await manager.broadcast_to_workflow(message, workflow_id)
    
    @staticmethod
    async def send_step_completed(workflow_id: str, step_id: str, status: str, result: Any = None, duration: float = None):
        """Send step completion notification"""
        message = {
            "type": "step_completed",
            "payload": {
                "workflow_id": workflow_id,
                "step_id": step_id,
                "status": status,
                "result": result,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await manager.broadcast_to_workflow(message, workflow_id)
    
    @staticmethod
    async def send_visualization_ready(workflow_id: str, visualization_url: str, results: Any = None):
        """Send visualization ready notification"""
        message = {
            "type": "visualization_ready",
            "payload": {
                "workflow_id": workflow_id,
                "visualization_url": visualization_url,
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await manager.broadcast_to_workflow(message, workflow_id)
    
    @staticmethod
    async def send_error(workflow_id: str, error_message: str, step_id: str = None):
        """Send error notification"""
        message = {
            "type": "error",
            "payload": {
                "workflow_id": workflow_id,
                "error_message": error_message,
                "step_id": step_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await manager.broadcast_to_workflow(message, workflow_id)

class PINNTrainingSimulator:
    """Simulates real-time PINN training progress for demo"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.is_running = False
        
    async def simulate_training(self):
        """Simulate PINN training with real-time updates"""
        self.is_running = True
        
        steps = [
            {"id": "analyze", "name": "Problem Analysis", "duration": 5},
            {"id": "mesh", "name": "Mesh Generation", "duration": 8},
            {"id": "train", "name": "PINN Training", "duration": 45},
            {"id": "validate", "name": "Model Validation", "duration": 10},
            {"id": "visualize", "name": "Results Visualization", "duration": 7}
        ]
        
        for step_index, step in enumerate(steps):
            if not self.is_running:
                break
                
            # Start step
            await WorkflowUpdater.send_step_completed(
                self.workflow_id, step["id"], "running"
            )
            
            # Simulate step progress
            for progress in range(0, 101, 10):
                if not self.is_running:
                    break
                    
                # Generate realistic metrics for training step
                if step["id"] == "train":
                    metrics = {
                        "accuracy": min(0.99, 0.5 + (progress / 100) * 0.49),
                        "loss": max(0.001, 0.1 * (1 - progress / 100)),
                        "convergence": progress / 100,
                        "trainingTime": (progress / 100) * step["duration"]
                    }
                    
                    await WorkflowUpdater.send_training_metrics(
                        self.workflow_id, metrics
                    )
                
                await WorkflowUpdater.send_workflow_progress(
                    self.workflow_id, step_index, progress
                )
                
                await asyncio.sleep(step["duration"] / 10)  # Simulate time
            
            # Complete step
            if self.is_running:
                await WorkflowUpdater.send_step_completed(
                    self.workflow_id, step["id"], "completed", 
                    duration=step["duration"]
                )
        
        # Send final visualization
        if self.is_running:
            await WorkflowUpdater.send_visualization_ready(
                self.workflow_id,
                f"/visualizations/{self.workflow_id}/results.html",
                {"status": "completed", "accuracy": 0.984}
            )
    
    def stop(self):
        """Stop the simulation"""
        self.is_running = False

# Global training simulators
active_simulators: Dict[str, PINNTrainingSimulator] = {}

async def handle_websocket_message(websocket: WebSocket, connection_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages"""
    
    message_type = message.get("type")
    
    if message_type == "subscribe_workflow":
        workflow_id = message.get("workflow_id")
        if workflow_id:
            manager.subscribe_to_workflow(connection_id, workflow_id)
            await manager.send_personal_message({
                "type": "subscription_confirmed",
                "workflow_id": workflow_id
            }, connection_id)
    
    elif message_type == "unsubscribe_workflow":
        workflow_id = message.get("workflow_id")
        if workflow_id:
            manager.unsubscribe_from_workflow(connection_id, workflow_id)
    
    elif message_type == "start_simulation":
        workflow_id = message.get("workflow_id")
        if workflow_id and workflow_id not in active_simulators:
            simulator = PINNTrainingSimulator(workflow_id)
            active_simulators[workflow_id] = simulator
            
            # Start simulation in background
            asyncio.create_task(simulator.simulate_training())
            
            await manager.send_personal_message({
                "type": "simulation_started",
                "workflow_id": workflow_id
            }, connection_id)
    
    elif message_type == "pause_workflow":
        workflow_id = message.get("workflow_id")
        if workflow_id in active_simulators:
            active_simulators[workflow_id].stop()
            del active_simulators[workflow_id]
            
            await manager.send_personal_message({
                "type": "workflow_paused",
                "workflow_id": workflow_id
            }, connection_id)
    
    elif message_type == "get_status":
        # Send current system status
        await manager.send_personal_message({
            "type": "system_status",
            "payload": {
                "active_connections": len(manager.active_connections),
                "active_workflows": len(active_simulators),
                "timestamp": datetime.utcnow().isoformat()
            }
        }, connection_id)

async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint handler"""
    connection_id = None
    
    try:
        connection_id = await manager.connect(websocket)
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle message
            await handle_websocket_message(websocket, connection_id, message)
            
    except WebSocketDisconnect:
        if connection_id:
            manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if connection_id:
            manager.disconnect(connection_id)