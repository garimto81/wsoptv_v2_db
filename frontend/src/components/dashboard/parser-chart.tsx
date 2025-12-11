'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  Cell,
} from 'recharts'
import type { ParserStatsResponse } from '@/types/api'

interface ParserChartProps {
  data?: ParserStatsResponse
  loading?: boolean
}

const PARSER_COLORS: Record<string, string> = {
  WSOPBracelet: '#10b981',
  WSOPCircuit: '#059669',
  WSOPArchive: '#047857',
  HCL: '#3b82f6',
  GGMillions: '#8b5cf6',
  GOG: '#f59e0b',
  PAD: '#ec4899',
  MPP: '#14b8a6',
  Generic: '#6b7280',
  Unmatched: '#ef4444',
}

export function ParserChart({ data, loading }: ParserChartProps) {
  if (loading) {
    return (
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-300">
            Parser Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center">
            <div className="animate-pulse text-zinc-600">Loading...</div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const chartData =
    data?.by_parser
      .filter((p) => p.matched_count > 0)
      .sort((a, b) => b.matched_count - a.matched_count)
      .slice(0, 8) ?? []

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-zinc-300">
          Parser Statistics
        </CardTitle>
        <span className="text-sm text-zinc-500">
          {data?.parse_rate.toFixed(1)}% parsed
        </span>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ left: 80, right: 20 }}
          >
            <XAxis type="number" stroke="#52525b" fontSize={12} />
            <YAxis
              type="category"
              dataKey="parser_name"
              stroke="#52525b"
              fontSize={12}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#18181b',
                border: '1px solid #27272a',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#a1a1aa' }}
              formatter={(value: number, name: string, props) => [
                `${value.toLocaleString()} files (${props.payload.percentage.toFixed(
                  1
                )}%)`,
                'Count',
              ]}
            />
            <Bar dataKey="matched_count" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={PARSER_COLORS[entry.parser_name] ?? '#6b7280'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
