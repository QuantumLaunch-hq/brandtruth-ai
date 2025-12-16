'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

interface AdPreview {
  headline: string;
  primaryText: string;
  cta: string;
  imageUrl?: string;
  brandName: string;
  brandLogo?: string;
}

export function PhoneFrame({ children, platform }: { children: React.ReactNode; platform: 'instagram' | 'facebook' | 'tiktok' }) {
  return (
    <div className="relative mx-auto" style={{ width: '280px' }}>
      {/* Phone frame */}
      <div className="relative bg-black rounded-[3rem] p-2 shadow-2xl">
        {/* Screen */}
        <div className="bg-black rounded-[2.5rem] overflow-hidden">
          {/* Notch */}
          <div className="relative h-8 bg-black flex items-center justify-center">
            <div className="absolute w-24 h-6 bg-black rounded-b-2xl" />
            <div className="relative flex items-center gap-2 text-white/50 text-xs">
              <span>9:41</span>
            </div>
          </div>
          
          {/* Content */}
          <div className="bg-black" style={{ height: '520px' }}>
            {children}
          </div>
          
          {/* Home indicator */}
          <div className="h-8 bg-black flex items-center justify-center">
            <div className="w-32 h-1 bg-white/30 rounded-full" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function InstagramAdPreview({ ad }: { ad: AdPreview }) {
  return (
    <PhoneFrame platform="instagram">
      <div className="h-full bg-black text-white">
        {/* Instagram header */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-white/10">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-xs font-bold">
              {ad.brandName.charAt(0)}
            </div>
            <div>
              <div className="text-sm font-semibold">{ad.brandName.toLowerCase()}</div>
              <div className="text-xs text-white/50">Sponsored</div>
            </div>
          </div>
          <svg className="w-5 h-5 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z" />
          </svg>
        </div>
        
        {/* Image */}
        <div className="aspect-square bg-gradient-to-br from-violet-600 to-purple-800 flex items-center justify-center">
          {ad.imageUrl ? (
            <img src={ad.imageUrl} alt="Ad" className="w-full h-full object-cover" />
          ) : (
            <div className="text-center px-8">
              <span className="text-6xl mb-4 block">✨</span>
              <p className="text-xl font-bold leading-tight">{ad.headline}</p>
            </div>
          )}
        </div>
        
        {/* Actions */}
        <div className="flex items-center justify-between px-3 py-2">
          <div className="flex items-center gap-4">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
          </div>
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </div>
        
        {/* CTA Button */}
        <div className="px-3 mb-2">
          <button className="w-full py-2 bg-white text-black font-semibold rounded-lg text-sm">
            {ad.cta}
          </button>
        </div>
        
        {/* Text */}
        <div className="px-3 text-sm">
          <span className="font-semibold">{ad.brandName.toLowerCase()}</span>
          <span className="ml-2 text-white/80">{ad.primaryText.slice(0, 100)}{ad.primaryText.length > 100 ? '...' : ''}</span>
        </div>
      </div>
    </PhoneFrame>
  );
}

export function FacebookAdPreview({ ad }: { ad: AdPreview }) {
  return (
    <PhoneFrame platform="facebook">
      <div className="h-full bg-[#18191a] text-white">
        {/* Facebook header */}
        <div className="px-3 py-2 flex items-center justify-between bg-[#242526]">
          <div className="text-blue-500 font-bold text-xl">f</div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-[#3a3b3c] flex items-center justify-center">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div className="w-8 h-8 rounded-full bg-[#3a3b3c]" />
          </div>
        </div>
        
        {/* Post */}
        <div className="mt-2">
          {/* Post header */}
          <div className="px-3 flex items-start gap-2">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-sm font-bold">
              {ad.brandName.charAt(0)}
            </div>
            <div className="flex-1">
              <div className="font-semibold text-sm">{ad.brandName}</div>
              <div className="flex items-center gap-1 text-xs text-white/50">
                <span>Sponsored</span>
                <span>·</span>
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                </svg>
              </div>
            </div>
            <svg className="w-5 h-5 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h.01M12 12h.01M19 12h.01" />
            </svg>
          </div>
          
          {/* Primary text */}
          <div className="px-3 mt-2 text-sm text-white/90">
            {ad.primaryText.slice(0, 150)}{ad.primaryText.length > 150 ? '... See More' : ''}
          </div>
          
          {/* Image */}
          <div className="mt-3 aspect-square bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center">
            {ad.imageUrl ? (
              <img src={ad.imageUrl} alt="Ad" className="w-full h-full object-cover" />
            ) : (
              <div className="text-center px-8">
                <span className="text-6xl mb-4 block">🚀</span>
                <p className="text-xl font-bold leading-tight">{ad.headline}</p>
              </div>
            )}
          </div>
          
          {/* Link preview */}
          <div className="bg-[#242526] px-3 py-2">
            <div className="text-xs text-white/50 uppercase">careerfied.ai</div>
            <div className="font-semibold text-sm mt-1">{ad.headline}</div>
            <button className="mt-2 w-full py-2 bg-[#3a3b3c] text-white font-semibold rounded text-sm">
              {ad.cta}
            </button>
          </div>
          
          {/* Reactions */}
          <div className="px-3 py-2 flex items-center justify-between text-white/50 text-xs">
            <div className="flex items-center gap-1">
              <span className="flex -space-x-1">
                <span className="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center">👍</span>
                <span className="w-4 h-4 rounded-full bg-red-500 flex items-center justify-center">❤️</span>
              </span>
              <span>2.4K</span>
            </div>
            <div>847 comments · 312 shares</div>
          </div>
        </div>
      </div>
    </PhoneFrame>
  );
}

export function TikTokAdPreview({ ad }: { ad: AdPreview }) {
  return (
    <PhoneFrame platform="tiktok">
      <div className="h-full bg-black text-white relative">
        {/* Full screen video/image background */}
        <div className="absolute inset-0 bg-gradient-to-br from-pink-600 via-purple-700 to-blue-800 flex items-center justify-center">
          {ad.imageUrl ? (
            <img src={ad.imageUrl} alt="Ad" className="w-full h-full object-cover" />
          ) : (
            <div className="text-center px-8">
              <span className="text-6xl mb-4 block">🔥</span>
              <p className="text-2xl font-bold leading-tight">{ad.headline}</p>
            </div>
          )}
        </div>
        
        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
        
        {/* Right sidebar actions */}
        <div className="absolute right-3 bottom-32 flex flex-col items-center gap-5">
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
              </svg>
            </div>
            <span className="text-xs mt-1">24.5K</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
              </svg>
            </div>
            <span className="text-xs mt-1">1,847</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z" />
              </svg>
            </div>
            <span className="text-xs mt-1">Share</span>
          </div>
        </div>
        
        {/* Bottom content */}
        <div className="absolute bottom-4 left-3 right-16">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center text-xs font-bold">
              {ad.brandName.charAt(0)}
            </div>
            <span className="font-semibold text-sm">{ad.brandName}</span>
            <span className="px-2 py-0.5 bg-white/20 rounded text-xs">Sponsored</span>
          </div>
          <p className="text-sm mb-3">{ad.primaryText.slice(0, 80)}...</p>
          <button className="px-6 py-2 bg-[#fe2c55] text-white font-semibold rounded text-sm">
            {ad.cta}
          </button>
        </div>
      </div>
    </PhoneFrame>
  );
}

// Platform selector
export function PlatformPreview({ ad }: { ad: AdPreview }) {
  const [platform, setPlatform] = useState<'instagram' | 'facebook' | 'tiktok'>('instagram');
  
  return (
    <div className="space-y-4">
      {/* Platform tabs */}
      <div className="flex gap-2 justify-center">
        {(['instagram', 'facebook', 'tiktok'] as const).map((p) => (
          <button
            key={p}
            onClick={() => setPlatform(p)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              platform === p 
                ? 'bg-white/10 text-white' 
                : 'text-white/50 hover:text-white/80'
            }`}
          >
            {p === 'instagram' ? '📸 Instagram' : p === 'facebook' ? '👤 Facebook' : '🎵 TikTok'}
          </button>
        ))}
      </div>
      
      {/* Preview */}
      <motion.div
        key={platform}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2 }}
      >
        {platform === 'instagram' && <InstagramAdPreview ad={ad} />}
        {platform === 'facebook' && <FacebookAdPreview ad={ad} />}
        {platform === 'tiktok' && <TikTokAdPreview ad={ad} />}
      </motion.div>
    </div>
  );
}
