import React from 'react';

const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white mt-12">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-lg font-bold mb-3">🗳️ Kenya Election Tracker</h3>
            <p className="text-gray-400 text-sm">
              Real-time election influence tracking across Kenya. Monitor candidates,
              regions, and public sentiment.
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-3">Quick Links</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><a href="/" className="hover:text-white">Dashboard</a></li>
              <li><a href="/analytics" className="hover:text-white">Analytics</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-3">Data Sources</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>Live News Feeds</li>
              <li>Social Media</li>
              <li>Public Records</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-700 mt-6 pt-4 text-center text-sm text-gray-400">
          © {new Date().getFullYear()} Kenya Election Tracker. All rights reserved.
        </div>
      </div>
    </footer>
  );
};

export default Footer;
