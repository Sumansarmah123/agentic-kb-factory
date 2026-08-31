/**
 * API Client with Mock Data Fallback
 * Shows production-quality demo even without backend
 */

import type {
  CollectorConfig,
  ExtractionLog,
  HealingEvent,
  HealthStatus,
  DashboardMetrics,
} from '../types';

import {
  MOCK_COLLECTORS,
  MOCK_EXTRACTION_LOGS,
  MOCK_HEALING_EVENTS,
  MOCK_DASHBOARD_METRICS,
} from '../data/mockData';

const API_BASE = '/api';
const USE_MOCK_DATA = true; // Enable for demo - shows data even if backend is down

class APIClient {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      // Fallback to mock data for demo
      if (USE_MOCK_DATA) {
        console.log('Using mock data for:', endpoint);
        return this.getMockData<T>(endpoint);
      }
      throw error;
    }
  }

  private getMockData<T>(endpoint: string): T {
    if (endpoint.includes('/health')) {
      return { status: 'healthy', environment: 'demo', version: '1.0.0' } as T;
    }
    if (endpoint.includes('/collectors')) {
      return { collectors: MOCK_COLLECTORS, total: MOCK_COLLECTORS.length } as T;
    }
    if (endpoint.includes('/extraction-logs')) {
      return { logs: MOCK_EXTRACTION_LOGS, total: MOCK_EXTRACTION_LOGS.length } as T;
    }
    if (endpoint.includes('/healing-logs')) {
      return { events: MOCK_HEALING_EVENTS, total: MOCK_HEALING_EVENTS.length } as T;
    }
    return {} as T;
  }

  // Health Check
  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/health');
  }

  // Collectors
  async listCollectors(activeOnly = false): Promise<{ collectors: CollectorConfig[]; total: number }> {
    const url = activeOnly ? '/collectors?active_only=true' : '/collectors';
    return this.request(url);
  }

  async getCollector(id: string): Promise<CollectorConfig> {
    return this.request(`/collectors/${id}`);
  }

  async createCollector(data: Partial<CollectorConfig>): Promise<CollectorConfig> {
    return this.request('/collectors', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async triggerRun(_collectorId: string): Promise<{ job_id: string; status: string }> {
    // Simulate trigger for demo
    return Promise.resolve({
      job_id: `job_${Date.now()}`,
      status: 'running'
    });
  }

  // Logs
  async getExtractionLogs(
    collectorId?: string,
    limit = 100
  ): Promise<{ logs: ExtractionLog[]; total: number }> {
    const params = new URLSearchParams();
    if (collectorId) params.append('collector_id', collectorId);
    params.append('limit', limit.toString());
    
    return this.request(`/extraction-logs?${params.toString()}`);
  }

  async getHealingLogs(
    collectorId?: string,
    limit = 100
  ): Promise<{ events: HealingEvent[]; total: number }> {
    const params = new URLSearchParams();
    if (collectorId) params.append('collector_id', collectorId);
    params.append('limit', limit.toString());
    
    return this.request(`/healing-logs?${params.toString()}`);
  }

  // Metrics (computed client-side)
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    try {
      const [{ collectors }, { logs }, { events }] = await Promise.all([
        this.listCollectors(),
        this.getExtractionLogs(undefined, 1000),
        this.getHealingLogs(undefined, 1000),
      ]);

      const activeCollectors = collectors.filter(c => c.is_active).length;
      const totalExtractions = logs.length;
      const successfulExtractions = logs.filter(l => l.status === 'success').length;
      const successRate = totalExtractions > 0 
        ? (successfulExtractions / totalExtractions) * 100 
        : 0;

      return {
        total_collectors: collectors.length,
        active_collectors: activeCollectors,
        total_extractions: totalExtractions,
        healing_events: events.length,
        success_rate: Math.round(successRate),
      };
    } catch {
      // Return mock metrics if API fails
      return MOCK_DASHBOARD_METRICS;
    }
  }
}

export const apiClient = new APIClient();
