'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Clock,
  TrendingDown,
  AlertTriangle,
  RefreshCw,
  AlertCircle,
  Calendar,
  Target,
  Users,
  DollarSign,
  Zap,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { ScoreOrb, ProgressBar } from '@/components/ui';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FatigueResult {
  ad_id: string;
  fatigue_score: number;
  fatigue_level: string;
  summary: string;
  days_until_fatigue: number;
  refresh_urgency: string;
  metrics: {
    ctr_decline_percent: number;
    cpm_increase_percent: number;
    frequency_risk: number;
    audience_saturation: number;
  };
  decay: {
    pattern: string;
    rate_percent_per_day: number;
  };
  projections_7d: {
    ctr: number;
    cpm: number;
    frequency: number;
  };
  recommendations: string[];
  refresh_strategies: string[];
  optimal_refresh_date: string;
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

export default function FatiguePage() {
  const [adId, setAdId] = useState('careerfied_ad_001');
  const [daysRunning, setDaysRunning] = useState(14);
  const [frequency, setFrequency] = useState(2.5);
  const [reach, setReach] = useState(45000);
  const [audienceSize, setAudienceSize] = useState(150000);
  const [industry, setIndustry] = useState('saas');

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FatigueResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/fatigue/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ad_id: adId,
          days_running: daysRunning,
          frequency,
          reach,
          audience_size: audienceSize,
          industry,
        }),
      });

      if (!response.ok) throw new Error('Prediction failed');
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async (scenario: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/fatigue/demo/${scenario}`, {
        method: 'POST',
      });
      const data = await response.json();

      const daysMap: Record<string, number> = { fresh: 3, healthy: 10, moderate: 18, high: 25, critical: 35 };
      const freqMap: Record<string, number> = { fresh: 1.2, healthy: 2.0, moderate: 3.0, high: 4.0, critical: 5.5 };
      setDaysRunning(daysMap[scenario] || 14);
      setFrequency(freqMap[scenario] || 2.5);

      const fullResponse = await fetch(`${API_BASE}/fatigue/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ad_id: `demo_${scenario}`,
          days_running: daysMap[scenario],
          frequency: freqMap[scenario],
          reach: daysMap[scenario] * 3000,
          audience_size: 150000,
          industry: 'saas',
        }),
      });
      const fullData = await fullResponse.json();
      setResult(fullData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getFatigueColor = (level: string) => {
    const colors: Record<string, string> = {
      fresh: 'text-quantum-400',
      healthy: 'text-blue-400',
      moderate: 'text-yellow-400',
      high: 'text-orange-400',
      critical: 'text-red-400',
    };
    return colors[level] || 'text-zinc-400';
  };

  const getFatigueBg = (level: string) => {
    const colors: Record<string, string> = {
      fresh: 'bg-quantum-500/10 border-quantum-500/30',
      healthy: 'bg-blue-500/10 border-blue-500/30',
      moderate: 'bg-yellow-500/10 border-yellow-500/30',
      high: 'bg-orange-500/10 border-orange-500/30',
      critical: 'bg-red-500/10 border-red-500/30',
    };
    return colors[level] || 'bg-zinc-500/10';
  };

  const getUrgencyBadge = (urgency: string) => {
    const badges: Record<string, { color: string; text: string }> = {
      none: { color: 'bg-quantum-500/20 text-quantum-400', text: 'No Action' },
      plan: { color: 'bg-blue-500/20 text-blue-400', text: 'Plan Refresh' },
      prepare: { color: 'bg-yellow-500/20 text-yellow-400', text: 'Prepare Creative' },
      urgent: { color: 'bg-orange-500/20 text-orange-400', text: 'Urgent' },
      immediate: { color: 'bg-red-500/20 text-red-400', text: 'Immediate!' },
    };
    return badges[urgency] || badges.none;
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
              <div className="w-8 h-8 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
                <Clock className="w-4 h-4 text-white" />
              </div>
              Creative Fatigue Predictor
            </h1>
            <span className="text-xs bg-orange-500/20 text-orange-400 px-2 py-1 rounded font-mono">
              AI-POWERED
            </span>
          </div>
        </div>
      </motion.header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Input */}
          <motion.div
            className="space-y-6"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {/* Quick Demo Scenarios */}
            <motion.div
              className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors"
              variants={itemVariants}
            >
              <h2 className="text-lg font-semibold mb-4">Quick Demo Scenarios</h2>
              <div className="grid grid-cols-5 gap-2">
                {['fresh', 'healthy', 'moderate', 'high', 'critical'].map((scenario) => (
                  <motion.button
                    key={scenario}
                    onClick={() => handleDemo(scenario)}
                    disabled={loading}
                    className={`py-2.5 px-3 rounded-lg text-xs font-medium transition-all ${
                      scenario === 'fresh' ? 'bg-quantum-500/20 text-quantum-400 hover:bg-quantum-500/30 border border-quantum-500/30' :
                      scenario === 'healthy' ? 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 border border-blue-500/30' :
                      scenario === 'moderate' ? 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 border border-yellow-500/30' :
                      scenario === 'high' ? 'bg-orange-500/20 text-orange-400 hover:bg-orange-500/30 border border-orange-500/30' :
                      'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {scenario.charAt(0).toUpperCase() + scenario.slice(1)}
                  </motion.button>
                ))}
              </div>
            </motion.div>

            {/* Ad Performance Data */}
            <motion.div
              className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors"
              variants={itemVariants}
            >
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-orange-400" />
                Ad Performance Data
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Ad ID</label>
                  <input
                    type="text"
                    value={adId}
                    onChange={(e) => setAdId(e.target.value)}
                    className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500/50 transition-all font-mono"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">Days Running</label>
                    <input
                      type="number"
                      value={daysRunning}
                      onChange={(e) => setDaysRunning(parseInt(e.target.value) || 0)}
                      min={1}
                      max={90}
                      className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-orange-500 transition-all font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">Frequency</label>
                    <input
                      type="number"
                      value={frequency}
                      onChange={(e) => setFrequency(parseFloat(e.target.value) || 1)}
                      step={0.1}
                      min={1}
                      max={10}
                      className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-orange-500 transition-all font-mono"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">Reach</label>
                    <input
                      type="number"
                      value={reach}
                      onChange={(e) => setReach(parseInt(e.target.value) || 0)}
                      className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-orange-500 transition-all font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">Audience Size</label>
                    <input
                      type="number"
                      value={audienceSize}
                      onChange={(e) => setAudienceSize(parseInt(e.target.value) || 0)}
                      className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-orange-500 transition-all font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Industry</label>
                  <select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-orange-500 transition-all"
                  >
                    <option value="general">General</option>
                    <option value="ecommerce">E-commerce</option>
                    <option value="saas">SaaS</option>
                    <option value="finance">Finance</option>
                    <option value="entertainment">Entertainment</option>
                    <option value="travel">Travel</option>
                    <option value="healthcare">Healthcare</option>
                    <option value="education">Education</option>
                    <option value="real_estate">Real Estate</option>
                    <option value="retail">Retail</option>
                  </select>
                </div>
              </div>
            </motion.div>

            {/* Actions */}
            <motion.div variants={itemVariants}>
              <motion.button
                onClick={handlePredict}
                disabled={loading}
                className="w-full py-4 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-400 hover:to-red-400 rounded-xl font-semibold disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-lg shadow-orange-500/25 hover:shadow-orange-500/40"
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
                    Predicting...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Predict Fatigue
                  </>
                )}
              </motion.button>
            </motion.div>
          </motion.div>

          {/* Right Column - Results */}
          <div className="space-y-6">
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
                  <Clock className="w-10 h-10 text-zinc-600" />
                </div>
                <h3 className="text-lg font-medium text-zinc-400 mb-2">No prediction yet</h3>
                <p className="text-zinc-500">Enter ad data or try a demo scenario</p>
              </motion.div>
            )}

            {/* Loading */}
            {loading && (
              <motion.div
                className="bg-zinc-900/80 border border-orange-500/30 rounded-xl p-12 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <motion.div
                  className="w-20 h-20 mx-auto mb-4 relative"
                  animate={{
                    boxShadow: ['0 0 20px rgba(249,115,22,0.3)', '0 0 40px rgba(249,115,22,0.5)', '0 0 20px rgba(249,115,22,0.3)']
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <motion.div
                    className="w-full h-full border-4 border-orange-500/30 border-t-orange-500 rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                  />
                  <Clock className="w-8 h-8 text-orange-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                </motion.div>
                <h3 className="text-lg font-medium text-zinc-300 mb-2">Analyzing fatigue patterns...</h3>
                <p className="text-zinc-500">Calculating decay rates and projections</p>
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
                  {/* Main Score Card */}
                  <motion.div
                    className={`border rounded-xl p-6 ${getFatigueBg(result.fatigue_level)}`}
                    variants={itemVariants}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <div className="text-sm text-zinc-400 mb-2">Fatigue Score</div>
                        <ScoreOrb score={100 - result.fatigue_score} size="md" animate />
                        <div className={`text-lg font-medium ${getFatigueColor(result.fatigue_level)} capitalize mt-2`}>
                          {result.fatigue_level}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-zinc-400 mb-1">Days Until Critical</div>
                        <div className="text-4xl font-bold text-white font-mono">
                          {result.days_until_fatigue}
                        </div>
                        <motion.div
                          className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getUrgencyBadge(result.refresh_urgency).color}`}
                          initial={{ scale: 0.9 }}
                          animate={{ scale: 1 }}
                        >
                          {getUrgencyBadge(result.refresh_urgency).text}
                        </motion.div>
                      </div>
                    </div>

                    <div className="text-zinc-300 text-sm">{result.summary}</div>
                  </motion.div>

                  {/* Metrics Grid */}
                  <motion.div className="grid grid-cols-2 gap-4" variants={itemVariants}>
                    {[
                      { icon: TrendingDown, label: 'CTR Decline', value: `${result.metrics.ctr_decline_percent.toFixed(1)}%`, color: 'text-red-400' },
                      { icon: DollarSign, label: 'CPM Increase', value: `${result.metrics.cpm_increase_percent.toFixed(1)}%`, color: 'text-orange-400' },
                      { icon: Target, label: 'Frequency Risk', value: `${(result.metrics.frequency_risk * 100).toFixed(0)}%`, color: 'text-yellow-400' },
                      { icon: Users, label: 'Saturation', value: `${(result.metrics.audience_saturation * 100).toFixed(0)}%`, color: 'text-blue-400' },
                    ].map((metric, i) => (
                      <motion.div
                        key={metric.label}
                        className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                      >
                        <div className="flex items-center gap-2 text-zinc-400 mb-2">
                          <metric.icon className="w-4 h-4" />
                          <span className="text-sm">{metric.label}</span>
                        </div>
                        <div className={`text-2xl font-bold font-mono ${metric.color}`}>
                          {metric.value}
                        </div>
                      </motion.div>
                    ))}
                  </motion.div>

                  {/* Decay Analysis */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                      <Zap className="w-5 h-5 text-yellow-400" />
                      Decay Analysis
                    </h3>
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-zinc-400">Pattern:</span>
                        <span className="ml-2 font-medium capitalize">{result.decay.pattern}</span>
                      </div>
                      <div>
                        <span className="text-zinc-400">Rate:</span>
                        <span className="ml-2 font-medium text-red-400 font-mono">{result.decay.rate_percent_per_day.toFixed(1)}%/day</span>
                      </div>
                    </div>
                  </motion.div>

                  {/* 7-Day Projections */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4">7-Day Projections</h3>
                    <div className="grid grid-cols-3 gap-4">
                      {[
                        { label: 'CTR', value: `${result.projections_7d.ctr.toFixed(2)}%` },
                        { label: 'CPM', value: `$${result.projections_7d.cpm.toFixed(2)}` },
                        { label: 'Frequency', value: `${result.projections_7d.frequency.toFixed(1)}x` },
                      ].map((proj) => (
                        <div key={proj.label} className="text-center">
                          <div className="text-sm text-zinc-400 mb-1">{proj.label}</div>
                          <div className="text-xl font-bold font-mono">{proj.value}</div>
                        </div>
                      ))}
                    </div>
                  </motion.div>

                  {/* Recommendations */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-yellow-400" />
                      Recommendations
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
                          <ChevronRight className="w-4 h-4 text-zinc-500 mt-0.5 flex-shrink-0" />
                          <span className="text-zinc-300">{rec}</span>
                        </motion.li>
                      ))}
                    </ul>
                  </motion.div>

                  {/* Refresh Strategies */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                      <RefreshCw className="w-5 h-5 text-quantum-400" />
                      Refresh Strategies
                    </h3>
                    <ul className="space-y-2">
                      {result.refresh_strategies.map((strategy, i) => (
                        <motion.li
                          key={i}
                          className="flex items-start gap-2 text-sm"
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.1 }}
                        >
                          <span className="text-quantum-400">+</span>
                          <span className="text-zinc-300">{strategy}</span>
                        </motion.li>
                      ))}
                    </ul>
                  </motion.div>

                  {/* Optimal Refresh Date */}
                  <motion.div
                    className="bg-gradient-to-r from-orange-900/20 to-red-900/20 border border-orange-500/30 rounded-xl p-4"
                    variants={itemVariants}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-orange-500/20 rounded-lg flex items-center justify-center">
                        <Calendar className="w-6 h-6 text-orange-400" />
                      </div>
                      <div>
                        <div className="text-sm text-zinc-400">Optimal Refresh Date</div>
                        <div className="font-medium text-white">
                          {new Date(result.optimal_refresh_date).toLocaleDateString('en-US', {
                            weekday: 'long',
                            month: 'long',
                            day: 'numeric',
                          })}
                        </div>
                      </div>
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
