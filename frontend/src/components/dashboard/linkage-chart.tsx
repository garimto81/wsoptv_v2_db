'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts'
import type { LinkageStatsResponse } from '@/types/api'

interface LinkageChartProps {
  data?: LinkageStatsResponse
  loading?: boolean
}

const COLORS = {
  linked: '#10b981', // emerald-500
  unlinked: '#ef4444', // red-500
}

export function LinkageChart({ data, loading }: LinkageChartProps) {
  if (loading) {
    return (
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-300">
            Linkage Distribution
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center">
            <div className="animate-pulse text-zinc-600">Loading...</div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const chartData = [
    { name: 'Linked', value: data?.nas_files.linked ?? 0 },
    { name: 'Unlinked', value: data?.nas_files.unlinked ?? 0 },
  ]

  const total = chartData.reduce((sum, item) => sum + item.value, 0)
  const linkageRate = data?.overall_linkage_rate ?? 0

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-zinc-300">
          Linkage Distribution
        </CardTitle>
        <span className="text-2xl font-bold text-emerald-500">
          {linkageRate.toFixed(1)}%
        </span>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={70}
              paddingAngle={2}
              dataKey="value"
              strokeWidth={0}
            >
              <Cell fill={COLORS.linked} />
              <Cell fill={COLORS.unlinked} />
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#18181b',
                border: '1px solid #27272a',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#a1a1aa' }}
              formatter={(value: number) => [
                `${value.toLocaleString()} (${((value / total) * 100).toFixed(
                  1
                )}%)`,
              ]}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value) => (
                <span className="text-zinc-400 text-sm">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
