'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  ArrowLeft, 
  Search,
  TrendingUp,
  Eye,
  DollarSign,
  Target,
  Lightbulb,
  AlertTriangle,
  Loader2,
  AlertCircle,
  Building2,
  BarChart3,
  Zap,
  ChevronDown,
  ChevronRight,
  Plus
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface CompetitorProfile {
  page_id: string;
  page_name: string;
  total_ads: number;
  active_ads: number;
  estimated_monthly_spend: number;
  threat_level: string;
  ad_formats: Record<string, number>;
  top_themes: string[];
  common_ctas: string[];
}

interface CopyPattern {
  type: string;
  frequency: number;
  effectiveness: number;
  examples: string[];
}

interface Insight {
  type: string;
  title: string;
  description: string;
  action: string;
  priority: number;
  competitors: string[];
}

interface IntelResult {
  analysis_id: string;
  brand_name: string;
  industry: string;
  summary: string;
  market_overview: {
    total_competitor_ads: number;
    estimated_market_spend: number;
    dominant_platforms: string[];
    trending_formats: string[];
  };
  competitors: CompetitorProfile[];
  copy_intelligence: {
    patterns: CopyPattern[];
    overused_phrases: string[];
    underutilized_angles: string[];
  };
  visual_intelligence: {
    trends: { type: string; frequency: number; examples: string[] }[];
  };
  insights: Insight[];
  opportunities: string[];
  threats: string[];
  recommendations: string[];
}

export default function IntelPage() {
  const [brandName, setBrandName] = useState('Careerfied');
  const [industry, setIndustry] = useState('career');
  const [competitors, setCompetitors] = useState('Resume.io, Zety, Indeed');
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IntelResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['competitors', 'copy', 'insights']));

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const competitorList = competitors.split(',').map(c => c.trim()).filter(c => c);
      
      const response = await fetch(`${API_BASE}/intel/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_name: brandName,
          industry,
          competitor_names: competitorList.length > 0 ? competitorList : null,
        }),
      });

      if (!response.ok) throw new Error('Analysis failed');
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async (ind: string) => {
    setLoading(true);
    setError(null);
    setIndustry(ind);

    try {
      const response = await fetch(`${API_BASE}/intel/demo/${ind}`, { method: 'POST' });
      const demoData = await response.json();
      
      // Fetch full analysis
      const fullResponse = await fetch(`${API_BASE}/intel/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_name: demoData.brand_name || brandName,
          industry: ind,
        }),
      });
      const data = await fullResponse.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getThreatColor = (level: string) => {
    const colors: Record<string, string> = {
      low: 'text-green-400 bg-green-500/20',
      medium: 'text-yellow-400 bg-yellow-500/20',
      high: 'text-orange-400 bg-orange-500/20',
      critical: 'text-red-400 bg-red-500/20',
    };
    return colors[level] || 'text-gray-400 bg-gray-500/20';
  };

  const getInsightIcon = (type: string) => {
    if (type === 'opportunity') return <Lightbulb className="w-5 h-5 text-green-400" />;
    if (type === 'threat') return <AlertTriangle className="w-5 h-5 text-red-400" />;
    if (type === 'trend') return <TrendingUp className="w-5 h-5 text-blue-400" />;
    return <Target className="w-5 h-5 text-purple-400" />;
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-gray-400 hover:text-white">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <Eye className="w-5 h-5 text-purple-400" />
              Competitor Intelligence
            </h1>
            <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">
              Slice 12
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Input */}
          <div className="space-y-6">
            {/* Quick Demo */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Quick Demo</h2>
              <div className="grid grid-cols-3 gap-2">
                {['career', 'saas', 'ecommerce'].map((ind) => (
                  <button
                    key={ind}
                    onClick={() => handleDemo(ind)}
                    disabled={loading}
                    className="py-2 px-3 bg-purple-500/20 text-purple-400 rounded text-sm font-medium hover:bg-purple-500/30 transition capitalize"
                  >
                    {ind}
                  </button>
                ))}
              </div>
            </div>

            {/* Analysis Settings */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Analysis Settings</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Your Brand Name</label>
                  <input
                    type="text"
                    value={brandName}
                    onChange={(e) => setBrandName(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-purple-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Industry</label>
                  <select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-purple-500"
                  >
                    <option value="career">Career & Recruiting</option>
                    <option value="saas">SaaS & Software</option>
                    <option value="ecommerce">E-commerce</option>
                    <option value="fintech">Fintech</option>
                    <option value="edtech">EdTech</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Competitors (comma-separated)</label>
                  <textarea
                    value={competitors}
                    onChange={(e) => setCompetitors(e.target.value)}
                    rows={2}
                    placeholder="e.g., Competitor A, Competitor B"
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>
            </div>

            {/* Analyze Button */}
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-400 hover:to-pink-400 rounded-lg font-medium disabled:opacity-50 transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Analyze Competitors
                </>
              )}
            </button>
          </div>

          {/* Right Columns - Results */}
          <div className="lg:col-span-2 space-y-6">
            {/* Error */}
            {error && (
              <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 text-red-400">
                  <AlertCircle className="w-5 h-5" />
                  <p>{error}</p>
                </div>
              </div>
            )}

            {/* Placeholder */}
            {!result && !loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <Eye className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-400 mb-2">No analysis yet</h3>
                <p className="text-gray-500">Enter your brand and competitors to analyze</p>
              </div>
            )}

            {/* Loading */}
            {loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <Loader2 className="w-16 h-16 text-purple-500 mx-auto mb-4 animate-spin" />
                <h3 className="text-lg font-medium text-gray-300 mb-2">Analyzing competitors...</h3>
                <p className="text-gray-500">Fetching ads and patterns from Meta Ads Library</p>
              </div>
            )}

            {/* Results */}
            {result && !loading && (
              <>
                {/* Market Overview */}
                <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 border border-purple-500/30 rounded-lg p-6">
                  <h3 className="font-semibold mb-4">Market Overview</h3>
                  <div className="grid grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-400">{result.competitors.length}</div>
                      <div className="text-sm text-gray-400">Competitors</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-pink-400">{result.market_overview.total_competitor_ads}</div>
                      <div className="text-sm text-gray-400">Total Ads</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-400">${(result.market_overview.estimated_market_spend / 1000).toFixed(0)}K</div>
                      <div className="text-sm text-gray-400">Market Spend/mo</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-400">{result.market_overview.trending_formats[0] || 'Image'}</div>
                      <div className="text-sm text-gray-400">Top Format</div>
                    </div>
                  </div>
                </div>

                {/* Competitors Section */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg">
                  <button
                    onClick={() => toggleSection('competitors')}
                    className="w-full p-4 flex items-center justify-between hover:bg-gray-800/50 transition"
                  >
                    <div className="flex items-center gap-3">
                      <Building2 className="w-5 h-5 text-blue-400" />
                      <span className="font-semibold">Competitors ({result.competitors.length})</span>
                    </div>
                    {expandedSections.has('competitors') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                  </button>
                  
                  {expandedSections.has('competitors') && (
                    <div className="border-t border-gray-800 p-4 space-y-3">
                      {result.competitors.map((comp, i) => (
                        <div key={i} className="bg-gray-800 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="font-medium">{comp.page_name}</div>
                            <span className={`text-xs px-2 py-1 rounded ${getThreatColor(comp.threat_level)}`}>
                              {comp.threat_level.toUpperCase()} THREAT
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="text-gray-400">Ads:</span>
                              <span className="ml-2">{comp.total_ads}</span>
                            </div>
                            <div>
                              <span className="text-gray-400">Spend:</span>
                              <span className="ml-2 text-green-400">${comp.estimated_monthly_spend.toLocaleString()}/mo</span>
                            </div>
                            <div>
                              <span className="text-gray-400">CTAs:</span>
                              <span className="ml-2">{comp.common_ctas.slice(0, 2).join(', ')}</span>
                            </div>
                          </div>
                          {comp.top_themes.length > 0 && (
                            <div className="mt-2 flex gap-2 flex-wrap">
                              {comp.top_themes.map((theme, j) => (
                                <span key={j} className="text-xs bg-gray-700 px-2 py-1 rounded">{theme}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Copy Intelligence Section */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg">
                  <button
                    onClick={() => toggleSection('copy')}
                    className="w-full p-4 flex items-center justify-between hover:bg-gray-800/50 transition"
                  >
                    <div className="flex items-center gap-3">
                      <BarChart3 className="w-5 h-5 text-yellow-400" />
                      <span className="font-semibold">Copy Intelligence</span>
                    </div>
                    {expandedSections.has('copy') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                  </button>
                  
                  {expandedSections.has('copy') && (
                    <div className="border-t border-gray-800 p-4 space-y-4">
                      {/* Patterns */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-400 mb-2">Copy Patterns Used</h4>
                        <div className="space-y-2">
                          {result.copy_intelligence.patterns.map((pattern, i) => (
                            <div key={i} className="bg-gray-800 rounded p-3">
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-medium capitalize">{pattern.type.replace('_', ' ')}</span>
                                <div className="flex items-center gap-2">
                                  <span className="text-sm text-gray-400">{pattern.frequency}x used</span>
                                  <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                                    {(pattern.effectiveness * 100).toFixed(0)}% effective
                                  </span>
                                </div>
                              </div>
                              <div className="text-xs text-gray-500 truncate">{pattern.examples[0]}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Overused & Underutilized */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h4 className="text-sm font-medium text-red-400 mb-2">⚠️ Overused Phrases</h4>
                          <ul className="text-sm space-y-1">
                            {result.copy_intelligence.overused_phrases.slice(0, 3).map((phrase, i) => (
                              <li key={i} className="text-gray-400">• {phrase}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-green-400 mb-2">✨ Underutilized Angles</h4>
                          <ul className="text-sm space-y-1">
                            {result.copy_intelligence.underutilized_angles.slice(0, 3).map((angle, i) => (
                              <li key={i} className="text-gray-400">• {angle}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Insights Section */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg">
                  <button
                    onClick={() => toggleSection('insights')}
                    className="w-full p-4 flex items-center justify-between hover:bg-gray-800/50 transition"
                  >
                    <div className="flex items-center gap-3">
                      <Zap className="w-5 h-5 text-green-400" />
                      <span className="font-semibold">Insights ({result.insights.length})</span>
                    </div>
                    {expandedSections.has('insights') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                  </button>
                  
                  {expandedSections.has('insights') && (
                    <div className="border-t border-gray-800 p-4 space-y-3">
                      {result.insights.map((insight, i) => (
                        <div key={i} className="bg-gray-800 rounded-lg p-4">
                          <div className="flex items-start gap-3">
                            {getInsightIcon(insight.type)}
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium">{insight.title}</span>
                                <span className="text-xs bg-gray-700 px-2 py-0.5 rounded">P{insight.priority}</span>
                              </div>
                              <p className="text-sm text-gray-400 mb-2">{insight.description}</p>
                              <p className="text-sm text-green-400">→ {insight.action}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Recommendations */}
                <div className="bg-gradient-to-r from-green-900/30 to-emerald-900/30 border border-green-500/30 rounded-lg p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <Target className="w-5 h-5 text-green-400" />
                    Strategic Recommendations
                  </h3>
                  <ul className="space-y-2">
                    {result.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <span className="text-green-400 mt-1">✓</span>
                        <span className="text-gray-300">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Opportunities & Threats */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <h4 className="font-medium text-green-400 mb-3">✨ Opportunities</h4>
                    <ul className="text-sm space-y-2">
                      {result.opportunities.slice(0, 3).map((opp, i) => (
                        <li key={i} className="text-gray-400">• {opp}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <h4 className="font-medium text-red-400 mb-3">⚠️ Threats</h4>
                    <ul className="text-sm space-y-2">
                      {result.threats.length > 0 ? result.threats.map((threat, i) => (
                        <li key={i} className="text-gray-400">• {threat}</li>
                      )) : (
                        <li className="text-gray-500">No immediate threats detected</li>
                      )}
                    </ul>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
