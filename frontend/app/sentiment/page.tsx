'use client';

import React, { useState } from 'react';

type Scenario = 'normal' | 'crisis' | 'positive';

interface SentimentResult {
  demo_scenario: string;
  brand_name: string;
  health_status: string;
  overall_score: number;
  is_crisis: boolean;
  alerts_count: number;
  auto_pause_triggered: boolean;
  recommendation: string;
  mentions_analyzed: number;
  breakdown: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

interface Mention {
  id: string;
  source: string;
  content: string;
  sentiment_score: number;
  sentiment_level: string;
  engagement: number | null;
  issues: string[];
}

interface DetailedResult {
  brand_name: string;
  using_mock_data: boolean;
  scenario: string;
  snapshot: {
    health_status: string;
    overall_score: number;
    sentiment_level: string;
    total_mentions: number;
    positive: number;
    negative: number;
    neutral: number;
    trending_issues: string[];
    is_crisis: boolean;
  };
  alerts: Array<{
    severity: string;
    reason: string;
    recommended_action: string;
  }>;
  auto_pause: {
    should_pause: boolean;
    rule_triggered: string | null;
  };
  mentions: Mention[];
}

export default function SentimentDashboard() {
  const [brandName, setBrandName] = useState('Careerfied');
  const [scenario, setScenario] = useState<Scenario>('normal');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SentimentResult | null>(null);
  const [detailedResult, setDetailedResult] = useState<DetailedResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runDemo = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `http://localhost:8000/sentiment/demo/${scenario}?brand_name=${encodeURIComponent(brandName)}`,
        { method: 'POST' }
      );
      
      if (!response.ok) throw new Error('Failed to run sentiment demo');
      
      const data = await response.json();
      setResult(data);
      setDetailedResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const checkSentiment = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/sentiment/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brand_name: brandName, scenario }),
      });
      
      if (!response.ok) throw new Error('Failed to check sentiment');
      
      const data = await response.json();
      setDetailedResult(data);
      setResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (status: string) => {
    if (status.includes('🟢')) return 'text-green-400';
    if (status.includes('🟡')) return 'text-yellow-400';
    if (status.includes('🟠')) return 'text-orange-400';
    if (status.includes('🔴')) return 'text-red-400';
    return 'text-gray-400';
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.4) return 'text-green-400';
    if (score >= 0) return 'text-yellow-400';
    if (score >= -0.4) return 'text-orange-400';
    return 'text-red-400';
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <a href="/" className="text-gray-400 hover:text-white">←</a>
            <h1 className="text-xl font-bold">
              <span className="text-purple-400">Sentiment</span> Monitor
            </h1>
            <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">
              UNIQUE FEATURE
            </span>
          </div>
          <span className="text-sm text-gray-500">Slice 6 • No competitor has this</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        {/* Intro */}
        <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 border border-purple-500/30 rounded-lg p-6 mb-8">
          <h2 className="text-lg font-semibold mb-2">🎯 The Feature No One Else Has</h2>
          <p className="text-gray-400">
            BrandTruth AI monitors your brand sentiment in real-time and automatically pauses your ads 
            during crises. No more running cheerful ads while your brand is trending for the wrong reasons.
          </p>
          <p className="text-purple-400 mt-2 text-sm font-medium">
            "Marketing that respects human moments"
          </p>
        </div>

        {/* Controls */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm text-gray-400 mb-2">Brand Name</label>
              <input
                type="text"
                value={brandName}
                onChange={(e) => setBrandName(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                placeholder="Enter brand name..."
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">Demo Scenario</label>
              <div className="flex gap-2">
                {(['normal', 'crisis', 'positive'] as Scenario[]).map((s) => (
                  <button
                    key={s}
                    onClick={() => setScenario(s)}
                    className={`px-4 py-2 rounded text-sm font-medium transition ${
                      scenario === s
                        ? s === 'crisis'
                          ? 'bg-red-500 text-white'
                          : s === 'positive'
                          ? 'bg-green-500 text-white'
                          : 'bg-purple-500 text-white'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    }`}
                  >
                    {s === 'normal' && '📊'} {s === 'crisis' && '🚨'} {s === 'positive' && '✨'}{' '}
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={runDemo}
                disabled={loading}
                className="px-6 py-2 bg-purple-600 hover:bg-purple-500 rounded font-medium disabled:opacity-50 transition"
              >
                {loading ? 'Analyzing...' : 'Run Quick Demo'}
              </button>
              <button
                onClick={checkSentiment}
                disabled={loading}
                className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded font-medium disabled:opacity-50 transition"
              >
                Detailed Check
              </button>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-4 mb-6">
            <p className="text-red-400">⚠️ {error}</p>
            <p className="text-sm text-gray-500 mt-2">
              Make sure the API server is running: <code className="bg-gray-800 px-2 py-1 rounded">python api_server.py</code>
            </p>
          </div>
        )}

        {/* Quick Demo Results */}
        {result && (
          <div className="space-y-6">
            {/* Health Status */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-sm text-gray-400 mb-1">Brand Health</h3>
                  <p className={`text-3xl font-bold ${getHealthColor(result.health_status)}`}>
                    {result.health_status}
                  </p>
                </div>
                <div className="text-right">
                  <h3 className="text-sm text-gray-400 mb-1">Sentiment Score</h3>
                  <p className={`text-3xl font-bold ${getScoreColor(result.overall_score)}`}>
                    {result.overall_score > 0 ? '+' : ''}{result.overall_score.toFixed(2)}
                  </p>
                </div>
              </div>

              {/* Breakdown */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-green-900/20 border border-green-500/30 rounded p-3 text-center">
                  <p className="text-2xl font-bold text-green-400">{result.breakdown.positive}</p>
                  <p className="text-sm text-gray-400">Positive</p>
                </div>
                <div className="bg-gray-800 border border-gray-700 rounded p-3 text-center">
                  <p className="text-2xl font-bold text-gray-300">{result.breakdown.neutral}</p>
                  <p className="text-sm text-gray-400">Neutral</p>
                </div>
                <div className="bg-red-900/20 border border-red-500/30 rounded p-3 text-center">
                  <p className="text-2xl font-bold text-red-400">{result.breakdown.negative}</p>
                  <p className="text-sm text-gray-400">Negative</p>
                </div>
              </div>

              {/* Auto-Pause Status */}
              {result.auto_pause_triggered ? (
                <div className="bg-red-900/40 border border-red-500 rounded-lg p-4 animate-pulse">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">🛑</span>
                    <div>
                      <h4 className="font-bold text-red-400">AUTO-PAUSE TRIGGERED</h4>
                      <p className="text-gray-300">Your ads should be paused immediately to protect brand reputation.</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">✅</span>
                    <div>
                      <h4 className="font-bold text-green-400">ALL SYSTEMS GO</h4>
                      <p className="text-gray-400">Sentiment is healthy. Ads can continue running.</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Recommendation */}
              <div className="mt-4 p-4 bg-gray-800 rounded-lg">
                <h4 className="text-sm text-gray-400 mb-2">Recommended Action</h4>
                <p className="text-white">{result.recommendation}</p>
              </div>
            </div>
          </div>
        )}

        {/* Detailed Results */}
        {detailedResult && (
          <div className="space-y-6">
            {/* Header */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold">{detailedResult.brand_name}</h3>
                  {detailedResult.using_mock_data && (
                    <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
                      Demo Data
                    </span>
                  )}
                </div>
                <p className={`text-3xl font-bold ${getHealthColor(detailedResult.snapshot.health_status)}`}>
                  {detailedResult.snapshot.health_status}
                </p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-800 rounded p-3">
                  <p className="text-sm text-gray-400">Score</p>
                  <p className={`text-xl font-bold ${getScoreColor(detailedResult.snapshot.overall_score)}`}>
                    {detailedResult.snapshot.overall_score.toFixed(2)}
                  </p>
                </div>
                <div className="bg-gray-800 rounded p-3">
                  <p className="text-sm text-gray-400">Total Mentions</p>
                  <p className="text-xl font-bold">{detailedResult.snapshot.total_mentions}</p>
                </div>
                <div className="bg-gray-800 rounded p-3">
                  <p className="text-sm text-gray-400">Crisis Status</p>
                  <p className={`text-xl font-bold ${detailedResult.snapshot.is_crisis ? 'text-red-400' : 'text-green-400'}`}>
                    {detailedResult.snapshot.is_crisis ? '🚨 YES' : '✅ NO'}
                  </p>
                </div>
                <div className="bg-gray-800 rounded p-3">
                  <p className="text-sm text-gray-400">Auto-Pause</p>
                  <p className={`text-xl font-bold ${detailedResult.auto_pause.should_pause ? 'text-red-400' : 'text-green-400'}`}>
                    {detailedResult.auto_pause.should_pause ? '🛑 ACTIVE' : '▶️ OFF'}
                  </p>
                </div>
              </div>
            </div>

            {/* Alerts */}
            {detailedResult.alerts.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-bold mb-4">⚠️ Active Alerts</h3>
                <div className="space-y-3">
                  {detailedResult.alerts.map((alert, i) => (
                    <div
                      key={i}
                      className={`p-4 rounded-lg border ${
                        alert.severity === 'critical' || alert.severity === 'emergency'
                          ? 'bg-red-900/30 border-red-500/50'
                          : 'bg-yellow-900/30 border-yellow-500/50'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`text-xs font-bold uppercase px-2 py-1 rounded ${
                          alert.severity === 'critical' || alert.severity === 'emergency'
                            ? 'bg-red-500 text-white'
                            : 'bg-yellow-500 text-black'
                        }`}>
                          {alert.severity}
                        </span>
                        <span className="text-gray-300">{alert.reason}</span>
                      </div>
                      <p className="text-sm text-gray-400">→ {alert.recommended_action}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Mentions */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-bold mb-4">📝 Recent Mentions</h3>
              <div className="space-y-3">
                {detailedResult.mentions.map((mention) => (
                  <div
                    key={mention.id}
                    className={`p-4 rounded-lg border ${
                      mention.sentiment_score < -0.2
                        ? 'bg-red-900/10 border-red-500/30'
                        : mention.sentiment_score > 0.2
                        ? 'bg-green-900/10 border-green-500/30'
                        : 'bg-gray-800 border-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs bg-gray-700 px-2 py-1 rounded">
                        {mention.source === 'twitter' ? '𝕏' : '📰'} {mention.source}
                      </span>
                      <span className={`text-sm font-medium ${getScoreColor(mention.sentiment_score)}`}>
                        {mention.sentiment_score > 0 ? '+' : ''}{mention.sentiment_score.toFixed(2)}
                      </span>
                      {mention.engagement && (
                        <span className="text-xs text-gray-500">
                          {mention.engagement.toLocaleString()} engagements
                        </span>
                      )}
                    </div>
                    <p className="text-gray-300 text-sm">{mention.content}</p>
                    {mention.issues.length > 0 && (
                      <div className="mt-2 flex gap-2">
                        {mention.issues.map((issue, i) => (
                          <span key={i} className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">
                            {issue}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* How It Works */}
        {!result && !detailedResult && !error && (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-bold mb-4">🔮 How It Works</h3>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">👁️</span>
                </div>
                <h4 className="font-medium mb-2">1. Monitor</h4>
                <p className="text-sm text-gray-400">
                  Continuously scan Twitter, news, and social media for brand mentions
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">📊</span>
                </div>
                <h4 className="font-medium mb-2">2. Analyze</h4>
                <p className="text-sm text-gray-400">
                  AI analyzes sentiment in real-time and detects negative spikes
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">🛑</span>
                </div>
                <h4 className="font-medium mb-2">3. Auto-Pause</h4>
                <p className="text-sm text-gray-400">
                  Automatically pause ads during crises to protect your brand
                </p>
              </div>
            </div>

            <div className="mt-8 p-4 bg-gradient-to-r from-purple-900/20 to-pink-900/20 rounded-lg border border-purple-500/30">
              <p className="text-center text-gray-300">
                <strong>Try the demo scenarios above</strong> to see how BrandTruth AI protects your brand
                from advertising during the wrong moments.
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
