import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { getConstituenciesByCounty, getWardsByConstituency } from 'osm-kenya-boundaries';
import * as d3 from 'd3-geo'; // For projecting lat/lng to SVG coordinates

const KenyaMap = ({ onCountyClick , selectedCountyCode = null}) => {
  const [geojson, setGeojson] = useState(null);
  const [hoveredCounty, setHoveredCounty] = useState(null);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, name: '', code: '' });

  // Load GeoJSON boundary data
  useEffect(() => {
    fetch('/assets/kenya-counties.geojson')
      .then(res => res.json())
      .then(data => setGeojson(data))
      .catch(err => console.error('GeoJSON load failed:', err));
  }, []);

  // Use d3-geo to create a projection mapping lat/lng to SVG coordinates
  const projection = useMemo(() => {
    if (!geojson) return null;
    return d3.geoMercator().fitSize([800, 800], geojson);
  }, [geojson]);

  const pathGenerator = useMemo(() => {
    if (!projection) return null;
    return d3.geoPath().projection(projection);
  }, [projection]);

  // Mouse enter county: lift effect + show tooltip
  const handleMouseEnter = useCallback((event, feature) => {
    const countyCode = feature.properties.county_code || feature.properties.CODE;
    const countyName = feature.properties.county_name || feature.properties.NAME_1;
    
    setHoveredCounty(countyCode);
    setTooltip({
      visible: true,
      x: event.nativeEvent.offsetX,
      y: event.nativeEvent.offsetY,
      name: countyName,
      code: countyCode,
    });
  }, []);

  // Mouse leave county
  const handleMouseLeave = useCallback(() => {
    setHoveredCounty(null);
    setTooltip({ visible: false, x: 0, y: 0, name: '', code: '' });
  }, []);

  // Click county: fetch constituencies and callback
  const handleClick = useCallback((feature) => {
    const countyCode = feature.properties.county_code || feature.properties.CODE;
    const countyName = feature.properties.county_name || feature.properties.NAME_1;

    // Use osm-kenya-boundaries to get constituencies
    const constituencies = getConstituenciesByCounty(countyCode);
    
    // Assemble data structure
    const countyData = {
      code: countyCode,
      name: countyName,
      constituencies: constituencies.map(c => ({
        name: c.constituency_name,
        wards: getWardsByConstituency(c.constituency_name),
      })),
    };

    if (onCountyClick) {
      onCountyClick(countyData);
    }
  }, [onCountyClick]);

  if (!geojson || !pathGenerator) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="relative w-full">
      <style>{`
        .county-path {
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          cursor: pointer;
        }
        .county-path:hover {
          transform: translateY(-6px) scale(1.02);
          filter: drop-shadow(0 12px 20px rgba(0,0,0,0.35));
          fill: #38bdf8 !important;
          stroke: #0284c7;
          stroke-width: 2;
        }
        .county-path.dimmed {
          opacity: 0.35;
          transition: opacity 0.25s ease;
        }
        .county-path.selected {
          fill: #0284c7 !important;
          stroke: #0369a1;
          stroke-width: 2;
        }
          
      `}</style>

      <svg
        viewBox="0 0 800 800"
        className="w-full h-auto max-h-[80vh]"
        style={{ background: 'transparent' }}
      >
        {/* County paths layer */}
        {geojson.features.map((feature, i) => {
          const countyCode = feature.properties.county_code || feature.properties.CODE;
          const isHovered = hoveredCounty === countyCode;
          const isSelected = selectedCountyCode === countyCode;
          const isAnyHovered = hoveredCounty !== null;

          return (
            <path
              key={i}
              d={pathGenerator(feature)}
              className={`county-path ${isAnyHovered && !isHovered ? 'dimmed' : ''} ${isSelected ? 'selected' : ''}`}
              fill={isSelected ? '#0284c7' : '#38bdf8'}
              stroke={isSelected ? '#0369a1' : '#0284c7'}
              strokeWidth= {isSelected ? 2 : 1}
              onMouseEnter={(e) => handleMouseEnter(e, feature)}
              onMouseLeave={handleMouseLeave}
              onClick={() => handleClick(feature)}
            />
          );
        })}
      </svg>

      {/* Hover tooltip */}
      {tooltip.visible && (
        <div
          className="absolute pointer-events-none bg-gray-900 text-white px-3 py-2 rounded-lg text-sm shadow-xl z-10"
          style={{ left: tooltip.x + 12, top: tooltip.y + 12 }}
        >
          <p className="font-semibold">{tooltip.name}</p>
          <p className="text-xs text-gray-300">Code: {tooltip.code}</p>
          <p className="text-xs text-blue-300 mt-1">Click to view constituencies</p>
        </div>
      )}
    </div>
  );
};

export default KenyaMap;