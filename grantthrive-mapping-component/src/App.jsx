import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { MapPin, Filter, Search, DollarSign, Building, Calendar, ExternalLink, Heart, GraduationCap, Leaf, Users, Shield, Briefcase, Laptop, Palette } from 'lucide-react';
import './App.css';

const GrantMapping = () => {
  const [grants, setGrants] = useState([]);
  const [filteredGrants, setFilteredGrants] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedState, setSelectedState] = useState('all');
  const [selectedSize, setSelectedSize] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGrant, setSelectedGrant] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load national grant data from public folder
    fetch('/grant_mapping_data.json')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to load grant data');
        }
        return response.json();
      })
      .then(data => {
        console.log('Loading national grant data:', data.length, 'grants');
        setGrants(data);
        setFilteredGrants(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error loading national grant data:', error);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    // Filter grants based on selected criteria
    let filtered = grants;

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(grant => grant.category.name === selectedCategory);
    }

    if (selectedState !== 'all') {
      filtered = filtered.filter(grant => grant.location.state === selectedState);
    }

    if (selectedSize !== 'all') {
      filtered = filtered.filter(grant => grant.size_category === selectedSize);
    }

    if (searchTerm) {
      filtered = filtered.filter(grant => 
        grant.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        grant.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        grant.agency.toLowerCase().includes(searchTerm.toLowerCase()) ||
        grant.recipient.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredGrants(filtered);
  }, [grants, selectedCategory, selectedState, selectedSize, searchTerm]);

  // Calculate statistics
  const totalValue = filteredGrants.reduce((sum, grant) => sum + grant.value, 0);
  const averageValue = filteredGrants.length > 0 ? totalValue / filteredGrants.length : 0;
  const statesCovered = new Set(filteredGrants.map(grant => grant.location.state)).size;

  // Format currency
  const formatCurrency = (amount) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    } else {
      return `$${amount.toLocaleString()}`;
    }
  };

  // Get unique values for filters
  const uniqueCategories = [...new Set(grants.map(grant => grant.category.name))];
  const uniqueStates = [...new Set(grants.map(grant => grant.location.state))].sort();
  const uniqueSizes = ['Small', 'Medium', 'Large', 'Major'];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading national grant data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <MapPin className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">GrantThrive Interactive Grant Mapping</h1>
              <p className="text-gray-600">Explore Australian Government grant funding across the nation</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Building className="w-8 h-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Grants</p>
                  <p className="text-2xl font-bold text-gray-900">{filteredGrants.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <DollarSign className="w-8 h-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Value</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalValue)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Calendar className="w-8 h-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Average Value</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(averageValue)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <MapPin className="w-8 h-8 text-orange-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">States Covered</p>
                  <p className="text-2xl font-bold text-gray-900">{statesCovered}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="map" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="map" className="flex items-center space-x-2">
              <MapPin className="w-4 h-4" />
              <span>Interactive Map</span>
            </TabsTrigger>
            <TabsTrigger value="list" className="flex items-center space-x-2">
              <Building className="w-4 h-4" />
              <span>Grant List</span>
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center space-x-2">
              <DollarSign className="w-4 h-4" />
              <span>Analytics</span>
            </TabsTrigger>
          </TabsList>

          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Filter className="w-5 h-5" />
                <span>Filters</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Search grants..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>

                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Categories" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Categories</SelectItem>
                    {uniqueCategories.map(category => (
                      <SelectItem key={category} value={category}>{category}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={selectedState} onValueChange={setSelectedState}>
                  <SelectTrigger>
                    <SelectValue placeholder="All States" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All States</SelectItem>
                    {uniqueStates.map(state => (
                      <SelectItem key={state} value={state}>{state}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={selectedSize} onValueChange={setSelectedSize}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Sizes" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Sizes</SelectItem>
                    {uniqueSizes.map(size => (
                      <SelectItem key={size} value={size}>{size}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Button 
                  variant="outline" 
                  onClick={() => {
                    setSelectedCategory('all');
                    setSelectedState('all');
                    setSelectedSize('all');
                    setSearchTerm('');
                  }}
                  className="w-full"
                >
                  Clear Filters
                </Button>
              </div>
            </CardContent>
          </Card>

          <TabsContent value="map" className="space-y-6">
            {/* Enhanced Interactive Map */}
            <Card>
              <CardHeader>
                <CardTitle>Grant Distribution Map</CardTitle>
                <CardDescription>
                  Interactive map showing grant locations across Australia with comprehensive national data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="relative w-full h-96 bg-gradient-to-br from-blue-50 to-green-50 rounded-lg border-2 border-gray-200 overflow-hidden">
                  
                  {/* Map Background */}
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-100 via-green-50 to-blue-50">
                    
                    {/* Australia Outline Representation */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="relative w-80 h-60">
                        
                        {/* Regional Clusters for all states */}
                        {[
                          { name: 'Sydney Metro', grants: filteredGrants.filter(g => g.location?.state === 'NSW'), color: '#e74c3c', left: '85%', top: '45%' },
                          { name: 'Brisbane Metro', grants: filteredGrants.filter(g => g.location?.state === 'QLD'), color: '#f39c12', left: '80%', top: '25%' },
                          { name: 'Perth Metro', grants: filteredGrants.filter(g => g.location?.state === 'WA'), color: '#9b59b6', left: '15%', top: '40%' },
                          { name: 'Adelaide Metro', grants: filteredGrants.filter(g => g.location?.state === 'SA'), color: '#e67e22', left: '60%', top: '70%' },
                          { name: 'Melbourne Metro', grants: filteredGrants.filter(g => g.location?.state === 'VIC'), color: '#3498db', left: '70%', top: '85%' },
                          { name: 'Hobart', grants: filteredGrants.filter(g => g.location?.state === 'TAS'), color: '#27ae60', left: '75%', top: '95%' },
                          { name: 'Darwin', grants: filteredGrants.filter(g => g.location?.state === 'NT'), color: '#16a085', left: '50%', top: '5%' },
                          { name: 'Canberra', grants: filteredGrants.filter(g => g.location?.state === 'ACT'), color: '#8e44ad', left: '85%', top: '60%' }
                        ].filter(region => region.grants.length > 0).map((region, index) => {
                          const totalValue = region.grants.reduce((sum, grant) => sum + grant.value, 0);
                          const grantCount = region.grants.length;
                          
                          return (
                            <div
                              key={region.name}
                              className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer group"
                              style={{ left: region.left, top: region.top }}
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
                                  <div>{formatCurrency(totalValue)}</div>
                                </div>
                              </div>
                            </div>
                          );
                        })}

                        {/* State Labels */}
                        <div className="absolute" style={{ left: '80%', top: '50%' }}>
                          <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded shadow">NSW</span>
                        </div>
                        <div className="absolute" style={{ left: '75%', top: '30%' }}>
                          <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded shadow">QLD</span>
                        </div>
                        <div className="absolute" style={{ left: '10%', top: '45%' }}>
                          <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded shadow">WA</span>
                        </div>
                        <div className="absolute" style={{ left: '55%', top: '75%' }}>
                          <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded shadow">SA</span>
                        </div>
                        <div className="absolute" style={{ left: '65%', top: '90%' }}>
                          <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded shadow">VIC</span>
                        </div>
                        <div className="absolute" style={{ left: '70%', top: '100%' }}>
                          <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded shadow">TAS</span>
                        </div>
                        <div className="absolute" style={{ left: '45%', top: '10%' }}>
                          <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded shadow">NT</span>
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
                        {['Major', 'Large', 'Medium', 'Small'].map(size => {
                          const getSizeMultiplier = (sizeCategory) => {
                            switch (sizeCategory) {
                              case 'Major': return 2.5;
                              case 'Large': return 2.0;
                              case 'Medium': return 1.5;
                              case 'Small': return 1.0;
                              default: return 1.0;
                            }
                          };
                          
                          return (
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
                          );
                        })}
                      </div>
                    </div>

                    {/* Statistics Panel */}
                    <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-3">
                      <h4 className="text-sm font-semibold text-gray-800 mb-2">Map Statistics</h4>
                      <div className="space-y-1 text-xs text-gray-600">
                        <div>Grants Shown: {filteredGrants.length}</div>
                        <div>Regions: {statesCovered}</div>
                        <div>Total Value: {formatCurrency(totalValue)}</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Interactive Features Info */}
                <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-blue-900 mb-2">🗺️ National Coverage Features</h4>
                  <div className="text-sm text-blue-800 space-y-1">
                    <div>• <strong>Complete Coverage:</strong> All 8 Australian states and territories represented</div>
                    <div>• <strong>Regional Clusters:</strong> Circles show grant concentration by major cities</div>
                    <div>• <strong>Real Data:</strong> Based on authentic Australian Government grant awards</div>
                    <div>• <strong>Interactive Filtering:</strong> Filter by state, category, size, or search terms</div>
                    <div>• <strong>Live Statistics:</strong> Real-time updates based on applied filters</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="list" className="space-y-6">
            {/* Grant List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredGrants.slice(0, 12).map((grant) => (
                <Card key={grant.id} className="hover:shadow-lg transition-shadow cursor-pointer">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <Badge 
                        variant="secondary" 
                        className="mb-2"
                        style={{ backgroundColor: grant.category.color + '20', color: grant.category.color }}
                      >
                        {grant.size_category}
                      </Badge>
                      <Badge variant="outline">{grant.location.state}</Badge>
                    </div>
                    <CardTitle className="text-lg line-clamp-2">{grant.title}</CardTitle>
                    <CardDescription className="line-clamp-2">{grant.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Value:</span>
                        <span className="font-semibold text-green-600">{grant.value_formatted}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Recipient:</span>
                        <span className="text-sm font-medium truncate ml-2">{grant.recipient}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Location:</span>
                        <span className="text-sm">{grant.location.city}, {grant.location.state}</span>
                      </div>
                      <div className="flex items-center space-x-2 mt-3">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: grant.category.color }}
                        ></div>
                        <span className="text-sm text-gray-600">{grant.category.name}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {filteredGrants.length > 12 && (
              <div className="text-center">
                <Button variant="outline">
                  View All {filteredGrants.length} Grants
                </Button>
              </div>
            )}
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            {/* Analytics Dashboard */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Category Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>Category Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {uniqueCategories.map(category => {
                      const categoryGrants = filteredGrants.filter(g => g.category.name === category);
                      const percentage = filteredGrants.length > 0 ? (categoryGrants.length / filteredGrants.length) * 100 : 0;
                      const categoryColor = categoryGrants[0]?.category.color || '#gray';
                      
                      return (
                        <div key={category} className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">{category}</span>
                            <span className="text-sm text-gray-600">{categoryGrants.length} ({percentage.toFixed(1)}%)</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="h-2 rounded-full transition-all duration-300"
                              style={{ 
                                width: `${percentage}%`,
                                backgroundColor: categoryColor
                              }}
                            ></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* State Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>State Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {uniqueStates.map(state => {
                      const stateGrants = filteredGrants.filter(g => g.location.state === state);
                      const percentage = filteredGrants.length > 0 ? (stateGrants.length / filteredGrants.length) * 100 : 0;
                      
                      return (
                        <div key={state} className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">{state}</span>
                            <span className="text-sm text-gray-600">{stateGrants.length} ({percentage.toFixed(1)}%)</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default GrantMapping;

