"""
Monitoring and metrics API routes
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from core.database import get_db, Workflow, TrainingJob, InferenceRequest
from core.redis_client import redis_client

router = APIRouter()

class SystemMetrics(BaseModel):
    """System metrics model"""
    timestamp: datetime
    active_workflows: int
    queue_depth: int
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float] = None

class PerformanceMetrics(BaseModel):
    """Performance metrics model"""
    avg_training_time: float
    avg_accuracy: float
    success_rate: float
    total_workflows: int
    completed_workflows: int
    failed_workflows: int

@router.get("/health")
async def health_check():
    """
    Comprehensive health check
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "services": {},
            "metrics": {}
        }
        
        # Check database
        try:
            from core.database import get_db
            db = next(get_db())
            db.execute("SELECT 1")
            health_status["services"]["database"] = "up"
        except Exception as e:
            health_status["services"]["database"] = f"down: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check Redis
        try:
            await redis_client.ping()
            health_status["services"]["redis"] = "up"
        except Exception as e:
            health_status["services"]["redis"] = f"down: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check MinIO
        try:
            from core.minio_client import minio_client
            minio_client.bucket_exists("pinn-models")
            health_status["services"]["minio"] = "up"
        except Exception as e:
            health_status["services"]["minio"] = f"down: {str(e)}"
            health_status["status"] = "degraded"
        
        # Get basic metrics
        try:
            db = next(get_db())
            
            # Active workflows
            active_count = db.query(Workflow).filter(
                Workflow.status.in_(["pending", "training"])
            ).count()
            
            # Queue depth
            queue_depth = await redis_client.llen("training_queue")
            
            health_status["metrics"] = {
                "active_workflows": active_count,
                "queue_depth": queue_depth,
                "total_workflows": db.query(Workflow).count()
            }
            
        except Exception as e:
            health_status["metrics"]["error"] = str(e)
        
        return health_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/system")
async def get_system_metrics(db: Session = Depends(get_db)):
    """
    Get current system metrics
    """
    try:
        # Get active workflows
        active_workflows = db.query(Workflow).filter(
            Workflow.status.in_(["pending", "training"])
        ).count()
        
        # Get queue depth
        queue_depth = await redis_client.llen("training_queue")
        
        # Get resource usage (mock data - in production, integrate with actual monitoring)
        cpu_usage = 45.2  # Would come from system monitoring
        memory_usage = 67.8  # Would come from system monitoring
        gpu_usage = 23.4  # Would come from GPU monitoring
        
        return SystemMetrics(
            timestamp=datetime.utcnow(),
            active_workflows=active_workflows,
            queue_depth=queue_depth,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            gpu_usage=gpu_usage
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/performance")
async def get_performance_metrics(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get performance metrics for the specified time period
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get workflows in date range
        workflows = db.query(Workflow).filter(
            Workflow.created_at >= start_date,
            Workflow.created_at <= end_date
        ).all()
        
        if not workflows:
            return PerformanceMetrics(
                avg_training_time=0.0,
                avg_accuracy=0.0,
                success_rate=0.0,
                total_workflows=0,
                completed_workflows=0,
                failed_workflows=0
            )
        
        # Calculate metrics
        total_workflows = len(workflows)
        completed_workflows = len([w for w in workflows if w.status == "completed"])
        failed_workflows = len([w for w in workflows if w.status == "failed"])
        
        # Average training time (only for completed workflows)
        completed_with_time = [w for w in workflows if w.status == "completed" and w.training_time]
        avg_training_time = (
            sum(w.training_time for w in completed_with_time) / len(completed_with_time)
            if completed_with_time else 0.0
        )
        
        # Average accuracy (only for completed workflows)
        completed_with_accuracy = [w for w in workflows if w.status == "completed" and w.accuracy]
        avg_accuracy = (
            sum(w.accuracy for w in completed_with_accuracy) / len(completed_with_accuracy)
            if completed_with_accuracy else 0.0
        )
        
        # Success rate
        success_rate = completed_workflows / total_workflows if total_workflows > 0 else 0.0
        
        return PerformanceMetrics(
            avg_training_time=avg_training_time,
            avg_accuracy=avg_accuracy,
            success_rate=success_rate,
            total_workflows=total_workflows,
            completed_workflows=completed_workflows,
            failed_workflows=failed_workflows
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/training")
async def get_training_metrics(
    workflow_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get training metrics for workflows
    """
    try:
        query = db.query(TrainingJob)
        
        if workflow_id:
            query = query.filter(TrainingJob.workflow_id == workflow_id)
        
        # Get recent training jobs
        training_jobs = query.order_by(desc(TrainingJob.created_at)).limit(100).all()
        
        metrics = []
        for job in training_jobs:
            metrics.append({
                "job_id": job.id,
                "workflow_id": job.workflow_id,
                "worker_type": job.worker_type,
                "status": job.status,
                "current_epoch": job.current_epoch,
                "total_epochs": job.total_epochs,
                "current_loss": job.current_loss,
                "best_loss": job.best_loss,
                "cpu_usage": job.cpu_usage,
                "memory_usage": job.memory_usage,
                "gpu_usage": job.gpu_usage,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "duration": (
                    (job.completed_at - job.started_at).total_seconds()
                    if job.started_at and job.completed_at else None
                )
            })
        
        return {
            "training_jobs": metrics,
            "summary": {
                "total_jobs": len(training_jobs),
                "running_jobs": len([j for j in training_jobs if j.status == "running"]),
                "completed_jobs": len([j for j in training_jobs if j.status == "completed"]),
                "failed_jobs": len([j for j in training_jobs if j.status == "failed"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/inference")
async def get_inference_metrics(
    workflow_id: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get inference metrics
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=hours)
        
        query = db.query(InferenceRequest).filter(
            InferenceRequest.created_at >= start_date,
            InferenceRequest.created_at <= end_date
        )
        
        if workflow_id:
            query = query.filter(InferenceRequest.workflow_id == workflow_id)
        
        inference_requests = query.all()
        
        if not inference_requests:
            return {
                "total_requests": 0,
                "avg_inference_time": 0.0,
                "success_rate": 0.0,
                "requests_per_hour": 0.0
            }
        
        # Calculate metrics
        total_requests = len(inference_requests)
        successful_requests = len([r for r in inference_requests if r.status == "completed"])
        
        # Average inference time
        completed_requests = [r for r in inference_requests if r.inference_time_ms is not None]
        avg_inference_time = (
            sum(r.inference_time_ms for r in completed_requests) / len(completed_requests)
            if completed_requests else 0.0
        )
        
        # Success rate
        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
        
        # Requests per hour
        requests_per_hour = total_requests / hours
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": total_requests - successful_requests,
            "avg_inference_time_ms": avg_inference_time,
            "success_rate": success_rate,
            "requests_per_hour": requests_per_hour,
            "time_range_hours": hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/domains")
async def get_domain_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get metrics by physics domain
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get domain statistics
        domain_stats = db.query(
            Workflow.domain_type,
            func.count(Workflow.id).label("total"),
            func.count(func.nullif(Workflow.status != "completed", True)).label("completed"),
            func.avg(Workflow.accuracy).label("avg_accuracy"),
            func.avg(Workflow.training_time).label("avg_training_time")
        ).filter(
            Workflow.created_at >= start_date,
            Workflow.created_at <= end_date
        ).group_by(Workflow.domain_type).all()
        
        metrics = []
        for stat in domain_stats:
            success_rate = stat.completed / stat.total if stat.total > 0 else 0.0
            
            metrics.append({
                "domain": stat.domain_type,
                "total_workflows": stat.total,
                "completed_workflows": stat.completed,
                "success_rate": success_rate,
                "avg_accuracy": float(stat.avg_accuracy) if stat.avg_accuracy else 0.0,
                "avg_training_time": float(stat.avg_training_time) if stat.avg_training_time else 0.0
            })
        
        return {
            "domain_metrics": metrics,
            "time_range_days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/{workflow_id}")
async def get_workflow_logs(
    workflow_id: str,
    lines: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get logs for a specific workflow
    """
    try:
        # Check if workflow exists
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get logs from Redis (in production, might use ELK stack)
        logs = await redis_client.get(f"logs:{workflow_id}")
        
        if not logs:
            logs = []
        
        # Return last N lines
        if isinstance(logs, list):
            logs = logs[-lines:]
        
        return {
            "workflow_id": workflow_id,
            "logs": logs,
            "total_lines": len(logs) if isinstance(logs, list) else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))