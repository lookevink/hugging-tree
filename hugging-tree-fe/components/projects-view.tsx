'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import '@/src/lib/api-client' // Ensure API client is configured
import { apiListProjectsProjectsGet } from '@/src/lib/api'
import { toast } from 'sonner'
import { CheckCircle2, Circle, GitBranch, Folder, Loader2 } from 'lucide-react'

// Type definition based on the API response structure
type Project = {
  name: string
  path: string
  is_git_repo: boolean
  is_scanned: boolean
  file_count: number
}

type ProjectsResponse = {
  projects_root: string | null
  projects: Project[]
  total: number
  scanned_count: number
  error?: string
}

export function ProjectsView({ onSelectProject }: { onSelectProject: (path: string) => void }) {
  const [projects, setProjects] = useState<ProjectsResponse['projects']>([])
  const [loading, setLoading] = useState(true)
  const [projectsRoot, setProjectsRoot] = useState<string>('')

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      setLoading(true)
      // Use the default configured client (no need to pass explicitly)
      const response = await apiListProjectsProjectsGet()
      
      if (response.data) {
        const data = response.data as ProjectsResponse
        setProjects(data.projects || [])
        setProjectsRoot(data.projects_root || '')
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load projects'
      toast.error('Error loading projects', {
        description: errorMessage,
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Available Projects</CardTitle>
          <CardDescription>
            {projectsRoot && `Projects root: ${projectsRoot}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">Loading projects...</span>
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No projects found</div>
          ) : (
            <div className="space-y-2">
              {projects.map((project) => (
                <Card
                  key={project.path}
                  className="cursor-pointer transition-all hover:shadow-md hover:border-primary/50"
                  onClick={() => onSelectProject(project.path)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        {project.is_scanned ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
                        ) : (
                          <Circle className="h-5 w-5 text-gray-400 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold truncate">{project.name}</div>
                          <div className="text-sm text-muted-foreground flex items-center gap-2 flex-wrap">
                            {project.is_git_repo ? (
                              <span className="flex items-center gap-1">
                                <GitBranch className="h-3 w-3" />
                                Git repo
                              </span>
                            ) : (
                              <span className="flex items-center gap-1">
                                <Folder className="h-3 w-3" />
                                Directory
                              </span>
                            )}
                            {project.is_scanned && (
                              <>
                                <span>•</span>
                                <span>{project.file_count} files</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="text-sm text-muted-foreground">
                          {project.is_scanned ? (
                            <span className="text-green-600 dark:text-green-400">Scanned</span>
                          ) : (
                            <span>Not scanned</span>
                          )}
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            onSelectProject(project.path)
                          }}
                        >
                          Open
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
          <div className="mt-4">
            <Button onClick={loadProjects} variant="outline" size="sm" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

