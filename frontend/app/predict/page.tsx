'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  ArrowLeft, 
  Zap, 
  TrendingUp, 
  AlertCircle,
  CheckCircle,
  Loader2,
  Target,
  BarChart3,
  Lightbulb,
  FlaskConical,
  ChevronRight,
  Sparkles
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ComponentScore {
  name: string;
  score: number;
  weight: number;
  analysis: string;
  strengths: string[];
  weaknesses: string[];
}

interface Improvement {
  component: string;
  priority: string;
  suggestion: string;
  expected_impact: string;
  example?: string;
}

interface ABTest {
  variant_name: string;
  change_description: string;
  hypothesis: string;
  expected_lift: string;
}

interface Prediction {
  overall_score: number;
  performance_tier: string;
  summary: string;
  confidence: number;
  ctr_prediction: string;
  estimated_ctr_range: { min: number; max: number };
  conversion_potential: string;
  component_scores: ComponentScore[];
  improvements: Improvement[];
  ab_test_suggestions: ABTest[];
}

export default function PredictPage() {
  // Form state
  const [headline, setHeadline] = useState('Stop Getting Rejected by ATS');
  const [primaryText, setPrimaryText] = useState('Your dream job slips away because your resume can\'t pass automated screening. Build resumes that get interviews with AI-powered optimization. Join 10,000+ job seekers who landed their dream jobs.');
  const [cta, setCta] = useState('Get Started');
  const [targetAudience, setTargetAudience] = useState('Job seekers aged 25-45');
  const [industry, setIndustry] = useState('Career Tech');
  
  // Result state
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const response = await fetch(`${API_BASE}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          headline,
          primary_text: primaryText,
          cta,
          target_audience: targetAudience,
          industry,
          platform: 'meta',
          objective: 'conversions',
        }),
      });

      if (!response.ok) {
        throw new Error('Prediction failed');
      }

      const data = await response.json();
      setPrediction(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/predict/demo`, {
        method: 'POST',
      });
      
      // For demo, run actual prediction
      await handlePredict();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    if (score >= 40) return 'text-orange-400';
    return 'text-red-400';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getTierEmoji = (tier: string) => {
    const emojis: Record<string, string> = {
      exceptional: '🌟',
      strong: '💪',
      good: '👍',
      average: '📊',
      weak: '⚠️',
      poor: '❌',
    };
    return emojis[tier] || '📊';
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-500/20 text-red-400 border-red-500/30',
      high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    };
    return colors[priority] || 'bg-gray-500/20 text-gray-400';
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
              <Zap className="w-5 h-5 text-yellow-400" />
              Performance Predictor
            </h1>
            <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
              Slice 9
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Input Form */}
          <div className="space-y-6">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-400" />
                Ad Content
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Headline</label>
                  <input
                    type="text"
                    value={headline}
                    onChange={(e) => setHeadline(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-yellow-500"
                    placeholder="Your attention-grabbing headline"
                  />
                  <p className="text-xs text-gray-500 mt-1">{headline.length} characters</p>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Primary Text</label>
                  <textarea
                    value={primaryText}
                    onChange={(e) => setPrimaryText(e.target.value)}
                    rows={4}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-yellow-500"
                    placeholder="Your ad copy..."
                  />
                  <p className="text-xs text-gray-500 mt-1">{primaryText.length} characters</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Call to Action</label>
                    <select
                      value={cta}
                      onChange={(e) => setCta(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-yellow-500"
                    >
                      <option value="Learn More">Learn More</option>
                      <option value="Sign Up">Sign Up</option>
                      <option value="Get Started">Get Started</option>
                      <option value="Shop Now">Shop Now</option>
                      <option value="Start Free">Start Free</option>
                      <option value="Try Now">Try Now</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Industry</label>
                    <input
                      type="text"
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-yellow-500"
                      placeholder="e.g., Career Tech"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Target Audience</label>
                  <input
                    type="text"
                    value={targetAudience}
                    onChange={(e) => setTargetAudience(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-yellow-500"
                    placeholder="e.g., Job seekers aged 25-45"
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button
                onClick={handlePredict}
                disabled={loading || !headline || !primaryText}
                className="flex-1 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-400 hover:to-orange-400 rounded-lg font-medium disabled:opacity-50 transition flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Predict Performance
                  </>
                )}
              </button>
            </div>

            {/* How it works */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 text-sm text-gray-400">
              <h3 className="font-medium text-white mb-2">How it works</h3>
              <p>AI analyzes your ad against proven performance patterns:</p>
              <ul className="mt-2 space-y-1">
                <li>• Headline power & clarity</li>
                <li>• Copy persuasion & structure</li>
                <li>• CTA effectiveness</li>
                <li>• Emotional resonance</li>
                <li>• Platform optimization</li>
              </ul>
            </div>
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

            {/* Placeholder when no prediction */}
            {!prediction && !loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <BarChart3 className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-400 mb-2">No prediction yet</h3>
                <p className="text-gray-500">Enter your ad content and click "Predict Performance"</p>
              </div>
            )}

            {/* Loading state */}
            {loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <Loader2 className="w-16 h-16 text-yellow-500 mx-auto mb-4 animate-spin" />
                <h3 className="text-lg font-medium text-gray-300 mb-2">Analyzing your ad...</h3>
                <p className="text-gray-500">AI is evaluating performance indicators</p>
              </div>
            )}

            {/* Prediction Results */}
            {prediction && !loading && (
              <>
                {/* Main Score Card */}
                <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold">Performance Score</h2>
                    <span className="text-2xl">{getTierEmoji(prediction.performance_tier)}</span>
                  </div>
                  
                  {/* Big Score */}
                  <div className="text-center py-6">
                    <div className={`text-7xl font-bold ${getScoreColor(prediction.overall_score)}`}>
                      {prediction.overall_score}
                    </div>
                    <div className="text-gray-400 text-lg mt-2">out of 100</div>
                    <div className={`inline-block px-4 py-1 rounded-full mt-3 text-sm font-medium ${
                      prediction.overall_score >= 75 ? 'bg-green-500/20 text-green-400' :
                      prediction.overall_score >= 50 ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {prediction.performance_tier.charAt(0).toUpperCase() + prediction.performance_tier.slice(1)} Performance
                    </div>
                  </div>
                  
                  {/* Quick Stats */}
                  <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-700">
                    <div className="text-center">
                      <div className="text-sm text-gray-400">CTR Prediction</div>
                      <div className="font-semibold text-white capitalize">
                        {prediction.ctr_prediction.replace(/_/g, ' ')}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-gray-400">Est. CTR</div>
                      <div className="font-semibold text-white">
                        {prediction.estimated_ctr_range.min}% - {prediction.estimated_ctr_range.max}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-gray-400">Conversion</div>
                      <div className="font-semibold text-white">
                        {prediction.conversion_potential}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Component Breakdown */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-blue-400" />
                    Component Breakdown
                  </h3>
                  
                  <div className="space-y-4">
                    {prediction.component_scores.map((component) => (
                      <div key={component.name}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-300">{component.name}</span>
                          <span className={getScoreColor(component.score)}>{component.score}</span>
                        </div>
                        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${getScoreBgColor(component.score)} transition-all duration-500`}
                            style={{ width: `${component.score}%` }}
                          />
                        </div>
                        {component.analysis && (
                          <p className="text-xs text-gray-500 mt-1">{component.analysis}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Improvements */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-yellow-400" />
                    Improvements
                  </h3>
                  
                  <div className="space-y-3">
                    {prediction.improvements.map((imp, i) => (
                      <div key={i} className="border border-gray-800 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`px-2 py-0.5 text-xs font-medium rounded border ${getPriorityColor(imp.priority)}`}>
                            {imp.priority.toUpperCase()}
                          </span>
                          <span className="text-sm text-gray-400">{imp.component}</span>
                        </div>
                        <p className="text-sm text-white mb-1">{imp.suggestion}</p>
                        <p className="text-xs text-green-400">{imp.expected_impact}</p>
                        {imp.example && (
                          <div className="mt-2 p-2 bg-gray-800 rounded text-xs">
                            <span className="text-gray-500">Example: </span>
                            <span className="text-gray-300">{imp.example}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* A/B Test Suggestions */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <FlaskConical className="w-5 h-5 text-purple-400" />
                    A/B Test Ideas
                  </h3>
                  
                  <div className="space-y-3">
                    {prediction.ab_test_suggestions.map((ab, i) => (
                      <div key={i} className="flex items-start gap-3 p-3 border border-gray-800 rounded-lg hover:border-purple-500/50 transition">
                        <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-purple-400 font-bold text-sm">{String.fromCharCode(65 + i)}</span>
                        </div>
                        <div>
                          <h4 className="font-medium text-white">{ab.variant_name}</h4>
                          <p className="text-sm text-gray-400 mt-1">{ab.change_description}</p>
                          <div className="flex items-center gap-4 mt-2 text-xs">
                            <span className="text-gray-500">Hypothesis: {ab.hypothesis}</span>
                          </div>
                          <div className="mt-1">
                            <span className="text-green-400 text-sm font-medium">+{ab.expected_lift} expected lift</span>
                          </div>
                        </div>
                      </div>
                    ))}
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
