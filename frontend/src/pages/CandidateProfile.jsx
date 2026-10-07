import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useCandidateDetail, useCandidateRegions } from '../hooks/useApi';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

const CandidateProfile = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('overview');
  
  const { data: candidate, loading: candidateLoading } = useCandidateDetail(id);
  const { data: regions, loading: regionsLoading } = useCandidateRegions(id);

  if (!id || id === 'null' || id === 'undefined') {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-600">No candidate selected</h2>
        <Link to="/" className="text-blue-500 hover:underline mt-4 inline-block">
          Back to Dashboard
        </Link>
      </div>
    );
  }

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
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center space-x-6">
          <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center">
            <span className="text-4xl">👤</span>
          </div>
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-800">{candidate.name}</h1>
            <div className="flex items-center space-x-3 mt-1">
              <span 
                className="px-3 py-1 rounded-full text-sm font-medium"
                style={{
                  backgroundColor: candidate.party_detail?.color + '20',
                  color: candidate.party_detail?.color
                }}
              >
                {candidate.party_detail?.name}
              </span>
              <span className="text-sm text-gray-500">{candidate.position}</span>
            </div>
            <p className="text-gray-600 mt-2">{candidate.biography}</p>
          </div>
          <Link
            to="/"
            className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
          >
            ← Back
          </Link>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-4 px-6">
            {['overview', 'regions'].map((tab) => (
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
          {activeTab === 'overview' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Candidate Overview</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Total Regions</p>
                  <p className="text-2xl font-bold">{regions?.length || 0}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Average Influence</p>
                  <p className="text-2xl font-bold">
                    {regions?.length > 0 
                      ? (regions.reduce((sum, r) => sum + r.influence, 0) / regions.length).toFixed(1)
                      : '0'}%
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Average Support</p>
                  <p className="text-2xl font-bold">
                    {regions?.length > 0 
                      ? (regions.reduce((sum, r) => sum + r.support, 0) / regions.length).toFixed(1)
                      : '0'}%
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Total Mentions</p>
                  <p className="text-2xl font-bold">
                    {regions?.reduce((sum, r) => sum + r.mentions, 0) || 0}
                  </p>
                </div>
              </div>

              {regions && regions.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-semibold mb-3">Regional Performance</h4>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={regions}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="region" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="influence" fill="#3b82f6" name="Influence %" />
                      <Bar dataKey="support" fill="#10b981" name="Support %" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}

          {activeTab === 'regions' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Regional Influence</h3>
              <div className="space-y-3">
                {regions?.map((region) => (
                  <div key={region.region_id} className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold">{region.region}</h4>
                        <p className="text-sm text-gray-500">{region.mentions} mentions</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-blue-600">
                          {region.influence.toFixed(1)}%
                        </p>
                        <p className="text-xs text-gray-500">Influence</p>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                      <div 
                        className="bg-blue-500 rounded-full h-2 transition-all"
                        style={{ width: `${region.influence}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CandidateProfile;
