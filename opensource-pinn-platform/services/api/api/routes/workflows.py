"""
Workflow management API routes
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from core.database import get_db, Workflow, TrainingJob, Model

router = APIRouter()

class WorkflowSummary(BaseModel):
    """Workflow summary model"""
    id: str
    name: str
    domain_type: str
    status: str
    progress: float
    accuracy: Optional[float] = None
    training_time: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class WorkflowDetail(BaseModel):
    """Detailed workflow model"""
    id: str
    name: str
    description: Optional[str] = None
    domain_type: str
    status: str
    progress: float
    accuracy: Optional[float] = None
    training_time: Optional[float] = None
    problem_config: dict
    pinn_config: Optional[dict] = None
    model_path: Optional[str] = None
    results_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class TrainingJobSummary(BaseModel):
    """Training job summary model"""
    id: str
    workflow_id: str
    worker_type: str
    status: str
    current_epoch: Optional[int] = None
    total_epochs: Optional[int] = None
    current_loss: Optional[float] = None
    best_loss: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None

@router.get("/", response_model=List[WorkflowSummary])
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    domain_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List workflows with optional filtering
    """
    try:
        query = db.query(Workflow)
        
        # Apply filters
        if status:
            query = query.filter(Workflow.status == status)
        
        if domain_type:
            query = query.filter(Workflow.domain_type == domain_type)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(Workflow.created_at))
        
        # Apply pagination
        workflows = query.offset(skip).limit(limit).all()
        
        return [
            WorkflowSummary(
                id=w.id,
                name=w.name,
                domain_type=w.domain_type,
                status=w.status,
                progress=w.progress,
                accuracy=w.accuracy,
                training_time=w.training_time,
                created_at=w.created_at,
                updated_at=w.updated_at
            )
            for w in workflows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{workflow_id}", response_model=WorkflowDetail)
async def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """
    Get detailed workflow information
    """
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return WorkflowDetail(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            domain_type=workflow.domain_type,
            status=workflow.status,
            progress=workflow.progress,
            accuracy=workflow.accuracy,
            training_time=workflow.training_time,
            problem_config=workflow.problem_config or {},
            pinn_config=workflow.pinn_config,
            model_path=workflow.model_path,
            results_path=workflow.results_path,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{workflow_id}/training-jobs", response_model=List[TrainingJobSummary])
async def get_workflow_training_jobs(workflow_id: str, db: Session = Depends(get_db)):
    """
    Get training jobs for a workflow
    """
    try:
        # Check if workflow exists
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get training jobs
        jobs = db.query(TrainingJob).filter(
            TrainingJob.workflow_id == workflow_id
        ).order_by(desc(TrainingJob.created_at)).all()
        
        return [
            TrainingJobSummary(
                id=job.id,
                workflow_id=job.workflow_id,
                worker_type=job.worker_type,
                status=job.status,
                current_epoch=job.current_epoch,
                total_epochs=job.total_epochs,
                current_loss=job.current_loss,
                best_loss=job.best_loss,
                started_at=job.started_at,
                completed_at=job.completed_at,
                estimated_completion=job.estimated_completion
            )
            for job in jobs
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{workflow_id}/models")
async def get_workflow_models(workflow_id: str, db: Session = Depends(get_db)):
    """
    Get models for a workflow
    """
    try:
        # Check if workflow exists
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get models
        models = db.query(Model).filter(
            Model.workflow_id == workflow_id
        ).order_by(desc(Model.created_at)).all()
        
        return [
            {
                "id": model.id,
                "name": model.name,
                "version": model.version,
                "architecture": model.architecture,
                "parameters_count": model.parameters_count,
                "model_size_mb": model.model_size_mb,
                "accuracy": model.accuracy,
                "is_active": model.is_active,
                "is_deployed": model.is_deployed,
                "created_at": model.created_at,
                "updated_at": model.updated_at
            }
            for model in models
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{workflow_id}/stop")
async def stop_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """
    Stop a running workflow
    """
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status not in ["pending", "training"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot stop workflow in status: {workflow.status}"
            )
        
        # Update workflow status
        workflow.status = "stopped"
        workflow.updated_at = datetime.utcnow()
        
        # Stop associated training jobs
        training_jobs = db.query(TrainingJob).filter(
            TrainingJob.workflow_id == workflow_id,
            TrainingJob.status.in_(["queued", "running"])
        ).all()
        
        for job in training_jobs:
            job.status = "stopped"
            job.completed_at = datetime.utcnow()
        
        db.commit()
        
        # Send stop signal to workers (via Redis)
        from core.redis_client import redis_client
        await redis_client.publish(
            "workflow_control",
            {
                "action": "stop",
                "workflow_id": workflow_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {"message": "Workflow stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{workflow_id}/restart")
async def restart_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """
    Restart a failed or stopped workflow
    """
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status not in ["failed", "stopped"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot restart workflow in status: {workflow.status}"
            )
        
        # Reset workflow status
        workflow.status = "pending"
        workflow.progress = 0.0
        workflow.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Queue training task
        from core.redis_client import redis_client
        await redis_client.lpush(
            "training_queue",
            {
                "workflow_id": workflow_id,
                "problem_config": workflow.problem_config,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {"message": "Workflow restarted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_workflow_stats(db: Session = Depends(get_db)):
    """
    Get workflow statistics summary
    """
    try:
        # Count workflows by status
        status_counts = {}
        for status in ["pending", "training", "completed", "failed", "stopped"]:
            count = db.query(Workflow).filter(Workflow.status == status).count()
            status_counts[status] = count
        
        # Count workflows by domain
        domain_counts = {}
        for domain in ["heat_transfer", "fluid_dynamics", "structural_mechanics", "electromagnetics"]:
            count = db.query(Workflow).filter(Workflow.domain_type == domain).count()
            domain_counts[domain] = count
        
        # Get recent activity
        recent_workflows = db.query(Workflow).order_by(
            desc(Workflow.created_at)
        ).limit(10).all()
        
        return {
            "total_workflows": db.query(Workflow).count(),
            "status_distribution": status_counts,
            "domain_distribution": domain_counts,
            "recent_workflows": [
                {
                    "id": w.id,
                    "name": w.name,
                    "status": w.status,
                    "domain_type": w.domain_type,
                    "created_at": w.created_at
                }
                for w in recent_workflows
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))