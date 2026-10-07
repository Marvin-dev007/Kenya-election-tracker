import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getConstituenciesByCounty, getWardsByConstituency } from 'osm-kenya-boundaries';
import KenyaMap from '../components/map/KenyaMap';
import { useRegionDetail, useRegionCandidates } from '../hooks/useApi';

const RegionDetail = () => {
  const { id } = useParams();

  if (!id || id === 'null' || id === 'undefined') {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-600">No region selected</h2>
        <Link to="/" className="text-blue-500 hover:underline mt-4 inline-block">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  
  const [activeTab, setActiveTab] = useState('overview');
  const [constituencies, setConstituencies] = useState([]);
  const [loadingConstituencies, setLoadingConstituencies] = useState(true);


  // Backend fetches
  const { data: region, loading: regionLoading } = useRegionDetail(id);
  const { data: candidates, loading: candidatesLoading } = useRegionCandidates(id);

  // Load constituencies + wards from the boundary package once we have the county code
  useEffect(() => {
    if (!region) return;
    const handleCountyClick = async (county) => {
      setLoadingConstituencies(true);
      try {
        const res = await fetch(`/api/region/${id}/tree/`);
        const tree = await res.json();

        setConstituencies(tree.children.map((constituency) => ({
          name:constituency.name,
          code: constituency.code,
          wards: constituency.children.map((ward) => ward.name),
        }))
        );

      } catch (err) {
        console.error('Failed to load constituencies:', err);
        setConstituencies([]);
      } finally {
        setLoadingConstituencies(false);
      }

    }
    
  }, [region]);

  // Aggregate stats for the overview tab
  const stats = useMemo(() => {
    if (!candidates || candidates.length === 0) {
      return { total: 0, avgInfluence: 0, totalMentions: 0 };
    }
    const totalInfluence = candidates.reduce(
      (sum, c) => sum + (c.influence_score || 0),
      0
    );
    const totalMentions = candidates.reduce(
      (sum, c) => sum + (c.news_mentions || 0) + (c.social_mentions || 0),
      0
    );
    return {
      total: candidates.length,
      avgInfluence: totalInfluence / candidates.length,
      totalMentions,
    };
  }, [candidates]);

  if (regionLoading || candidatesLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!region) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-600">Region not found</h2>
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
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">{region.name}</h1>
            <p className="text-gray-500 mt-1">
              {region.region_type} • Code: {region.code}
              {region.population &&
                ` • Population: ${region.population.toLocaleString()}`}
            </p>
          </div>
          <Link
            to="/"
            className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </div>

      {/* Map + Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-4">
          <h3 className="text-lg font-semibold mb-3">Location on Map</h3>
          <KenyaMap
            onCountyClick={(county) => {
              // Navigate to that county's detail page if user clicks a different one
              if (county.code !== region.code) {
                window.location.href = `/region/${county.code}`;
              }
            }}
            selectedCountyCode={region.code}
          />
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Quick Stats</h3>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">Total Candidates</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Average Influence</p>
              <p className="text-2xl font-bold text-blue-600">
                {stats.avgInfluence.toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Mentions</p>
              <p className="text-2xl font-bold">
                {stats.totalMentions.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Constituencies</p>
              <p className="text-2xl font-bold">
                {loadingConstituencies ? '…' : constituencies.length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-4 px-6">
            {['overview', 'constituencies', 'candidates'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-2 border-b-2 font-medium text-sm transition ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Region Overview</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Region Type</p>
                  <p className="text-lg font-semibold capitalize">
                    {region.region_type}
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Region Code</p>
                  <p className="text-lg font-semibold">{region.code}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Population</p>
                  <p className="text-lg font-semibold">
                    {region.population
                      ? region.population.toLocaleString()
                      : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Constituencies Tab */}
          {activeTab === 'constituencies' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">
                Constituencies in {region.name}
              </h3>

              {loadingConstituencies ? (
                <div className="flex justify-center py-8">
                  <div className="spinner"></div>
                </div>
              ) : constituencies.length === 0 ? (
                <p className="text-gray-500 py-4">
                  No constituency data available for this region.
                </p>
              ) : (
                <div className="space-y-4">
                  {constituencies.map((c, idx) => (
                    <div
                      key={idx}
                      className="border border-gray-200 rounded-lg overflow-hidden"
                    >
                      <div className="bg-gray-50 px-4 py-3 flex justify-between items-center">
                        <div>
                          <h4 className="font-semibold text-gray-800">
                            {c.name}
                          </h4>
                          <p className="text-xs text-gray-500">
                            {c.wards.length} wards
                          </p>
                        </div>
                        <span className="text-xs text-gray-400">
                          #{idx + 1}
                        </span>
                      </div>
                      <div className="p-4">
                        {c.wards.length === 0 ? (
                          <p className="text-sm text-gray-400">
                            No ward data
                          </p>
                        ) : (
                          <div className="flex flex-wrap gap-2">
                            {c.wards.map((ward, wIdx) => (
                              <span
                                key={wIdx}
                                className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm"
                              >
                                {typeof ward === 'string'
                                  ? ward
                                  : ward.ward_name || ward.name}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Candidates Tab */}
          {activeTab === 'candidates' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">
                Candidates in {region.name}
              </h3>

              {!candidates || candidates.length === 0 ? (
                <p className="text-gray-500 py-4">
                  No candidate data available for this region.
                </p>
              ) : (
                <div className="space-y-4">
                  {candidates.map((c) => (
                    <Link
                      key={c.id}
                      to={`/candidate/${c.candidate}`}
                      className="block"
                    >
                      <div className="bg-gray-50 p-4 rounded-lg hover:bg-gray-100 transition">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-semibold">
                              {c.candidate_name}
                            </h4>
                            <span
                              className="text-xs px-2 py-1 rounded-full inline-block mt-1"
                              style={{
                                backgroundColor: c.party_color + '20',
                                color: c.party_color,
                              }}
                            >
                              {c.candidate_party}
                            </span>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold text-blue-600">
                              {(c.influence_score || 0).toFixed(1)}%
                            </p>
                            <p className="text-xs text-gray-500">
                              Influence
                            </p>
                          </div>
                        </div>

                        {/* Influence bar */}
                        <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                          <div
                            className="bg-blue-500 rounded-full h-2 transition-all"
                            style={{
                              width: `${Math.min(
                                c.influence_score || 0,
                                100
                              )}%`,
                            }}
                          />
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RegionDetail;