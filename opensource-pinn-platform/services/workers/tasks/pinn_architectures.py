"""
PINN architecture configurations for different physics domains
"""

from typing import Dict, Any

def get_pinn_architecture(domain_type: str, problem_config: Dict[str, Any]) -> Dict[str, Any]:
    """Get optimal PINN architecture for the given domain and problem"""
    
    if domain_type == "heat_transfer":
        return get_heat_transfer_architecture(problem_config)
    elif domain_type == "fluid_dynamics":
        return get_fluid_dynamics_architecture(problem_config)
    elif domain_type == "structural_mechanics":
        return get_structural_architecture(problem_config)
    elif domain_type == "electromagnetics":
        return get_electromagnetics_architecture(problem_config)
    else:
        return get_default_architecture(problem_config)

def get_heat_transfer_architecture(problem_config: Dict[str, Any]) -> Dict[str, Any]:
    """Architecture for heat transfer problems"""
    
    geometry = problem_config["geometry"]
    
    # Determine input/output dimensions
    spatial_dims = len([k for k in geometry.keys() if k.startswith(('x', 'y', 'z'))])
    input_dim = spatial_dims + (1 if geometry.get("time_dependent", False) else 0)
    output_dim = 1  # Temperature
    
    # Complexity-based architecture selection
    complexity = estimate_problem_complexity(problem_config)
    
    if complexity < 0.3:  # Simple problems
        hidden_layers = [50, 50, 50]
        epochs = 5000
        num_domain = 1000
    elif complexity < 0.7:  # Medium complexity
        hidden_layers = [100, 100, 100, 100]
        epochs = 10000
        num_domain = 2000
    else:  # Complex problems
        hidden_layers = [200, 200, 200, 200]
        epochs = 20000
        num_domain = 3000
    
    return {
        "input_dim": input_dim,
        "output_dim": output_dim,
        "hidden_layers": hidden_layers,
        "activation": "tanh",
        "initializer": "Glorot uniform",
        "optimizer": "adam",
        "learning_rate": 1e-3,
        "epochs": epochs,
        "num_domain": num_domain,
        "num_boundary": num_domain // 10,
        "num_initial": num_domain // 20 if geometry.get("time_dependent", False) else 0,
        "loss_weights": [1.0, 10.0, 10.0] if geometry.get("time_dependent", False) else [1.0, 10.0]
    }

def get_fluid_dynamics_architecture(problem_config: Dict[str, Any]) -> Dict[str, Any]:
    """Architecture for fluid dynamics problems"""
    
    geometry = problem_config["geometry"]
    physics_params = problem_config["physics_parameters"]
    
    spatial_dims = 2  # Assuming 2D for now
    input_dim = spatial_dims + (1 if geometry.get("time_dependent", False) else 0)
    output_dim = spatial_dims + 1  # u, v, p
    
    # Reynolds number affects complexity
    reynolds = physics_params.get("reynolds_number", 100)
    
    if reynolds < 50:
        hidden_layers = [100, 100, 100, 100]
        epochs = 15000
    elif reynolds < 200:
        hidden_layers = [200, 200, 200, 200, 200]
        epochs = 25000
    else:
        hidden_layers = [300, 300, 300, 300, 300]
        epochs = 40000
    
    return {
        "input_dim": input_dim,
        "output_dim": output_dim,
        "hidden_layers": hidden_layers,
        "activation": "tanh",
        "initializer": "Xavier",
        "optimizer": "adam",  # Start with Adam, can switch to L-BFGS
        "learning_rate": 1e-3,
        "epochs": epochs,
        "num_domain": 3000,
        "num_boundary": 300,
        "loss_weights": [1.0, 1.0, 1.0, 100.0]  # continuity, momentum_x, momentum_y, BC
    }

def get_structural_architecture(problem_config: Dict[str, Any]) -> Dict[str, Any]:
    """Architecture for structural mechanics problems"""
    
    geometry = problem_config["geometry"]
    
    spatial_dims = len([k for k in geometry.keys() if k.startswith(('x', 'y', 'z'))])
    input_dim = spatial_dims
    output_dim = spatial_dims  # Displacement components
    
    return {
        "input_dim": input_dim,
        "output_dim": output_dim,
        "hidden_layers": [100, 100, 100, 100],
        "activation": "tanh",
        "initializer": "Glorot uniform",
        "optimizer": "adam",
        "learning_rate": 1e-3,
        "epochs": 15000,
        "num_domain": 2000,
        "num_boundary": 200,
        "loss_weights": [1.0, 50.0]
    }

def get_electromagnetics_architecture(problem_config: Dict[str, Any]) -> Dict[str, Any]:
    """Architecture for electromagnetics problems"""
    
    geometry = problem_config["geometry"]
    
    spatial_dims = len([k for k in geometry.keys() if k.startswith(('x', 'y', 'z'))])
    input_dim = spatial_dims + (1 if geometry.get("time_dependent", False) else 0)
    output_dim = 1  # Electric potential or field component
    
    return {
        "input_dim": input_dim,
        "output_dim": output_dim,
        "hidden_layers": [100, 100, 100, 100],
        "activation": "tanh",
        "initializer": "Glorot uniform",
        "optimizer": "adam",
        "learning_rate": 1e-3,
        "epochs": 12000,
        "num_domain": 2000,
        "num_boundary": 200,
        "loss_weights": [1.0, 20.0]
    }

def get_default_architecture(problem_config: Dict[str, Any]) -> Dict[str, Any]:
    """Default architecture for unknown domains"""
    
    return {
        "input_dim": 2,
        "output_dim": 1,
        "hidden_layers": [100, 100, 100],
        "activation": "tanh",
        "initializer": "Glorot uniform",
        "optimizer": "adam",
        "learning_rate": 1e-3,
        "epochs": 10000,
        "num_domain": 2000,
        "num_boundary": 200,
        "loss_weights": [1.0, 10.0]
    }

def estimate_problem_complexity(problem_config: Dict[str, Any]) -> float:
    """Estimate problem complexity (0.0 to 1.0)"""
    
    complexity = 0.0
    
    # Geometry complexity
    geometry = problem_config["geometry"]
    if geometry["type"] == "circle":
        complexity += 0.1
    elif geometry["type"] == "rectangle":
        complexity += 0.05
    else:
        complexity += 0.2
    
    # Time dependency
    if geometry.get("time_dependent", False):
        complexity += 0.3
    
    # Number of boundary conditions
    bc_count = len(problem_config.get("boundary_conditions", {}))
    complexity += min(0.3, bc_count * 0.1)
    
    # Physics parameters complexity
    physics_params = problem_config.get("physics_parameters", {})
    if len(physics_params) > 3:
        complexity += 0.2
    
    # Accuracy requirements
    accuracy_req = problem_config.get("accuracy_requirements", 0.95)
    if accuracy_req > 0.98:
        complexity += 0.2
    
    return min(1.0, complexity)