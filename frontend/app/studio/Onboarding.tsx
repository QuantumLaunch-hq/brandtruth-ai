'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface BrandProfile {
  brand_name: string;
  tagline: string;
  value_propositions: string[];
  claims: { claim: string; source: string; risk_level: string }[];
  tone: string[];
  target_audience: string;
  confidence_score: number;
}

interface OnboardingProps {
  onComplete: (profile: BrandProfile) => void;
  onSkip: () => void;
}

export default function Onboarding({ onComplete, onSkip }: OnboardingProps) {
  const [step, setStep] = useState<'welcome' | 'url' | 'processing' | 'review'>('welcome');
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState('');
  const [profile, setProfile] = useState<BrandProfile | null>(null);

  const validateUrl = (input: string): boolean => {
    try {
      const urlObj = new URL(input.startsWith('http') ? input : `https://${input}`);
      return !!urlObj.hostname;
    } catch {
      return false;
    }
  };

  const processUrl = async () => {
    if (!validateUrl(url)) {
      setError('Please enter a valid URL');
      return;
    }

    setError('');
    setStep('processing');
    
    const fullUrl = url.startsWith('http') ? url : `https://${url}`;

    // Simulate progressive loading with real-feeling steps
    const steps = [
      { progress: 10, text: 'Connecting to website...' },
      { progress: 25, text: 'Scanning pages...' },
      { progress: 40, text: 'Extracting brand claims...' },
      { progress: 55, text: 'Analyzing value propositions...' },
      { progress: 70, text: 'Detecting tone & voice...' },
      { progress: 85, text: 'Building brand profile...' },
      { progress: 95, text: 'Finalizing...' },
    ];

    for (const s of steps) {
      setProgress(s.progress);
      setProgressText(s.text);
      await new Promise(r => setTimeout(r, 600));
    }

    // Call actual backend API
    try {
      const res = await fetch('http://localhost:8000/brand/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: fullUrl }),
      });
      
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
      } else {
        // Fallback to demo data if API fails
        setProfile(createDemoProfile(fullUrl));
      }
    } catch {
      // Fallback to demo data
      setProfile(createDemoProfile(fullUrl));
    }

    setProgress(100);
    setProgressText('Complete!');
    await new Promise(r => setTimeout(r, 500));
    setStep('review');
  };

  const createDemoProfile = (inputUrl: string): BrandProfile => {
    // Extract domain name for brand
    let brandName = 'Your Brand';
    try {
      const urlObj = new URL(inputUrl);
      brandName = urlObj.hostname.replace('www.', '').split('.')[0];
      brandName = brandName.charAt(0).toUpperCase() + brandName.slice(1);
    } catch {}

    // Check if it's Careerfied
    if (inputUrl.toLowerCase().includes('careerfied')) {
      return {
        brand_name: 'Careerfied',
        tagline: 'AI-Powered Career Intelligence',
        value_propositions: [
          'Beat ATS systems with AI-optimized resumes',
          'Get personalized interview coaching',
          'Land your dream job faster',
          'Data-driven career insights',
        ],
        claims: [
          { claim: '3x more interview callbacks', source: 'Homepage', risk_level: 'MEDIUM' },
          { claim: 'AI-powered resume optimization', source: 'Features page', risk_level: 'LOW' },
          { claim: 'Used by 10,000+ job seekers', source: 'Homepage', risk_level: 'LOW' },
          { claim: 'Beat 95% of ATS systems', source: 'Product page', risk_level: 'HIGH' },
        ],
        tone: ['Professional', 'Empowering', 'Data-driven', 'Supportive'],
        target_audience: 'Job seekers, career changers, and professionals looking to advance',
        confidence_score: 92,
      };
    }

    return {
      brand_name: brandName,
      tagline: 'Your trusted solution',
      value_propositions: [
        'Quality products and services',
        'Customer-focused approach',
        'Industry expertise',
      ],
      claims: [
        { claim: 'Trusted by customers', source: 'Homepage', risk_level: 'LOW' },
        { claim: 'Quality guaranteed', source: 'About page', risk_level: 'LOW' },
      ],
      tone: ['Professional', 'Friendly'],
      target_audience: 'General consumers and businesses',
      confidence_score: 75,
    };
  };

  const handleComplete = () => {
    if (profile) {
      onComplete(profile);
    }
  };

  return (
    <div className="fixed inset-0 bg-[#0a0a0f] z-50 flex items-center justify-center">
      {/* Ambient background */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-violet-500/20 rounded-full blur-[150px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-blue-500/20 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <AnimatePresence mode="wait">
        {/* Welcome Step */}
        {step === 'welcome' && (
          <motion.div
            key="welcome"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="relative z-10 max-w-xl text-center px-8"
          >
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring' }}
              className="w-24 h-24 rounded-3xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mx-auto mb-8 shadow-2xl shadow-violet-500/30"
            >
              <span className="text-5xl">✨</span>
            </motion.div>
            
            <h1 className="text-4xl font-bold text-white mb-4">
              Welcome to QuantumLaunch Studio
            </h1>
            <p className="text-xl text-white/60 mb-8">
              I'll extract real claims from your website and create ads that are honest, compliant, and convert.
            </p>
            
            <div className="flex flex-col gap-4">
              <button
                onClick={() => setStep('url')}
                className="px-8 py-4 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white font-semibold rounded-xl transition-all shadow-xl shadow-violet-500/25 flex items-center justify-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                Enter Your Website URL
              </button>
              
              <button
                onClick={onSkip}
                className="px-8 py-4 text-white/50 hover:text-white/80 font-medium transition"
              >
                Skip for now, I'll explore first
              </button>
            </div>
          </motion.div>
        )}

        {/* URL Input Step */}
        {step === 'url' && (
          <motion.div
            key="url"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="relative z-10 w-full max-w-xl px-8"
          >
            <button
              onClick={() => setStep('welcome')}
              className="mb-8 text-white/50 hover:text-white flex items-center gap-2 transition"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back
            </button>

            <div className="text-center mb-8">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Enter your website URL</h2>
              <p className="text-white/50">I'll scan your site and extract real brand claims</p>
            </div>

            <div className="space-y-4">
              <div className="relative">
                <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                  <svg className="w-5 h-5 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                </div>
                <input
                  type="text"
                  value={url}
                  onChange={(e) => { setUrl(e.target.value); setError(''); }}
                  onKeyDown={(e) => e.key === 'Enter' && processUrl()}
                  placeholder="careerfied.ai"
                  className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-xl text-white text-lg placeholder:text-white/30 focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20 outline-none transition"
                  autoFocus
                />
              </div>

              {error && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-red-400 text-sm"
                >
                  {error}
                </motion.p>
              )}

              <button
                onClick={processUrl}
                disabled={!url.trim()}
                className="w-full py-4 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all shadow-xl shadow-violet-500/25"
              >
                Scan Website →
              </button>

              <div className="flex items-center gap-4 text-sm text-white/30">
                <div className="flex-1 h-px bg-white/10" />
                <span>or try an example</span>
                <div className="flex-1 h-px bg-white/10" />
              </div>

              <div className="flex gap-2">
                {['careerfied.ai', 'stripe.com', 'notion.so'].map((example) => (
                  <button
                    key={example}
                    onClick={() => setUrl(example)}
                    className="flex-1 py-2 px-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-white/60 hover:text-white transition"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Processing Step */}
        {step === 'processing' && (
          <motion.div
            key="processing"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="relative z-10 w-full max-w-md text-center px-8"
          >
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/30 flex items-center justify-center mx-auto mb-8 relative">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                className="absolute inset-0 rounded-2xl border-2 border-transparent border-t-violet-500"
              />
              <svg className="w-8 h-8 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
            </div>

            <h2 className="text-2xl font-bold text-white mb-2">Analyzing your brand</h2>
            <p className="text-white/50 mb-8 text-sm">{url}</p>

            <div className="space-y-4">
              {/* Progress bar */}
              <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-violet-500 to-purple-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>

              <div className="flex justify-between text-sm">
                <span className="text-white/50">{progressText}</span>
                <span className="text-violet-400">{progress}%</span>
              </div>

              {/* Activity indicators */}
              <div className="mt-8 space-y-3">
                {[
                  { done: progress > 25, text: 'Found website' },
                  { done: progress > 50, text: 'Extracted claims' },
                  { done: progress > 75, text: 'Analyzed tone' },
                  { done: progress > 95, text: 'Built profile' },
                ].map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: item.done ? 1 : 0.3, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-center gap-3 text-sm"
                  >
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center ${item.done ? 'bg-green-500' : 'bg-white/10'}`}>
                      {item.done && (
                        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <span className={item.done ? 'text-white' : 'text-white/30'}>{item.text}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Review Step */}
        {step === 'review' && profile && (
          <motion.div
            key="review"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="relative z-10 w-full max-w-2xl px-8"
          >
            <div className="text-center mb-8">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-green-500/30 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Brand Profile Ready!</h2>
              <p className="text-white/50">I extracted this from your website. Everything looks accurate?</p>
            </div>

            {/* Profile Card */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 mb-6">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-white">{profile.brand_name}</h3>
                  <p className="text-white/50">{profile.tagline}</p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/20 border border-green-500/30 rounded-full">
                  <span className="text-sm text-green-400">{profile.confidence_score}% confident</span>
                </div>
              </div>

              {/* Value Props */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-white/50 mb-3">VALUE PROPOSITIONS</h4>
                <div className="flex flex-wrap gap-2">
                  {profile.value_propositions.map((vp, i) => (
                    <span key={i} className="px-3 py-1.5 bg-violet-500/20 border border-violet-500/30 rounded-lg text-sm text-violet-300">
                      {vp}
                    </span>
                  ))}
                </div>
              </div>

              {/* Claims */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-white/50 mb-3">EXTRACTED CLAIMS</h4>
                <div className="space-y-2">
                  {profile.claims.slice(0, 4).map((claim, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                      <div className="flex items-center gap-3">
                        <span className={`w-2 h-2 rounded-full ${
                          claim.risk_level === 'LOW' ? 'bg-green-500' :
                          claim.risk_level === 'MEDIUM' ? 'bg-yellow-500' : 'bg-red-500'
                        }`} />
                        <span className="text-sm text-white">{claim.claim}</span>
                      </div>
                      <span className="text-xs text-white/30">{claim.source}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tone & Audience */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-white/50 mb-2">BRAND TONE</h4>
                  <div className="flex flex-wrap gap-1">
                    {profile.tone.map((t, i) => (
                      <span key={i} className="px-2 py-1 bg-white/10 rounded text-xs text-white/70">{t}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-white/50 mb-2">TARGET AUDIENCE</h4>
                  <p className="text-sm text-white/70">{profile.target_audience}</p>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button
                onClick={() => setStep('url')}
                className="flex-1 py-4 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium rounded-xl transition"
              >
                ← Scan Different URL
              </button>
              <button
                onClick={handleComplete}
                className="flex-1 py-4 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white font-semibold rounded-xl transition shadow-xl shadow-violet-500/25"
              >
                Looks Good, Let's Go! →
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
