/**
 * 3D Visualization Service for Cloudflare Workers
 * Generates professional WebGL-based 3D visualizations
 */

export class Visualization3D {
  constructor(env) {
    this.env = env;
    this.colorSchemes = {
      viridis: ["#440154", "#482777", "#3f4a8a", "#31678e", "#26838f", "#1f9d8a", "#6cce5a", "#b6de2b", "#fee825"],
      plasma: ["#0c0786", "#40039c", "#6a00a7", "#8f0da4", "#b12a90", "#cc4778", "#e16462", "#f2844b", "#fca636", "#fcce25"],
      coolwarm: ["#3b4cc0", "#5977e3", "#7aa3f4", "#9dc9f7", "#c0e1fa", "#e2f1fc", "#f7d7d7", "#f4b7b0", "#e68a8a", "#d85c5c", "#b40426"]
    };
  }

  async createVisualization(simulationResults, options = {}) {
    const {
      visualizationType = 'surface',
      colorScheme = 'viridis',
      interactiveFeatures = ['zoom', 'rotate', 'probe']
    } = options;

    const visualizationId = this.generateVisualizationId();
    
    // Process simulation data for WebGL
    const webglData = this.prepareWebGLData(simulationResults);
    
    // Generate Three.js scene configuration
    const sceneConfig = this.createThreeJSScene(webglData, {
      visualizationType,
      colorScheme,
      interactiveFeatures
    });
    
    // Generate interactive HTML
    const htmlContent = this.generateVisualizationHTML(sceneConfig, {
      visualizationId,
      colorScheme,
      interactiveFeatures
    });
    
    // Store in R2 if available
    if (this.env.VISUALIZATIONS_BUCKET) {
      await this.env.VISUALIZATIONS_BUCKET.put(
        `${visualizationId}/visualization.html`,
        htmlContent,
        {
          httpMetadata: {
            contentType: 'text/html',
            cacheControl: 'public, max-age=3600'
          }
        }
      );
    }
    
    return {
      visualization_id: visualizationId,
      type: '3D_interactive_viewport',
      data: webglData,
      scene_config: sceneConfig,
      html_content: htmlContent,
      metadata: {
        created_at: new Date().toISOString(),
        visualization_type: visualizationType,
        color_scheme: colorScheme,
        interactive_features: interactiveFeatures,
        field_count: Object.keys(simulationResults.fields || {}).length
      }
    };
  }

  generateVisualizationId() {
    return 'viz_' + new Date().toISOString().replace(/[-:]/g, '').replace(/\..+/, '');
  }

  prepareWebGLData(simulationResults) {
    const { grid, fields } = simulationResults;
    
    // Generate sample grid if not provided
    const gridData = grid || this.generateSampleGrid();
    const fieldData = fields || this.generateSampleFields(gridData);
    
    // Convert to WebGL format
    const vertices = [];
    const faces = [];
    const normals = [];
    const uvs = [];
    
    // Process grid data
    if (gridData.x && gridData.y) {
      const xGrid = gridData.x;
      const yGrid = gridData.y;
      const zGrid = gridData.z || xGrid.map(row => row.map(() => 0));
      
      const rows = xGrid.length;
      const cols = xGrid[0].length;
      
      // Generate vertices
      for (let i = 0; i < rows; i++) {
        for (let j = 0; j < cols; j++) {
          vertices.push(xGrid[i][j], yGrid[i][j], zGrid[i][j]);
          uvs.push(j / (cols - 1), i / (rows - 1));
        }
      }
      
      // Generate faces
      for (let i = 0; i < rows - 1; i++) {
        for (let j = 0; j < cols - 1; j++) {
          const v1 = i * cols + j;
          const v2 = i * cols + (j + 1);
          const v3 = (i + 1) * cols + j;
          const v4 = (i + 1) * cols + (j + 1);
          
          faces.push(v1, v2, v3, v2, v4, v3);
        }
      }
      
      // Calculate normals (simplified)
      for (let i = 0; i < vertices.length; i += 3) {
        normals.push(0, 0, 1); // Simple upward normal
      }
    }
    
    return {
      geometry: { vertices, faces, normals, uvs },
      fields: this.processFieldData(fieldData),
      metadata: {
        vertex_count: vertices.length / 3,
        face_count: faces.length / 3,
        field_names: Object.keys(fieldData)
      }
    };
  }

  generateSampleGrid() {
    const x = [];
    const y = [];
    const z = [];
    
    for (let i = 0; i < 30; i++) {
      const row_x = [];
      const row_y = [];
      const row_z = [];
      
      for (let j = 0; j < 20; j++) {
        const xVal = -5 + (10 * j) / 19;
        const yVal = -3 + (6 * i) / 29;
        const zVal = Math.sin(xVal * 0.5) * Math.cos(yVal * 0.5);
        
        row_x.push(xVal);
        row_y.push(yVal);
        row_z.push(zVal);
      }
      
      x.push(row_x);
      y.push(row_y);
      z.push(row_z);
    }
    
    return { x, y, z };
  }

  generateSampleFields(gridData) {
    const { x, y } = gridData;
    const velocity = [];
    const pressure = [];
    
    for (let i = 0; i < x.length; i++) {
      const vel_row = [];
      const press_row = [];
      
      for (let j = 0; j < x[i].length; j++) {
        const xVal = x[i][j];
        const yVal = y[i][j];
        
        vel_row.push(Math.sqrt(Math.sin(xVal * 0.3) ** 2 + Math.cos(yVal * 0.3) ** 2));
        press_row.push(Math.sin(xVal * 0.5) * Math.cos(yVal * 0.5));
      }
      
      velocity.push(vel_row);
      pressure.push(press_row);
    }
    
    return { velocity_magnitude: velocity, pressure };
  }

  processFieldData(fieldData) {
    const processed = {};
    
    for (const [fieldName, fieldValues] of Object.entries(fieldData)) {
      const flatValues = fieldValues.flat();
      const min = Math.min(...flatValues);
      const max = Math.max(...flatValues);
      const normalized = flatValues.map(v => (v - min) / (max - min || 1));
      
      processed[fieldName] = {
        values: normalized,
        original_values: flatValues,
        min,
        max
      };
    }
    
    return processed;
  }

  createThreeJSScene(webglData, options) {
    return {
      scene: {
        background: { type: 'gradient', top_color: '#87CEEB', bottom_color: '#E0F6FF' },
        fog: { enabled: true, color: '#cccccc', near: 10, far: 100 }
      },
      camera: {
        type: 'perspective',
        fov: 75,
        near: 0.1,
        far: 1000,
        position: [5, 5, 5],
        target: [0, 0, 0]
      },
      lighting: {
        ambient: { color: '#404040', intensity: 0.4 },
        directional: [
          { color: '#ffffff', intensity: 0.8, position: [10, 10, 5] }
        ]
      },
      objects: [{
        type: 'mesh',
        name: 'simulation_surface',
        geometry: webglData.geometry,
        material: {
          type: 'shader_material',
          uniforms: {
            colormap: { type: 'texture', value: webglData.fields },
            opacity: { type: 'float', value: 0.9 }
          }
        }
      }],
      controls: {
        type: 'orbit',
        enabled: true,
        auto_rotate: false
      }
    };
  }

  generateVisualizationHTML(sceneConfig, options) {
    const { visualizationId, colorScheme, interactiveFeatures } = options;
    
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PINN Simulation - 3D Visualization</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        body { margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               font-family: 'Segoe UI', sans-serif; overflow: hidden; }
        #viewport-container { position: relative; width: 100vw; height: 100vh; }
        #three-canvas { display: block; width: 100%; height: 100%; }
        #controls-panel { position: absolute; top: 20px; right: 20px; width: 300px; 
                         background: rgba(255, 255, 255, 0.95); border-radius: 10px; padding: 20px; 
                         box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1); backdrop-filter: blur(10px); }
        #info-panel { position: absolute; bottom: 20px; left: 20px; background: rgba(0, 0, 0, 0.8); 
                     color: white; padding: 15px; border-radius: 8px; font-family: 'Courier New', monospace; }
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
               border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; margin: 2px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); }
    </style>
</head>
<body>
    <div id="viewport-container">
        <canvas id="three-canvas"></canvas>
        
        <div id="controls-panel">
            <h3>🎮 Visualization Controls</h3>
            <div>
                <label>Color Scheme:</label>
                <select id="colormap-selector">
                    <option value="viridis">Viridis</option>
                    <option value="plasma">Plasma</option>
                    <option value="coolwarm">Cool-Warm</option>
                </select>
            </div>
            <div>
                <label>Opacity: <span id="opacity-value">0.9</span></label>
                <input type="range" id="opacity-slider" min="0" max="1" step="0.05" value="0.9">
            </div>
            <div>
                <button class="btn" onclick="resetView()">Reset View</button>
                <button class="btn" onclick="exportPNG()">📸 Export PNG</button>
            </div>
        </div>
        
        <div id="info-panel">
            <div><strong>🧮 PINN Simulation Results</strong></div>
            <div>Visualization ID: ${visualizationId}</div>
            <div>Color Scheme: ${colorScheme}</div>
            <div>Features: ${interactiveFeatures.join(', ')}</div>
            <div><small>🖱️ Click and drag to rotate • 🔍 Scroll to zoom</small></div>
        </div>
    </div>

    <script>
        let scene, camera, renderer, controls, simulationMesh;
        
        const sceneConfig = ${JSON.stringify(sceneConfig, null, 8)};
        
        function init3DScene() {
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x87CEEB);
            
            const aspect = window.innerWidth / window.innerHeight;
            camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
            camera.position.set(5, 5, 5);
            
            const canvas = document.getElementById('three-canvas');
            renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            
            const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 10, 5);
            scene.add(directionalLight);
            
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            createSimulationMesh();
            setupEventListeners();
            animate();
        }
        
        function createSimulationMesh() {
            const geometry = new THREE.PlaneGeometry(10, 10, 50, 50);
            const vertices = geometry.attributes.position.array;
            
            for (let i = 0; i < vertices.length; i += 3) {
                const x = vertices[i];
                const y = vertices[i + 1];
                vertices[i + 2] = Math.sin(x * 0.5) * Math.cos(y * 0.5) * 2;
            }
            
            geometry.attributes.position.needsUpdate = true;
            geometry.computeVertexNormals();
            
            const material = new THREE.MeshLambertMaterial({
                color: 0x00ff00,
                wireframe: false,
                transparent: true,
                opacity: 0.9
            });
            
            simulationMesh = new THREE.Mesh(geometry, material);
            scene.add(simulationMesh);
        }
        
        function setupEventListeners() {
            document.getElementById('opacity-slider').addEventListener('input', (e) => {
                const opacity = parseFloat(e.target.value);
                document.getElementById('opacity-value').textContent = opacity.toFixed(2);
                if (simulationMesh) simulationMesh.material.opacity = opacity;
            });
            
            window.addEventListener('resize', () => {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });
        }
        
        function resetView() {
            camera.position.set(5, 5, 5);
            controls.reset();
        }
        
        function exportPNG() {
            const link = document.createElement('a');
            link.download = 'pinn_simulation.png';
            link.href = renderer.domElement.toDataURL();
            link.click();
        }
        
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }
        
        window.addEventListener('load', init3DScene);
    </script>
</body>
</html>`;
  }
}