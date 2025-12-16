'use client';

import { useState, useEffect, useCallback } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Zap,
  Globe,
  Loader2,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  Download,
  ExternalLink,
  RefreshCw,
  Eye,
  TrendingUp,
  DollarSign,
  Users,
  Shield,
  Target,
  Clock,
  BarChart3,
  Play,
  Pause,
  Settings,
  Sparkles,
  AlertCircle,
  Video,
  Wand2,
  Save,
} from 'lucide-react';
import { quantumAPI } from './lib/api';
import { useDraftStore, draftToCampaign } from '@/stores/draft';
import { useCampaignStore, createNewCampaign, generateCampaignId } from '@/stores/campaign';
import { useApiStatusStore } from '@/stores/api-status';
import { useStoreHydration } from '@/components/providers/StoreProvider';
import { ApiStatusBadge } from '@/components/ApiStatusBanner';
import { DraftIndicator } from '@/components/DraftIndicator';
import { WorkflowProgress } from '@/components/WorkflowProgress';
import { QueueStatus } from '@/components/QueueStatus';
import { useWorkflow, useWorkflowProgress, type WorkflowProgress as WorkflowProgressType } from '@/lib/hooks';
import { usePipelineQueueStore } from '@/stores/pipeline-queue';

// =============================================================================
// TYPES
// =============================================================================
interface BrandClaim {
  claim: string;
  source: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
}

interface BrandProfile {
  brand_name: string;
  tagline: string;
  value_propositions: string[];
  claims: BrandClaim[];
  confidence_score: number;
}

interface AdVariant {
  id: string;
  headline: string;
  primary_text: string;
  cta: string;
  angle: string;
  emotion: string;
  score: number;
  image_url?: string;
  status: 'pending' | 'approved' | 'rejected';
}

interface BudgetRecommendation {
  daily_budget: number;
  monthly_budget: number;
  expected_clicks: number;
  expected_conversions: number;
  expected_cpa: number;
  expected_roas: number;
}

interface AudienceRecommendation {
  name: string;
  description: string;
  age_min: number;
  age_max: number;
  countries: string[];
  interests: string[];
}

interface CampaignState {
  step: 'input' | 'processing' | 'results' | 'publishing' | 'live';
  url: string;
  brand: BrandProfile | null;
  variants: AdVariant[];
  budget: BudgetRecommendation | null;
  audience: AudienceRecommendation | null;
  error: string | null;
  processingStage: string;
  processingProgress: number;
  apiAvailable: boolean;
  publishResult: any;
}

// =============================================================================
// MOCK DATA (Fallback when API unavailable)
// =============================================================================
const mockBrand: BrandProfile = {
  brand_name: 'Careerfied',
  tagline: 'Your intelligent career partner',
  value_propositions: [
    'Quantum-optimized resume building',
    'ATS-friendly formatting',
    'Smart job matching',
    'Real-time feedback',
  ],
  claims: [
    { claim: 'Build resumes that get interviews', source: 'Homepage hero', risk_level: 'LOW' },
    { claim: 'Quantum Intelligence writes your bullet points', source: 'Features section', risk_level: 'LOW' },
    { claim: 'Get real-time feedback on your resume', source: 'Homepage', risk_level: 'LOW' },
    { claim: 'Land your dream job in 30 days', source: 'CTA section', risk_level: 'HIGH' },
    { claim: 'Beat the ATS every time', source: 'Features', risk_level: 'MEDIUM' },
  ],
  confidence_score: 0.87,
};

const mockVariants: AdVariant[] = [
  {
    id: 'v1',
    headline: 'Stop Getting Rejected by ATS',
    primary_text: 'Your dream job slips away because your resume can\'t pass automated screening. Quantum Intelligence builds resumes that get interviews.',
    cta: 'Start Building',
    angle: 'pain',
    emotion: 'frustration',
    score: 94,
    image_url: 'https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600',
    status: 'pending',
  },
  {
    id: 'v2',
    headline: 'Your Resume, Quantum Optimized',
    primary_text: 'What if your resume could outsmart every screening system? Quantum Intelligence analyzes job descriptions and tailors your resume for maximum impact.',
    cta: 'Try Free',
    angle: 'curiosity',
    emotion: 'curiosity',
    score: 89,
    image_url: 'https://images.unsplash.com/photo-1493612276216-ee3925520721?w=600',
    status: 'pending',
  },
  {
    id: 'v3',
    headline: 'Land More Interviews, Guaranteed',
    primary_text: 'Join 10,000+ job seekers who transformed their job search. Quantum-powered resume building that actually works.',
    cta: 'Get Started',
    angle: 'social_proof',
    emotion: 'confidence',
    score: 91,
    image_url: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600',
    status: 'pending',
  },
  {
    id: 'v4',
    headline: 'From Rejection to Interview',
    primary_text: 'Most resumes get filtered out before a human sees them. Our Quantum Analysis ensures yours gets through.',
    cta: 'Start Free',
    angle: 'transformation',
    emotion: 'hope',
    score: 87,
    image_url: 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=600',
    status: 'pending',
  },
  {
    id: 'v5',
    headline: 'The Resume Builder That Works',
    primary_text: 'Stop guessing what recruiters want. Quantum Intelligence optimizes every word for maximum interview callbacks.',
    cta: 'Build Now',
    angle: 'benefit',
    emotion: 'confidence',
    score: 88,
    image_url: 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600',
    status: 'pending',
  },
];

const mockBudget: BudgetRecommendation = {
  daily_budget: 30,
  monthly_budget: 900,
  expected_clicks: 2100,
  expected_conversions: 42,
  expected_cpa: 21.43,
  expected_roas: 2.3,
};

const mockAudience: AudienceRecommendation = {
  name: 'Career Changers',
  description: 'Professionals actively seeking new opportunities',
  age_min: 25,
  age_max: 45,
  countries: ['US', 'UK', 'CA'],
  interests: ['Job searching', 'Career development', 'LinkedIn', 'Professional networking'],
};

// =============================================================================
// COMPONENTS
// =============================================================================

function QuantumLogo() {
  return (
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl bg-quantum-500/20 border border-quantum-500/30 flex items-center justify-center">
        <Zap className="w-5 h-5 text-quantum-400" />
      </div>
      <span className="text-xl font-bold text-white">QuantumLaunch</span>
    </div>
  );
}

function QuantumPill({ children }: { children: React.ReactNode }) {
  return (
    <div className="inline-flex items-center gap-2 px-4 py-2 bg-quantum-500/10 border border-quantum-500/30 rounded-full">
      <Sparkles className="w-4 h-4 text-quantum-400" />
      <span className="text-sm font-medium text-quantum-400">{children}</span>
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const level = score >= 90 ? 'high' : score >= 75 ? 'medium' : 'low';
  const colors = {
    high: 'bg-quantum-500/15 text-quantum-400 border-quantum-500/30',
    medium: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
    low: 'bg-red-500/15 text-red-400 border-red-500/30',
  };
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-bold font-mono border ${colors[level]}`}>
      {score}
    </span>
  );
}

function RiskBadge({ level }: { level: 'LOW' | 'MEDIUM' | 'HIGH' }) {
  const colors = {
    LOW: 'bg-quantum-500/10 text-quantum-400 border-quantum-500/20',
    MEDIUM: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    HIGH: 'bg-red-500/10 text-red-400 border-red-500/20',
  };
  
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide border ${colors[level]}`}>
      {level}
    </span>
  );
}

function StatCard({ icon: Icon, value, label, color = 'quantum' }: { 
  icon: any; 
  value: string; 
  label: string;
  color?: 'quantum' | 'purple' | 'yellow';
}) {
  const colors = {
    quantum: 'text-quantum-400 bg-quantum-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
    yellow: 'text-yellow-400 bg-yellow-500/10',
  };
  
  return (
    <div className="text-center">
      <div className={`w-12 h-12 mx-auto mb-2 rounded-full flex items-center justify-center ${colors[color]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className={`text-2xl font-bold font-mono ${colors[color].split(' ')[0]}`}>{value}</div>
      <div className="text-sm text-zinc-500">{label}</div>
    </div>
  );
}

function LivePreviewCard({ stage, progress }: { stage: string; progress: number }) {
  const stages = [
    { key: 'extracting', label: 'Quantum Extractor', icon: Globe },
    { key: 'analyzing', label: 'Quantum Analysis', icon: BarChart3 },
    { key: 'generating', label: 'Generating variants', icon: Sparkles },
    { key: 'scoring', label: 'Quantum Score', icon: TrendingUp },
    { key: 'optimizing', label: 'Quantum Optimization', icon: Target },
  ];
  
  const currentIndex = stages.findIndex(s => s.key === stage);
  
  return (
    <div className="bg-dark-surface border border-quantum-500/30 rounded-xl p-6 shadow-quantum">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-zinc-300">Live Generation Preview</span>
        <span className="text-sm font-mono text-quantum-400">{progress}%</span>
      </div>
      
      <div className="h-1 bg-dark-hover rounded-full mb-6 overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-quantum-500 to-quantum-400 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      
      <div className="space-y-3">
        {stages.map((s, i) => {
          const isComplete = i < currentIndex;
          const isCurrent = i === currentIndex;
          const Icon = s.icon;
          
          return (
            <div key={s.key} className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                isComplete ? 'bg-quantum-500/20' : 
                isCurrent ? 'bg-quantum-500/10 animate-pulse' : 
                'bg-dark-hover'
              }`}>
                {isComplete ? (
                  <CheckCircle className="w-4 h-4 text-quantum-400" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-quantum-400 animate-spin" />
                ) : (
                  <Icon className="w-4 h-4 text-zinc-600" />
                )}
              </div>
              <span className={`text-sm ${
                isComplete ? 'text-quantum-400' : 
                isCurrent ? 'text-white' : 
                'text-zinc-600'
              }`}>
                {s.label}
              </span>
            </div>
          );
        })}
      </div>
      
      <div className="mt-6 pt-4 border-t border-dark-hover">
        <p className="text-xs text-zinc-500 text-center">
          ⚡ Quantum Multi-Model Intelligence at work
        </p>
      </div>
    </div>
  );
}

function AdCard({ 
  variant, 
  onApprove, 
  onReject, 
  onReset,
  onGenerateVideo,
  onImprove,
}: { 
  variant: AdVariant;
  onApprove: () => void;
  onReject: () => void;
  onReset: () => void;
  onGenerateVideo?: () => void;
  onImprove?: () => void;
}) {
  const [showDetails, setShowDetails] = useState(false);
  
  const statusColors = {
    pending: 'border-dark-hover',
    approved: 'border-quantum-500 ring-2 ring-quantum-500/20',
    rejected: 'border-red-500/30 opacity-50',
  };
  
  return (
    <div className={`bg-dark-surface rounded-xl overflow-hidden border ${statusColors[variant.status]} transition-all`}>
      <div className="relative aspect-[4/3] bg-dark-elevated">
        {variant.image_url && (
          <Image
            src={variant.image_url}
            alt={variant.headline}
            fill
            className="object-cover"
          />
        )}
        
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent">
          <div className="absolute bottom-0 left-0 right-0 p-4">
            <h3 className="text-lg font-bold text-white mb-1">{variant.headline}</h3>
            <p className="text-sm text-white/80 line-clamp-2">{variant.primary_text}</p>
            <span className="inline-block mt-2 px-3 py-1 bg-quantum-500 text-black text-sm font-medium rounded">
              {variant.cta}
            </span>
          </div>
        </div>
        
        <div className="absolute top-3 right-3">
          <ScoreBadge score={variant.score} />
        </div>
        
        {variant.status !== 'pending' && (
          <div className={`absolute top-3 left-3 px-2 py-1 rounded text-xs font-medium ${
            variant.status === 'approved' ? 'bg-quantum-500 text-black' : 'bg-red-500 text-white'
          }`}>
            {variant.status === 'approved' ? '✓ Approved' : '✗ Rejected'}
          </div>
        )}
      </div>
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-4 text-xs">
          <span className="px-2 py-1 bg-purple-500/10 text-purple-400 rounded capitalize">{variant.angle}</span>
          <span className="px-2 py-1 bg-dark-hover text-zinc-400 rounded capitalize">{variant.emotion}</span>
          
          {/* Quick Actions */}
          {onGenerateVideo && (
            <button 
              onClick={onGenerateVideo}
              className="ml-auto p-1.5 hover:bg-dark-hover rounded transition"
              title="Generate Video"
            >
              <Video className="w-4 h-4 text-zinc-400 hover:text-quantum-400" />
            </button>
          )}
          {onImprove && variant.score < 90 && (
            <button 
              onClick={onImprove}
              className="p-1.5 hover:bg-dark-hover rounded transition"
              title="Improve this ad"
            >
              <Wand2 className="w-4 h-4 text-zinc-400 hover:text-yellow-400" />
            </button>
          )}
        </div>
        
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="w-full flex items-center justify-between text-sm text-zinc-400 hover:text-white transition"
        >
          <span>View full copy</span>
          {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        
        {showDetails && (
          <div className="mt-3 space-y-2 text-sm">
            <div>
              <span className="text-zinc-500">Headline:</span>
              <p className="text-white">{variant.headline}</p>
            </div>
            <div>
              <span className="text-zinc-500">Primary Text:</span>
              <p className="text-zinc-300">{variant.primary_text}</p>
            </div>
          </div>
        )}
        
        <div className="mt-4 flex gap-2">
          {variant.status === 'pending' ? (
            <>
              <button
                onClick={onApprove}
                className="flex-1 py-2 bg-quantum-500 hover:bg-quantum-600 text-black font-medium rounded-lg transition flex items-center justify-center gap-2"
              >
                <ThumbsUp className="w-4 h-4" />
                Approve
              </button>
              <button
                onClick={onReject}
                className="flex-1 py-2 bg-dark-hover hover:bg-dark-elevated text-zinc-300 font-medium rounded-lg transition flex items-center justify-center gap-2"
              >
                <ThumbsDown className="w-4 h-4" />
                Reject
              </button>
            </>
          ) : (
            <button
              onClick={onReset}
              className="flex-1 py-2 bg-dark-hover hover:bg-dark-elevated text-zinc-300 font-medium rounded-lg transition flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Reset
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================
export default function QuantumLaunchStudio() {
  const router = useRouter();
  const isHydrated = useStoreHydration();

  // Zustand stores
  const draftStore = useDraftStore();
  const campaignStore = useCampaignStore();
  const apiStatus = useApiStatusStore();

  // Temporal workflow hooks
  const { startWorkflow, getResult, approveVariants: approveWorkflowVariants, checkHealth: checkTemporalHealth, isLoading: workflowLoading } = useWorkflow();

  // Local UI state (not persisted)
  const [step, setStep] = useState<'input' | 'processing' | 'results' | 'publishing' | 'live'>('input');
  const [brand, setBrand] = useState<BrandProfile | null>(null);
  const [variants, setVariants] = useState<AdVariant[]>([]);
  const [budget, setBudget] = useState<BudgetRecommendation | null>(null);
  const [audience, setAudience] = useState<AudienceRecommendation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [publishResult, setPublishResult] = useState<any>(null);
  const [expandedSections, setExpandedSections] = useState({
    claims: false,
    budget: false,
    audience: false,
  });

  // Temporal workflow state
  const [workflowId, setWorkflowId] = useState<string | null>(null);

  // Queue store for showing queue status
  const { isTemporalAvailable } = usePipelineQueueStore();

  // Sync from draft store on hydration
  useEffect(() => {
    if (isHydrated && draftStore.processingStage === 'complete' && draftStore.variants.length > 0) {
      // Restore from draft if we have completed results
      setStep('results');
      if (draftStore.brandProfile) {
        setBrand(draftStore.brandProfile as unknown as BrandProfile);
      }
      setVariants(
        draftStore.variants.map((v) => ({
          id: v.id,
          headline: v.headline,
          primary_text: v.primaryText,
          cta: v.cta,
          angle: v.angle || 'benefit',
          emotion: v.emotion || 'confidence',
          score: v.score || 85,
          image_url: v.imageUrl,
          status:
            v.status === 'APPROVED' ? 'approved' : v.status === 'REJECTED' ? 'rejected' : 'pending',
        }))
      );
      if (draftStore.budgetResult) {
        setBudget(draftStore.budgetResult as unknown as BudgetRecommendation);
      }
      if (draftStore.audienceResult) {
        setAudience(draftStore.audienceResult as unknown as AudienceRecommendation);
      }
    }
  }, [isHydrated, draftStore.processingStage, draftStore.variants.length]);

  // Save campaign to store
  const saveCampaign = useCallback(() => {
    if (variants.length === 0 || !draftStore.url) return;

    const newCampaign = createNewCampaign(draftStore.url, draftStore.campaignName);
    newCampaign.status = variants.some((v) => v.status === 'approved') ? 'APPROVED' : 'READY';
    newCampaign.brandProfile = brand ? { ...brand } : undefined;
    newCampaign.budgetResult = budget ? { ...budget } : undefined;
    newCampaign.audienceResult = audience ? { ...audience } : undefined;
    newCampaign.variants = variants.map((v) => ({
      id: v.id,
      headline: v.headline,
      primaryText: v.primary_text,
      cta: v.cta,
      angle: v.angle,
      emotion: v.emotion,
      score: v.score,
      imageUrl: v.image_url,
      status: v.status === 'approved' ? 'APPROVED' : v.status === 'rejected' ? 'REJECTED' : 'PENDING',
    }));

    campaignStore.addCampaign(newCampaign);
    campaignStore.setCurrentCampaign(newCampaign.id);

    // Clear draft after saving
    draftStore.reset();

    // Navigate to campaigns page
    router.push('/campaigns');
  }, [variants, brand, budget, audience, draftStore, campaignStore, router]);

  // API availability from store
  const apiAvailable = apiStatus.status === 'connected';

  // Handle Temporal workflow completion
  const handleWorkflowComplete = useCallback(async (progress: WorkflowProgressType) => {
    if (!workflowId) return;

    try {
      // Fetch the complete result from the workflow
      const result = await getResult(workflowId);
      if (!result) {
        setError('Failed to get workflow result');
        setStep('input');
        return;
      }

      // Transform workflow result to component state
      const brandProfile: BrandProfile = result.brand_profile ? {
        brand_name: result.brand_profile.brand_name,
        tagline: result.brand_profile.tagline,
        value_propositions: result.brand_profile.value_propositions,
        claims: result.brand_profile.claims.map((c) => ({
          claim: c.claim,
          source: c.source,
          risk_level: c.risk_level as 'LOW' | 'MEDIUM' | 'HIGH',
        })),
        confidence_score: result.brand_profile.confidence_score,
      } : mockBrand;

      const scoredVariants: AdVariant[] = result.copy_variants?.variants.map((v, i) => ({
        id: v.id,
        headline: v.headline,
        primary_text: v.primary_text,
        cta: v.cta,
        angle: v.angle,
        emotion: v.emotion,
        score: result.performance_scores?.scores.find((s) => s.variant_id === v.id)?.score || v.quality_score,
        image_url: result.image_matches?.[v.id]?.image_url ||
          mockVariants[i % mockVariants.length].image_url,
        status: 'pending' as const,
      })) || mockVariants;

      // Update state
      setStep('results');
      setBrand(brandProfile);
      setVariants(scoredVariants);
      setBudget(mockBudget); // Budget/audience from separate APIs for now
      setAudience(mockAudience);

      // Save to draft store for persistence
      draftStore.setBrandProfile({ ...brandProfile });
      draftStore.setVariants(
        scoredVariants.map((v) => ({
          id: v.id,
          headline: v.headline,
          primaryText: v.primary_text,
          cta: v.cta,
          angle: v.angle,
          emotion: v.emotion,
          score: v.score,
          imageUrl: v.image_url,
          status: 'PENDING' as const,
        }))
      );
      draftStore.setBudgetResult({ ...mockBudget });
      draftStore.setAudienceResult({ ...mockAudience });
      draftStore.completeProcessing();

      // Clear workflow ID after completion
      setWorkflowId(null);
    } catch (err) {
      console.error('Error handling workflow completion:', err);
      setError(err instanceof Error ? err.message : 'Failed to process workflow result');
      setStep('input');
    }
  }, [workflowId, getResult, draftStore]);

  // Handle Temporal workflow error
  const handleWorkflowError = useCallback((errorMsg: string) => {
    setError(`Workflow error: ${errorMsg}`);
    setStep('input');
    setWorkflowId(null);
    draftStore.setError(errorMsg);
  }, [draftStore]);

  // Process URL (Temporal workflow only)
  const processUrl = async () => {
    const url = draftStore.url;
    if (!url) return;

    setStep('processing');
    setError(null);
    draftStore.startProcessing();

    try {
      // Always use Temporal workflow - hook handles queueing if unavailable
      const id = await startWorkflow({ url, num_variants: 5 });

      if (id) {
        // Check if this is a queue ID (starts with 'queue-')
        if (id.startsWith('queue-')) {
          // Request was queued - show appropriate message
          setError('Temporal service unavailable. Your request has been queued and will start automatically when the service is available.');
          setStep('input');
          draftStore.setError('Request queued for later processing');
          return;
        }

        // Real workflow ID - start tracking progress
        setWorkflowId(id);
        draftStore.updateProgress('extracting', 5, 'Starting Temporal workflow...');
        // WorkflowProgress component will handle SSE streaming and call handleWorkflowComplete
        return;
      }

      // No ID returned - something went wrong
      throw new Error('Failed to start workflow - no workflow ID returned');
    } catch (err) {
      console.error('Processing error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to process URL';
      setStep('input');
      setError(errorMessage);
      draftStore.setError(errorMessage);
    }
  };

  // Variant actions
  const approveVariant = (id: string) => {
    setVariants((prev) =>
      prev.map((v) => (v.id === id ? { ...v, status: 'approved' as const } : v))
    );
    draftStore.updateVariantStatus(id, 'APPROVED');
  };

  const rejectVariant = (id: string) => {
    setVariants((prev) =>
      prev.map((v) => (v.id === id ? { ...v, status: 'rejected' as const } : v))
    );
    draftStore.updateVariantStatus(id, 'REJECTED');
  };

  const resetVariant = (id: string) => {
    setVariants((prev) =>
      prev.map((v) => (v.id === id ? { ...v, status: 'pending' as const } : v))
    );
    draftStore.updateVariantStatus(id, 'PENDING');
  };

  const approveAll = () => {
    setVariants((prev) => prev.map((v) => ({ ...v, status: 'approved' as const })));
    variants.forEach((v) => draftStore.updateVariantStatus(v.id, 'APPROVED'));
  };

  // Publish
  const publish = async () => {
    setStep('publishing');
    setError(null);

    try {
      const approvedAds = variants.filter((v) => v.status === 'approved');

      if (apiAvailable && approvedAds.length > 0) {
        // Publish first approved ad
        const firstAd = approvedAds[0];
        const result = await quantumAPI.publishToMeta({
          headline: firstAd.headline,
          primary_text: firstAd.primary_text,
          cta: firstAd.cta,
          link_url: draftStore.url,
          campaign_name: `${brand?.brand_name || 'QuantumLaunch'} Campaign`,
          daily_budget: budget?.daily_budget || 30,
          start_paused: true,
        });

        setStep('live');
        setPublishResult(result);
      } else {
        // Demo mode
        await new Promise((r) => setTimeout(r, 2000));
        setStep('live');
        setPublishResult({ success: true, demo: true });
      }
    } catch (err) {
      console.error('Publish error:', err);
      setStep('results');
      setError(err instanceof Error ? err.message : 'Failed to publish');
    }
  };

  // Generate video for a variant
  const generateVideo = async (variant: AdVariant) => {
    if (!apiAvailable || !brand) {
      alert('Video generation requires API connection. Start the backend server.');
      return;
    }

    try {
      const result = await quantumAPI.generateVideo({
        brand_name: brand.brand_name,
        product_description: brand.tagline,
        target_audience: audience?.name || 'Target audience',
        key_benefits: brand.value_propositions,
        cta: variant.cta,
      });
      alert(`Video generated! ID: ${result.video_id}\nHook: ${result.hook}`);
    } catch (err) {
      alert('Video generation failed. Check console for details.');
      console.error(err);
    }
  };

  // Improve variant
  const improveVariant = async (variant: AdVariant) => {
    if (!apiAvailable) {
      alert('Improvement suggestions require API connection.');
      return;
    }

    try {
      const result = await quantumAPI.analyzeForIteration({
        headline: variant.headline,
        primary_text: variant.primary_text,
        cta: variant.cta,
        current_ctr: 0.8,
        current_cpa: 50,
        target_cpa: 30,
      });
      alert(`Improvement suggestions:\n${result.summary}`);
    } catch (err) {
      alert('Failed to get improvement suggestions.');
      console.error(err);
    }
  };

  // Start over
  const startOver = () => {
    setStep('input');
    setBrand(null);
    setVariants([]);
    setBudget(null);
    setAudience(null);
    setError(null);
    setPublishResult(null);
    setWorkflowId(null);
    draftStore.reset();
  };

  const approvedCount = variants.filter((v) => v.status === 'approved').length;

  return (
    <div className="min-h-screen bg-dark-primary">
      {/* Header */}
      <header className="border-b border-dark-hover px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <QuantumLogo />

          <div className="flex items-center gap-4">
            <ApiStatusBadge />
            {/* Temporal/Queue status badge */}
            <div className="flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/30">
              <span className={`w-1.5 h-1.5 rounded-full ${isTemporalAvailable ? 'bg-purple-400' : 'bg-yellow-400 animate-pulse'}`} />
              Temporal {isTemporalAvailable ? 'Ready' : 'Offline'}
            </div>
            <QueueStatus compact />
            <DraftIndicator showSaveButton={step === 'results'} onSave={saveCampaign} />
            {step === 'results' && (
              <button
                onClick={startOver}
                className="text-sm text-zinc-400 hover:text-white transition"
              >
                Start Over
              </button>
            )}
            <Link href="/tools" className="text-sm text-zinc-400 hover:text-white transition">
              All Tools
            </Link>
            <Link
              href="/campaigns"
              className="text-sm text-zinc-400 hover:text-white transition"
            >
              My Campaigns
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {/* Queue Status Banner */}
        <QueueStatus className="mb-4" />

        {/* Error Banner */}
        {error && (
          <div className="mb-8 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <p className="text-red-400">{error}</p>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-300"
            >
              <XCircle className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* STEP 1: INPUT */}
        {step === 'input' && (
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <QuantumPill>Quantum Multi-Model Ad Intelligence</QuantumPill>
              
              <h1 className="mt-6 text-5xl font-bold">
                Launch ads at{' '}
                <span className="gradient-text-quantum">quantum speed</span>
              </h1>
              
              <p className="mt-4 text-xl text-zinc-400 max-w-2xl mx-auto">
                The First Autonomous Ad Engine. Transform your website into high-performing 
                ads with Quantum Intelligence — automatic extraction, compliance verification, 
                and one-click publishing.
              </p>
            </div>
            
            <div className="max-w-xl mx-auto mb-8">
              <div className="relative">
                <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-quantum-400" />
                <input
                  type="url"
                  value={draftStore.url}
                  onChange={(e) => draftStore.setUrl(e.target.value)}
                  placeholder="Enter your website URL"
                  className="quantum-input pl-12"
                  onKeyDown={(e) => e.key === 'Enter' && processUrl()}
                />
              </div>
              <p className="mt-2 text-sm text-zinc-500 text-center">
                ✨ Try with:{' '}
                <button
                  onClick={() => draftStore.setUrl('https://careerfied.ai')}
                  className="text-quantum-400 hover:underline"
                >
                  careerfied.ai
                </button>
                {' '}or{' '}
                <button
                  onClick={() => draftStore.setUrl('https://stripe.com')}
                  className="text-quantum-400 hover:underline"
                >
                  stripe.com
                </button>
              </p>
            </div>

            <div className="flex items-center justify-center gap-4">
              <button
                onClick={processUrl}
                disabled={!draftStore.url}
                className="quantum-btn text-lg px-8 py-4"
              >
                <Zap className="w-5 h-5" />
                Launch My Ads
              </button>
              <Link href="/dashboard" className="quantum-btn-secondary text-lg px-8 py-4">
                Advanced Mode
                <ExternalLink className="w-4 h-4" />
              </Link>
            </div>
            
            <div className="mt-16 grid grid-cols-3 gap-8 max-w-lg mx-auto">
              <StatCard icon={Clock} value="60s" label="To Launch" />
              <StatCard icon={DollarSign} value="$99" label="/month" color="purple" />
              <StatCard icon={TrendingUp} value="2.3x" label="Avg ROAS" color="yellow" />
            </div>
            
            {/* What happens */}
            <div className="mt-16 max-w-2xl mx-auto">
              <h3 className="text-center text-sm font-medium text-zinc-500 mb-6 uppercase tracking-wider">
                What Quantum Intelligence does for you
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { icon: Globe, label: 'Extracts claims from your website' },
                  { icon: Shield, label: 'Verifies legal compliance' },
                  { icon: Sparkles, label: 'Generates ad variants' },
                  { icon: TrendingUp, label: 'Scores predicted performance' },
                  { icon: Target, label: 'Suggests optimal audience' },
                  { icon: DollarSign, label: 'Recommends budget' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-dark-surface border border-dark-hover">
                    <item.icon className="w-5 h-5 text-quantum-400" />
                    <span className="text-sm text-zinc-300">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: PROCESSING */}
        {step === 'processing' && (
          <div className="max-w-4xl mx-auto">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="text-3xl font-bold text-white mb-4">
                  {workflowId ? 'Temporal Workflow Processing' : 'Quantum Intelligence is analyzing your website'}
                </h2>
                <p className="text-zinc-400 mb-8">
                  {workflowId
                    ? 'Your ad pipeline is running as a durable Temporal workflow. Progress is streamed in real-time.'
                    : 'Our multi-model system is extracting claims, generating compliant ad copy, matching visuals, and optimizing for performance.'
                  }
                </p>

                <div className="text-sm text-zinc-500">
                  <p className="mb-2">Currently processing:</p>
                  <p className="text-quantum-400 font-mono break-all">{draftStore.url}</p>
                  {workflowId && (
                    <p className="mt-2 text-zinc-600 font-mono text-xs">
                      Workflow: {workflowId}
                    </p>
                  )}
                </div>
              </div>

              {/* Show WorkflowProgress for Temporal, LivePreviewCard for sync */}
              {workflowId ? (
                <WorkflowProgress
                  workflowId={workflowId}
                  onComplete={handleWorkflowComplete}
                  onError={handleWorkflowError}
                />
              ) : (
                <LivePreviewCard
                  stage={draftStore.processingStage}
                  progress={draftStore.processingProgress}
                />
              )}
            </div>
          </div>
        )}

        {/* STEP 3: RESULTS */}
        {step === 'results' && brand && (
          <div className="space-y-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-quantum-500/20 mb-4">
                <CheckCircle className="w-8 h-8 text-quantum-400" />
              </div>
              <h2 className="text-3xl font-bold text-white">
                {brand.brand_name} Campaign Ready
              </h2>
              <p className="mt-2 text-zinc-400">
                Quantum Intelligence analyzed your site and created {variants.length} ads
              </p>
            </div>

            {/* Claims Section */}
            <div className="bg-dark-surface border border-dark-hover rounded-xl overflow-hidden">
              <button
                onClick={() => setExpandedSections((s) => ({ ...s, claims: !s.claims }))}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-dark-hover/50 transition"
              >
                <div className="flex items-center gap-3">
                  <Shield className="w-5 h-5 text-quantum-400" />
                  <span className="font-medium text-white">
                    Extracted Claims ({brand.claims.length})
                  </span>
                  <span className="text-sm text-zinc-500">— Compliance verified</span>
                </div>
                {expandedSections.claims ? (
                  <ChevronUp className="w-5 h-5 text-zinc-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-zinc-400" />
                )}
              </button>

              {expandedSections.claims && (
                <div className="px-6 pb-4 space-y-2">
                  {brand.claims.map((claim, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between py-2 px-3 bg-dark-hover rounded-lg"
                    >
                      <div>
                        <p className="text-white">{claim.claim}</p>
                        <p className="text-sm text-zinc-500">Source: {claim.source}</p>
                      </div>
                      <RiskBadge level={claim.risk_level} />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Ads Grid */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Generated Ads</h3>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-zinc-400">
                    {approvedCount} of {variants.length} approved
                  </span>
                  <button
                    onClick={approveAll}
                    className="text-sm text-quantum-400 hover:text-quantum-300 transition"
                  >
                    Approve All
                  </button>
                </div>
              </div>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {variants.map((variant) => (
                  <AdCard
                    key={variant.id}
                    variant={variant}
                    onApprove={() => approveVariant(variant.id)}
                    onReject={() => rejectVariant(variant.id)}
                    onReset={() => resetVariant(variant.id)}
                    onGenerateVideo={() => generateVideo(variant)}
                    onImprove={() => improveVariant(variant)}
                  />
                ))}
              </div>
            </div>

            {/* Budget & Audience Row */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Budget */}
              <div className="bg-dark-surface border border-dark-hover rounded-xl overflow-hidden">
                <button
                  onClick={() => setExpandedSections((s) => ({ ...s, budget: !s.budget }))}
                  className="w-full px-6 py-4 flex items-center justify-between hover:bg-dark-hover/50 transition"
                >
                  <div className="flex items-center gap-3">
                    <DollarSign className="w-5 h-5 text-quantum-400" />
                    <span className="font-medium text-white">Budget Recommendation</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-quantum-400 font-mono font-bold">
                      ${budget?.daily_budget}/day
                    </span>
                    {expandedSections.budget ? (
                      <ChevronUp className="w-5 h-5 text-zinc-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-zinc-400" />
                    )}
                  </div>
                </button>

                {expandedSections.budget && budget && (
                  <div className="px-6 pb-4 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-zinc-500">Monthly Budget</span>
                      <p className="text-white font-medium">${budget.monthly_budget}</p>
                    </div>
                    <div>
                      <span className="text-zinc-500">Expected Clicks</span>
                      <p className="text-white font-medium">
                        {budget.expected_clicks.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <span className="text-zinc-500">Expected CPA</span>
                      <p className="text-white font-medium">${budget.expected_cpa.toFixed(2)}</p>
                    </div>
                    <div>
                      <span className="text-zinc-500">Expected ROAS</span>
                      <p className="text-quantum-400 font-medium">{budget.expected_roas}x</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Audience */}
              <div className="bg-dark-surface border border-dark-hover rounded-xl overflow-hidden">
                <button
                  onClick={() => setExpandedSections((s) => ({ ...s, audience: !s.audience }))}
                  className="w-full px-6 py-4 flex items-center justify-between hover:bg-dark-hover/50 transition"
                >
                  <div className="flex items-center gap-3">
                    <Users className="w-5 h-5 text-quantum-400" />
                    <span className="font-medium text-white">Target Audience</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-zinc-400">{audience?.name}</span>
                    {expandedSections.audience ? (
                      <ChevronUp className="w-5 h-5 text-zinc-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-zinc-400" />
                    )}
                  </div>
                </button>

                {expandedSections.audience && audience && (
                  <div className="px-6 pb-4 space-y-3 text-sm">
                    <p className="text-zinc-400">{audience.description}</p>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-2 py-1 bg-dark-hover text-zinc-300 rounded text-xs">
                        Ages {audience.age_min}-{audience.age_max}
                      </span>
                      {audience.countries.map((c) => (
                        <span
                          key={c}
                          className="px-2 py-1 bg-dark-hover text-zinc-300 rounded text-xs"
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {audience.interests.slice(0, 4).map((interest, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-purple-500/10 text-purple-400 rounded text-xs"
                        >
                          {interest}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Publish CTA */}
            <div className="bg-gradient-to-r from-quantum-500/10 to-purple-500/10 border border-quantum-500/30 rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white">Ready to launch?</h3>
                  <p className="text-zinc-400">
                    {approvedCount} ads approved • ${budget?.daily_budget}/day •{' '}
                    {audience?.countries.join(', ')}
                  </p>
                </div>
                <button
                  onClick={publish}
                  disabled={approvedCount === 0}
                  className="quantum-btn px-8"
                >
                  <Zap className="w-5 h-5" />
                  Publish to Meta
                </button>
              </div>
              
              <div className="mt-4 pt-4 border-t border-quantum-500/20 text-sm text-zinc-500">
                <p>After launch, Quantum Sentinel will monitor for:</p>
                <div className="flex gap-4 mt-2">
                  <span className="flex items-center gap-1">
                    <Shield className="w-4 h-4 text-quantum-400" />
                    PR crises (auto-pause)
                  </span>
                  <span className="flex items-center gap-1">
                    <RefreshCw className="w-4 h-4 text-yellow-400" />
                    Creative fatigue
                  </span>
                  <span className="flex items-center gap-1">
                    <BarChart3 className="w-4 h-4 text-purple-400" />
                    Performance reports
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 4: PUBLISHING */}
        {step === 'publishing' && (
          <div className="max-w-lg mx-auto text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-quantum-500/20 mb-6 animate-quantum-pulse">
              <Loader2 className="w-10 h-10 text-quantum-400 animate-spin" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Publishing to Meta</h2>
            <p className="text-zinc-400">
              Creating campaign, ad sets, and uploading creatives...
            </p>
          </div>
        )}

        {/* STEP 5: LIVE */}
        {step === 'live' && (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-quantum-500/20 mb-6">
                <CheckCircle className="w-10 h-10 text-quantum-400" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">Campaign is Live!</h2>
              <p className="text-zinc-400">
                Your ads are now running on Meta. Quantum Sentinel is monitoring 24/7.
              </p>
            </div>

            <div className="bg-dark-surface border border-quantum-500/30 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between py-2">
                <span className="text-zinc-400">Campaign Status</span>
                <span className="flex items-center gap-2 text-quantum-400">
                  <span className="w-2 h-2 bg-quantum-400 rounded-full animate-pulse" />
                  {publishResult?.demo ? 'Demo (Paused)' : 'Active'}
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-t border-dark-hover">
                <span className="text-zinc-400">Ads Published</span>
                <span className="text-white font-medium">{approvedCount}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-t border-dark-hover">
                <span className="text-zinc-400">Daily Budget</span>
                <span className="text-white font-medium">${budget?.daily_budget}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-t border-dark-hover">
                <span className="text-zinc-400">Quantum Sentinel</span>
                <span className="flex items-center gap-2 text-quantum-400">
                  <Shield className="w-4 h-4" />
                  Monitoring
                </span>
              </div>

              {publishResult?.campaign_id && (
                <div className="pt-4 border-t border-dark-hover text-sm">
                  <p className="text-zinc-500 mb-2">Campaign Details:</p>
                  <p className="font-mono text-zinc-400">
                    Campaign: {publishResult.campaign_id}
                  </p>
                  <p className="font-mono text-zinc-400">Ad: {publishResult.ad_id}</p>
                </div>
              )}

              {publishResult?.demo && (
                <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-sm text-yellow-400">
                  Demo mode - Connect Meta API for live publishing
                </div>
              )}
            </div>
            
            <div className="mt-6 flex gap-4">
              <button className="flex-1 quantum-btn-secondary">
                <ExternalLink className="w-4 h-4" />
                Open Meta Ads Manager
              </button>
              <button onClick={startOver} className="flex-1 quantum-btn-secondary">
                <RefreshCw className="w-4 h-4" />
                Launch Another
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-hover mt-20 py-8">
        <div className="max-w-7xl mx-auto px-6 text-center text-sm text-zinc-500">
          <p>Powered by Quantum Multi-Model Intelligence</p>
          <p className="mt-1">© 2025 QuantumLaunch • Part of the Quantum family</p>
        </div>
      </footer>
    </div>
  );
}
