/**
 * API Client for Data Quality Dashboard
 */

import type {
  LinkageStatsResponse,
  ProblemSummaryResponse,
  OrphanListResponse,
  ProjectLinkageResponse,
  BulkLinkRequest,
  BulkLinkResponse,
  ParserStatsResponse,
  DuplicatesResponse,
  NASFileStats,
  SyncErrorsResponse,
  SyncSummary,
  SyncRecord,
  HandClipLinkageStatsResponse,
  BuildCatalogRequest,
  BuildCatalogResponse,
} from '@/types/api'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004'

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// ==================== Quality API ====================

export const qualityApi = {
  getLinkageStats: () =>
    fetchApi<LinkageStatsResponse>('/api/v1/quality/linkage-stats'),

  getProblems: () =>
    fetchApi<ProblemSummaryResponse>('/api/v1/quality/problems'),

  getOrphans: (type?: string, skip = 0, limit = 100) => {
    const params = new URLSearchParams()
    if (type) params.append('type', type)
    params.append('skip', String(skip))
    params.append('limit', String(limit))
    return fetchApi<OrphanListResponse>(`/api/v1/quality/orphans?${params}`)
  },

  getLinkageByProject: () =>
    fetchApi<ProjectLinkageResponse[]>('/api/v1/quality/linkage-by-project'),

  bulkLink: (data: BulkLinkRequest) =>
    fetchApi<BulkLinkResponse>('/api/v1/quality/bulk-link', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  buildCatalog: (data?: BuildCatalogRequest) =>
    fetchApi<BuildCatalogResponse>('/api/v1/quality/build-catalog', {
      method: 'POST',
      body: JSON.stringify(data || { limit: 10000, skip_linked: true }),
    }),
}

// ==================== NAS API ====================

export const nasApi = {
  getStats: () =>
    fetchApi<NASFileStats>('/api/v1/nas/files/stats'),

  getParserStats: (limit = 10000) =>
    fetchApi<ParserStatsResponse>(`/api/v1/nas/parser-stats?limit=${limit}`),

  getDuplicates: (limit = 50) =>
    fetchApi<DuplicatesResponse>(`/api/v1/nas/duplicates?limit=${limit}`),
}

// ==================== Sync API ====================

export const syncApi = {
  getSummary: () =>
    fetchApi<SyncSummary>('/api/v1/sync/summary'),

  getRecords: () =>
    fetchApi<SyncRecord[]>('/api/v1/sync/records'),

  getErrors: () =>
    fetchApi<SyncErrorsResponse>('/api/v1/sync/errors'),
}

// ==================== HandClip API ====================

export const handClipsApi = {
  getLinkageStats: () =>
    fetchApi<HandClipLinkageStatsResponse>('/api/v1/hand-clips/linkage-stats'),
}
