import React from 'react';
import { Link } from 'react-router-dom';

const CandidateCard = ({ candidate, index }) => {
  const influenceColor = candidate.average_influence > 70 ? 'text-green-600' :
                         candidate.average_influence > 40 ? 'text-yellow-600' :
                         'text-red-600';

  return (
    <Link to={`/candidate/${candidate.id}`}>
      <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition cursor-pointer">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
            <span className="text-2xl">👤</span>
          </div>
          <div className="flex-1">
            <h4 className="font-semibold">{candidate.name}</h4>
            <div className="flex items-center space-x-2">
              <span 
                className="text-xs px-2 py-1 rounded-full"
                style={{
                  backgroundColor: candidate.party_color + '20',
                  color: candidate.party_color
                }}
              >
                {candidate.party}
              </span>
              <span className="text-xs text-gray-500">
                {candidate.regions} regions
              </span>
            </div>
          </div>
          <div className="text-right">
            <p className={`text-xl font-bold ${influenceColor}`}>
              {candidate.average_influence?.toFixed(1) || 0}%
            </p>
            <p className="text-xs text-gray-500">Influence Score</p>
          </div>
        </div>
      </div>
    </Link>
  );
};

const CandidateList = ({ candidates, title = "Top Candidates" }) => {
  if (!candidates || candidates.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center text-gray-500">
        No candidates found
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-bold mb-4">{title}</h3>
      <div className="space-y-3">
        {candidates.map((candidate, index) => (
          <div key={candidate.id} className="relative">
            {index < 3 && (
              <div className="absolute -left-2 top-1/2 transform -translate-y-1/2">
                <span className={`text-xs font-bold px-2 py-1 rounded-full ${
                  index === 0 ? 'bg-yellow-400' :
                  index === 1 ? 'bg-gray-300' :
                  'bg-orange-300'
                }`}>
                  #{index + 1}
                </span>
              </div>
            )}
            <CandidateCard candidate={candidate} index={index} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default CandidateList;
