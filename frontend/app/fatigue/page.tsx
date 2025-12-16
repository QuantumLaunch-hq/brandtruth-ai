'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  ArrowLeft, 
  Clock, 
  TrendingDown,
  AlertTriangle,
  RefreshCw,
  Loader2,
  AlertCircle,
  Calendar,
  Target,
  Users,
  DollarSign,
  Zap,
  ChevronRight
} from 'lucide-react';

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
      
      // Set form values to match demo
      const daysMap: Record<string, number> = { fresh: 3, healthy: 10, moderate: 18, high: 25, critical: 35 };
      const freqMap: Record<string, number> = { fresh: 1.2, healthy: 2.0, moderate: 3.0, high: 4.0, critical: 5.5 };
      setDaysRunning(daysMap[scenario] || 14);
      setFrequency(freqMap[scenario] || 2.5);
      
      // Fetch full prediction
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
      fresh: 'text-green-400',
      healthy: 'text-blue-400',
      moderate: 'text-yellow-400',
      high: 'text-orange-400',
      critical: 'text-red-400',
    };
    return colors[level] || 'text-gray-400';
  };

  const getFatigueBg = (level: string) => {
    const colors: Record<string, string> = {
      fresh: 'bg-green-500/20 border-green-500/30',
      healthy: 'bg-blue-500/20 border-blue-500/30',
      moderate: 'bg-yellow-500/20 border-yellow-500/30',
      high: 'bg-orange-500/20 border-orange-500/30',
      critical: 'bg-red-500/20 border-red-500/30',
    };
    return colors[level] || 'bg-gray-500/20';
  };

  const getUrgencyBadge = (urgency: string) => {
    const badges: Record<string, { color: string; text: string }> = {
      none: { color: 'bg-green-500/20 text-green-400', text: 'No Action' },
      plan: { color: 'bg-blue-500/20 text-blue-400', text: 'Plan Refresh' },
      prepare: { color: 'bg-yellow-500/20 text-yellow-400', text: 'Prepare Creative' },
      urgent: { color: 'bg-orange-500/20 text-orange-400', text: 'Urgent' },
      immediate: { color: 'bg-red-500/20 text-red-400', text: 'Immediate!' },
    };
    return badges[urgency] || badges.none;
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
              <Clock className="w-5 h-5 text-orange-400" />
              Creative Fatigue Predictor
            </h1>
            <span className="text-xs bg-orange-500/20 text-orange-400 px-2 py-1 rounded">
              Slice 14
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Input */}
          <div className="space-y-6">
            {/* Quick Demo Scenarios */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Quick Demo Scenarios</h2>
              <div className="grid grid-cols-5 gap-2">
                {['fresh', 'healthy', 'moderate', 'high', 'critical'].map((scenario) => (
                  <button
                    key={scenario}
                    onClick={() => handleDemo(scenario)}
                    disabled={loading}
                    className={`py-2 px-3 rounded text-xs font-medium transition ${
                      scenario === 'fresh' ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30' :
                      scenario === 'healthy' ? 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30' :
                      scenario === 'moderate' ? 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30' :
                      scenario === 'high' ? 'bg-orange-500/20 text-orange-400 hover:bg-orange-500/30' :
                      'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                    }`}
                  >
                    {scenario.charAt(0).toUpperCase() + scenario.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Ad Performance Data */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Ad Performance Data</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Ad ID</label>
                  <input
                    type="text"
                    value={adId}
                    onChange={(e) => setAdId(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-orange-500"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Days Running</label>
                    <input
                      type="number"
                      value={daysRunning}
                      onChange={(e) => setDaysRunning(parseInt(e.target.value) || 0)}
                      min={1}
                      max={90}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-orange-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Frequency</label>
                    <input
                      type="number"
                      value={frequency}
                      onChange={(e) => setFrequency(parseFloat(e.target.value) || 1)}
                      step={0.1}
                      min={1}
                      max={10}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-orange-500"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Reach</label>
                    <input
                      type="number"
                      value={reach}
                      onChange={(e) => setReach(parseInt(e.target.value) || 0)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-orange-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Audience Size</label>
                    <input
                      type="number"
                      value={audienceSize}
                      onChange={(e) => setAudienceSize(parseInt(e.target.value) || 0)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-orange-500"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Industry</label>
                  <select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-orange-500"
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
            </div>

            {/* Actions */}
            <button
              onClick={handlePredict}
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-400 hover:to-red-400 rounded-lg font-medium disabled:opacity-50 transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Predicting...
                </>
              ) : (
                <>
                  <TrendingDown className="w-5 h-5" />
                  Predict Fatigue
                </>
              )}
            </button>
          </div>

          {/* Right Column - Results */}
          <div className="space-y-6">
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
                <Clock className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-400 mb-2">No prediction yet</h3>
                <p className="text-gray-500">Enter ad data or try a demo scenario</p>
              </div>
            )}

            {/* Loading */}
            {loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <Loader2 className="w-16 h-16 text-orange-500 mx-auto mb-4 animate-spin" />
                <h3 className="text-lg font-medium text-gray-300 mb-2">Analyzing fatigue patterns...</h3>
                <p className="text-gray-500">Calculating decay rates and projections</p>
              </div>
            )}

            {/* Results */}
            {result && !loading && (
              <>
                {/* Main Score Card */}
                <div className={`border rounded-lg p-6 ${getFatigueBg(result.fatigue_level)}`}>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="text-sm text-gray-400 mb-1">Fatigue Score</div>
                      <div className={`text-5xl font-bold ${getFatigueColor(result.fatigue_level)}`}>
                        {result.fatigue_score}
                      </div>
                      <div className={`text-lg font-medium ${getFatigueColor(result.fatigue_level)} capitalize`}>
                        {result.fatigue_level}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-400 mb-1">Days Until Critical</div>
                      <div className="text-3xl font-bold text-white">
                        {result.days_until_fatigue}
                      </div>
                      <div className={`inline-block px-3 py-1 rounded-full text-sm ${getUrgencyBadge(result.refresh_urgency).color}`}>
                        {getUrgencyBadge(result.refresh_urgency).text}
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-gray-300 text-sm">{result.summary}</div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-gray-400 mb-2">
                      <TrendingDown className="w-4 h-4" />
                      <span className="text-sm">CTR Decline</span>
                    </div>
                    <div className="text-2xl font-bold text-red-400">
                      {result.metrics.ctr_decline_percent.toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-gray-400 mb-2">
                      <DollarSign className="w-4 h-4" />
                      <span className="text-sm">CPM Increase</span>
                    </div>
                    <div className="text-2xl font-bold text-orange-400">
                      {result.metrics.cpm_increase_percent.toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-gray-400 mb-2">
                      <Target className="w-4 h-4" />
                      <span className="text-sm">Frequency Risk</span>
                    </div>
                    <div className="text-2xl font-bold text-yellow-400">
                      {(result.metrics.frequency_risk * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-gray-400 mb-2">
                      <Users className="w-4 h-4" />
                      <span className="text-sm">Saturation</span>
                    </div>
                    <div className="text-2xl font-bold text-blue-400">
                      {(result.metrics.audience_saturation * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>

                {/* Decay Pattern */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <Zap className="w-5 h-5 text-yellow-400" />
                    Decay Analysis
                  </h3>
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-gray-400">Pattern:</span>
                      <span className="ml-2 font-medium capitalize">{result.decay.pattern}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Rate:</span>
                      <span className="ml-2 font-medium text-red-400">{result.decay.rate_percent_per_day.toFixed(1)}%/day</span>
                    </div>
                  </div>
                </div>

                {/* 7-Day Projections */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-4">7-Day Projections</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-sm text-gray-400 mb-1">CTR</div>
                      <div className="text-xl font-bold">{result.projections_7d.ctr.toFixed(2)}%</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-gray-400 mb-1">CPM</div>
                      <div className="text-xl font-bold">${result.projections_7d.cpm.toFixed(2)}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-gray-400 mb-1">Frequency</div>
                      <div className="text-xl font-bold">{result.projections_7d.frequency.toFixed(1)}x</div>
                    </div>
                  </div>
                </div>

                {/* Recommendations */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-400" />
                    Recommendations
                  </h3>
                  <ul className="space-y-2">
                    {result.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <ChevronRight className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
                        <span className="text-gray-300">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Refresh Strategies */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <RefreshCw className="w-5 h-5 text-green-400" />
                    Refresh Strategies
                  </h3>
                  <ul className="space-y-2">
                    {result.refresh_strategies.map((strategy, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <span className="text-green-400">✓</span>
                        <span className="text-gray-300">{strategy}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Optimal Refresh Date */}
                <div className="bg-gradient-to-r from-orange-900/30 to-red-900/30 border border-orange-500/30 rounded-lg p-4">
                  <div className="flex items-center gap-3">
                    <Calendar className="w-6 h-6 text-orange-400" />
                    <div>
                      <div className="text-sm text-gray-400">Optimal Refresh Date</div>
                      <div className="font-medium text-white">
                        {new Date(result.optimal_refresh_date).toLocaleDateString('en-US', {
                          weekday: 'long',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </div>
                    </div>
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
