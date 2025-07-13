import React, { useState, useEffect, useRef } from 'react';
import { 
  useCopilotAction, 
  useCopilotReadable, 
  CopilotChat,
  useCopilotChatSuggestions 
} from '@copilotkit/react-core';
import { CopilotSidebar } from '@copilotkit/react-ui';
import { motion, AnimatePresence } from 'framer-motion';

interface PINNWorkflowState {
  workflowId?: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  currentStep?: string;
  progress?: number;
  metrics?: {
    accuracy: number;
    loss: number;
    convergence: number;
    trainingTime: number;
  };
  results?: any;
}

interface WebSocketMessage {
  type: string;
  payload?: any;
  timestamp?: string;
}

export const PINNWorkflowAgent: React.FC = () => {
  const [workflowState, setWorkflowState] = useState<PINNWorkflowState>({ status: 'idle' });
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  // Make workflow state readable by Copilot
  useCopilotReadable({
    description: "Current PINN workflow state, including progress, metrics, and results",
    value: workflowState
  });

  useCopilotReadable({
    description: "WebSocket connection status for real-time updates",
    value: { connected: isConnected, hasActiveWorkflow: !!workflowState.workflowId }
  });

  // Chat suggestions based on workflow state
  useCopilotChatSuggestions({
    instructions: "Suggest helpful actions based on the current PINN workflow state",
    minSuggestions: 2,
    maxSuggestions: 4
  });

  // Copilot Actions
  useCopilotAction({
    name: "startFluidDynamicsSimulation",
    description: "Start a fluid dynamics PINN simulation (like golf ball aerodynamics)",
    parameters: [
      {
        name: "objectType",
        type: "string",
        description: "Type of object (golf_ball, cylinder, airfoil, etc.)",
        required: true
      },
      {
        name: "velocity",
        type: "number",
        description: "Flow velocity in m/s",
        required: true
      },
      {
        name: "geometry",
        type: "object",
        description: "Geometry parameters (radius, dimensions, etc.)",
        required: false
      }
    ],
    handler: async ({ objectType, velocity, geometry }) => {
      const config = {
        name: `${objectType.replace('_', ' ').toUpperCase()} Aerodynamics`,
        domain_type: "fluid_dynamics",
        geometry: geometry || { type: "circle", radius: 0.021 },
        boundary_conditions: {
          inlet: { velocity: [velocity, 0.0] },
          object_surface: { type: "no_slip_wall" }
        },
        physics_parameters: {
          reynolds_number: velocity * 0.042 / 1.5e-5, // Approximate Re
          turbulence_model: "k_epsilon"
        }
      };

      await startWorkflow(config);
      return `Started ${objectType} aerodynamics simulation at ${velocity} m/s. Monitoring real-time progress...`;
    }
  });

  useCopilotAction({
    name: "startHeatTransferSimulation", 
    description: "Start a heat transfer PINN simulation",
    parameters: [
      {
        name: "geometry",
        type: "string",
        description: "Geometry type (rectangle, circle, complex)",
        required: true
      },
      {
        name: "temperature",
        type: "number",
        description: "Initial temperature in Celsius",
        required: true
      },
      {
        name: "thermalDiffusivity",
        type: "number",
        description: "Thermal diffusivity (default: 1.0)",
        required: false
      }
    ],
    handler: async ({ geometry, temperature, thermalDiffusivity = 1.0 }) => {
      const config = {
        name: `Heat Transfer - ${geometry.toUpperCase()}`,
        domain_type: "heat_transfer",
        geometry: { type: geometry, temperature_initial: temperature },
        physics_parameters: {
          thermal_diffusivity: thermalDiffusivity,
          source_term: 0.0
        }
      };

      await startWorkflow(config);
      return `Started heat transfer simulation with initial temperature ${temperature}°C. Real-time monitoring active.`;
    }
  });

  useCopilotAction({
    name: "analyzeCurrentResults",
    description: "Analyze the current simulation results and provide insights",
    parameters: [],
    handler: async () => {
      if (!workflowState.results) {
        return "No simulation results available yet. Please wait for the simulation to complete or start a new one.";
      }

      const analysis = generateResultsAnalysis(workflowState);
      return analysis;
    }
  });

  useCopilotAction({
    name: "optimizeSimulation",
    description: "Suggest optimizations based on current metrics",
    parameters: [],
    handler: async () => {
      if (!workflowState.metrics) {
        return "No metrics available for optimization. Please run a simulation first.";
      }

      const suggestions = generateOptimizationSuggestions(workflowState.metrics);
      return suggestions;
    }
  });

  useCopilotAction({
    name: "connectRealTimeUpdates",
    description: "Connect to real-time workflow updates via WebSocket",
    parameters: [],
    handler: async () => {
      if (isConnected) {
        return "Already connected to real-time updates.";
      }
      
      connectWebSocket();
      return "Connecting to real-time updates... You'll receive live progress notifications.";
    }
  });

  useCopilotAction({
    name: "explainPhysics",
    description: "Explain the physics behind the current simulation",
    parameters: [
      {
        name: "aspect",
        type: "string", 
        description: "Specific aspect to explain (equations, boundary_conditions, convergence, etc.)",
        required: false
      }
    ],
    handler: async ({ aspect }) => {
      if (!workflowState.workflowId) {
        return "No active simulation to explain. Please start a simulation first.";
      }

      return generatePhysicsExplanation(workflowState, aspect);
    }
  });

  // WebSocket connection management
  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    wsRef.current = new WebSocket('ws://localhost:8000/ws/workflow');
    
    wsRef.current.onopen = () => {
      setIsConnected(true);
      addMessage('system', '🔌 Connected to real-time updates');
    };

    wsRef.current.onmessage = (event) => {
      const data: WebSocketMessage = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
      addMessage('system', '❌ Disconnected from real-time updates');
    };

    wsRef.current.onerror = (error) => {
      addMessage('system', `❌ WebSocket error: ${error}`);
    };
  };

  const handleWebSocketMessage = (data: WebSocketMessage) => {
    switch (data.type) {
      case 'connection_established':
        addMessage('system', `✅ Real-time connection established`);
        break;

      case 'workflow_progress':
        setWorkflowState(prev => ({
          ...prev,
          progress: data.payload.progress,
          currentStep: data.payload.step_index
        }));
        addMessage('progress', `Step ${data.payload.step_index + 1}: ${data.payload.progress}% complete`);
        break;

      case 'training_metrics':
        setWorkflowState(prev => ({
          ...prev,
          metrics: data.payload.metrics
        }));
        addMessage('metrics', `📊 Accuracy: ${(data.payload.metrics.accuracy * 100).toFixed(1)}%, Loss: ${data.payload.metrics.loss.toExponential(2)}`);
        break;

      case 'step_completed':
        addMessage('success', `✅ Completed: ${data.payload.step_id}`);
        break;

      case 'visualization_ready':
        setWorkflowState(prev => ({
          ...prev,
          status: 'completed',
          results: data.payload.results
        }));
        addMessage('success', `🎨 Visualization ready! Results available for analysis.`);
        break;

      default:
        console.log('Unknown WebSocket message:', data);
    }
  };

  const startWorkflow = async (config: any) => {
    try {
      const response = await fetch('/api/v1/pinn/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      const result = await response.json();
      
      setWorkflowState({
        workflowId: result.workflow_id,
        status: 'running',
        progress: 0
      });

      // Subscribe to updates if connected
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'subscribe_workflow',
          workflow_id: result.workflow_id
        }));
      }

      addMessage('success', `🚀 Started workflow: ${result.workflow_id}`);
      
    } catch (error) {
      addMessage('error', `❌ Failed to start workflow: ${error}`);
      setWorkflowState(prev => ({ ...prev, status: 'error' }));
    }
  };

  const addMessage = (type: string, content: string) => {
    const message = {
      role: 'system',
      content: `[${type.toUpperCase()}] ${content}`,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, message]);
  };

  const generateResultsAnalysis = (state: PINNWorkflowState) => {
    if (!state.results || !state.metrics) {
      return "Insufficient data for analysis.";
    }

    const accuracy = state.metrics.accuracy * 100;
    const convergence = state.metrics.convergence * 100;

    return `
## Simulation Results Analysis

### Performance Metrics
- **Accuracy**: ${accuracy.toFixed(1)}% ${accuracy > 95 ? '(Excellent)' : accuracy > 90 ? '(Good)' : '(Needs improvement)'}
- **Convergence**: ${convergence.toFixed(1)}%
- **Training Time**: ${state.metrics.trainingTime.toFixed(1)}s
- **Final Loss**: ${state.metrics.loss.toExponential(2)}

### Physics Insights
${accuracy > 95 ? 
  '✅ The simulation successfully captured the key physics phenomena with high fidelity.' :
  '⚠️ The simulation may need parameter tuning for better accuracy.'
}

### Recommendations
${accuracy < 90 ? '- Consider increasing network depth or training epochs\n' : ''}
${state.metrics.loss > 0.01 ? '- Adjust loss function weights for better convergence\n' : ''}
- Results are ${accuracy > 90 ? 'suitable' : 'preliminary'} for engineering analysis
    `;
  };

  const generateOptimizationSuggestions = (metrics: any) => {
    const suggestions = [];
    
    if (metrics.accuracy < 0.95) {
      suggestions.push("🔧 Increase network depth (add more hidden layers)");
      suggestions.push("📈 Extend training epochs for better convergence");
    }
    
    if (metrics.loss > 0.01) {
      suggestions.push("⚖️ Adjust loss function weights (increase boundary condition weight)");
      suggestions.push("🎯 Use adaptive learning rate scheduling");
    }
    
    if (metrics.trainingTime > 300) {
      suggestions.push("⚡ Implement early stopping to reduce training time");
      suggestions.push("🚀 Consider using GPU acceleration");
    }

    if (suggestions.length === 0) {
      return "🎉 Current parameters are well-optimized! The simulation is performing excellently.";
    }

    return `### Optimization Suggestions:\n${suggestions.map(s => `- ${s}`).join('\n')}`;
  };

  const generatePhysicsExplanation = (state: PINNWorkflowState, aspect?: string) => {
    // This would be more sophisticated in a real implementation
    const explanations = {
      equations: "PINNs solve partial differential equations by embedding physics laws directly into the neural network loss function.",
      boundary_conditions: "Boundary conditions are enforced through penalty terms in the loss function, ensuring physical constraints are satisfied.",
      convergence: "Convergence indicates how well the neural network has learned to satisfy both the PDE and boundary conditions.",
      default: "Physics-Informed Neural Networks combine the power of deep learning with fundamental physics principles to solve complex engineering problems."
    };

    return explanations[aspect as keyof typeof explanations] || explanations.default;
  };

  // Auto-connect on mount
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Content Area */}
      <div className="flex-1 p-6">
        {/* Status Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">🧮 PINN Workflow Agent</h1>
              <p className="text-gray-600">AI-powered physics simulation assistant</p>
            </div>
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>

        {/* Workflow Status */}
        {workflowState.workflowId && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-lg shadow-sm p-6 mb-6"
          >
            <h2 className="text-xl font-semibold mb-4">Active Workflow</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Workflow ID:</span>
                <span className="font-mono text-sm">{workflowState.workflowId}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Status:</span>
                <span className={`px-2 py-1 rounded text-sm ${
                  workflowState.status === 'running' ? 'bg-blue-100 text-blue-700' :
                  workflowState.status === 'completed' ? 'bg-green-100 text-green-700' :
                  workflowState.status === 'error' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {workflowState.status.toUpperCase()}
                </span>
              </div>
              {workflowState.progress !== undefined && (
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{workflowState.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <motion.div
                      className="bg-blue-500 h-2 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${workflowState.progress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Real-time Metrics */}
        {workflowState.metrics && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
          >
            <div className="bg-white rounded-lg shadow-sm p-4">
              <div className="text-sm text-gray-600">Accuracy</div>
              <div className="text-2xl font-bold text-green-600">
                {(workflowState.metrics.accuracy * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4">
              <div className="text-sm text-gray-600">Loss</div>
              <div className="text-2xl font-bold text-blue-600">
                {workflowState.metrics.loss.toExponential(2)}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4">
              <div className="text-sm text-gray-600">Convergence</div>
              <div className="text-2xl font-bold text-purple-600">
                {(workflowState.metrics.convergence * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4">
              <div className="text-sm text-gray-600">Time</div>
              <div className="text-2xl font-bold text-orange-600">
                {workflowState.metrics.trainingTime.toFixed(1)}s
              </div>
            </div>
          </motion.div>
        )}

        {/* Getting Started */}
        {!workflowState.workflowId && (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <div className="text-6xl mb-4">🤖</div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              AI Physics Simulation Assistant
            </h2>
            <p className="text-gray-600 mb-6">
              Start a conversation to begin your PINN simulation journey
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="text-2xl mb-2">🌊</div>
                <h3 className="font-semibold">Fluid Dynamics</h3>
                <p className="text-sm text-gray-600">Golf balls, airfoils, cylinders</p>
              </div>
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="text-2xl mb-2">🔥</div>
                <h3 className="font-semibold">Heat Transfer</h3>
                <p className="text-sm text-gray-600">Conduction, convection, diffusion</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Copilot Sidebar */}
      <CopilotSidebar
        instructions={`You are an expert PINN (Physics-Informed Neural Networks) simulation assistant. 

Your capabilities:
- Start fluid dynamics simulations (golf balls, airfoils, cylinders)
- Start heat transfer simulations 
- Analyze simulation results and provide physics insights
- Suggest optimizations for better accuracy and performance
- Explain the physics and mathematics behind simulations
- Monitor real-time training progress

Current state: ${JSON.stringify(workflowState)}
Connection status: ${isConnected ? 'Connected' : 'Disconnected'}

Be technical but accessible. Always relate results to real-world applications and provide actionable insights.`}
        labels={{
          title: "PINN Assistant",
          initial: "Hi! I'm your PINN simulation expert. I can help you solve complex physics problems using neural networks.\n\nTry saying:\n• 'Simulate golf ball aerodynamics at 45 m/s'\n• 'Start heat transfer simulation'\n• 'Analyze my results'\n• 'Connect real-time updates'"
        }}
        defaultOpen={true}
        clickOutsideToClose={false}
      >
        <CopilotChat
          instructions="Help users with PINN simulations. Be encouraging and educational."
          messages={messages}
          onMessagesChange={setMessages}
        />
      </CopilotSidebar>
    </div>
  );
};

export default PINNWorkflowAgent;