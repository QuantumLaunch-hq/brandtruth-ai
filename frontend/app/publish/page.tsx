'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  ArrowLeft, 
  Facebook, 
  Instagram, 
  Upload, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  ExternalLink,
  DollarSign,
  Users,
  Target,
  Pause,
  Play
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PublishResult {
  success: boolean;
  campaign_id?: string;
  adset_id?: string;
  creative_id?: string;
  ad_id?: string;
  details?: any;
  error?: string;
  message?: string;
}

interface MetaStatus {
  configured: boolean;
  mode: 'live' | 'demo';
  valid?: boolean;
  user?: { id: string; name: string };
  message?: string;
}

export default function PublishPage() {
  // Form state
  const [headline, setHeadline] = useState('Stop Getting Rejected by ATS');
  const [primaryText, setPrimaryText] = useState('Build resumes that get interviews with AI-powered optimization. Join 10,000+ job seekers who landed their dream jobs.');
  const [cta, setCta] = useState('Get Started');
  const [imageUrl, setImageUrl] = useState('https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600');
  const [linkUrl, setLinkUrl] = useState('https://careerfied.ai');
  const [campaignName, setCampaignName] = useState('BrandTruth Campaign');
  const [dailyBudget, setDailyBudget] = useState(10);
  const [startPaused, setStartPaused] = useState(true);
  
  // Targeting
  const [ageMin, setAgeMin] = useState(25);
  const [ageMax, setAgeMax] = useState(45);
  const [countries, setCountries] = useState(['US']);
  
  // Status
  const [loading, setLoading] = useState(false);
  const [metaStatus, setMetaStatus] = useState<MetaStatus | null>(null);
  const [result, setResult] = useState<PublishResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Check Meta status on load
  useEffect(() => {
    checkMetaStatus();
  }, []);

  const checkMetaStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/meta/status`);
      const data = await response.json();
      setMetaStatus(data);
    } catch (err) {
      setMetaStatus({ configured: false, mode: 'demo', message: 'API not available' });
    }
  };

  const handlePublish = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/meta/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          headline,
          primary_text: primaryText,
          cta,
          image_url: imageUrl,
          link_url: linkUrl,
          page_id: 'demo_page',
          campaign_name: campaignName,
          adset_name: `${campaignName} - Ad Set`,
          ad_name: `${campaignName} - Ad`,
          daily_budget: dailyBudget * 100, // Convert to cents
          start_paused: startPaused,
          age_min: ageMin,
          age_max: ageMax,
          countries,
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to publish');
      }

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/meta/demo`, {
        method: 'POST',
      });

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
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
            <h1 className="text-xl font-bold">
              <span className="text-blue-400">Meta</span> Publishing
            </h1>
            <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
              Slice 8
            </span>
          </div>
          
          {/* Status Badge */}
          {metaStatus && (
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              metaStatus.mode === 'live' 
                ? 'bg-green-500/20 text-green-400' 
                : 'bg-yellow-500/20 text-yellow-400'
            }`}>
              {metaStatus.mode === 'live' ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Live Mode
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4" />
                  Demo Mode
                </>
              )}
            </div>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Form */}
          <div className="space-y-6">
            {/* Platform Selector */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Platform</h2>
              <div className="flex gap-4">
                <button className="flex-1 flex items-center justify-center gap-2 py-3 bg-blue-600 text-white rounded-lg">
                  <Facebook className="w-5 h-5" />
                  Facebook
                </button>
                <button className="flex-1 flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg">
                  <Instagram className="w-5 h-5" />
                  Instagram
                </button>
              </div>
            </div>

            {/* Ad Content */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Ad Content</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Headline</label>
                  <input
                    type="text"
                    value={headline}
                    onChange={(e) => setHeadline(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Primary Text</label>
                  <textarea
                    value={primaryText}
                    onChange={(e) => setPrimaryText(e.target.value)}
                    rows={3}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Call to Action</label>
                    <select
                      value={cta}
                      onChange={(e) => setCta(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                    >
                      <option value="Learn More">Learn More</option>
                      <option value="Sign Up">Sign Up</option>
                      <option value="Get Started">Get Started</option>
                      <option value="Shop Now">Shop Now</option>
                      <option value="Book Now">Book Now</option>
                      <option value="Download">Download</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Destination URL</label>
                    <input
                      type="url"
                      value={linkUrl}
                      onChange={(e) => setLinkUrl(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Image URL</label>
                  <input
                    type="url"
                    value={imageUrl}
                    onChange={(e) => setImageUrl(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Targeting */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-400" />
                Targeting
              </h2>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Age Min</label>
                    <input
                      type="number"
                      value={ageMin}
                      onChange={(e) => setAgeMin(parseInt(e.target.value))}
                      min={18}
                      max={65}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Age Max</label>
                    <input
                      type="number"
                      value={ageMax}
                      onChange={(e) => setAgeMax(parseInt(e.target.value))}
                      min={18}
                      max={65}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Countries</label>
                  <div className="flex flex-wrap gap-2">
                    {['US', 'UK', 'CA', 'AU', 'IN'].map((country) => (
                      <button
                        key={country}
                        onClick={() => {
                          if (countries.includes(country)) {
                            setCountries(countries.filter(c => c !== country));
                          } else {
                            setCountries([...countries, country]);
                          }
                        }}
                        className={`px-3 py-1 rounded text-sm ${
                          countries.includes(country)
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                        }`}
                      >
                        {country}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Budget & Launch */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-green-400" />
                Budget & Launch
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Daily Budget (USD)</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                    <input
                      type="number"
                      value={dailyBudget}
                      onChange={(e) => setDailyBudget(parseInt(e.target.value))}
                      min={1}
                      className="w-full bg-gray-800 border border-gray-700 rounded pl-8 pr-3 py-2 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Start Paused</p>
                    <p className="text-sm text-gray-400">Review in Ads Manager before going live</p>
                  </div>
                  <button
                    onClick={() => setStartPaused(!startPaused)}
                    className={`relative w-14 h-7 rounded-full transition ${
                      startPaused ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                  >
                    <span className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-all ${
                      startPaused ? 'left-1' : 'left-8'
                    }`} />
                  </button>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Campaign Name</label>
                  <input
                    type="text"
                    value={campaignName}
                    onChange={(e) => setCampaignName(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                  />
                </div>
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
                onClick={handlePublish}
                disabled={loading}
                className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium disabled:opacity-50 transition flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Publishing...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    Publish to Meta
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right Column - Preview & Results */}
          <div className="space-y-6">
            {/* Ad Preview */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Ad Preview</h2>
              
              <div className="bg-white rounded-lg overflow-hidden text-gray-900">
                {/* Facebook-style ad preview */}
                <div className="p-3 border-b flex items-center gap-2">
                  <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                    C
                  </div>
                  <div>
                    <p className="font-semibold text-sm">Careerfied</p>
                    <p className="text-xs text-gray-500">Sponsored</p>
                  </div>
                </div>
                
                <div className="p-3">
                  <p className="text-sm mb-3">{primaryText}</p>
                </div>
                
                {imageUrl && (
                  <img 
                    src={imageUrl} 
                    alt="Ad preview" 
                    className="w-full h-64 object-cover"
                  />
                )}
                
                <div className="p-3 border-t bg-gray-50">
                  <p className="text-xs text-gray-500 uppercase mb-1">{new URL(linkUrl).hostname}</p>
                  <p className="font-semibold">{headline}</p>
                  <button className="mt-2 px-4 py-2 bg-gray-200 text-gray-800 text-sm font-medium rounded">
                    {cta}
                  </button>
                </div>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 text-red-400">
                  <AlertCircle className="w-5 h-5" />
                  <p className="font-medium">Error</p>
                </div>
                <p className="mt-2 text-sm text-gray-300">{error}</p>
              </div>
            )}

            {/* Result */}
            {result && (
              <div className={`border rounded-lg p-6 ${
                result.success 
                  ? 'bg-green-900/20 border-green-500/30' 
                  : 'bg-red-900/20 border-red-500/30'
              }`}>
                <div className="flex items-center gap-2 mb-4">
                  {result.success ? (
                    <>
                      <CheckCircle className="w-6 h-6 text-green-400" />
                      <h3 className="text-lg font-semibold text-green-400">Published Successfully!</h3>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-6 h-6 text-red-400" />
                      <h3 className="text-lg font-semibold text-red-400">Publishing Failed</h3>
                    </>
                  )}
                </div>

                {result.success && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-400">Campaign ID</p>
                        <p className="font-mono">{result.campaign_id}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">Ad Set ID</p>
                        <p className="font-mono">{result.adset_id}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">Creative ID</p>
                        <p className="font-mono">{result.creative_id}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">Ad ID</p>
                        <p className="font-mono">{result.ad_id}</p>
                      </div>
                    </div>

                    <div className={`flex items-center gap-2 p-3 rounded ${
                      startPaused ? 'bg-yellow-500/20' : 'bg-green-500/20'
                    }`}>
                      {startPaused ? (
                        <>
                          <Pause className="w-5 h-5 text-yellow-400" />
                          <span className="text-yellow-400">Ad is paused - Review in Ads Manager</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-5 h-5 text-green-400" />
                          <span className="text-green-400">Ad is now live!</span>
                        </>
                      )}
                    </div>

                    {result.details?.demo_mode && (
                      <div className="p-3 bg-blue-500/20 rounded text-sm text-blue-300">
                        📋 This was a demo. In production, a real campaign would be created in Meta Ads Manager.
                      </div>
                    )}

                    <button className="w-full py-2 bg-blue-600 hover:bg-blue-500 rounded flex items-center justify-center gap-2 transition">
                      <ExternalLink className="w-4 h-4" />
                      Open in Meta Ads Manager
                    </button>
                  </div>
                )}

                {result.message && (
                  <p className="mt-4 text-sm text-gray-300">{result.message}</p>
                )}
              </div>
            )}

            {/* Info Box */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h3 className="font-semibold mb-3">How it works</h3>
              <ol className="space-y-2 text-sm text-gray-400">
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center text-xs flex-shrink-0">1</span>
                  <span>Creates a campaign in Meta Ads Manager</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center text-xs flex-shrink-0">2</span>
                  <span>Sets up an ad set with your targeting</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center text-xs flex-shrink-0">3</span>
                  <span>Uploads your image and creates the creative</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center text-xs flex-shrink-0">4</span>
                  <span>Creates the ad (paused by default for review)</span>
                </li>
              </ol>
              
              <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded text-sm text-yellow-300">
                💡 For live publishing, configure META_ACCESS_TOKEN and META_AD_ACCOUNT_ID in your .env file.
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
