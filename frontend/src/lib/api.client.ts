/**
 * API Client Service
 * Handles all backend communication with proper error handling
 */

import type {
  DetectionResult,
  VideoDetectionResult,
  ModelInfo,
  DetectionStats,
  DetectionLog,
  ClassDistributionResponse,
  HealthStatus,
  DetectionOptions,
  PaginationParams,
} from './api.types';

/**
 * API Client for backend communication
 */
class ApiClient {
  private baseUrl: string;
  private timeout: number = 30000; // 30 seconds default
  private videoTimeout: number = 300000; // 5 minutes for videos

  constructor(baseUrl?: string) {
    // Use environment variable or default to localhost
    this.baseUrl =
      baseUrl ||
      import.meta.env.VITE_API_URL ||
      'http://localhost:8000/api';
  }

  /**
   * Generic fetch wrapper with error handling
   */
  private async fetch<T>(
    endpoint: string,
    options: RequestInit & { timeout?: number } = {}
  ): Promise<T> {
    const { timeout = this.timeout, ...fetchOptions } = options;
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          'Content-Type':
            fetchOptions.headers instanceof Headers
              ? undefined
              : 'application/json',
          ...((fetchOptions.headers instanceof Headers)
            ? {}
            : fetchOptions.headers),
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: response.statusText,
        }));
        throw new Error(
          error.detail || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof TypeError) {
        throw new Error(
          'Cannot connect to backend. Make sure the API is running on http://localhost:8000'
        );
      }
      throw error;
    }
  }

  // ===== Health Endpoints =====

  /**
   * Check API health status
   */
  async getHealth(): Promise<HealthStatus> {
    return this.fetch<HealthStatus>('/health');
  }

  /**
   * Get system status
   */
  async getStatus(): Promise<HealthStatus> {
    return this.fetch<HealthStatus>('/health/status');
  }

  // ===== Detection Endpoints =====

  /**
   * Detect objects in an image
   */
  async detectImage(
    file: File,
    options: DetectionOptions = {}
  ): Promise<DetectionResult> {
    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams({
      confidence_threshold: String(options.confidence_threshold ?? 0.5),
      iou_threshold: String(options.iou_threshold ?? 0.45),
      model_id: String(options.model_id ?? 1),
    });

    return this.fetch<DetectionResult>(
      `/detect/image?${params.toString()}`,
      {
        method: 'POST',
        headers: {}, // Let browser set Content-Type for FormData
        body: formData,
      }
    );
  }

  /**
   * Detect objects in a video
   */
  async detectVideo(
    file: File,
    options: DetectionOptions & { frame_skip?: number } = {}
  ): Promise<VideoDetectionResult> {
    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams({
      confidence_threshold: String(options.confidence_threshold ?? 0.5),
      iou_threshold: String(options.iou_threshold ?? 0.45),
      frame_skip: String(options.frame_skip ?? 1),
      model_id: String(options.model_id ?? 1),
    });

    return this.fetch<VideoDetectionResult>(
      `/detect/video?${params.toString()}`,
      {
        method: 'POST',
        headers: {}, // Let browser set Content-Type for FormData
        body: formData,
        timeout: this.videoTimeout,
      }
    );
  }

  /**
   * Get available models
   */
  async getModels(): Promise<any[]> {
    return this.fetch<any[]>('/detect/models');
  }

  /**
   * Get model information
   */
  async getModelInfo(): Promise<ModelInfo> {
    return this.fetch<ModelInfo>('/detect/model-info');
  }

  // ===== Logs Endpoints =====

  /**
   * Get detection logs with pagination and filtering
   */
  async getDetectionLogs(
    params: PaginationParams & { input_type?: string } = {}
  ): Promise<DetectionLog[]> {
    const searchParams = new URLSearchParams();
    if (params.skip !== undefined) searchParams.append('skip', String(params.skip));
    if (params.limit !== undefined) searchParams.append('limit', String(params.limit));
    if (params.input_type) searchParams.append('input_type', params.input_type);

    return this.fetch<DetectionLog[]>(
      `/logs/detections?${searchParams.toString()}`
    );
  }

  /**
   * Get detection statistics
   */
  async getStats(days: number = 7): Promise<DetectionStats> {
    return this.fetch<DetectionStats>(
      `/logs/stats?days=${days}`
    );
  }

  /**
   * Get class distribution for chart visualization
   */
  async getClassDistribution(days: number = 7): Promise<ClassDistributionResponse> {
    return this.fetch<ClassDistributionResponse>(
      `/logs/class-distribution?days=${days}`
    );
  }

  /**
   * Export detection logs as CSV
   */
  async exportLogs(filters?: { input_type?: string; days?: number }): Promise<Blob> {
    const params = new URLSearchParams();
    if (filters?.input_type) params.append('input_type', filters.input_type);
    if (filters?.days) params.append('days', String(filters.days));

    const response = await fetch(
      `${this.baseUrl}/logs/export-csv?${params.toString()}`,
      {
        method: 'GET',
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to export logs: ${response.statusText}`);
    }

    return response.blob();
  }

  // ===== Utility Methods =====

  /**
   * Check if backend is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      await this.getHealth();
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get the full API URL for debugging
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Set custom timeout for requests
   */
  setTimeout(ms: number): void {
    this.timeout = ms;
  }

  /**
   * Download file from URL
   */
  downloadFile(url: string, filename: string): void {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();

// Export for custom instantiation if needed
export default ApiClient;
