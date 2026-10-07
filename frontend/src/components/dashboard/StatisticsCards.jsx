import React from 'react';

const StatCard = ({ icon, label, value, color = 'blue' }) => {
  const colors = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    purple: 'bg-purple-100 text-purple-600',
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-5 hover:shadow-lg transition">
      <div className="flex items-center">
        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${colors[color]}`}>
          <span className="text-2xl">{icon}</span>
        </div>
        <div className="ml-4">
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold">{value}</p>
        </div>
      </div>
    </div>
  );
};

const StatisticsCards = ({ data }) => {
  if (!data) return null;

  const stats = data.stats || {};

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <StatCard 
        icon="🗳️"
        label="Total Candidates"
        value={stats.total_candidates || 0}
        color="blue"
      />
      <StatCard 
        icon="🏛️"
        label="Regions"
        value={stats.total_regions || 0}
        color="green"
      />
      <StatCard 
        icon="📰"
        label="News Articles"
        value={stats.total_news || 0}
        color="purple"
      />
      <StatCard 
        icon="📊"
        label="Avg Influence"
        value={`${(stats.avg_influence || 0).toFixed(1)}%`}
        color="yellow"
      />
    </div>
  );
};

export default StatisticsCards;
