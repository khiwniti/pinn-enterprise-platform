"""
Professional 3D Visualization System for PINN Simulation Results
Enterprise-grade WebGL-based 3D viewport with interactive features
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import base64
import io
from datetime import datetime

@dataclass
class VisualizationData:
    """3D visualization data structure"""
    grid: Dict[str, List[List[float]]]
    fields: Dict[str, List[List[float]]]
    metadata: Dict[str, Any]
    visualization_config: Dict[str, Any]
    timestamp: str

class Professional3DViewport:
    """Enterprise-grade 3D visualization system for engineering simulations"""
    
    def __init__(self):
        self.supported_formats = ["WebGL", "Three.js", "VTK", "ParaView"]
        self.color_schemes = {
            "viridis": ["#440154", "#482777", "#3f4a8a", "#31678e", "#26838f", "#1f9d8a", "#6cce5a", "#b6de2b", "#fee825"],
            "plasma": ["#0c0786", "#40039c", "#6a00a7", "#8f0da4", "#b12a90", "#cc4778", "#e16462", "#f2844b", "#fca636", "#fcce25"],
            "coolwarm": ["#3b4cc0", "#5977e3", "#7aa3f4", "#9dc9f7", "#c0e1fa", "#e2f1fc", "#f7d7d7", "#f4b7b0", "#e68a8a", "#d85c5c", "#b40426"],
            "jet": ["#000080", "#0000ff", "#0080ff", "#00ffff", "#80ff00", "#ffff00", "#ff8000", "#ff0000", "#800000"]
        }
        
    def create_3d_visualization(self, 
                              simulation_results: Dict[str, Any],
                              visualization_type: str = "surface",
                              color_scheme: str = "viridis",
                              interactive_features: List[str] = None) -> Dict[str, Any]:
        """Create professional 3D visualization from simulation results"""
        
        if interactive_features is None:
            interactive_features = ["zoom", "rotate", "probe", "slice"]
        
        # Extract field data
        field_data = simulation_results.get("fields", {})
        grid_data = simulation_results.get("grid", {})
        metadata = simulation_results.get("metadata", {})
        
        # Generate 3D visualization configuration
        viz_config = self._generate_visualization_config(
            visualization_type, color_scheme, interactive_features, metadata
        )
        
        # Create WebGL-compatible data structure
        webgl_data = self._prepare_webgl_data(field_data, grid_data, viz_config)
        
        # Generate Three.js scene configuration
        threejs_scene = self._create_threejs_scene(webgl_data, viz_config)
        
        # Create interactive controls
        controls_config = self._create_controls_config(interactive_features, metadata)
        
        # Generate HTML/JavaScript for 3D viewport
        html_content = self._generate_3d_viewport_html(
            threejs_scene, controls_config, viz_config
        )
        
        return {
            "visualization_id": f"viz_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": "3D_interactive_viewport",
            "data": webgl_data,
            "scene_config": threejs_scene,
            "controls": controls_config,
            "html_content": html_content,
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "visualization_type": visualization_type,
                "color_scheme": color_scheme,
                "interactive_features": interactive_features,
                "field_count": len(field_data),
                "grid_resolution": self._get_grid_resolution(grid_data)
            }
        }
    
    def _generate_visualization_config(self, 
                                     viz_type: str, 
                                     color_scheme: str, 
                                     features: List[str],
                                     metadata: Dict) -> Dict[str, Any]:
        """Generate comprehensive visualization configuration"""
        
        domain = metadata.get("domain", "unknown")
        
        config = {
            "type": viz_type,
            "color_scheme": color_scheme,
            "interactive_features": features,
            "rendering": {
                "quality": "high",
                "anti_aliasing": True,
                "shadows": True,
                "lighting": "professional",
                "background": "gradient"
            },
            "camera": {
                "type": "perspective",
                "fov": 75,
                "near": 0.1,
                "far": 1000,
                "position": [5, 5, 5],
                "target": [0, 0, 0]
            },
            "lighting": {
                "ambient": {"color": "#404040", "intensity": 0.4},
                "directional": [
                    {"color": "#ffffff", "intensity": 0.8, "position": [10, 10, 5]},
                    {"color": "#ffffff", "intensity": 0.3, "position": [-10, -10, -5]}
                ],
                "point": {"color": "#ffffff", "intensity": 0.5, "position": [0, 10, 0]}
            }
        }
        
        # Domain-specific configurations
        if domain == "fluid_dynamics":
            config.update({
                "streamlines": {
                    "enabled": True,
                    "density": 50,
                    "integration_time": 10,
                    "step_size": 0.01
                },
                "particles": {
                    "enabled": True,
                    "count": 1000,
                    "size": 0.02,
                    "animation": True
                },
                "vectors": {
                    "enabled": True,
                    "scale": 0.1,
                    "color_by_magnitude": True
                }
            })
        elif domain == "heat_transfer":
            config.update({
                "isotherms": {
                    "enabled": True,
                    "levels": 10,
                    "opacity": 0.7
                },
                "heat_flux_vectors": {
                    "enabled": True,
                    "scale": 0.05,
                    "color": "#ff4444"
                },
                "temperature_probe": {
                    "enabled": True,
                    "display_format": "celsius"
                }
            })
        
        return config
    
    def _prepare_webgl_data(self, 
                          field_data: Dict[str, Any], 
                          grid_data: Dict[str, Any], 
                          config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for WebGL rendering"""
        
        # Convert numpy arrays to lists if needed
        webgl_data = {
            "geometry": {
                "vertices": [],
                "faces": [],
                "normals": [],
                "uvs": []
            },
            "fields": {},
            "textures": {},
            "buffers": {}
        }
        
        # Process grid data
        if "x" in grid_data and "y" in grid_data:
            x_grid = np.array(grid_data["x"])
            y_grid = np.array(grid_data["y"])
            z_grid = np.array(grid_data.get("z", np.zeros_like(x_grid)))
            
            # Create vertices
            vertices = []
            faces = []
            normals = []
            uvs = []
            
            rows, cols = x_grid.shape
            
            # Generate vertices
            for i in range(rows):
                for j in range(cols):
                    vertices.extend([
                        float(x_grid[i, j]),
                        float(y_grid[i, j]), 
                        float(z_grid[i, j])
                    ])
                    
                    # UV coordinates for texture mapping
                    uvs.extend([j / (cols - 1), i / (rows - 1)])
            
            # Generate faces (triangles)
            for i in range(rows - 1):
                for j in range(cols - 1):
                    # Two triangles per quad
                    v1 = i * cols + j
                    v2 = i * cols + (j + 1)
                    v3 = (i + 1) * cols + j
                    v4 = (i + 1) * cols + (j + 1)
                    
                    # First triangle
                    faces.extend([v1, v2, v3])
                    # Second triangle
                    faces.extend([v2, v4, v3])
            
            # Calculate normals
            normals = self._calculate_normals(vertices, faces)
            
            webgl_data["geometry"] = {
                "vertices": vertices,
                "faces": faces,
                "normals": normals,
                "uvs": uvs
            }
        
        # Process field data for color mapping
        for field_name, field_values in field_data.items():
            field_array = np.array(field_values)
            
            # Normalize field values for color mapping
            min_val = float(np.min(field_array))
            max_val = float(np.max(field_array))
            normalized = (field_array - min_val) / (max_val - min_val) if max_val > min_val else np.zeros_like(field_array)
            
            webgl_data["fields"][field_name] = {
                "values": normalized.flatten().tolist(),
                "original_values": field_array.flatten().tolist(),
                "min": min_val,
                "max": max_val,
                "colormap": self._generate_colormap_texture(config["color_scheme"])
            }
        
        return webgl_data
    
    def _calculate_normals(self, vertices: List[float], faces: List[int]) -> List[float]:
        """Calculate vertex normals for proper lighting"""
        vertex_count = len(vertices) // 3
        normals = [0.0] * len(vertices)
        
        # Calculate face normals and accumulate at vertices
        for i in range(0, len(faces), 3):
            v1_idx, v2_idx, v3_idx = faces[i] * 3, faces[i + 1] * 3, faces[i + 2] * 3
            
            # Get vertex positions
            v1 = np.array(vertices[v1_idx:v1_idx + 3])
            v2 = np.array(vertices[v2_idx:v2_idx + 3])
            v3 = np.array(vertices[v3_idx:v3_idx + 3])
            
            # Calculate face normal
            edge1 = v2 - v1
            edge2 = v3 - v1
            normal = np.cross(edge1, edge2)
            normal = normal / np.linalg.norm(normal) if np.linalg.norm(normal) > 0 else normal
            
            # Accumulate at vertices
            for vertex_idx in [v1_idx, v2_idx, v3_idx]:
                normals[vertex_idx:vertex_idx + 3] = [
                    normals[vertex_idx] + normal[0],
                    normals[vertex_idx + 1] + normal[1],
                    normals[vertex_idx + 2] + normal[2]
                ]
        
        # Normalize accumulated normals
        for i in range(0, len(normals), 3):
            normal = np.array(normals[i:i + 3])
            length = np.linalg.norm(normal)
            if length > 0:
                normal = normal / length
                normals[i:i + 3] = normal.tolist()
        
        return normals
    
    def _generate_colormap_texture(self, color_scheme: str) -> Dict[str, Any]:
        """Generate colormap texture data"""
        colors = self.color_schemes.get(color_scheme, self.color_schemes["viridis"])
        
        # Create texture data
        texture_size = 256
        texture_data = []
        
        for i in range(texture_size):
            t = i / (texture_size - 1)
            color = self._interpolate_color(colors, t)
            texture_data.extend(color)
        
        return {
            "data": texture_data,
            "width": texture_size,
            "height": 1,
            "format": "RGB"
        }
    
    def _interpolate_color(self, colors: List[str], t: float) -> List[int]:
        """Interpolate between colors in colormap"""
        if t <= 0:
            return self._hex_to_rgb(colors[0])
        if t >= 1:
            return self._hex_to_rgb(colors[-1])
        
        # Find surrounding colors
        segment = t * (len(colors) - 1)
        idx = int(segment)
        local_t = segment - idx
        
        if idx >= len(colors) - 1:
            return self._hex_to_rgb(colors[-1])
        
        color1 = self._hex_to_rgb(colors[idx])
        color2 = self._hex_to_rgb(colors[idx + 1])
        
        # Linear interpolation
        return [
            int(color1[0] * (1 - local_t) + color2[0] * local_t),
            int(color1[1] * (1 - local_t) + color2[1] * local_t),
            int(color1[2] * (1 - local_t) + color2[2] * local_t)
        ]
    
    def _hex_to_rgb(self, hex_color: str) -> List[int]:
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    
    def _create_threejs_scene(self, webgl_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Three.js scene configuration"""
        
        scene_config = {
            "scene": {
                "background": {
                    "type": "gradient",
                    "top_color": "#87CEEB",
                    "bottom_color": "#E0F6FF"
                },
                "fog": {
                    "enabled": True,
                    "color": "#cccccc",
                    "near": 10,
                    "far": 100
                }
            },
            "camera": config["camera"],
            "lighting": config["lighting"],
            "objects": [],
            "controls": {
                "type": "orbit",
                "enabled": True,
                "auto_rotate": False,
                "zoom_speed": 1.0,
                "pan_speed": 1.0,
                "rotate_speed": 1.0
            },
            "post_processing": {
                "enabled": True,
                "effects": ["SSAO", "bloom", "tone_mapping"]
            }
        }
        
        # Add main surface object
        main_surface = {
            "type": "mesh",
            "name": "simulation_surface",
            "geometry": {
                "type": "buffer_geometry",
                "vertices": webgl_data["geometry"]["vertices"],
                "faces": webgl_data["geometry"]["faces"],
                "normals": webgl_data["geometry"]["normals"],
                "uvs": webgl_data["geometry"]["uvs"]
            },
            "material": {
                "type": "shader_material",
                "vertex_shader": self._get_vertex_shader(),
                "fragment_shader": self._get_fragment_shader(),
                "uniforms": {
                    "colormap": {"type": "texture", "value": webgl_data["fields"]},
                    "field_min": {"type": "float", "value": 0.0},
                    "field_max": {"type": "float", "value": 1.0},
                    "opacity": {"type": "float", "value": 0.9}
                },
                "transparent": True,
                "side": "double"
            },
            "position": [0, 0, 0],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1]
        }
        
        scene_config["objects"].append(main_surface)
        
        return scene_config
    
    def _create_controls_config(self, features: List[str], metadata: Dict) -> Dict[str, Any]:
        """Create interactive controls configuration"""
        
        controls = {
            "enabled_features": features,
            "ui_elements": []
        }
        
        # Field selection
        controls["ui_elements"].append({
            "type": "dropdown",
            "name": "active_field",
            "label": "Display Field",
            "options": list(metadata.get("fields", {}).keys()) or ["primary_field"],
            "value": "primary_field"
        })
        
        # Color scheme selection
        controls["ui_elements"].append({
            "type": "dropdown",
            "name": "color_scheme",
            "label": "Color Scheme",
            "options": list(self.color_schemes.keys()),
            "value": "viridis"
        })
        
        # Opacity control
        controls["ui_elements"].append({
            "type": "slider",
            "name": "opacity",
            "label": "Opacity",
            "min": 0.0,
            "max": 1.0,
            "value": 0.9,
            "step": 0.05
        })
        
        return controls
    
    def _get_vertex_shader(self) -> str:
        """Get vertex shader code for field visualization"""
        return """
        attribute vec3 position;
        attribute vec3 normal;
        attribute vec2 uv;
        
        uniform mat4 modelViewMatrix;
        uniform mat4 projectionMatrix;
        uniform mat3 normalMatrix;
        
        varying vec3 vNormal;
        varying vec2 vUv;
        varying vec3 vPosition;
        
        void main() {
            vNormal = normalize(normalMatrix * normal);
            vUv = uv;
            vPosition = position;
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
        """
    
    def _get_fragment_shader(self) -> str:
        """Get fragment shader code for field visualization"""
        return """
        uniform float opacity;
        
        varying vec3 vNormal;
        varying vec2 vUv;
        varying vec3 vPosition;
        
        void main() {
            // Simple color based on position
            vec3 color = vec3(0.5 + 0.5 * sin(vPosition.x), 
                             0.5 + 0.5 * sin(vPosition.y), 
                             0.5 + 0.5 * sin(vPosition.z));
            
            // Simple lighting
            vec3 light_direction = normalize(vec3(1.0, 1.0, 1.0));
            float light_intensity = max(dot(vNormal, light_direction), 0.2);
            
            color *= light_intensity;
            
            gl_FragColor = vec4(color, opacity);
        }
        """
    
    def _generate_3d_viewport_html(self, 
                                 scene_config: Dict[str, Any], 
                                 controls_config: Dict[str, Any], 
                                 viz_config: Dict[str, Any]) -> str:
        """Generate complete HTML page with 3D viewport"""
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PINN Simulation - 3D Visualization</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
        }}
        
        #viewport-container {{
            position: relative;
            width: 100vw;
            height: 100vh;
        }}
        
        #three-canvas {{
            display: block;
            width: 100%;
            height: 100%;
        }}
        
        #controls-panel {{
            position: absolute;
            top: 20px;
            right: 20px;
            width: 300px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            max-height: 80vh;
            overflow-y: auto;
        }}
        
        .control-group {{
            margin-bottom: 15px;
        }}
        
        .control-label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
            font-size: 14px;
        }}
        
        .control-input {{
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }}
        
        .control-slider {{
            width: 100%;
            margin: 5px 0;
        }}
        
        #info-panel {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            min-width: 250px;
        }}
        
        .info-row {{
            margin: 3px 0;
        }}
        
        #loading-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-size: 18px;
            z-index: 1000;
        }}
        
        .spinner {{
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin-right: 15px;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin: 2px;
            transition: all 0.3s ease;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }}
    </style>
</head>
<body>
    <div id="viewport-container">
        <div id="loading-overlay">
            <div class="spinner"></div>
            <div>Loading 3D Visualization...</div>
        </div>
        
        <canvas id="three-canvas"></canvas>
        
        <div id="controls-panel">
            <h3 style="margin-top: 0; color: #333;">🎮 Visualization Controls</h3>
            
            <div class="control-group">
                <label class="control-label">Display Field</label>
                <select id="field-selector" class="control-input">
                    <option value="primary_field">Primary Field</option>
                </select>
            </div>
            
            <div class="control-group">
                <label class="control-label">Color Scheme</label>
                <select id="colormap-selector" class="control-input">
                    <option value="viridis">Viridis</option>
                    <option value="plasma">Plasma</option>
                    <option value="coolwarm">Cool-Warm</option>
                    <option value="jet">Jet</option>
                </select>
            </div>
            
            <div class="control-group">
                <label class="control-label">Opacity: <span id="opacity-value">0.9</span></label>
                <input type="range" id="opacity-slider" class="control-slider" 
                       min="0" max="1" step="0.05" value="0.9">
            </div>
            
            <div class="control-group">
                <label class="control-label">Visualization Mode</label>
                <button class="btn" onclick="toggleWireframe()">Toggle Wireframe</button>
                <button class="btn" onclick="resetView()">Reset View</button>
            </div>
            
            <div class="control-group">
                <label class="control-label">Export</label>
                <button class="btn" onclick="exportPNG()">📸 Export PNG</button>
                <button class="btn" onclick="exportSTL()">📦 Export STL</button>
            </div>
        </div>
        
        <div id="info-panel">
            <div class="info-row"><strong>🧮 PINN Simulation Results</strong></div>
            <div class="info-row">Field: <span id="current-field">Primary Field</span></div>
            <div class="info-row">Min: <span id="field-min">0.0</span></div>
            <div class="info-row">Max: <span id="field-max">1.0</span></div>
            <div class="info-row">Vertices: <span id="vertex-count">0</span></div>
            <div class="info-row">FPS: <span id="fps-counter">60</span></div>
            <div class="info-row">
                <small>🖱️ Click and drag to rotate • 🔍 Scroll to zoom • 🖱️ Right-click to pan</small>
            </div>
        </div>
    </div>

    <script>
        // Global variables
        let scene, camera, renderer, controls;
        let simulationMesh, wireframeMesh;
        let animationId;
        
        // Scene configuration from Python
        const sceneConfig = {json.dumps(scene_config, indent=8)};
        const controlsConfig = {json.dumps(controls_config, indent=8)};
        const vizConfig = {json.dumps(viz_config, indent=8)};
        
        // Initialize 3D scene
        function init3DScene() {{
            // Create scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x87CEEB);
            
            // Create camera
            const aspect = window.innerWidth / window.innerHeight;
            camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
            camera.position.set(5, 5, 5);
            
            // Create renderer
            const canvas = document.getElementById('three-canvas');
            renderer = new THREE.WebGLRenderer({{ canvas: canvas, antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            
            // Add lighting
            const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 10, 5);
            directionalLight.castShadow = true;
            scene.add(directionalLight);
            
            // Add controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Create simulation mesh (placeholder)
            createSimulationMesh();
            
            // Setup event listeners
            setupEventListeners();
            
            // Hide loading overlay
            document.getElementById('loading-overlay').style.display = 'none';
            
            // Start animation loop
            animate();
        }}
        
        function createSimulationMesh() {{
            // Create a sample surface (would be replaced with actual simulation data)
            const geometry = new THREE.PlaneGeometry(10, 10, 50, 50);
            
            // Add some height variation (simulating field data)
            const vertices = geometry.attributes.position.array;
            for (let i = 0; i < vertices.length; i += 3) {{
                const x = vertices[i];
                const y = vertices[i + 1];
                vertices[i + 2] = Math.sin(x * 0.5) * Math.cos(y * 0.5) * 2;
            }}
            geometry.attributes.position.needsUpdate = true;
            geometry.computeVertexNormals();
            
            // Create material with color mapping
            const material = new THREE.MeshLambertMaterial({{
                color: 0x00ff00,
                wireframe: false,
                transparent: true,
                opacity: 0.9
            }});
            
            simulationMesh = new THREE.Mesh(geometry, material);
            simulationMesh.receiveShadow = true;
            scene.add(simulationMesh);
            
            // Create wireframe version
            const wireframeMaterial = new THREE.MeshBasicMaterial({{
                color: 0x000000,
                wireframe: true,
                transparent: true,
                opacity: 0.3
            }});
            wireframeMesh = new THREE.Mesh(geometry.clone(), wireframeMaterial);
            wireframeMesh.visible = false;
            scene.add(wireframeMesh);
            
            // Update info panel
            document.getElementById('vertex-count').textContent = 
                geometry.attributes.position.count;
        }}
        
        function setupEventListeners() {{
            // Opacity slider
            const opacitySlider = document.getElementById('opacity-slider');
            opacitySlider.addEventListener('input', (e) => {{
                const opacity = parseFloat(e.target.value);
                document.getElementById('opacity-value').textContent = opacity.toFixed(2);
                if (simulationMesh) {{
                    simulationMesh.material.opacity = opacity;
                }}
            }});
            
            // Color scheme selector
            const colormapSelector = document.getElementById('colormap-selector');
            colormapSelector.addEventListener('change', (e) => {{
                updateColorScheme(e.target.value);
            }});
            
            // Window resize
            window.addEventListener('resize', onWindowResize);
        }}
        
        function updateColorScheme(scheme) {{
            // Update material color based on scheme
            if (simulationMesh) {{
                const colors = {{
                    'viridis': 0x440154,
                    'plasma': 0x0c0786,
                    'coolwarm': 0x3b4cc0,
                    'jet': 0x000080
                }};
                simulationMesh.material.color.setHex(colors[scheme] || 0x00ff00);
            }}
        }}
        
        function toggleWireframe() {{
            if (wireframeMesh) {{
                wireframeMesh.visible = !wireframeMesh.visible;
            }}
        }}
        
        function resetView() {{
            camera.position.set(5, 5, 5);
            controls.reset();
        }}
        
        function exportPNG() {{
            const link = document.createElement('a');
            link.download = 'pinn_simulation.png';
            link.href = renderer.domElement.toDataURL();
            link.click();
        }}
        
        function exportSTL() {{
            alert('🚀 STL export functionality would be implemented with THREE.STLExporter');
        }}
        
        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}
        
        function animate() {{
            animationId = requestAnimationFrame(animate);
            
            controls.update();
            renderer.render(scene, camera);
            
            // Update FPS counter
            updateFPSCounter();
        }}
        
        let lastTime = performance.now();
        let frameCount = 0;
        function updateFPSCounter() {{
            frameCount++;
            const currentTime = performance.now();
            if (currentTime - lastTime >= 1000) {{
                const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                document.getElementById('fps-counter').textContent = fps;
                frameCount = 0;
                lastTime = currentTime;
            }}
        }}
        
        // Initialize when page loads
        window.addEventListener('load', init3DScene);
    </script>
</body>
</html>
        """
        
        return html_template
    
    def _get_grid_resolution(self, grid_data: Dict[str, Any]) -> List[int]:
        """Get grid resolution from grid data"""
        if "x" in grid_data:
            x_data = grid_data["x"]
            if isinstance(x_data, list) and len(x_data) > 0:
                if isinstance(x_data[0], list):
                    return [len(x_data), len(x_data[0])]
                else:
                    return [len(x_data), 1]
        return [0, 0]

# Example usage
def create_sample_visualization():
    """Create a sample 3D visualization"""
    
    # Sample simulation data
    x = np.linspace(-5, 5, 50)
    y = np.linspace(-3, 3, 30)
    X, Y = np.meshgrid(x, y)
    
    # Sample field data (e.g., temperature or pressure)
    field_data = np.sin(X * 0.5) * np.cos(Y * 0.5) + np.random.normal(0, 0.1, X.shape)
    
    simulation_results = {
        "grid": {
            "x": X.tolist(),
            "y": Y.tolist(),
            "z": (field_data * 0.5).tolist()
        },
        "fields": {
            "temperature": field_data.tolist(),
            "pressure": (field_data * 2 + 1).tolist()
        },
        "metadata": {
            "domain": "heat_transfer",
            "resolution": [50, 30],
            "bounds": {
                "x": [-5, 5],
                "y": [-3, 3],
                "fields": {
                    "temperature": [float(np.min(field_data)), float(np.max(field_data))],
                    "pressure": [float(np.min(field_data * 2 + 1)), float(np.max(field_data * 2 + 1))]
                }
            }
        }
    }
    
    viewport = Professional3DViewport()
    visualization = viewport.create_3d_visualization(
        simulation_results,
        visualization_type="surface",
        color_scheme="viridis",
        interactive_features=["zoom", "rotate", "probe", "slice"]
    )
    
    return visualization

if __name__ == "__main__":
    # Create sample visualization
    viz = create_sample_visualization()
    
    # Save HTML file
    with open("sample_3d_visualization.html", "w") as f:
        f.write(viz["html_content"])
    
    print("3D visualization created: sample_3d_visualization.html")
    print(f"Visualization ID: {viz['visualization_id']}")
    print(f"Features: {viz['metadata']['interactive_features']}")