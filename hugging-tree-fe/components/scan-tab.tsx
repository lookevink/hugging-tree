'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { apiScanScanPost } from '@/src/lib/api'
import { toast } from 'sonner'
import { Loader2, Scan, CheckCircle2 } from 'lucide-react'

interface ScanTabProps {
  projectPath: string
}

export function ScanTab({ projectPath }: ScanTabProps) {
  const [path, setPath] = useState(projectPath)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleScan = async () => {
    if (!path.trim()) {
      toast.error('Error', {
        description: 'Please enter a project path',
      })
      return
    }

    try {
      setLoading(true)
      setResult(null)
      const response = await apiScanScanPost({
        body: { path },
      })
      
      if (response.data) {
        setResult(response.data)
        toast.success('Success', {
          description: `Scanned ${(response.data as any).files_scanned || 0} files`,
        })
      }
    } catch (error: any) {
      toast.error('Error', {
        description: error.message || 'Failed to scan repository',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Scan className="h-5 w-5" />
          Scan Repository
        </CardTitle>
        <CardDescription>
          Scan a repository and sync to Neo4j graph database and ChromaDB vector database
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="scan-path">Project Path</Label>
          <Input
            id="scan-path"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="/projects/your-repo"
            disabled={loading}
          />
        </div>
        <Button onClick={handleScan} disabled={loading || !path.trim()}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Scan Repository
        </Button>

        {result && (
          <Card className="mt-4 bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
            <CardContent className="pt-6">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
                  <span className="font-semibold">Scan Complete</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold">Status:</span>
                  <span className="text-green-600 dark:text-green-400">{(result as any).status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold">Files Scanned:</span>
                  <span>{(result as any).files_scanned || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold">Total Files in Graph:</span>
                  <span>{(result as any).total_files_in_graph || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  )
}

