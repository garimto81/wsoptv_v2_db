'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Unlink } from 'lucide-react'
import { useOrphans } from '@/hooks/use-quality'

const orphanTypes = [
  { value: 'nas_file', label: 'NAS Files' },
  { value: 'video_file', label: 'Video Files' },
  { value: 'hand_clip', label: 'Hand Clips' },
  { value: 'episode', label: 'Episodes' },
]

export default function OrphansPage() {
  const [selectedType, setSelectedType] = useState<string>('nas_file')
  const { data: orphanData, isLoading } = useOrphans(selectedType)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Orphan Records</h1>
          <p className="text-zinc-400 mt-1">
            Records missing parent entity links
          </p>
        </div>
        <Badge variant="secondary" className="font-mono text-lg px-4 py-1">
          {orphanData?.total ?? 0} orphans
        </Badge>
      </div>

      <Tabs value={selectedType} onValueChange={setSelectedType}>
        <TabsList className="bg-zinc-800 border-zinc-700">
          {orphanTypes.map((type) => (
            <TabsTrigger
              key={type.value}
              value={type.value}
              className="data-[state=active]:bg-zinc-700"
            >
              {type.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {orphanTypes.map((type) => (
          <TabsContent key={type.value} value={type.value}>
            <Card className="bg-zinc-900 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm text-zinc-400">
                  {type.label} without required links
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="space-y-2">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div
                        key={i}
                        className="h-12 bg-zinc-800 rounded animate-pulse"
                      />
                    ))}
                  </div>
                ) : (orphanData?.items.length ?? 0) === 0 ? (
                  <div className="text-center py-12 text-zinc-500">
                    <div className="text-4xl mb-4">All clear!</div>
                    <div>No orphan {type.label.toLowerCase()} found</div>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-zinc-800">
                        <TableHead className="text-zinc-400">Name</TableHead>
                        <TableHead className="text-zinc-400">Type</TableHead>
                        <TableHead className="text-zinc-400">Reason</TableHead>
                        <TableHead className="text-zinc-400">Created</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {orphanData?.items.map((orphan) => (
                        <TableRow
                          key={orphan.id}
                          className="border-zinc-800"
                        >
                          <TableCell className="font-medium max-w-xs truncate">
                            {orphan.name}
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary">{orphan.type}</Badge>
                          </TableCell>
                          <TableCell className="max-w-md">
                            <div className="flex items-center gap-2">
                              <Unlink className="h-4 w-4 text-amber-500 flex-shrink-0" />
                              <span className="text-amber-400 text-sm">
                                {orphan.reason}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="text-zinc-500 text-sm">
                            {new Date(orphan.created_at).toLocaleDateString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
