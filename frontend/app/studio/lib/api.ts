/**
 * QuantumLaunch API Client
 * Connects to all backend endpoints running Quantum Intelligence
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// TYPES
// =============================================================================

export interface BrandClaim {
  claim: string;
  source: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface BrandProfile {
  brand_name: string;
  tagline: string;
  value_propositions: string[];
  claims: BrandClaim[];
  confidence_score: number;
}

export interface AdVariant {
  id: string;
  headline: string;
  primary_text: string;
  cta: string;
  angle: string;
  emotion: string;
  score: number;
  image_url?: string;
  composed_url?: string;
  status: 'pending' | 'approved' | 'rejected';
}

export interface PipelineResult {
  job_id: string;
  stage: string;
  brand_profile?: BrandProfile;
  copy_variants?: any[];
  images?: any[];
  composed_ads?: any[];
  image_matches?: Record<string, {
    image_url: string;
    relevance_score: number;
    photographer?: string;
    photographer_url?: string;
  }>;
}

export interface BudgetSimulation {
  daily_budget: number;
  monthly_budget: number;
  tier: string;
  expected_impressions: number;
  expected_clicks: number;
  expected_conversions: number;
  expected_cpa: number;
  expected_roas: number;
  break_even_days: number;
  confidence_level: number;
  recommendations: string[];
  summary: string;
}

export interface AudienceSuggestion {
  primary_audiences: {
    name: string;
    type: string;
    estimated_size: number;
    relevance_score: number;
    targeting_tips: string[];
  }[];
  secondary_audiences: {
    name: string;
    type: string;
    estimated_size: number;
    relevance_score: number;
  }[];
  exclusions: {
    name: string;
    reason: string;
    impact: string;
  }[];
  lookalike_strategy: string;
  budget_allocation: Record<string, number>;
  testing_order: string[];
  recommendations: string[];
  summary: string;
}

export interface HookResult {
  hooks: {
    text: string;
    pattern: string;
    score: number;
    explanation: string;
  }[];
  best_hook: string;
  summary: string;
  recommendations: string[];
}

export interface PredictionResult {
  score: number;
  tier: string;
  summary: string;
}

export interface SentimentResult {
  health: string;
  auto_pause: boolean;
}

export interface PublishResult {
  success: boolean;
  campaign_id?: string;
  adset_id?: string;
  creative_id?: string;
  ad_id?: string;
  details?: any;
  error?: string;
  message?: string;
}

// =============================================================================
// API CLIENT
// =============================================================================

class QuantumAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // ===========================================================================
  // HEALTH
  // ===========================================================================

  async checkHealth(): Promise<{ status: string; version: string }> {
    return this.request('/health');
  }

  // ===========================================================================
  // PIPELINE - Core extraction and generation
  // ===========================================================================

  /**
   * @deprecated Use Temporal workflows via useWorkflow hook instead.
   *
   * This synchronous pipeline API has been superseded by Temporal workflows
   * which provide:
   * - Durable execution (survives crashes/restarts)
   * - Real-time progress streaming via SSE
   * - Automatic retries and queue management
   * - Better observability in Temporal UI
   *
   * Migration guide:
   * ```tsx
   * // Before (deprecated):
   * const result = await quantumAPI.runPipeline({ url, num_variants: 5 });
   *
   * // After (recommended):
   * import { useWorkflow } from '@/lib/hooks';
   * const { startWorkflow, getResult } = useWorkflow();
   * const workflowId = await startWorkflow({ url, num_variants: 5 });
   * // Use WorkflowProgress component for SSE progress streaming
   * // Get final result with: await getResult(workflowId)
   * ```
   *
   * The useWorkflow hook also handles automatic queueing when Temporal
   * is unavailable, with background health polling and auto-retry.
   */
  async runPipeline(params: {
    url: string;
    num_variants?: number;
    platform?: string;
    formats?: string[];
  }): Promise<PipelineResult> {
    console.warn(
      '[DEPRECATED] quantumAPI.runPipeline() is deprecated. ' +
      'Use useWorkflow hook with Temporal workflows instead. ' +
      'See @/lib/hooks/useWorkflow.ts for the new API.'
    );
    return this.request('/pipeline/run', {
      method: 'POST',
      body: JSON.stringify({
        url: params.url,
        num_variants: params.num_variants || 5,
        platform: params.platform || 'meta',
        formats: params.formats || ['square'],
      }),
    });
  }

  // ===========================================================================
  // HOOKS - Generate headlines
  // ===========================================================================

  async generateHooks(params: {
    product_name: string;
    product_description: string;
    target_audience: string;
    pain_points?: string[];
    benefits?: string[];
    tone?: string;
    num_hooks?: number;
  }): Promise<HookResult> {
    return this.request('/hooks/generate', {
      method: 'POST',
      body: JSON.stringify({
        product_name: params.product_name,
        product_description: params.product_description,
        target_audience: params.target_audience,
        pain_points: params.pain_points || [],
        benefits: params.benefits || [],
        tone: params.tone || 'professional',
        include_emojis: false,
        num_hooks: params.num_hooks || 10,
      }),
    });
  }

  // ===========================================================================
  // PREDICT - Score ad performance
  // ===========================================================================

  async predictPerformance(params: {
    headline: string;
    primary_text: string;
    cta: string;
  }): Promise<PredictionResult> {
    return this.request('/predict', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // ===========================================================================
  // BUDGET - Simulate budget scenarios
  // ===========================================================================

  async simulateBudget(params: {
    industry?: string;
    goal?: string;
    product_price?: number;
    target_monthly_conversions?: number;
    target_cpa?: number;
  }): Promise<BudgetSimulation> {
    return this.request('/budget/simulate', {
      method: 'POST',
      body: JSON.stringify({
        industry: params.industry || 'saas',
        goal: params.goal || 'leads',
        product_price: params.product_price || 99,
        target_monthly_conversions: params.target_monthly_conversions || 50,
        target_cpa: params.target_cpa,
      }),
    });
  }

  // ===========================================================================
  // AUDIENCE - Suggest targeting
  // ===========================================================================

  async suggestAudiences(params: {
    product_name: string;
    product_description: string;
    product_type?: string;
    target_persona: string;
    price_point?: number;
  }): Promise<AudienceSuggestion> {
    return this.request('/audience/suggest', {
      method: 'POST',
      body: JSON.stringify({
        product_name: params.product_name,
        product_description: params.product_description,
        product_type: params.product_type || 'saas',
        target_persona: params.target_persona,
        price_point: params.price_point || 99,
        existing_customers: false,
        website_traffic: false,
      }),
    });
  }

  // ===========================================================================
  // PLATFORMS - Recommend best platforms
  // ===========================================================================

  async recommendPlatforms(params: {
    product_type?: string;
    audience_type?: string;
    monthly_budget?: number;
    product_price?: number;
    is_visual?: boolean;
  }): Promise<any> {
    return this.request('/platforms/recommend', {
      method: 'POST',
      body: JSON.stringify({
        product_type: params.product_type || 'b2b_saas',
        audience_type: params.audience_type || 'professionals',
        monthly_budget: params.monthly_budget || 1000,
        product_price: params.product_price || 99,
        is_visual: params.is_visual ?? true,
      }),
    });
  }

  // ===========================================================================
  // SENTIMENT - Monitor brand health (Quantum Sentinel)
  // ===========================================================================

  async checkSentiment(params: {
    brand_name: string;
    scenario?: string;
  }): Promise<SentimentResult> {
    return this.request('/sentiment/check', {
      method: 'POST',
      body: JSON.stringify({
        brand_name: params.brand_name,
        scenario: params.scenario || 'normal',
      }),
    });
  }

  // ===========================================================================
  // ATTENTION - Analyze visual attention
  // ===========================================================================

  async analyzeAttention(params: {
    image_url?: string;
    headline?: string;
    cta?: string;
  }): Promise<any> {
    return this.request('/attention/analyze', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // ===========================================================================
  // LANDING - Analyze landing page
  // ===========================================================================

  async analyzeLandingPage(params: {
    landing_page_url: string;
    ad_headline: string;
    ad_primary_text: string;
    ad_cta?: string;
  }): Promise<any> {
    return this.request('/landing/analyze', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // ===========================================================================
  // COMPETITOR INTEL (Quantum Radar)
  // ===========================================================================

  async analyzeCompetitors(params: {
    brand_name: string;
    industry: string;
    competitor_names?: string[];
  }): Promise<any> {
    return this.request('/intel/analyze', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // ===========================================================================
  // FATIGUE - Predict creative fatigue (Quantum Pulse)
  // ===========================================================================

  async predictFatigue(params: {
    ad_id: string;
    days_running?: number;
    frequency?: number;
    reach?: number;
    audience_size?: number;
    industry?: string;
  }): Promise<any> {
    return this.request('/fatigue/predict', {
      method: 'POST',
      body: JSON.stringify({
        ad_id: params.ad_id,
        days_running: params.days_running || 14,
        frequency: params.frequency || 2.5,
        reach: params.reach || 20000,
        audience_size: params.audience_size || 100000,
        industry: params.industry || 'general',
      }),
    });
  }

  // ===========================================================================
  // A/B TEST - Plan tests
  // ===========================================================================

  async planABTest(params: {
    variants: any[];
    baseline_ctr?: number;
    baseline_cvr?: number;
    daily_budget?: number;
  }): Promise<any> {
    return this.request('/abtest/plan', {
      method: 'POST',
      body: JSON.stringify({
        variants: params.variants,
        baseline_ctr: params.baseline_ctr || 1.0,
        baseline_cvr: params.baseline_cvr || 2.0,
        daily_budget: params.daily_budget || 50,
        confidence_level: 0.95,
        minimum_lift: 0.20,
      }),
    });
  }

  // ===========================================================================
  // ITERATE - Improve ads
  // ===========================================================================

  async analyzeForIteration(params: {
    headline: string;
    primary_text: string;
    cta: string;
    current_ctr?: number;
    current_cvr?: number;
    current_cpa?: number;
    target_cpa?: number;
  }): Promise<any> {
    return this.request('/iterate/analyze', {
      method: 'POST',
      body: JSON.stringify({
        headline: params.headline,
        primary_text: params.primary_text,
        cta: params.cta,
        current_ctr: params.current_ctr || 0.8,
        current_cvr: params.current_cvr || 1.5,
        current_cpa: params.current_cpa || 80,
        target_cpa: params.target_cpa || 50,
        impressions: 10000,
        frequency: 2.0,
        days_running: 7,
      }),
    });
  }

  // ===========================================================================
  // VIDEO - Generate video ads
  // ===========================================================================

  async generateVideo(params: {
    brand_name: string;
    product_description: string;
    target_audience: string;
    key_benefits: string[];
    cta?: string;
    style?: string;
  }): Promise<any> {
    return this.request('/video/generate', {
      method: 'POST',
      body: JSON.stringify({
        brand_name: params.brand_name,
        product_description: params.product_description,
        target_audience: params.target_audience,
        key_benefits: params.key_benefits,
        cta: params.cta || 'Learn More',
        style: params.style || 'ugc',
        aspect_ratio: '9:16',
        avatar_style: 'casual',
        include_captions: true,
        include_music: true,
      }),
    });
  }

  // ===========================================================================
  // META - Publish to Meta Ads
  // ===========================================================================

  async publishToMeta(params: {
    headline: string;
    primary_text: string;
    cta?: string;
    image_url?: string;
    link_url: string;
    campaign_name?: string;
    daily_budget?: number;
    start_paused?: boolean;
  }): Promise<PublishResult> {
    return this.request('/meta/publish', {
      method: 'POST',
      body: JSON.stringify({
        headline: params.headline,
        primary_text: params.primary_text,
        cta: params.cta || 'Learn More',
        link_url: params.link_url,
        page_id: 'demo_page',
        campaign_name: params.campaign_name || 'QuantumLaunch Campaign',
        daily_budget: (params.daily_budget || 10) * 100, // Convert to cents
        start_paused: params.start_paused ?? true,
      }),
    });
  }

  // ===========================================================================
  // EXPORT - Export to multiple formats
  // ===========================================================================

  async exportAllFormats(params: {
    image_url: string;
    headline: string;
    cta?: string;
    formats?: string[];
  }): Promise<any> {
    return this.request('/export/all', {
      method: 'POST',
      body: JSON.stringify({
        image_url: params.image_url,
        headline: params.headline,
        cta: params.cta || 'Learn More',
        formats: params.formats,
        create_zip: true,
      }),
    });
  }

  // ===========================================================================
  // SOCIAL PROOF - Collect testimonials
  // ===========================================================================

  async collectSocialProof(params: {
    brand_name: string;
    brand_url: string;
    product_description: string;
    existing_testimonials?: string[];
    user_count?: number;
    rating?: number;
  }): Promise<any> {
    return this.request('/social/collect', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // ===========================================================================
  // PROOF PACK - Compliance documentation
  // ===========================================================================

  async generateProofPack(params: {
    ad_id: string;
    campaign_name: string;
    brand_name: string;
    headline: string;
    primary_text: string;
    cta?: string;
    claims?: any[];
  }): Promise<any> {
    return this.request('/proof/generate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }
}

// Export singleton instance
export const quantumAPI = new QuantumAPI();

// Export class for custom instances
export { QuantumAPI };
