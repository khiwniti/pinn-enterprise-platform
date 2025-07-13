'use client'

import { Brain, Zap, Activity } from 'lucide-react'

export function Header() {
  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Brain className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900 dark:text-white">
                PINN Solver
              </span>
            </div>
            <div className="hidden md:flex items-center space-x-1 text-sm text-gray-500 dark:text-gray-400">
              <Zap className="h-4 w-4" />
              <span>Physics-Informed Neural Networks</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-300">
              <Activity className="h-4 w-4 text-green-500" />
              <span>System Online</span>
            </div>
            
            <div className="hidden md:flex items-center space-x-6 text-sm">
              <a 
                href="#examples" 
                className="text-gray-600 hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400 transition-colors"
              >
                Examples
              </a>
              <a 
                href="#docs" 
                className="text-gray-600 hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400 transition-colors"
              >
                Documentation
              </a>
              <a 
                href="#about" 
                className="text-gray-600 hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400 transition-colors"
              >
                About
              </a>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}