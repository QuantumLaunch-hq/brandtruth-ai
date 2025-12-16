'use client';

import { useEffect } from 'react';
import {
  Globe,
  Sparkles,
  ImageIcon,
  Layers,
  TrendingUp,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  Wifi,
  WifiOff,
} from 'lucide-react';
import {
  useWorkflowProgress,
  getStageLabel,
  type WorkflowStage,
  type WorkflowProgress as WorkflowProgressType,
} from '@/lib/hooks/useWorkflowProgress';

interface WorkflowProgressProps {
  workflowId: string | null;
  onComplete?: (progress: WorkflowProgressType) => void;
  onError?: (error: string) => void;
  className?: string;
}

interface StageInfo {
  key: WorkflowStage;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const stages: StageInfo[] = [
  { key: 'extracting', label: 'Extracting Brand', icon: Globe },
  { key: 'generating', label: 'Generating Copy', icon: Sparkles },
  { key: 'matching', label: 'Matching Images', icon: ImageIcon },
  { key: 'composing', label: 'Composing Ads', icon: Layers },
  { key: 'scoring', label: 'Scoring Performance', icon: TrendingUp },
];

export function WorkflowProgress({
  workflowId,
  onComplete,
  onError,
  className = '',
}: WorkflowProgressProps) {
  const { progress, isConnected, isComplete, error, startStreaming, stopStreaming } =
    useWorkflowProgress({
      onComplete,
      onError,
    });

  // Start streaming when workflowId changes
  useEffect(() => {
    if (workflowId) {
      startStreaming(workflowId);
    }
    return () => {
      stopStreaming();
    };
  }, [workflowId, startStreaming, stopStreaming]);

  if (!workflowId) {
    return null;
  }

  const currentStageIndex = stages.findIndex((s) => s.key === progress?.stage);
  const progressPercent = progress?.progress_percent ?? 0;

  return (
    <div className={`bg-dark-surface border border-quantum-500/30 rounded-xl p-6 shadow-quantum ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-zinc-300">
            {progress?.stage === 'failed' ? 'Pipeline Failed' : 'Live Generation Progress'}
          </span>
          {isConnected ? (
            <span className="flex items-center gap-1 text-xs text-quantum-400">
              <Wifi className="w-3 h-3" />
              Live
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-zinc-500">
              <WifiOff className="w-3 h-3" />
              {error ? 'Error' : 'Connecting...'}
            </span>
          )}
        </div>
        <span className="text-sm font-mono text-quantum-400">{progressPercent}%</span>
      </div>

      {/* Progress Bar */}
      <div className="h-1.5 bg-dark-hover rounded-full mb-6 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            progress?.stage === 'failed'
              ? 'bg-red-500'
              : 'bg-gradient-to-r from-quantum-500 to-quantum-400'
          }`}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Stages */}
      <div className="space-y-3">
        {stages.map((stage, i) => {
          const isComplete = i < currentStageIndex || progress?.stage === 'completed';
          const isCurrent = stage.key === progress?.stage;
          const isFailed = progress?.stage === 'failed' && i === currentStageIndex;
          const Icon = stage.icon;

          return (
            <div key={stage.key} className="flex items-center gap-3">
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                  isComplete
                    ? 'bg-quantum-500/20'
                    : isCurrent
                    ? 'bg-quantum-500/10 animate-pulse'
                    : isFailed
                    ? 'bg-red-500/20'
                    : 'bg-dark-hover'
                }`}
              >
                {isComplete ? (
                  <CheckCircle className="w-4 h-4 text-quantum-400" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-quantum-400 animate-spin" />
                ) : isFailed ? (
                  <XCircle className="w-4 h-4 text-red-400" />
                ) : (
                  <Icon className="w-4 h-4 text-zinc-600" />
                )}
              </div>
              <span
                className={`text-sm ${
                  isComplete
                    ? 'text-quantum-400'
                    : isCurrent
                    ? 'text-white'
                    : isFailed
                    ? 'text-red-400'
                    : 'text-zinc-600'
                }`}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Status Message */}
      {progress?.message && (
        <div className="mt-4 pt-4 border-t border-dark-hover">
          <p className="text-xs text-zinc-400">{progress.message}</p>
        </div>
      )}

      {/* Error Message */}
      {(error || progress?.error) && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-400">{error || progress?.error}</p>
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-dark-hover">
        <p className="text-xs text-zinc-500 text-center">
          {isComplete
            ? '✓ Pipeline complete'
            : progress?.stage === 'failed'
            ? '✗ Pipeline failed - check errors above'
            : '⚡ Temporal Durable Workflow in progress'}
        </p>
      </div>
    </div>
  );
}

/**
 * Compact progress indicator for headers
 */
export function WorkflowProgressBadge({
  workflowId,
  className = '',
}: {
  workflowId: string | null;
  className?: string;
}) {
  const { progress, isConnected } = useWorkflowProgress();

  useEffect(() => {
    // Note: This component should be used alongside WorkflowProgress
    // which handles the actual streaming connection
  }, []);

  if (!workflowId || !progress) {
    return null;
  }

  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
        progress.stage === 'failed'
          ? 'bg-red-500/10 text-red-400 border border-red-500/30'
          : progress.stage === 'completed'
          ? 'bg-quantum-500/10 text-quantum-400 border border-quantum-500/30'
          : 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
      } ${className}`}
    >
      {progress.stage === 'failed' ? (
        <XCircle className="w-3 h-3" />
      ) : progress.stage === 'completed' ? (
        <CheckCircle className="w-3 h-3" />
      ) : (
        <Loader2 className="w-3 h-3 animate-spin" />
      )}
      <span>{getStageLabel(progress.stage)}</span>
      {progress.stage !== 'completed' && progress.stage !== 'failed' && (
        <span className="font-mono">{progress.progress_percent}%</span>
      )}
    </div>
  );
}
