'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { apiPlanPlanPost } from '@/src/lib/api'
import { toast } from 'sonner'
import { Loader2, FileText } from 'lucide-react'

interface PlanTabProps {
  projectPath: string
}

export function PlanTab({ projectPath }: PlanTabProps) {
  const [task, setTask] = useState('')
  const [n, setN] = useState(10)
  const [model, setModel] = useState('')
  const [format, setFormat] = useState<'json' | 'xml'>('xml')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

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
          format,
        },
      })
      
      if (response.data) {
        setResult(response.data)
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
        <div className="grid grid-cols-3 gap-4">
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
          <div className="space-y-2">
            <Label htmlFor="plan-format">Format</Label>
            <select
              id="plan-format"
              value={format}
              onChange={(e) => setFormat(e.target.value as 'json' | 'xml')}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              disabled={loading}
            >
              <option value="xml">XML</option>
              <option value="json">JSON</option>
            </select>
          </div>
        </div>
        <Button onClick={handlePlan} disabled={loading || !task.trim()}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Generate Plan
        </Button>

        {result && (
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Generated Plan</CardTitle>
              {result.model_name && (
                <CardDescription>Model: {result.model_name}</CardDescription>
              )}
            </CardHeader>
            <CardContent>
              <pre className="bg-muted p-4 rounded-md overflow-auto text-sm whitespace-pre-wrap max-h-96">
                {result.plan_xml || JSON.stringify(result, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  )
}

