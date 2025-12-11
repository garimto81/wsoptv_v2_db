'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { AlertTriangle } from 'lucide-react'
import { useSyncErrors } from '@/hooks/use-sync'

export default function SyncErrorsPage() {
  const { data: syncErrors, isLoading } = useSyncErrors()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Sync Errors</h1>
          <p className="text-zinc-400 mt-1">
            Failed sync operations requiring attention
          </p>
        </div>
        <Badge
          variant={
            (syncErrors?.total_errors ?? 0) > 0 ? 'destructive' : 'secondary'
          }
          className="font-mono text-lg px-4 py-1"
        >
          {syncErrors?.total_errors ?? 0} errors
        </Badge>
      </div>

      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400">Error List</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="h-12 bg-zinc-800 rounded animate-pulse"
                />
              ))}
            </div>
          ) : (syncErrors?.errors.length ?? 0) === 0 ? (
            <div className="text-center py-12 text-zinc-500">
              <div className="text-4xl mb-4">All clear!</div>
              <div>No sync errors detected</div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-zinc-800">
                  <TableHead className="text-zinc-400">Sheet ID</TableHead>
                  <TableHead className="text-zinc-400">Entity Type</TableHead>
                  <TableHead className="text-zinc-400">Row</TableHead>
                  <TableHead className="text-zinc-400">Error Message</TableHead>
                  <TableHead className="text-zinc-400">Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {syncErrors?.errors.map((error) => (
                  <TableRow key={error.record_id} className="border-zinc-800">
                    <TableCell className="font-mono text-sm">
                      {error.sheet_id}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{error.entity_type}</Badge>
                    </TableCell>
                    <TableCell className="font-mono">
                      {error.row_number ?? '-'}
                    </TableCell>
                    <TableCell className="max-w-md">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-red-500 flex-shrink-0" />
                        <span className="text-red-400 text-sm truncate">
                          {error.error_message}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-zinc-500 text-sm">
                      {error.failed_at
                        ? new Date(error.failed_at).toLocaleString()
                        : '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
