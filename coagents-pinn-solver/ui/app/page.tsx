'use client'

import { CopilotKit } from "@copilotkit/react-core"
import { CopilotSidebar } from "@copilotkit/react-ui"
import { useState } from "react"
import { PINNDashboard } from "@/components/PINNDashboard"
import { PhysicsExamples } from "@/components/PhysicsExamples"
import { Header } from "@/components/Header"

export default function Home() {
  const [activeWorkflow, setActiveWorkflow] = useState<string | null>(null)

  return (
    <CopilotKit 
      runtimeUrl="/api/copilotkit"
      agent="pinn_solver_agent"
    >
      <div className="flex h-screen">
        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          <Header />
          
          <main className="flex-1 overflow-auto p-6">
            <div className="max-w-7xl mx-auto space-y-8">
              {/* Hero Section */}
              <div className="text-center space-y-4">
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
                  Physics-Informed Neural Networks
                </h1>
                <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
                  Solve complex physics problems using deep learning. Chat with our AI to set up and solve 
                  heat transfer, fluid dynamics, structural mechanics, and electromagnetics problems.
                </p>
              </div>

              {/* Physics Examples */}
              <PhysicsExamples />

              {/* Dashboard */}
              <PINNDashboard 
                activeWorkflow={activeWorkflow}
                onWorkflowSelect={setActiveWorkflow}
              />
            </div>
          </main>
        </div>

        {/* CopilotKit Sidebar */}
        <CopilotSidebar
          instructions="You are a PINN (Physics-Informed Neural Network) specialist. Help users solve physics problems by:
          1. Understanding their problem description
          2. Setting up the appropriate PINN configuration
          3. Monitoring training progress
          4. Visualizing and explaining results
          
          Be conversational, explain physics concepts clearly, and guide users through the process step by step."
          labels={{
            title: "PINN Solver Assistant",
            initial: "Hi! I'm your PINN specialist. Describe a physics problem you'd like to solve, and I'll help you set up and train a Physics-Informed Neural Network to solve it.",
          }}
          defaultOpen={true}
          clickOutsideToClose={false}
        />
      </div>
    </CopilotKit>
  )
}