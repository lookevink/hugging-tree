'use client'

import { useState } from 'react'
import { Toaster } from '@/components/ui/sonner'
import { ProjectsView } from '@/components/projects-view'
import { ProjectDetailView } from '@/components/project-detail-view'

export default function Home() {
  const [selectedProject, setSelectedProject] = useState<string | null>(null)

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            🌳 Hugging Tree
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Semantic Knowledge Graph for your codebase
          </p>
        </div>

        {selectedProject ? (
          <ProjectDetailView 
            projectPath={selectedProject} 
            onBack={() => setSelectedProject(null)} 
          />
        ) : (
          <ProjectsView onSelectProject={setSelectedProject} />
        )}
      </div>
      <Toaster />
    </main>
  )
}
