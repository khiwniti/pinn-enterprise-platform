"""
Database models for workers
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Workflow(Base):
    """PINN workflow model"""
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    domain_type = Column(String, nullable=False)
    status = Column(String, default="pending")
    progress = Column(Float, default=0.0)
    
    problem_config = Column(JSON)
    pinn_config = Column(JSON)
    
    accuracy = Column(Float)
    training_time = Column(Float)
    model_path = Column(String)
    results_path = Column(String)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String)

class TrainingJob(Base):
    """Training job model"""
    __tablename__ = "training_jobs"
    
    id = Column(String, primary_key=True, index=True)
    workflow_id = Column(String, nullable=False, index=True)
    worker_type = Column(String, default="cpu")
    status = Column(String, default="queued")
    
    current_epoch = Column(Integer, default=0)
    total_epochs = Column(Integer)
    current_loss = Column(Float)
    best_loss = Column(Float)
    
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    gpu_usage = Column(Float)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    estimated_completion = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Model(Base):
    """Trained model model"""
    __tablename__ = "models"
    
    id = Column(String, primary_key=True, index=True)
    workflow_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    version = Column(String, default="1.0.0")
    
    architecture = Column(JSON)
    parameters_count = Column(Integer)
    model_size_mb = Column(Float)
    accuracy = Column(Float)
    
    storage_path = Column(String, nullable=False)
    metadata_path = Column(String)
    
    is_active = Column(Boolean, default=True)
    is_deployed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())