import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// Types matching Prisma schema
export type CampaignStatus =
  | 'DRAFT'
  | 'PROCESSING'
  | 'READY'
  | 'APPROVED'
  | 'PUBLISHED'
  | 'FAILED'
  | 'CANCELLED';

export type VariantStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface Variant {
  id: string;
  headline: string;
  primaryText: string;
  cta: string;
  angle?: string;
  emotion?: string;
  imageUrl?: string;
  composedUrl?: string;
  score?: number;
  scoreDetails?: Record<string, unknown>;
  status: VariantStatus;
}

export interface Campaign {
  id: string;
  name: string;
  url: string;
  status: CampaignStatus;
  workflowId?: string;
  brandProfile?: Record<string, unknown>;
  budgetResult?: Record<string, unknown>;
  audienceResult?: Record<string, unknown>;
  variants: Variant[];
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  // Local-only fields
  isSynced?: boolean;
  lastSyncedAt?: string;
}

interface CampaignState {
  // Data
  campaigns: Campaign[];
  currentCampaignId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setCampaigns: (campaigns: Campaign[]) => void;
  addCampaign: (campaign: Campaign) => void;
  updateCampaign: (id: string, updates: Partial<Campaign>) => void;
  deleteCampaign: (id: string) => void;
  setCurrentCampaign: (id: string | null) => void;

  // Variant actions
  updateVariant: (campaignId: string, variantId: string, updates: Partial<Variant>) => void;
  approveVariant: (campaignId: string, variantId: string) => void;
  rejectVariant: (campaignId: string, variantId: string) => void;
  approveAllVariants: (campaignId: string) => void;

  // Sync actions
  markSynced: (id: string) => void;
  markUnsaved: (id: string) => void;

  // Selectors
  getCampaign: (id: string) => Campaign | undefined;
  getCurrentCampaign: () => Campaign | undefined;
  getUnsyncedCampaigns: () => Campaign[];

  // Loading state
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useCampaignStore = create<CampaignState>()(
  persist(
    (set, get) => ({
      // Initial state
      campaigns: [],
      currentCampaignId: null,
      isLoading: false,
      error: null,

      // Actions
      setCampaigns: (campaigns) => set({ campaigns }),

      addCampaign: (campaign) =>
        set((state) => ({
          campaigns: [campaign, ...state.campaigns],
        })),

      updateCampaign: (id, updates) =>
        set((state) => ({
          campaigns: state.campaigns.map((c) =>
            c.id === id
              ? { ...c, ...updates, updatedAt: new Date().toISOString(), isSynced: false }
              : c
          ),
        })),

      deleteCampaign: (id) =>
        set((state) => ({
          campaigns: state.campaigns.filter((c) => c.id !== id),
          currentCampaignId: state.currentCampaignId === id ? null : state.currentCampaignId,
        })),

      setCurrentCampaign: (id) => set({ currentCampaignId: id }),

      // Variant actions
      updateVariant: (campaignId, variantId, updates) =>
        set((state) => ({
          campaigns: state.campaigns.map((c) =>
            c.id === campaignId
              ? {
                  ...c,
                  variants: c.variants.map((v) =>
                    v.id === variantId ? { ...v, ...updates } : v
                  ),
                  updatedAt: new Date().toISOString(),
                  isSynced: false,
                }
              : c
          ),
        })),

      approveVariant: (campaignId, variantId) =>
        get().updateVariant(campaignId, variantId, { status: 'APPROVED' }),

      rejectVariant: (campaignId, variantId) =>
        get().updateVariant(campaignId, variantId, { status: 'REJECTED' }),

      approveAllVariants: (campaignId) =>
        set((state) => ({
          campaigns: state.campaigns.map((c) =>
            c.id === campaignId
              ? {
                  ...c,
                  variants: c.variants.map((v) => ({ ...v, status: 'APPROVED' as VariantStatus })),
                  status: 'APPROVED' as CampaignStatus,
                  updatedAt: new Date().toISOString(),
                  isSynced: false,
                }
              : c
          ),
        })),

      // Sync actions
      markSynced: (id) =>
        set((state) => ({
          campaigns: state.campaigns.map((c) =>
            c.id === id
              ? { ...c, isSynced: true, lastSyncedAt: new Date().toISOString() }
              : c
          ),
        })),

      markUnsaved: (id) =>
        set((state) => ({
          campaigns: state.campaigns.map((c) =>
            c.id === id ? { ...c, isSynced: false } : c
          ),
        })),

      // Selectors
      getCampaign: (id) => get().campaigns.find((c) => c.id === id),

      getCurrentCampaign: () => {
        const { campaigns, currentCampaignId } = get();
        return campaigns.find((c) => c.id === currentCampaignId);
      },

      getUnsyncedCampaigns: () => get().campaigns.filter((c) => !c.isSynced),

      // Loading state
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
    }),
    {
      name: 'brandtruth-campaigns',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        campaigns: state.campaigns,
        currentCampaignId: state.currentCampaignId,
      }),
    }
  )
);

// Helper to generate a unique ID
export const generateCampaignId = () => {
  return `campaign_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Helper to create a new campaign
export const createNewCampaign = (url: string, name?: string): Campaign => {
  const id = generateCampaignId();
  return {
    id,
    name: name || `Campaign ${new Date().toLocaleDateString()}`,
    url,
    status: 'DRAFT',
    variants: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    isSynced: false,
  };
};
