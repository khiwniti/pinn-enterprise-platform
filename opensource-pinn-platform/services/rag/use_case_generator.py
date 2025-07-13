"""
RAG-Powered Use Case Generator for PINN Simulations
Generates professional engineering simulation use cases with Python code
"""

import json
import uuid
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import numpy as np
from pathlib import Path

@dataclass
class SimulationUseCase:
    """Professional engineering simulation use case"""
    id: str
    name: str
    category: str
    description: str
    physics_domain: str
    complexity_level: str
    industry_application: str
    python_code: str
    parameters: Dict[str, Any]
    expected_results: Dict[str, Any]
    visualization_config: Dict[str, Any]
    engineering_insights: List[str]
    created_at: str

class EngineeringUseCaseRAG:
    """RAG system for generating professional engineering simulation use cases"""
    
    def __init__(self):
        self.knowledge_base = self._load_engineering_knowledge()
        self.templates = self._load_code_templates()
        
    def _load_engineering_knowledge(self) -> Dict[str, Any]:
        """Load engineering domain knowledge for RAG"""
        return {
            "fluid_dynamics": {
                "applications": [
                    "Aerospace vehicle design", "Automotive aerodynamics", 
                    "Wind turbine optimization", "HVAC system design",
                    "Marine vessel hull design", "Sports equipment optimization"
                ],
                "physics_equations": [
                    "Navier-Stokes equations", "Continuity equation",
                    "Energy equation", "Turbulence models (k-ε, k-ω, LES)"
                ],
                "boundary_conditions": [
                    "No-slip wall", "Velocity inlet", "Pressure outlet",
                    "Symmetry", "Periodic", "Moving wall"
                ],
                "key_parameters": [
                    "Reynolds number", "Mach number", "Prandtl number",
                    "Turbulence intensity", "Viscosity", "Density"
                ]
            },
            "heat_transfer": {
                "applications": [
                    "Electronic cooling", "Building thermal analysis",
                    "Heat exchanger design", "Manufacturing processes",
                    "Energy storage systems", "Thermal management"
                ],
                "physics_equations": [
                    "Heat conduction equation", "Convection-diffusion equation",
                    "Stefan-Boltzmann law", "Fourier's law"
                ],
                "boundary_conditions": [
                    "Fixed temperature", "Heat flux", "Convective heat transfer",
                    "Radiation", "Adiabatic", "Thermal contact"
                ],
                "key_parameters": [
                    "Thermal conductivity", "Heat capacity", "Convection coefficient",
                    "Emissivity", "Stefan-Boltzmann constant", "Biot number"
                ]
            }
        }
    
    def _load_code_templates(self) -> Dict[str, str]:
        """Load Python code templates for different simulation types"""
        return {
            "fluid_dynamics": '''
import numpy as np
import deepxde as dde
import tensorflow as tf
from typing import Dict, Any

class {class_name}:
    """
    Professional {application} simulation using PINNs
    
    Physics: {physics_description}
    Application: {industry_application}
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_geometry()
        self.setup_physics()
        
    def setup_geometry(self):
        """Define computational domain geometry"""
        {geometry_code}
        
    def setup_physics(self):
        """Define physics equations and boundary conditions"""
        {physics_code}
        
    def create_pinn_model(self):
        """Create and configure PINN model"""
        {model_code}
        
    def train_model(self):
        """Train the PINN model"""
        {training_code}
        
    def analyze_results(self):
        """Analyze simulation results"""
        {analysis_code}
        
    def generate_visualization(self):
        """Generate 3D visualization data"""
        {visualization_code}

# Usage example
if __name__ == "__main__":
    config = {config_dict}
    
    simulation = {class_name}(config)
    model = simulation.create_pinn_model()
    results = simulation.train_model()
    analysis = simulation.analyze_results()
    viz_data = simulation.generate_visualization()
    
    print(f"Simulation completed: {{analysis}}")
''',
            "heat_transfer": '''
import numpy as np
import deepxde as dde
import tensorflow as tf
from typing import Dict, Any

class {class_name}:
    """
    Professional {application} heat transfer simulation using PINNs
    
    Physics: {physics_description}
    Application: {industry_application}
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_thermal_domain()
        self.setup_heat_equations()
        
    def setup_thermal_domain(self):
        """Define thermal computational domain"""
        {geometry_code}
        
    def setup_heat_equations(self):
        """Define heat transfer equations and thermal boundary conditions"""
        {physics_code}
        
    def create_thermal_pinn(self):
        """Create thermal PINN model"""
        {model_code}
        
    def solve_heat_transfer(self):
        """Solve heat transfer problem"""
        {training_code}
        
    def thermal_analysis(self):
        """Perform thermal analysis"""
        {analysis_code}
        
    def generate_thermal_visualization(self):
        """Generate thermal field visualization"""
        {visualization_code}

# Usage example
if __name__ == "__main__":
    config = {config_dict}
    
    thermal_sim = {class_name}(config)
    model = thermal_sim.create_thermal_pinn()
    results = thermal_sim.solve_heat_transfer()
    analysis = thermal_sim.thermal_analysis()
    viz_data = thermal_sim.generate_thermal_visualization()
    
    print(f"Thermal simulation completed: {{analysis}}")
'''
        }
    
    async def generate_use_case(self, 
                              domain: str, 
                              application: str, 
                              complexity: str = "intermediate",
                              custom_requirements: Optional[str] = None) -> SimulationUseCase:
        """Generate a professional engineering simulation use case"""
        
        # RAG: Retrieve relevant knowledge
        domain_knowledge = self.knowledge_base.get(domain, {})
        
        # Generate use case metadata
        use_case_id = str(uuid.uuid4())
        use_case_name = f"{application.title()} - {domain.replace('_', ' ').title()} Analysis"
        
        # Generate detailed description
        description = self._generate_description(domain, application, domain_knowledge)
        
        # Generate Python code
        python_code = self._generate_python_code(domain, application, complexity, domain_knowledge)
        
        # Generate parameters
        parameters = self._generate_parameters(domain, application, complexity, domain_knowledge)
        
        # Generate expected results
        expected_results = self._generate_expected_results(domain, application, parameters)
        
        # Generate visualization config
        visualization_config = self._generate_visualization_config(domain, application)
        
        # Generate engineering insights
        engineering_insights = self._generate_engineering_insights(domain, application, domain_knowledge)
        
        return SimulationUseCase(
            id=use_case_id,
            name=use_case_name,
            category=domain,
            description=description,
            physics_domain=domain,
            complexity_level=complexity,
            industry_application=application,
            python_code=python_code,
            parameters=parameters,
            expected_results=expected_results,
            visualization_config=visualization_config,
            engineering_insights=engineering_insights,
            created_at=datetime.utcnow().isoformat()
        )
    
    def _generate_description(self, domain: str, application: str, knowledge: Dict) -> str:
        """Generate detailed technical description"""
        applications = knowledge.get("applications", [])
        equations = knowledge.get("physics_equations", [])
        
        return f"""
Professional {domain.replace('_', ' ')} simulation for {application} using Physics-Informed Neural Networks (PINNs).

This simulation addresses critical engineering challenges in {application} by solving {', '.join(equations[:2])} 
with advanced boundary conditions and material properties. The PINN approach enables:

• Mesh-free solution methodology
• Continuous field representation
• Physics-constrained learning
• Real-time parameter optimization
• Uncertainty quantification

Industry applications include: {', '.join(applications[:3])}

The simulation provides quantitative insights for design optimization, performance prediction, 
and engineering decision-making with professional-grade accuracy and reliability.
        """.strip()
    
    def _generate_python_code(self, domain: str, application: str, complexity: str, knowledge: Dict) -> str:
        """Generate professional Python simulation code"""
        
        class_name = f"{application.replace(' ', '').replace('-', '')}Simulation"
        
        # Generate geometry code based on domain
        geometry_code = self._generate_geometry_code(domain, application)
        
        # Generate physics code
        physics_code = self._generate_physics_code(domain, knowledge)
        
        # Generate model code
        model_code = self._generate_model_code(complexity)
        
        # Generate training code
        training_code = self._generate_training_code(complexity)
        
        # Generate analysis code
        analysis_code = self._generate_analysis_code(domain)
        
        # Generate visualization code
        visualization_code = self._generate_visualization_code(domain)
        
        # Generate config dictionary
        config_dict = self._generate_config_dict(domain, application)
        
        template = self.templates.get(domain, self.templates["fluid_dynamics"])
        
        return template.format(
            class_name=class_name,
            application=application,
            physics_description=', '.join(knowledge.get("physics_equations", [])[:2]),
            industry_application=application,
            geometry_code=geometry_code,
            physics_code=physics_code,
            model_code=model_code,
            training_code=training_code,
            analysis_code=analysis_code,
            visualization_code=visualization_code,
            config_dict=config_dict
        )
    
    def _generate_geometry_code(self, domain: str, application: str) -> str:
        """Generate geometry setup code"""
        if "aerodynamics" in application.lower() or "flow" in application.lower():
            return '''
        # Define flow domain around object
        if self.config["geometry_type"] == "airfoil":
            # NACA airfoil geometry
            self.geom = dde.geometry.Polygon(self._generate_airfoil_points())
        elif self.config["geometry_type"] == "cylinder":
            # Circular cylinder
            self.geom = dde.geometry.Disk([0, 0], self.config["radius"])
        else:
            # Custom geometry from config
            self.geom = dde.geometry.Rectangle(
                [self.config["x_min"], self.config["y_min"]], 
                [self.config["x_max"], self.config["y_max"]]
            )
        
        # Time domain for unsteady simulations
        if self.config.get("unsteady", False):
            self.time_domain = dde.geometry.TimeDomain(0, self.config["time_end"])
            self.geomtime = dde.geometry.GeometryXTime(self.geom, self.time_domain)
            '''
        else:
            return '''
        # Define computational domain
        self.geom = dde.geometry.Rectangle(
            [self.config["x_min"], self.config["y_min"]], 
            [self.config["x_max"], self.config["y_max"]]
        )
        
        # Add time dimension if transient
        if self.config.get("transient", False):
            self.time_domain = dde.geometry.TimeDomain(0, self.config["time_end"])
            self.geomtime = dde.geometry.GeometryXTime(self.geom, self.time_domain)
            '''
    
    def _generate_physics_code(self, domain: str, knowledge: Dict) -> str:
        """Generate physics equations code"""
        if domain == "fluid_dynamics":
            return '''
        # Navier-Stokes equations for incompressible flow
        def navier_stokes(x, u):
            """
            u[:, 0:1] - velocity in x-direction
            u[:, 1:2] - velocity in y-direction  
            u[:, 2:3] - pressure
            """
            u_vel, v_vel, p = u[:, 0:1], u[:, 1:2], u[:, 2:3]
            
            # Velocity gradients
            u_x = dde.grad.jacobian(u_vel, x, i=0, j=0)
            u_y = dde.grad.jacobian(u_vel, x, i=0, j=1)
            v_x = dde.grad.jacobian(v_vel, x, i=0, j=0)
            v_y = dde.grad.jacobian(v_vel, x, i=0, j=1)
            
            # Pressure gradients
            p_x = dde.grad.jacobian(p, x, i=0, j=0)
            p_y = dde.grad.jacobian(p, x, i=0, j=1)
            
            # Second derivatives for viscous terms
            u_xx = dde.grad.hessian(u_vel, x, i=0, j=0)
            u_yy = dde.grad.hessian(u_vel, x, i=1, j=1)
            v_xx = dde.grad.hessian(v_vel, x, i=0, j=0)
            v_yy = dde.grad.hessian(v_vel, x, i=1, j=1)
            
            # Reynolds number
            Re = self.config["reynolds_number"]
            
            # Momentum equations
            momentum_x = u_vel * u_x + v_vel * u_y + p_x - (u_xx + u_yy) / Re
            momentum_y = u_vel * v_x + v_vel * v_y + p_y - (v_xx + v_yy) / Re
            
            # Continuity equation
            continuity = u_x + v_y
            
            return [momentum_x, momentum_y, continuity]
        
        self.pde = navier_stokes
        
        # Boundary conditions
        self.bcs = []
        
        # No-slip wall condition
        def wall_boundary(x, on_boundary):
            return on_boundary and self._is_wall(x)
        
        bc_wall_u = dde.DirichletBC(self.geomtime, lambda x: 0, wall_boundary, component=0)
        bc_wall_v = dde.DirichletBC(self.geomtime, lambda x: 0, wall_boundary, component=1)
        self.bcs.extend([bc_wall_u, bc_wall_v])
        
        # Inlet condition
        def inlet_boundary(x, on_boundary):
            return on_boundary and self._is_inlet(x)
        
        bc_inlet_u = dde.DirichletBC(self.geomtime, 
                                   lambda x: self.config["inlet_velocity"], 
                                   inlet_boundary, component=0)
        self.bcs.append(bc_inlet_u)
            '''
        elif domain == "heat_transfer":
            return '''
        # Heat conduction/convection equation
        def heat_equation(x, T):
            """
            T - temperature field
            """
            # Temperature gradients
            T_x = dde.grad.jacobian(T, x, i=0, j=0)
            T_y = dde.grad.jacobian(T, x, i=0, j=1)
            
            # Second derivatives
            T_xx = dde.grad.hessian(T, x, i=0, j=0)
            T_yy = dde.grad.hessian(T, x, i=1, j=1)
            
            # Time derivative for transient problems
            if self.config.get("transient", False):
                T_t = dde.grad.jacobian(T, x, i=0, j=2)  # Time is 3rd dimension
                
                # Transient heat equation: ρcp(∂T/∂t) = k∇²T + Q
                alpha = self.config["thermal_diffusivity"]
                source = self.config.get("heat_source", 0)
                
                return T_t - alpha * (T_xx + T_yy) - source
            else:
                # Steady-state: k∇²T + Q = 0
                k = self.config["thermal_conductivity"]
                source = self.config.get("heat_source", 0)
                
                return k * (T_xx + T_yy) + source
        
        self.pde = heat_equation
        
        # Thermal boundary conditions
        self.bcs = []
        
        # Fixed temperature boundary
        def hot_boundary(x, on_boundary):
            return on_boundary and self._is_hot_surface(x)
        
        bc_hot = dde.DirichletBC(self.geomtime, 
                               lambda x: self.config["hot_temperature"], 
                               hot_boundary)
        self.bcs.append(bc_hot)
        
        # Heat flux boundary
        def flux_boundary(x, on_boundary):
            return on_boundary and self._is_flux_surface(x)
        
        bc_flux = dde.NeumannBC(self.geomtime, 
                              lambda x: self.config["heat_flux"], 
                              flux_boundary)
        self.bcs.append(bc_flux)
            '''
        else:
            return '''
        # Generic PDE setup
        def pde_equation(x, u):
            # Define your PDE here
            return dde.grad.jacobian(u, x) - self.config["source_term"]
        
        self.pde = pde_equation
        self.bcs = []  # Define boundary conditions
            '''
    
    def _generate_model_code(self, complexity: str) -> str:
        """Generate PINN model creation code"""
        if complexity == "basic":
            layers = "[3, 50, 50, 50, 1]"
            activation = "tanh"
        elif complexity == "intermediate":
            layers = "[3, 100, 100, 100, 100, 1]"
            activation = "tanh"
        else:  # advanced
            layers = "[3, 200, 200, 200, 200, 200, 1]"
            activation = "swish"
        
        return f'''
        # Create neural network
        layer_sizes = {layers}
        activation = "{activation}"
        initializer = "Glorot uniform"
        
        net = dde.nn.FNN(layer_sizes, activation, initializer)
        
        # Create PINN model
        if hasattr(self, 'geomtime'):
            data = dde.data.TimePDE(self.geomtime, self.pde, self.bcs,
                                  num_domain=2000, num_boundary=200, num_initial=100)
        else:
            data = dde.data.PDE(self.geom, self.pde, self.bcs,
                              num_domain=2000, num_boundary=200)
        
        model = dde.Model(data, net)
        
        # Compile model
        model.compile("adam", lr=1e-3, loss_weights=[1, 1, 10])  # Adjust weights as needed
        
        return model
        '''
    
    def _generate_training_code(self, complexity: str) -> str:
        """Generate model training code"""
        if complexity == "basic":
            epochs = 5000
        elif complexity == "intermediate":
            epochs = 10000
        else:  # advanced
            epochs = 20000
        
        return f'''
        # Training configuration
        epochs = {epochs}
        
        # Callbacks for monitoring
        callbacks = [
            dde.callbacks.ModelCheckpoint("./models/checkpoint", save_better_only=True),
            dde.callbacks.EarlyStopping(patience=2000),
            dde.callbacks.ReduceLROnPlateau(factor=0.8, patience=1000, min_lr=1e-6)
        ]
        
        # Train model
        losshistory, train_state = model.train(epochs=epochs, callbacks=callbacks)
        
        # Fine-tune with L-BFGS
        model.compile("L-BFGS")
        losshistory, train_state = model.train()
        
        return {{
            "loss_history": losshistory.loss_train,
            "train_state": train_state,
            "final_loss": losshistory.loss_train[-1],
            "model": model
        }}
        '''
    
    def _generate_analysis_code(self, domain: str) -> str:
        """Generate results analysis code"""
        if domain == "fluid_dynamics":
            return '''
        # Generate test points for analysis
        test_points = self.geom.random_points(1000)
        
        # Predict flow field
        predictions = model.predict(test_points)
        
        # Extract velocity and pressure fields
        u_velocity = predictions[:, 0]
        v_velocity = predictions[:, 1] 
        pressure = predictions[:, 2]
        
        # Calculate derived quantities
        velocity_magnitude = np.sqrt(u_velocity**2 + v_velocity**2)
        
        # Engineering analysis
        analysis = {
            "max_velocity": float(np.max(velocity_magnitude)),
            "min_pressure": float(np.min(pressure)),
            "max_pressure": float(np.max(pressure)),
            "pressure_drop": float(np.max(pressure) - np.min(pressure)),
            "reynolds_number": self.config["reynolds_number"],
            "flow_regime": "laminar" if self.config["reynolds_number"] < 2300 else "turbulent"
        }
        
        return analysis
            '''
        elif domain == "heat_transfer":
            return '''
        # Generate test points for thermal analysis
        test_points = self.geom.random_points(1000)
        
        # Predict temperature field
        temperature = model.predict(test_points)
        
        # Calculate thermal gradients
        temp_gradients = []
        for i, point in enumerate(test_points[:100]):  # Sample points
            grad = model.predict(point.reshape(1, -1), operator=lambda x, u: dde.grad.jacobian(u, x))
            temp_gradients.append(grad)
        
        temp_gradients = np.array(temp_gradients)
        
        # Engineering thermal analysis
        analysis = {
            "max_temperature": float(np.max(temperature)),
            "min_temperature": float(np.min(temperature)),
            "temperature_range": float(np.max(temperature) - np.min(temperature)),
            "avg_temperature": float(np.mean(temperature)),
            "max_gradient": float(np.max(np.linalg.norm(temp_gradients, axis=1))),
            "thermal_efficiency": self._calculate_thermal_efficiency(temperature)
        }
        
        return analysis
            '''
        else:
            return '''
        # Generic analysis
        test_points = self.geom.random_points(1000)
        predictions = model.predict(test_points)
        
        analysis = {
            "max_value": float(np.max(predictions)),
            "min_value": float(np.min(predictions)),
            "mean_value": float(np.mean(predictions)),
            "std_value": float(np.std(predictions))
        }
        
        return analysis
            '''
    
    def _generate_visualization_code(self, domain: str) -> str:
        """Generate 3D visualization data code"""
        return '''
        # Generate high-resolution grid for visualization
        x_viz = np.linspace(self.config["x_min"], self.config["x_max"], 100)
        y_viz = np.linspace(self.config["y_min"], self.config["y_max"], 100)
        X_viz, Y_viz = np.meshgrid(x_viz, y_viz)
        
        # Flatten for prediction
        viz_points = np.column_stack([X_viz.ravel(), Y_viz.ravel()])
        
        # Predict on visualization grid
        viz_predictions = model.predict(viz_points)
        
        # Reshape for 3D visualization
        if viz_predictions.shape[1] > 1:
            # Multiple fields (e.g., velocity components, pressure)
            field_data = {}
            field_names = self._get_field_names()
            
            for i, name in enumerate(field_names):
                field_data[name] = viz_predictions[:, i].reshape(X_viz.shape)
        else:
            # Single field (e.g., temperature)
            field_data = {"primary_field": viz_predictions.reshape(X_viz.shape)}
        
        # Prepare 3D visualization data
        viz_data = {
            "grid": {
                "x": X_viz.tolist(),
                "y": Y_viz.tolist(),
                "z": [[0 for _ in range(len(x_viz))] for _ in range(len(y_viz))]  # 2D elevated to 3D
            },
            "fields": {name: field.tolist() for name, field in field_data.items()},
            "metadata": {
                "domain": self.config.get("physics_domain", "unknown"),
                "resolution": [len(x_viz), len(y_viz)],
                "bounds": {
                    "x": [float(np.min(x_viz)), float(np.max(x_viz))],
                    "y": [float(np.min(y_viz)), float(np.max(y_viz))],
                    "fields": {name: [float(np.min(field)), float(np.max(field))] 
                             for name, field in field_data.items()}
                }
            },
            "visualization_config": {
                "colormap": "viridis",
                "show_streamlines": domain == "fluid_dynamics",
                "show_contours": True,
                "show_vectors": domain == "fluid_dynamics",
                "animation": self.config.get("transient", False) or self.config.get("unsteady", False)
            }
        }
        
        return viz_data
        '''
    
    def _generate_config_dict(self, domain: str, application: str) -> str:
        """Generate configuration dictionary"""
        base_config = {
            "physics_domain": domain,
            "application": application,
            "x_min": -2.0,
            "x_max": 8.0,
            "y_min": -3.0,
            "y_max": 3.0
        }
        
        if domain == "fluid_dynamics":
            base_config.update({
                "reynolds_number": 100,
                "inlet_velocity": 1.0,
                "geometry_type": "cylinder",
                "radius": 0.5,
                "unsteady": False
            })
        elif domain == "heat_transfer":
            base_config.update({
                "thermal_conductivity": 1.0,
                "thermal_diffusivity": 1.0,
                "hot_temperature": 100.0,
                "cold_temperature": 0.0,
                "heat_flux": 10.0,
                "transient": False,
                "time_end": 1.0
            })
        
        return json.dumps(base_config, indent=8)
    
    def _generate_parameters(self, domain: str, application: str, complexity: str, knowledge: Dict) -> Dict[str, Any]:
        """Generate simulation parameters"""
        key_params = knowledge.get("key_parameters", [])
        
        parameters = {
            "domain": domain,
            "application": application,
            "complexity": complexity,
            "mesh_resolution": "high" if complexity == "advanced" else "medium",
            "convergence_tolerance": 1e-6 if complexity == "advanced" else 1e-4,
            "max_iterations": 20000 if complexity == "advanced" else 10000
        }
        
        # Add domain-specific parameters
        if domain == "fluid_dynamics":
            parameters.update({
                "reynolds_number": 1000 if complexity == "advanced" else 100,
                "mach_number": 0.1,
                "turbulence_model": "k_epsilon" if complexity == "advanced" else "laminar",
                "inlet_velocity": 10.0,
                "fluid_density": 1.225,
                "dynamic_viscosity": 1.8e-5
            })
        elif domain == "heat_transfer":
            parameters.update({
                "thermal_conductivity": 0.6,
                "specific_heat": 1005,
                "density": 1.225,
                "convection_coefficient": 25.0,
                "radiation_emissivity": 0.8,
                "ambient_temperature": 20.0
            })
        
        return parameters
    
    def _generate_expected_results(self, domain: str, application: str, parameters: Dict) -> Dict[str, Any]:
        """Generate expected simulation results"""
        results = {
            "simulation_type": f"{domain} - {application}",
            "expected_accuracy": "95-99%" if parameters.get("complexity") == "advanced" else "90-95%",
            "convergence_time": "2-5 minutes" if parameters.get("complexity") == "basic" else "10-30 minutes",
            "output_fields": []
        }
        
        if domain == "fluid_dynamics":
            results["output_fields"] = [
                "velocity_magnitude", "pressure_field", "vorticity", 
                "streamlines", "drag_coefficient", "lift_coefficient"
            ]
            results["engineering_metrics"] = {
                "drag_coefficient": "0.1 - 2.0 (depending on geometry)",
                "pressure_drop": "Proportional to velocity squared",
                "flow_separation": "Detected if Re > critical value"
            }
        elif domain == "heat_transfer":
            results["output_fields"] = [
                "temperature_field", "heat_flux", "thermal_gradients",
                "isotherms", "heat_transfer_coefficient"
            ]
            results["engineering_metrics"] = {
                "max_temperature": "Within material limits",
                "heat_transfer_rate": "Watts per unit area",
                "thermal_efficiency": "Percentage of ideal performance"
            }
        
        return results
    
    def _generate_visualization_config(self, domain: str, application: str) -> Dict[str, Any]:
        """Generate 3D visualization configuration"""
        config = {
            "type": "3D_field_visualization",
            "renderer": "WebGL",
            "interactive": True,
            "animation_capable": True,
            "export_formats": ["PNG", "MP4", "WebM", "STL"],
            "color_schemes": ["viridis", "plasma", "coolwarm", "jet"],
            "view_modes": ["surface", "contour", "streamlines", "vectors", "particles"]
        }
        
        if domain == "fluid_dynamics":
            config.update({
                "primary_visualization": "streamlines_with_pressure",
                "secondary_visualizations": ["velocity_vectors", "vorticity_contours"],
                "animation_type": "particle_tracing",
                "interactive_features": ["zoom", "rotate", "slice_planes", "probe_points"]
            })
        elif domain == "heat_transfer":
            config.update({
                "primary_visualization": "temperature_surface",
                "secondary_visualizations": ["heat_flux_vectors", "isotherms"],
                "animation_type": "thermal_evolution",
                "interactive_features": ["zoom", "rotate", "temperature_probe", "cross_sections"]
            })
        
        return config
    
    def _generate_engineering_insights(self, domain: str, application: str, knowledge: Dict) -> List[str]:
        """Generate professional engineering insights"""
        applications = knowledge.get("applications", [])
        
        insights = [
            f"This {domain.replace('_', ' ')} simulation addresses critical challenges in {application}",
            f"Physics-informed approach ensures solution satisfies fundamental conservation laws",
            f"Mesh-free methodology enables complex geometry handling without grid generation",
            f"Real-time parameter optimization supports design space exploration"
        ]
        
        if domain == "fluid_dynamics":
            insights.extend([
                "Reynolds number analysis determines flow regime and turbulence characteristics",
                "Boundary layer behavior affects drag, heat transfer, and separation phenomena",
                "Pressure distribution provides insights for aerodynamic optimization",
                "Streamline patterns reveal flow physics and potential design improvements"
            ])
        elif domain == "heat_transfer":
            insights.extend([
                "Temperature gradients indicate thermal stress locations and magnitude",
                "Heat flux distribution guides thermal management design decisions",
                "Thermal boundary layer development affects convective heat transfer",
                "Transient response reveals system thermal time constants"
            ])
        
        # Add application-specific insights
        if "aerodynamics" in application.lower():
            insights.append("Aerodynamic coefficients enable performance prediction and optimization")
        elif "cooling" in application.lower():
            insights.append("Thermal performance metrics guide cooling system design")
        elif "structural" in application.lower():
            insights.append("Stress concentrations identify critical design locations")
        
        return insights

# Usage example and API integration
async def main():
    """Example usage of the RAG use case generator"""
    rag_generator = EngineeringUseCaseRAG()
    
    # Generate different types of use cases
    use_cases = []
    
    # Fluid dynamics use cases
    fluid_cases = [
        ("fluid_dynamics", "Golf Ball Aerodynamics", "intermediate"),
        ("fluid_dynamics", "Wind Turbine Blade Analysis", "advanced"),
        ("fluid_dynamics", "Automotive Spoiler Design", "intermediate"),
        ("fluid_dynamics", "HVAC Duct Optimization", "basic")
    ]
    
    # Heat transfer use cases
    thermal_cases = [
        ("heat_transfer", "Electronic Component Cooling", "intermediate"),
        ("heat_transfer", "Building Thermal Analysis", "basic"),
        ("heat_transfer", "Heat Exchanger Design", "advanced"),
        ("heat_transfer", "Solar Panel Thermal Management", "intermediate")
    ]
    
    all_cases = fluid_cases + thermal_cases
    
    for domain, application, complexity in all_cases:
        use_case = await rag_generator.generate_use_case(domain, application, complexity)
        use_cases.append(use_case)
        print(f"Generated: {use_case.name}")
    
    return use_cases

if __name__ == "__main__":
    use_cases = asyncio.run(main())
    print(f"Generated {len(use_cases)} professional engineering use cases")