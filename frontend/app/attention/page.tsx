'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Eye,
  Target,
  AlertCircle,
  Lightbulb,
  ArrowRight,
  MousePointer,
  BarChart3,
  Sparkles
} from 'lucide-react';
import { ScoreOrb, ProgressBar } from '@/components/ui';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface AttentionPoint {
  x: number;
  y: number;
  radius: number;
  intensity: number;
  element_type: string;
  description: string;
  attention_level: string;
}

interface VisualFlowStep {
  order: number;
  x: number;
  y: number;
  element: string;
  dwell_time_ms: number;
}

interface AttentionAnalysis {
  overall_score: number;
  cta_visibility_score: number;
  headline_visibility_score: number;
  summary: string;
  first_focus: {
    element: string;
    x: number;
    y: number;
    time_to_notice_ms: number;
  };
  time_to_cta_ms: number;
  attention_points: AttentionPoint[];
  attention_distribution: Record<string, number>;
  visual_flow: VisualFlowStep[];
  flow_efficiency: number;
  issues: string[];
  recommendations: string[];
  heatmap_grid?: number[][];
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

export default function AttentionPage() {
  const [imageUrl, setImageUrl] = useState('https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600');
  const [headline, setHeadline] = useState('Stop Getting Rejected by ATS');
  const [cta, setCta] = useState('Get Started');

  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AttentionAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showFlow, setShowFlow] = useState(true);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const response = await fetch(`${API_BASE}/attention/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_url: imageUrl,
          headline,
          cta,
        }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setAnalysis(data);
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
      const response = await fetch(`${API_BASE}/attention/demo`, {
        method: 'POST',
      });

      const data = await response.json();
      setAnalysis({
        ...data,
        first_focus: {
          element: data.first_focus_element,
          x: 0.5,
          y: 0.25,
          time_to_notice_ms: 50,
        },
        attention_points: [
          { x: 0.5, y: 0.25, radius: 0.15, intensity: 1.0, element_type: 'text_headline', description: 'Headline', attention_level: 'very_high' },
          { x: 0.5, y: 0.5, radius: 0.2, intensity: 0.85, element_type: 'image_focal', description: 'Hero Image', attention_level: 'high' },
          { x: 0.5, y: 0.75, radius: 0.12, intensity: 0.75, element_type: 'cta_button', description: 'CTA Button', attention_level: 'high' },
          { x: 0.5, y: 0.4, radius: 0.1, intensity: 0.6, element_type: 'text_body', description: 'Body Text', attention_level: 'medium' },
          { x: 0.85, y: 0.1, radius: 0.08, intensity: 0.4, element_type: 'logo', description: 'Logo', attention_level: 'low' },
        ],
        issues: data.top_issues || [],
        recommendations: data.top_recommendations || [],
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Draw heatmap overlay on canvas
  useEffect(() => {
    if (!analysis || !canvasRef.current || !imageRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = imageRef.current;
    canvas.width = img.width;
    canvas.height = img.height;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (showHeatmap) {
      analysis.attention_points.forEach(point => {
        const x = point.x * canvas.width;
        const y = point.y * canvas.height;
        const r = point.radius * canvas.width;

        const gradient = ctx.createRadialGradient(x, y, 0, x, y, r * 2);
        const alpha = point.intensity * 0.6;

        if (point.intensity > 0.8) {
          gradient.addColorStop(0, `rgba(34, 197, 94, ${alpha})`);
          gradient.addColorStop(0.5, `rgba(74, 222, 128, ${alpha * 0.5})`);
          gradient.addColorStop(1, 'rgba(134, 239, 172, 0)');
        } else if (point.intensity > 0.5) {
          gradient.addColorStop(0, `rgba(250, 204, 21, ${alpha})`);
          gradient.addColorStop(0.5, `rgba(253, 224, 71, ${alpha * 0.5})`);
          gradient.addColorStop(1, 'rgba(254, 240, 138, 0)');
        } else {
          gradient.addColorStop(0, `rgba(59, 130, 246, ${alpha})`);
          gradient.addColorStop(0.5, `rgba(96, 165, 250, ${alpha * 0.5})`);
          gradient.addColorStop(1, 'rgba(147, 197, 253, 0)');
        }

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, r * 2, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    if (showFlow && analysis.visual_flow.length > 0) {
      ctx.strokeStyle = 'rgba(34, 197, 94, 0.8)';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);

      analysis.visual_flow.forEach((step, i) => {
        const x = step.x * canvas.width;
        const y = step.y * canvas.height;

        if (i < analysis.visual_flow.length - 1) {
          const next = analysis.visual_flow[i + 1];
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(next.x * canvas.width, next.y * canvas.height);
          ctx.stroke();
        }

        ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(34, 197, 94, 0.9)';
        ctx.beginPath();
        ctx.arc(x, y, 16, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = 'black';
        ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(step.order), x, y);
      });
    }
  }, [analysis, showHeatmap, showFlow]);

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
              Attention Heatmap
            </h1>
            <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded font-mono">
              PREMIUM
            </span>
          </div>
        </div>
      </motion.header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Input & Preview */}
          <motion.div
            className="space-y-6"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {/* Image Input */}
            <motion.div
              className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors"
              variants={itemVariants}
            >
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-purple-400" />
                Ad Image
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Image URL</label>
                  <input
                    type="url"
                    value={imageUrl}
                    onChange={(e) => setImageUrl(e.target.value)}
                    className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/50 transition-all font-mono text-sm"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">Headline</label>
                    <input
                      type="text"
                      value={headline}
                      onChange={(e) => setHeadline(e.target.value)}
                      className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-purple-500 transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">CTA</label>
                    <input
                      type="text"
                      value={cta}
                      onChange={(e) => setCta(e.target.value)}
                      className="w-full bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 focus:outline-none focus:border-purple-500 transition-all"
                    />
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Image Preview with Heatmap */}
            <motion.div
              className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
              variants={itemVariants}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Preview</h2>
                {analysis && (
                  <div className="flex gap-2">
                    <motion.button
                      onClick={() => setShowHeatmap(!showHeatmap)}
                      className={`px-3 py-1.5 text-sm rounded-lg transition-all ${showHeatmap ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/25' : 'bg-zinc-800 text-zinc-400 hover:text-white'}`}
                      whileTap={{ scale: 0.95 }}
                    >
                      Heatmap
                    </motion.button>
                    <motion.button
                      onClick={() => setShowFlow(!showFlow)}
                      className={`px-3 py-1.5 text-sm rounded-lg transition-all ${showFlow ? 'bg-quantum-500 text-black shadow-lg shadow-quantum-500/25' : 'bg-zinc-800 text-zinc-400 hover:text-white'}`}
                      whileTap={{ scale: 0.95 }}
                    >
                      Flow
                    </motion.button>
                  </div>
                )}
              </div>

              <div className="relative rounded-lg overflow-hidden">
                <img
                  ref={imageRef}
                  src={imageUrl}
                  alt="Ad preview"
                  className="w-full"
                  onLoad={() => {
                    if (analysis) {
                      setShowHeatmap(h => h);
                    }
                  }}
                />
                <canvas
                  ref={canvasRef}
                  className="absolute top-0 left-0 w-full h-full pointer-events-none"
                />
              </div>
            </motion.div>

            {/* Actions */}
            <motion.div className="flex gap-4" variants={itemVariants}>
              <motion.button
                onClick={handleDemo}
                disabled={loading}
                className="flex-1 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-medium disabled:opacity-50 transition-all border border-zinc-700 hover:border-zinc-600"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                Run Demo
              </motion.button>
              <motion.button
                onClick={handleAnalyze}
                disabled={loading || !imageUrl}
                className="flex-1 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-400 hover:to-pink-400 rounded-xl font-semibold disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40"
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
                    Analyze Attention
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
            {!analysis && !loading && (
              <motion.div
                className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-12 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className="w-20 h-20 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Eye className="w-10 h-10 text-zinc-600" />
                </div>
                <h3 className="text-lg font-medium text-zinc-400 mb-2">No analysis yet</h3>
                <p className="text-zinc-500">Click "Analyze Attention" to see where eyes will focus</p>
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
                <h3 className="text-lg font-medium text-zinc-300 mb-2">Analyzing eye-tracking patterns...</h3>
                <p className="text-zinc-500">Predicting where users will look</p>
              </motion.div>
            )}

            {/* Results */}
            <AnimatePresence>
              {analysis && !loading && (
                <motion.div
                  className="space-y-6"
                  variants={containerVariants}
                  initial="hidden"
                  animate="visible"
                >
                  {/* Score Cards */}
                  <motion.div className="grid grid-cols-3 gap-4" variants={itemVariants}>
                    <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 text-center hover:border-purple-500/30 transition-colors">
                      <ScoreOrb score={analysis.overall_score} size="sm" animate />
                      <div className="text-sm text-zinc-400 mt-2">Overall</div>
                    </div>
                    <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 text-center hover:border-quantum-500/30 transition-colors">
                      <div className="text-3xl font-bold text-quantum-400 font-mono">{analysis.headline_visibility_score}</div>
                      <div className="text-sm text-zinc-400 mt-1">Headline</div>
                    </div>
                    <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 text-center hover:border-blue-500/30 transition-colors">
                      <div className="text-3xl font-bold text-blue-400 font-mono">{analysis.cta_visibility_score}</div>
                      <div className="text-sm text-zinc-400 mt-1">CTA</div>
                    </div>
                  </motion.div>

                  {/* First Focus */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                      <MousePointer className="w-5 h-5 text-yellow-400" />
                      First Focus
                    </h3>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white font-medium">{analysis.first_focus.element}</p>
                        <p className="text-sm text-zinc-400">Noticed in ~<span className="text-quantum-400 font-mono">{analysis.first_focus.time_to_notice_ms}ms</span></p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-zinc-400">Time to CTA</p>
                        <p className="font-medium text-blue-400 font-mono">{analysis.time_to_cta_ms}ms</p>
                      </div>
                    </div>
                  </motion.div>

                  {/* Visual Flow */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                      <ArrowRight className="w-5 h-5 text-quantum-400" />
                      Visual Flow
                      <span className="ml-auto text-sm font-normal text-zinc-400">
                        <span className="text-quantum-400 font-mono">{(analysis.flow_efficiency * 100).toFixed(0)}%</span> efficient
                      </span>
                    </h3>

                    <div className="space-y-2">
                      {analysis.visual_flow.map((step, i) => (
                        <motion.div
                          key={i}
                          className="flex items-center gap-3 p-2 rounded-lg hover:bg-zinc-800/50 transition-colors"
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.1 }}
                        >
                          <div className="w-8 h-8 bg-quantum-500/20 text-quantum-400 rounded-full flex items-center justify-center font-bold text-sm">
                            {step.order}
                          </div>
                          <div className="flex-1">
                            <p className="text-white">{step.element}</p>
                          </div>
                          <div className="text-sm text-zinc-400 font-mono">
                            {step.dwell_time_ms}ms
                          </div>
                          {i < analysis.visual_flow.length - 1 && (
                            <ArrowRight className="w-4 h-4 text-zinc-600" />
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>

                  {/* Attention Distribution */}
                  <motion.div
                    className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
                    variants={itemVariants}
                  >
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-quantum-400" />
                      Attention Distribution
                    </h3>

                    <div className="space-y-4">
                      {Object.entries(analysis.attention_distribution)
                        .filter(([_, value]) => value > 0)
                        .sort((a, b) => b[1] - a[1])
                        .map(([key, value], i) => (
                          <motion.div
                            key={key}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.05 }}
                          >
                            <div className="flex justify-between text-sm mb-2">
                              <span className="text-zinc-300 capitalize">{key.replace('_', ' ')}</span>
                              <span className="text-zinc-400 font-mono">{value}%</span>
                            </div>
                            <ProgressBar
                              value={value}
                              max={100}
                              variant="default"
                              animate
                              showValue={false}
                            />
                          </motion.div>
                        ))}
                    </div>
                  </motion.div>

                  {/* Issues & Recommendations */}
                  {analysis.issues.length > 0 && (
                    <motion.div
                      className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
                      variants={itemVariants}
                    >
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <AlertCircle className="w-5 h-5 text-yellow-400" />
                        Issues
                      </h3>
                      <ul className="space-y-2">
                        {analysis.issues.map((issue, i) => (
                          <motion.li
                            key={i}
                            className="flex items-start gap-2 text-sm text-zinc-300"
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.1 }}
                          >
                            <span className="text-yellow-400 mt-0.5">!</span>
                            {issue}
                          </motion.li>
                        ))}
                      </ul>
                    </motion.div>
                  )}

                  {analysis.recommendations.length > 0 && (
                    <motion.div
                      className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6"
                      variants={itemVariants}
                    >
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-quantum-400" />
                        Recommendations
                      </h3>
                      <ul className="space-y-2">
                        {analysis.recommendations.map((rec, i) => (
                          <motion.li
                            key={i}
                            className="flex items-start gap-2 text-sm text-zinc-300"
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.1 }}
                          >
                            <span className="text-quantum-400 mt-0.5">+</span>
                            {rec}
                          </motion.li>
                        ))}
                      </ul>
                    </motion.div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
}
