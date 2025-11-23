'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { apiAnalyzeAnalyzePost } from '@/src/lib/api'
import { toast } from 'sonner'
import { Loader2, Brain } from 'lucide-react'

interface AnalyzeTabProps {
  projectPath: string
}

export function AnalyzeTab({ projectPath }: AnalyzeTabProps) {
  const [task, setTask] = useState('')
  const [n, setN] = useState(10)
  const [model, setModel] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleAnalyze = async () => {
    if (!task.trim()) {
      toast.error('Error', {
        description: 'Please enter a task description',
      })
      return
    }

    try {
      setLoading(true)
      setResult(null)
      const response = await apiAnalyzeAnalyzePost({
        body: {
          task,
          path: projectPath,
          n,
          model: model || undefined,
        },
      })
      
      if (response.data) {
        setResult(response.data)
      }
    } catch (error: any) {
      toast.error('Error', {
        description: error.message || 'Failed to analyze',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Analyze Task
        </CardTitle>
        <CardDescription>
          Analyze a query/task and generate actionable context including files to modify, blast radius, and step-by-step actions
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="analyze-task">Task Description</Label>
          <Textarea
            id="analyze-task"
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="add user authentication"
            rows={4}
            disabled={loading}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="analyze-n">Number of Results</Label>
            <Input
              id="analyze-n"
              type="number"
              value={n}
              onChange={(e) => setN(parseInt(e.target.value) || 10)}
              min={1}
              max={50}
              disabled={loading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="analyze-model">Model (optional)</Label>
            <Input
              id="analyze-model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="gemini-3-pro-preview"
              disabled={loading}
            />
          </div>
        </div>
        <Button onClick={handleAnalyze} disabled={loading || !task.trim()}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Analyze
        </Button>

        {result && (
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Analysis Results</CardTitle>
              {result.model_name && (
                <CardDescription>Model: {result.model_name}</CardDescription>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {result.analysis_result?.structured && (
                <>
                  {result.analysis_result.structured.files_to_modify && (
                    <div>
                      <h4 className="font-semibold mb-2">Files to Modify</h4>
                      <ul className="list-disc list-inside space-y-1">
                        {result.analysis_result.structured.files_to_modify.map((file: string, idx: number) => (
                          <li key={idx} className="text-sm">{file}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {result.analysis_result.structured.actions && (
                    <div>
                      <h4 className="font-semibold mb-2">Step-by-Step Actions</h4>
                      <ol className="list-decimal list-inside space-y-1">
                        {result.analysis_result.structured.actions.map((action: string, idx: number) => (
                          <li key={idx} className="text-sm">{action}</li>
                        ))}
                      </ol>
                    </div>
                  )}
                </>
              )}
              {result.analysis_result?.analysis && (
                <div>
                  <h4 className="font-semibold mb-2">Full Analysis</h4>
                  <pre className="bg-muted p-4 rounded-md overflow-auto text-sm whitespace-pre-wrap max-h-96">
                    {result.analysis_result.analysis}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  )
}

