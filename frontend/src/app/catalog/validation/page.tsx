'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  CheckCircle,
  XCircle,
  FileText,
  Layers,
  Calendar,
  Tag,
  AlertTriangle,
} from 'lucide-react'
import {
  useCatalogSummary,
  useCatalogSamples,
  useTitleQuality,
} from '@/hooks/use-quality'

export default function CatalogValidationPage() {
  const { data: summary, isLoading: summaryLoading } = useCatalogSummary()
  const { data: samples, isLoading: samplesLoading } = useCatalogSamples(5)
  const { data: titleQuality, isLoading: qualityLoading } = useTitleQuality()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Catalog Validation</h1>
        <p className="text-zinc-400 mt-1">
          제목 품질 검증 및 파서별 파싱 결과 확인
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Total Items
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {summaryLoading ? '...' : summary?.total_items.toLocaleString()}
            </div>
            <p className="text-xs text-zinc-500 mt-1">카탈로그 총 항목 수</p>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-emerald-500" />
              Title Coverage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-500">
              {summaryLoading ? '...' : `${summary?.title_coverage_rate}%`}
            </div>
            <Progress
              value={summary?.title_coverage_rate ?? 0}
              className="h-1.5 mt-2 bg-zinc-800"
            />
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <Layers className="h-4 w-4" />
              Projects
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {summaryLoading ? '...' : summary?.by_project.length}
            </div>
            <p className="text-xs text-zinc-500 mt-1">활성 프로젝트 수</p>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Quality Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {qualityLoading ? '...' : `${titleQuality?.quality_score}%`}
            </div>
            <p className="text-xs text-zinc-500 mt-1">
              이슈: {titleQuality?.issues_count ?? 0}건
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="by-project" className="space-y-4">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="by-project">프로젝트별</TabsTrigger>
          <TabsTrigger value="by-parser">파서별 샘플</TabsTrigger>
          <TabsTrigger value="by-year">연도별</TabsTrigger>
          <TabsTrigger value="issues">품질 이슈</TabsTrigger>
        </TabsList>

        {/* 프로젝트별 탭 */}
        <TabsContent value="by-project">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400">
                프로젝트별 카탈로그 분포
              </CardTitle>
            </CardHeader>
            <CardContent>
              {summaryLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="h-10 bg-zinc-800 rounded animate-pulse"
                    />
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {summary?.by_project.map((project) => (
                    <div
                      key={project.project_code}
                      className="flex items-center gap-4"
                    >
                      <Badge
                        variant="secondary"
                        className="w-20 justify-center"
                      >
                        {project.project_code}
                      </Badge>
                      <div className="flex-1">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-zinc-300">
                            {project.count.toLocaleString()} items
                          </span>
                          <span
                            className={
                              project.coverage_rate === 100
                                ? 'text-emerald-500'
                                : 'text-amber-500'
                            }
                          >
                            {project.coverage_rate}%
                          </span>
                        </div>
                        <Progress
                          value={project.coverage_rate}
                          className="h-2 bg-zinc-800"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 파서별 샘플 탭 */}
        <TabsContent value="by-parser">
          <div className="space-y-4">
            {samplesLoading ? (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-6">
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className="h-20 bg-zinc-800 rounded animate-pulse"
                      />
                    ))}
                  </div>
                </CardContent>
              </Card>
            ) : (
              samples?.map((parserGroup) => (
                <Card
                  key={parserGroup.parser_name}
                  className="bg-zinc-900 border-zinc-800"
                >
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Tag className="h-4 w-4 text-blue-500" />
                      {parserGroup.parser_name}
                      <Badge variant="outline" className="ml-2">
                        {parserGroup.total_count} samples
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow className="border-zinc-800">
                          <TableHead className="text-zinc-400">
                            파일명
                          </TableHead>
                          <TableHead className="text-zinc-400">
                            Display Title
                          </TableHead>
                          <TableHead className="text-zinc-400">Year</TableHead>
                          <TableHead className="text-zinc-400">
                            Event #
                          </TableHead>
                          <TableHead className="text-zinc-400 w-16">
                            Valid
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {parserGroup.samples.map((sample) => (
                          <TableRow
                            key={sample.id}
                            className="border-zinc-800 hover:bg-zinc-800/50"
                          >
                            <TableCell className="font-mono text-xs text-zinc-500 max-w-[200px] truncate">
                              {sample.file_name}
                            </TableCell>
                            <TableCell className="text-zinc-300 max-w-[300px]">
                              <span className="line-clamp-2">
                                {sample.display_title || (
                                  <span className="text-red-500">
                                    (no title)
                                  </span>
                                )}
                              </span>
                            </TableCell>
                            <TableCell className="text-zinc-400">
                              {sample.year ?? '-'}
                            </TableCell>
                            <TableCell className="text-zinc-400">
                              {sample.event_number ?? '-'}
                            </TableCell>
                            <TableCell>
                              {sample.is_valid ? (
                                <CheckCircle className="h-4 w-4 text-emerald-500" />
                              ) : (
                                <XCircle className="h-4 w-4 text-red-500" />
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* 연도별 탭 */}
        <TabsContent value="by-year">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                연도별 분포
              </CardTitle>
            </CardHeader>
            <CardContent>
              {summaryLoading ? (
                <div className="h-40 bg-zinc-800 rounded animate-pulse" />
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {Object.entries(summary?.by_year ?? {}).map(
                    ([year, count]) => (
                      <div
                        key={year}
                        className="bg-zinc-800 rounded-lg p-4 text-center"
                      >
                        <div className="text-lg font-bold text-zinc-200">
                          {year}
                        </div>
                        <div className="text-2xl font-bold text-emerald-500">
                          {count.toLocaleString()}
                        </div>
                        <div className="text-xs text-zinc-500">items</div>
                      </div>
                    )
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* 카테고리별 */}
          <Card className="bg-zinc-900 border-zinc-800 mt-4">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400">
                카테고리별 분포
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {Object.entries(summary?.by_category ?? {}).map(
                  ([category, count]) => (
                    <Badge
                      key={category}
                      variant="secondary"
                      className="text-sm py-1 px-3"
                    >
                      {category}: {count.toLocaleString()}
                    </Badge>
                  )
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 품질 이슈 탭 */}
        <TabsContent value="issues">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                제목 품질 이슈
                <Badge variant="destructive" className="ml-2">
                  {titleQuality?.issues_count ?? 0}건
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {qualityLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="h-12 bg-zinc-800 rounded animate-pulse"
                    />
                  ))}
                </div>
              ) : titleQuality?.issues_sample.length === 0 ? (
                <div className="text-center py-8 text-zinc-500">
                  <CheckCircle className="h-12 w-12 mx-auto mb-2 text-emerald-500" />
                  <p>품질 이슈가 없습니다!</p>
                </div>
              ) : (
                <>
                  {/* 제목 길이 분포 */}
                  <div className="mb-6">
                    <h4 className="text-sm text-zinc-400 mb-3">
                      제목 길이 분포
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {Object.entries(
                        titleQuality?.title_length_distribution ?? {}
                      ).map(([range, count]) => (
                        <div
                          key={range}
                          className="bg-zinc-800 rounded p-3 text-center"
                        >
                          <div className="text-xs text-zinc-500">{range}</div>
                          <div className="text-xl font-bold">{count}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 이슈 샘플 */}
                  <Table>
                    <TableHeader>
                      <TableRow className="border-zinc-800">
                        <TableHead className="text-zinc-400">ID</TableHead>
                        <TableHead className="text-zinc-400">Issue</TableHead>
                        <TableHead className="text-zinc-400">Title</TableHead>
                        <TableHead className="text-zinc-400">Project</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {titleQuality?.issues_sample.map((issue) => (
                        <TableRow
                          key={issue.id}
                          className="border-zinc-800 hover:bg-zinc-800/50"
                        >
                          <TableCell className="font-mono text-xs text-zinc-500">
                            {issue.id.slice(0, 8)}...
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                issue.issue === 'missing_title'
                                  ? 'destructive'
                                  : 'outline'
                              }
                            >
                              {issue.issue}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-zinc-400 max-w-[300px] truncate">
                            {issue.title || '-'}
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary">{issue.project}</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
