/**
 * useWorkflow - Hook for managing Temporal workflow lifecycle
 *
 * This hook provides functions for:
 * - Starting a new workflow (with queue fallback if Temporal unavailable)
 * - Querying workflow progress
 * - Getting workflow results
 * - Approving/rejecting variants
 * - Cancelling workflows
 * - Background health polling and auto-retry of queued items
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { usePipelineQueueStore } from '@/stores/pipeline-queue';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface WorkflowConfig {
  url: string;
  num_variants?: number;
  platform?: string;
  user_id?: string;
  campaign_name?: string;
}

export interface WorkflowStartResponse {
  workflow_id: string;
  status: string;
  message: string;
}

export interface WorkflowProgressResponse {
  workflow_id: string;
  stage: string;
  progress_percent: number;
  message: string;
  error?: string;
}

export interface BrandProfile {
  brand_name: string;
  tagline: string;
  industry: string;
  value_propositions: string[];
  claims: Array<{ claim: string; source: string; risk_level: string }>;
  confidence_score: number;
}

export interface CopyVariant {
  id: string;
  headline: string;
  primary_text: string;
  cta: string;
  angle: string;
  emotion: string;
  quality_score: number;
}

export interface PerformanceScore {
  variant_id: string;
  score: number;
  confidence: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

export interface WorkflowResult {
  workflow_id: string;
  stage: string;
  config: WorkflowConfig;
  brand_profile?: BrandProfile;
  copy_variants?: {
    variants: CopyVariant[];
    generation_time_ms: number;
  };
  image_matches?: Record<string, {
    image_url: string;
    relevance_score: number;
    photographer?: string;
    photographer_url?: string;
  }>;
  composed_ads?: {
    ads: Array<{
      id: string;
      copy_variant_id: string;
      headline: string;
      primary_text: string;
      cta: string;
      assets: Array<{
        format: string;
        file_path: string;
        width: number;
        height: number;
      }>;
    }>;
  };
  performance_scores?: {
    scores: PerformanceScore[];
  };
  approved_variant_ids?: string[];
  error?: string;
  duration_ms: number;
}

export interface UseWorkflowReturn {
  /** Start a new workflow */
  startWorkflow: (config: WorkflowConfig) => Promise<string | null>;
  /** Get workflow progress */
  getProgress: (workflowId: string) => Promise<WorkflowProgressResponse | null>;
  /** Get workflow result */
  getResult: (workflowId: string) => Promise<WorkflowResult | null>;
  /** Approve variants */
  approveVariants: (workflowId: string, variantIds: string[]) => Promise<boolean>;
  /** Cancel workflow */
  cancelWorkflow: (workflowId: string) => Promise<boolean>;
  /** Check if Temporal is available */
  checkHealth: () => Promise<boolean>;
  /** Loading state */
  isLoading: boolean;
  /** Error state */
  error: string | null;
}

export function useWorkflow(): UseWorkflowReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const retryingRef = useRef(false);

  // Get queue store actions
  const {
    addToQueue,
    updateStatus,
    removeFromQueue,
    getNextQueued,
    incrementRetry,
    setTemporalAvailable,
    setPolling,
    isTemporalAvailable,
  } = usePipelineQueueStore();

  // Check Temporal health
  const checkHealth = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/workflow/health`);
      if (!response.ok) {
        setTemporalAvailable(false);
        return false;
      }

      const data = await response.json();
      const available = data.temporal_available === true;
      setTemporalAvailable(available);
      return available;
    } catch {
      setTemporalAvailable(false);
      return false;
    }
  }, [setTemporalAvailable]);

  // Start workflow directly (internal use)
  const startWorkflowDirect = useCallback(async (config: WorkflowConfig): Promise<string | null> => {
    const response = await fetch(`${API_BASE}/workflow/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: config.url,
        num_variants: config.num_variants || 5,
        platform: config.platform || 'meta',
        user_id: config.user_id || null,
        campaign_name: config.campaign_name || null,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to start workflow: ${response.status}`);
    }

    const data: WorkflowStartResponse = await response.json();
    return data.workflow_id;
  }, []);

  // Process queued items when Temporal becomes available
  const processQueue = useCallback(async () => {
    if (retryingRef.current) return;
    retryingRef.current = true;
    setPolling(true);

    try {
      let nextItem = getNextQueued();
      while (nextItem) {
        updateStatus(nextItem.id, 'retrying');

        try {
          const workflowId = await startWorkflowDirect({
            url: nextItem.url,
            num_variants: nextItem.num_variants,
            platform: nextItem.platform,
          });

          if (workflowId) {
            updateStatus(nextItem.id, 'started');
            // Remove from queue after short delay to show "started" state
            setTimeout(() => removeFromQueue(nextItem!.id), 2000);
          } else {
            incrementRetry(nextItem.id);
          }
        } catch (e) {
          const errorMsg = e instanceof Error ? e.message : 'Failed to start workflow';
          incrementRetry(nextItem.id);
          updateStatus(nextItem.id, 'queued', errorMsg);
        }

        // Get next item
        nextItem = getNextQueued();
      }
    } finally {
      retryingRef.current = false;
      setPolling(false);
    }
  }, [getNextQueued, updateStatus, removeFromQueue, incrementRetry, startWorkflowDirect, setPolling]);

  // Background health polling and auto-retry
  useEffect(() => {
    const poll = async () => {
      const available = await checkHealth();
      if (available) {
        await processQueue();
      }
    };

    // Initial check
    poll();

    // Poll every 30 seconds
    pollingRef.current = setInterval(poll, 30000);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [checkHealth, processQueue]);

  // Start workflow with queue fallback
  const startWorkflow = useCallback(async (config: WorkflowConfig): Promise<string | null> => {
    setIsLoading(true);
    setError(null);

    try {
      // First check if Temporal is available
      const available = await checkHealth();

      if (!available) {
        // Queue the request for later
        const queueId = addToQueue({
          url: config.url,
          num_variants: config.num_variants || 5,
          platform: config.platform || 'meta',
        });
        setError('Temporal service unavailable. Request queued for automatic retry.');
        return queueId; // Return queue ID as a temporary identifier
      }

      // Temporal is available, start workflow directly
      return await startWorkflowDirect(config);
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Failed to start workflow';

      // If it looks like a connection error, queue it
      if (errorMsg.includes('fetch') || errorMsg.includes('network') || errorMsg.includes('ECONNREFUSED')) {
        const queueId = addToQueue({
          url: config.url,
          num_variants: config.num_variants || 5,
          platform: config.platform || 'meta',
        });
        setError('Connection failed. Request queued for automatic retry.');
        return queueId;
      }

      setError(errorMsg);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [checkHealth, addToQueue, startWorkflowDirect]);

  const getProgress = useCallback(
    async (workflowId: string): Promise<WorkflowProgressResponse | null> => {
      try {
        const response = await fetch(`${API_BASE}/workflow/progress/${workflowId}`);

        if (!response.ok) {
          if (response.status === 404) {
            return null;
          }
          throw new Error(`Failed to get progress: ${response.status}`);
        }

        return await response.json();
      } catch (e) {
        console.error('Failed to get workflow progress:', e);
        return null;
      }
    },
    []
  );

  const getResult = useCallback(async (workflowId: string): Promise<WorkflowResult | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/workflow/result/${workflowId}`);

      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to get result: ${response.status}`);
      }

      return await response.json();
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Failed to get result';
      setError(errorMsg);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const approveVariants = useCallback(
    async (workflowId: string, variantIds: string[]): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE}/workflow/approve/${workflowId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ variant_ids: variantIds }),
        });

        if (!response.ok) {
          throw new Error(`Failed to approve variants: ${response.status}`);
        }

        return true;
      } catch (e) {
        const errorMsg = e instanceof Error ? e.message : 'Failed to approve variants';
        setError(errorMsg);
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const cancelWorkflow = useCallback(async (workflowId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/workflow/cancel/${workflowId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to cancel workflow: ${response.status}`);
      }

      return true;
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Failed to cancel workflow';
      setError(errorMsg);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    startWorkflow,
    getProgress,
    getResult,
    approveVariants,
    cancelWorkflow,
    checkHealth,
    isLoading,
    error,
  };
}
