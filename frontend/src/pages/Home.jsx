import React, { useState } from 'react';
import toast from 'react-hot-toast';
import KenyaMap from '../components/map/KenyaMap';
import CountyDetailPanel from '../components/map/CountyDetailPanel';
import StatisticsCards from '../components/dashboard/StatisticsCards';
import CandidateList from '../components/dashboard/CandidateList';
import { useDashboard, useInfluenceSummary } from '../hooks/useApi';

const Home = () => {
  const [selectedCounty, setSelectedCounty] = useState(null);

  // const KenyaMapComponent = React.useMemo(() => <KenyaMap onCountyClick={handleCountyClick} />, []);
  const { data: dashboardData, loading: dashboardLoading } = useDashboard();
  const { data: influenceData, loading: influenceLoading } = useInfluenceSummary();

  const handleCountyClick = (county) => {
    setSelectedCounty(county);
    toast.success(`${county.name} selected`);
  };

  if (dashboardLoading || influenceLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">
          Kenya Election Dashboard
        </h1>
        <p className="text-gray-500 mt-1">
          Click any county on the map to see its constituencies and wards
        </p>
      </div>

      <StatisticsCards data={dashboardData} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-lg p-4">
            <h3 className="text-lg font-semibold mb-3">
              Interactive Map
              {selectedCounty && (
                <span className="ml-2 text-sm font-normal text-blue-600">
                  — Selected: {selectedCounty.name}
                </span>
              )}
            </h3>
            <KenyaMap onCountyClick={handleCountyClick} />
          </div>
        </div>
        <div>
          <CandidateList
            candidates={influenceData?.top_candidates || []}
            title="Top Candidates by Influence"
          />
        </div>
      </div>

      {/* Recent News */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">📰 Recent News</h3>
        <div className="space-y-3">
          {dashboardData?.recent_news?.slice(0, 5).map((news) => (
          <div key={news.id} className="border-b border-gray-100 pb-3 last:border-0">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <h4 className="font-medium text-gray-800">{news.title}</h4>
                <div className="flex items-center flex-wrap gap-2 mt-1">
                  <span className="text-sm text-gray-500">{news.source}</span>
                  <span className="text-sm text-gray-400">
                    {new Date(news.published_date).toLocaleDateString()}
                  </span>
                  {news.sentiment_label && (
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      news.sentiment_label === 'positive' ? 'bg-green-100 text-green-700' :
                      news.sentiment_label === 'negative' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {news.sentiment_label}
                    </span>
                  )}
                </div>
              </div>
              {news.image_url && (
                <img
                  src={news.image_url}
                  alt=""
                  className="w-16 h-16 rounded object-cover flex-shrink-0"
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              )}
            </div>
          </div>
        ))}

        </div>
      </div>

      {/* Drawer overlay */}
      <CountyDetailPanel
        county={selectedCounty}
        onClose={() => setSelectedCounty(null)}
      />
    </div>
  );
};

export default Home;