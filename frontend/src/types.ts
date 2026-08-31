/**
 * TypeScript types for Agentic KB Factory
 */

export interface FieldSelector {
  name: string;
  css_selector: string;
  extraction_type: 'text' | 'attribute' | 'html';
  attribute_name?: string;
}

export interface CollectorConfig {
  id: string;
  name: string;
  target_url: string;
  description?: string;
  selectors: FieldSelector[];
  schedule_cron?: string;
  is_active: boolean;
  status: 'healthy' | 'warning' | 'error';
  created_at: string;
  updated_at: string;
  last_run_at?: string;
  last_success_at?: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
}

export interface ExtractionLog {
  id: string;
  collector_id: string;
  timestamp: string;
  status: 'success' | 'partial' | 'failed';
  items_extracted: number;
  fields_extracted: number;
  duration_ms: number;
  error_message?: string;
}

export interface HealingEvent {
  id: string;
  collector_id: string;
  timestamp: string;
  field_name: string;
  old_selector: string;
  new_selector: string;
  confidence_score: number;
  status: 'success' | 'failed';
  reasoning: string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  app_name: string;
  version: string;
  gcp_connected: boolean;
  firestore_connected: boolean;
  gemini_connected: boolean;
}

export interface DashboardMetrics {
  total_collectors: number;
  active_collectors: number;
  total_extractions: number;
  healing_events: number;
  success_rate: number;
}
