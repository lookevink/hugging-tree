'use client'

import { useState, useEffect, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, Network, X } from 'lucide-react'
import { toast } from 'sonner'
import '@/src/lib/api-client'
import { apiGetGraphGraphPost } from '@/src/lib/api'

// Dynamically import InteractiveNvlWrapper to avoid SSR issues
const InteractiveNvlWrapper = dynamic(
  () => import('@neo4j-nvl/react').then((mod) => mod.InteractiveNvlWrapper),
  { ssr: false }
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
  const [isFiltered, setIsFiltered] = useState(false)

  const loadGraph = useCallback(async (filePaths?: string[]) => {
    try {
      setLoading(true)
      const response = await apiGetGraphGraphPost({
        body: {
          path: projectPath,
          file_paths: filePaths || null,
          max_nodes: filePaths ? 200 : 500, // Limit nodes when filtering
        },
      })

      if (response.data) {
        const data = response.data as unknown as GraphData
        console.log('Graph data received:', {
          nodeCount: data.nodes?.length || 0,
          edgeCount: data.edges?.length || 0,
        })
        const converted = convertToNvlFormat(data)
        console.log('Converted NVL data:', {
          nodeCount: converted.nodes?.length || 0,
          relCount: converted.relationships?.length || 0,
          sampleNode: converted.nodes[0],
          sampleRel: converted.relationships[0],
        })
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
    console.log('Node clicked:', node)
    // Could show details in a sidebar or modal
  }, [])

  const handleRelationshipClick = useCallback((relationship: unknown) => {
    console.log('Relationship clicked:', relationship)
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
          <div className="border rounded-lg overflow-hidden" style={{ height: '600px' }}>
            <InteractiveNvlWrapper
              nodes={nvlData.nodes}
              rels={nvlData.relationships}
              mouseEventCallbacks={{
                onNodeClick: handleNodeClick,
                onRelationshipClick: handleRelationshipClick,
              }}
            />
          </div>
        ) : (
          <div className="flex items-center justify-center h-96 text-muted-foreground">
            No graph data available. Scan the project first.
          </div>
        )}
      </CardContent>
    </Card>
  )
}

