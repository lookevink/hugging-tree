'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import '@/src/lib/api-client' // Ensure API client is configured
import { apiPlanPlanPost } from '@/src/lib/api'
import { toast } from 'sonner'
import { Loader2, FileText, Network, Copy } from 'lucide-react'
import { GraphVisualization } from '@/components/graph-visualization'

interface PlanTabProps {
  projectPath: string
}

interface PlanResult {
  model_name?: string
  plan_xml: string
  related_files: string[]
  semantic_matches: any[]
  semantic_matches_count: number
}

export function PlanTab({ projectPath }: PlanTabProps) {
  const [task, setTask] = useState('')
  const [n, setN] = useState(10)
  const [model, setModel] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PlanResult | null>(null)
  const [showGraph, setShowGraph] = useState(false)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const handlePlan = async () => {
    if (!task.trim()) {
      toast.error('Error', {
        description: 'Please enter a task description',
      })
      return
    }

    try {
      setLoading(true)
      setResult(null)
      const response = await apiPlanPlanPost({
        body: {
          task,
          path: projectPath,
          n,
          model: model || undefined,
          format: 'json', // Always use JSON now - XML is included as a string field
        },
      })
      
      if (response.data) {
        setResult(response.data as unknown as PlanResult)
      }
    } catch (error: any) {
      toast.error('Error', {
        description: error.message || 'Failed to generate plan',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Generate Plan
        </CardTitle>
        <CardDescription>
          Generate an executable, step-by-step plan in XML format for AI coding tools
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="plan-task">Task Description</Label>
          <Textarea
            id="plan-task"
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="implement user authentication"
            rows={4}
            disabled={loading}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="plan-n">Number of Results</Label>
            <Input
              id="plan-n"
              type="number"
              value={n}
              onChange={(e) => setN(parseInt(e.target.value) || 10)}
              min={1}
              max={50}
              disabled={loading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="plan-model">Model (optional)</Label>
            <Input
              id="plan-model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="gemini-3-pro-preview"
              disabled={loading}
            />
          </div>
        </div>
        <Button onClick={handlePlan} disabled={loading || !task.trim()}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Generate Plan
        </Button>

        {result && (
          <div className="mt-4 space-y-4">
            {/* Blast Radius / Related Files Section */}
            {result.related_files && result.related_files.length > 0 && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Blast Radius</CardTitle>
                      <CardDescription>
                        {result.related_files.length} related file{result.related_files.length !== 1 ? 's' : ''} identified
                      </CardDescription>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setShowGraph(!showGraph)
                      }}
                    >
                      <Network className="h-4 w-4 mr-2" />
                      {showGraph ? 'Hide Graph' : 'View Graph'}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    <ul className="list-disc list-inside space-y-1">
                      {result.related_files.map((file: string, idx: number) => (
                        <li key={idx} className="text-sm font-mono">
                          {file}
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* XML Plan Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Generated Plan (XML)</CardTitle>
                    {result.model_name && (
                      <CardDescription>Model: {result.model_name}</CardDescription>
                    )}
                  </div>
                  {result.plan_xml && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(result.plan_xml)}
                    >
                      <Copy className="h-4 w-4 mr-2" />
                      Copy XML
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <pre className="bg-muted p-4 rounded-md overflow-auto text-sm whitespace-pre-wrap max-h-96">
                  {result.plan_xml}
                </pre>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Inline Graph Visualization */}
        {showGraph && result.related_files && result.related_files.length > 0 && (
          <div className="mt-4">
            <GraphVisualization
              projectPath={projectPath}
              filterFiles={result.related_files}
              title="Plan Graph View"
              description={`Showing relationships for ${result.related_files.length} file${result.related_files.length !== 1 ? 's' : ''}`}
              collapsible={true}
              defaultCollapsed={false}
              height="500px"
              maxNodes={200}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

