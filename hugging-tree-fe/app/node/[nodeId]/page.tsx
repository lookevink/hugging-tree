'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, ArrowLeft, Code, Network, FileText, Info } from 'lucide-react'
import { toast } from 'sonner'
import '@/src/lib/api-client'
import { getNodeDetailsNodeDetailsPost, deepTraceAnalyzeDeepTraceAnalyzePost, deepTraceApplyDeepTraceApplyPost } from '@/src/lib/api'
import {
  CodeBlock,
  CodeBlockBody,
  CodeBlockContent,
  CodeBlockCopyButton,
  CodeBlockFilename,
  CodeBlockFiles,
  CodeBlockHeader,
  CodeBlockItem,
} from '@/src/components/ui/shadcn-io/code-block'

// Dynamically import InteractiveNvlWrapper to avoid SSR issues
const InteractiveNvlWrapper = dynamic(
  () => {
    return import('@neo4j-nvl/react').then((mod) => {
      if (typeof window !== 'undefined') {
        const originalWorker = window.Worker
        window.Worker = class extends originalWorker {
          constructor(scriptURL: string | URL, options?: WorkerOptions) {
            const urlStr = typeof scriptURL === 'string' ? scriptURL : scriptURL.toString()
            try {
              super(scriptURL, options)
            } catch (error) {
              console.error('Worker creation failed:', error, 'URL:', urlStr)
              super(scriptURL, options)
            }
          }
        } as typeof Worker
      }
      return mod.InteractiveNvlWrapper
    }).catch((error) => {
      console.error('Failed to load InteractiveNvlWrapper:', error)
      throw error
    })
  },
  { 
    ssr: false,
    loading: () => <div className="flex items-center justify-center h-full text-sm text-muted-foreground">Loading graph...</div>
  }
)

interface NodeDetails {
  node: {
    id: string
    label: string
    type: string
    path?: string
    properties?: Record<string, unknown>
  }
  source_code: string | null
  related_nodes: Array<{
    id: string
    label: string
    type: string
    path?: string
    properties?: Record<string, unknown>
  }>
  related_edges: Array<{
    id: string
    source: string
    target: string
    type: string
    label: string
  }>
}

export default function NodeDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const nodeId = decodeURIComponent(params.nodeId as string)
  const [projectPath, setProjectPath] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [details, setDetails] = useState<NodeDetails | null>(null)
  const [activeTab, setActiveTab] = useState<'code' | 'graph' | 'list'>('code')
  const [deepTraceLoading, setDeepTraceLoading] = useState(false)
  const [deepTraceResults, setDeepTraceResults] = useState<any[]>([])
  const [showDeepTraceResults, setShowDeepTraceResults] = useState(false)

  const loadNodeDetails = useCallback(async (projectRoot: string) => {
    try {
      setLoading(true)
      const response = await getNodeDetailsNodeDetailsPost({
        body: {
          node_id: nodeId,
          project_root: projectRoot,
        },
      })

      if (response.data) {
        setDetails(response.data as unknown as NodeDetails)
      }
    } catch (error) {
      toast.error('Error', {
        description: error instanceof Error ? error.message : 'Failed to load node details',
      })
    } finally {
      setLoading(false)
    }
  }, [nodeId])

  useEffect(() => {
    // Get project path from query params or localStorage
    const urlParams = new URLSearchParams(window.location.search)
    const path = urlParams.get('project') || localStorage.getItem('lastProjectPath')
    if (path) {
      setProjectPath(path)
      loadNodeDetails(path)
    } else {
      toast.error('Project path not found')
      router.push('/')
    }
  }, [nodeId, router, loadNodeDetails])

  if (loading || !details) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-96">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </div>
      </div>
    )
  }

  const { node, source_code, related_nodes, related_edges } = details

  // Convert to NVL format for graph visualization
  const convertToNvlFormat = (nodes: typeof related_nodes, edges: typeof related_edges, centerNode: typeof node) => {
    const allNodes = [centerNode, ...nodes]
    const nvlNodes = allNodes.map((n) => ({
      id: n.id,
      captions: [{ value: n.label }],
      labels: [n.type],
      properties: {
        ...n.properties,
        label: n.label,
        path: n.path || '',
        type: n.type,
      },
    }))

    const nvlRels = edges.map((e) => ({
      id: e.id,
      from: e.source,
      to: e.target,
      captions: [{ value: e.label || e.type }],
      type: e.type,
      properties: {
        label: e.label,
        type: e.type,
      },
    }))

    return { nodes: nvlNodes, relationships: nvlRels }
  }

  const nvlData = convertToNvlFormat(related_nodes, related_edges, node)

  // Helper function to detect language from file path
  const detectLanguage = (path: string | undefined): string => {
    if (!path) return 'typescript'
    const ext = path.split('.').pop()?.toLowerCase()
    const languageMap: Record<string, string> = {
      'ts': 'typescript',
      'tsx': 'typescript',
      'js': 'javascript',
      'jsx': 'javascript',
      'py': 'python',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'cs': 'csharp',
      'go': 'go',
      'rs': 'rust',
      'rb': 'ruby',
      'php': 'php',
      'swift': 'swift',
      'kt': 'kotlin',
      'scala': 'scala',
      'sh': 'bash',
      'yaml': 'yaml',
      'yml': 'yaml',
      'json': 'json',
      'xml': 'xml',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'sass': 'sass',
      'less': 'less',
      'md': 'markdown',
      'sql': 'sql',
      'r': 'r',
      'm': 'matlab',
      'pl': 'perl',
      'lua': 'lua',
      'dart': 'dart',
      'vue': 'vue',
      'svelte': 'svelte',
    }
    return languageMap[ext || ''] || 'typescript'
  }

  const codeBlockData = source_code
    ? [
        {
          language: detectLanguage(node.path),
          filename: node.path || 'code',
          code: source_code,
        },
      ]
    : []

  const handleDeepTrace = async () => {
    if (!projectPath) return
    
    try {
      setDeepTraceLoading(true)
      setShowDeepTraceResults(true)
      const response = await deepTraceAnalyzeDeepTraceAnalyzePost({
        body: {
          node_id: nodeId,
          project_root: projectPath
        }
      })
      
      if (response.data && (response.data as any).results) {
        setDeepTraceResults((response.data as any).results)
      } else {
        setDeepTraceResults([])
      }
    } catch (error) {
      toast.error("Deep Trace Failed", {
        description: error instanceof Error ? error.message : "Unknown error"
      })
    } finally {
      setDeepTraceLoading(false)
    }
  }

  const handleApplyDeepTrace = async (result: any, match: any) => {
    if (!projectPath) return
    
    try {
      await deepTraceApplyDeepTraceApplyPost({
        body: {
          source_id: nodeId,
          target_id: match.id,
          rel_type: result.call.type === 'api_call' ? 'CALLS_API' : 'PRODUCES_EVENT'
        }
      })
      
      toast.success("Relationship Applied", {
        description: `Linked to ${match.label}`
      })
      
      // Reload node details to show the new relationship
      loadNodeDetails(projectPath)
    } catch (error) {
      toast.error("Failed to apply relationship")
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Button variant="ghost" size="sm" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        </div>

        {/* Node Header */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Info className="h-5 w-5" />
                  {node.label}
                </CardTitle>
                <CardDescription className="mt-2">
                  <span className="capitalize">{node.type}</span>
                  {node.path && (
                    <>
                      {' • '}
                      <span className="font-mono text-xs">{node.path}</span>
                    </>
                  )}
                </CardDescription>
              </div>
              {node.properties && Object.keys(node.properties).length > 0 && (
                <div className="text-sm text-muted-foreground">
                  {node.properties.start_line != null && node.properties.end_line != null && (
                    <div>
                      Lines: {String(node.properties.start_line)} - {String(node.properties.end_line)}
                    </div>
                  )}
                </div>
              )}
            </div>
          </CardHeader>
        </Card>

        {/* Tabs */}
        <div className="flex gap-2 mb-4">
          <Button
            variant={activeTab === 'code' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('code')}
          >
            <Code className="h-4 w-4 mr-2" />
            Source Code
          </Button>
          <Button
            variant={activeTab === 'graph' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('graph')}
          >
            <Network className="h-4 w-4 mr-2" />
            Graph View ({related_nodes.length})
          </Button>
          <Button
            variant={activeTab === 'list' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('list')}
          >
            <FileText className="h-4 w-4 mr-2" />
            Related Nodes ({related_nodes.length})
          </Button>
        </div>

        {/* Content */}
        {activeTab === 'code' && (
          <Card>
            <CardHeader>
              <CardTitle>Source Code</CardTitle>
              <CardDescription>
                {node.type === 'function' || node.type === 'class'
                  ? `${node.type} definition`
                  : 'File contents'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {source_code ? (
                <div className="max-h-[600px] overflow-auto">
                  <CodeBlock data={codeBlockData} defaultValue={codeBlockData[0]?.filename}>
                    <CodeBlockHeader>
                      <CodeBlockFiles>
                        {(item: { language: string; filename: string; code: string }) => (
                          <CodeBlockFilename value={item.filename}>
                            {item.filename}
                          </CodeBlockFilename>
                        )}
                      </CodeBlockFiles>
                      <CodeBlockCopyButton />
                    </CodeBlockHeader>
                    <CodeBlockBody>
                      {(item: { language: string; filename: string; code: string }) => (
                        <CodeBlockItem value={item.filename} lineNumbers>
                          <CodeBlockContent language={item.language}>
                            {item.code}
                          </CodeBlockContent>
                        </CodeBlockItem>
                      )}
                    </CodeBlockBody>
                  </CodeBlock>
                </div>
              ) : (
                <div className="text-muted-foreground text-center py-8">
                  No source code available
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === 'graph' && (
          <Card>
            <CardHeader>
              <CardTitle>Related Nodes Graph</CardTitle>
              <CardDescription>
                Showing {related_nodes.length} related node{related_nodes.length !== 1 ? 's' : ''}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative border rounded-lg" style={{ height: '600px' }}>
                <div className="absolute bottom-2 left-2 z-10 px-2 py-1 text-xs text-muted-foreground bg-background/80 backdrop-blur-sm rounded pointer-events-none">
                  Scroll to zoom • Click & drag to pan • Click node for details
                </div>
                <div style={{ width: '100%', height: '100%' }}>
                  <InteractiveNvlWrapper
                    nodes={nvlData.nodes}
                    rels={nvlData.relationships}
                    nvlOptions={{
                      initialZoom: 1.0,
                      minZoom: 0.1,
                      maxZoom: 4.0,
                    }}
                    mouseEventCallbacks={{
                      onNodeClick: (clickedNode: unknown) => {
                        if (clickedNode && typeof clickedNode === 'object' && 'id' in clickedNode) {
                          const clickedNodeId = clickedNode.id as string
                          const url = `/node/${encodeURIComponent(clickedNodeId)}?project=${encodeURIComponent(projectPath!)}`
                          window.open(url, '_blank')
                        }
                      },
                      onRelationshipClick: () => {},
                      onZoom: () => {},
                      onPan: () => {},
                    }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === 'list' && (
          <Card>
            <CardHeader>
              <CardTitle>Related Nodes</CardTitle>
              <CardDescription>
                {related_nodes.length} related node{related_nodes.length !== 1 ? 's' : ''} found
              </CardDescription>
            </CardHeader>
            <CardContent>
              {related_nodes.length > 0 ? (
                <div className="space-y-3">
                  {related_nodes.map((relatedNode) => {
                    const edges = related_edges.filter(
                      (e) => e.source === node.id && e.target === relatedNode.id
                        || e.target === node.id && e.source === relatedNode.id
                    )
                    return (
                      <div
                        key={relatedNode.id}
                        className="p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="font-medium">{relatedNode.label}</span>
                              <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground capitalize">
                                {relatedNode.type}
                              </span>
                            </div>
                            {relatedNode.path && (
                              <div className="text-sm text-muted-foreground font-mono mb-2">
                                {relatedNode.path}
                              </div>
                            )}
                            {edges.length > 0 && (
                              <div className="text-xs text-muted-foreground">
                                <span className="font-medium">Relationships:</span>{' '}
                                {edges.map((e) => (
                                  <span key={e.id} className="capitalize mr-2">
                                    {e.type}
                                  </span>
                                ))}
                              </div>
                            )}
                            {relatedNode.properties && (
                              <div className="mt-2 text-xs text-muted-foreground">
                                {Object.entries(relatedNode.properties).map(([key, value]) => (
                                  <div key={key}>
                                    <span className="font-medium">{key}:</span>{' '}
                                    {String(value)}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              const url = `/node/${encodeURIComponent(relatedNode.id)}?project=${encodeURIComponent(projectPath!)}`
                              window.open(url, '_blank')
                            }}
                          >
                            View Details
                          </Button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  No related nodes found
                </div>
              )}

              {/* Deep Trace Section */}
              <div className="pt-4 border-t mt-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold">Deep Trace Analysis</h3>
                  <Button 
                    variant="secondary" 
                    size="sm" 
                    onClick={handleDeepTrace}
                    disabled={deepTraceLoading}
                  >
                    {deepTraceLoading ? (
                      <>
                        <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Network className="h-3 w-3 mr-2" />
                        Run Deep Trace
                      </>
                    )}
                  </Button>
                </div>
                
                {showDeepTraceResults && (
                  <div className="space-y-4">
                    {deepTraceLoading ? (
                      <div className="text-sm text-muted-foreground">
                        Analyzing source code for implicit relationships...
                      </div>
                    ) : deepTraceResults.length > 0 ? (
                      <div className="space-y-3">
                        {deepTraceResults.map((result, idx) => (
                          <div key={idx} className="p-3 border rounded-lg bg-muted/30">
                            <div className="flex items-start justify-between">
                              <div>
                                <div className="font-medium text-sm flex items-center gap-2">
                                  <span className="uppercase text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                                    {result.call.method || 'EVENT'}
                                  </span>
                                  <span className="font-mono">{result.call.target}</span>
                                </div>
                                <div className="text-xs text-muted-foreground mt-1 font-mono bg-muted p-1 rounded">
                                  {result.call.evidence}
                                </div>
                              </div>
                            </div>
                            
                            <div className="mt-3 pl-4 border-l-2">
                              <div className="text-xs font-medium text-muted-foreground mb-2">Proposed Matches:</div>
                              {result.proposed_matches && result.proposed_matches.length > 0 ? (
                                <div className="space-y-2">
                                  {result.proposed_matches.map((match: any) => (
                                    <div key={match.id} className="flex items-center justify-between bg-background p-2 rounded border">
                                      <div className="text-sm truncate flex-1 mr-2">
                                        {match.label}
                                      </div>
                                      <Button 
                                        size="sm" 
                                        variant="outline" 
                                        className="h-7 text-xs"
                                        onClick={() => handleApplyDeepTrace(result, match)}
                                      >
                                        Link
                                      </Button>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div className="text-xs text-muted-foreground italic">No internal matches found</div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground italic">
                        No implicit relationships found.
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

