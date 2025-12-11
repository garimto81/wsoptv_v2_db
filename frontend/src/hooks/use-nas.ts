'use client'

import { useQuery } from '@tanstack/react-query'
import { nasApi } from '@/lib/api'

export const nasKeys = {
  all: ['nas'] as const,
  stats: () => [...nasKeys.all, 'stats'] as const,
  parserStats: () => [...nasKeys.all, 'parser-stats'] as const,
  duplicates: () => [...nasKeys.all, 'duplicates'] as const,
}

export function useNASStats() {
  return useQuery({
    queryKey: nasKeys.stats(),
    queryFn: nasApi.getStats,
    refetchInterval: 5 * 60 * 1000, // 5 minutes
  })
}

export function useParserStats() {
  return useQuery({
    queryKey: nasKeys.parserStats(),
    queryFn: () => nasApi.getParserStats(),
    staleTime: 5 * 60 * 1000,
  })
}

export function useDuplicates(limit = 50) {
  return useQuery({
    queryKey: [...nasKeys.duplicates(), limit],
    queryFn: () => nasApi.getDuplicates(limit),
    staleTime: 10 * 60 * 1000,
  })
}
