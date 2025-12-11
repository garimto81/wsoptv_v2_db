'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Unlink, BarChart3, GitBranch } from 'lucide-react'
import { useLinkageStats, useProjectLinkage } from '@/hooks/use-quality'

export default function CatalogPage() {
  const { data: linkageStats } = useLinkageStats()
  const { data: projectLinkage, isLoading: projectLoading } =
    useProjectLinkage()

  const entities = [
    {
      name: 'NAS Files',
      total: linkageStats?.nas_files.total ?? 0,
      linked: linkageStats?.nas_files.linked ?? 0,
      unlinked: linkageStats?.nas_files.unlinked ?? 0,
    },
    {
      name: 'Video Files',
      total: linkageStats?.video_files.total ?? 0,
      linked: linkageStats?.video_files.with_episode ?? 0,
      unlinked: linkageStats?.video_files.without_episode ?? 0,
    },
    {
      name: 'Episodes',
      total: linkageStats?.episodes.total ?? 0,
      linked: linkageStats?.episodes.with_video ?? 0,
      unlinked: linkageStats?.episodes.without_video ?? 0,
    },
    {
      name: 'Hand Clips',
      total: linkageStats?.hand_clips.total ?? 0,
      linked: linkageStats?.hand_clips.with_video ?? 0,
      unlinked: linkageStats?.hand_clips.without_video ?? 0,
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Catalog Linkage</h1>
        <p className="text-zinc-400 mt-1">
          Verify data integrity across all entities
        </p>
      </div>

      {/* Overall Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {entities.map((entity) => (
          <Card key={entity.name} className="bg-zinc-900 border-zinc-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-zinc-400">
                {entity.name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {entity.total.toLocaleString()}
              </div>
              <div className="flex items-center gap-2 mt-2">
                <Progress
                  value={(entity.linked / (entity.total || 1)) * 100}
                  className="h-1.5 flex-1 bg-zinc-800"
                />
                <span className="text-xs text-zinc-500">
                  {((entity.linked / (entity.total || 1)) * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between text-xs text-zinc-500 mt-1">
                <span className="text-emerald-500">
                  {entity.linked.toLocaleString()} linked
                </span>
                <span className="text-amber-500">
                  {entity.unlinked.toLocaleString()} unlinked
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Link href="/catalog/orphans">
          <Card className="bg-zinc-900 border-zinc-800 hover:border-amber-500/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center justify-between p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-amber-500/10">
                  <Unlink className="h-6 w-6 text-amber-500" />
                </div>
                <div>
                  <div className="font-medium">Orphan Records</div>
                  <div className="text-sm text-zinc-400">
                    Records without parent links
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/catalog/stats">
          <Card className="bg-zinc-900 border-zinc-800 hover:border-blue-500/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center justify-between p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-blue-500/10">
                  <BarChart3 className="h-6 w-6 text-blue-500" />
                </div>
                <div>
                  <div className="font-medium">Statistics</div>
                  <div className="text-sm text-zinc-400">
                    Detailed linkage analytics
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
                <GitBranch className="h-6 w-6 text-emerald-500" />
              </div>
              <div>
                <div className="font-medium">Overall Rate</div>
                <div className="text-sm text-zinc-400">
                  {linkageStats?.overall_linkage_rate.toFixed(1) ?? 0}% connected
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Project Linkage */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400">
            Linkage by Project
          </CardTitle>
        </CardHeader>
        <CardContent>
          {projectLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="h-8 bg-zinc-800 rounded animate-pulse"
                />
              ))}
            </div>
          ) : projectLinkage && projectLinkage.length > 0 ? (
            <div className="space-y-4">
              {projectLinkage
                .sort((a, b) => b.linkage_rate - a.linkage_rate)
                .map((project) => (
                  <div
                    key={project.project_id}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <Badge variant="secondary" className="w-24 justify-center">
                        {project.project_code}
                      </Badge>
                      <span className="text-sm text-zinc-300 w-32 truncate">
                        {project.project_name}
                      </span>
                      <Progress
                        value={project.linkage_rate}
                        className="h-2 flex-1 max-w-xs bg-zinc-800"
                      />
                    </div>
                    <div className="text-sm text-zinc-400 ml-4 text-right">
                      {project.linked_episodes} / {project.total_episodes} (
                      {project.linkage_rate.toFixed(1)}%)
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No project data available
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
