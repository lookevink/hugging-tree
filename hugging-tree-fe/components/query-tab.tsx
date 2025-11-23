'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { apiQueryQueryPost } from '@/src/lib/api'
import { toast } from 'sonner'
import { Loader2, Search } from 'lucide-react'

interface QueryTabProps {
  projectPath: string
}

export function QueryTab({ projectPath }: QueryTabProps) {
  const [text, setText] = useState('')
  const [n, setN] = useState(5)
  const [withGraph, setWithGraph] = useState(true)
  const [xml, setXml] = useState(false)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)

  const handleQuery = async () => {
    if (!text.trim()) {
      toast.error('Error', {
        description: 'Please enter a query',
      })
      return
    }

    try {
      setLoading(true)
      setResults(null)
      const response = await apiQueryQueryPost({
        body: {
          text,
          path: projectPath,
          n,
          with_graph: withGraph,
          xml,
        },
      })
      
      if (response.data) {
        setResults(response.data)
      }
    } catch (error: any) {
      toast.error('Error', {
        description: error.message || 'Failed to query',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Semantic Search
          </CardTitle>
          <CardDescription>
            Search the codebase using semantic search, optionally enhanced with graph traversal
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="query-text">Query</Label>
            <Textarea
              id="query-text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="find authentication logic"
              rows={3}
              disabled={loading}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="query-n">Number of Results</Label>
              <Input
                id="query-n"
                type="number"
                value={n}
                onChange={(e) => setN(parseInt(e.target.value) || 5)}
                min={1}
                max={50}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Options</Label>
              <div className="flex items-center space-x-4 pt-2">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={withGraph}
                    onChange={(e) => setWithGraph(e.target.checked)}
                    disabled={loading}
                    className="cursor-pointer"
                  />
                  <span className="text-sm">With Graph</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={xml}
                    onChange={(e) => setXml(e.target.checked)}
                    disabled={loading}
                    className="cursor-pointer"
                  />
                  <span className="text-sm">XML Output</span>
                </label>
              </div>
            </div>
          </div>
          <Button onClick={handleQuery} disabled={loading || !text.trim()}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Search
          </Button>

          {results && (
            <Card className="mt-4">
              <CardHeader>
                <CardTitle>Results</CardTitle>
              </CardHeader>
              <CardContent>
                {results.xml_packet ? (
                  <pre className="bg-muted p-4 rounded-md overflow-auto text-sm max-h-96">
                    {results.xml_packet}
                  </pre>
                ) : results.expanded_context ? (
                  <div className="space-y-4">
                    <div className="text-sm text-muted-foreground">
                      Found {results.expanded_context.semantic_matches?.length || 0} semantic matches
                    </div>
                    {results.expanded_context.semantic_matches?.map((match: any, idx: number) => (
                      <Card key={idx}>
                        <CardContent className="pt-6">
                          <div className="space-y-2">
                            <div className="font-semibold">
                              {match.vector_result?.metadata?.name} ({match.vector_result?.metadata?.type})
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {match.vector_result?.metadata?.file_path}:{match.vector_result?.metadata?.start_line}
                            </div>
                            <div className="text-sm">Score: {match.vector_result?.score?.toFixed(4)}</div>
                            <pre className="bg-muted p-2 rounded text-xs overflow-auto max-h-32">
                              {match.vector_result?.document?.substring(0, 200)}...
                            </pre>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {results.vector_results?.map((result: any, idx: number) => (
                      <Card key={idx}>
                        <CardContent className="pt-6">
                          <div className="space-y-2">
                            <div className="font-semibold">
                              {result.metadata?.name} ({result.metadata?.type})
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {result.metadata?.file_path}:{result.metadata?.start_line}
                            </div>
                            <div className="text-sm">Score: {result.score?.toFixed(4)}</div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

