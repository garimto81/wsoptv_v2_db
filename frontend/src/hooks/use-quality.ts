'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { qualityApi, catalogApi } from '@/lib/api'
import type { BulkLinkRequest, BuildCatalogRequest } from '@/types/api'

export const qualityKeys = {
  all: ['quality'] as const,
  linkageStats: () => [...qualityKeys.all, 'linkage-stats'] as const,
  problems: () => [...qualityKeys.all, 'problems'] as const,
  orphans: (type?: string) => [...qualityKeys.all, 'orphans', type] as const,
  projectLinkage: () => [...qualityKeys.all, 'project-linkage'] as const,
}

export function useLinkageStats() {
  return useQuery({
    queryKey: qualityKeys.linkageStats(),
    queryFn: qualityApi.getLinkageStats,
    refetchInterval: 5 * 60 * 1000, // 5 minutes
  })
}

export function useProblems() {
  return useQuery({
    queryKey: qualityKeys.problems(),
    queryFn: qualityApi.getProblems,
    refetchInterval: 60 * 1000, // 1 minute
  })
}

export function useOrphans(type?: string) {
  return useQuery({
    queryKey: qualityKeys.orphans(type),
    queryFn: () => qualityApi.getOrphans(type),
    staleTime: 5 * 60 * 1000,
  })
}

export function useProjectLinkage() {
  return useQuery({
    queryKey: qualityKeys.projectLinkage(),
    queryFn: qualityApi.getLinkageByProject,
    staleTime: 5 * 60 * 1000,
  })
}

export function useBulkLink() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: BulkLinkRequest) => qualityApi.bulkLink(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qualityKeys.all })
    },
  })
}

export function useBuildCatalog() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data?: BuildCatalogRequest) => qualityApi.buildCatalog(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qualityKeys.all })
    },
  })
}

// ==================== Catalog Validation Hooks ====================

export const catalogKeys = {
  all: ['catalog'] as const,
  summary: () => [...catalogKeys.all, 'summary'] as const,
  samples: (count?: number) => [...catalogKeys.all, 'samples', count] as const,
  titleQuality: () => [...catalogKeys.all, 'title-quality'] as const,
}

export function useCatalogSummary() {
  return useQuery({
    queryKey: catalogKeys.summary(),
    queryFn: catalogApi.getSummary,
    staleTime: 5 * 60 * 1000,
  })
}

export function useCatalogSamples(samplesPerParser = 5) {
  return useQuery({
    queryKey: catalogKeys.samples(samplesPerParser),
    queryFn: () => catalogApi.getSamples(samplesPerParser),
    staleTime: 5 * 60 * 1000,
  })
}

export function useTitleQuality(limit = 1000) {
  return useQuery({
    queryKey: catalogKeys.titleQuality(),
    queryFn: () => catalogApi.getTitleQuality(limit),
    staleTime: 5 * 60 * 1000,
  })
}
