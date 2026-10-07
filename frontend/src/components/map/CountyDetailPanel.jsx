import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from 'recharts';
import { getConstituenciesByCounty } from 'osm-kenya-boundaries';
import KenyaMap from './KenyaMap'; // Maps to the same folder
import { useFetch } from '../../hooks/useApi'; // Uses named destructuring {}
import { useCandidateDetail, useCandidateRegions } from '../../hooks/useApi';

const CandidateProfile = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCounty, setSelectedCounty] = useState(null);
  const [constituencyStats, setConstituencyStats] = useState([]);
  const [loadingConstituencies, setLoadingConstituencies] = useState(false);

  const { data: candidate, loading: candidateLoading } = useCandidateDetail(id);
  const { data: regions, loading: regionsLoading } = useCandidateRegions(id);

  // Build map of {countyCode: {influence, support, name}} for map highlighting
  const highlightedRegions = useMemo(() => {
    if (!regions) return {};
    const map = {};
    regions.forEach((r) => {
      map[r.region_id?.toString()] = {
        influence: r.influence || 0,
        support: r.support || 0,
        name: r.region,
      };
    });
    return map;
  }, [regions]);

  // Top 10 regions by influence for the bar chart
  const topRegions = useMemo(() => {
    if (!regions) return [];
    return [...regions]
      .sort((a, b) => (b.influence || 0) - (a.influence || 0))
      .slice(0, 10)
      .map((r) => ({
        name: r.region,
        influence: r.influence || 0,
        support: r.support || 0,
      }));
  }, [regions]);

  // Filtered region list for the table
  const filteredRegions = useMemo(() => {
    if (!regions) return [];
    const q = searchTerm.toLowerCase();
    return regions
      .filter((r) => r.region.toLowerCase().includes(q))
      .sort((a, b) => (b.influence || 0) - (a.influence || 0));
  }, [regions, searchTerm]);

  // When user clicks a county on the map, load its constituencies
  const handleCountyClick = async (county) => {
    setSelectedCounty(county);
    setLoadingConstituencies(true);

    try {
      const treeRes = await fetch(`/api/regions/${county.id}/tree`);
      const treeData = await treeRes.json();

      if (!treeData || !treeData.children) {
        throw new Error('No constituency heirarchy data returned for county ' + county.name);
      }

      const stats = await Promise.all(
        tree.children.map(async (constituency) => {
          const infRes = await fetch(`/api/influence/?candidate=${id}&region=${constituency.id}`);
          const infData = await infRes.json();
          const influence = infData.results?.[0]?.influence || 0;
          return {
            name: constituency.name,
            influence,
            wards: constituency.children?.length || 0,
          };
        })
      );
      setConstituencyStats(stats);
    } catch (err) {
      console.error('Constituency load failed:', err);
      setConstituencyStats([]);
    } finally {
      setLoadingConstituencies(false);
    }
  };

  // Aggregate stats
  const stats = useMemo(() => {
    if (!regions || regions.length === 0) {
      return {
        totalRegions: 0,
        avgInfluence: 0,
        avgSupport: 0,
        totalMentions: 0,
      };
    }
    return {
      totalRegions: regions.length,
      avgInfluence:
        regions.reduce((s, r) => s + (r.influence || 0), 0) / regions.length,
      avgSupport:
        regions.reduce((s, r) => s + (r.support || 0), 0) / regions.length,
      totalMentions: regions.reduce((s, r) => s + (r.mentions || 0), 0),
    };
  }, [regions]);

  if (candidateLoading || regionsLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-600">Candidate not found</h2>
        <Link to="/" className="text-blue-500 hover:underline mt-4 inline-block">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center space-x-6 flex-wrap gap-4">
          <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
            {candidate.photo ? (
              <img
                src={candidate.photo}
                alt={candidate.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-4xl">👤</span>
            )}
          </div>
          <div className="flex-1 min-w-[200px]">
            <h1 className="text-3xl font-bold text-gray-800">
              {candidate.name}
            </h1>
            <div className="flex items-center space-x-3 mt-2">
              <span
                className="px-3 py-1 rounded-full text-sm font-medium"
                style={{
                  backgroundColor: candidate.party_detail?.color + '20',
                  color: candidate.party_detail?.color,
                }}
              >
                {candidate.party_detail?.name}
              </span>
              <span className="text-sm text-gray-500 capitalize">
                {candidate.position}
              </span>
              {candidate.age && (
                <span className="text-sm text-gray-500">
                  {candidate.age} yrs
                </span>
              )}
            </div>
            {candidate.biography && (
              <p className="text-gray-600 mt-3 max-w-3xl">
                {candidate.biography}
              </p>
            )}
          </div>
          <Link
            to="/"
            className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
          >
            ← Back
          </Link>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Regions Covered</p>
          <p className="text-2xl font-bold">{stats.totalRegions}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Avg Influence</p>
          <p className="text-2xl font-bold text-blue-600">
            {stats.avgInfluence.toFixed(1)}%
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Avg Support</p>
          <p className="text-2xl font-bold text-green-600">
            {stats.avgSupport.toFixed(1)}%
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Total Mentions</p>
          <p className="text-2xl font-bold">
            {stats.totalMentions.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Map + Top Regions Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-4">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-semibold">
              Regional Influence Map
            </h3>
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-gray-500">Low</span>
              <div className="flex">
                <span className="w-4 h-4 bg-red-500" />
                <span className="w-4 h-4 bg-orange-500" />
                <span className="w-4 h-4 bg-yellow-500" />
                <span className="w-4 h-4 bg-lime-500" />
                <span className="w-4 h-4 bg-green-600" />
              </div>
              <span className="text-gray-500">High</span>
            </div>
          </div>
          <KenyaMap
            onCountyClick={handleCountyClick}
            selectedCountyCode={selectedCounty?.code}
            highlightedRegions={highlightedRegions}
          />
          <p className="text-xs text-gray-400 mt-2 text-center">
            Click any county to see {candidate.name.split(' ')[0]}'s
            constituency-level strength
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">
            Top 10 Strongholds
          </h3>
          {topRegions.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                data={topRegions}
                layout="vertical"
                margin={{ left: 20, right: 20, top: 5, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={80}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip />
                <Bar dataKey="influence" fill="#3b82f6" radius={[0, 4, 4, 0]}>
                  {topRegions.map((entry, idx) => (
                    <Cell
                      key={idx}
                      fill={
                        entry.influence >= 70
                          ? '#16a34a'
                          : entry.influence >= 50
                          ? '#84cc16'
                          : entry.influence >= 30
                          ? '#eab308'
                          : '#f97316'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500">No data available</p>
          )}
        </div>
      </div>

      {/* Selected County Drill-Down */}
      {selectedCounty && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-semibold">
                Constituency Breakdown — {selectedCounty.name}
              </h3>
              <p className="text-sm text-gray-500">
                Estimated influence across constituencies
              </p>
            </div>
            <button
              onClick={() => {
                setSelectedCounty(null);
                setConstituencyStats([]);
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {loadingConstituencies ? (
            <div className="flex justify-center py-8">
              <div className="spinner"></div>
            </div>
          ) : constituencyStats.length === 0 ? (
            <p className="text-gray-500 py-4">
              No constituency data available.
            </p>
          ) : (
            <div className="space-y-3">
              {constituencyStats.map((c, idx) => (
                <div key={idx} className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <div>
                      <h4 className="font-semibold">{c.name}</h4>
                      <p className="text-xs text-gray-500">
                        {c.wards} wards
                      </p>
                    </div>
                    <span className="text-lg font-bold text-blue-600">
                      {c.influence.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 rounded-full h-2 transition-all"
                      style={{ width: `${Math.min(c.influence, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-4 px-6">
            {['regions', 'all-data'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-2 border-b-2 font-medium text-sm transition ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab === 'regions'
                  ? 'Regional Ranking'
                  : 'Full Data Table'}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'regions' && (
            <div>
              <input
                type="text"
                placeholder="Search regions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="space-y-3">
                {filteredRegions.map((r, idx) => (
                  <div
                    key={r.region_id}
                    className="border border-gray-100 rounded-lg p-4 hover:shadow-md transition"
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-3">
                        <span className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-semibold text-gray-600">
                          {idx + 1}
                        </span>
                        <div>
                          <h4 className="font-semibold">{r.region}</h4>
                          <p className="text-xs text-gray-500">
                            {r.mentions} mentions
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-blue-600">
                          {(r.influence || 0).toFixed(1)}%
                        </p>
                        <p className="text-xs text-gray-500">
                          Support: {(r.support || 0).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                      <div
                        className="bg-blue-500 rounded-full h-2 transition-all"
                        style={{
                          width: `${Math.min(r.influence || 0, 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'all-data' && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-3">Region</th>
                    <th className="text-right py-2 px-3">Influence</th>
                    <th className="text-right py-2 px-3">Support</th>
                    <th className="text-right py-2 px-3">Mentions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRegions.map((r) => (
                    <tr
                      key={r.region_id}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="py-2 px-3 font-medium">{r.region}</td>
                      <td className="py-2 px-3 text-right">
                        {(r.influence || 0).toFixed(1)}%
                      </td>
                      <td className="py-2 px-3 text-right">
                        {(r.support || 0).toFixed(1)}%
                      </td>
                      <td className="py-2 px-3 text-right">
                        {r.mentions || 0}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CandidateProfile;