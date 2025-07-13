# CoAgents PINN Solver Example

This example demonstrates a Physics-Informed Neural Network (PINN) solver integrated with CopilotKit, allowing users to solve complex physics problems through a conversational interface.

**Features:**
- Conversational interface for defining physics problems
- Automatic PINN architecture selection based on problem complexity
- Real-time training progress monitoring
- Interactive visualization of results
- Support for multiple physics domains (heat transfer, fluid dynamics, structural mechanics)

---

## Architecture Overview

The PINN solver consists of:

1. **Agent Backend**: FastAPI server with CopilotKit integration
2. **Serverless PINN Engine**: AWS Lambda/ECS-based training and inference
3. **UI Frontend**: Next.js application with CopilotKit chat interface
4. **Physics Agents**: Specialized agents for different physics domains

## Running the Agent

**These instructions assume you are in the `coagents-pinn-solver/` directory**

### Backend Setup

First, install the backend dependencies:

```sh
cd agent
poetry install
```

Create a `.env` file inside `./agent` with the following:

```
OPENAI_API_KEY=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
PINN_API_ENDPOINT=https://your-api-gateway-url.amazonaws.com/prod
```

⚠️ IMPORTANT:
Make sure the OpenAI API Key supports GPT-4o and your AWS credentials have access to the PINN platform.

Then, run the agent:

```sh
poetry run demo
```

### UI Setup

First, install the UI dependencies:

```sh
cd ./ui
pnpm i
```

Create a `.env` file inside `./ui` with the following:

```
OPENAI_API_KEY=...
NEXT_PUBLIC_COPILOT_CLOUD_API_KEY=...
```

Then, run the Next.js project:

```sh
pnpm run dev
```

## Usage

Navigate to [http://localhost:3000](http://localhost:3000).

### Example Conversations

**Heat Transfer Problem:**
```
User: "I need to solve a 2D heat conduction problem in a square domain. The left wall is at 100°C, right wall at 0°C, and top/bottom walls are insulated."

Agent: "I'll help you solve this heat transfer problem using Physics-Informed Neural Networks. Let me set up the problem parameters..."
```

**Fluid Dynamics Problem:**
```
User: "Can you solve lid-driven cavity flow with Reynolds number 100?"

Agent: "I'll configure a PINN to solve the Navier-Stokes equations for your lid-driven cavity problem..."
```

**Structural Mechanics:**
```
User: "I have a cantilever beam with a point load. Can you analyze the stress distribution?"

Agent: "I'll set up a structural mechanics PINN to solve the elasticity equations for your cantilever beam..."
```

## Physics Domains Supported

1. **Heat Transfer**
   - Steady-state and transient heat conduction
   - Convection and radiation boundary conditions
   - Multi-material domains

2. **Fluid Dynamics**
   - Incompressible Navier-Stokes equations
   - Various boundary conditions (no-slip, inlet, outlet)
   - Laminar and turbulent flows

3. **Structural Mechanics**
   - Linear and nonlinear elasticity
   - Static and dynamic analysis
   - Various loading conditions

4. **Electromagnetics**
   - Maxwell's equations
   - Electrostatic and magnetostatic problems
   - Wave propagation

## Agent Capabilities

The PINN agents can:

- **Problem Analysis**: Understand physics problems from natural language descriptions
- **Architecture Selection**: Choose optimal PINN architectures based on problem complexity
- **Training Management**: Monitor and manage training processes
- **Result Visualization**: Generate plots and visualizations of solutions
- **Performance Optimization**: Suggest improvements for better accuracy or speed

## Troubleshooting

### Common Issues

1. **Agent Connection Issues**:
   - Ensure the PINN API endpoint is correctly deployed
   - Check AWS credentials and permissions
   - Verify network connectivity

2. **Training Failures**:
   - Check CloudWatch logs for detailed error messages
   - Verify problem parameters are physically meaningful
   - Ensure sufficient computational resources

3. **UI Issues**:
   - Make sure the agent backend is running on port 8000
   - Check browser console for JavaScript errors
   - Verify CopilotKit API keys

### Performance Tips

1. **For Complex Problems**:
   - Use higher accuracy requirements for better results
   - Allow longer training times
   - Consider using GPU instances

2. **For Real-time Applications**:
   - Pre-train models for common problem types
   - Use model caching for repeated inference
   - Optimize network architectures

## Development

### Adding New Physics Domains

1. Create a new agent in `agent/pinn_solver/agents/`
2. Implement domain-specific PDE setup
3. Add boundary condition handlers
4. Update the main agent router

### Customizing PINN Architectures

1. Modify `agent/pinn_solver/core/architecture_selector.py`
2. Add new network types in the training service
3. Update complexity estimation algorithms

### Extending UI Features

1. Add new visualization components
2. Implement custom chat interfaces
3. Create domain-specific input forms

## Deployment

### Local Development
```sh
# Start agent
cd agent && poetry run demo

# Start UI
cd ui && pnpm run dev
```

### Production Deployment
```sh
# Deploy serverless backend
serverless deploy --stage prod

# Deploy agent to cloud
docker build -t pinn-agent .
docker push your-registry/pinn-agent

# Deploy UI
vercel deploy
```

## Support

For issues and questions:
- Check the troubleshooting section
- Review CloudWatch logs for backend issues
- Consult the PINN platform documentation
- Open an issue on GitHub