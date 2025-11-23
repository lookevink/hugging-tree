'use client'

import { useState, useEffect, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, Network, X, Info } from 'lucide-react'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import '@/src/lib/api-client'
import { getGraphGraphPost, deepTraceAnalyzeDeepTraceAnalyzePost, deepTraceApplyDeepTraceApplyPost } from '@/src/lib/api'

// Dynamically import InteractiveNvlWrapper to avoid SSR issues
const InteractiveNvlWrapper = dynamic(
  () => {
    return import('@neo4j-nvl/react').then((mod) => {
      // Log worker creation attempts for debugging
      if (typeof window !== 'undefined') {
        const originalWorker = window.Worker
        window.Worker = class extends originalWorker {
          constructor(scriptURL: string | URL, options?: WorkerOptions) {
            const urlStr = typeof scriptURL === 'string' ? scriptURL : scriptURL.toString()
            try {
              super(scriptURL, options)
            } catch (error) {
              console.error('Worker creation failed:', error, 'URL:', urlStr)
              // Don't throw - let the library handle the error
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

interface GraphTabProps {
  projectPath: string
  filterFiles?: string[] // Optional: files to filter to (from analyze/plan results)
}

interface GraphNode {
  id: string
  label: string
  type: string
  path?: string
  properties?: Record<string, unknown>
}

interface GraphEdge {
  id: string
  source: string
  target: string
  type: string
  label: string
}

// NVL types (simplified)
interface NvlNode {
  id: string
  captions: Array<{ value: string }>
  labels?: string[]
  properties?: Record<string, unknown>
}

interface NvlRelationship {
  id: string
  from: string
  to: string
  captions: Array<{ value: string }>
  type?: string
  properties?: Record<string, unknown>
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// Convert our graph format to NVL format
// NVL expects: nodes with captions array, rels with from/to and captions array
function convertToNvlFormat(data: GraphData): { nodes: NvlNode[]; relationships: NvlRelationship[] } {
  const nvlNodes: NvlNode[] = data.nodes.map((node) => ({
    id: node.id,
    captions: [{ value: node.label }],
    labels: [node.type],
    properties: {
      ...node.properties,
      label: node.label,
      path: node.path || '',
    },
  }))

  const nvlRels: NvlRelationship[] = data.edges.map((edge) => ({
    id: edge.id,
    from: edge.source,
    to: edge.target,
    captions: [{ value: edge.label || edge.type }],
    type: edge.type,
    properties: {
      label: edge.label,
    },
  }))

  return { nodes: nvlNodes, relationships: nvlRels }
}

export function GraphTab({ projectPath, filterFiles }: GraphTabProps) {
  const [loading, setLoading] = useState(false)
  const [nvlData, setNvlData] = useState<{ nodes: NvlNode[]; relationships: NvlRelationship[] } | null>(null)
  const [originalGraphData, setOriginalGraphData] = useState<GraphData | null>(null)
  const [isFiltered, setIsFiltered] = useState(false)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [relatedNodes, setRelatedNodes] = useState<{ node: GraphNode; relationship: GraphEdge }[]>([])
  const [isNodeDialogOpen, setIsNodeDialogOpen] = useState(false)
  const [deepTraceLoading, setDeepTraceLoading] = useState(false)
  const [deepTraceResults, setDeepTraceResults] = useState<any[]>([])
  const [showDeepTraceResults, setShowDeepTraceResults] = useState(false)

  const handleDeepTrace = async () => {
    if (!selectedNode) return
    
    try {
      setDeepTraceLoading(true)
      setShowDeepTraceResults(true)
      const response = await deepTraceAnalyzeDeepTraceAnalyzePost({
        body: {
          node_id: selectedNode.id,
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
    if (!selectedNode) return
    
    try {
      await deepTraceApplyDeepTraceApplyPost({
        body: {
          source_id: selectedNode.id,
          target_id: match.id,
          rel_type: result.call.type === 'api_call' ? 'CALLS_API' : 'PRODUCES_EVENT'
        }
      })
      
      toast.success("Relationship Applied", {
        description: `Linked to ${match.label}`
      })
      
      // Reload graph to show new link
      loadGraph(isFiltered ? filterFiles : undefined)
      setIsNodeDialogOpen(false)
      
    } catch (error) {
      toast.error("Failed to apply relationship")
    }
  }

  const loadGraph = useCallback(async (filePaths?: string[]) => {
    try {
      setLoading(true)
      const response = await getGraphGraphPost({
        body: {
          project_root: projectPath,
          file_paths: filePaths || null,
          max_nodes: filePaths ? 200 : 500, // Limit nodes when filtering
        },
      })

      if (response.data) {
        const data = response.data as unknown as GraphData
      
        setOriginalGraphData(data) // Store original data for node details
        const converted = convertToNvlFormat(data)
      
        setNvlData(converted)
        setIsFiltered(!!filePaths)
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load graph'
      toast.error('Error', {
        description: errorMessage,
      })
    } finally {
      setLoading(false)
    }
  }, [projectPath])

  useEffect(() => {
    // Load graph on mount, or when filterFiles changes
    if (filterFiles && filterFiles.length > 0) {
      loadGraph(filterFiles)
    } else {
      loadGraph()
    }
  }, [loadGraph, filterFiles])


  const handleNodeClick = useCallback((node: unknown) => {
    // Find the original node data and related nodes
    if (originalGraphData && node && typeof node === 'object' && 'id' in node) {
      const nodeId = node.id as string
      const originalNode = originalGraphData.nodes.find((n) => n.id === nodeId)
      if (originalNode) {
        setSelectedNode(originalNode)
        
        // Find related nodes (nodes connected via edges)
        const related: { node: GraphNode; relationship: GraphEdge }[] = []
        originalGraphData.edges.forEach((edge) => {
          if (edge.source === nodeId) {
            const targetNode = originalGraphData.nodes.find((n) => n.id === edge.target)
            if (targetNode) {
              related.push({ node: targetNode, relationship: edge })
            }
          } else if (edge.target === nodeId) {
            const sourceNode = originalGraphData.nodes.find((n) => n.id === edge.source)
            if (sourceNode) {
              related.push({ node: sourceNode, relationship: edge })
            }
          }
        })
        setRelatedNodes(related)
        setIsNodeDialogOpen(true)
      }
    }
  }, [originalGraphData])

  const handleRelationshipClick = useCallback((relationship: unknown) => {
  }, [])

  // Use library's built-in callbacks for zoom and pan (as per documentation)
  const handleZoom = useCallback((zoomLevel: number) => {
  }, [])

  const handlePan = useCallback((panning: { x: number; y: number }, evt: MouseEvent) => {
  }, [])

  const handleClearFilter = () => {
    loadGraph()
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5" />
              Graph Visualization
            </CardTitle>
            <CardDescription>
              {isFiltered
                ? `Showing filtered view (${filterFiles?.length || 0} files)`
                : 'Top-down view of the entire project'}
            </CardDescription>
          </div>
          {isFiltered && (
            <Button variant="outline" size="sm" onClick={handleClearFilter}>
              <X className="h-4 w-4 mr-2" />
              Show All
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : nvlData && nvlData.nodes && nvlData.nodes.length > 0 ? (
          <div className="relative border rounded-lg" style={{ height: '600px' }}>
            {/* Instructions */}
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
                  onNodeClick: handleNodeClick,
                  onRelationshipClick: handleRelationshipClick,
                  onZoom: handleZoom,
                  onPan: handlePan,
                }}
              />
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-96 text-muted-foreground">
            No graph data available. Scan the project first.
          </div>
        )}
      </CardContent>

      {/* Node Details Dialog */}
      <Dialog open={isNodeDialogOpen} onOpenChange={setIsNodeDialogOpen}>
        <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              Node Details
            </DialogTitle>
            <DialogDescription>
              Information about the selected node and its relationships
            </DialogDescription>
          </DialogHeader>
          {selectedNode && (
            <div className="mt-4 space-y-6">
              <div>
                <h3 className="text-sm font-semibold mb-1">Label</h3>
                <p className="text-sm text-muted-foreground">{selectedNode.label}</p>
              </div>
              <div>
                <h3 className="text-sm font-semibold mb-1">Type</h3>
                <p className="text-sm text-muted-foreground capitalize">{selectedNode.type}</p>
              </div>
              {selectedNode.path && (
                <div>
                  <h3 className="text-sm font-semibold mb-1">Path</h3>
                  <p className="text-sm text-muted-foreground font-mono break-all">{selectedNode.path}</p>
                </div>
              )}
              {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">Properties</h3>
                  <div className="space-y-2">
                    {Object.entries(selectedNode.properties).map(([key, value]) => (
                      <div key={key} className="text-sm">
                        <span className="font-medium">{key}:</span>{' '}
                        <span className="text-muted-foreground">
                          {typeof value === 'object' && value !== null
                            ? JSON.stringify(value, null, 2)
                            : value != null
                              ? String(value)
                              : 'null'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {selectedNode.type === 'function' && selectedNode.properties && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">Function Details</h3>
                  {(() => {
                    const filePath = selectedNode.properties.file_path
                    return filePath ? (
                      <div className="text-sm mb-1">
                        <span className="font-medium">File:</span>{' '}
                        <span className="text-muted-foreground font-mono">{String(filePath)}</span>
                      </div>
                    ) : null
                  })()}
                  {(() => {
                    const startLine = selectedNode.properties.start_line
                    const endLine = selectedNode.properties.end_line
                    return startLine != null && endLine != null ? (
                      <div className="text-sm">
                        <span className="font-medium">Lines:</span>{' '}
                        <span className="text-muted-foreground">
                          {String(startLine)} - {String(endLine)}
                        </span>
                      </div>
                    ) : null
                  })()}
                </div>
              )}
              {selectedNode.type === 'class' && selectedNode.properties && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">Class Details</h3>
                  {(() => {
                    const filePath = selectedNode.properties.file_path
                    return filePath ? (
                      <div className="text-sm mb-1">
                        <span className="font-medium">File:</span>{' '}
                        <span className="text-muted-foreground font-mono">{String(filePath)}</span>
                      </div>
                    ) : null
                  })()}
                  {(() => {
                    const startLine = selectedNode.properties.start_line
                    const endLine = selectedNode.properties.end_line
                    return startLine != null && endLine != null ? (
                      <div className="text-sm">
                        <span className="font-medium">Lines:</span>{' '}
                        <span className="text-muted-foreground">
                          {String(startLine)} - {String(endLine)}
                        </span>
                      </div>
                    ) : null
                  })()}
                </div>
              )}
              
              {/* Related Nodes */}
              {relatedNodes.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold mb-3">Related Nodes ({relatedNodes.length})</h3>
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {relatedNodes.map(({ node, relationship }) => (
                      <div
                        key={`${relationship.id}-${node.id}`}
                        className="p-3 border rounded-lg hover:bg-accent/50 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm font-medium truncate">{node.label}</span>
                              <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground capitalize">
                                {node.type}
                              </span>
                            </div>
                            <div className="text-xs text-muted-foreground mb-1">
                              <span className="font-medium">Relationship:</span>{' '}
                              <span className="capitalize">{relationship.type}</span>
                            </div>
                            {node.path && (
                              <div className="text-xs text-muted-foreground font-mono truncate">
                                {node.path}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {relatedNodes.length === 0 && (
                <div className="text-sm text-muted-foreground italic">
                  No related nodes found
                </div>
              )}
              {/* Deep Trace Section */}
              <div className="pt-4 border-t">
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
            </div>
          )}
        </DialogContent>
      </Dialog>
    </Card>
  )
}

