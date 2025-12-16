'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Search,
  TrendingUp,
  Eye,
  DollarSign,
  Target,
  Lightbulb,
  AlertTriangle,
  AlertCircle,
  Building2,
  BarChart3,
  Zap,
  ChevronDown,
  ChevronRight,
  Sparkles
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

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

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
      low: 'text-quantum-400 bg-quantum-500/20 border border-quantum-500/30',
      medium: 'text-yellow-400 bg-yellow-500/20 border border-yellow-500/30',
      high: 'text-orange-400 bg-orange-500/20 border border-orange-500/30',
      critical: 'text-red-400 bg-red-500/20 border border-red-500/30',
    };
    return colors[level] || 'text-zinc-400 bg-zinc-500/20';
  };

  const getInsightIcon = (type: string) => {
    if (type === 'opportunity') return <Lightbulb className="w-5 h-5 text-quantum-400" />;
    if (type === 'threat') return <AlertTriangle className="w-5 h-5 text-red-400" />;
    if (type === 'trend') return <TrendingUp className="w-5 h-5 text-blue-400" />;
    return <Target className="w-5 h-5 text-purple-400" />;
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <motion.header
        className="border-b border-zinc-800 px-6 py-4 backdrop-blur-xl bg-zinc-900/50 sticky top-0 z-50"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/tools" className="text-zinc-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <Eye className="w-4 h-4 text-white" />
              </div>
              Competitor Intelligence
            </h1>
            <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded font-mono">
              AI-POWERED
            </span>
          </div>
        </div>
      </motion.header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Input */}
          <motion.div
            className="space-y-6"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {/* Quick Demo */}
            <motion.div
              className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors"
              variants={itemVariants}
            >
              <h2 className="text-lg font-semibold mb-4">Quick Demo</h2>
              <div className="grid grid-cols-3 gap-2">
                {['career', 'saas', 'ecommerce'].map((ind) => (
                  <motion.button
                    key={ind}
                    onClick={() => handleDemo(ind)}
                    disabled={loading}
                    className="py-2.5 px-3 bg-purple-500/20 text-purple-400 rounded-lg text-sm font-medium hover:bg-purple-500/30 transition-all capitalize border border-purple-500/30"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {ind}
                  </motion.button>
                ))}
              </div>
            </motion.div>

            {/* Analysis Settings */}
            <motion.div
              className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors"
              variants={itemVariants}
            >
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-purple-400" />
                Analysis Settings
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Your Brand Name</label>
                  <input
                    type="text"
                    value={brandName}
                    onChange={(e) => setBrandName(e.target.value)}
                    className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/50 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Industry</label>
                  <select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-purple-500 transition-all"
                  >
                    <option value="career">Career & Recruiting</option>
                    <option value="saas">SaaS & Software</option>
                    <option value="ecommerce">E-commerce</option>
                    <option value="fintech">Fintech</option>
                    <option value="edtech">EdTech</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Competitors (comma-separated)</label>
                  <textarea
                    value={competitors}
                    onChange={(e) => setCompetitors(e.target.value)}
                    rows={2}
                    placeholder="e.g., Competitor A, Competitor B"
                    className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-purple-500 transition-all"
                  />
                </div>
              </div>
            </motion.div>

            {/* Analyze Button */}
            <motion.div variants={itemVariants}>
              <motion.button
                onClick={handleAnalyze}
                disabled={loading}
                className="w-full py-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-400 hover:to-pink-400 rounded-xl font-semibold disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                {loading ? (
                  <>
                    <motion.div
                      className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Analyze Competitors
                  </>
                )}
              </motion.button>
            </motion.div>
          </motion.div>

          {/* Right Columns - Results */}
          <div className="lg:col-span-2 space-y-6">
            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  className="bg-red-900/30 border border-red-500/30 rounded-xl p-4"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <div className="flex items-center gap-2 text-red-400">
                    <AlertCircle className="w-5 h-5" />
                    <p>{error}</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Placeholder */}
            {!result && !loading && (
              <motion.div
                className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-12 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className="w-20 h-20 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Eye className="w-10 h-10 text-zinc-600" />
                </div>
                <h3 className="text-lg font-medium text-zinc-400 mb-2">No analysis yet</h3>
                <p className="text-zinc-500">Enter your brand and competitors to analyze</p>
              </motion.div>
            )}

            {/* Loading */}
            {loading && (
              <motion.div
                className="bg-zinc-900/80 border border-purple-500/30 rounded-xl p-12 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <motion.div
                  className="w-20 h-20 mx-auto mb-4 relative"
                  animate={{
                    boxShadow: ['0 0 20px rgba(168,85,247,0.3)', '0 0 40px rgba(168,85,247,0.5)', '0 0 20px rgba(168,85,247,0.3)']
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <motion.div
                    className="w-full h-full border-4 border-purple-500/30 border-t-purple-500 rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                  />
                  <Eye className="w-8 h-8 text-purple-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                </motion.div>
                <h3 className="text-lg font-medium text-zinc-300 mb-2">Analyzing competitors...</h3>
                <p className="text-zinc-500">Fetching ads and patterns from Meta Ads Library</p>
              </motion.div>
            )}

            {/* Results */}
            <AnimatePresence>
              {result && !loading && (
                <motion.div
                  className="space-y-6"
                  variants={containerVariants}
                  initial="hidden"
                  animate="visible"
                >
                  {/* Market Overview */}
                  <motion.div
                    className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 border border-purple-500/30 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4">Market Overview</h3>
                    <div className="grid grid-cols-4 gap-4">
                      {[
                        { value: result.competitors.length, label: 'Competitors', color: 'text-purple-400' },
                        { value: result.market_overview.total_competitor_ads, label: 'Total Ads', color: 'text-pink-400' },
                        { value: `$${(result.market_overview.estimated_market_spend / 1000).toFixed(0)}K`, label: 'Market Spend/mo', color: 'text-quantum-400' },
                        { value: result.market_overview.trending_formats[0] || 'Image', label: 'Top Format', color: 'text-blue-400' },
                      ].map((stat, i) => (
                        <motion.div
                          key={stat.label}
                          className="text-center"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.1 }}
                        >
                          <div className={`text-2xl font-bold font-mono ${stat.color}`}>{stat.value}</div>
                          <div className="text-sm text-zinc-400">{stat.label}</div>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>

                  {/* Competitors Section */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl overflow-hidden"
                    variants={itemVariants}
                  >
                    <button
                      onClick={() => toggleSection('competitors')}
                      className="w-full p-4 flex items-center justify-between hover:bg-zinc-800/50 transition"
                    >
                      <div className="flex items-center gap-3">
                        <Building2 className="w-5 h-5 text-blue-400" />
                        <span className="font-semibold">Competitors ({result.competitors.length})</span>
                      </div>
                      {expandedSections.has('competitors') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                    </button>

                    <AnimatePresence>
                      {expandedSections.has('competitors') && (
                        <motion.div
                          className="border-t border-zinc-800 p-4 space-y-3"
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                        >
                          {result.competitors.map((comp, i) => (
                            <motion.div
                              key={i}
                              className="bg-zinc-800/50 rounded-lg p-4 hover:bg-zinc-800 transition-colors"
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: i * 0.1 }}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <div className="font-medium">{comp.page_name}</div>
                                <span className={`text-xs px-2 py-1 rounded-lg ${getThreatColor(comp.threat_level)}`}>
                                  {comp.threat_level.toUpperCase()} THREAT
                                </span>
                              </div>
                              <div className="grid grid-cols-3 gap-4 text-sm">
                                <div>
                                  <span className="text-zinc-400">Ads:</span>
                                  <span className="ml-2 font-mono">{comp.total_ads}</span>
                                </div>
                                <div>
                                  <span className="text-zinc-400">Spend:</span>
                                  <span className="ml-2 text-quantum-400 font-mono">${comp.estimated_monthly_spend.toLocaleString()}/mo</span>
                                </div>
                                <div>
                                  <span className="text-zinc-400">CTAs:</span>
                                  <span className="ml-2">{comp.common_ctas.slice(0, 2).join(', ')}</span>
                                </div>
                              </div>
                              {comp.top_themes.length > 0 && (
                                <div className="mt-2 flex gap-2 flex-wrap">
                                  {comp.top_themes.map((theme, j) => (
                                    <span key={j} className="text-xs bg-zinc-700 px-2 py-1 rounded-lg">{theme}</span>
                                  ))}
                                </div>
                              )}
                            </motion.div>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>

                  {/* Copy Intelligence Section */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl overflow-hidden"
                    variants={itemVariants}
                  >
                    <button
                      onClick={() => toggleSection('copy')}
                      className="w-full p-4 flex items-center justify-between hover:bg-zinc-800/50 transition"
                    >
                      <div className="flex items-center gap-3">
                        <BarChart3 className="w-5 h-5 text-yellow-400" />
                        <span className="font-semibold">Copy Intelligence</span>
                      </div>
                      {expandedSections.has('copy') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                    </button>

                    <AnimatePresence>
                      {expandedSections.has('copy') && (
                        <motion.div
                          className="border-t border-zinc-800 p-4 space-y-4"
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                        >
                          {/* Patterns */}
                          <div>
                            <h4 className="text-sm font-medium text-zinc-400 mb-2">Copy Patterns Used</h4>
                            <div className="space-y-2">
                              {result.copy_intelligence.patterns.map((pattern, i) => (
                                <motion.div
                                  key={i}
                                  className="bg-zinc-800/50 rounded-lg p-3"
                                  initial={{ opacity: 0, x: -10 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ delay: i * 0.1 }}
                                >
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="font-medium capitalize">{pattern.type.replace('_', ' ')}</span>
                                    <div className="flex items-center gap-2">
                                      <span className="text-sm text-zinc-400 font-mono">{pattern.frequency}x used</span>
                                      <span className="text-xs bg-quantum-500/20 text-quantum-400 px-2 py-0.5 rounded-lg">
                                        {(pattern.effectiveness * 100).toFixed(0)}% effective
                                      </span>
                                    </div>
                                  </div>
                                  <div className="text-xs text-zinc-500 truncate">{pattern.examples[0]}</div>
                                </motion.div>
                              ))}
                            </div>
                          </div>

                          {/* Overused & Underutilized */}
                          <div className="grid grid-cols-2 gap-4">
                            <div className="bg-red-900/10 border border-red-500/20 rounded-lg p-4">
                              <h4 className="text-sm font-medium text-red-400 mb-2 flex items-center gap-1">
                                <AlertTriangle className="w-4 h-4" />
                                Overused Phrases
                              </h4>
                              <ul className="text-sm space-y-1">
                                {result.copy_intelligence.overused_phrases.slice(0, 3).map((phrase, i) => (
                                  <li key={i} className="text-zinc-400">- {phrase}</li>
                                ))}
                              </ul>
                            </div>
                            <div className="bg-quantum-900/10 border border-quantum-500/20 rounded-lg p-4">
                              <h4 className="text-sm font-medium text-quantum-400 mb-2 flex items-center gap-1">
                                <Lightbulb className="w-4 h-4" />
                                Underutilized Angles
                              </h4>
                              <ul className="text-sm space-y-1">
                                {result.copy_intelligence.underutilized_angles.slice(0, 3).map((angle, i) => (
                                  <li key={i} className="text-zinc-400">+ {angle}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>

                  {/* Insights Section */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl overflow-hidden"
                    variants={itemVariants}
                  >
                    <button
                      onClick={() => toggleSection('insights')}
                      className="w-full p-4 flex items-center justify-between hover:bg-zinc-800/50 transition"
                    >
                      <div className="flex items-center gap-3">
                        <Zap className="w-5 h-5 text-quantum-400" />
                        <span className="font-semibold">Insights ({result.insights.length})</span>
                      </div>
                      {expandedSections.has('insights') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                    </button>

                    <AnimatePresence>
                      {expandedSections.has('insights') && (
                        <motion.div
                          className="border-t border-zinc-800 p-4 space-y-3"
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                        >
                          {result.insights.map((insight, i) => (
                            <motion.div
                              key={i}
                              className="bg-zinc-800/50 rounded-lg p-4 hover:bg-zinc-800 transition-colors"
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: i * 0.1 }}
                            >
                              <div className="flex items-start gap-3">
                                {getInsightIcon(insight.type)}
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="font-medium">{insight.title}</span>
                                    <span className="text-xs bg-zinc-700 px-2 py-0.5 rounded-lg font-mono">P{insight.priority}</span>
                                  </div>
                                  <p className="text-sm text-zinc-400 mb-2">{insight.description}</p>
                                  <p className="text-sm text-quantum-400">+ {insight.action}</p>
                                </div>
                              </div>
                            </motion.div>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>

                  {/* Recommendations */}
                  <motion.div
                    className="bg-gradient-to-r from-quantum-900/20 to-emerald-900/20 border border-quantum-500/30 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                      <Target className="w-5 h-5 text-quantum-400" />
                      Strategic Recommendations
                    </h3>
                    <ul className="space-y-2">
                      {result.recommendations.map((rec, i) => (
                        <motion.li
                          key={i}
                          className="flex items-start gap-2 text-sm"
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.1 }}
                        >
                          <span className="text-quantum-400 mt-0.5">+</span>
                          <span className="text-zinc-300">{rec}</span>
                        </motion.li>
                      ))}
                    </ul>
                  </motion.div>

                  {/* Opportunities & Threats */}
                  <motion.div className="grid grid-cols-2 gap-4" variants={itemVariants}>
                    <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4">
                      <h4 className="font-medium text-quantum-400 mb-3 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4" />
                        Opportunities
                      </h4>
                      <ul className="text-sm space-y-2">
                        {result.opportunities.slice(0, 3).map((opp, i) => (
                          <motion.li
                            key={i}
                            className="text-zinc-400"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: i * 0.1 }}
                          >
                            + {opp}
                          </motion.li>
                        ))}
                      </ul>
                    </div>
                    <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4">
                      <h4 className="font-medium text-red-400 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        Threats
                      </h4>
                      <ul className="text-sm space-y-2">
                        {result.threats.length > 0 ? result.threats.map((threat, i) => (
                          <motion.li
                            key={i}
                            className="text-zinc-400"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: i * 0.1 }}
                          >
                            ! {threat}
                          </motion.li>
                        )) : (
                          <li className="text-zinc-500">No immediate threats detected</li>
                        )}
                      </ul>
                    </div>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
}
