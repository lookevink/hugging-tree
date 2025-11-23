'use client'

import { GraphVisualization } from '@/components/graph-visualization'

interface GraphTabProps {
  projectPath: string
  filterFiles?: string[]
}

export function GraphTab({ projectPath, filterFiles }: GraphTabProps) {
  return (
    <GraphVisualization
      projectPath={projectPath}
      filterFiles={filterFiles}
      title="Graph Visualization"
      description={filterFiles 
        ? `Showing filtered view (${filterFiles.length} files)`
        : 'Top-down view of the entire project'}
      height="600px"
      maxNodes={500}
    />
  )
}

