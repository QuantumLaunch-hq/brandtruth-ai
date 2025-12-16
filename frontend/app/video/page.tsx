'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  ArrowLeft, 
  Video,
  Play,
  User,
  Music,
  Sparkles,
  Loader2,
  AlertCircle,
  FileText,
  Clock,
  Zap,
  Volume2,
  Captions,
  Smartphone,
  Square,
  Monitor,
  ChevronDown
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface VideoResult {
  video_id: string;
  title: string;
  status: string;
  summary: string;
  video_url: string;
  thumbnail_url: string;
  duration_seconds: number;
  resolution: string;
  file_size_mb: number;
  script: {
    hook: string;
    body: string[];
    cta: string;
    full_script: string;
    scenes: { number: number; duration: number; text: string; visual: string }[];
  };
  avatar: { id: string; name: string; style: string } | null;
  music: { name: string; mood: string; bpm: number } | null;
  predictions: {
    engagement_score: number;
    hook_strength: number;
  };
}

interface Avatar {
  id: string;
  name: string;
  gender: string;
  age_range: string;
  style: string;
}

interface MusicTrack {
  id: string;
  name: string;
  genre: string;
  mood: string;
  bpm: number;
}

interface VideoStyleOption {
  id: string;
  name: string;
  description: string;
}

export default function VideoPage() {
  // Form state
  const [brandName, setBrandName] = useState('Careerfied');
  const [productDescription, setProductDescription] = useState('AI-powered resume builder that helps job seekers pass ATS screening and land interviews');
  const [targetAudience, setTargetAudience] = useState('Job seekers frustrated with resume rejections');
  const [benefits, setBenefits] = useState('ATS-optimized resumes\nIndustry-specific templates\nReal-time feedback and scoring');
  const [cta, setCta] = useState('Get Started Free');
  const [customScript, setCustomScript] = useState('');
  
  // Config state
  const [style, setStyle] = useState('ugc');
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [avatarStyle, setAvatarStyle] = useState('casual');
  const [includeCaptions, setIncludeCaptions] = useState(true);
  const [includeMusic, setIncludeMusic] = useState(true);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VideoResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'form' | 'script'>('form');
  
  // Options
  const [styles, setStyles] = useState<VideoStyleOption[]>([]);
  const [avatars, setAvatars] = useState<Avatar[]>([]);
  const [musicTracks, setMusicTracks] = useState<MusicTrack[]>([]);

  // Fetch options on mount
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const [stylesRes, avatarsRes, musicRes] = await Promise.all([
          fetch(`${API_BASE}/video/styles`),
          fetch(`${API_BASE}/video/avatars`),
          fetch(`${API_BASE}/video/music`),
        ]);
        
        const stylesData = await stylesRes.json();
        const avatarsData = await avatarsRes.json();
        const musicData = await musicRes.json();
        
        setStyles(stylesData.styles || []);
        setAvatars(avatarsData.avatars || []);
        setMusicTracks(musicData.tracks || []);
      } catch (err) {
        console.error('Failed to fetch options:', err);
      }
    };
    
    fetchOptions();
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const benefitsList = benefits.split('\n').map(b => b.trim()).filter(b => b);
      
      const response = await fetch(`${API_BASE}/video/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_name: brandName,
          product_description: productDescription,
          target_audience: targetAudience,
          key_benefits: benefitsList,
          cta,
          style,
          aspect_ratio: aspectRatio,
          avatar_style: avatarStyle,
          include_captions: includeCaptions,
          include_music: includeMusic,
          custom_script: activeTab === 'script' && customScript ? customScript : null,
        }),
      });

      if (!response.ok) throw new Error('Generation failed');
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async (demoStyle: string) => {
    setLoading(true);
    setError(null);
    setStyle(demoStyle);

    try {
      const response = await fetch(`${API_BASE}/video/demo/${demoStyle}`, { method: 'POST' });
      if (!response.ok) throw new Error('Demo failed');
      
      // Now get full generation
      const fullResponse = await fetch(`${API_BASE}/video/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_name: 'Careerfied',
          product_description: 'AI-powered resume builder',
          target_audience: 'Job seekers',
          key_benefits: ['ATS-optimized', 'Industry templates', 'Real-time feedback'],
          cta: 'Get Started Free',
          style: demoStyle,
          aspect_ratio: '9:16',
          avatar_style: 'casual',
          include_captions: true,
          include_music: true,
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

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    if (score >= 40) return 'text-orange-400';
    return 'text-red-400';
  };

  const getAspectIcon = (ratio: string) => {
    if (ratio === '9:16') return <Smartphone className="w-4 h-4" />;
    if (ratio === '1:1') return <Square className="w-4 h-4" />;
    return <Monitor className="w-4 h-4" />;
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
              <Video className="w-5 h-5 text-pink-400" />
              AI UGC Video Generator
            </h1>
            <span className="text-xs bg-pink-500/20 text-pink-400 px-2 py-1 rounded">
              Slice 13
            </span>
          </div>
          <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">
            🎉 100% Complete
          </span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Input */}
          <div className="space-y-6">
            {/* Quick Demo */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Quick Demo Styles</h2>
              <div className="grid grid-cols-3 gap-2">
                {['ugc', 'testimonial', 'listicle', 'demo', 'explainer', 'storytelling'].map((s) => (
                  <button
                    key={s}
                    onClick={() => handleDemo(s)}
                    disabled={loading}
                    className={`py-2 px-3 rounded text-sm font-medium transition capitalize ${
                      style === s 
                        ? 'bg-pink-500 text-white' 
                        : 'bg-pink-500/20 text-pink-400 hover:bg-pink-500/30'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('form')}
                className={`flex-1 py-2 rounded-lg font-medium transition ${
                  activeTab === 'form' ? 'bg-pink-500 text-white' : 'bg-gray-800 text-gray-400'
                }`}
              >
                Auto-Generate
              </button>
              <button
                onClick={() => setActiveTab('script')}
                className={`flex-1 py-2 rounded-lg font-medium transition ${
                  activeTab === 'script' ? 'bg-pink-500 text-white' : 'bg-gray-800 text-gray-400'
                }`}
              >
                Custom Script
              </button>
            </div>

            {/* Form / Script Input */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              {activeTab === 'form' ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Brand Name</label>
                    <input
                      type="text"
                      value={brandName}
                      onChange={(e) => setBrandName(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-pink-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Product Description</label>
                    <textarea
                      value={productDescription}
                      onChange={(e) => setProductDescription(e.target.value)}
                      rows={2}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-pink-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Target Audience</label>
                    <input
                      type="text"
                      value={targetAudience}
                      onChange={(e) => setTargetAudience(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-pink-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Key Benefits (one per line)</label>
                    <textarea
                      value={benefits}
                      onChange={(e) => setBenefits(e.target.value)}
                      rows={3}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-pink-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Call to Action</label>
                    <input
                      type="text"
                      value={cta}
                      onChange={(e) => setCta(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-pink-500"
                    />
                  </div>
                </div>
              ) : (
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Custom Video Script</label>
                  <textarea
                    value={customScript}
                    onChange={(e) => setCustomScript(e.target.value)}
                    rows={8}
                    placeholder={`POV: You just discovered something amazing...

Here's why it changed everything:
- First benefit
- Second benefit
- Third benefit

Link in bio to try it yourself!`}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-pink-500 font-mono text-sm"
                  />
                </div>
              )}
            </div>

            {/* Video Config */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h3 className="font-semibold mb-4">Video Settings</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Style</label>
                  <select
                    value={style}
                    onChange={(e) => setStyle(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-pink-500"
                  >
                    {styles.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Aspect Ratio</label>
                  <select
                    value={aspectRatio}
                    onChange={(e) => setAspectRatio(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-pink-500"
                  >
                    <option value="9:16">9:16 (TikTok/Reels)</option>
                    <option value="1:1">1:1 (Square)</option>
                    <option value="16:9">16:9 (YouTube)</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Avatar Style</label>
                  <select
                    value={avatarStyle}
                    onChange={(e) => setAvatarStyle(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-pink-500"
                  >
                    <option value="casual">Casual</option>
                    <option value="professional">Professional</option>
                    <option value="energetic">Energetic</option>
                    <option value="friendly">Friendly</option>
                    <option value="authoritative">Authoritative</option>
                  </select>
                </div>
                
                <div className="flex flex-col gap-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeCaptions}
                      onChange={(e) => setIncludeCaptions(e.target.checked)}
                      className="w-4 h-4 rounded bg-gray-800 border-gray-700"
                    />
                    <Captions className="w-4 h-4 text-gray-400" />
                    <span className="text-sm">Captions</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeMusic}
                      onChange={(e) => setIncludeMusic(e.target.checked)}
                      className="w-4 h-4 rounded bg-gray-800 border-gray-700"
                    />
                    <Volume2 className="w-4 h-4 text-gray-400" />
                    <span className="text-sm">Music</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-400 hover:to-purple-400 rounded-lg font-medium disabled:opacity-50 transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating Video...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate AI Video
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
                <Video className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-400 mb-2">No video yet</h3>
                <p className="text-gray-500">Fill in the form or try a demo style</p>
              </div>
            )}

            {/* Loading */}
            {loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <Loader2 className="w-16 h-16 text-pink-500 mx-auto mb-4 animate-spin" />
                <h3 className="text-lg font-medium text-gray-300 mb-2">Generating your video...</h3>
                <p className="text-gray-500">Creating script, selecting avatar, composing scenes</p>
              </div>
            )}

            {/* Results */}
            {result && !loading && (
              <>
                {/* Video Preview */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
                  <div className="aspect-[9/16] max-h-[400px] bg-gray-800 flex items-center justify-center relative">
                    <div className="text-center">
                      <Play className="w-16 h-16 text-pink-500 mx-auto mb-2" />
                      <p className="text-gray-400">Video Preview</p>
                      <p className="text-xs text-gray-500 mt-1">(Mock render - integrate with HeyGen/Synthesia for real video)</p>
                    </div>
                    <div className="absolute top-4 right-4 flex items-center gap-2">
                      {getAspectIcon(aspectRatio)}
                      <span className="text-xs text-gray-400">{result.resolution}</span>
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold">{result.title}</h3>
                      <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">
                        {result.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {result.duration_seconds.toFixed(0)}s
                      </span>
                      <span>{result.file_size_mb} MB</span>
                    </div>
                  </div>
                </div>

                {/* Engagement Predictions */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-center">
                    <div className="text-sm text-gray-400 mb-1">Engagement Score</div>
                    <div className={`text-3xl font-bold ${getScoreColor(result.predictions.engagement_score)}`}>
                      {result.predictions.engagement_score}
                    </div>
                  </div>
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-center">
                    <div className="text-sm text-gray-400 mb-1">Hook Strength</div>
                    <div className={`text-3xl font-bold ${getScoreColor(result.predictions.hook_strength)}`}>
                      {result.predictions.hook_strength}
                    </div>
                  </div>
                </div>

                {/* Script */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-pink-400" />
                    Generated Script
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <div className="text-xs text-pink-400 font-medium mb-1">🎣 HOOK (First 3 seconds)</div>
                      <p className="bg-gray-800 rounded p-3 text-sm">{result.script.hook}</p>
                    </div>
                    
                    <div>
                      <div className="text-xs text-blue-400 font-medium mb-1">📝 BODY</div>
                      <div className="space-y-2">
                        {result.script.body.map((point, i) => (
                          <p key={i} className="bg-gray-800 rounded p-3 text-sm">{point}</p>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <div className="text-xs text-green-400 font-medium mb-1">📢 CTA</div>
                      <p className="bg-gray-800 rounded p-3 text-sm">{result.script.cta}</p>
                    </div>
                  </div>
                </div>

                {/* Scenes */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-4">Scene Breakdown ({result.script.scenes.length} scenes)</h3>
                  <div className="space-y-2">
                    {result.script.scenes.map((scene, i) => (
                      <div key={i} className="flex items-center gap-3 bg-gray-800 rounded p-3">
                        <div className="w-8 h-8 bg-pink-500/20 rounded flex items-center justify-center text-pink-400 text-sm font-bold">
                          {scene.number}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm truncate">{scene.text}</p>
                          <p className="text-xs text-gray-500">{scene.visual} • {scene.duration.toFixed(1)}s</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Avatar & Music */}
                <div className="grid grid-cols-2 gap-4">
                  {result.avatar && (
                    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-pink-500/20 rounded-full flex items-center justify-center">
                          <User className="w-5 h-5 text-pink-400" />
                        </div>
                        <div>
                          <div className="font-medium">{result.avatar.name}</div>
                          <div className="text-xs text-gray-400 capitalize">{result.avatar.style}</div>
                        </div>
                      </div>
                    </div>
                  )}
                  {result.music && (
                    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-500/20 rounded-full flex items-center justify-center">
                          <Music className="w-5 h-5 text-purple-400" />
                        </div>
                        <div>
                          <div className="font-medium">{result.music.name}</div>
                          <div className="text-xs text-gray-400">{result.music.mood} • {result.music.bpm} BPM</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
