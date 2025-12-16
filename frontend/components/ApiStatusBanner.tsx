'use client';

import { useEffect } from 'react';
import { Wifi, WifiOff, AlertCircle, Loader2, X } from 'lucide-react';
import { useApiStatusStore } from '@/stores/api-status';

interface ApiStatusBannerProps {
  className?: string;
  compact?: boolean;
}

export function ApiStatusBanner({ className = '', compact = false }: ApiStatusBannerProps) {
  const { status, isDemo, errorMessage, checkHealth } = useApiStatusStore();

  useEffect(() => {
    // Check health on mount
    checkHealth();
  }, [checkHealth]);

  // Don't show banner when connected (compact mode)
  if (compact && status === 'connected') {
    return null;
  }

  // Compact badge mode (for headers)
  if (compact) {
    return (
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
          status === 'connected'
            ? 'bg-quantum-500/10 text-quantum-400 border border-quantum-500/30'
            : status === 'checking'
            ? 'bg-zinc-500/10 text-zinc-400 border border-zinc-500/30'
            : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
        } ${className}`}
      >
        <span
          className={`w-2 h-2 rounded-full ${
            status === 'connected'
              ? 'bg-quantum-400'
              : status === 'checking'
              ? 'bg-zinc-400 animate-pulse'
              : 'bg-yellow-400'
          }`}
        />
        {status === 'connected'
          ? 'API Connected'
          : status === 'checking'
          ? 'Checking...'
          : 'Demo Mode'}
      </div>
    );
  }

  // Full banner mode (for page top)
  if (status === 'connected') {
    return null; // Hide when connected in full mode
  }

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-lg ${
        status === 'disconnected' || status === 'error'
          ? 'bg-yellow-500/10 border border-yellow-500/30'
          : 'bg-zinc-500/10 border border-zinc-500/30'
      } ${className}`}
    >
      {status === 'checking' ? (
        <Loader2 className="w-5 h-5 text-zinc-400 animate-spin flex-shrink-0" />
      ) : status === 'error' ? (
        <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
      ) : (
        <WifiOff className="w-5 h-5 text-yellow-400 flex-shrink-0" />
      )}

      <div className="flex-1">
        <p className="text-sm font-medium text-white">
          {status === 'checking'
            ? 'Connecting to API...'
            : isDemo
            ? 'Running in Demo Mode'
            : 'API Unavailable'}
        </p>
        {errorMessage && (
          <p className="text-xs text-zinc-400 mt-0.5">{errorMessage}</p>
        )}
        {isDemo && status !== 'checking' && (
          <p className="text-xs text-zinc-400 mt-0.5">
            Results shown are simulated. Start the backend for real AI generation.
          </p>
        )}
      </div>

      <button
        onClick={() => checkHealth()}
        className="px-3 py-1.5 text-xs font-medium bg-zinc-800 hover:bg-zinc-700 text-white rounded-md transition"
      >
        Retry
      </button>
    </div>
  );
}

export function ApiStatusBadge({ className = '' }: { className?: string }) {
  return <ApiStatusBanner compact className={className} />;
}
