import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API functions
export const fetchRegions = () => api.get('/regions/');
export const fetchRegionDetail = (id) => api.get(`/regions/${id}/`);
export const fetchRegionCandidates = (id) => api.get(`/regions/${id}/candidates/`);
export const fetchCandidates = () => api.get('/candidates/');
export const fetchCandidateDetail = (id) => api.get(`/candidates/${id}/`);
export const fetchCandidateRegions = (id) => api.get(`/candidates/${id}/regions/`);
export const fetchInfluenceSummary = () => api.get('/influences/summary/');
export const fetchInfluenceTimeline = (params) => api.get('/influences/timeline/', { params });
export const fetchNews = () => api.get('/news/');
export const fetchLatestNews = () => api.get('/news/latest/');
export const fetchDashboard = () => api.get('/dashboard/overview/');


export const fetchAnalyticsSummary = (days = 30) =>
  api.get('/analytics/summary/', { params: { days } });

export const fetchSentimentTimeline = (days = 30) =>
  api.get('/analytics/sentiment-timeline/', { params: { days } });

export const fetchCoverageByRegion = (days = 30) =>
  api.get('/analytics/coverage-by-region/', { params: { days } });

export const fetchCandidateCoverage = (days = 30) =>
  api.get('/analytics/candidate-coverage/', { params: { days } });

export const fetchSourceBreakdown = (days = 30) =>
  api.get('/analytics/source-breakdown/', { params: { days } });

export const fetchSentimentDistribution = (days = 30) =>
  api.get('/analytics/sentiment-distribution/', { params: { days } });

export const fetchLatestArticles = (limit = 15) =>
  api.get('/analytics/latest-articles/', { params: { limit } });

export default api;
