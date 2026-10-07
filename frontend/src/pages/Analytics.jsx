import React, { useState } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  useAnalyticsSummary,
  useSentimentTimeline,
  useCoverageByRegion,
  useCandidateCoverage,
  useSourceBreakdown,
  useSentimentDistribution,
  useLatestArticles,
} from '../hooks/useApi';

const TIME_RANGES = [
  { label: '7 days', value: 7 },
  { label: '14 days', value: 14 },
  { label: '30 days', value: 30 },
  { label: '90 days', value: 90 },
];

const SENTIMENT_COLORS = {
  positive: '#10b981',
  neutral: '#9ca3af',
  negative: '#ef4444',
};

const PIE_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
  '#8b5cf6', '#ec4899', '#14b8a6', '#f97316',
];

const Analytics = () => {
  const [days, setDays] = useState(30);

  const { data: summary, loading: summaryLoading } = useAnalyticsSummary(days);
  const { data: timeline } = useSentimentTimeline(days);
  const { data: coverage } = useCoverageByRegion(days);
  const { data: candidates } = useCandidateCoverage(days);
  const { data: sources } = useSourceBreakdown(days);
  const { data: distribution } = useSentimentDistribution(days);
  const { data: articles } = useLatestArticles(15);

  const isLoading = summaryLoading && !summary;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6 flex justify-between items-center flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">
            Analytics Dashboard
          </h1>
          <p className="text-gray-500 mt-1">
            News sentiment, coverage, and candidate mentions
          </p>
        </div>
        <div className="flex gap-2">
          {TIME_RANGES.map((range) => (
            <button
              key={range.value}
              onClick={() => setDays(range.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                days === range.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="spinner"></div>
        </div>
      ) : (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="Articles Analyzed"
              value={summary?.total_articles || 0}
              color="blue"
            />
            <StatCard
              label="Positive"
              value={`${summary?.positive_pct || 0}%`}
              color="green"
            />
            <StatCard
              label="Negative"
              value={`${summary?.negative_pct || 0}%`}
              color="red"
            />
            <StatCard
              label="Avg Sentiment"
              value={(summary?.avg_sentiment || 0).toFixed(2)}
              color="yellow"
              subtitle={sentimentLabel(summary?.avg_sentiment)}
            />
          </div>

          {/* Sentiment Timeline */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">
              Sentiment Over Time
            </h3>
            {timeline && timeline.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(d) => d.slice(5)} // MM-DD
                  />
                  <YAxis domain={[-1, 1]} tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(value) => value.toFixed(3)}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="sentiment"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name="Avg Sentiment"
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState
                message="No timeline data yet"
                hint="Run `python manage.py fetch_news` to populate articles"
              />
            )}
          </div>

          {/* Two-column: Coverage by Region + Candidate Coverage */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                News Coverage by Region
              </h3>
              {coverage && coverage.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart
                    data={coverage.slice(0, 10)}
                    layout="vertical"
                    margin={{ left: 30, right: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={80}
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip />
                    <Bar
                      dataKey="article_count"
                      fill="#3b82f6"
                      radius={[0, 4, 4, 0]}
                      name="Articles"
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No region data yet" />
              )}
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                Candidate Mentions
              </h3>
              {candidates && candidates.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart
                    data={candidates}
                    layout="vertical"
                    margin={{ left: 30, right: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={110}
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip />
                    <Bar dataKey="mentions" radius={[0, 4, 4, 0]} name="Mentions">
                      {candidates.map((entry, idx) => (
                        <Cell key={idx} fill={entry.party_color || '#3b82f6'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No candidate data yet" />
              )}
            </div>
          </div>

          {/* Two-column: Sources + Sentiment Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">News Sources</h3>
              {sources && sources.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={sources}
                      dataKey="count"
                      nameKey="source"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={({ source, count }) => `${source}: ${count}`}
                      labelLine={false}
                    >
                      {sources.map((_, idx) => (
                        <Cell
                          key={idx}
                          fill={PIE_COLORS[idx % PIE_COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No source data yet" />
              )}
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                Sentiment Distribution
              </h3>
              {distribution &&
              distribution.positive +
                distribution.neutral +
                distribution.negative >
                0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Positive', value: distribution.positive },
                        { name: 'Neutral', value: distribution.neutral },
                        { name: 'Negative', value: distribution.negative },
                      ]}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      <Cell fill={SENTIMENT_COLORS.positive} />
                      <Cell fill={SENTIMENT_COLORS.neutral} />
                      <Cell fill={SENTIMENT_COLORS.negative} />
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No sentiment data yet" />
              )}
            </div>
          </div>

          {/* Candidate Leaderboard Table */}
          {candidates && candidates.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                Candidate Sentiment Leaderboard
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-left">
                      <th className="py-2 px-3">#</th>
                      <th className="py-2 px-3">Candidate</th>
                      <th className="py-2 px-3">Party</th>
                      <th className="py-2 px-3 text-right">Mentions</th>
                      <th className="py-2 px-3 text-right">Avg Sentiment</th>
                      <th className="py-2 px-3">Score Bar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {candidates.map((c, idx) => (
                      <tr
                        key={c.id}
                        className="border-b border-gray-100 hover:bg-gray-50"
                      >
                        <td className="py-2 px-3 text-gray-500">{idx + 1}</td>
                        <td className="py-2 px-3 font-medium">{c.name}</td>
                        <td className="py-2 px-3">
                          <span
                            className="text-xs px-2 py-1 rounded-full"
                            style={{
                              backgroundColor: c.party_color + '20',
                              color: c.party_color,
                            }}
                          >
                            {c.party}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right font-semibold">
                          {c.mentions}
                        </td>
                        <td className="py-2 px-3 text-right">
                          <span
                            className={
                              c.avg_sentiment > 0.05
                                ? 'text-green-600'
                                : c.avg_sentiment < -0.05
                                ? 'text-red-600'
                                : 'text-gray-500'
                            }
                          >
                            {c.avg_sentiment.toFixed(2)}
                          </span>
                        </td>
                        <td className="py-2 px-3">
                          <div className="w-full max-w-[160px] bg-gray-100 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                c.avg_sentiment > 0.05
                                  ? 'bg-green-500'
                                  : c.avg_sentiment < -0.05
                                  ? 'bg-red-500'
                                  : 'bg-gray-400'
                              }`}
                              style={{
                                width: `${
                                  ((c.avg_sentiment + 1) / 2) * 100
                                }%`,
                              }}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Latest Articles */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">
              Latest Analyzed Articles
            </h3>
            {articles && articles.length > 0 ? (
              <div className="space-y-3">
                {articles.map((a) => (
                  <a
                    key={a.id}
                    href={a.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block border border-gray-100 rounded-lg p-4 hover:shadow-md transition"
                  >
                    <div className="flex items-start gap-3">
                      {a.image_url && (
                        <img
                          src={a.image_url}
                          alt=""
                          className="w-16 h-16 rounded object-cover flex-shrink-0"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-800 line-clamp-2">
                          {a.title}
                        </h4>
                        <div className="flex items-center flex-wrap gap-2 mt-1">
                          <span className="text-xs text-gray-500">
                            {a.source}
                          </span>
                          <span className="text-xs text-gray-400">
                            {new Date(a.published_date).toLocaleDateString()}
                          </span>
                          {a.sentiment_label && (
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full ${
                                a.sentiment_label === 'positive'
                                  ? 'bg-green-100 text-green-700'
                                  : a.sentiment_label === 'negative'
                                  ? 'bg-red-100 text-red-700'
                                  : 'bg-gray-100 text-gray-600'
                              }`}
                            >
                              {a.sentiment_label} ({a.sentiment_score.toFixed(2)})
                            </span>
                          )}
                        </div>
                        {(a.candidates?.length > 0 ||
                          a.regions?.length > 0) && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {a.candidates?.map((c) => (
                              <span
                                key={`c-${c.id}`}
                                className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full"
                              >
                                👤 {c.name}
                              </span>
                            ))}
                            {a.regions?.map((r) => (
                              <span
                                key={`r-${r.id}`}
                                className="text-xs px-2 py-0.5 bg-gray-100 text-gray-700 rounded-full"
                              >
                                📍 {r.name}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            ) : (
              <EmptyState
                message="No articles yet"
                hint="Run `python manage.py fetch_news`"
              />
            )}
          </div>
        </>
      )}
    </div>
  );
};

// ------------------------------------------------------------------
// Small helper components
// ------------------------------------------------------------------

const StatCard = ({ label, value, color = 'blue', subtitle }) => {
  const colorMap = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    red: 'text-red-600',
    yellow: 'text-yellow-600',
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold ${colorMap[color]}`}>{value}</p>
      {subtitle && (
        <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
      )}
    </div>
  );
};

const EmptyState = ({ message, hint }) => (
  <div className="text-center py-12 text-gray-400">
    <p className="text-lg">{message}</p>
    {hint && (
      <p className="text-xs mt-2 font-mono bg-gray-50 inline-block px-3 py-1 rounded">
        {hint}
      </p>
    )}
  </div>
);

const sentimentLabel = (score) => {
  if (!score && score !== 0) return '';
  if (score >= 0.05) return 'Positive leaning';
  if (score <= -0.05) return 'Negative leaning';
  return 'Neutral';
};

export default Analytics;