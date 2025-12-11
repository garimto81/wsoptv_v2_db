'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Copy, FileVideo } from 'lucide-react'
import { useDuplicates } from '@/hooks/use-nas'

export default function DuplicatesPage() {
  const { data: duplicates, isLoading } = useDuplicates()

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Calculate wasted bytes (sum of extra copies)
  const wastedBytes = duplicates?.groups?.reduce((acc, group) => {
    const extraCopies = group.file_count - 1
    const avgFileSize = group.total_size_bytes / group.file_count
    return acc + avgFileSize * extraCopies
  }, 0) ?? 0

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/nas">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Duplicate Files</h1>
          <p className="text-zinc-400 mt-1">
            Files with same name and size (suspected duplicates)
          </p>
        </div>
      </div>

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">
              Duplicate Groups
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">
              {duplicates?.total_groups?.toLocaleString() ?? '-'}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">
              Total Duplicate Files
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">
              {duplicates?.total_duplicate_files?.toLocaleString() ?? '-'}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">
              Wasted Space
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">
              {wastedBytes > 0 ? formatBytes(wastedBytes) : '-'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Duplicate Groups */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400">
            Duplicate Groups
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-24 bg-zinc-800 rounded animate-pulse"
                />
              ))}
            </div>
          ) : duplicates?.groups && duplicates.groups.length > 0 ? (
            <div className="space-y-4">
              {duplicates.groups.map((group, index) => (
                <div
                  key={index}
                  className="p-4 bg-zinc-800/50 rounded-lg space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Copy className="h-4 w-4 text-blue-500" />
                      <span className="font-medium">{group.base_name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">
                        {group.file_count} copies
                      </Badge>
                      <Badge variant="outline">
                        {formatBytes(group.total_size_bytes)}
                      </Badge>
                    </div>
                  </div>
                  <div className="space-y-1">
                    {group.files.map((file) => (
                      <div
                        key={file.id}
                        className="flex items-center gap-2 text-sm text-zinc-400"
                      >
                        <FileVideo className="h-3 w-3" />
                        <span className="font-mono text-xs truncate">
                          {file.file_path}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No duplicate files found
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
