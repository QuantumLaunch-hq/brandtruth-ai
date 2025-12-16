/**
 * useWorkflowProgress - SSE hook for real-time Temporal workflow progress
 *
 * This hook connects to the backend SSE endpoint and streams real-time
 * progress updates from the Temporal workflow.
 *
 * Features:
 * - Automatic reconnection on connection loss
 * - Typed progress events
 * - Cleanup on unmount
 * - Error handling with fallback
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export type WorkflowStage =
  | 'pending'
  | 'extracting'
  | 'generating'
  | 'matching'
  | 'composing'
  | 'scoring'
  | 'awaiting_approval'
  | 'approved'
  | 'completed'
  | 'failed';

export interface WorkflowProgress {
  workflow_id: string;
  stage: WorkflowStage;
  progress_percent: number;
  message: string;
  error?: string;
}

export interface UseWorkflowProgressOptions {
  /** API base URL */
  apiUrl?: string;
  /** Callback when progress updates */
  onProgress?: (progress: WorkflowProgress) => void;
  /** Callback when workflow completes */
  onComplete?: (progress: WorkflowProgress) => void;
  /** Callback on error */
  onError?: (error: string) => void;
  /** Auto-reconnect on connection loss */
  autoReconnect?: boolean;
  /** Max reconnection attempts */
  maxReconnectAttempts?: number;
}

export interface UseWorkflowProgressReturn {
  /** Current progress state */
  progress: WorkflowProgress | null;
  /** Whether connected to SSE stream */
  isConnected: boolean;
  /** Whether workflow is complete */
  isComplete: boolean;
  /** Error message if any */
  error: string | null;
  /** Start streaming for a workflow */
  startStreaming: (workflowId: string) => void;
  /** Stop streaming */
  stopStreaming: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useWorkflowProgress(
  options: UseWorkflowProgressOptions = {}
): UseWorkflowProgressReturn {
  const {
    apiUrl = API_BASE,
    onProgress,
    onComplete,
    onError,
    autoReconnect = true,
    maxReconnectAttempts = 3,
  } = options;

  const [progress, setProgress] = useState<WorkflowProgress | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const workflowIdRef = useRef<string | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const stopStreaming = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsConnected(false);
    workflowIdRef.current = null;
    reconnectAttemptsRef.current = 0;
  }, []);

  const startStreaming = useCallback(
    (workflowId: string) => {
      // Close existing connection
      stopStreaming();

      workflowIdRef.current = workflowId;
      setError(null);
      setIsComplete(false);
      setProgress(null);

      const url = `${apiUrl}/workflow/stream/${workflowId}`;

      try {
        const eventSource = new EventSource(url);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
          setIsConnected(true);
          setError(null);
          reconnectAttemptsRef.current = 0;
        };

        eventSource.addEventListener('progress', (event) => {
          try {
            const data = JSON.parse(event.data) as WorkflowProgress;
            setProgress(data);
            onProgress?.(data);
          } catch (e) {
            console.error('Failed to parse progress event:', e);
          }
        });

        eventSource.addEventListener('complete', (event) => {
          try {
            const data = JSON.parse(event.data) as WorkflowProgress;
            setProgress(data);
            setIsComplete(true);
            setIsConnected(false);
            onComplete?.(data);
            eventSource.close();
          } catch (e) {
            console.error('Failed to parse complete event:', e);
          }
        });

        eventSource.addEventListener('error', (event) => {
          try {
            const data = JSON.parse((event as MessageEvent).data);
            const errorMsg = data.error || 'Unknown error';
            setError(errorMsg);
            onError?.(errorMsg);
          } catch {
            // Connection error, not a message error
            if (eventSource.readyState === EventSource.CLOSED) {
              setIsConnected(false);

              // Auto-reconnect logic
              if (
                autoReconnect &&
                reconnectAttemptsRef.current < maxReconnectAttempts &&
                workflowIdRef.current
              ) {
                reconnectAttemptsRef.current++;
                setTimeout(() => {
                  if (workflowIdRef.current) {
                    startStreaming(workflowIdRef.current);
                  }
                }, 1000 * reconnectAttemptsRef.current);
              }
            }
          }
        });

        eventSource.addEventListener('timeout', () => {
          setError('Stream timeout');
          setIsConnected(false);
          eventSource.close();
        });

        // Generic message handler for backwards compatibility
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.stage) {
              setProgress(data as WorkflowProgress);
              onProgress?.(data as WorkflowProgress);
            }
          } catch (e) {
            console.error('Failed to parse message:', e);
          }
        };

        eventSource.onerror = () => {
          if (eventSource.readyState === EventSource.CLOSED) {
            setIsConnected(false);
          }
        };
      } catch (e) {
        const errorMsg = e instanceof Error ? e.message : 'Failed to connect';
        setError(errorMsg);
        onError?.(errorMsg);
      }
    },
    [apiUrl, onProgress, onComplete, onError, autoReconnect, maxReconnectAttempts, stopStreaming]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStreaming();
    };
  }, [stopStreaming]);

  return {
    progress,
    isConnected,
    isComplete,
    error,
    startStreaming,
    stopStreaming,
  };
}

/**
 * Helper to convert workflow stage to user-friendly label
 */
export function getStageLabel(stage: WorkflowStage): string {
  const labels: Record<WorkflowStage, string> = {
    pending: 'Starting...',
    extracting: 'Extracting brand',
    generating: 'Generating copy',
    matching: 'Matching images',
    composing: 'Composing ads',
    scoring: 'Scoring performance',
    awaiting_approval: 'Ready for review',
    approved: 'Approved',
    completed: 'Complete',
    failed: 'Failed',
  };
  return labels[stage] || stage;
}

/**
 * Helper to check if workflow is in a terminal state
 */
export function isTerminalStage(stage: WorkflowStage): boolean {
  return ['completed', 'failed', 'approved'].includes(stage);
}
