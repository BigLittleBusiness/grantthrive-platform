import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Button } from '../components/ui/button.jsx';
import { Input } from '../components/ui/input.jsx';
import { 
  Search,
  Filter,
  Award,
  Calendar,
  DollarSign,
  Users,
  MapPin,
  ExternalLink,
  Share2,
  Heart,
  TrendingUp,
  Target,
  Star,
  Eye,
  Download,
  Play,
  Image as ImageIcon,
  ChevronRight,
  Building,
  Clock,
  CheckCircle
} from 'lucide-react';

const WinnersShowcase = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedYear, setSelectedYear] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedFundingRange, setSelectedFundingRange] = useState('all');
  const [viewMode, setViewMode] = useState('grid'); // grid or list

  // Success stories data with comprehensive details
  const successStories = [
    {
      id: 1,
      title: 'New Playground Equipment',
      organization: 'Riverbank Community Group',
      amount: 15000,
      category: 'Community Infrastructure',
      year: 2024,
      location: 'Riverbank Park',
      description: 'The installation of new playground equipment has provided a safe and engaging play space for local children, encouraging outdoor activity and community interaction.',
      impact: {
        beneficiaries: 450,
        metric: 'children served daily',
        communityReach: '1,200 families'
      },
      images: ['/api/placeholder/400/300'],
      status: 'Completed',
      completionDate: '2024-02-15',
      tags: ['playground', 'children', 'safety', 'community'],
      testimonial: 'This playground has transformed our community. Children now have a safe place to play, and families gather here regularly.',
      contact: 'Sarah Mitchell',
      isFeatured: true,
      socialShares: 234,
      views: 1456
    },
    {
      id: 2,
      title: 'Youth Arts Workshops',
      organization: 'Creative Arts Collective',
      amount: 9500,
      category: 'Arts & Culture',
      year: 2024,
      location: 'Community Arts Center',
      description: 'Created workshops on a wide variety of creative arts, providing young people with opportunities to explore their artistic talents and build confidence.',
      impact: {
        beneficiaries: 85,
        metric: 'youth participants',
        communityReach: '300 family members engaged'
      },
      images: ['/api/placeholder/400/300'],
      status: 'Completed',
      completionDate: '2024-01-20',
      tags: ['youth', 'arts', 'workshops', 'creativity'],
      testimonial: 'My daughter discovered her passion for painting through these workshops. The confidence she\'s gained is incredible.',
      contact: 'Michael Chen',
      isFeatured: false,
      socialShares: 156,
      views: 892
    },
    {
      id: 3,
      title: 'Sports Tournament Sponsorship',
      organization: 'Hit Sports Club',
      amount: 12000,
      category: 'Sports & Recreation',
      year: 2024,
      location: 'Mount Isa Sports Complex',
      description: 'Sports tournament sponsorship for local youth teams, providing equipment, uniforms, and facility access to promote healthy competition and teamwork.',
      impact: {
        beneficiaries: 120,
        metric: 'young athletes',
        communityReach: '500 spectators and families'
      },
      images: ['/api/placeholder/400/300'],
      status: 'Completed',
      completionDate: '2024-03-10',
      tags: ['sports', 'youth', 'tournament', 'teamwork'],
      testimonial: 'This sponsorship allowed our kids to compete at a level they never thought possible. The community support was amazing.',
      contact: 'David Rodriguez',
      isFeatured: false,
      socialShares: 189,
      views: 1123
    },
    {
      id: 4,
      title: 'Community Garden Project',
      organization: 'GreenThumbs Collective',
      amount: 9000,
      category: 'Environment',
      year: 2023,
      location: 'Central Community Garden',
      description: 'Established a community garden that provides fresh produce for local families while teaching sustainable gardening practices and building community connections.',
      impact: {
        beneficiaries: 75,
        metric: 'families with fresh produce',
        communityReach: '200 community members involved'
      },
      images: ['/api/placeholder/400/300'],
      status: 'Ongoing',
      completionDate: '2023-11-15',
      tags: ['environment', 'sustainability', 'community', 'food-security'],
      testimonial: 'The garden has brought our neighborhood together. We share knowledge, produce, and friendship.',
      contact: 'Emma Thompson',
      isFeatured: true,
      socialShares: 267,
      views: 1789
    },
    {
      id: 5,
      title: 'Senior Citizens Luncheon Program',
      organization: 'Sunnywalkers Senior Group',
      amount: 3000,
      category: 'Community Services',
      year: 2023,
      location: 'Community Center',
      description: 'Weekly luncheon program for senior citizens, providing nutritious meals, social interaction, and health monitoring services.',
      impact: {
        beneficiaries: 45,
        metric: 'seniors served weekly',
        communityReach: '150 family members connected'
      },
      images: ['/api/placeholder/400/300'],
      status: 'Ongoing',
      completionDate: '2023-09-01',
      tags: ['seniors', 'nutrition', 'social-connection', 'health'],
      testimonial: 'These lunches are the highlight of my week. I\'ve made wonderful friends and feel less isolated.',
      contact: 'Margaret Wilson',
      isFeatured: false,
      socialShares: 98,
      views: 567
    },
    {
      id: 6,
      title: 'Digital Literacy Training',
      organization: 'Tech for All Initiative',
      amount: 7500,
      category: 'Education',
      year: 2023,
      location: 'Public Library',
      description: 'Computer and internet training program for community members, focusing on essential digital skills for employment and daily life.',
      impact: {
        beneficiaries: 95,
        metric: 'people trained',
        communityReach: '300 family members benefited'
      },
      images: ['/api/placeholder/400/300'],
      status: 'Completed',
      completionDate: '2023-12-20',
      tags: ['education', 'digital-literacy', 'employment', 'skills'],
      testimonial: 'I can now apply for jobs online and video call my grandchildren. This program changed my life.',
      contact: 'James Park',
      isFeatured: false,
      socialShares: 145,
      views: 823
    }
  ];

  // Filter options
  const years = ['all', '2024', '2023', '2022', '2021'];
  const categories = [
    'all',
    'Community Infrastructure',
    'Arts & Culture',
    'Sports & Recreation',
    'Environment',
    'Community Services',
    'Education',
    'Health & Wellbeing'
  ];
  const fundingRanges = [
    { id: 'all', label: 'All Amounts' },
    { id: 'small', label: 'Under $5,000' },
    { id: 'medium', label: '$5,000 - $15,000' },
    { id: 'large', label: 'Over $15,000' }
  ];

  // Calculate statistics
  const totalProjects = successStories.length;
  const totalFunding = successStories.reduce((sum, story) => sum + story.amount, 0);
  const totalBeneficiaries = successStories.reduce((sum, story) => sum + story.impact.beneficiaries, 0);
  const featuredStory = successStories.find(story => story.isFeatured);

  // Filter stories
  const filteredStories = successStories.filter(story => {
    const matchesSearch = story.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         story.organization.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         story.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         story.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesYear = selectedYear === 'all' || story.year.toString() === selectedYear;
    const matchesCategory = selectedCategory === 'all' || story.category === selectedCategory;
    
    let matchesFunding = true;
    if (selectedFundingRange === 'small') matchesFunding = story.amount < 5000;
    else if (selectedFundingRange === 'medium') matchesFunding = story.amount >= 5000 && story.amount <= 15000;
    else if (selectedFundingRange === 'large') matchesFunding = story.amount > 15000;
    
    return matchesSearch && matchesYear && matchesCategory && matchesFunding;
  });

  const getCategoryColor = (category) => {
    const colors = {
      'Community Infrastructure': 'bg-blue-100 text-blue-800',
      'Arts & Culture': 'bg-purple-100 text-purple-800',
      'Sports & Recreation': 'bg-orange-100 text-orange-800',
      'Environment': 'bg-green-100 text-green-800',
      'Community Services': 'bg-pink-100 text-pink-800',
      'Education': 'bg-indigo-100 text-indigo-800',
      'Health & Wellbeing': 'bg-red-100 text-red-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status) => {
    return status === 'Completed' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="max-w-7xl mx-auto px-4 py-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            <div>
              <h1 className="text-4xl font-bold mb-4">
                CELEBRATING OUR COMMUNITY CHAMPIONS
              </h1>
              <p className="text-xl text-blue-100 mb-6">
                Discover the amazing projects and initiatives that are making a real difference in our community
              </p>
              <div className="flex gap-4">
                <Button className="bg-orange-500 hover:bg-orange-600">
                  <Award className="w-4 h-4 mr-2" />
                  Apply for Grant
                </Button>
                <Button variant="outline" className="text-white border-white hover:bg-white hover:text-blue-600">
                  <Share2 className="w-4 h-4 mr-2" />
                  Share Stories
                </Button>
              </div>
            </div>
            
            {/* Featured Story Preview */}
            {featuredStory && (
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
                <div className="flex items-center gap-2 mb-3">
                  <Star className="w-5 h-5 text-yellow-400" />
                  <span className="text-sm font-medium">Featured Success Story</span>
                </div>
                <h3 className="text-xl font-semibold mb-2">{featuredStory.title}</h3>
                <p className="text-blue-100 text-sm mb-3">{featuredStory.organization}</p>
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-1">
                    <DollarSign className="w-4 h-4" />
                    <span>${featuredStory.amount.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    <span>{featuredStory.impact.beneficiaries} {featuredStory.impact.metric}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Statistics Bar */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{totalProjects}</div>
              <div className="text-sm text-gray-600">TOTAL PROJECTS FUNDED</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">${(totalFunding / 1000).toFixed(0)}K</div>
              <div className="text-sm text-gray-600">TOTAL FUNDING DISTRIBUTED</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">{(totalBeneficiaries / 1000).toFixed(1)}K</div>
              <div className="text-sm text-gray-600">COMMUNITY MEMBERS HELPED</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">172</div>
              <div className="text-sm text-gray-600">ORGANIZATIONS SUPPORTED</div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Search and Filters */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                placeholder="Search success stories, organizations, or impact areas..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2"
              >
                {years.map(year => (
                  <option key={year} value={year}>
                    {year === 'all' ? 'All Years' : year}
                  </option>
                ))}
              </select>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2"
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category === 'all' ? 'All Categories' : category}
                  </option>
                ))}
              </select>
              <select
                value={selectedFundingRange}
                onChange={(e) => setSelectedFundingRange(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2"
              >
                {fundingRanges.map(range => (
                  <option key={range.id} value={range.id}>{range.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">
                {filteredStories.length} Success Stor{filteredStories.length !== 1 ? 'ies' : 'y'} Found
              </h2>
              <p className="text-gray-600">Inspiring projects that made a difference</p>
            </div>
            <div className="flex gap-2">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('grid')}
              >
                Grid
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('list')}
              >
                List
              </Button>
            </div>
          </div>
        </div>

        {/* Success Stories Grid */}
        <div className={`grid gap-6 ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
          {filteredStories.map(story => (
            <Card key={story.id} className="hover:shadow-lg transition-all duration-300 overflow-hidden">
              {/* Story Image */}
              <div className="relative h-48 bg-gray-200">
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                <div className="absolute top-4 left-4">
                  <Badge className={getCategoryColor(story.category)}>
                    {story.category}
                  </Badge>
                </div>
                <div className="absolute top-4 right-4">
                  <Badge className={getStatusColor(story.status)}>
                    {story.status}
                  </Badge>
                </div>
                <div className="absolute bottom-4 left-4 text-white">
                  <div className="text-2xl font-bold">${story.amount.toLocaleString()}</div>
                  <div className="text-sm opacity-90">Grant Amount</div>
                </div>
              </div>

              <CardContent className="p-6">
                <div className="mb-4">
                  <h3 className="font-semibold text-lg mb-1">{story.title}</h3>
                  <p className="text-sm text-gray-600 mb-2">{story.organization}</p>
                  <p className="text-sm text-gray-700 line-clamp-2">{story.description}</p>
                </div>

                {/* Impact Metrics */}
                <div className="bg-green-50 rounded-lg p-3 mb-4">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800">Community Impact</span>
                  </div>
                  <div className="text-lg font-bold text-green-600">{story.impact.beneficiaries}</div>
                  <div className="text-xs text-green-700">{story.impact.metric}</div>
                  <div className="text-xs text-gray-600 mt-1">{story.impact.communityReach}</div>
                </div>

                {/* Project Details */}
                <div className="space-y-2 mb-4">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <MapPin className="w-4 h-4" />
                    <span>{story.location}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Calendar className="w-4 h-4" />
                    <span>Completed {story.completionDate}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Building className="w-4 h-4" />
                    <span>Contact: {story.contact}</span>
                  </div>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1 mb-4">
                  {story.tags.slice(0, 3).map(tag => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      #{tag}
                    </Badge>
                  ))}
                  {story.tags.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{story.tags.length - 3} more
                    </Badge>
                  )}
                </div>

                {/* Testimonial */}
                <div className="bg-gray-50 rounded-lg p-3 mb-4">
                  <p className="text-sm italic text-gray-700">"{story.testimonial}"</p>
                </div>

                {/* Engagement Stats */}
                <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                      <Eye className="w-4 h-4" />
                      <span>{story.views}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Share2 className="w-4 h-4" />
                      <span>{story.socialShares}</span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-400">{story.year}</div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button className="flex-1" size="sm">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Read Full Story
                  </Button>
                  <Button variant="outline" size="sm">
                    <Share2 className="w-4 h-4" />
                  </Button>
                  <Button variant="outline" size="sm">
                    <Heart className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Load More */}
        {filteredStories.length > 0 && (
          <div className="text-center mt-8">
            <Button variant="outline">
              Load More Success Stories
            </Button>
          </div>
        )}

        {/* Call to Action */}
        <div className="mt-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to Create Your Own Success Story?</h2>
          <p className="text-blue-100 mb-6">
            Join the hundreds of organizations that have transformed their communities with grant funding
          </p>
          <div className="flex justify-center gap-4">
            <Button className="bg-orange-500 hover:bg-orange-600">
              <Award className="w-4 h-4 mr-2" />
              Apply for a Grant
            </Button>
            <Button variant="outline" className="text-white border-white hover:bg-white hover:text-blue-600">
              <Users className="w-4 h-4 mr-2" />
              Join Community
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WinnersShowcase;

