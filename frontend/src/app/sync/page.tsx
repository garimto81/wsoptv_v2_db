'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { AlertTriangle, History, CheckCircle2 } from 'lucide-react'
import { useSyncErrors, useHandClipLinkageStats } from '@/hooks/use-sync'

export default function SyncPage() {
  const { data: syncErrors } = useSyncErrors()
  const { data: handClipStats, isLoading: statsLoading } =
    useHandClipLinkageStats()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">
          Google Sheets Sync
        </h1>
        <p className="text-zinc-400 mt-1">
          Verify sync status between Google Sheets and database
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">Total Clips</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {handClipStats?.total_clips?.toLocaleString() ?? '-'}
            </div>
            <p className="text-xs text-zinc-500 mt-1">HandClips created</p>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">
              With VideoFile
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">
              {handClipStats?.with_video_file?.toLocaleString() ?? '-'}
            </div>
            <Progress
              value={handClipStats?.linkage_rate ?? 0}
              className="h-1.5 mt-2 bg-zinc-800"
            />
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">
              With Episode
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">
              {handClipStats?.with_episode?.toLocaleString() ?? '-'}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Fully linked clips</p>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">
              Orphan Clips
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">
              {handClipStats?.orphan_clips?.toLocaleString() ?? '-'}
            </div>
            <p className="text-xs text-zinc-500 mt-1">No video or episode</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Link href="/sync/errors">
          <Card className="bg-zinc-900 border-zinc-800 hover:border-red-500/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center justify-between p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-red-500/10">
                  <AlertTriangle className="h-6 w-6 text-red-500" />
                </div>
                <div>
                  <div className="font-medium">Sync Errors</div>
                  <div className="text-sm text-zinc-400">
                    Failed sync operations
                  </div>
                </div>
              </div>
              <Badge
                variant={
                  (syncErrors?.total_errors ?? 0) > 0
                    ? 'destructive'
                    : 'secondary'
                }
                className="font-mono"
              >
                {syncErrors?.total_errors ?? 0}
              </Badge>
            </CardContent>
          </Card>
        </Link>

        <Link href="/sync/history">
          <Card className="bg-zinc-900 border-zinc-800 hover:border-blue-500/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center justify-between p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-blue-500/10">
                  <History className="h-6 w-6 text-blue-500" />
                </div>
                <div>
                  <div className="font-medium">Sync History</div>
                  <div className="text-sm text-zinc-400">
                    View sync records
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="flex items-center justify-between p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-emerald-500/10">
                <CheckCircle2 className="h-6 w-6 text-emerald-500" />
              </div>
              <div>
                <div className="font-medium">Linkage Rate</div>
                <div className="text-sm text-zinc-400">
                  {handClipStats?.linkage_rate.toFixed(1) ?? 0}% connected
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Linkage Breakdown */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400">
            HandClip Linkage Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          {statsLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-8 bg-zinc-800 rounded animate-pulse"
                />
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm">With VideoFile</span>
                <div className="flex items-center gap-4">
                  <Progress
                    value={handClipStats?.linkage_rate ?? 0}
                    className="h-2 w-48 bg-zinc-800"
                  />
                  <span className="text-sm text-zinc-400 w-24 text-right">
                    {handClipStats?.with_video_file ?? 0} (
                    {handClipStats?.linkage_rate.toFixed(1) ?? 0}%)
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm">With Episode</span>
                <div className="flex items-center gap-4">
                  <Progress
                    value={
                      ((handClipStats?.with_episode ?? 0) /
                        (handClipStats?.total_clips || 1)) *
                      100
                    }
                    className="h-2 w-48 bg-zinc-800"
                  />
                  <span className="text-sm text-zinc-400 w-24 text-right">
                    {handClipStats?.with_episode ?? 0} (
                    {(
                      ((handClipStats?.with_episode ?? 0) /
                        (handClipStats?.total_clips || 1)) *
                      100
                    ).toFixed(1)}
                    %)
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm">Video Only (no Episode)</span>
                <div className="flex items-center gap-4">
                  <Progress
                    value={
                      ((handClipStats?.video_only ?? 0) /
                        (handClipStats?.total_clips || 1)) *
                      100
                    }
                    className="h-2 w-48 bg-zinc-800"
                  />
                  <span className="text-sm text-zinc-400 w-24 text-right">
                    {handClipStats?.video_only ?? 0}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-amber-500">Orphan (no links)</span>
                <div className="flex items-center gap-4">
                  <Progress
                    value={
                      ((handClipStats?.orphan_clips ?? 0) /
                        (handClipStats?.total_clips || 1)) *
                      100
                    }
                    className="h-2 w-48 bg-zinc-800"
                  />
                  <span className="text-sm text-zinc-400 w-24 text-right">
                    {handClipStats?.orphan_clips ?? 0}
                  </span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
