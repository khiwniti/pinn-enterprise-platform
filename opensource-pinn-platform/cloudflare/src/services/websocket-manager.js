/**
 * WebSocket Manager using Cloudflare Durable Objects
 * Handles real-time communication for simulation updates
 */

export class WebSocketManager {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.sessions = new Map();
  }

  async fetch(request) {
    const url = new URL(request.url);
    
    if (url.pathname === '/websocket') {
      if (request.headers.get('Upgrade') !== 'websocket') {
        return new Response('Expected websocket', { status: 400 });
      }
      
      const workflowId = request.headers.get('Workflow-ID');
      const webSocketPair = new WebSocketPair();
      const [client, server] = Object.values(webSocketPair);
      
      await this.handleSession(server, workflowId);
      
      return new Response(null, {
        status: 101,
        webSocket: client
      });
    }
    
    return new Response('Not found', { status: 404 });
  }

  async handleSession(webSocket, workflowId) {
    webSocket.accept();
    
    const sessionId = this.generateSessionId();
    
    // Store session
    this.sessions.set(sessionId, {
      webSocket,
      workflowId,
      connectedAt: new Date().toISOString(),
      lastActivity: new Date().toISOString()
    });
    
    // Send connection confirmation
    await this.sendMessage(webSocket, {
      type: 'connection_established',
      sessionId,
      workflowId,
      timestamp: new Date().toISOString()
    });
    
    // Set up event handlers
    webSocket.addEventListener('message', async (event) => {
      await this.handleMessage(sessionId, JSON.parse(event.data));
    });
    
    webSocket.addEventListener('close', () => {
      this.sessions.delete(sessionId);
    });
    
    webSocket.addEventListener('error', (error) => {
      console.error('WebSocket error:', error);
      this.sessions.delete(sessionId);
    });
    
    // Start sending periodic updates
    this.startPeriodicUpdates(sessionId, workflowId);
  }

  async handleMessage(sessionId, message) {
    const session = this.sessions.get(sessionId);
    if (!session) return;
    
    // Update last activity
    session.lastActivity = new Date().toISOString();
    
    // Handle different message types
    switch (message.type) {
      case 'ping':
        await this.sendMessage(session.webSocket, {
          type: 'pong',
          timestamp: new Date().toISOString()
        });
        break;
        
      case 'subscribe_metrics':
        // Subscribe to specific metrics updates
        session.subscriptions = message.metrics || [];
        break;
        
      case 'request_status':
        // Send current workflow status
        await this.sendWorkflowStatus(session.webSocket, session.workflowId);
        break;
    }
  }

  async sendMessage(webSocket, message) {
    try {
      webSocket.send(JSON.stringify({
        ...message,
        timestamp: new Date().toISOString()
      }));
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
    }
  }

  async sendWorkflowStatus(webSocket, workflowId) {
    try {
      // In a real implementation, you'd fetch from KV storage
      // For now, send a mock status
      await this.sendMessage(webSocket, {
        type: 'workflow_status',
        workflowId,
        payload: {
          status: 'processing',
          progress: Math.random() * 100,
          currentStep: 'pinn_training',
          metrics: {
            accuracy: 0.85 + Math.random() * 0.1,
            loss: 0.01 * Math.random(),
            epoch: Math.floor(Math.random() * 5000)
          }
        }
      });
    } catch (error) {
      console.error('Failed to send workflow status:', error);
    }
  }

  startPeriodicUpdates(sessionId, workflowId) {
    const interval = setInterval(async () => {
      const session = this.sessions.get(sessionId);
      if (!session) {
        clearInterval(interval);
        return;
      }
      
      // Send periodic updates
      await this.sendMessage(session.webSocket, {
        type: 'workflow_progress',
        workflowId,
        payload: {
          progress: Math.min(100, Math.random() * 100),
          step: this.getRandomStep(),
          metrics: this.generateRandomMetrics(),
          timestamp: new Date().toISOString()
        }
      });
      
    }, 5000); // Send updates every 5 seconds
  }

  getRandomStep() {
    const steps = [
      'problem_analysis',
      'mesh_generation', 
      'pinn_training',
      'model_validation',
      'results_generation'
    ];
    return steps[Math.floor(Math.random() * steps.length)];
  }

  generateRandomMetrics() {
    return {
      accuracy: 0.8 + Math.random() * 0.19,
      loss: Math.random() * 0.1,
      convergence: Math.random(),
      training_time: Math.floor(Math.random() * 300),
      epoch: Math.floor(Math.random() * 10000)
    };
  }

  generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9);
  }

  // Broadcast to all sessions for a workflow
  async broadcastToWorkflow(workflowId, message) {
    const promises = [];
    
    for (const [sessionId, session] of this.sessions) {
      if (session.workflowId === workflowId) {
        promises.push(this.sendMessage(session.webSocket, message));
      }
    }
    
    await Promise.all(promises);
  }

  // Get connection statistics
  getStats() {
    return {
      totalSessions: this.sessions.size,
      sessionsByWorkflow: this.getSessionsByWorkflow(),
      oldestConnection: this.getOldestConnection()
    };
  }

  getSessionsByWorkflow() {
    const workflowCounts = {};
    
    for (const session of this.sessions.values()) {
      const workflowId = session.workflowId;
      workflowCounts[workflowId] = (workflowCounts[workflowId] || 0) + 1;
    }
    
    return workflowCounts;
  }

  getOldestConnection() {
    let oldest = null;
    
    for (const session of this.sessions.values()) {
      if (!oldest || session.connectedAt < oldest) {
        oldest = session.connectedAt;
      }
    }
    
    return oldest;
  }
}