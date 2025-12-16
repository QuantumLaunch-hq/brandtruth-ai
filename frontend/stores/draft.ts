import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { Campaign, Variant, CampaignStatus } from './campaign';

// Pipeline processing stages
export type ProcessingStage =
  | 'idle'
  | 'extracting'
  | 'generating'
  | 'matching'
  | 'composing'
  | 'scoring'
  | 'complete'
  | 'error';

// Draft state for current work-in-progress
export interface DraftState {
  // Input
  url: string;
  campaignName: string;

  // Processing state
  isProcessing: boolean;
  processingStage: ProcessingStage;
  processingProgress: number; // 0-100
  processingMessage: string;
  workflowId: string | null;

  // Results (in-progress, not yet saved to campaign)
  brandProfile: Record<string, unknown> | null;
  variants: Variant[];
  budgetResult: Record<string, unknown> | null;
  audienceResult: Record<string, unknown> | null;

  // Error state
  error: string | null;

  // Timestamps
  lastUpdated: string | null;
  startedAt: string | null;

  // Actions
  setUrl: (url: string) => void;
  setCampaignName: (name: string) => void;
  startProcessing: (workflowId?: string) => void;
  updateProgress: (stage: ProcessingStage, progress: number, message?: string) => void;
  setError: (error: string) => void;
  setBrandProfile: (profile: Record<string, unknown>) => void;
  setVariants: (variants: Variant[]) => void;
  setBudgetResult: (result: Record<string, unknown>) => void;
  setAudienceResult: (result: Record<string, unknown>) => void;
  updateVariantStatus: (variantId: string, status: Variant['status']) => void;
  updateVariantScore: (variantId: string, score: number, details?: Record<string, unknown>) => void;
  completeProcessing: () => void;
  reset: () => void;
  clearDraft: () => void;

  // Computed
  hasUnsavedChanges: () => boolean;
  getApprovedVariants: () => Variant[];
  canSave: () => boolean;
}

const initialState = {
  url: '',
  campaignName: '',
  isProcessing: false,
  processingStage: 'idle' as ProcessingStage,
  processingProgress: 0,
  processingMessage: '',
  workflowId: null,
  brandProfile: null,
  variants: [],
  budgetResult: null,
  audienceResult: null,
  error: null,
  lastUpdated: null,
  startedAt: null,
};

export const useDraftStore = create<DraftState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Actions
      setUrl: (url) =>
        set({
          url,
          lastUpdated: new Date().toISOString(),
        }),

      setCampaignName: (campaignName) =>
        set({
          campaignName,
          lastUpdated: new Date().toISOString(),
        }),

      startProcessing: (workflowId) =>
        set({
          isProcessing: true,
          processingStage: 'extracting',
          processingProgress: 0,
          processingMessage: 'Starting pipeline...',
          workflowId: workflowId || null,
          error: null,
          startedAt: new Date().toISOString(),
          lastUpdated: new Date().toISOString(),
        }),

      updateProgress: (stage, progress, message) =>
        set({
          processingStage: stage,
          processingProgress: progress,
          processingMessage: message || get().processingMessage,
          lastUpdated: new Date().toISOString(),
        }),

      setError: (error) =>
        set({
          error,
          isProcessing: false,
          processingStage: 'error',
          lastUpdated: new Date().toISOString(),
        }),

      setBrandProfile: (brandProfile) =>
        set({
          brandProfile,
          lastUpdated: new Date().toISOString(),
        }),

      setVariants: (variants) =>
        set({
          variants,
          lastUpdated: new Date().toISOString(),
        }),

      setBudgetResult: (budgetResult) =>
        set({
          budgetResult,
          lastUpdated: new Date().toISOString(),
        }),

      setAudienceResult: (audienceResult) =>
        set({
          audienceResult,
          lastUpdated: new Date().toISOString(),
        }),

      updateVariantStatus: (variantId, status) =>
        set((state) => ({
          variants: state.variants.map((v) =>
            v.id === variantId ? { ...v, status } : v
          ),
          lastUpdated: new Date().toISOString(),
        })),

      updateVariantScore: (variantId, score, details) =>
        set((state) => ({
          variants: state.variants.map((v) =>
            v.id === variantId ? { ...v, score, scoreDetails: details } : v
          ),
          lastUpdated: new Date().toISOString(),
        })),

      completeProcessing: () =>
        set({
          isProcessing: false,
          processingStage: 'complete',
          processingProgress: 100,
          processingMessage: 'Pipeline complete!',
          lastUpdated: new Date().toISOString(),
        }),

      reset: () =>
        set({
          ...initialState,
          lastUpdated: new Date().toISOString(),
        }),

      clearDraft: () => set(initialState),

      // Computed
      hasUnsavedChanges: () => {
        const state = get();
        return (
          state.url !== '' ||
          state.brandProfile !== null ||
          state.variants.length > 0
        );
      },

      getApprovedVariants: () => {
        return get().variants.filter((v) => v.status === 'APPROVED');
      },

      canSave: () => {
        const state = get();
        return (
          state.processingStage === 'complete' &&
          state.variants.length > 0 &&
          !state.isProcessing
        );
      },
    }),
    {
      name: 'brandtruth-draft',
      storage: createJSONStorage(() => localStorage),
      // Don't persist processing state - only persist results
      partialize: (state) => ({
        url: state.url,
        campaignName: state.campaignName,
        brandProfile: state.brandProfile,
        variants: state.variants,
        budgetResult: state.budgetResult,
        audienceResult: state.audienceResult,
        lastUpdated: state.lastUpdated,
        processingStage: state.processingStage === 'complete' ? 'complete' : 'idle',
      }),
    }
  )
);

// Helper to convert draft to campaign
export const draftToCampaign = (draft: DraftState, campaignId: string): Partial<Campaign> => {
  return {
    id: campaignId,
    name: draft.campaignName || `Campaign ${new Date().toLocaleDateString()}`,
    url: draft.url,
    status: draft.variants.some((v) => v.status === 'APPROVED') ? 'APPROVED' : 'READY',
    brandProfile: draft.brandProfile || undefined,
    budgetResult: draft.budgetResult || undefined,
    audienceResult: draft.audienceResult || undefined,
    variants: draft.variants,
    workflowId: draft.workflowId || undefined,
  };
};
