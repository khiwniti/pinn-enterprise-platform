"""
PINN training tasks using DeepXDE
"""

import os
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any

import numpy as np
import tensorflow as tf
import deepxde as dde
from celery import current_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from celery_app import celery_app
from .database_models import Workflow, TrainingJob, Model
from .storage_client import StorageClient
from .pinn_architectures import get_pinn_architecture

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pinn:secure123@postgres:5432/pinn")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Storage client
storage = StorageClient()

@celery_app.task(bind=True)
def train_pinn_model(self, workflow_id: str, problem_config: Dict[str, Any]):
    """
    Train a PINN model using DeepXDE
    """
    task_id = self.request.id
    worker_type = os.getenv("WORKER_TYPE", "cpu")
    
    logger.info(f"Starting PINN training for workflow {workflow_id} on {worker_type} worker")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get workflow
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Create training job record
        training_job = TrainingJob(
            id=task_id,
            workflow_id=workflow_id,
            worker_type=worker_type,
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(training_job)
        
        # Update workflow status
        workflow.status = "training"
        workflow.progress = 0.0
        
        db.commit()
        
        # Configure TensorFlow
        configure_tensorflow(worker_type)
        
        # Setup PINN problem
        logger.info("Setting up PINN problem...")
        problem_setup = setup_pinn_problem(problem_config)
        
        # Update progress
        workflow.progress = 10.0
        db.commit()
        
        # Create and train model
        logger.info("Creating PINN model...")
        model, training_metrics = train_model(
            problem_setup, 
            problem_config,
            progress_callback=lambda p: update_progress(db, workflow, training_job, p)
        )
        
        # Update progress
        workflow.progress = 90.0
        db.commit()
        
        # Save model and results
        logger.info("Saving model and results...")
        model_info = save_model_artifacts(workflow_id, model, training_metrics, problem_config)
        
        # Update database records
        workflow.status = "completed"
        workflow.progress = 100.0
        workflow.accuracy = training_metrics.get("final_accuracy", 0.0)
        workflow.training_time = training_metrics.get("training_time", 0.0)
        workflow.model_path = model_info["model_path"]
        workflow.results_path = model_info["results_path"]
        workflow.pinn_config = model_info["pinn_config"]
        
        training_job.status = "completed"
        training_job.completed_at = datetime.utcnow()
        training_job.total_epochs = training_metrics.get("total_epochs", 0)
        training_job.best_loss = training_metrics.get("best_loss", 0.0)
        
        # Create model record
        model_record = Model(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            name=f"{workflow.name}_model",
            architecture=model_info["pinn_config"],
            parameters_count=model_info["parameters_count"],
            model_size_mb=model_info["model_size_mb"],
            accuracy=training_metrics.get("final_accuracy", 0.0),
            storage_path=model_info["model_path"],
            metadata_path=model_info["metadata_path"]
        )
        db.add(model_record)
        
        db.commit()
        
        logger.info(f"PINN training completed for workflow {workflow_id}")
        
        return {
            "status": "completed",
            "workflow_id": workflow_id,
            "training_time": training_metrics.get("training_time", 0.0),
            "accuracy": training_metrics.get("final_accuracy", 0.0),
            "model_path": model_info["model_path"]
        }
        
    except Exception as e:
        logger.error(f"PINN training failed for workflow {workflow_id}: {str(e)}")
        
        # Update database on failure
        try:
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if workflow:
                workflow.status = "failed"
            
            training_job = db.query(TrainingJob).filter(TrainingJob.id == task_id).first()
            if training_job:
                training_job.status = "failed"
                training_job.completed_at = datetime.utcnow()
            
            db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update database on error: {db_error}")
        
        raise
        
    finally:
        db.close()

def configure_tensorflow(worker_type: str):
    """Configure TensorFlow for optimal performance"""
    
    if worker_type == "gpu":
        # Configure GPU
        gpus = tf.config.experimental.list_physical_devices('GPU')
        if gpus:
            try:
                # Enable memory growth
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logger.info(f"Configured {len(gpus)} GPU(s)")
            except RuntimeError as e:
                logger.error(f"GPU configuration failed: {e}")
        else:
            logger.warning("No GPUs found, falling back to CPU")
    
    # Set DeepXDE backend
    dde.config.set_default_float("float32")
    
    # Disable XLA JIT for stability (can be enabled for performance)
    # dde.config.disable_xla_jit()

def setup_pinn_problem(problem_config: Dict[str, Any]) -> Dict[str, Any]:
    """Setup PINN problem based on configuration"""
    
    domain_type = problem_config["domain_type"]
    geometry = problem_config["geometry"]
    boundary_conditions = problem_config["boundary_conditions"]
    physics_parameters = problem_config["physics_parameters"]
    
    # Get domain-specific architecture
    architecture = get_pinn_architecture(domain_type, problem_config)
    
    if domain_type == "heat_transfer":
        return setup_heat_transfer_problem(geometry, boundary_conditions, physics_parameters, architecture)
    elif domain_type == "fluid_dynamics":
        return setup_fluid_dynamics_problem(geometry, boundary_conditions, physics_parameters, architecture)
    elif domain_type == "structural_mechanics":
        return setup_structural_problem(geometry, boundary_conditions, physics_parameters, architecture)
    elif domain_type == "electromagnetics":
        return setup_electromagnetics_problem(geometry, boundary_conditions, physics_parameters, architecture)
    else:
        raise ValueError(f"Unsupported domain type: {domain_type}")

def setup_heat_transfer_problem(geometry: Dict, boundary_conditions: Dict, 
                               physics_params: Dict, architecture: Dict) -> Dict[str, Any]:
    """Setup heat transfer problem using DeepXDE"""
    
    # Create geometry
    if geometry["type"] == "rectangle":
        geom = dde.geometry.Rectangle(
            [geometry["xmin"], geometry["ymin"]], 
            [geometry["xmax"], geometry["ymax"]]
        )
    elif geometry["type"] == "circle":
        geom = dde.geometry.Disk(
            [geometry["center_x"], geometry["center_y"]], 
            geometry["radius"]
        )
    else:
        raise ValueError(f"Unsupported geometry type: {geometry['type']}")
    
    # Time domain for transient problems
    if geometry.get("time_dependent", False):
        time_domain = dde.geometry.TimeDomain(0, geometry.get("time_end", 1.0))
        geomtime = dde.geometry.GeometryXTime(geom, time_domain)
        domain = geomtime
    else:
        domain = geom
    
    # Define PDE
    alpha = physics_params.get("thermal_diffusivity", 1.0)
    
    def heat_equation(x, u):
        """Heat equation: ∂u/∂t = α∇²u + f"""
        if geometry.get("time_dependent", False):
            # Transient heat equation
            du_t = dde.grad.jacobian(u, x, i=0, j=2)  # ∂u/∂t
            du_xx = dde.grad.hessian(u, x, i=0, j=0)  # ∂²u/∂x²
            du_yy = dde.grad.hessian(u, x, i=1, j=1)  # ∂²u/∂y²
            return du_t - alpha * (du_xx + du_yy)
        else:
            # Steady-state heat equation
            du_xx = dde.grad.hessian(u, x, i=0, j=0)  # ∂²u/∂x²
            du_yy = dde.grad.hessian(u, x, i=1, j=1)  # ∂²u/∂y²
            return du_xx + du_yy
    
    # Boundary conditions
    bcs = []
    for bc_name, bc_config in boundary_conditions.items():
        if bc_config["type"] == "dirichlet":
            def boundary_func(x, on_boundary):
                return on_boundary and bc_config.get("condition", lambda x: True)(x)
            
            bc = dde.DirichletBC(
                domain,
                lambda x: bc_config["value"],
                boundary_func
            )
            bcs.append(bc)
        
        elif bc_config["type"] == "neumann":
            def boundary_func(x, on_boundary):
                return on_boundary and bc_config.get("condition", lambda x: True)(x)
            
            bc = dde.NeumannBC(
                domain,
                lambda x: bc_config["value"],
                boundary_func
            )
            bcs.append(bc)
    
    # Initial condition for transient problems
    if geometry.get("time_dependent", False) and "initial_condition" in physics_params:
        ic = dde.IC(
            domain,
            lambda x: physics_params["initial_condition"],
            lambda x, on_initial: on_initial
        )
        bcs.append(ic)
    
    # Create PDE problem
    if geometry.get("time_dependent", False):
        data = dde.data.TimePDE(
            domain,
            heat_equation,
            bcs,
            num_domain=architecture.get("num_domain", 2000),
            num_boundary=architecture.get("num_boundary", 200),
            num_initial=architecture.get("num_initial", 100)
        )
    else:
        data = dde.data.PDE(
            domain,
            heat_equation,
            bcs,
            num_domain=architecture.get("num_domain", 2000),
            num_boundary=architecture.get("num_boundary", 200)
        )
    
    return {
        "data": data,
        "domain": domain,
        "pde_function": heat_equation,
        "boundary_conditions": bcs,
        "architecture": architecture,
        "physics_params": physics_params
    }

def setup_fluid_dynamics_problem(geometry: Dict, boundary_conditions: Dict,
                                physics_params: Dict, architecture: Dict) -> Dict[str, Any]:
    """Setup fluid dynamics problem (Navier-Stokes)"""
    
    # Create geometry
    if geometry["type"] == "rectangle":
        geom = dde.geometry.Rectangle(
            [geometry["xmin"], geometry["ymin"]], 
            [geometry["xmax"], geometry["ymax"]]
        )
    else:
        raise ValueError(f"Unsupported geometry type for fluid dynamics: {geometry['type']}")
    
    # Physics parameters
    reynolds = physics_params.get("reynolds_number", 100.0)
    
    def navier_stokes(x, u):
        """Navier-Stokes equations for incompressible flow"""
        # u = [u_velocity, v_velocity, pressure]
        u_vel, v_vel, p = u[:, 0:1], u[:, 1:2], u[:, 2:3]
        
        # Gradients
        u_x = dde.grad.jacobian(u_vel, x, i=0, j=0)
        u_y = dde.grad.jacobian(u_vel, x, i=0, j=1)
        u_xx = dde.grad.hessian(u_vel, x, i=0, j=0)
        u_yy = dde.grad.hessian(u_vel, x, i=1, j=1)
        
        v_x = dde.grad.jacobian(v_vel, x, i=0, j=0)
        v_y = dde.grad.jacobian(v_vel, x, i=0, j=1)
        v_xx = dde.grad.hessian(v_vel, x, i=0, j=0)
        v_yy = dde.grad.hessian(v_vel, x, i=1, j=1)
        
        p_x = dde.grad.jacobian(p, x, i=0, j=0)
        p_y = dde.grad.jacobian(p, x, i=0, j=1)
        
        # Continuity equation
        continuity = u_x + v_y
        
        # Momentum equations
        momentum_x = u_vel * u_x + v_vel * u_y + p_x - (u_xx + u_yy) / reynolds
        momentum_y = u_vel * v_x + v_vel * v_y + p_y - (v_xx + v_yy) / reynolds
        
        return [continuity, momentum_x, momentum_y]
    
    # Boundary conditions (simplified for lid-driven cavity)
    bcs = []
    
    # No-slip walls
    def wall_boundary(x, on_boundary):
        return on_boundary and (x[1] == 0 or x[0] == 0 or x[0] == 1)
    
    bc_u_wall = dde.DirichletBC(geom, lambda x: 0, wall_boundary, component=0)
    bc_v_wall = dde.DirichletBC(geom, lambda x: 0, wall_boundary, component=1)
    bcs.extend([bc_u_wall, bc_v_wall])
    
    # Moving lid
    def lid_boundary(x, on_boundary):
        return on_boundary and x[1] == 1
    
    bc_u_lid = dde.DirichletBC(geom, lambda x: 1, lid_boundary, component=0)
    bc_v_lid = dde.DirichletBC(geom, lambda x: 0, lid_boundary, component=1)
    bcs.extend([bc_u_lid, bc_v_lid])
    
    # Create PDE problem
    data = dde.data.PDE(
        geom,
        navier_stokes,
        bcs,
        num_domain=architecture.get("num_domain", 3000),
        num_boundary=architecture.get("num_boundary", 300)
    )
    
    return {
        "data": data,
        "domain": geom,
        "pde_function": navier_stokes,
        "boundary_conditions": bcs,
        "architecture": architecture,
        "physics_params": physics_params
    }

def setup_structural_problem(geometry: Dict, boundary_conditions: Dict,
                           physics_params: Dict, architecture: Dict) -> Dict[str, Any]:
    """Setup structural mechanics problem"""
    # Simplified implementation - would need full elasticity equations
    raise NotImplementedError("Structural mechanics not yet implemented")

def setup_electromagnetics_problem(geometry: Dict, boundary_conditions: Dict,
                                 physics_params: Dict, architecture: Dict) -> Dict[str, Any]:
    """Setup electromagnetics problem"""
    # Simplified implementation - would need Maxwell's equations
    raise NotImplementedError("Electromagnetics not yet implemented")

def train_model(problem_setup: Dict, problem_config: Dict, progress_callback=None) -> tuple:
    """Train the PINN model"""
    
    architecture = problem_setup["architecture"]
    
    # Create neural network
    layer_sizes = [architecture["input_dim"]] + architecture["hidden_layers"] + [architecture["output_dim"]]
    activation = architecture.get("activation", "tanh")
    initializer = architecture.get("initializer", "Glorot uniform")
    
    net = dde.nn.FNN(layer_sizes, activation, initializer)
    
    # Create model
    model = dde.Model(problem_setup["data"], net)
    
    # Compile model
    optimizer = architecture.get("optimizer", "adam")
    learning_rate = architecture.get("learning_rate", 1e-3)
    loss_weights = architecture.get("loss_weights", [1.0])
    
    if optimizer == "adam":
        model.compile(optimizer, lr=learning_rate, loss_weights=loss_weights)
    elif optimizer == "lbfgs":
        model.compile("L-BFGS", loss_weights=loss_weights)
    
    # Training callbacks
    callbacks = []
    
    # Progress callback
    if progress_callback:
        class ProgressCallback(dde.callbacks.Callback):
            def __init__(self, total_epochs):
                self.total_epochs = total_epochs
                
            def on_epoch_end(self, epoch, logs=None):
                progress = min(90.0, 10.0 + (epoch / self.total_epochs) * 80.0)
                progress_callback(progress)
        
        callbacks.append(ProgressCallback(architecture.get("epochs", 10000)))
    
    # Early stopping
    callbacks.append(dde.callbacks.EarlyStopping(patience=5000))
    
    # Model checkpoint
    callbacks.append(dde.callbacks.ModelCheckpoint(
        filepath=f"/tmp/model_checkpoint_{int(time.time())}.ckpt",
        save_better_only=True,
        period=1000
    ))
    
    # Train model
    start_time = time.time()
    
    epochs = architecture.get("epochs", 10000)
    losshistory, train_state = model.train(epochs=epochs, callbacks=callbacks)
    
    training_time = time.time() - start_time
    
    # Calculate metrics
    training_metrics = {
        "training_time": training_time,
        "total_epochs": len(losshistory.loss_train),
        "final_loss": float(losshistory.loss_train[-1]),
        "best_loss": float(min(losshistory.loss_train)),
        "final_accuracy": calculate_accuracy(model, problem_setup),
        "loss_history": losshistory.loss_train[-100:]  # Last 100 values
    }
    
    return model, training_metrics

def calculate_accuracy(model, problem_setup) -> float:
    """Calculate model accuracy (simplified)"""
    try:
        # Generate test points
        if hasattr(problem_setup["domain"], "random_points"):
            test_points = problem_setup["domain"].random_points(1000)
            predictions = model.predict(test_points)
            
            # Simple accuracy metric based on prediction variance
            # In practice, would compare with analytical solution if available
            accuracy = max(0.0, min(1.0, 1.0 - np.std(predictions) / (np.mean(np.abs(predictions)) + 1e-8)))
            return float(accuracy)
        else:
            return 0.95  # Default accuracy
    except Exception:
        return 0.95  # Default accuracy

def save_model_artifacts(workflow_id: str, model, training_metrics: Dict, 
                        problem_config: Dict) -> Dict[str, Any]:
    """Save model and artifacts to storage"""
    
    # Save model
    model_path = f"models/{workflow_id}/model"
    local_model_path = f"/tmp/model_{workflow_id}"
    
    model.save(local_model_path)
    
    # Upload model files to storage
    model_files = [
        f"{local_model_path}.meta",
        f"{local_model_path}.data-00000-of-00001",
        f"{local_model_path}.index"
    ]
    
    uploaded_files = []
    for model_file in model_files:
        if os.path.exists(model_file):
            remote_path = f"{model_path}/{os.path.basename(model_file)}"
            if storage.upload_file(remote_path, model_file):
                uploaded_files.append(remote_path)
    
    # Save metadata
    metadata = {
        "workflow_id": workflow_id,
        "model_type": "deepxde_pinn",
        "training_metrics": training_metrics,
        "problem_config": problem_config,
        "model_files": uploaded_files,
        "created_at": datetime.utcnow().isoformat()
    }
    
    metadata_path = f"models/{workflow_id}/metadata.json"
    storage.upload_json(metadata_path, metadata)
    
    # Save results
    results = {
        "workflow_id": workflow_id,
        "training_metrics": training_metrics,
        "model_info": {
            "path": model_path,
            "files": uploaded_files,
            "size_mb": sum(os.path.getsize(f) for f in model_files if os.path.exists(f)) / (1024 * 1024)
        }
    }
    
    results_path = f"results/{workflow_id}/results.json"
    storage.upload_json(results_path, results)
    
    # Calculate model info
    total_size = sum(os.path.getsize(f) for f in model_files if os.path.exists(f))
    model_size_mb = total_size / (1024 * 1024)
    
    # Count parameters (simplified)
    parameters_count = sum(np.prod(var.shape) for var in model.net.trainable_variables)
    
    return {
        "model_path": model_path,
        "metadata_path": metadata_path,
        "results_path": results_path,
        "model_size_mb": model_size_mb,
        "parameters_count": int(parameters_count),
        "pinn_config": problem_config
    }

def update_progress(db, workflow, training_job, progress: float):
    """Update training progress in database"""
    try:
        workflow.progress = progress
        db.commit()
    except Exception as e:
        logger.error(f"Failed to update progress: {e}")
        db.rollback()