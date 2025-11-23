'use client'

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { ScanTab } from '@/components/scan-tab'
import { QueryTab } from '@/components/query-tab'
import { AnalyzeTab } from '@/components/analyze-tab'
import { PlanTab } from '@/components/plan-tab'
import { GraphTab } from '@/components/graph-tab'
import { ArrowLeft } from 'lucide-react'

interface ProjectDetailViewProps {
  projectPath: string
  onBack: () => void
}

export function ProjectDetailView({ projectPath, onBack }: ProjectDetailViewProps) {
  const [activeTab, setActiveTab] = useState('scan')

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Projects
        </Button>
        <div>
          <h2 className="text-2xl font-bold">{projectPath.split('/').pop()}</h2>
          <p className="text-sm text-muted-foreground">{projectPath}</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="scan">Climb</TabsTrigger>
          <TabsTrigger value="query">Hang</TabsTrigger>
          <TabsTrigger value="analyze">Shake</TabsTrigger>
          <TabsTrigger value="plan">Plant</TabsTrigger>
          <TabsTrigger value="graph">Dig</TabsTrigger>
        </TabsList>

        <TabsContent value="scan" className="mt-6">
          <ScanTab projectPath={projectPath} />
        </TabsContent>

        <TabsContent value="query" className="mt-6">
          <QueryTab projectPath={projectPath} />
        </TabsContent>

        <TabsContent value="analyze" className="mt-6">
          <AnalyzeTab projectPath={projectPath} />
        </TabsContent>

        <TabsContent value="plan" className="mt-6">
          <PlanTab projectPath={projectPath} />
        </TabsContent>

        <TabsContent value="graph" className="mt-6">
          <GraphTab projectPath={projectPath} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

