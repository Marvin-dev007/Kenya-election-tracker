import React, { createContext, useState, useContext } from 'react';

const RegionContext = createContext();

export const RegionProvider = ({ children }) => {
  const [regions, setRegions] = useState([]);
  const [currentRegion, setCurrentRegion] = useState(null);

  const value = {
    regions,
    setRegions,
    currentRegion,
    setCurrentRegion,
  };

  return (
    <RegionContext.Provider value={value}>
      {children}
    </RegionContext.Provider>
  );
};

export const useRegionContext = () => {
  const context = useContext(RegionContext);
  if (!context) {
    throw new Error('useRegionContext must be used within a RegionProvider');
  }
  return context;
};

export default RegionContext;
