'use client';

import { useEffect, useState, ReactNode } from 'react';
import { useApiStatusStore } from '@/stores/api-status';

interface StoreProviderProps {
  children: ReactNode;
}

/**
 * StoreProvider handles:
 * 1. Hydration of persisted Zustand stores
 * 2. Initial API health check
 * 3. Periodic health check polling
 */
export function StoreProvider({ children }: StoreProviderProps) {
  const [isHydrated, setIsHydrated] = useState(false);
  const checkHealth = useApiStatusStore((state) => state.checkHealth);

  useEffect(() => {
    // Mark stores as hydrated after first render
    setIsHydrated(true);

    // Initial health check
    checkHealth();

    // Set up periodic health check (every 30 seconds)
    const interval = setInterval(() => {
      checkHealth();
    }, 30000);

    return () => clearInterval(interval);
  }, [checkHealth]);

  // During SSR or before hydration, render children without store data
  // This prevents hydration mismatch errors
  if (!isHydrated) {
    return <>{children}</>;
  }

  return <>{children}</>;
}

/**
 * Hook to check if stores are hydrated
 * Useful for components that need to wait for localStorage data
 */
export function useStoreHydration() {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  return isHydrated;
}
