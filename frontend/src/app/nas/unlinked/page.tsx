'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ArrowLeft, FileVideo, HardDrive } from 'lucide-react'
import { useNASStats } from '@/hooks/use-nas'

export default function UnlinkedFilesPage() {
  const { data: nasStats, isLoading } = useNASStats()

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/nas">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Unlinked Files</h1>
          <p className="text-zinc-400 mt-1">
            Video files without VideoFile connection
          </p>
        </div>
      </div>

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">
              Unlinked Videos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">
              {nasStats?.unlinked_count?.toLocaleString() ?? '-'}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">
              Linked Videos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">
              {nasStats?.linked_count?.toLocaleString() ?? '-'}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">
              Total Size
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {nasStats?.total_size_bytes
                ? formatBytes(nasStats.total_size_bytes)
                : '-'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* File Categories */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400">
            Files by Category
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="h-10 bg-zinc-800 rounded animate-pulse"
                />
              ))}
            </div>
          ) : nasStats?.by_category ? (
            <div className="space-y-3">
              {Object.entries(nasStats.by_category)
                .sort(([, a], [, b]) => b - a)
                .map(([category, count]) => (
                  <div
                    key={category}
                    className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {category === 'video' ? (
                        <FileVideo className="h-5 w-5 text-blue-500" />
                      ) : (
                        <HardDrive className="h-5 w-5 text-zinc-500" />
                      )}
                      <span className="font-medium capitalize">{category}</span>
                    </div>
                    <Badge variant="secondary" className="font-mono">
                      {count.toLocaleString()}
                    </Badge>
                  </div>
                ))}
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No category data available
            </div>
          )}
        </CardContent>
      </Card>

      {/* File Extensions */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400">
            Files by Extension
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="h-8 bg-zinc-800 rounded animate-pulse"
                />
              ))}
            </div>
          ) : nasStats?.by_extension ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {Object.entries(nasStats.by_extension)
                .sort(([, a], [, b]) => b - a)
                .map(([ext, count]) => (
                  <div
                    key={ext}
                    className="flex items-center justify-between p-2 bg-zinc-800/50 rounded"
                  >
                    <span className="text-sm font-mono text-zinc-300">
                      {ext}
                    </span>
                    <Badge variant="outline" className="font-mono text-xs">
                      {count.toLocaleString()}
                    </Badge>
                  </div>
                ))}
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No extension data available
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
