import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { 
  Map, 
  MapPin, 
  Filter, 
  Search, 
  DollarSign, 
  Calendar,
  Users,
  TrendingUp,
  Camera,
  FileText,
  Star,
  MessageSquare,
  Navigation,
  Layers,
  Info
} from 'lucide-react';

const PublicGrantMap = () => {
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);
  const [markers, setMarkers] = useState([]);
  const [grantData, setGrantData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [selectedGrant, setSelectedGrant] = useState(null);
  const [filters, setFilters] = useState({
    postcode: '',
    suburb: '',
    project_status: '',
    category: ''
  });
  const [loading, setLoading] = useState(true);
  const [mapConfig, setMapConfig] = useState(null);

  // Mock grant data for demonstration
  const mockGrantData = [
    {
      id: 1,
      grant_id: 'GRANT-2024-001',
      coordinates: { lat: -33.8688, lng: 151.2093 },
      address: '123 Community Street, Sydney NSW 2000',
      suburb: 'Sydney',
      postcode: '2000',
      location_type: 'Primary',
      project: {
        title: 'Sydney Community Garden Project',
        description: 'Creating a sustainable community garden space for local residents to grow fresh produce and connect with neighbors.',
        status: 'In Progress',
        completion_percentage: 65,
        beneficiaries_count: 150,
        photos: [
          '/images/garden-progress-1.jpg',
          '/images/garden-progress-2.jpg'
        ],
        last_updated: '2024-08-25T10:30:00Z',
        is_featured: true,
        category: 'Environment',
        funding_amount: 25000,
        start_date: '2024-03-01',
        expected_completion: '2024-12-31'
      }
    },
    {
      id: 2,
      grant_id: 'GRANT-2024-002',
      coordinates: { lat: -33.8650, lng: 151.2094 },
      address: '456 Arts Lane, Sydney NSW 2000',
      suburb: 'Sydney',
      postcode: '2000',
      location_type: 'Primary',
      project: {
        title: 'Youth Arts Workshop Series',
        description: 'Weekly art workshops for young people aged 12-18, providing free access to art supplies and professional instruction.',
        status: 'Completed',
        completion_percentage: 100,
        beneficiaries_count: 85,
        photos: [
          '/images/arts-workshop-1.jpg',
          '/images/arts-workshop-2.jpg',
          '/images/arts-workshop-3.jpg'
        ],
        last_updated: '2024-08-20T14:15:00Z',
        is_featured: false,
        category: 'Arts & Culture',
        funding_amount: 15000,
        start_date: '2024-01-15',
        expected_completion: '2024-07-31'
      }
    },
    {
      id: 3,
      grant_id: 'GRANT-2024-003',
      coordinates: { lat: -33.8720, lng: 151.2070 },
      address: '789 Sports Avenue, Sydney NSW 2000',
      suburb: 'Sydney',
      postcode: '2000',
      location_type: 'Primary',
      project: {
        title: 'Community Sports Equipment Upgrade',
        description: 'Upgrading basketball courts and installing new fitness equipment in the local park for community use.',
        status: 'Planning',
        completion_percentage: 15,
        beneficiaries_count: 300,
        photos: [
          '/images/sports-planning.jpg'
        ],
        last_updated: '2024-08-28T09:00:00Z',
        is_featured: true,
        category: 'Recreation & Sports',
        funding_amount: 45000,
        start_date: '2024-09-01',
        expected_completion: '2025-03-31'
      }
    }
  ];

  useEffect(() => {
    // Initialize map
    initializeMap();
    
    // Load grant data
    loadGrantData();
  }, []);

  useEffect(() => {
    // Apply filters when filter state changes
    applyFilters();
  }, [filters, grantData]);

  const initializeMap = () => {
    // Mock map initialization
    // In real implementation, this would use Google Maps or similar
    setTimeout(() => {
      setMapConfig({
        default_center: { lat: -33.8688, lng: 151.2093 },
        default_zoom_level: 14,
        map_style: 'standard',
        is_public_map_enabled: true,
        branding: {
          map_title: 'Sydney Council Grant Projects',
          map_description: 'Explore funded community projects in your area'
        }
      });
      setLoading(false);
    }, 1000);
  };

  const loadGrantData = () => {
    // Simulate API call
    setTimeout(() => {
      setGrantData(mockGrantData);
      setFilteredData(mockGrantData);
    }, 1200);
  };

  const applyFilters = () => {
    let filtered = [...grantData];

    if (filters.postcode) {
      filtered = filtered.filter(grant => 
        grant.postcode.includes(filters.postcode)
      );
    }

    if (filters.suburb) {
      filtered = filtered.filter(grant => 
        grant.suburb.toLowerCase().includes(filters.suburb.toLowerCase())
      );
    }

    if (filters.project_status) {
      filtered = filtered.filter(grant => 
        grant.project.status === filters.project_status
      );
    }

    if (filters.category) {
      filtered = filtered.filter(grant => 
        grant.project.category === filters.category
      );
    }

    setFilteredData(filtered);
  };

  const handleMarkerClick = (grant) => {
    setSelectedGrant(grant);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-AU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusColor = (status) => {
    const colors = {
      'Planning': 'bg-yellow-100 text-yellow-800',
      'In Progress': 'bg-blue-100 text-blue-800',
      'Completed': 'bg-green-100 text-green-800',
      'On Hold': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Environment': 'bg-green-100 text-green-800',
      'Arts & Culture': 'bg-purple-100 text-purple-800',
      'Recreation & Sports': 'bg-blue-100 text-blue-800',
      'Community Services': 'bg-orange-100 text-orange-800',
      'Technology': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading grant map...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Map className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {mapConfig?.branding?.map_title || 'Community Grant Map'}
              </h1>
              <p className="text-gray-600">
                {mapConfig?.branding?.map_description || 'Explore funded projects in your community'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-green-50 text-green-700">
              <TrendingUp className="h-4 w-4 mr-1" />
              {filteredData.length} Projects
            </Badge>
          </div>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* Sidebar */}
        <div className="w-96 bg-white border-r border-gray-200 flex flex-col">
          {/* Filters */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="h-5 w-5 text-gray-600" />
              <h3 className="font-semibold text-gray-900">Filter Projects</h3>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Postcode
                </label>
                <Input
                  placeholder="e.g. 2000"
                  value={filters.postcode}
                  onChange={(e) => setFilters({...filters, postcode: e.target.value})}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Suburb
                </label>
                <Input
                  placeholder="e.g. Sydney"
                  value={filters.suburb}
                  onChange={(e) => setFilters({...filters, suburb: e.target.value})}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Project Status
                </label>
                <Select value={filters.project_status} onValueChange={(value) => setFilters({...filters, project_status: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All statuses</SelectItem>
                    <SelectItem value="Planning">Planning</SelectItem>
                    <SelectItem value="In Progress">In Progress</SelectItem>
                    <SelectItem value="Completed">Completed</SelectItem>
                    <SelectItem value="On Hold">On Hold</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <Select value={filters.category} onValueChange={(value) => setFilters({...filters, category: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="All categories" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All categories</SelectItem>
                    <SelectItem value="Environment">Environment</SelectItem>
                    <SelectItem value="Arts & Culture">Arts & Culture</SelectItem>
                    <SelectItem value="Recreation & Sports">Recreation & Sports</SelectItem>
                    <SelectItem value="Community Services">Community Services</SelectItem>
                    <SelectItem value="Technology">Technology</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Project List */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-4">
              <h3 className="font-semibold text-gray-900 mb-3">
                Projects ({filteredData.length})
              </h3>
              
              <div className="space-y-3">
                {filteredData.map((grant) => (
                  <Card 
                    key={grant.id}
                    className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
                      selectedGrant?.id === grant.id ? 'ring-2 ring-blue-500 bg-blue-50' : ''
                    }`}
                    onClick={() => handleMarkerClick(grant)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-semibold text-gray-900 text-sm leading-tight">
                          {grant.project.title}
                        </h4>
                        {grant.project.is_featured && (
                          <Star className="h-4 w-4 text-yellow-500 fill-current" />
                        )}
                      </div>
                      
                      <div className="flex flex-wrap gap-1 mb-2">
                        <Badge className={getStatusColor(grant.project.status)} size="sm">
                          {grant.project.status}
                        </Badge>
                        <Badge className={getCategoryColor(grant.project.category)} size="sm">
                          {grant.project.category}
                        </Badge>
                      </div>
                      
                      <p className="text-xs text-gray-600 mb-3 line-clamp-2">
                        {grant.project.description}
                      </p>
                      
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          <span>{grant.suburb}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <DollarSign className="h-3 w-3" />
                          <span>{formatCurrency(grant.project.funding_amount)}</span>
                        </div>
                      </div>
                      
                      {grant.project.status !== 'Planning' && (
                        <div className="mt-2">
                          <div className="flex justify-between text-xs text-gray-600 mb-1">
                            <span>Progress</span>
                            <span>{grant.project.completion_percentage}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div 
                              className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                              style={{ width: `${grant.project.completion_percentage}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Map Area */}
        <div className="flex-1 relative">
          {/* Mock Map */}
          <div className="w-full h-full bg-gray-100 relative overflow-hidden">
            {/* Map Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-green-50">
              <div className="absolute inset-0 opacity-20">
                <svg className="w-full h-full" viewBox="0 0 800 600">
                  {/* Mock street lines */}
                  <line x1="0" y1="200" x2="800" y2="200" stroke="#cbd5e1" strokeWidth="2" />
                  <line x1="0" y1="400" x2="800" y2="400" stroke="#cbd5e1" strokeWidth="2" />
                  <line x1="200" y1="0" x2="200" y2="600" stroke="#cbd5e1" strokeWidth="2" />
                  <line x1="400" y1="0" x2="400" y2="600" stroke="#cbd5e1" strokeWidth="2" />
                  <line x1="600" y1="0" x2="600" y2="600" stroke="#cbd5e1" strokeWidth="2" />
                </svg>
              </div>
            </div>

            {/* Map Markers */}
            {filteredData.map((grant, index) => (
              <div
                key={grant.id}
                className={`absolute transform -translate-x-1/2 -translate-y-full cursor-pointer transition-all duration-200 hover:scale-110 ${
                  selectedGrant?.id === grant.id ? 'scale-125 z-20' : 'z-10'
                }`}
                style={{
                  left: `${30 + (index * 25)}%`,
                  top: `${40 + (index * 15)}%`
                }}
                onClick={() => handleMarkerClick(grant)}
              >
                <div className={`relative ${
                  selectedGrant?.id === grant.id ? 'animate-bounce' : ''
                }`}>
                  <MapPin 
                    className={`h-8 w-8 ${
                      grant.project.is_featured 
                        ? 'text-yellow-500 fill-yellow-100' 
                        : 'text-blue-600 fill-blue-100'
                    }`} 
                  />
                  {grant.project.is_featured && (
                    <Star className="h-3 w-3 text-yellow-600 fill-current absolute -top-1 -right-1" />
                  )}
                </div>
              </div>
            ))}

            {/* Map Controls */}
            <div className="absolute top-4 right-4 flex flex-col gap-2">
              <Button variant="outline" size="sm" className="bg-white">
                <Layers className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" className="bg-white">
                <Navigation className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Selected Project Details */}
          {selectedGrant && (
            <div className="absolute bottom-4 left-4 right-4">
              <Card className="bg-white shadow-lg">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{selectedGrant.project.title}</CardTitle>
                      <p className="text-sm text-gray-600 mt-1">{selectedGrant.address}</p>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => setSelectedGrant(null)}
                    >
                      ×
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2 mb-3">
                    <Badge className={getStatusColor(selectedGrant.project.status)}>
                      {selectedGrant.project.status}
                    </Badge>
                    <Badge className={getCategoryColor(selectedGrant.project.category)}>
                      {selectedGrant.project.category}
                    </Badge>
                    {selectedGrant.project.is_featured && (
                      <Badge className="bg-yellow-100 text-yellow-800">
                        <Star className="h-3 w-3 mr-1" />
                        Featured
                      </Badge>
                    )}
                  </div>
                  
                  <p className="text-gray-600 mb-4">{selectedGrant.project.description}</p>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-green-600" />
                      <div>
                        <p className="text-xs text-gray-500">Funding</p>
                        <p className="font-semibold text-sm">
                          {formatCurrency(selectedGrant.project.funding_amount)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-blue-600" />
                      <div>
                        <p className="text-xs text-gray-500">Beneficiaries</p>
                        <p className="font-semibold text-sm">{selectedGrant.project.beneficiaries_count}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-purple-600" />
                      <div>
                        <p className="text-xs text-gray-500">Started</p>
                        <p className="font-semibold text-sm">{formatDate(selectedGrant.project.start_date)}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-orange-600" />
                      <div>
                        <p className="text-xs text-gray-500">Progress</p>
                        <p className="font-semibold text-sm">{selectedGrant.project.completion_percentage}%</p>
                      </div>
                    </div>
                  </div>
                  
                  {selectedGrant.project.photos && selectedGrant.project.photos.length > 0 && (
                    <div className="mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Camera className="h-4 w-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-900">Project Photos</span>
                      </div>
                      <div className="flex gap-2 overflow-x-auto">
                        {selectedGrant.project.photos.map((photo, index) => (
                          <div key={index} className="flex-shrink-0 w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                            <Camera className="h-6 w-6 text-gray-400" />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1">
                      <Info className="h-4 w-4 mr-2" />
                      View Details
                    </Button>
                    <Button variant="outline" size="sm" className="flex-1">
                      <MessageSquare className="h-4 w-4 mr-2" />
                      Feedback
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PublicGrantMap;

