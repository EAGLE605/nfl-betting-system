import { useState, useEffect, useCallback } from 'react';
import type { BettingCard } from '../types';
import { fetchBettingCard, getMockBettingCard } from '../services/api';

interface UsePicksOptions {
  week?: number;
  useMockData?: boolean;
}

interface UsePicksReturn {
  bettingCard: BettingCard | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function usePicks(options: UsePicksOptions = {}): UsePicksReturn {
  const { week, useMockData = false } = options;
  const [bettingCard, setBettingCard] = useState<BettingCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      if (useMockData) {
        // Simulate network delay for mock data
        await new Promise(resolve => setTimeout(resolve, 500));
        setBettingCard(getMockBettingCard());
      } else {
        const data = await fetchBettingCard(week);
        setBettingCard(data);
      }
    } catch (err) {
      console.error('Failed to fetch betting card:', err);
      // Fall back to mock data if API fails
      try {
        setBettingCard(getMockBettingCard());
        setError('Using demo data - API unavailable');
      } catch {
        setError(err instanceof Error ? err.message : 'Failed to load picks');
      }
    } finally {
      setLoading(false);
    }
  }, [week, useMockData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    bettingCard,
    loading,
    error,
    refetch: fetchData
  };
}

// Hook for pull-to-refresh functionality
export function usePullToRefresh(onRefresh: () => Promise<void>) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [startY, setStartY] = useState(0);
  const [pulling, setPulling] = useState(false);

  const handleTouchStart = useCallback((e: TouchEvent) => {
    if (window.scrollY === 0) {
      setStartY(e.touches[0].clientY);
      setPulling(true);
    }
  }, []);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (!pulling) return;
    const currentY = e.touches[0].clientY;
    const diff = currentY - startY;

    if (diff > 80 && !isRefreshing) {
      setIsRefreshing(true);
      setPulling(false);
      onRefresh().finally(() => {
        setIsRefreshing(false);
      });
    }
  }, [pulling, startY, isRefreshing, onRefresh]);

  const handleTouchEnd = useCallback(() => {
    setPulling(false);
  }, []);

  useEffect(() => {
    document.addEventListener('touchstart', handleTouchStart);
    document.addEventListener('touchmove', handleTouchMove);
    document.addEventListener('touchend', handleTouchEnd);

    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  return { isRefreshing };
}
