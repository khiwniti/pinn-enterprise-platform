'use client'

import { useState } from 'react'
import { Thermometer, Waves, Building, Zap, ChevronRight, Play } from 'lucide-react'
import { motion } from 'framer-motion'

const physicsExamples = [
  {
    id: 'heat-transfer',
    title: 'Heat Transfer',
    description: 'Solve steady-state and transient heat conduction problems',
    icon: Thermometer,
    color: 'bg-red-500',
    examples: [
      {
        name: '2D Heat Conduction',
        description: 'Square domain with Dirichlet and Neumann boundary conditions',
        prompt: 'I need to solve a 2D heat conduction problem in a square domain. The left wall is at 100°C, right wall at 0°C, and top/bottom walls are insulated.',
      },
      {
        name: 'Transient Heat Transfer',
        description: 'Time-dependent heat diffusion with initial conditions',
        prompt: 'Solve a transient heat transfer problem in a rod. Initial temperature is 20°C, left end heated to 100°C at t=0.',
      },
      {
        name: 'Heat Exchanger',
        description: 'Multi-domain heat transfer with convection',
        prompt: 'Model heat transfer in a parallel plate heat exchanger with hot fluid at 80°C and cold fluid at 20°C.',
      },
    ],
  },
  {
    id: 'fluid-dynamics',
    title: 'Fluid Dynamics',
    description: 'Solve incompressible Navier-Stokes equations',
    icon: Waves,
    color: 'bg-blue-500',
    examples: [
      {
        name: 'Lid-Driven Cavity',
        description: 'Classic CFD benchmark problem',
        prompt: 'Solve lid-driven cavity flow with Reynolds number 100. The top wall moves with velocity 1 m/s, other walls are stationary.',
      },
      {
        name: 'Flow Around Cylinder',
        description: 'External flow with wake formation',
        prompt: 'Analyze flow around a circular cylinder at Re=40. Inlet velocity is 1 m/s, cylinder diameter is 0.1 m.',
      },
      {
        name: 'Poiseuille Flow',
        description: 'Fully developed pipe flow',
        prompt: 'Solve Poiseuille flow in a 2D channel. Parabolic velocity profile with no-slip walls.',
      },
    ],
  },
  {
    id: 'structural',
    title: 'Structural Mechanics',
    description: 'Analyze stress and deformation in solid structures',
    icon: Building,
    color: 'bg-green-500',
    examples: [
      {
        name: 'Cantilever Beam',
        description: 'Beam with fixed support and point load',
        prompt: 'Analyze a cantilever beam with length 1m, fixed at left end, point load 1000N at free end. Material: steel.',
      },
      {
        name: 'Plate with Hole',
        description: 'Stress concentration around circular hole',
        prompt: 'Calculate stress distribution in a plate with circular hole under tension. Applied stress 100 MPa.',
      },
      {
        name: 'Vibration Analysis',
        description: 'Modal analysis of structures',
        prompt: 'Find natural frequencies and mode shapes of a simply supported beam. Length 2m, steel material.',
      },
    ],
  },
  {
    id: 'electromagnetics',
    title: 'Electromagnetics',
    description: 'Solve Maxwell equations and electromagnetic fields',
    icon: Zap,
    color: 'bg-purple-500',
    examples: [
      {
        name: 'Electrostatic Field',
        description: 'Electric field between charged plates',
        prompt: 'Calculate electrostatic field between parallel plates. Top plate at +100V, bottom at 0V, separation 1cm.',
      },
      {
        name: 'Magnetic Field',
        description: 'Magnetic field around current-carrying conductor',
        prompt: 'Find magnetic field around a straight wire carrying 10A current. Calculate field at various distances.',
      },
      {
        name: 'Wave Propagation',
        description: 'Electromagnetic wave in waveguide',
        prompt: 'Analyze TE10 mode propagation in rectangular waveguide. Frequency 10 GHz, dimensions 2.3cm x 1.0cm.',
      },
    ],
  },
]

interface PhysicsExamplesProps {
  onExampleSelect?: (prompt: string) => void
}

export function PhysicsExamples({ onExampleSelect }: PhysicsExamplesProps) {
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null)

  return (
    <div className="space-y-6" id="examples">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Physics Domains
        </h2>
        <p className="text-gray-600 dark:text-gray-300">
          Choose a physics domain to explore example problems
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {physicsExamples.map((domain) => {
          const Icon = domain.icon
          const isSelected = selectedDomain === domain.id
          
          return (
            <motion.div
              key={domain.id}
              className={`physics-card cursor-pointer ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
              onClick={() => setSelectedDomain(isSelected ? null : domain.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="flex items-center space-x-3 mb-4">
                <div className={`p-2 rounded-lg ${domain.color} text-white`}>
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {domain.title}
                </h3>
              </div>
              
              <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
                {domain.description}
              </p>
              
              <div className="flex items-center text-blue-600 dark:text-blue-400 text-sm font-medium">
                <span>View Examples</span>
                <ChevronRight className={`h-4 w-4 ml-1 transition-transform ${isSelected ? 'rotate-90' : ''}`} />
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Selected Domain Examples */}
      {selectedDomain && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-8"
        >
          {physicsExamples
            .filter(domain => domain.id === selectedDomain)
            .map(domain => (
              <div key={domain.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  {domain.title} Examples
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {domain.examples.map((example, index) => (
                    <div
                      key={index}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                        {example.name}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                        {example.description}
                      </p>
                      <button
                        onClick={() => onExampleSelect?.(example.prompt)}
                        className="flex items-center space-x-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium transition-colors"
                      >
                        <Play className="h-4 w-4" />
                        <span>Try This Example</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
        </motion.div>
      )}
    </div>
  )
}