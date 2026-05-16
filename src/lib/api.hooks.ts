/**
 * React Hooks for API Communication
 * Provides hooks for managing API calls with loading/error states
 */

import { useState, useCallback, useEffect } from 'react';
import { apiClient } from './api.client';
import type {
  DetectionResult,
  VideoDetectionResult,
  ModelInfo,
  DetectionStats,
  DetectionLog,
  ClassDistributionResponse,
  HealthStatus,
  DetectionOptions,
} from './api.types';

/**
 * Generic hook for handling async API calls
 */
export function useApiCall<T>(
  asyncFn: () => Promise<T>,
  dependencies: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await asyncFn();
      setData(result);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, dependencies);

  return { data, loading, error, execute };
}

/**
 * Hook for image detection
 */
export function useImageDetection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<DetectionResult | null>(null);

  const detect = useCallback(
    async (file: File, options: DetectionOptions = {}) => {
      setLoading(true);
      setError(null);
      setResult(null);

      try {
        // Validate file
        if (!file.type.startsWith('image/')) {
          throw new Error('Please select a valid image file');
        }

        const maxSize = (import.meta.env.VITE_MAX_IMAGE_SIZE ?? 50) * 1024 * 1024;
        if (file.size > maxSize) {
          throw new Error(`Image must be smaller than ${maxSize / 1024 / 1024}MB`);
        }

        const detectionResult = await apiClient.detectImage(file, options);
        setResult(detectionResult);
        return detectionResult;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { detect, loading, error, result };
}

/**
 * Hook for video detection
 */
export function useVideoDetection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<VideoDetectionResult | null>(null);
  const [progress, setProgress] = useState(0);

  const detect = useCallback(
    async (file: File, options: DetectionOptions & { frame_skip?: number } = {}) => {
      setLoading(true);
      setError(null);
      setResult(null);
      setProgress(0);

      try {
        // Validate file
        if (!file.type.startsWith('video/')) {
          throw new Error('Please select a valid video file');
        }

        const maxSize = (import.meta.env.VITE_MAX_VIDEO_SIZE ?? 500) * 1024 * 1024;
        if (file.size > maxSize) {
          throw new Error(`Video must be smaller than ${maxSize / 1024 / 1024}MB`);
        }

        // Simulate progress (backend processes the video)
        const progressInterval = setInterval(() => {
          setProgress((prev) => Math.min(prev + Math.random() * 30, 90));
        }, 500);

        const detectionResult = await apiClient.detectVideo(file, options);
        clearInterval(progressInterval);
        setProgress(100);
        setResult(detectionResult);
        return detectionResult;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { detect, loading, error, result, progress };
}

/**
 * Hook for model information
 */
export function useModelInfo() {
  const [data, setData] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchModelInfo = async () => {
      try {
        setLoading(true);
        const info = await apiClient.getModelInfo();
        setData(info);
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
      } finally {
        setLoading(false);
      }
    };

    fetchModelInfo();
  }, []);

  return { data, loading, error };
}

/**
 * Hook for detection statistics
 */
export function useDetectionStats(days: number = 7) {
  const [data, setData] = useState<DetectionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const stats = await apiClient.getStats(days);
      setData(stats);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    refresh();
  }, [days, refresh]);

  return { data, loading, error, refresh };
}

/**
 * Hook for detection logs
 */
export function useDetectionLogs(skip: number = 0, limit: number = 10) {
  const [data, setData] = useState<DetectionLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const logs = await apiClient.getDetectionLogs({ skip, limit });
      setData(logs);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [skip, limit]);

  useEffect(() => {
    refresh();
  }, [skip, limit, refresh]);

  return { data, loading, error, refresh };
}

/**
 * Hook for class distribution
 */
export function useClassDistribution(days: number = 7) {
  const [data, setData] = useState<ClassDistributionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const distribution = await apiClient.getClassDistribution(days);
      setData(distribution);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    refresh();
  }, [days, refresh]);

  return { data, loading, error, refresh };
}

/**
 * Hook for health status
 */
export function useHealthStatus() {
  const [data, setData] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isAvailable, setIsAvailable] = useState(false);

  const check = useCallback(async () => {
    try {
      setLoading(true);
      const status = await apiClient.getHealth();
      setData(status);
      setIsAvailable(true);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      setIsAvailable(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    check();
    const interval = setInterval(check, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, [check]);

  return { data, loading, error, isAvailable, check };
}
