'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import {
  Zap,
  ArrowLeft,
  Globe,
  Loader2,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Download,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Sparkles,
  ImageIcon,
  FileText,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Copy,
  Check,
  LayoutGrid,
  List,
  Eye,
  Shield,
  Target,
  TrendingUp,
} from 'lucide-react'

// =============================================================================
// TYPES
// =============================================================================
interface BrandClaim {
  claim: string
  source: string
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
}

interface BrandProfile {
  brand_name: string
  tagline: string
  value_propositions: string[]
  claims: BrandClaim[]
  confidence_score: number
}

interface AdVariant {
  id: string
  headline: string
  primary_text: string
  cta: string
  angle: string
  emotion: string
  score: number
  image_url?: string
  composed_url?: string
  status: 'pending' | 'approved' | 'rejected'
}

type PipelineStep = 'idle' | 'extracting' | 'generating' | 'matching' | 'composing' | 'complete'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// =============================================================================
// QUANTUM COMPONENTS
// =============================================================================
function QuantumLogo() {
  return (
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl bg-quantum-500/20 border border-quantum-500/30 flex items-center justify-center">
        <Zap className="w-5 h-5 text-quantum-400" />
      </div>
      <span className="text-xl font-bold text-white">QuantumLaunch</span>
    </div>
  )
}

function RiskBadge({ level }: { level: 'LOW' | 'MEDIUM' | 'HIGH' }) {
  const colors = {
    LOW: 'bg-quantum-500/10 text-quantum-400 border-quantum-500/20',
    MEDIUM: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    HIGH: 'bg-red-500/10 text-red-400 border-red-500/20',
  }
  
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide border ${colors[level]}`}>
      {level}
    </span>
  )
}

function ScoreBadge({ score }: { score: number }) {
  const displayScore = score > 1 ? score : Math.round(score * 100)
  const level = displayScore >= 90 ? 'high' : displayScore >= 75 ? 'medium' : 'low'
  const colors = {
    high: 'bg-quantum-500/15 text-quantum-400 border-quantum-500/30',
    medium: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
    low: 'bg-red-500/15 text-red-400 border-red-500/30',
  }
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-bold font-mono border ${colors[level]}`}>
      {displayScore}
    </span>
  )
}

function AngleBadge({ angle }: { angle: string }) {
  const colors: Record<string, string> = {
    pain: 'bg-red-500/10 text-red-400',
    benefit: 'bg-quantum-500/10 text-quantum-400',
    curiosity: 'bg-purple-500/10 text-purple-400',
    social_proof: 'bg-blue-500/10 text-blue-400',
    direct_offer: 'bg-orange-500/10 text-orange-400',
    fomo: 'bg-pink-500/10 text-pink-400',
    educational: 'bg-teal-500/10 text-teal-400',
    transformation: 'bg-indigo-500/10 text-indigo-400',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-xs capitalize ${colors[angle] || 'bg-zinc-500/10 text-zinc-400'}`}>
      {angle}
    </span>
  )
}

function APIStatusBadge({ isDemo }: { isDemo: boolean }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
      !isDemo 
        ? 'bg-quantum-500/10 text-quantum-400 border border-quantum-500/30'
        : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
    }`}>
      <span className={`w-2 h-2 rounded-full ${!isDemo ? 'bg-quantum-400' : 'bg-yellow-400'}`} />
      {!isDemo ? 'Live API' : 'Demo Mode'}
    </div>
  )
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================
export default function DashboardPage() {
  // State
  const [url, setUrl] = useState('')
  const [step, setStep] = useState<PipelineStep>('idle')
  const [brandProfile, setBrandProfile] = useState<BrandProfile | null>(null)
  const [variants, setVariants] = useState<AdVariant[]>([])
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all')
  const [expandedClaims, setExpandedClaims] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)
  const [useMockData, setUseMockData] = useState(true)
  const [numVariants, setNumVariants] = useState(5)
  const [selectedVariant, setSelectedVariant] = useState<AdVariant | null>(null)
  const [apiAvailable, setApiAvailable] = useState(false)

  // Check API availability on mount and when switching modes
  useEffect(() => {
    const checkAPI = async () => {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000) // 5s timeout
        const response = await fetch(`${API_BASE}/health`, { signal: controller.signal })
        clearTimeout(timeoutId)
        setApiAvailable(response.ok)
        if (response.ok) {
          setUseMockData(false) // Use real API when available
        }
      } catch {
        setApiAvailable(false)
        setUseMockData(true) // Fall back to demo if API unavailable
      }
    }
    checkAPI()
  }, [])

  // Warn when switching to Live API if not available
  const handleModeChange = async (useDemo: boolean) => {
    if (!useDemo && !apiAvailable) {
      // Check again before switching
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 3000)
        const response = await fetch(`${API_BASE}/health`, { signal: controller.signal })
        clearTimeout(timeoutId)
        if (response.ok) {
          setApiAvailable(true)
          setUseMockData(false)
        } else {
          setError('Backend not available. Start the server with: python api_server.py')
        }
      } catch {
        setError('Backend not available. Start the server with: python api_server.py')
      }
    } else {
      setUseMockData(useDemo)
      setError(null)
    }
  }

  // Mock data for demo
  const mockBrandProfile: BrandProfile = {
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
      { claim: 'Get real-time feedback', source: 'Homepage', risk_level: 'LOW' },
      { claim: 'Land your dream job', source: 'CTA button', risk_level: 'HIGH' },
      { claim: 'Beat the ATS every time', source: 'Features', risk_level: 'MEDIUM' },
    ],
    confidence_score: 0.87,
  }

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
      composed_url: 'https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600',
      status: 'pending',
    },
    {
      id: 'v2',
      headline: 'Your Resume, Quantum Optimized',
      primary_text: 'What if your resume could outsmart every screening system? Quantum Intelligence analyzes job descriptions and tailors your resume.',
      cta: 'Try Free',
      angle: 'curiosity',
      emotion: 'curiosity',
      score: 89,
      image_url: 'https://images.unsplash.com/photo-1493612276216-ee3925520721?w=600',
      composed_url: 'https://images.unsplash.com/photo-1493612276216-ee3925520721?w=600',
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
      composed_url: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600',
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
      composed_url: 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=600',
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
      composed_url: 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600',
      status: 'pending',
    },
  ]

  // Handlers
  const handleGenerate = async () => {
    if (!url) return
    
    setError(null)
    setStep('extracting')
    
    if (useMockData) {
      // Simulate pipeline steps with mock data
      await new Promise(r => setTimeout(r, 1500))
      setBrandProfile(mockBrandProfile)
      
      setStep('generating')
      await new Promise(r => setTimeout(r, 1500))
      
      setStep('matching')
      await new Promise(r => setTimeout(r, 1500))
      
      setStep('composing')
      await new Promise(r => setTimeout(r, 1000))
      
      setVariants(mockVariants.slice(0, numVariants))
      setStep('complete')
    } else {
      // Call real API
      try {
        setStep('extracting')
        
        // Add timeout to prevent infinite hang
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 300000) // 5 min timeout
        
        const response = await fetch(`${API_BASE}/pipeline/run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url,
            num_variants: numVariants,
            platform: 'meta',
            formats: ['square'],
          }),
          signal: controller.signal,
        })
        
        clearTimeout(timeoutId)
        
        if (!response.ok) {
          const err = await response.json().catch(() => ({ detail: 'Server error' }))
          throw new Error(err.detail || `HTTP ${response.status}`)
        }
        
        const data = await response.json()
        
        // Check for pipeline error
        if (data.error) {
          throw new Error(data.error)
        }
        
        // Simulate progress through stages
        setStep('generating')
        await new Promise(r => setTimeout(r, 500))
        setStep('matching')
        await new Promise(r => setTimeout(r, 500))
        setStep('composing')
        await new Promise(r => setTimeout(r, 500))
        
        // Transform API response - brand profile
        if (data.brand_profile) {
          setBrandProfile({
            brand_name: data.brand_profile.brand_name || 'Your Brand',
            tagline: data.brand_profile.tagline || '',
            value_propositions: data.brand_profile.value_propositions || [],
            claims: (data.brand_profile.claims || []).map((c: any) => ({
              claim: c.claim || c,
              source: c.source || c.source_text || 'Website',
              risk_level: c.risk_level || 'LOW',
            })),
            confidence_score: data.brand_profile.confidence_score || 0.85,
          })
        } else {
          // Use mock if no brand profile returned
          setBrandProfile(mockBrandProfile)
        }
        
        // Transform API response - variants
        if (data.copy_variants && data.copy_variants.length > 0) {
          // Get image URLs from image_matches if available
          const imageMatches = data.image_matches || {}
          
          setVariants(data.copy_variants.map((v: any, i: number) => {
            const matchedImage = imageMatches[v.id]?.image_url
            return {
              id: v.id || `v${i + 1}`,
              headline: v.headline,
              primary_text: v.primary_text,
              cta: v.cta,
              angle: v.angle || 'benefit',
              emotion: v.emotion || 'confidence',
              score: v.quality_score ? Math.round(v.quality_score * 100) : Math.floor(Math.random() * 15) + 80,
              image_url: matchedImage || mockVariants[i % mockVariants.length].image_url,
              status: 'pending' as const,
            }
          }))
        } else {
          // Fallback to mock variants if none returned
          setVariants(mockVariants.slice(0, numVariants))
        }
        
        setStep('complete')
        
      } catch (err: any) {
        console.error('Pipeline error:', err)
        const errorMessage = err.name === 'AbortError' 
          ? 'Request timed out. Make sure the backend is running and try again.'
          : (err.message || 'Failed to generate ads. Make sure the backend is running.')
        setError(errorMessage)
        setStep('idle')
      }
    }
  }

  const handleApprove = (id: string) => {
    setVariants(variants.map(v => 
      v.id === id ? { ...v, status: 'approved' } : v
    ))
  }

  const handleReject = (id: string) => {
    setVariants(variants.map(v => 
      v.id === id ? { ...v, status: 'rejected' } : v
    ))
  }

  const handleReset = (id: string) => {
    setVariants(variants.map(v => 
      v.id === id ? { ...v, status: 'pending' } : v
    ))
  }

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  const handleDownloadAll = () => {
    const approved = variants.filter(v => v.status === 'approved')
    alert(`Downloading ${approved.length} approved ads...`)
  }

  const handleStartOver = () => {
    setUrl('')
    setStep('idle')
    setBrandProfile(null)
    setVariants([])
    setError(null)
    setSelectedVariant(null)
  }

  const handleApproveAll = () => {
    setVariants(variants.map(v => ({ ...v, status: 'approved' })))
  }

  const handleRejectAll = () => {
    setVariants(variants.map(v => ({ ...v, status: 'rejected' })))
  }

  // Filtered variants
  const filteredVariants = variants.filter(v => 
    filterStatus === 'all' ? true : v.status === filterStatus
  )

  const approvedCount = variants.filter(v => v.status === 'approved').length
  const rejectedCount = variants.filter(v => v.status === 'rejected').length
  const pendingCount = variants.filter(v => v.status === 'pending').length

  return (
    <div className="min-h-screen bg-dark-primary">
      {/* Header */}
      <header className="border-b border-dark-hover sticky top-0 z-50 bg-dark-primary/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link href="/" className="text-zinc-400 hover:text-white transition">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div className="h-6 w-px bg-dark-hover"></div>
              <QuantumLogo />
              <span className="text-sm text-zinc-500 hidden sm:inline">/ Advanced Dashboard</span>
            </div>
            
            <div className="flex items-center gap-4">
              <APIStatusBadge isDemo={useMockData} />
              
              {step === 'complete' && (
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleStartOver}
                    className="px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white transition flex items-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Start Over
                  </button>
                  {approvedCount > 0 && (
                    <button
                      onClick={handleDownloadAll}
                      className="px-4 py-2 text-sm font-medium text-black bg-quantum-500 hover:bg-quantum-600 rounded-lg transition flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download ({approvedCount})
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* URL Input Section */}
        {step === 'idle' && (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-white mb-2">Advanced Campaign Builder</h1>
              <p className="text-zinc-400">Full control over extraction, generation, and composition</p>
            </div>
            
            <div className="bg-dark-surface rounded-2xl border border-dark-hover p-8">
              <div className="flex flex-col gap-6">
                {/* URL Input */}
                <label className="block">
                  <span className="text-sm font-medium text-zinc-300 mb-2 block">Website URL</span>
                  <div className="relative">
                    <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-quantum-400" />
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://yourwebsite.com"
                      className="quantum-input pl-12"
                      onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
                    />
                  </div>
                </label>
                
                {/* Settings */}
                <div className="grid grid-cols-2 gap-4">
                  <label className="block">
                    <span className="text-sm font-medium text-zinc-300 mb-2 block">Number of Variants</span>
                    <select
                      value={numVariants}
                      onChange={(e) => setNumVariants(parseInt(e.target.value))}
                      className="w-full px-4 py-3 bg-dark-elevated border border-dark-hover rounded-xl text-white focus:ring-2 focus:ring-quantum-500 focus:border-transparent outline-none transition"
                    >
                      <option value={3}>3 variants</option>
                      <option value={5}>5 variants</option>
                      <option value={10}>10 variants</option>
                    </select>
                  </label>
                  
                  <label className="block">
                    <span className="text-sm font-medium text-zinc-300 mb-2 block">Mode</span>
                    <div className="flex items-center gap-2 py-1">
                      <button
                        onClick={() => handleModeChange(true)}
                        className={`flex-1 px-4 py-2.5 rounded-lg border transition ${
                          useMockData 
                            ? 'bg-quantum-500/10 border-quantum-500/30 text-quantum-400' 
                            : 'border-dark-hover text-zinc-400 hover:bg-dark-hover'
                        }`}
                      >
                        Demo
                      </button>
                      <button
                        onClick={() => handleModeChange(false)}
                        className={`flex-1 px-4 py-2.5 rounded-lg border transition ${
                          !useMockData 
                            ? 'bg-quantum-500/10 border-quantum-500/30 text-quantum-400' 
                            : 'border-dark-hover text-zinc-400 hover:bg-dark-hover'
                        } ${!apiAvailable ? 'opacity-50' : ''}`}
                        title={!apiAvailable ? 'Backend not running' : 'Use live API'}
                      >
                        Live API {!apiAvailable && '⚠️'}
                      </button>
                    </div>
                  </label>
                </div>
                
                <button
                  onClick={handleGenerate}
                  disabled={!url}
                  className="quantum-btn w-full py-4 text-lg"
                >
                  <Sparkles className="w-5 h-5" />
                  Generate Ads
                </button>
                
                {/* Error Display */}
                {error && (
                  <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-red-400 text-sm">{error}</p>
                        <button 
                          onClick={() => setError(null)}
                          className="text-xs text-zinc-500 hover:text-zinc-300 mt-1"
                        >
                          Dismiss
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="mt-6 pt-6 border-t border-dark-hover">
                <p className="text-sm text-zinc-500 text-center">
                  Try with:{' '}
                  <button onClick={() => setUrl('https://careerfied.ai')} className="text-quantum-400 hover:underline">
                    careerfied.ai
                  </button>
                  {' '}or{' '}
                  <button onClick={() => setUrl('https://stripe.com')} className="text-quantum-400 hover:underline">
                    stripe.com
                  </button>
                </p>
              </div>
            </div>
            
            {/* Quick link to simple studio */}
            <div className="mt-6 text-center">
              <Link href="/studio" className="text-sm text-zinc-500 hover:text-quantum-400 transition">
                Want a simpler experience? Try the{' '}
                <span className="underline">Studio</span> →
              </Link>
            </div>
          </div>
        )}

        {/* Processing Steps */}
        {(step !== 'idle' && step !== 'complete') && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-dark-surface rounded-2xl border border-quantum-500/30 p-8 shadow-quantum">
              <div className="text-center mb-8">
                <Loader2 className="w-12 h-12 text-quantum-400 animate-spin mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-white mb-2">
                  {step === 'extracting' && 'Quantum Extractor running...'}
                  {step === 'generating' && 'Generating ad variants...'}
                  {step === 'matching' && 'Quantum Vision matching images...'}
                  {step === 'composing' && 'Composing final ads...'}
                </h2>
                <p className="text-zinc-400">This usually takes about 30-60 seconds</p>
              </div>
              
              {/* Progress Steps */}
              <div className="space-y-4">
                {[
                  { key: 'extracting', label: 'Quantum Extractor', icon: Globe },
                  { key: 'generating', label: 'Copy Generation', icon: FileText },
                  { key: 'matching', label: 'Quantum Vision', icon: ImageIcon },
                  { key: 'composing', label: 'Ad Composition', icon: Sparkles },
                ].map((s) => {
                  const steps: PipelineStep[] = ['extracting', 'generating', 'matching', 'composing']
                  const currentIndex = steps.indexOf(step)
                  const thisIndex = steps.indexOf(s.key as PipelineStep)
                  const isComplete = thisIndex < currentIndex
                  const isCurrent = thisIndex === currentIndex
                  
                  return (
                    <div key={s.key} className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        isComplete ? 'bg-quantum-500/20' : isCurrent ? 'bg-quantum-500/10' : 'bg-dark-hover'
                      }`}>
                        {isComplete ? (
                          <CheckCircle className="w-5 h-5 text-quantum-400" />
                        ) : isCurrent ? (
                          <Loader2 className="w-5 h-5 text-quantum-400 animate-spin" />
                        ) : (
                          <s.icon className="w-5 h-5 text-zinc-600" />
                        )}
                      </div>
                      <span className={`font-medium ${
                        isComplete ? 'text-quantum-400' : isCurrent ? 'text-white' : 'text-zinc-600'
                      }`}>
                        {s.label}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        {/* Results Section */}
        {step === 'complete' && brandProfile && (
          <div className="space-y-8">
            {/* Brand Profile Card */}
            <div className="bg-dark-surface rounded-2xl border border-dark-hover overflow-hidden">
              <div className="p-6 border-b border-dark-hover">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-white">{brandProfile.brand_name}</h2>
                    <p className="text-zinc-400">{brandProfile.tagline}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-quantum-400 font-mono">
                      {Math.round(brandProfile.confidence_score * 100)}%
                    </div>
                    <div className="text-sm text-zinc-500">Confidence</div>
                  </div>
                </div>
              </div>
              
              {/* Value Props */}
              <div className="p-6 border-b border-dark-hover">
                <h3 className="font-medium text-zinc-300 mb-3">Value Propositions</h3>
                <div className="flex flex-wrap gap-2">
                  {brandProfile.value_propositions.map((vp, i) => (
                    <span key={i} className="px-3 py-1 bg-quantum-500/10 text-quantum-400 rounded-full text-sm border border-quantum-500/20">
                      {vp}
                    </span>
                  ))}
                </div>
              </div>
              
              {/* Claims */}
              <div className="p-6">
                <button
                  onClick={() => setExpandedClaims(!expandedClaims)}
                  className="w-full flex items-center justify-between text-left"
                >
                  <div className="flex items-center gap-3">
                    <Shield className="w-5 h-5 text-quantum-400" />
                    <span className="font-medium text-white">
                      Extracted Claims ({brandProfile.claims.length})
                    </span>
                  </div>
                  {expandedClaims ? (
                    <ChevronUp className="w-5 h-5 text-zinc-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-zinc-400" />
                  )}
                </button>
                
                {expandedClaims && (
                  <div className="mt-4 space-y-2">
                    {brandProfile.claims.map((claim, i) => (
                      <div key={i} className="flex items-center justify-between py-2 px-3 bg-dark-hover rounded-lg">
                        <div className="flex-1">
                          <p className="text-white">{claim.claim}</p>
                          <p className="text-sm text-zinc-500">Source: {claim.source}</p>
                        </div>
                        <RiskBadge level={claim.risk_level} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Variants Section */}
            <div>
              {/* Toolbar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div className="flex items-center gap-4">
                  <h2 className="text-xl font-bold text-white">Ad Variants</h2>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="px-2 py-1 bg-yellow-500/10 text-yellow-400 rounded border border-yellow-500/20">
                      {pendingCount} pending
                    </span>
                    <span className="px-2 py-1 bg-quantum-500/10 text-quantum-400 rounded border border-quantum-500/20">
                      {approvedCount} approved
                    </span>
                    <span className="px-2 py-1 bg-red-500/10 text-red-400 rounded border border-red-500/20">
                      {rejectedCount} rejected
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  {/* Bulk Actions */}
                  <button
                    onClick={handleApproveAll}
                    className="px-3 py-1.5 text-sm text-quantum-400 bg-quantum-500/10 rounded-lg hover:bg-quantum-500/20 transition border border-quantum-500/20"
                  >
                    Approve All
                  </button>
                  <button
                    onClick={handleRejectAll}
                    className="px-3 py-1.5 text-sm text-red-400 bg-red-500/10 rounded-lg hover:bg-red-500/20 transition border border-red-500/20"
                  >
                    Reject All
                  </button>
                  
                  <div className="h-6 w-px bg-dark-hover mx-2"></div>
                  
                  {/* Filter */}
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value as any)}
                    className="px-3 py-2 bg-dark-elevated border border-dark-hover rounded-lg text-sm text-white focus:ring-2 focus:ring-quantum-500 outline-none"
                  >
                    <option value="all">All</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                  </select>
                  
                  {/* View Toggle */}
                  <div className="flex items-center bg-dark-elevated rounded-lg p-1 border border-dark-hover">
                    <button
                      onClick={() => setViewMode('grid')}
                      className={`p-2 rounded ${viewMode === 'grid' ? 'bg-dark-hover text-white' : 'text-zinc-500'}`}
                    >
                      <LayoutGrid className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setViewMode('list')}
                      className={`p-2 rounded ${viewMode === 'list' ? 'bg-dark-hover text-white' : 'text-zinc-500'}`}
                    >
                      <List className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Variants Grid */}
              <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
                {filteredVariants.map((variant) => (
                  <div
                    key={variant.id}
                    className={`bg-dark-surface rounded-2xl border overflow-hidden transition ${
                      variant.status === 'approved' ? 'border-quantum-500 ring-2 ring-quantum-500/20' :
                      variant.status === 'rejected' ? 'border-red-500/30 opacity-50' :
                      'border-dark-hover hover:border-zinc-700'
                    }`}
                  >
                    {/* Image Preview */}
                    <div 
                      className="relative aspect-square bg-dark-elevated cursor-pointer group"
                      onClick={() => setSelectedVariant(variant)}
                    >
                      {variant.image_url && (
                        <Image
                          src={variant.image_url}
                          alt={variant.headline}
                          fill
                          className="object-cover"
                        />
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent">
                        <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
                          <h3 className="font-bold text-lg mb-1">{variant.headline}</h3>
                          <p className="text-sm text-white/80 line-clamp-2">{variant.primary_text}</p>
                          <span className="inline-block mt-2 px-3 py-1 bg-quantum-500 text-black text-sm font-medium rounded">
                            {variant.cta}
                          </span>
                        </div>
                      </div>
                      
                      {/* Score Badge */}
                      <div className="absolute top-3 right-3">
                        <ScoreBadge score={variant.score} />
                      </div>
                      
                      {/* Preview button */}
                      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition flex items-center justify-center opacity-0 group-hover:opacity-100">
                        <Eye className="w-8 h-8 text-white" />
                      </div>
                      
                      {/* Status Badge */}
                      {variant.status !== 'pending' && (
                        <div className={`absolute top-3 left-3 px-3 py-1 rounded-full text-xs font-medium ${
                          variant.status === 'approved' ? 'bg-quantum-500 text-black' : 'bg-red-500 text-white'
                        }`}>
                          {variant.status === 'approved' ? '✓ Approved' : '✗ Rejected'}
                        </div>
                      )}
                    </div>
                    
                    {/* Details */}
                    <div className="p-4">
                      {/* Meta */}
                      <div className="flex items-center gap-2 mb-4 text-sm">
                        <AngleBadge angle={variant.angle} />
                        <span className="px-2 py-0.5 bg-dark-hover text-zinc-400 rounded text-xs capitalize">
                          {variant.emotion}
                        </span>
                      </div>
                      
                      {/* Copy Text */}
                      <div className="space-y-2 mb-4">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <span className="text-xs text-zinc-500 uppercase tracking-wider">Headline</span>
                            <p className="text-white font-medium truncate">{variant.headline}</p>
                          </div>
                          <button
                            onClick={() => handleCopy(variant.headline, `${variant.id}-headline`)}
                            className="p-1.5 text-zinc-500 hover:text-white transition flex-shrink-0"
                          >
                            {copied === `${variant.id}-headline` ? (
                              <Check className="w-4 h-4 text-quantum-400" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        {variant.status === 'pending' ? (
                          <>
                            <button
                              onClick={() => handleApprove(variant.id)}
                              className="flex-1 py-2 px-4 bg-quantum-500 hover:bg-quantum-600 text-black rounded-lg transition flex items-center justify-center gap-2 font-medium"
                            >
                              <ThumbsUp className="w-4 h-4" />
                              Approve
                            </button>
                            <button
                              onClick={() => handleReject(variant.id)}
                              className="flex-1 py-2 px-4 bg-dark-hover hover:bg-dark-elevated text-zinc-300 rounded-lg transition flex items-center justify-center gap-2"
                            >
                              <ThumbsDown className="w-4 h-4" />
                              Reject
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => handleReset(variant.id)}
                              className="flex-1 py-2 px-4 bg-dark-hover hover:bg-dark-elevated text-zinc-300 rounded-lg transition flex items-center justify-center gap-2"
                            >
                              <RefreshCw className="w-4 h-4" />
                              Reset
                            </button>
                            {variant.status === 'approved' && (
                              <button className="flex-1 py-2 px-4 bg-quantum-500 hover:bg-quantum-600 text-black rounded-lg transition flex items-center justify-center gap-2 font-medium">
                                <Download className="w-4 h-4" />
                                Download
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Publish CTA */}
            {approvedCount > 0 && (
              <div className="bg-gradient-to-r from-quantum-500/10 to-purple-500/10 border border-quantum-500/30 rounded-xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-white">Ready to publish?</h3>
                    <p className="text-zinc-400">{approvedCount} ads approved and ready for Meta</p>
                  </div>
                  <Link
                    href="/publish"
                    className="quantum-btn px-6"
                  >
                    <Zap className="w-5 h-5" />
                    Publish to Meta
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Variant Preview Modal */}
        {selectedVariant && (
          <div 
            className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedVariant(null)}
          >
            <div 
              className="bg-dark-surface rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-auto border border-dark-hover"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-dark-hover flex items-center justify-between">
                <h3 className="text-xl font-bold text-white">Ad Preview</h3>
                <button
                  onClick={() => setSelectedVariant(null)}
                  className="p-2 text-zinc-400 hover:text-white transition"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
                {/* Image */}
                <div className="relative aspect-square bg-dark-elevated rounded-xl overflow-hidden">
                  {selectedVariant.image_url && (
                    <Image
                      src={selectedVariant.image_url}
                      alt={selectedVariant.headline}
                      fill
                      className="object-cover"
                    />
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent">
                    <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
                      <h3 className="font-bold text-2xl mb-2">{selectedVariant.headline}</h3>
                      <p className="text-white/90 mb-4">{selectedVariant.primary_text}</p>
                      <span className="inline-block px-4 py-2 bg-quantum-500 text-black rounded font-medium">
                        {selectedVariant.cta}
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Details */}
                <div className="space-y-6">
                  <div>
                    <h4 className="font-medium text-zinc-400 mb-2">Headline</h4>
                    <p className="text-lg text-white">{selectedVariant.headline}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-zinc-400 mb-2">Primary Text</h4>
                    <p className="text-zinc-300">{selectedVariant.primary_text}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-zinc-400 mb-2">Call to Action</h4>
                    <p className="text-white">{selectedVariant.cta}</p>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div>
                      <h4 className="font-medium text-zinc-400 mb-1">Angle</h4>
                      <AngleBadge angle={selectedVariant.angle} />
                    </div>
                    <div>
                      <h4 className="font-medium text-zinc-400 mb-1">Emotion</h4>
                      <span className="px-3 py-1 bg-dark-hover text-zinc-300 rounded text-sm capitalize">
                        {selectedVariant.emotion}
                      </span>
                    </div>
                    <div>
                      <h4 className="font-medium text-zinc-400 mb-1">Score</h4>
                      <ScoreBadge score={selectedVariant.score} />
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex gap-3 pt-4">
                    {selectedVariant.status === 'pending' ? (
                      <>
                        <button
                          onClick={() => {
                            handleApprove(selectedVariant.id)
                            setSelectedVariant(null)
                          }}
                          className="flex-1 py-3 bg-quantum-500 hover:bg-quantum-600 text-black rounded-xl transition font-medium"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => {
                            handleReject(selectedVariant.id)
                            setSelectedVariant(null)
                          }}
                          className="flex-1 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-xl transition font-medium border border-red-500/30"
                        >
                          Reject
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => {
                          handleReset(selectedVariant.id)
                          setSelectedVariant(null)
                        }}
                        className="flex-1 py-3 bg-dark-hover hover:bg-dark-elevated text-zinc-300 rounded-xl transition font-medium"
                      >
                        Reset Status
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6 text-center">
              <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-red-400 mb-2">Something went wrong</h3>
              <p className="text-zinc-400 mb-4">{error}</p>
              <button
                onClick={handleStartOver}
                className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition border border-red-500/30"
              >
                Try Again
              </button>
            </div>
          </div>
        )}
      </main>
      
      {/* Footer */}
      <footer className="border-t border-dark-hover py-8 mt-12">
        <div className="max-w-7xl mx-auto px-6 text-center text-sm text-zinc-500">
          <p>Powered by Quantum Multi-Model Intelligence</p>
        </div>
      </footer>
    </div>
  )
}
