'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Zap,
  TrendingUp,
  AlertCircle,
  Target,
  BarChart3,
  Lightbulb,
  FlaskConical,
  Sparkles
} from 'lucide-react';
import { ScoreOrb, ProgressBar } from '@/components/ui';

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
              <div className="w-8 h-8 bg-gradient-to-br from-quantum-500 to-quantum-600 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-black" />
              </div>
              Performance Predictor
            </h1>
            <span className="text-xs bg-quantum-500/20 text-quantum-400 px-2 py-1 rounded font-mono">
              AI-POWERED
            </span>
          </div>
        </div>
      </motion.header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Input Form */}
          <motion.div
            className="space-y-6"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.div
              className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors"
              variants={itemVariants}
            >
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-quantum-400" />
                Ad Content
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Headline</label>
                  <input
                    type="text"
                    value={headline}
                    onChange={(e) => setHeadline(e.target.value)}
                    className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-quantum-500 focus:ring-1 focus:ring-quantum-500/50 transition-all font-mono"
                    placeholder="Your attention-grabbing headline"
                  />
                  <p className="text-xs text-zinc-500 mt-1 font-mono">{headline.length} chars</p>
                </div>

                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Primary Text</label>
                  <textarea
                    value={primaryText}
                    onChange={(e) => setPrimaryText(e.target.value)}
                    rows={4}
                    className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-quantum-500 focus:ring-1 focus:ring-quantum-500/50 transition-all"
                    placeholder="Your ad copy..."
                  />
                  <p className="text-xs text-zinc-500 mt-1 font-mono">{primaryText.length} chars</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">Call to Action</label>
                    <select
                      value={cta}
                      onChange={(e) => setCta(e.target.value)}
                      className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-quantum-500 transition-all"
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
                    <label className="block text-sm text-zinc-400 mb-2">Industry</label>
                    <input
                      type="text"
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                      className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-quantum-500 transition-all"
                      placeholder="e.g., Career Tech"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Target Audience</label>
                  <input
                    type="text"
                    value={targetAudience}
                    onChange={(e) => setTargetAudience(e.target.value)}
                    className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-quantum-500 transition-all"
                    placeholder="e.g., Job seekers aged 25-45"
                  />
                </div>
              </div>
            </motion.div>

            {/* Actions */}
            <motion.div variants={itemVariants}>
              <motion.button
                onClick={handlePredict}
                disabled={loading || !headline || !primaryText}
                className="w-full py-4 bg-gradient-to-r from-quantum-500 to-quantum-600 hover:from-quantum-400 hover:to-quantum-500 rounded-xl font-semibold disabled:opacity-50 transition-all flex items-center justify-center gap-2 text-black shadow-lg shadow-quantum-500/25 hover:shadow-quantum-500/40"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                {loading ? (
                  <>
                    <motion.div
                      className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Predict Performance
                  </>
                )}
              </motion.button>
            </motion.div>

            {/* How it works */}
            <motion.div
              className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 text-sm text-zinc-400"
              variants={itemVariants}
            >
              <h3 className="font-medium text-white mb-2">How it works</h3>
              <p>AI analyzes your ad against proven performance patterns:</p>
              <ul className="mt-2 space-y-1 text-zinc-500">
                <li className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-quantum-500 rounded-full" />
                  Headline power & clarity
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-quantum-500 rounded-full" />
                  Copy persuasion & structure
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-quantum-500 rounded-full" />
                  CTA effectiveness
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-quantum-500 rounded-full" />
                  Emotional resonance
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-quantum-500 rounded-full" />
                  Platform optimization
                </li>
              </ul>
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

            {/* Placeholder when no prediction */}
            {!prediction && !loading && (
              <motion.div
                className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-12 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className="w-20 h-20 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4">
                  <BarChart3 className="w-10 h-10 text-zinc-600" />
                </div>
                <h3 className="text-lg font-medium text-zinc-400 mb-2">No prediction yet</h3>
                <p className="text-zinc-500">Enter your ad content and click "Predict Performance"</p>
              </motion.div>
            )}

            {/* Loading state */}
            {loading && (
              <motion.div
                className="bg-zinc-900/80 border border-quantum-500/30 rounded-xl p-12 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <motion.div
                  className="w-20 h-20 mx-auto mb-4 relative"
                  animate={{
                    boxShadow: ['0 0 20px rgba(34,197,94,0.3)', '0 0 40px rgba(34,197,94,0.5)', '0 0 20px rgba(34,197,94,0.3)']
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <motion.div
                    className="w-full h-full border-4 border-quantum-500/30 border-t-quantum-500 rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                  />
                  <Zap className="w-8 h-8 text-quantum-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                </motion.div>
                <h3 className="text-lg font-medium text-zinc-300 mb-2">Analyzing your ad...</h3>
                <p className="text-zinc-500">AI is evaluating performance indicators</p>
              </motion.div>
            )}

            {/* Prediction Results */}
            <AnimatePresence>
              {prediction && !loading && (
                <motion.div
                  className="space-y-6"
                  variants={containerVariants}
                  initial="hidden"
                  animate="visible"
                >
                  {/* Main Score Card */}
                  <motion.div
                    className="bg-gradient-to-br from-zinc-900 to-zinc-800 border border-zinc-700 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-lg font-semibold">Performance Score</h2>
                      <span className="px-3 py-1 bg-zinc-800 rounded-lg text-sm font-mono text-zinc-400">
                        {prediction.confidence}% confidence
                      </span>
                    </div>

                    {/* Score Orb */}
                    <div className="flex justify-center py-4">
                      <ScoreOrb
                        score={prediction.overall_score}
                        size="lg"
                        label={prediction.performance_tier.charAt(0).toUpperCase() + prediction.performance_tier.slice(1)}
                        animate
                      />
                    </div>

                    {/* Quick Stats */}
                    <div className="grid grid-cols-3 gap-4 pt-4 border-t border-zinc-700 mt-6">
                      <div className="text-center">
                        <div className="text-sm text-zinc-400 mb-1">CTR Prediction</div>
                        <div className="font-semibold text-white capitalize">
                          {prediction.ctr_prediction.replace(/_/g, ' ')}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-zinc-400 mb-1">Est. CTR</div>
                        <div className="font-semibold text-quantum-400 font-mono">
                          {prediction.estimated_ctr_range.min}% - {prediction.estimated_ctr_range.max}%
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-zinc-400 mb-1">Conversion</div>
                        <div className="font-semibold text-white">
                          {prediction.conversion_potential}
                        </div>
                      </div>
                    </div>
                  </motion.div>

                  {/* Component Breakdown */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-quantum-400" />
                      Component Breakdown
                    </h3>

                    <div className="space-y-4">
                      {prediction.component_scores.map((component, i) => (
                        <motion.div
                          key={component.name}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.1 }}
                        >
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-zinc-300">{component.name}</span>
                            <span className="font-mono font-semibold" style={{
                              color: component.score >= 80 ? '#22c55e' : component.score >= 60 ? '#eab308' : '#ef4444'
                            }}>
                              {component.score}
                            </span>
                          </div>
                          <ProgressBar
                            value={component.score}
                            max={100}
                            variant="gradient"
                            animate
                            showValue={false}
                          />
                          {component.analysis && (
                            <p className="text-xs text-zinc-500 mt-1">{component.analysis}</p>
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>

                  {/* Improvements */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                      <Lightbulb className="w-5 h-5 text-yellow-400" />
                      Improvements
                    </h3>

                    <div className="space-y-3">
                      {prediction.improvements.map((imp, i) => (
                        <motion.div
                          key={i}
                          className="border border-zinc-800 rounded-lg p-4 hover:border-zinc-700 transition-colors"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.1 }}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`px-2 py-0.5 text-xs font-medium rounded border ${getPriorityColor(imp.priority)}`}>
                              {imp.priority.toUpperCase()}
                            </span>
                            <span className="text-sm text-zinc-400">{imp.component}</span>
                          </div>
                          <p className="text-sm text-white mb-1">{imp.suggestion}</p>
                          <p className="text-xs text-quantum-400">{imp.expected_impact}</p>
                          {imp.example && (
                            <div className="mt-2 p-2 bg-zinc-800/50 rounded text-xs font-mono">
                              <span className="text-zinc-500">Example: </span>
                              <span className="text-zinc-300">{imp.example}</span>
                            </div>
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>

                  {/* A/B Test Suggestions */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                      <FlaskConical className="w-5 h-5 text-purple-400" />
                      A/B Test Ideas
                    </h3>

                    <div className="space-y-3">
                      {prediction.ab_test_suggestions.map((ab, i) => (
                        <motion.div
                          key={i}
                          className="flex items-start gap-3 p-4 border border-zinc-800 rounded-lg hover:border-purple-500/50 transition-all group"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.1 }}
                          whileHover={{ x: 4 }}
                        >
                          <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-purple-500/30 transition-colors">
                            <span className="text-purple-400 font-bold">{String.fromCharCode(65 + i)}</span>
                          </div>
                          <div className="flex-1">
                            <h4 className="font-medium text-white">{ab.variant_name}</h4>
                            <p className="text-sm text-zinc-400 mt-1">{ab.change_description}</p>
                            <p className="text-xs text-zinc-500 mt-2">Hypothesis: {ab.hypothesis}</p>
                            <div className="mt-2">
                              <span className="text-quantum-400 text-sm font-semibold">+{ab.expected_lift} expected lift</span>
                            </div>
                          </div>
                        </motion.div>
                      ))}
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
