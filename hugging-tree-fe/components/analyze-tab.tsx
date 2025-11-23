'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import '@/src/lib/api-client' // Ensure API client is configured
import { apiAnalyzeAnalyzePost } from '@/src/lib/api'
import { toast } from 'sonner'
import { Loader2, Brain, Copy } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface AnalyzeTabProps {
  projectPath: string
}

interface GraphContextItem {
  name: string;
  file: string;
}

interface SemanticMatch {
  vector_result: {
    score: number;
    metadata: {
      name: string;
      type: string;
      file_path: string;
      start_line: number;
    };
  };
  graph_context: {
    callers?: GraphContextItem[];
    callees?: GraphContextItem[];
    dependents?: string[];
    dependencies?: string[];
  };
}

interface AnalysisResult {
  model_name?: string;
  analysis_result: {
    task: string;
    semantic_matches_count: number;
    semantic_matches: SemanticMatch[];
    related_files: string[];
    analysis: string;
    structured: {
      files_to_modify?: string[];
      actions?: string[];
      blast_radius?: string[];
      dependencies?: string[];
      risks?: string[];
    };
  };
}

export function AnalyzeTab({ projectPath }: AnalyzeTabProps) {
  const [task, setTask] = useState('')
  const [n, setN] = useState(10)
  const [model, setModel] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

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
        setResult(response.data as unknown as AnalysisResult)
      }
      } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to analyze'
      toast.error('Error', {
        description: errorMessage,
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
                          <li key={idx} className="text-sm">
                            <ReactMarkdown components={{ p: ({ children }) => <span>{children}</span> }}>
                              {file}
                            </ReactMarkdown>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {result.analysis_result.structured.actions && (
                    <div>
                      <h4 className="font-semibold mb-2">Step-by-Step Actions</h4>
                      <ol className="list-decimal list-inside space-y-1">
                        {result.analysis_result.structured.actions.map((action: string, idx: number) => (
                          <li key={idx} className="text-sm">
                            <ReactMarkdown components={{ p: ({ children }) => <span>{children}</span> }}>
                              {action}
                            </ReactMarkdown>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                </>
              )}
              {result.analysis_result?.analysis && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold">Full Analysis</h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(result.analysis_result.analysis)}
                    >
                      <Copy className="h-4 w-4 mr-2" />
                      Copy
                    </Button>
                  </div>
                  <div className="bg-muted p-4 rounded-md overflow-auto text-sm max-h-96 prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {result.analysis_result.analysis}
                    </ReactMarkdown>
                  </div>
                </div>
              )}

              {result.analysis_result?.semantic_matches && (
                <div className="mt-6 pt-6 border-t">
                  <h4 className="font-semibold mb-4">Graph Context</h4>
                  <div className="grid gap-4 md:grid-cols-2">
                    {result.analysis_result.semantic_matches.map((match: SemanticMatch, idx: number) => (
                      <Card key={idx} className="bg-muted/50">
                        <CardHeader className="py-3">
                          <CardTitle className="text-sm font-medium flex justify-between items-center">
                            <span className="truncate mr-2">{match.vector_result.metadata.name}</span>
                            <span className="text-xs text-muted-foreground bg-background px-2 py-1 rounded border">
                              {match.vector_result.score.toFixed(2)}
                            </span>
                          </CardTitle>
                          <CardDescription className="text-xs truncate font-mono">
                            {match.vector_result.metadata.file_path}:{match.vector_result.metadata.start_line}
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="py-3 text-xs space-y-3">
                          {match.graph_context?.callers && match.graph_context.callers.length > 0 && (
                            <div>
                              <span className="font-semibold block mb-1">Called by:</span>
                              <ul className="list-disc list-inside pl-1 text-muted-foreground space-y-0.5">
                                {match.graph_context.callers.slice(0, 3).map((c: GraphContextItem, i: number) => (
                                  <li key={i} className="truncate">{c.name}</li>
                                ))}
                                {match.graph_context.callers.length > 3 && (
                                  <li className="list-none text-[10px] pt-1">+{match.graph_context.callers.length - 3} more</li>
                                )}
                              </ul>
                            </div>
                          )}
                          {match.graph_context?.callees && match.graph_context.callees.length > 0 && (
                            <div>
                              <span className="font-semibold block mb-1">Calls:</span>
                              <ul className="list-disc list-inside pl-1 text-muted-foreground space-y-0.5">
                                {match.graph_context.callees.slice(0, 3).map((c: GraphContextItem, i: number) => (
                                  <li key={i} className="truncate">{c.name}</li>
                                ))}
                                {match.graph_context.callees.length > 3 && (
                                  <li className="list-none text-[10px] pt-1">+{match.graph_context.callees.length - 3} more</li>
                                )}
                              </ul>
                            </div>
                          )}
                          {match.graph_context?.dependents && match.graph_context.dependents.length > 0 && (
                            <div>
                              <span className="font-semibold block mb-1">Used by:</span>
                              <ul className="list-disc list-inside pl-1 text-muted-foreground space-y-0.5">
                                {match.graph_context.dependents.slice(0, 3).map((d: string, i: number) => (
                                  <li key={i} className="truncate">{d.split('/').pop()}</li>
                                ))}
                                {match.graph_context.dependents.length > 3 && (
                                  <li className="list-none text-[10px] pt-1">+{match.graph_context.dependents.length - 3} more</li>
                                )}
                              </ul>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  )
}

