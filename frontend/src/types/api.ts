/**
 * API Response Types for Data Quality Dashboard
 * Based on backend Pydantic models
 */

// Common types
export type UUID = string
export type ISODatetime = string

// ==================== Quality Types ====================

export interface EntityStats {
  total: number
  linked: number
  unlinked: number
}

export interface VideoFileStats {
  total: number
  with_episode: number
  without_episode: number
}

export interface EpisodeStats {
  total: number
  with_video: number
  without_video: number
}

export interface HandClipStats {
  total: number
  with_video: number
  without_video: number
}

export interface LinkageStatsResponse {
  nas_files: EntityStats
  video_files: VideoFileStats
  episodes: EpisodeStats
  hand_clips: HandClipStats
  overall_linkage_rate: number
}

export interface ProblemSummaryResponse {
  unlinked_nas_files: number
  parsing_failed_files: number
  sync_errors: number
  orphan_hand_clips: number
  orphan_video_files: number
  orphan_episodes: number
  total_problems: number
}

export interface OrphanRecord {
  id: UUID
  name: string
  type: 'nas_file' | 'video_file' | 'hand_clip' | 'episode'
  reason: string
  created_at: ISODatetime
}

export interface OrphanListResponse {
  type: string
  total: number
  items: OrphanRecord[]
}

export interface ProjectLinkageResponse {
  project_id: UUID
  project_code: string
  project_name: string
  total_episodes: number
  linked_episodes: number
  linkage_rate: number
}

export interface BulkLinkRequest {
  source_type: 'nas_file' | 'video_file' | 'hand_clip'
  source_ids: UUID[]
  target_type: 'video_file' | 'episode'
  target_id: UUID
}

export interface BulkLinkResponse {
  success_count: number
  failed_count: number
  errors: string[]
}

// ==================== NAS Types ====================

export interface ParserStatItem {
  parser_name: string
  matched_count: number
  percentage: number
}

export interface ParserStatsResponse {
  total_files: number
  parsed_files: number
  unparsed_files: number
  parse_rate: number
  by_parser: ParserStatItem[]
}

export interface NASFileResponse {
  id: UUID
  file_path: string
  file_name: string
  file_extension?: string
  file_category: 'video' | 'metadata' | 'system' | 'archive' | 'other'
  file_size_bytes: number
  file_mtime?: ISODatetime
  is_hidden_file: boolean
  folder_id?: UUID
  video_file_id?: UUID
  created_at: ISODatetime
  updated_at: ISODatetime
}

export interface DuplicateFileGroup {
  base_name: string
  file_count: number
  total_size_bytes: number
  files: NASFileResponse[]
}

export interface DuplicatesResponse {
  total_groups: number
  total_duplicate_files: number
  groups: DuplicateFileGroup[]
}

export interface NASFileStats {
  total_files: number
  total_size_bytes: number
  video_count?: number
  metadata_count?: number
  other_count?: number
  linked_count: number
  unlinked_count: number
  by_category?: Record<string, number>
  by_extension?: Record<string, number>
}

// ==================== Sync Types ====================

export interface SyncErrorItem {
  record_id: UUID
  sheet_id: string
  entity_type: string
  error_message: string
  failed_at?: ISODatetime
  row_number?: number
}

export interface SyncErrorsResponse {
  total_errors: number
  errors: SyncErrorItem[]
}

export interface SyncRecord {
  id: UUID
  sheet_id: string
  entity_type: string
  sync_status: 'pending' | 'syncing' | 'completed' | 'failed'
  last_synced_at?: ISODatetime
  last_row_synced?: number
  total_rows?: number
  error_message?: string
}

export interface SyncSummary {
  total_records: number
  completed: number
  failed: number
  in_progress: number
  last_sync_at?: ISODatetime
}

// ==================== HandClip Types ====================

export interface HandClipLinkageStatsResponse {
  total_clips: number
  with_video_file: number
  with_episode: number
  video_only: number
  orphan_clips: number
  linkage_rate: number
}

// ==================== Catalog Build Types ====================

export interface BuildCatalogRequest {
  limit?: number
  skip_linked?: boolean
}

export interface BuildCatalogResponse {
  nas_files_processed: number
  projects_created: number
  seasons_created: number
  events_created: number
  episodes_created: number
  video_files_created: number
  links_created: number
  skipped: number
  errors: number
  error_messages: string[]
}
