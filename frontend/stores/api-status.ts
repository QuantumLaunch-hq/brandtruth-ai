import { create } from 'zustand';

export type ConnectionStatus = 'connected' | 'disconnected' | 'checking' | 'error';

interface ApiStatusState {
  // Connection state
  status: ConnectionStatus;
  isDemo: boolean;
  lastChecked: string | null;
  errorMessage: string | null;

  // API info
  apiUrl: string;
  apiVersion: string | null;

  // Actions
  setStatus: (status: ConnectionStatus) => void;
  setDemo: (isDemo: boolean) => void;
  setError: (message: string) => void;
  clearError: () => void;
  setApiInfo: (url: string, version?: string) => void;

  // Health check
  checkHealth: () => Promise<boolean>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useApiStatusStore = create<ApiStatusState>((set, get) => ({
  // Initial state
  status: 'checking',
  isDemo: false,
  lastChecked: null,
  errorMessage: null,
  apiUrl: API_BASE,
  apiVersion: null,

  // Actions
  setStatus: (status) =>
    set({
      status,
      lastChecked: new Date().toISOString(),
    }),

  setDemo: (isDemo) => set({ isDemo }),

  setError: (errorMessage) =>
    set({
      status: 'error',
      errorMessage,
      isDemo: true,
      lastChecked: new Date().toISOString(),
    }),

  clearError: () => set({ errorMessage: null }),

  setApiInfo: (apiUrl, apiVersion) =>
    set({
      apiUrl,
      apiVersion: apiVersion || null,
    }),

  // Health check
  checkHealth: async () => {
    set({ status: 'checking' });

    try {
      const response = await fetch(`${get().apiUrl}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });

      if (response.ok) {
        const data = await response.json();
        set({
          status: 'connected',
          isDemo: false,
          apiVersion: data.version || null,
          errorMessage: null,
          lastChecked: new Date().toISOString(),
        });
        return true;
      } else {
        set({
          status: 'error',
          isDemo: true,
          errorMessage: `API returned ${response.status}`,
          lastChecked: new Date().toISOString(),
        });
        return false;
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Connection failed';
      set({
        status: 'disconnected',
        isDemo: true,
        errorMessage: message,
        lastChecked: new Date().toISOString(),
      });
      return false;
    }
  },
}));

// Hook for periodic health checks
export const useApiHealthCheck = (intervalMs = 30000) => {
  const { checkHealth, status } = useApiStatusStore();

  // Initial check on mount
  if (typeof window !== 'undefined' && status === 'checking') {
    checkHealth();
  }

  return { checkHealth, status };
};
