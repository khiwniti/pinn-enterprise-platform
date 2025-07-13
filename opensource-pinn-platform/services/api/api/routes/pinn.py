"""
PINN API routes for problem solving and model management
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db, Workflow, TrainingJob
from core.redis_client import redis_client
from tasks.pinn_tasks import start_pinn_training

router = APIRouter()

# Pydantic models
class PINNProblemRequest(BaseModel):
    """Request model for PINN problem solving"""
    name: str
    description: str
    domain_type: str  # heat_transfer, fluid_dynamics, structural, electromagnetics
    geometry: Dict[str, Any]
    boundary_conditions: Dict[str, Any]
    initial_conditions: Optional[Dict[str, Any]] = None
    physics_parameters: Dict[str, Any]
    accuracy_requirements: float = 0.95
    max_training_time: int = 3600
    real_time_inference: bool = True

class PINNProblemResponse(BaseModel):
    """Response model for PINN problem submission"""
    workflow_id: str
    status: str
    estimated_completion_time: int
    endpoints: Dict[str, str]

class WorkflowStatus(BaseModel):
    """Workflow status response"""
    workflow_id: str
    name: str
    status: str
    progress: float
    accuracy: Optional[float] = None
    training_time: Optional[float] = None
    created_at: datetime
    updated_at: datetime

@router.post("/solve", response_model=PINNProblemResponse)
async def solve_pinn_problem(
    request: PINNProblemRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a PINN problem for solving
    """
    try:
        # Generate workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Create workflow record
        workflow = Workflow(
            id=workflow_id,
            name=request.name,
            description=request.description,
            domain_type=request.domain_type,
            status="pending",
            problem_config={
                "geometry": request.geometry,
                "boundary_conditions": request.boundary_conditions,
                "initial_conditions": request.initial_conditions,
                "physics_parameters": request.physics_parameters,
                "accuracy_requirements": request.accuracy_requirements,
                "max_training_time": request.max_training_time,
                "real_time_inference": request.real_time_inference
            }
        )
        
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        
        # Queue training task
        background_tasks.add_task(
            queue_training_task,
            workflow_id,
            request.dict()
        )
        
        return PINNProblemResponse(
            workflow_id=workflow_id,
            status="pending",
            estimated_completion_time=request.max_training_time,
            endpoints={
                "status": f"/api/v1/pinn/status/{workflow_id}",
                "results": f"/api/v1/pinn/results/{workflow_id}",
                "inference": f"/api/v1/pinn/inference/{workflow_id}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{workflow_id}", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str, db: Session = Depends(get_db)):
    """
    Get the status of a PINN workflow
    """
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return WorkflowStatus(
            workflow_id=workflow.id,
            name=workflow.name,
            status=workflow.status,
            progress=workflow.progress,
            accuracy=workflow.accuracy,
            training_time=workflow.training_time,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{workflow_id}")
async def get_workflow_results(workflow_id: str, db: Session = Depends(get_db)):
    """
    Get the results of a completed PINN workflow
    """
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status != "completed":
            raise HTTPException(status_code=202, detail="Workflow not completed yet")
        
        # Get results from cache or storage
        results = await redis_client.get(f"results:{workflow_id}")
        
        if not results:
            # Load from MinIO if not in cache
            from core.minio_client import minio_client
            results = minio_client.download_json(f"results/{workflow_id}/results.json")
        
        if not results:
            raise HTTPException(status_code=404, detail="Results not found")
        
        return {
            "workflow_id": workflow_id,
            "status": workflow.status,
            "accuracy": workflow.accuracy,
            "training_time": workflow.training_time,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inference/{workflow_id}")
async def run_inference(
    workflow_id: str,
    inference_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Run inference on a trained PINN model
    """
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status != "completed":
            raise HTTPException(status_code=400, detail="Model not ready for inference")
        
        # Queue inference task
        task_id = str(uuid.uuid4())
        
        await redis_client.lpush(
            "inference_queue",
            {
                "task_id": task_id,
                "workflow_id": workflow_id,
                "inference_data": inference_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "task_id": task_id,
            "status": "queued",
            "estimated_time": "5-30 seconds"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domains")
async def get_supported_domains():
    """
    Get list of supported physics domains
    """
    return {
        "domains": [
            {
                "id": "heat_transfer",
                "name": "Heat Transfer",
                "description": "Steady-state and transient heat conduction problems",
                "equations": ["Heat equation", "Fourier's law"],
                "examples": [
                    "2D heat conduction in square domain",
                    "Transient heat transfer in rod",
                    "Heat exchanger analysis"
                ]
            },
            {
                "id": "fluid_dynamics",
                "name": "Fluid Dynamics",
                "description": "Incompressible Navier-Stokes equations",
                "equations": ["Continuity equation", "Momentum equations"],
                "examples": [
                    "Lid-driven cavity flow",
                    "Flow around cylinder",
                    "Poiseuille flow"
                ]
            },
            {
                "id": "structural_mechanics",
                "name": "Structural Mechanics",
                "description": "Linear and nonlinear elasticity",
                "equations": ["Equilibrium equations", "Constitutive relations"],
                "examples": [
                    "Cantilever beam analysis",
                    "Plate with hole",
                    "Vibration analysis"
                ]
            },
            {
                "id": "electromagnetics",
                "name": "Electromagnetics",
                "description": "Maxwell's equations and electromagnetic fields",
                "equations": ["Maxwell's equations", "Wave equation"],
                "examples": [
                    "Electrostatic field",
                    "Magnetic field",
                    "Wave propagation"
                ]
            }
        ]
    }

@router.delete("/workflow/{workflow_id}")
async def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """
    Delete a workflow and its associated data
    """
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Delete from database
        db.delete(workflow)
        
        # Delete training jobs
        training_jobs = db.query(TrainingJob).filter(TrainingJob.workflow_id == workflow_id).all()
        for job in training_jobs:
            db.delete(job)
        
        db.commit()
        
        # Delete from cache
        await redis_client.delete(f"results:{workflow_id}")
        await redis_client.delete(f"status:{workflow_id}")
        
        # Delete from storage (background task)
        from core.minio_client import minio_client
        objects = minio_client.list_objects(f"models/{workflow_id}/")
        for obj in objects:
            minio_client.delete_object(obj)
        
        return {"message": "Workflow deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def queue_training_task(workflow_id: str, problem_config: Dict[str, Any]):
    """
    Queue a training task in Redis
    """
    try:
        task_data = {
            "workflow_id": workflow_id,
            "problem_config": problem_config,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await redis_client.lpush("training_queue", task_data)
        
        # Update workflow status
        await redis_client.set(
            f"status:{workflow_id}",
            {"status": "queued", "progress": 0},
            expire=86400  # 24 hours
        )
        
    except Exception as e:
        print(f"Failed to queue training task: {e}")
        raise