import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// Queued pipeline request
export interface QueuedPipeline {
  id: string;
  url: string;
  num_variants: number;
  platform: string;
  queuedAt: string;
  status: 'queued' | 'retrying' | 'started' | 'failed';
  retryCount: number;
  lastError?: string;
}

interface PipelineQueueState {
  // Queue state
  queue: QueuedPipeline[];
  isTemporalAvailable: boolean;
  lastHealthCheck: string | null;
  isPolling: boolean;

  // Actions
  addToQueue: (pipeline: Omit<QueuedPipeline, 'id' | 'queuedAt' | 'status' | 'retryCount'>) => string;
  removeFromQueue: (id: string) => void;
  updateStatus: (id: string, status: QueuedPipeline['status'], error?: string) => void;
  clearQueue: () => void;
  setTemporalAvailable: (available: boolean) => void;
  setPolling: (polling: boolean) => void;
  getNextQueued: () => QueuedPipeline | undefined;
  incrementRetry: (id: string) => void;
}

const MAX_RETRIES = 3;

export const usePipelineQueueStore = create<PipelineQueueState>()(
  persist(
    (set, get) => ({
      // Initial state
      queue: [],
      isTemporalAvailable: true, // Assume available until proven otherwise
      lastHealthCheck: null,
      isPolling: false,

      // Add a pipeline to the queue
      addToQueue: (pipeline) => {
        const id = `queue-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const queuedPipeline: QueuedPipeline = {
          ...pipeline,
          id,
          queuedAt: new Date().toISOString(),
          status: 'queued',
          retryCount: 0,
        };

        set((state) => ({
          queue: [...state.queue, queuedPipeline],
        }));

        return id;
      },

      // Remove a pipeline from the queue
      removeFromQueue: (id) => {
        set((state) => ({
          queue: state.queue.filter((p) => p.id !== id),
        }));
      },

      // Update status of a queued pipeline
      updateStatus: (id, status, error) => {
        set((state) => ({
          queue: state.queue.map((p) =>
            p.id === id
              ? { ...p, status, lastError: error || p.lastError }
              : p
          ),
        }));
      },

      // Clear all queued pipelines
      clearQueue: () => {
        set({ queue: [] });
      },

      // Set Temporal availability
      setTemporalAvailable: (available) => {
        set({
          isTemporalAvailable: available,
          lastHealthCheck: new Date().toISOString(),
        });
      },

      // Set polling state
      setPolling: (polling) => {
        set({ isPolling: polling });
      },

      // Get next queued item ready for retry
      getNextQueued: () => {
        const { queue } = get();
        return queue.find(
          (p) => p.status === 'queued' && p.retryCount < MAX_RETRIES
        );
      },

      // Increment retry count
      incrementRetry: (id) => {
        set((state) => ({
          queue: state.queue.map((p) =>
            p.id === id
              ? {
                  ...p,
                  retryCount: p.retryCount + 1,
                  status: p.retryCount + 1 >= MAX_RETRIES ? 'failed' : 'queued',
                }
              : p
          ),
        }));
      },
    }),
    {
      name: 'brandtruth-pipeline-queue',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        queue: state.queue,
        // Don't persist polling/availability state - check fresh on load
      }),
    }
  )
);

// Selector for queue count
export const useQueueCount = () =>
  usePipelineQueueStore((state) => state.queue.filter((p) => p.status === 'queued').length);

// Selector for failed count
export const useFailedCount = () =>
  usePipelineQueueStore((state) => state.queue.filter((p) => p.status === 'failed').length);
