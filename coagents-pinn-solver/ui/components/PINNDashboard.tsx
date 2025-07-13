'use client'

import { useState, useEffect } from 'react'
import { Clock, CheckCircle, XCircle, AlertCircle, BarChart3, Eye } from 'lucide-react'
import { motion } from 'framer-motion'

interface Workflow {
  id: string
  name: string
  domain: string
  status: 'pending' | 'training' | 'completed' | 'failed'
  progress: number
  createdAt: string
  estimatedTime?: number
  accuracy?: number
}

interface PINNDashboardProps {
  activeWorkflow: string | null
  onWorkflowSelect: (id: string) => void
}

// Mock data - in real app, this would come from the PINN backend
const mockWorkflows: Workflow[] = [
  {
    id: 'wf-001',
    name: '2D Heat Conduction',
    domain: 'Heat Transfer',
    status: 'completed',
    progress: 100,
    createdAt: '2024-01-15T10:30:00Z',
    accuracy: 0.97,
  },
  {
    id: 'wf-002',
    name: 'Lid-Driven Cavity Flow',
    domain: 'Fluid Dynamics',
    status: 'training',
    progress: 65,
    createdAt: '2024-01-15T11:15:00Z',
    estimatedTime: 1200,
  },
  {
    id: 'wf-003',
    name: 'Cantilever Beam Analysis',
    domain: 'Structural Mechanics',
    status: 'pending',
    progress: 0,
    createdAt: '2024-01-15T11:45:00Z',
    estimatedTime: 1800,
  },
]

export function PINNDashboard({ activeWorkflow, onWorkflowSelect }: PINNDashboardProps) {
  const [workflows, setWorkflows] = useState<Workflow[]>(mockWorkflows)

  const getStatusIcon = (status: Workflow['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />
      case 'training':
        return <AlertCircle className="h-5 w-5 text-blue-500" />
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />
    }
  }

  const getStatusText = (status: Workflow['status']) => {
    switch (status) {
      case 'pending':
        return 'Pending'
      case 'training':
        return 'Training'
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
    }
  }

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}h ${minutes}m`
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`
    } else {
      return `${secs}s`
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          PINN Workflows
        </h2>
        <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-300">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>Completed: {workflows.filter(w => w.status === 'completed').length}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>Training: {workflows.filter(w => w.status === 'training').length}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span>Pending: {workflows.filter(w => w.status === 'pending').length}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {workflows.map((workflow) => (
          <motion.div
            key={workflow.id}
            className={`physics-card cursor-pointer ${
              activeWorkflow === workflow.id ? 'ring-2 ring-blue-500' : ''
            }`}
            onClick={() => onWorkflowSelect(workflow.id)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  {workflow.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  {workflow.domain}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(workflow.status)}
                <span className={`status-indicator status-${workflow.status}`}>
                  {getStatusText(workflow.status)}
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            {workflow.status === 'training' && (
              <div className="mb-4">
                <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-300 mb-2">
                  <span>Training Progress</span>
                  <span>{workflow.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${workflow.progress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Metrics */}
            <div className="space-y-2 mb-4">
              {workflow.accuracy && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-300">Accuracy</span>
                  <span className="font-medium text-green-600 dark:text-green-400">
                    {(workflow.accuracy * 100).toFixed(1)}%
                  </span>
                </div>
              )}
              
              {workflow.estimatedTime && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-300">Est. Time</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {formatTime(workflow.estimatedTime)}
                  </span>
                </div>
              )}
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-300">Created</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {formatDate(workflow.createdAt)}
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-2 pt-4 border-t border-gray-200 dark:border-gray-700">
              {workflow.status === 'completed' && (
                <>
                  <button className="flex items-center space-x-1 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium transition-colors">
                    <Eye className="h-4 w-4" />
                    <span>View Results</span>
                  </button>
                  <button className="flex items-center space-x-1 text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 text-sm font-medium transition-colors">
                    <BarChart3 className="h-4 w-4" />
                    <span>Visualize</span>
                  </button>
                </>
              )}
              
              {workflow.status === 'training' && (
                <button className="flex items-center space-x-1 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium transition-colors">
                  <BarChart3 className="h-4 w-4" />
                  <span>Monitor</span>
                </button>
              )}
              
              {workflow.status === 'failed' && (
                <button className="flex items-center space-x-1 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 text-sm font-medium transition-colors">
                  <AlertCircle className="h-4 w-4" />
                  <span>View Error</span>
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {workflows.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 dark:text-gray-600 mb-4">
            <BarChart3 className="h-16 w-16 mx-auto" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No workflows yet
          </h3>
          <p className="text-gray-600 dark:text-gray-300">
            Start a conversation with the AI assistant to create your first PINN workflow
          </p>
        </div>
      )}
    </div>
  )
}