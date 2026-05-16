/**
 * API Types and Interfaces
 * Defines all request/response structures for backend communication
 */

// Detection Results
export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface DetectedObject {
  bbox_x1: number;
  bbox_y1: number;
  bbox_x2: number;
  bbox_y2: number;
  label: string;
  confidence: number;
  class_id: number;
}

export interface DetectionResult {
  detection_id: number;
  total_objects: number;
  processing_ms: number;
  detected_objects: DetectedObject[];
  input_type: 'image' | 'video';
  filename: string;
  created_at: string;
  confidence_thresh: number;
  status: string;
}

export interface VideoDetectionResult {
  detection_id: number;
  total_objects: number;
  processing_ms: number;
  output_video: string;
  input_type: 'video';
  filename: string;
}

// Model Information
export interface ModelInfo {
  model_name: string;
  num_classes: number;
  class_names: string[];
  device: string;
  status: string;
}

// Statistics
export interface DetectionStats {
  total_detections: number;
  total_objects: number;
  average_confidence: number;
  most_common_class: string;
  processing_time_avg_ms: number;
}

// Detection Logs
export interface DetectionLog {
  detection_id: number;
  filename: string;
  input_type: 'image' | 'video';
  total_objects: number;
  processing_ms: number;
  created_at: string;
  confidence_thresh: number;
}

// Class Distribution
export interface ClassDistribution {
  [className: string]: number;
}

export interface ClassDistributionResponse {
  distribution: ClassDistribution;
  total_objects: number;
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export interface HealthStatus {
  api: string;
  model: string;
  database: string;
}

// Detection Request Options
export interface DetectionOptions {
  confidence_threshold?: number;
  iou_threshold?: number;
  model_id?: number;
}

// Pagination
export interface PaginationParams {
  skip?: number;
  limit?: number;
}
