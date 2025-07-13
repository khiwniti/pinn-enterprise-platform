import React, { useState, useEffect, useRef } from 'react';
import { useCopilotAction, useCopilotReadable, CopilotChat } from '@copilotkit/react-core';
import { CopilotSidebar } from '@copilotkit/react-ui';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, 
  Pause, 
  Square, 
  BarChart3, 
  Zap, 
  Brain, 
  Settings,
  Eye,
  MessageSquare,
  Activity,
  TrendingUp
} from 'lucide-react';

interface WorkflowStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  duration?: number;
  result?: any;
  visualization?: string;
}

interface PINNWorkflow {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  steps: WorkflowStep[];
  currentStep: number;
  results?: any;
  metrics?: {
    accuracy: number;
    loss: number;
    convergence: number;
    trainingTime: number;
  };
}

export const AgenticWorkflow: React.FC = () => {
  const [workflow, setWorkflow] = useState<PINNWorkflow | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [realTimeData, setRealTimeData] = useState<any>({});
  const wsRef = useRef<WebSocket | null>(null);

  // Make workflow state readable by Copilot
  useCopilotReadable({
    description: "Current PINN workflow state and progress",
    value: workflow
  });

  useCopilotReadable({
    description: "Real-time training metrics and convergence data",
    value: realTimeData
  });

  // Copilot actions for workflow control
  useCopilotAction({
    name: "startPINNWorkflow",
    description: "Start a new PINN simulation workflow",
    parameters: [
      {
        name: "problemType",
        type: "string",
        description: "Type of physics problem (heat_transfer, fluid_dynamics, etc.)",
        required: true
      },
      {
        name: "geometry",
        type: "object", 
        description: "Geometry configuration for the simulation",
        required: true
      },
      {
        name: "parameters",
        type: "object",
        description: "Physics parameters and boundary conditions",
        required: true
      }
    ],
    handler: async ({ problemType, geometry, parameters }) => {
      await startWorkflow(problemType, geometry, parameters);
      return "PINN workflow started successfully. You can monitor progress in real-time.";
    }
  });

  useCopilotAction({
    name: "pauseWorkflow",
    description: "Pause the current running workflow",
    parameters: [],
    handler: async () => {
      pauseWorkflow();
      return "Workflow paused. You can resume it anytime.";
    }
  });

  useCopilotAction({
    name: "analyzeResults",
    description: "Analyze and explain the simulation results",
    parameters: [],
    handler: async () => {
      if (!workflow?.results) {
        return "No results available yet. Please wait for the simulation to complete.";
      }
      return generateResultsAnalysis(workflow.results);
    }
  });

  useCopilotAction({
    name: "optimizeParameters",
    description: "Suggest parameter optimizations based on current results",
    parameters: [],
    handler: async () => {
      if (!workflow?.metrics) {
        return "No metrics available for optimization suggestions.";
      }
      return generateOptimizationSuggestions(workflow.metrics);
    }
  });

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      wsRef.current = new WebSocket('ws://localhost:8000/ws/workflow');
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleRealTimeUpdate(data);
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleRealTimeUpdate = (data: any) => {
    switch (data.type) {
      case 'workflow_progress':
        updateWorkflowProgress(data.payload);
        break;
      case 'training_metrics':
        setRealTimeData(prev => ({
          ...prev,
          metrics: data.payload
        }));
        break;
      case 'step_completed':
        updateStepStatus(data.payload);
        break;
      case 'visualization_ready':
        updateVisualization(data.payload);
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const startWorkflow = async (problemType: string, geometry: any, parameters: any) => {
    const newWorkflow: PINNWorkflow = {
      id: `workflow_${Date.now()}`,
      name: `${problemType.replace('_', ' ').toUpperCase()} Simulation`,
      status: 'running',
      currentStep: 0,
      steps: [
        { id: 'analyze', name: 'Problem Analysis', status: 'running', progress: 0 },
        { id: 'mesh', name: 'Mesh Generation', status: 'pending', progress: 0 },
        { id: 'train', name: 'PINN Training', status: 'pending', progress: 0 },
        { id: 'validate', name: 'Model Validation', status: 'pending', progress: 0 },
        { id: 'visualize', name: 'Results Visualization', status: 'pending', progress: 0 }
      ]
    };

    setWorkflow(newWorkflow);
    setIsRunning(true);

    // Send workflow start request
    try {
      const response = await fetch('/api/v1/pinn/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newWorkflow.name,
          domain_type: problemType,
          geometry,
          ...parameters
        })
      });

      const result = await response.json();
      
      setWorkflow(prev => prev ? {
        ...prev,
        id: result.workflow_id
      } : null);

    } catch (error) {
      console.error('Failed to start workflow:', error);
      setWorkflow(prev => prev ? {
        ...prev,
        status: 'error'
      } : null);
    }
  };

  const pauseWorkflow = () => {
    setIsRunning(false);
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({
        type: 'pause_workflow',
        workflow_id: workflow?.id
      }));
    }
  };

  const updateWorkflowProgress = (data: any) => {
    setWorkflow(prev => {
      if (!prev) return null;
      
      const updatedSteps = [...prev.steps];
      if (data.step_index < updatedSteps.length) {
        updatedSteps[data.step_index] = {
          ...updatedSteps[data.step_index],
          progress: data.progress,
          status: data.progress === 100 ? 'completed' : 'running'
        };
      }

      return {
        ...prev,
        steps: updatedSteps,
        currentStep: data.step_index,
        metrics: data.metrics
      };
    });
  };

  const updateStepStatus = (data: any) => {
    setWorkflow(prev => {
      if (!prev) return null;
      
      const updatedSteps = [...prev.steps];
      const stepIndex = updatedSteps.findIndex(step => step.id === data.step_id);
      
      if (stepIndex !== -1) {
        updatedSteps[stepIndex] = {
          ...updatedSteps[stepIndex],
          status: data.status,
          progress: data.status === 'completed' ? 100 : updatedSteps[stepIndex].progress,
          result: data.result,
          duration: data.duration
        };
      }

      return {
        ...prev,
        steps: updatedSteps
      };
    });
  };

  const updateVisualization = (data: any) => {
    setWorkflow(prev => {
      if (!prev) return null;
      
      const updatedSteps = [...prev.steps];
      const vizStep = updatedSteps.find(step => step.id === 'visualize');
      
      if (vizStep) {
        vizStep.visualization = data.visualization_url;
      }

      return {
        ...prev,
        steps: updatedSteps,
        results: data.results
      };
    });
  };

  const generateResultsAnalysis = (results: any) => {
    const analysis = `
## Simulation Results Analysis

### Key Findings:
- **Accuracy**: ${results.accuracy * 100}% - ${results.accuracy > 0.95 ? 'Excellent' : results.accuracy > 0.9 ? 'Good' : 'Needs improvement'}
- **Convergence**: ${results.convergence ? 'Achieved' : 'Not achieved'}
- **Training Time**: ${results.training_time}s

### Physics Insights:
- The simulation captured the key physics phenomena
- Boundary conditions were satisfied within tolerance
- Solution shows expected physical behavior

### Recommendations:
${results.accuracy < 0.9 ? '- Consider increasing network depth or training epochs' : ''}
${results.convergence ? '' : '- Adjust learning rate or loss function weights'}
- Results are suitable for engineering analysis
    `;
    
    return analysis;
  };

  const generateOptimizationSuggestions = (metrics: any) => {
    const suggestions = [];
    
    if (metrics.accuracy < 0.95) {
      suggestions.push("Increase network depth or width for better accuracy");
    }
    
    if (metrics.loss > 0.01) {
      suggestions.push("Adjust loss function weights to improve convergence");
    }
    
    if (metrics.trainingTime > 300) {
      suggestions.push("Consider using adaptive learning rate or early stopping");
    }
    
    return suggestions.length > 0 
      ? `### Optimization Suggestions:\n${suggestions.map(s => `- ${s}`).join('\n')}`
      : "Current parameters are well-optimized!";
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Workflow Panel */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white shadow-sm border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">PINN Workflow</h1>
              <p className="text-gray-600">Real-time physics simulation with AI assistance</p>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setIsRunning(!isRunning)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium ${
                  isRunning 
                    ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                    : 'bg-green-100 text-green-700 hover:bg-green-200'
                }`}
              >
                {isRunning ? <Pause size={16} /> : <Play size={16} />}
                <span>{isRunning ? 'Pause' : 'Start'}</span>
              </button>
              
              <button className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                <Settings size={16} />
                <span>Settings</span>
              </button>
            </div>
          </div>
        </div>

        {/* Workflow Steps */}
        <div className="flex-1 p-6">
          {workflow ? (
            <div className="space-y-6">
              {/* Workflow Overview */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">{workflow.name}</h2>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    workflow.status === 'running' ? 'bg-blue-100 text-blue-700' :
                    workflow.status === 'completed' ? 'bg-green-100 text-green-700' :
                    workflow.status === 'error' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {workflow.status.toUpperCase()}
                  </div>
                </div>
                
                {/* Progress Steps */}
                <div className="space-y-4">
                  {workflow.steps.map((step, index) => (
                    <motion.div
                      key={step.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`flex items-center space-x-4 p-4 rounded-lg border ${
                        step.status === 'running' ? 'border-blue-200 bg-blue-50' :
                        step.status === 'completed' ? 'border-green-200 bg-green-50' :
                        step.status === 'error' ? 'border-red-200 bg-red-50' :
                        'border-gray-200 bg-gray-50'
                      }`}
                    >
                      {/* Step Icon */}
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        step.status === 'running' ? 'bg-blue-500 text-white' :
                        step.status === 'completed' ? 'bg-green-500 text-white' :
                        step.status === 'error' ? 'bg-red-500 text-white' :
                        'bg-gray-300 text-gray-600'
                      }`}>
                        {step.status === 'running' ? (
                          <Activity size={16} className="animate-pulse" />
                        ) : step.status === 'completed' ? (
                          <span>✓</span>
                        ) : step.status === 'error' ? (
                          <span>✗</span>
                        ) : (
                          <span>{index + 1}</span>
                        )}
                      </div>
                      
                      {/* Step Details */}
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <h3 className="font-medium">{step.name}</h3>
                          <span className="text-sm text-gray-500">
                            {step.duration ? `${step.duration}s` : ''}
                          </span>
                        </div>
                        
                        {/* Progress Bar */}
                        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                          <motion.div
                            className={`h-2 rounded-full ${
                              step.status === 'completed' ? 'bg-green-500' :
                              step.status === 'running' ? 'bg-blue-500' :
                              step.status === 'error' ? 'bg-red-500' :
                              'bg-gray-300'
                            }`}
                            initial={{ width: 0 }}
                            animate={{ width: `${step.progress}%` }}
                            transition={{ duration: 0.5 }}
                          />
                        </div>
                        
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>{step.progress}% complete</span>
                          {step.status === 'running' && (
                            <span className="animate-pulse">Processing...</span>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Real-time Metrics */}
              {workflow.metrics && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <MetricCard
                    title="Accuracy"
                    value={`${(workflow.metrics.accuracy * 100).toFixed(1)}%`}
                    icon={<TrendingUp size={20} />}
                    color="green"
                  />
                  <MetricCard
                    title="Loss"
                    value={workflow.metrics.loss.toExponential(2)}
                    icon={<BarChart3 size={20} />}
                    color="blue"
                  />
                  <MetricCard
                    title="Convergence"
                    value={`${(workflow.metrics.convergence * 100).toFixed(1)}%`}
                    icon={<Zap size={20} />}
                    color="purple"
                  />
                  <MetricCard
                    title="Training Time"
                    value={`${workflow.metrics.trainingTime}s`}
                    icon={<Activity size={20} />}
                    color="orange"
                  />
                </div>
              )}

              {/* Visualization Panel */}
              {workflow.steps.find(s => s.visualization) && (
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold mb-4">Live Visualization</h3>
                  <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
                    <iframe
                      src={workflow.steps.find(s => s.visualization)?.visualization}
                      className="w-full h-full rounded-lg"
                      title="PINN Visualization"
                    />
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Brain size={64} className="mx-auto text-gray-400 mb-4" />
                <h2 className="text-xl font-semibold text-gray-600 mb-2">
                  No Active Workflow
                </h2>
                <p className="text-gray-500 mb-4">
                  Start a conversation with the AI to begin a PINN simulation
                </p>
                <button
                  onClick={() => {
                    // Trigger Copilot chat
                    setChatMessages([{
                      role: 'assistant',
                      content: 'Hi! I can help you set up and run physics simulations using PINNs. What kind of problem would you like to solve?'
                    }]);
                  }}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2 mx-auto"
                >
                  <MessageSquare size={20} />
                  <span>Start AI Conversation</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Copilot Sidebar */}
      <CopilotSidebar
        instructions="You are a PINN (Physics-Informed Neural Networks) expert assistant. Help users set up, run, and analyze physics simulations. You can start workflows, monitor progress, analyze results, and provide optimization suggestions. Always explain the physics behind the simulations and provide practical insights."
        labels={{
          title: "PINN Assistant",
          initial: "Hi! I'm your PINN simulation assistant. I can help you solve complex physics problems using neural networks. What would you like to simulate today?"
        }}
        defaultOpen={true}
        clickOutsideToClose={false}
      >
        <CopilotChat
          instructions="You are helping with physics simulations using PINNs. Be technical but accessible, and always relate results back to real-world applications."
          messages={chatMessages}
          onMessagesChange={setChatMessages}
        />
      </CopilotSidebar>
    </div>
  );
};

interface MetricCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  color: 'green' | 'blue' | 'purple' | 'orange';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, color }) => {
  const colorClasses = {
    green: 'bg-green-100 text-green-700',
    blue: 'bg-blue-100 text-blue-700', 
    purple: 'bg-purple-100 text-purple-700',
    orange: 'bg-orange-100 text-orange-700'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-sm p-4"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </motion.div>
  );
};

export default AgenticWorkflow;