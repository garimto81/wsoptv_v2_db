'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { FileWarning, Copy, BarChart3 } from 'lucide-react'
import { useNASStats, useParserStats, useDuplicates } from '@/hooks/use-nas'
import { useLinkageStats } from '@/hooks/use-quality'

export default function NASPage() {
  const { data: nasStats, isLoading: nasLoading } = useNASStats()
  const { data: linkageStats, isLoading: linkageLoading } = useLinkageStats()
  const { data: parserStats, isLoading: parserLoading } = useParserStats()
  const { data: duplicates } = useDuplicates()

  // Individual loading states used in the UI
  void nasLoading
  void linkageLoading

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">NAS Inventory</h1>
        <p className="text-zinc-400 mt-1">
          Verify NAS file scanning and linking status
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">Total Files</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {nasStats?.total_files?.toLocaleString() ?? '-'}
            </div>
            <p className="text-xs text-zinc-500 mt-1">
              {nasStats?.video_count ?? 0} videos,{' '}
              {nasStats?.metadata_count ?? 0} metadata
            </p>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">Linked</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">
              {linkageStats?.nas_files.linked?.toLocaleString() ?? '-'}
            </div>
            <Progress
              value={
                ((linkageStats?.nas_files.linked ?? 0) /
                  (linkageStats?.nas_files.total || 1)) *
                100
              }
              className="h-1.5 mt-2 bg-zinc-800"
            />
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">Unlinked</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">
              {linkageStats?.nas_files.unlinked?.toLocaleString() ?? '-'}
            </div>
            <p className="text-xs text-zinc-500 mt-1">
              Requires manual linking
            </p>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">Parse Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {parserStats?.parse_rate.toFixed(1) ?? '-'}%
            </div>
            <p className="text-xs text-zinc-500 mt-1">
              {parserStats?.parsed_files ?? 0} / {parserStats?.total_files ?? 0}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Link href="/nas/unlinked">
          <Card className="bg-zinc-900 border-zinc-800 hover:border-amber-500/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center justify-between p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-amber-500/10">
                  <FileWarning className="h-6 w-6 text-amber-500" />
                </div>
                <div>
                  <div className="font-medium">Unlinked Files</div>
                  <div className="text-sm text-zinc-400">
                    Files without VideoFile connection
                  </div>
                </div>
              </div>
              <Badge variant="secondary" className="font-mono">
                {linkageStats?.nas_files.unlinked ?? 0}
              </Badge>
            </CardContent>
          </Card>
        </Link>

        <Link href="/nas/duplicates">
          <Card className="bg-zinc-900 border-zinc-800 hover:border-blue-500/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center justify-between p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-blue-500/10">
                  <Copy className="h-6 w-6 text-blue-500" />
                </div>
                <div>
                  <div className="font-medium">Duplicate Files</div>
                  <div className="text-sm text-zinc-400">
                    Suspected duplicate files
                  </div>
                </div>
              </div>
              <Badge variant="secondary" className="font-mono">
                {duplicates?.total_duplicate_files ?? 0}
              </Badge>
            </CardContent>
          </Card>
        </Link>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="flex items-center justify-between p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-emerald-500/10">
                <BarChart3 className="h-6 w-6 text-emerald-500" />
              </div>
              <div>
                <div className="font-medium">Parser Statistics</div>
                <div className="text-sm text-zinc-400">
                  {parserStats?.by_parser.length ?? 0} parsers active
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Parser Stats Table */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400">
            Parser Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          {parserLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="h-8 bg-zinc-800 rounded animate-pulse"
                />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {parserStats?.by_parser
                .filter((p) => p.matched_count > 0)
                .sort((a, b) => b.matched_count - a.matched_count)
                .map((parser) => (
                  <div
                    key={parser.parser_name}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium w-32">
                        {parser.parser_name}
                      </span>
                      <Progress
                        value={parser.percentage}
                        className="h-2 w-48 bg-zinc-800"
                      />
                    </div>
                    <div className="text-sm text-zinc-400">
                      {parser.matched_count.toLocaleString()} (
                      {parser.percentage.toFixed(1)}%)
                    </div>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
