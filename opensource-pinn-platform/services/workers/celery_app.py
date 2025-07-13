"""
Celery application for PINN training workers
"""

import os
from celery import Celery

# Configure Celery
celery_app = Celery(
    "pinn_workers",
    broker=os.getenv("REDIS_URL", "redis://:secure123@redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://:secure123@redis:6379/0"),
    include=["tasks.pinn_training", "tasks.inference", "tasks.maintenance"]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "tasks.pinn_training.train_pinn_model": {"queue": "training"},
        "tasks.inference.run_inference": {"queue": "inference"},
        "tasks.maintenance.cleanup_old_models": {"queue": "maintenance"},
    },
    
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # Result backend
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-models": {
            "task": "tasks.maintenance.cleanup_old_models",
            "schedule": 3600.0,  # Every hour
        },
        "update-system-metrics": {
            "task": "tasks.maintenance.update_system_metrics",
            "schedule": 60.0,  # Every minute
        },
    },
)

if __name__ == "__main__":
    celery_app.start()