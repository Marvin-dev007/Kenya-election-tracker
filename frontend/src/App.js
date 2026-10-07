import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AppProvider } from './context/AppContext';
import { RegionProvider } from './context/RegionContext';
import { CandidateProvider } from './context/CandidateContext';
import Header from './components/common/Header';
import Footer from './components/common/Footer';
import Home from './pages/Home';
import RegionDetail from './pages/RegionDetail';
import CandidateProfile from './pages/CandidateProfile';
import Analytics from './pages/Analytics';
import './styles/globals.css';

function App() {
  return (
    <AppProvider>
      <Router>
        <div className="min-h-screen bg-gray-50 flex flex-col">
          <Header />
          <main className="flex-grow container mx-auto px-4 py-8">
            <RegionProvider>
              <CandidateProvider>
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/region/:id" element={<RegionDetail />} />
                  <Route path="/candidate/:id" element={<CandidateProfile />} />
                  <Route path="/analytics" element={<Analytics />} />
               
                </Routes>
              </CandidateProvider>
            </RegionProvider>
          </main>
          <Footer />
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 3000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
        </div>
      </Router>
    </AppProvider>
  );
}

export default App;
