'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  AlertTriangle,
  FileWarning,
  RefreshCcw,
  Unlink,
  ArrowRight,
} from 'lucide-react'
import type { ProblemSummaryResponse } from '@/types/api'

interface ProblemItemProps {
  icon: React.ElementType
  label: string
  count: number
  href: string
}

function ProblemItem({ icon: Icon, label, count, href }: ProblemItemProps) {
  if (count === 0) return null

  return (
    <Link
      href={href}
      className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50 hover:bg-zinc-800 transition-colors group"
    >
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-red-500/10">
          <Icon className="h-4 w-4 text-red-500" />
        </div>
        <span className="text-sm text-zinc-300">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="destructive" className="font-mono">
          {count}
        </Badge>
        <ArrowRight className="h-4 w-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
      </div>
    </Link>
  )
}

interface ProblemSummaryProps {
  data?: ProblemSummaryResponse
  loading?: boolean
}

export function ProblemSummary({ data, loading }: ProblemSummaryProps) {
  const problems = [
    {
      icon: FileWarning,
      label: 'Unlinked NAS Files',
      count: data?.unlinked_nas_files ?? 0,
      href: '/nas/unlinked',
    },
    {
      icon: AlertTriangle,
      label: 'Parsing Failed',
      count: data?.parsing_failed_files ?? 0,
      href: '/nas?filter=failed',
    },
    {
      icon: RefreshCcw,
      label: 'Sync Errors',
      count: data?.sync_errors ?? 0,
      href: '/sync/errors',
    },
    {
      icon: Unlink,
      label: 'Orphan HandClips',
      count: data?.orphan_hand_clips ?? 0,
      href: '/catalog/orphans?type=hand_clip',
    },
    {
      icon: Unlink,
      label: 'Orphan VideoFiles',
      count: data?.orphan_video_files ?? 0,
      href: '/catalog/orphans?type=video_file',
    },
    {
      icon: Unlink,
      label: 'Orphan Episodes',
      count: data?.orphan_episodes ?? 0,
      href: '/catalog/orphans?type=episode',
    },
  ]

  const totalProblems = data?.total_problems ?? 0

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-zinc-300">
          Problems Summary
        </CardTitle>
        <Badge
          variant={totalProblems > 0 ? 'destructive' : 'secondary'}
          className="font-mono"
        >
          {totalProblems} total
        </Badge>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-12 bg-zinc-800 rounded animate-pulse"
              />
            ))}
          </div>
        ) : totalProblems === 0 ? (
          <div className="text-center py-6 text-zinc-500">
            <div className="text-2xl mb-2">All clear</div>
            <div className="text-sm">No problems detected</div>
          </div>
        ) : (
          <div className="space-y-2">
            {problems.map(
              (problem, idx) =>
                problem.count > 0 && <ProblemItem key={idx} {...problem} />
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
