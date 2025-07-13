import { CopilotRuntime, OpenAIAdapter } from "@copilotkit/backend"
import { NextRequest } from "next/server"

const runtime = new CopilotRuntime({
  remoteEndpoints: [
    {
      url: process.env.PINN_AGENT_URL || "http://localhost:8000/copilotkit",
    },
  ],
})

export async function POST(req: NextRequest) {
  const { handleRequest } = runtime

  return handleRequest(req)
}