"""
Database configuration and models
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
from typing import Generator

from .config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Database models
class Workflow(Base):
    """PINN workflow model"""
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    domain_type = Column(String, nullable=False)  # heat_transfer, fluid_dynamics, etc.
    status = Column(String, default="pending")  # pending, training, completed, failed
    progress = Column(Float, default=0.0)
    
    # Problem configuration
    problem_config = Column(JSON)
    pinn_config = Column(JSON)
    
    # Results
    accuracy = Column(Float)
    training_time = Column(Float)
    model_path = Column(String)
    results_path = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String)

class TrainingJob(Base):
    """Training job model"""
    __tablename__ = "training_jobs"
    
    id = Column(String, primary_key=True, index=True)
    workflow_id = Column(String, nullable=False, index=True)
    worker_type = Column(String, default="cpu")  # cpu, gpu
    status = Column(String, default="queued")  # queued, running, completed, failed
    
    # Training metrics
    current_epoch = Column(Integer, default=0)
    total_epochs = Column(Integer)
    current_loss = Column(Float)
    best_loss = Column(Float)
    
    # Resource usage
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    gpu_usage = Column(Float)
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    estimated_completion = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Model(Base):
    """Trained model model"""
    __tablename__ = "models"
    
    id = Column(String, primary_key=True, index=True)
    workflow_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    version = Column(String, default="1.0.0")
    
    # Model metadata
    architecture = Column(JSON)
    parameters_count = Column(Integer)
    model_size_mb = Column(Float)
    accuracy = Column(Float)
    
    # Storage
    storage_path = Column(String, nullable=False)
    metadata_path = Column(String)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deployed = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class InferenceRequest(Base):
    """Inference request model"""
    __tablename__ = "inference_requests"
    
    id = Column(String, primary_key=True, index=True)
    model_id = Column(String, nullable=False, index=True)
    workflow_id = Column(String, nullable=False, index=True)
    
    # Request data
    input_data = Column(JSON)
    output_data = Column(JSON)
    
    # Performance metrics
    inference_time_ms = Column(Float)
    input_size = Column(Integer)
    output_size = Column(Integer)
    
    # Status
    status = Column(String, default="pending")  # pending, completed, failed
    error_message = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)

# Database dependency
def get_db() -> Generator:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
async def create_tables():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)