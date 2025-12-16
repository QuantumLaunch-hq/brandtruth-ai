/**
 * useUser - Hook for getting current user's database ID
 *
 * This hook fetches the user's database ID for use with API calls
 * that need to associate data with the user.
 */

import { useState, useEffect, useCallback } from 'react';
import { useSession } from 'next-auth/react';

export interface User {
  id: string;
  name: string | null;
  email: string;
  image: string | null;
}

export function useUser() {
  const { data: session, status } = useSession();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUser = useCallback(async () => {
    if (status !== 'authenticated') {
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/user');
      if (!response.ok) {
        throw new Error('Failed to fetch user');
      }
      const data = await response.json();
      setUser(data.user);
    } catch (err) {
      console.error('Failed to fetch user:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch user');
    } finally {
      setIsLoading(false);
    }
  }, [status]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return {
    user,
    userId: user?.id || null,
    isLoading: status === 'loading' || isLoading,
    error,
    refetch: fetchUser,
  };
}
