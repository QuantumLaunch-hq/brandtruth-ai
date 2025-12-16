'use client';

import { Clock, RefreshCw, Trash2, AlertTriangle, CheckCircle } from 'lucide-react';
import { usePipelineQueueStore, useQueueCount, useFailedCount, type QueuedPipeline } from '@/stores/pipeline-queue';

interface QueueStatusProps {
  className?: string;
  compact?: boolean;
  onRetryAll?: () => void;
}

export function QueueStatus({ className = '', compact = false, onRetryAll }: QueueStatusProps) {
  const queueCount = useQueueCount();
  const failedCount = useFailedCount();
  const { queue, clearQueue, isTemporalAvailable, isPolling } = usePipelineQueueStore();

  // Don't show if queue is empty and no failed items
  if (queueCount === 0 && failedCount === 0) {
    return null;
  }

  // Compact badge mode
  if (compact) {
    return (
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
          failedCount > 0
            ? 'bg-red-500/10 text-red-400 border border-red-500/30'
            : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
        } ${className}`}
      >
        {isPolling ? (
          <RefreshCw className="w-3 h-3 animate-spin" />
        ) : (
          <Clock className="w-3 h-3" />
        )}
        {queueCount > 0 && `${queueCount} queued`}
        {queueCount > 0 && failedCount > 0 && ' · '}
        {failedCount > 0 && `${failedCount} failed`}
      </div>
    );
  }

  // Full banner mode
  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-lg ${
        failedCount > 0
          ? 'bg-red-500/10 border border-red-500/30'
          : 'bg-yellow-500/10 border border-yellow-500/30'
      } ${className}`}
    >
      {isPolling ? (
        <RefreshCw className="w-5 h-5 text-yellow-400 animate-spin flex-shrink-0" />
      ) : failedCount > 0 ? (
        <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
      ) : (
        <Clock className="w-5 h-5 text-yellow-400 flex-shrink-0" />
      )}

      <div className="flex-1">
        <p className="text-sm font-medium text-white">
          {queueCount > 0 && (
            <>
              {queueCount} pipeline{queueCount > 1 ? 's' : ''} queued
              {isPolling && ' - retrying...'}
              {!isPolling && !isTemporalAvailable && ' - waiting for service'}
            </>
          )}
          {queueCount > 0 && failedCount > 0 && ' · '}
          {failedCount > 0 && (
            <span className="text-red-400">
              {failedCount} failed (max retries reached)
            </span>
          )}
        </p>
        <p className="text-xs text-zinc-400 mt-0.5">
          {isTemporalAvailable
            ? 'Service available - processing queue'
            : 'Will start automatically when Temporal service is available'}
        </p>
      </div>

      <div className="flex items-center gap-2">
        {onRetryAll && queueCount > 0 && (
          <button
            onClick={onRetryAll}
            className="px-3 py-1.5 text-xs font-medium bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded-md transition"
          >
            Retry Now
          </button>
        )}
        {(queueCount > 0 || failedCount > 0) && (
          <button
            onClick={clearQueue}
            className="p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-700 rounded-md transition"
            title="Clear queue"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

// Individual queue item component for detailed view
export function QueueItem({ item }: { item: QueuedPipeline }) {
  const { removeFromQueue } = usePipelineQueueStore();

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-zinc-800/50 rounded-lg">
      {item.status === 'queued' && <Clock className="w-4 h-4 text-yellow-400" />}
      {item.status === 'retrying' && <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />}
      {item.status === 'started' && <CheckCircle className="w-4 h-4 text-green-400" />}
      {item.status === 'failed' && <AlertTriangle className="w-4 h-4 text-red-400" />}

      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate">{item.url}</p>
        <p className="text-xs text-zinc-400">
          {item.status === 'queued' && `Queued ${new Date(item.queuedAt).toLocaleTimeString()}`}
          {item.status === 'retrying' && `Retrying (attempt ${item.retryCount + 1}/3)`}
          {item.status === 'started' && 'Started'}
          {item.status === 'failed' && (item.lastError || 'Max retries reached')}
        </p>
      </div>

      <button
        onClick={() => removeFromQueue(item.id)}
        className="p-1 text-zinc-500 hover:text-white hover:bg-zinc-700 rounded transition"
      >
        <Trash2 className="w-3 h-3" />
      </button>
    </div>
  );
}
