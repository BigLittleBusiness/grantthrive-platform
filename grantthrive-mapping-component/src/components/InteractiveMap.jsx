import React, { useState, useEffect } from 'react';

const InteractiveMap = ({ grants, filters }) => {
  const [mapData, setMapData] = useState(null);
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [hoveredMarker, setHoveredMarker] = useState(null);

  useEffect(() => {
    // Load the enhanced mapping data
    import('../assets/grant_mapping_data.json')
      .then(data => {
        setMapData(data.default);
      })
      .catch(error => {
        console.error('Error loading map data:', error);
      });
  }, []);

  // Filter grants based on current filters
  const filteredGrants = grants.filter(grant => {
    if (filters.search && !grant.title.toLowerCase().includes(filters.search.toLowerCase()) &&
        !grant.description.toLowerCase().includes(filters.search.toLowerCase())) {
      return false;
    }
    if (filters.category && filters.category !== 'All Categories' && 
        grant.category.primary !== filters.category) {
      return false;
    }
    if (filters.state && filters.state !== 'All States' && 
        grant.location.state !== filters.state) {
      return false;
    }
    if (filters.size && filters.size !== 'All Sizes' && 
        grant.size_category !== filters.size) {
      return false;
    }
    return true;
  });

  // Create markers from filtered grants
  const markers = filteredGrants
    .filter(grant => grant.location?.coordinates)
    .map(grant => ({
      id: grant.id,
      lat: grant.location.coordinates.lat,
      lng: grant.location.coordinates.lng,
      title: grant.title,
      value: grant.value,
      value_formatted: grant.value_formatted,
      category: grant.category.primary,
      color: grant.category.color,
      icon: grant.category.icon,
      size_category: grant.size_category,
      location_name: `${grant.location.city || ''}, ${grant.location.state || ''}`,
      recipient: grant.recipient,
      agency: grant.agency,
      grant: grant
    }));

  // Regional clusters for overview
  const regions = [
    {
      name: 'Adelaide Metro',
      center: { lat: -34.9285, lng: 138.6007 },
      grants: filteredGrants.filter(g => g.location?.state === 'SA'),
      color: '#e74c3c'
    },
    {
      name: 'Melbourne Metro', 
      center: { lat: -37.8136, lng: 144.9631 },
      grants: filteredGrants.filter(g => g.location?.state === 'VIC'),
      color: '#3498db'
    },
    {
      name: 'Canberra',
      center: { lat: -35.2809, lng: 149.1300 },
      grants: filteredGrants.filter(g => g.location?.state === 'ACT'),
      color: '#27ae60'
    }
  ].filter(region => region.grants.length > 0);

  const getSizeMultiplier = (sizeCategory) => {
    switch (sizeCategory) {
      case 'Major': return 2.5;
      case 'Large': return 2.0;
      case 'Medium': return 1.5;
      case 'Small': return 1.0;
      default: return 1.0;
    }
  };

  const formatValue = (value) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    } else {
      return `$${value.toFixed(0)}`;
    }
  };

  return (
    <div className="w-full h-full">
      {/* Map Container */}
      <div className="relative w-full h-96 bg-gradient-to-br from-blue-50 to-green-50 rounded-lg border-2 border-gray-200 overflow-hidden">
        
        {/* Map Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-100 via-green-50 to-blue-50">
          
          {/* Australia Outline Representation */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="relative w-80 h-60">
              
              {/* Regional Clusters */}
              {regions.map((region, index) => {
                const totalValue = region.grants.reduce((sum, grant) => sum + grant.value, 0);
                const grantCount = region.grants.length;
                
                return (
                  <div
                    key={region.name}
                    className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer group"
                    style={{
                      left: region.name === 'Adelaide Metro' ? '25%' : 
                            region.name === 'Melbourne Metro' ? '70%' : '85%',
                      top: region.name === 'Adelaide Metro' ? '70%' : 
                           region.name === 'Melbourne Metro' ? '85%' : '60%'
                    }}
                  >
                    {/* Regional Cluster Circle */}
                    <div 
                      className="rounded-full border-4 border-white shadow-lg flex items-center justify-center text-white font-bold transition-all duration-300 group-hover:scale-110"
                      style={{ 
                        backgroundColor: region.color,
                        width: `${Math.max(40, Math.min(80, grantCount * 8))}px`,
                        height: `${Math.max(40, Math.min(80, grantCount * 8))}px`
                      }}
                    >
                      {grantCount}
                    </div>
                    
                    {/* Regional Info Tooltip */}
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                      <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap">
                        <div className="font-semibold">{region.name}</div>
                        <div>{grantCount} grants</div>
                        <div>{formatValue(totalValue)}</div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Individual Grant Markers */}
              {markers.slice(0, 15).map((marker, index) => (
                <div
                  key={marker.id}
                  className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer group"
                  style={{
                    left: `${20 + (index % 5) * 15}%`,
                    top: `${30 + Math.floor(index / 5) * 20}%`,
                    zIndex: hoveredMarker === marker.id ? 20 : 10
                  }}
                  onMouseEnter={() => setHoveredMarker(marker.id)}
                  onMouseLeave={() => setHoveredMarker(null)}
                  onClick={() => setSelectedMarker(marker)}
                >
                  {/* Grant Marker */}
                  <div 
                    className="rounded-full border-2 border-white shadow-md transition-all duration-300 group-hover:scale-125"
                    style={{ 
                      backgroundColor: marker.color,
                      width: `${12 * getSizeMultiplier(marker.size_category)}px`,
                      height: `${12 * getSizeMultiplier(marker.size_category)}px`
                    }}
                  />
                  
                  {/* Marker Tooltip */}
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                    <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap max-w-48">
                      <div className="font-semibold truncate">{marker.title}</div>
                      <div>{marker.value_formatted}</div>
                      <div>{marker.location_name}</div>
                    </div>
                  </div>
                </div>
              ))}

              {/* State Labels */}
              <div className="absolute" style={{ left: '15%', top: '75%' }}>
                <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded shadow">SA</span>
              </div>
              <div className="absolute" style={{ left: '65%', top: '90%' }}>
                <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded shadow">VIC</span>
              </div>
              <div className="absolute" style={{ left: '80%', top: '65%' }}>
                <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded shadow">ACT</span>
              </div>
            </div>
          </div>

          {/* Map Legend */}
          <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3">
            <h4 className="text-sm font-semibold text-gray-800 mb-2">Grant Size</h4>
            <div className="space-y-1">
              {['Major', 'Large', 'Medium', 'Small'].map(size => (
                <div key={size} className="flex items-center space-x-2">
                  <div 
                    className="rounded-full bg-blue-500"
                    style={{ 
                      width: `${12 * getSizeMultiplier(size)}px`,
                      height: `${12 * getSizeMultiplier(size)}px`
                    }}
                  />
                  <span className="text-xs text-gray-600">{size}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Statistics Panel */}
          <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-3">
            <h4 className="text-sm font-semibold text-gray-800 mb-2">Map Statistics</h4>
            <div className="space-y-1 text-xs text-gray-600">
              <div>Grants Shown: {markers.length}</div>
              <div>Regions: {regions.length}</div>
              <div>Total Value: {formatValue(filteredGrants.reduce((sum, grant) => sum + grant.value, 0))}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Grant Detail Modal */}
      {selectedMarker && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setSelectedMarker(null)}>
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-semibold text-gray-900 pr-4">{selectedMarker.title}</h3>
              <button 
                onClick={() => setSelectedMarker(null)}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-green-600">{selectedMarker.value_formatted}</span>
                <span 
                  className="px-2 py-1 rounded-full text-xs font-medium text-white"
                  style={{ backgroundColor: selectedMarker.color }}
                >
                  {selectedMarker.size_category}
                </span>
              </div>
              
              <div className="text-sm text-gray-600">
                <div><strong>Category:</strong> {selectedMarker.category}</div>
                <div><strong>Location:</strong> {selectedMarker.location_name}</div>
                <div><strong>Recipient:</strong> {selectedMarker.recipient}</div>
                <div><strong>Agency:</strong> {selectedMarker.agency}</div>
              </div>
              
              {selectedMarker.grant.description && (
                <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                  {selectedMarker.grant.description}
                </div>
              )}
              
              <div className="flex space-x-2 pt-2">
                <a 
                  href={selectedMarker.grant.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex-1 bg-blue-600 text-white text-center py-2 px-4 rounded hover:bg-blue-700 transition-colors text-sm"
                >
                  View Details
                </a>
                <button 
                  onClick={() => setSelectedMarker(null)}
                  className="flex-1 bg-gray-200 text-gray-800 text-center py-2 px-4 rounded hover:bg-gray-300 transition-colors text-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Interactive Features Info */}
      <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">🗺️ Interactive Map Features</h4>
        <div className="text-sm text-blue-800 space-y-1">
          <div>• <strong>Regional Clusters:</strong> Large circles show grant concentration by region</div>
          <div>• <strong>Individual Markers:</strong> Small dots represent specific grants (hover for details)</div>
          <div>• <strong>Size Coding:</strong> Marker size indicates grant value (Major, Large, Medium, Small)</div>
          <div>• <strong>Color Coding:</strong> Colors represent grant categories</div>
          <div>• <strong>Click markers</strong> for detailed grant information</div>
        </div>
      </div>
    </div>
  );
};

export default InteractiveMap;

