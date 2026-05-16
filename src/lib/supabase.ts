/**
 * DEPRECATED: This file has been removed as part of removing Supabase dependency.
 * 
 * Migration Guide:
 * - Replace imports from './supabase' with './api.types'
 * - Use 'DetectedObject' from api.types instead of 'DetectionObject'
 * - All detection types are now defined in api.types.ts
 * - Backend communication is handled via api.client.ts
 * 
 * Example:
 *   OLD: import type { DetectionObject } from './supabase'
 *   NEW: import type { DetectedObject } from './api.types'
 */

throw new Error(
  'supabase.ts has been removed. '
  + 'Use api.types.ts instead for all type definitions. '
  + 'See file comments for migration guide.'
);
