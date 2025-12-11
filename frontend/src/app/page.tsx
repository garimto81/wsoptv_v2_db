'use client'

import { useState } from 'react'
import { HardDrive, RefreshCcw, Link2, Database, Loader2 } from 'lucide-react'
import { StatusCard } from '@/components/dashboard/status-card'
import { ProblemSummary } from '@/components/dashboard/problem-summary'
import { LinkageChart } from '@/components/dashboard/linkage-chart'
import { ParserChart } from '@/components/dashboard/parser-chart'
import { useLinkageStats, useProblems, useBuildCatalog } from '@/hooks/use-quality'
import { useNASStats, useParserStats } from '@/hooks/use-nas'
import { useSyncErrors, useHandClipLinkageStats } from '@/hooks/use-sync'
import type { BuildCatalogResponse } from '@/types/api'

export default function DashboardPage() {
  const { data: linkageStats, isLoading: linkageLoading } = useLinkageStats()
  const { data: problems, isLoading: problemsLoading } = useProblems()
  const { data: nasStats, isLoading: nasLoading } = useNASStats()
  const { data: parserStats, isLoading: parserLoading } = useParserStats()
  const { data: syncErrors, isLoading: syncLoading } = useSyncErrors()
  const { data: handClipStats, isLoading: handClipLoading } =
    useHandClipLinkageStats()

  const buildCatalog = useBuildCatalog()
  const [buildResult, setBuildResult] = useState<BuildCatalogResponse | null>(null)

  const handleBuildCatalog = async () => {
    setBuildResult(null)
    const result = await buildCatalog.mutateAsync({ limit: 10000, skip_linked: true })
    setBuildResult(result)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">
            Data Quality Dashboard
          </h1>
          <p className="text-zinc-400 mt-1">
            Monitor and validate PokerVOD data quality
          </p>
        </div>
        <button
          onClick={handleBuildCatalog}
          disabled={buildCatalog.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
        >
          {buildCatalog.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Database className="h-4 w-4" />
          )}
          {buildCatalog.isPending ? 'Building...' : 'Build Catalog'}
        </button>
      </div>

      {/* Build Result Alert */}
      {buildResult && (
        <div className="p-4 bg-zinc-800/50 border border-zinc-700 rounded-lg">
          <h3 className="text-sm font-semibold text-zinc-200 mb-2">
            Build Result
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-zinc-400">Files Processed:</span>{' '}
              <span className="text-zinc-100">{buildResult.nas_files_processed}</span>
            </div>
            <div>
              <span className="text-zinc-400">VideoFiles Created:</span>{' '}
              <span className="text-green-400">{buildResult.video_files_created}</span>
            </div>
            <div>
              <span className="text-zinc-400">Links Created:</span>{' '}
              <span className="text-green-400">{buildResult.links_created}</span>
            </div>
            <div>
              <span className="text-zinc-400">Errors:</span>{' '}
              <span className={buildResult.errors > 0 ? 'text-red-400' : 'text-green-400'}>
                {buildResult.errors}
              </span>
            </div>
          </div>
          {buildResult.error_messages.length > 0 && (
            <div className="mt-2 text-xs text-red-400">
              {buildResult.error_messages.slice(0, 5).join(', ')}
            </div>
          )}
        </div>
      )}

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <StatusCard
          title="NAS Inventory"
          icon={HardDrive}
          href="/nas"
          loading={nasLoading || linkageLoading}
          items={[
            {
              label: 'Total Files',
              value: nasStats?.total_files?.toLocaleString() ?? '-',
              status: 'neutral',
            },
            {
              label: 'Linked',
              value: linkageStats?.nas_files.linked?.toLocaleString() ?? '-',
              status: 'success',
            },
            {
              label: 'Unlinked',
              value: linkageStats?.nas_files.unlinked?.toLocaleString() ?? '-',
              status:
                (linkageStats?.nas_files.unlinked ?? 0) > 0
                  ? 'warning'
                  : 'success',
            },
          ]}
          progress={
            linkageStats
              ? {
                  value:
                    ((linkageStats.nas_files.linked ?? 0) /
                      (linkageStats.nas_files.total || 1)) *
                    100,
                  label: 'Linkage Rate',
                }
              : undefined
          }
        />

        <StatusCard
          title="Sheets Sync"
          icon={RefreshCcw}
          href="/sync"
          loading={syncLoading || handClipLoading}
          items={[
            {
              label: 'Total Clips',
              value: handClipStats?.total_clips?.toLocaleString() ?? '-',
              status: 'neutral',
            },
            {
              label: 'With Video',
              value: handClipStats?.with_video_file?.toLocaleString() ?? '-',
              status: 'success',
            },
            {
              label: 'Sync Errors',
              value: syncErrors?.total_errors?.toLocaleString() ?? '-',
              status:
                (syncErrors?.total_errors ?? 0) > 0 ? 'error' : 'success',
            },
          ]}
          progress={
            handClipStats
              ? {
                  value: handClipStats.linkage_rate,
                  label: 'Linkage Rate',
                }
              : undefined
          }
        />

        <StatusCard
          title="Catalog Linkage"
          icon={Link2}
          href="/catalog"
          loading={linkageLoading}
          items={[
            {
              label: 'VideoFiles',
              value: linkageStats?.video_files.total?.toLocaleString() ?? '-',
              status: 'neutral',
            },
            {
              label: 'Episodes',
              value: linkageStats?.episodes.total?.toLocaleString() ?? '-',
              status: 'neutral',
            },
            {
              label: 'HandClips',
              value: linkageStats?.hand_clips.total?.toLocaleString() ?? '-',
              status: 'neutral',
            },
          ]}
          progress={
            linkageStats
              ? {
                  value: linkageStats.overall_linkage_rate,
                  label: 'Overall Linkage',
                }
              : undefined
          }
        />
      </div>

      {/* Charts and Problems */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <ProblemSummary data={problems} loading={problemsLoading} />
        </div>
        <div className="lg:col-span-1">
          <LinkageChart data={linkageStats} loading={linkageLoading} />
        </div>
        <div className="lg:col-span-1">
          <ParserChart data={parserStats} loading={parserLoading} />
        </div>
      </div>
    </div>
  )
}
