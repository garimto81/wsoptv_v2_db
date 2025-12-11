'use client'

import { useQuery } from '@tanstack/react-query'
import { syncApi, handClipsApi } from '@/lib/api'

export const syncKeys = {
  all: ['sync'] as const,
  summary: () => [...syncKeys.all, 'summary'] as const,
  records: () => [...syncKeys.all, 'records'] as const,
  errors: () => [...syncKeys.all, 'errors'] as const,
}

export const handClipKeys = {
  all: ['hand-clips'] as const,
  linkageStats: () => [...handClipKeys.all, 'linkage-stats'] as const,
}

export function useSyncSummary() {
  return useQuery({
    queryKey: syncKeys.summary(),
    queryFn: syncApi.getSummary,
    refetchInterval: 60 * 1000, // 1 minute
  })
}

export function useSyncRecords() {
  return useQuery({
    queryKey: syncKeys.records(),
    queryFn: syncApi.getRecords,
    staleTime: 60 * 1000,
  })
}

export function useSyncErrors() {
  return useQuery({
    queryKey: syncKeys.errors(),
    queryFn: syncApi.getErrors,
    refetchInterval: 60 * 1000,
  })
}

export function useHandClipLinkageStats() {
  return useQuery({
    queryKey: handClipKeys.linkageStats(),
    queryFn: handClipsApi.getLinkageStats,
    refetchInterval: 5 * 60 * 1000,
  })
}
