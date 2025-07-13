"""LangGraph agent for PINN problem solving"""

from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
import json

from pinn_solver.tools.pinn_tools import PINN_TOOLS

class PINNAgentState(BaseModel):
    """State for the PINN agent"""
    messages: List[Any] = []
    current_workflow_id: Optional[str] = None
    problem_type: Optional[str] = None
    workflow_status: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

# Initialize the LLM
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.1,
    streaming=True
)

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(PINN_TOOLS)

# System prompt for the PINN agent
SYSTEM_PROMPT = """You are a Physics-Informed Neural Network (PINN) specialist agent. You help users solve complex physics problems using deep learning techniques.

Your capabilities include:
1. **Problem Analysis**: Understanding physics problems from natural language descriptions
2. **PINN Configuration**: Setting up optimal neural network architectures for different physics domains
3. **Training Management**: Monitoring and managing the training process
4. **Results Interpretation**: Analyzing and explaining simulation results
5. **Visualization**: Creating plots and visualizations of solutions

**Supported Physics Domains:**
- Heat Transfer (steady-state and transient heat conduction)
- Fluid Dynamics (Navier-Stokes equations, incompressible flow)
- Structural Mechanics (elasticity, stress analysis)
- Electromagnetics (Maxwell's equations)

**Workflow:**
1. When a user describes a physics problem, analyze it and determine the domain type
2. Use the solve_pinn_problem tool to submit the problem for training
3. Monitor progress using check_workflow_status
4. Once complete, retrieve and visualize results
5. Provide clear explanations of the solution and its physical meaning

**Communication Style:**
- Be conversational and helpful
- Explain physics concepts clearly
- Provide step-by-step guidance
- Offer suggestions for problem setup and optimization
- Always explain what you're doing and why

**Important Notes:**
- PINN training can take time (minutes to hours depending on complexity)
- Always check workflow status before attempting to get results
- Provide realistic expectations about training time and accuracy
- Suggest visualization options to help users understand results
"""

def should_continue(state: PINNAgentState) -> str:
    """Determine if the agent should continue or end"""
    messages = state.messages
    last_message = messages[-1]
    
    # If the last message has tool calls, continue to tool execution
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # Otherwise, end the conversation
    return END

def call_model(state: PINNAgentState) -> Dict[str, Any]:
    """Call the LLM with the current state"""
    
    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    # Format the prompt with current state
    formatted_prompt = prompt.format_messages(messages=state.messages)
    
    # Call the LLM
    response = llm_with_tools.invoke(formatted_prompt)
    
    # Update state
    return {
        "messages": state.messages + [response]
    }

def handle_tool_response(state: PINNAgentState) -> Dict[str, Any]:
    """Handle responses from tool execution"""
    
    messages = state.messages
    last_message = messages[-1]
    
    # Extract workflow information from tool responses
    current_workflow_id = state.current_workflow_id
    problem_type = state.problem_type
    workflow_status = state.workflow_status
    results = state.results
    
    # Parse tool responses for state updates
    if hasattr(last_message, 'content'):
        try:
            content = json.loads(last_message.content)
            
            # Update workflow ID if present
            if 'workflow_id' in content:
                current_workflow_id = content['workflow_id']
            
            # Update status if present
            if 'status' in content:
                workflow_status = content['status']
            
            # Update results if present
            if 'results' in content:
                results = content['results']
                
        except (json.JSONDecodeError, AttributeError):
            pass
    
    return {
        "current_workflow_id": current_workflow_id,
        "problem_type": problem_type,
        "workflow_status": workflow_status,
        "results": results
    }

# Create the tool node
tool_node = ToolNode(PINN_TOOLS)

# Build the graph
workflow = StateGraph(PINNAgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("handle_tool_response", handle_tool_response)

# Add edges
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)
workflow.add_edge("tools", "handle_tool_response")
workflow.add_edge("handle_tool_response", "agent")

# Compile the graph
graph = workflow.compile()

# Example usage and testing
if __name__ == "__main__":
    # Test the agent
    initial_state = PINNAgentState(
        messages=[
            HumanMessage(content="I need to solve a 2D heat conduction problem. The left wall is at 100°C, right wall at 0°C, and top/bottom walls are insulated.")
        ]
    )
    
    print("Testing PINN Agent...")
    
    # Run the agent
    for step in graph.stream(initial_state):
        print(f"Step: {step}")
        
    print("Agent test completed!")