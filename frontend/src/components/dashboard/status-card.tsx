'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { type LucideIcon, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatusCardProps {
  title: string
  icon: LucideIcon
  href?: string
  items: {
    label: string
    value: number | string
    status?: 'success' | 'warning' | 'error' | 'neutral'
  }[]
  progress?: {
    value: number
    label: string
  }
  loading?: boolean
}

export function StatusCard({
  title,
  icon: Icon,
  href,
  items,
  progress,
  loading,
}: StatusCardProps) {
  const content = (
    <Card className="bg-zinc-900 border-zinc-800 hover:border-zinc-700 transition-colors">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-zinc-300">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-zinc-500" />
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <div className="h-6 bg-zinc-800 rounded animate-pulse" />
            <div className="h-4 bg-zinc-800 rounded w-2/3 animate-pulse" />
          </div>
        ) : (
          <div className="space-y-3">
            <div className="space-y-1">
              {items.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-zinc-400">{item.label}</span>
                  <Badge
                    variant="secondary"
                    className={cn(
                      'font-mono',
                      item.status === 'success' &&
                        'bg-emerald-500/10 text-emerald-500',
                      item.status === 'warning' &&
                        'bg-amber-500/10 text-amber-500',
                      item.status === 'error' && 'bg-red-500/10 text-red-500',
                      item.status === 'neutral' &&
                        'bg-zinc-700 text-zinc-300'
                    )}
                  >
                    {item.value}
                  </Badge>
                </div>
              ))}
            </div>

            {progress && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-zinc-500">
                  <span>{progress.label}</span>
                  <span>{progress.value.toFixed(1)}%</span>
                </div>
                <Progress
                  value={progress.value}
                  className="h-1.5 bg-zinc-800"
                />
              </div>
            )}

            {href && (
              <div className="flex items-center justify-end text-xs text-zinc-500 hover:text-emerald-500 transition-colors">
                View details <ArrowRight className="h-3 w-3 ml-1" />
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )

  if (href) {
    return <Link href={href}>{content}</Link>
  }

  return content
}
