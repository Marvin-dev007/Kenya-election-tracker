import { useState, useEffect, useCallback, useRef } from 'react';
import * as api from '../api';

export const useFetch = (fetchFn, params = null) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Keep a stable ref to the function so inline wrappers don't trigger loops
  const fetchFnRef = useRef(fetchFn);
  useEffect(() => {
    fetchFnRef.current = fetchFn;
  }, [fetchFn]);

  // Safely serialize complex params (objects/arrays) to handle non-primitive states safely
  const paramsKey = typeof params === 'object' ? JSON.stringify(params) : params;

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Execute the most current function reference
      const response = paramsKey !== null 
        ? await fetchFnRef.current(params) 
        : await fetchFnRef.current();
        
      setData(response.data);
    } catch (err) {
      setError(err.message || 'An error occurred');
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
    // We intentionally watch paramsKey to safely monitor array/object changes by value
  }, [paramsKey, params]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
};

/* --- Hook Definitions --- */
export const useRegions = () => useFetch(api.fetchRegions);
export const useRegionDetail = (id) => useFetch(api.fetchRegionDetail, id);
export const useRegionCandidates = (id) => useFetch(api.fetchRegionCandidates, id);
export const useCandidates = () => useFetch(api.fetchCandidates);
export const useCandidateDetail = (id) => useFetch(api.fetchCandidateDetail, id);
export const useCandidateRegions = (id) => useFetch(api.fetchCandidateRegions, id);
export const useInfluenceSummary = () => useFetch(api.fetchInfluenceSummary);
export const useInfluenceTimeline = () => useFetch(api.fetchInfluenceTimeline);
export const useDashboard = () => useFetch(api.fetchDashboard);
export const useLatestNews = () => useFetch(api.fetchLatestNews);

/* 
  By stabilizing fetchFn with useRef above, these inline functional expressions
  will no longer trigger infinite loops when "days" or "limit" remains unchanged.
*/
export const useAnalyticsSummary = (days) =>
  useFetch(() => api.fetchAnalyticsSummary(days), days);

export const useSentimentTimeline = (days) =>
  useFetch(() => api.fetchSentimentTimeline(days), days);

export const useCoverageByRegion = (days) =>
  useFetch(() => api.fetchCoverageByRegion(days), days);

export const useCandidateCoverage = (days) =>
  useFetch(() => api.fetchCandidateCoverage(days), days);

export const useSourceBreakdown = (days) =>
  useFetch(() => api.fetchSourceBreakdown(days), days);

export const useSentimentDistribution = (days) =>
  useFetch(() => api.fetchSentimentDistribution(days), days);

export const useLatestArticles = (limit = 15) =>
  useFetch(() => api.fetchLatestArticles(limit), limit);
