'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { 
  ArrowLeft, 
  Eye, 
  Target, 
  Clock,
  AlertCircle,
  Loader2,
  Lightbulb,
  ArrowRight,
  MousePointer,
  BarChart3
} from 'lucide-react';

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
      // Convert demo response to full analysis format
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

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw heatmap
    if (showHeatmap) {
      analysis.attention_points.forEach(point => {
        const x = point.x * canvas.width;
        const y = point.y * canvas.height;
        const r = point.radius * canvas.width;

        // Create radial gradient
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, r * 2);
        
        // Color based on intensity
        const alpha = point.intensity * 0.6;
        if (point.intensity > 0.8) {
          gradient.addColorStop(0, `rgba(255, 0, 0, ${alpha})`);
          gradient.addColorStop(0.5, `rgba(255, 100, 0, ${alpha * 0.5})`);
          gradient.addColorStop(1, 'rgba(255, 200, 0, 0)');
        } else if (point.intensity > 0.5) {
          gradient.addColorStop(0, `rgba(255, 165, 0, ${alpha})`);
          gradient.addColorStop(0.5, `rgba(255, 200, 0, ${alpha * 0.5})`);
          gradient.addColorStop(1, 'rgba(255, 255, 0, 0)');
        } else {
          gradient.addColorStop(0, `rgba(0, 255, 0, ${alpha})`);
          gradient.addColorStop(0.5, `rgba(100, 255, 100, ${alpha * 0.5})`);
          gradient.addColorStop(1, 'rgba(200, 255, 200, 0)');
        }

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, r * 2, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    // Draw visual flow
    if (showFlow && analysis.visual_flow.length > 0) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);

      analysis.visual_flow.forEach((step, i) => {
        const x = step.x * canvas.width;
        const y = step.y * canvas.height;

        // Draw line to next point
        if (i < analysis.visual_flow.length - 1) {
          const next = analysis.visual_flow[i + 1];
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(next.x * canvas.width, next.y * canvas.height);
          ctx.stroke();
        }

        // Draw number circle
        ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(59, 130, 246, 0.9)';
        ctx.beginPath();
        ctx.arc(x, y, 16, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.fillStyle = 'white';
        ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(step.order), x, y);
      });
    }
  }, [analysis, showHeatmap, showFlow]);

  const getAttentionColor = (level: string) => {
    const colors: Record<string, string> = {
      very_high: 'bg-red-500',
      high: 'bg-orange-500',
      medium: 'bg-yellow-500',
      low: 'bg-green-500',
      very_low: 'bg-blue-500',
    };
    return colors[level] || 'bg-gray-500';
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
              Attention Heatmap
            </h1>
            <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">
              Slice 10
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Input & Preview */}
          <div className="space-y-6">
            {/* Image Input */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Ad Image</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Image URL</label>
                  <input
                    type="url"
                    value={imageUrl}
                    onChange={(e) => setImageUrl(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-purple-500"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Headline</label>
                    <input
                      type="text"
                      value={headline}
                      onChange={(e) => setHeadline(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">CTA</label>
                    <input
                      type="text"
                      value={cta}
                      onChange={(e) => setCta(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-purple-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Image Preview with Heatmap */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Preview</h2>
                {analysis && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowHeatmap(!showHeatmap)}
                      className={`px-3 py-1 text-sm rounded ${showHeatmap ? 'bg-purple-500 text-white' : 'bg-gray-700 text-gray-300'}`}
                    >
                      Heatmap
                    </button>
                    <button
                      onClick={() => setShowFlow(!showFlow)}
                      className={`px-3 py-1 text-sm rounded ${showFlow ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-300'}`}
                    >
                      Flow
                    </button>
                  </div>
                )}
              </div>
              
              <div className="relative">
                <img
                  ref={imageRef}
                  src={imageUrl}
                  alt="Ad preview"
                  className="w-full rounded-lg"
                  onLoad={() => {
                    if (analysis) {
                      // Trigger canvas redraw
                      setShowHeatmap(h => h);
                    }
                  }}
                />
                <canvas
                  ref={canvasRef}
                  className="absolute top-0 left-0 w-full h-full pointer-events-none"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button
                onClick={handleDemo}
                disabled={loading}
                className="flex-1 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium disabled:opacity-50 transition"
              >
                Run Demo
              </button>
              <button
                onClick={handleAnalyze}
                disabled={loading || !imageUrl}
                className="flex-1 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-400 hover:to-pink-400 rounded-lg font-medium disabled:opacity-50 transition flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Eye className="w-5 h-5" />
                    Analyze Attention
                  </>
                )}
              </button>
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

            {/* Placeholder */}
            {!analysis && !loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <Eye className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-400 mb-2">No analysis yet</h3>
                <p className="text-gray-500">Click "Analyze Attention" to see where eyes will focus</p>
              </div>
            )}

            {/* Loading */}
            {loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <Loader2 className="w-16 h-16 text-purple-500 mx-auto mb-4 animate-spin" />
                <h3 className="text-lg font-medium text-gray-300 mb-2">Analyzing eye-tracking patterns...</h3>
                <p className="text-gray-500">Predicting where users will look</p>
              </div>
            )}

            {/* Results */}
            {analysis && !loading && (
              <>
                {/* Score Cards */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-purple-400">{analysis.overall_score}</div>
                    <div className="text-sm text-gray-400">Overall</div>
                  </div>
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-green-400">{analysis.headline_visibility_score}</div>
                    <div className="text-sm text-gray-400">Headline</div>
                  </div>
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-blue-400">{analysis.cta_visibility_score}</div>
                    <div className="text-sm text-gray-400">CTA</div>
                  </div>
                </div>

                {/* First Focus */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <MousePointer className="w-5 h-5 text-yellow-400" />
                    First Focus
                  </h3>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-white font-medium">{analysis.first_focus.element}</p>
                      <p className="text-sm text-gray-400">Noticed in ~{analysis.first_focus.time_to_notice_ms}ms</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-400">Time to CTA</p>
                      <p className="font-medium text-blue-400">{analysis.time_to_cta_ms}ms</p>
                    </div>
                  </div>
                </div>

                {/* Visual Flow */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <ArrowRight className="w-5 h-5 text-blue-400" />
                    Visual Flow
                    <span className="ml-auto text-sm font-normal text-gray-400">
                      {(analysis.flow_efficiency * 100).toFixed(0)}% efficient
                    </span>
                  </h3>
                  
                  <div className="space-y-2">
                    {analysis.visual_flow.map((step, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center font-bold text-sm">
                          {step.order}
                        </div>
                        <div className="flex-1">
                          <p className="text-white">{step.element}</p>
                        </div>
                        <div className="text-sm text-gray-400">
                          {step.dwell_time_ms}ms
                        </div>
                        {i < analysis.visual_flow.length - 1 && (
                          <ArrowRight className="w-4 h-4 text-gray-600" />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Attention Distribution */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-green-400" />
                    Attention Distribution
                  </h3>
                  
                  <div className="space-y-3">
                    {Object.entries(analysis.attention_distribution)
                      .filter(([_, value]) => value > 0)
                      .sort((a, b) => b[1] - a[1])
                      .map(([key, value]) => (
                        <div key={key}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-300 capitalize">{key.replace('_', ' ')}</span>
                            <span className="text-gray-400">{value}%</span>
                          </div>
                          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                              style={{ width: `${value}%` }}
                            />
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Issues & Recommendations */}
                {analysis.issues.length > 0 && (
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <h3 className="font-semibold mb-3 flex items-center gap-2">
                      <AlertCircle className="w-5 h-5 text-yellow-400" />
                      Issues
                    </h3>
                    <ul className="space-y-2">
                      {analysis.issues.map((issue, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                          <span className="text-yellow-400 mt-1">•</span>
                          {issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {analysis.recommendations.length > 0 && (
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <h3 className="font-semibold mb-3 flex items-center gap-2">
                      <Lightbulb className="w-5 h-5 text-green-400" />
                      Recommendations
                    </h3>
                    <ul className="space-y-2">
                      {analysis.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                          <span className="text-green-400 mt-1">✓</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
