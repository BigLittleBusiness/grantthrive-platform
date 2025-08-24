import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Button } from '../components/ui/button.jsx';
import { Input } from '../components/ui/input.jsx';
import { 
  Search, 
  Filter, 
  MapPin, 
  Calendar, 
  DollarSign, 
  Clock,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
  Heart,
  Share2,
  ExternalLink
} from 'lucide-react';

const GrantsListing = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [selectedStatus, setSelectedStatus] = useState([]);
  const [fundingRange, setFundingRange] = useState([0, 50000]);
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [savedGrants, setSavedGrants] = useState(new Set());

  // Enhanced grant data with more realistic information
  const grants = [
    {
      id: 1,
      title: 'Community Development Grant',
      category: 'Community',
      amount: 5000,
      status: 'Open',
      daysLeft: 10,
      description: 'Support local community initiatives that bring people together and strengthen neighborhood connections through events, programs, and infrastructure improvements.',
      location: 'Mount Isa',
      applicants: 23,
      successRate: 75,
      tags: ['Community Building', 'Local Events', 'Infrastructure']
    },
    {
      id: 2,
      title: 'Local Arts Support Program',
      category: 'Arts',
      amount: 12000,
      status: 'Open',
      daysLeft: 30,
      description: 'Funding for local artists, art installations, cultural events, and creative workshops that enhance the cultural landscape of our community.',
      location: 'Mount Isa',
      applicants: 15,
      successRate: 68,
      tags: ['Visual Arts', 'Performing Arts', 'Cultural Events']
    },
    {
      id: 3,
      title: 'Sports Equipment Grant',
      category: 'Sports',
      amount: 3000,
      status: 'Closing Soon',
      daysLeft: 7,
      description: 'Equipment grants for local sports clubs and recreational groups to purchase essential sporting equipment and safety gear.',
      location: 'Mount Isa',
      applicants: 31,
      successRate: 82,
      tags: ['Equipment', 'Youth Sports', 'Safety']
    },
    {
      id: 4,
      title: 'Environmental Sustainability Fund',
      category: 'Environment',
      amount: 6000,
      status: 'Open',
      daysLeft: 23,
      description: 'Projects focused on environmental conservation, renewable energy, waste reduction, and sustainable community practices.',
      location: 'Mount Isa',
      applicants: 18,
      successRate: 71,
      tags: ['Sustainability', 'Conservation', 'Green Energy']
    },
    {
      id: 5,
      title: 'Youth Leadership Program',
      category: 'Education',
      amount: 8000,
      status: 'Open',
      daysLeft: 45,
      description: 'Empowering young people through leadership development, mentorship programs, and skill-building workshops.',
      location: 'Mount Isa',
      applicants: 12,
      successRate: 79,
      tags: ['Youth Development', 'Leadership', 'Mentorship']
    },
    {
      id: 6,
      title: 'Small Business Innovation Grant',
      category: 'Business',
      amount: 15000,
      status: 'Open',
      daysLeft: 60,
      description: 'Supporting local entrepreneurs and small businesses with innovative ideas that benefit the community and create local employment.',
      location: 'Mount Isa',
      applicants: 8,
      successRate: 65,
      tags: ['Innovation', 'Entrepreneurship', 'Job Creation']
    }
  ];

  const categories = ['Community', 'Arts', 'Sports', 'Environment', 'Education', 'Business'];
  const statuses = ['Open', 'Closing Soon', 'Closed'];

  // Enhanced filtering logic
  const filteredGrants = grants.filter(grant => {
    const matchesSearch = grant.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         grant.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         grant.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesCategory = selectedCategories.length === 0 || selectedCategories.includes(grant.category);
    const matchesStatus = selectedStatus.length === 0 || selectedStatus.includes(grant.status);
    const matchesFunding = grant.amount >= fundingRange[0] && grant.amount <= fundingRange[1];
    
    return matchesSearch && matchesCategory && matchesStatus && matchesFunding;
  });

  const grantsPerPage = 6;
  const totalPages = Math.ceil(filteredGrants.length / grantsPerPage);
  const startIndex = (currentPage - 1) * grantsPerPage;
  const currentGrants = filteredGrants.slice(startIndex, startIndex + grantsPerPage);

  const toggleCategory = (category) => {
    setSelectedCategories(prev => 
      prev.includes(category) 
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const toggleStatus = (status) => {
    setSelectedStatus(prev => 
      prev.includes(status) 
        ? prev.filter(s => s !== status)
        : [...prev, status]
    );
  };

  const toggleSaveGrant = (grantId) => {
    setSavedGrants(prev => {
      const newSaved = new Set(prev);
      if (newSaved.has(grantId)) {
        newSaved.delete(grantId);
      } else {
        newSaved.add(grantId);
      }
      return newSaved;
    });
  };

  const getStatusColor = (status, daysLeft) => {
    if (status === 'Closed') return 'bg-gray-500';
    if (status === 'Closing Soon' || daysLeft <= 7) return 'bg-red-500';
    return 'bg-green-500';
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Community': 'bg-blue-100 text-blue-800',
      'Arts': 'bg-purple-100 text-purple-800',
      'Sports': 'bg-orange-100 text-orange-800',
      'Environment': 'bg-green-100 text-green-800',
      'Education': 'bg-indigo-100 text-indigo-800',
      'Business': 'bg-yellow-100 text-yellow-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Public Grants Listing</h1>
              <p className="text-blue-100">Welcome to the Mount Isa Council portal.</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">{filteredGrants.length}</div>
              <div className="text-blue-100">Available Grants</div>
            </div>
          </div>

          {/* Enhanced Search Bar */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              placeholder="Search grants by title, description, or tags..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-12 pr-4 py-3 w-full text-gray-900 bg-white border-0 rounded-lg shadow-sm"
            />
            <Button
              onClick={() => setShowFilters(!showFilters)}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-green-600 hover:bg-green-700"
            >
              <SlidersHorizontal className="w-4 h-4 mr-2" />
              Filters
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex gap-8">
          {/* Enhanced Sidebar Filters */}
          <div className={`w-80 space-y-6 ${showFilters ? 'block' : 'hidden lg:block'}`}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Filter className="w-5 h-5" />
                  Filters
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Category Filter */}
                <div>
                  <h3 className="font-semibold mb-3">Category</h3>
                  <div className="space-y-2">
                    {categories.map(category => (
                      <label key={category} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedCategories.includes(category)}
                          onChange={() => toggleCategory(category)}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm">{category}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Status Filter */}
                <div>
                  <h3 className="font-semibold mb-3">Status</h3>
                  <div className="space-y-2">
                    {statuses.map(status => (
                      <label key={status} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedStatus.includes(status)}
                          onChange={() => toggleStatus(status)}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm">{status}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Funding Amount Range */}
                <div>
                  <h3 className="font-semibold mb-3">Funding Amount</h3>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Input
                        type="number"
                        placeholder="Min"
                        value={fundingRange[0]}
                        onChange={(e) => setFundingRange([parseInt(e.target.value) || 0, fundingRange[1]])}
                        className="w-20"
                      />
                      <span>to</span>
                      <Input
                        type="number"
                        placeholder="Max"
                        value={fundingRange[1]}
                        onChange={(e) => setFundingRange([fundingRange[0], parseInt(e.target.value) || 50000])}
                        className="w-20"
                      />
                    </div>
                    <div className="text-xs text-gray-500">
                      ${fundingRange[0].toLocaleString()} - ${fundingRange[1].toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Clear Filters */}
                <Button
                  variant="outline"
                  onClick={() => {
                    setSelectedCategories([]);
                    setSelectedStatus([]);
                    setFundingRange([0, 50000]);
                    setSearchTerm('');
                  }}
                  className="w-full"
                >
                  Clear All Filters
                </Button>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Stats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Funding Available</span>
                    <span className="font-semibold">${grants.reduce((sum, grant) => sum + grant.amount, 0).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Average Grant Size</span>
                    <span className="font-semibold">${Math.round(grants.reduce((sum, grant) => sum + grant.amount, 0) / grants.length).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Success Rate</span>
                    <span className="font-semibold text-green-600">74%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {/* Results Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold">
                  {filteredGrants.length} Grant{filteredGrants.length !== 1 ? 's' : ''} Found
                </h2>
                <p className="text-gray-600">
                  Showing {startIndex + 1}-{Math.min(startIndex + grantsPerPage, filteredGrants.length)} of {filteredGrants.length} results
                </p>
              </div>
              
              {/* Sort Options */}
              <select className="border border-gray-300 rounded-lg px-3 py-2">
                <option>Sort by Deadline</option>
                <option>Sort by Amount</option>
                <option>Sort by Popularity</option>
              </select>
            </div>

            {/* Enhanced Grant Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {currentGrants.map(grant => (
                <Card key={grant.id} className="hover:shadow-lg transition-all duration-300 border-l-4 border-l-blue-500">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className={getCategoryColor(grant.category)}>
                            {grant.category}
                          </Badge>
                          <div className={`w-2 h-2 rounded-full ${getStatusColor(grant.status, grant.daysLeft)}`}></div>
                          <span className="text-sm text-gray-600">{grant.status}</span>
                        </div>
                        <CardTitle className="text-lg mb-2">{grant.title}</CardTitle>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleSaveGrant(grant.id)}
                        className="text-gray-400 hover:text-red-500"
                      >
                        <Heart className={`w-4 h-4 ${savedGrants.has(grant.id) ? 'fill-red-500 text-red-500' : ''}`} />
                      </Button>
                    </div>
                  </CardHeader>
                  
                  <CardContent>
                    <p className="text-gray-600 text-sm mb-4 line-clamp-3">{grant.description}</p>
                    
                    {/* Grant Details */}
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center gap-2 text-sm">
                        <DollarSign className="w-4 h-4 text-green-600" />
                        <span className="font-semibold text-green-600">${grant.amount.toLocaleString()}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Clock className="w-4 h-4" />
                        <span>{grant.daysLeft} days left</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <MapPin className="w-4 h-4" />
                        <span>{grant.location}</span>
                      </div>
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1 mb-4">
                      {grant.tags.slice(0, 3).map(tag => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>

                    {/* Stats */}
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                      <span>{grant.applicants} applicants</span>
                      <span>{grant.successRate}% success rate</span>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                      <Button className="flex-1 bg-orange-500 hover:bg-orange-600">
                        Learn More
                      </Button>
                      <Button variant="outline" size="sm">
                        <Share2 className="w-4 h-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Enhanced Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Previous
                  </Button>
                  
                  {/* Page Numbers */}
                  <div className="flex gap-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      const pageNum = i + 1;
                      return (
                        <Button
                          key={pageNum}
                          variant={currentPage === pageNum ? "default" : "outline"}
                          size="sm"
                          onClick={() => setCurrentPage(pageNum)}
                          className="w-8 h-8 p-0"
                        >
                          {pageNum}
                        </Button>
                      );
                    })}
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                  >
                    Next
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GrantsListing;

