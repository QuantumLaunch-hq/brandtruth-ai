'use client';

import { Cloud, CloudOff, Save, Clock, AlertCircle } from 'lucide-react';
import { useDraftStore } from '@/stores/draft';
import { useCampaignStore } from '@/stores/campaign';
import { useStoreHydration } from './providers/StoreProvider';

interface DraftIndicatorProps {
  className?: string;
  showSaveButton?: boolean;
  onSave?: () => void;
}

export function DraftIndicator({
  className = '',
  showSaveButton = true,
  onSave,
}: DraftIndicatorProps) {
  const isHydrated = useStoreHydration();
  const { hasUnsavedChanges, processingStage, lastUpdated, canSave } = useDraftStore();
  const { currentCampaignId, getCurrentCampaign } = useCampaignStore();

  if (!isHydrated) {
    return null;
  }

  const currentCampaign = getCurrentCampaign();
  const hasDraftChanges = hasUnsavedChanges();
  const isSaved = currentCampaign?.isSynced;
  const isProcessing = processingStage !== 'idle' && processingStage !== 'complete' && processingStage !== 'error';

  // Format last updated time
  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  // No draft and no current campaign
  if (!hasDraftChanges && !currentCampaignId) {
    return null;
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Status indicator */}
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
          isProcessing
            ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
            : hasDraftChanges && !isSaved
            ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
            : currentCampaign
            ? 'bg-quantum-500/10 text-quantum-400 border border-quantum-500/30'
            : 'bg-zinc-500/10 text-zinc-400 border border-zinc-500/30'
        }`}
      >
        {isProcessing ? (
          <>
            <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
            Processing...
          </>
        ) : hasDraftChanges && !isSaved ? (
          <>
            <CloudOff className="w-3 h-3" />
            Draft
          </>
        ) : currentCampaign ? (
          <>
            <Cloud className="w-3 h-3" />
            Saved
          </>
        ) : (
          <>
            <Clock className="w-3 h-3" />
            New
          </>
        )}
      </div>

      {/* Last updated */}
      {lastUpdated && (
        <span className="text-xs text-zinc-500">
          {formatTime(lastUpdated)}
        </span>
      )}

      {/* Save button */}
      {showSaveButton && canSave() && !isSaved && onSave && (
        <button
          onClick={onSave}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-quantum-500 hover:bg-quantum-600 text-black rounded-full transition"
        >
          <Save className="w-3 h-3" />
          Save Campaign
        </button>
      )}
    </div>
  );
}

export function CompactDraftBadge({ className = '' }: { className?: string }) {
  const isHydrated = useStoreHydration();
  const { hasUnsavedChanges, processingStage } = useDraftStore();

  if (!isHydrated) return null;

  const hasDraftChanges = hasUnsavedChanges();
  const isProcessing =
    processingStage !== 'idle' &&
    processingStage !== 'complete' &&
    processingStage !== 'error';

  if (!hasDraftChanges && !isProcessing) return null;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium ${
        isProcessing
          ? 'bg-blue-500/20 text-blue-400'
          : 'bg-yellow-500/20 text-yellow-400'
      } ${className}`}
    >
      {isProcessing ? 'Processing' : 'Draft'}
    </span>
  );
}
