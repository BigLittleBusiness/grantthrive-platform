import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Button } from '../components/ui/button.jsx';
import { Input } from '../components/ui/input.jsx';
import { 
  Search,
  Filter,
  Download,
  Eye,
  Star,
  Clock,
  FileText,
  Video,
  BookOpen,
  HelpCircle,
  Bookmark,
  Share2,
  Plus,
  TrendingUp,
  Award,
  Users,
  Calendar,
  Tag,
  ThumbsUp,
  MessageSquare,
  ExternalLink,
  Play,
  File,
  Image as ImageIcon,
  Lightbulb
} from 'lucide-react';

const ResourceHub = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [sortBy, setSortBy] = useState('popular');
  const [savedResources, setSavedResources] = useState(new Set());

  // Resource categories with enhanced data
  const categories = [
    { id: 'all', name: 'All Resources', count: 156 },
    { id: 'guides', name: 'Guides', count: 45, icon: BookOpen },
    { id: 'templates', name: 'Templates', count: 38, icon: FileText },
    { id: 'videos', name: 'Videos', count: 28, icon: Video },
    { id: 'faqs', name: 'FAQs', count: 25, icon: HelpCircle },
    { id: 'tools', name: 'Tools', count: 20, icon: Lightbulb }
  ];

  // Resource types
  const resourceTypes = [
    { id: 'all', name: 'All Types' },
    { id: 'guide', name: 'Guide', icon: BookOpen, color: 'bg-blue-100 text-blue-800' },
    { id: 'template', name: 'Template', icon: FileText, color: 'bg-green-100 text-green-800' },
    { id: 'video', name: 'Video', icon: Video, color: 'bg-orange-100 text-orange-800' },
    { id: 'faq', name: 'FAQ', icon: HelpCircle, color: 'bg-purple-100 text-purple-800' },
    { id: 'tool', name: 'Tool', icon: Lightbulb, color: 'bg-yellow-100 text-yellow-800' }
  ];

  // Enhanced resources data
  const resources = [
    {
      id: 1,
      title: 'Getting Started with Grant Applications',
      description: 'Learn the basics of grant applications and get up and running quickly with our comprehensive starter guide.',
      type: 'guide',
      category: 'guides',
      readTime: '8 min read',
      downloads: 221,
      views: 1456,
      rating: 4.8,
      reviews: 34,
      author: 'Mount Isa Council',
      publishDate: '2024-03-15',
      tags: ['beginner', 'applications', 'getting-started'],
      isFeatured: true,
      fileSize: '2.3 MB',
      format: 'PDF'
    },
    {
      id: 2,
      title: 'How to Use the Admin Panel',
      description: 'Complete walkthrough of the administrative features and how to manage your grant programs effectively.',
      type: 'video',
      category: 'videos',
      duration: '4:30',
      downloads: 95,
      views: 892,
      rating: 4.6,
      reviews: 18,
      author: 'Sarah Johnson',
      publishDate: '2024-03-10',
      tags: ['admin', 'tutorial', 'management'],
      isFeatured: true,
      fileSize: '45 MB',
      format: 'MP4'
    },
    {
      id: 3,
      title: 'Grant Application Checklist Template',
      description: 'Comprehensive checklist template to ensure you don\'t miss any important steps in your application process.',
      type: 'template',
      category: 'templates',
      readTime: '2 min read',
      downloads: 178,
      views: 567,
      rating: 4.9,
      reviews: 22,
      author: 'Community Team',
      publishDate: '2024-03-08',
      tags: ['checklist', 'template', 'organization'],
      isFeatured: false,
      fileSize: '1.1 MB',
      format: 'DOCX'
    },
    {
      id: 4,
      title: 'Best Practices for Project Management',
      description: 'Discover effective strategies for managing community projects from planning to completion.',
      type: 'guide',
      category: 'guides',
      readTime: '8 min read',
      downloads: 340,
      views: 1234,
      rating: 4.7,
      reviews: 45,
      author: 'Project Management Team',
      publishDate: '2024-03-05',
      tags: ['project-management', 'best-practices', 'planning'],
      isFeatured: true,
      fileSize: '3.2 MB',
      format: 'PDF'
    },
    {
      id: 5,
      title: 'Budget Planning Spreadsheet',
      description: 'Professional budget template with formulas and categories specifically designed for grant applications.',
      type: 'template',
      category: 'templates',
      readTime: '5 min setup',
      downloads: 267,
      views: 789,
      rating: 4.8,
      reviews: 31,
      author: 'Finance Team',
      publishDate: '2024-03-01',
      tags: ['budget', 'spreadsheet', 'financial-planning'],
      isFeatured: false,
      fileSize: '2.8 MB',
      format: 'XLSX'
    },
    {
      id: 6,
      title: 'Community Engagement Strategies',
      description: 'Learn how to effectively engage your community and build support for your grant projects.',
      type: 'video',
      category: 'videos',
      duration: '6:15',
      downloads: 156,
      views: 678,
      rating: 4.5,
      reviews: 28,
      author: 'Community Outreach',
      publishDate: '2024-02-28',
      tags: ['community', 'engagement', 'outreach'],
      isFeatured: false,
      fileSize: '67 MB',
      format: 'MP4'
    },
    {
      id: 7,
      title: 'Frequently Asked Questions',
      description: 'Common questions and answers about the grant application process, eligibility, and requirements.',
      type: 'faq',
      category: 'faqs',
      readTime: '10 min read',
      downloads: 445,
      views: 2134,
      rating: 4.6,
      reviews: 67,
      author: 'Support Team',
      publishDate: '2024-02-25',
      tags: ['faq', 'support', 'common-questions'],
      isFeatured: false,
      fileSize: '1.5 MB',
      format: 'PDF'
    },
    {
      id: 8,
      title: 'Grant Writing Workshop Recording',
      description: 'Full recording of our popular grant writing workshop with expert tips and Q&A session.',
      type: 'video',
      category: 'videos',
      duration: '45:30',
      downloads: 89,
      views: 456,
      rating: 4.9,
      reviews: 15,
      author: 'Workshop Team',
      publishDate: '2024-02-20',
      tags: ['workshop', 'grant-writing', 'expert-tips'],
      isFeatured: true,
      fileSize: '234 MB',
      format: 'MP4'
    }
  ];

  // Featured resources
  const featuredResources = resources.filter(resource => resource.isFeatured);

  // Filter and sort resources
  const filteredResources = resources.filter(resource => {
    const matchesSearch = resource.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         resource.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         resource.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesCategory = selectedCategory === 'all' || resource.category === selectedCategory;
    const matchesType = selectedType === 'all' || resource.type === selectedType;
    
    return matchesSearch && matchesCategory && matchesType;
  });

  const sortedResources = [...filteredResources].sort((a, b) => {
    switch (sortBy) {
      case 'popular':
        return b.downloads - a.downloads;
      case 'recent':
        return new Date(b.publishDate) - new Date(a.publishDate);
      case 'rating':
        return b.rating - a.rating;
      case 'views':
        return b.views - a.views;
      default:
        return 0;
    }
  });

  const toggleSaveResource = (resourceId) => {
    setSavedResources(prev => {
      const newSaved = new Set(prev);
      if (newSaved.has(resourceId)) {
        newSaved.delete(resourceId);
      } else {
        newSaved.add(resourceId);
      }
      return newSaved;
    });
  };

  const getTypeIcon = (type) => {
    const typeData = resourceTypes.find(t => t.id === type);
    return typeData?.icon || FileText;
  };

  const getTypeColor = (type) => {
    const typeData = resourceTypes.find(t => t.id === type);
    return typeData?.color || 'bg-gray-100 text-gray-800';
  };

  const formatFileSize = (size) => {
    return size;
  };

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < Math.floor(rating) ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
      />
    ));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Resource Hub</h1>
              <p className="text-blue-100">Guides, templates, videos, and tools to help you succeed</p>
            </div>
            <Button className="bg-orange-500 hover:bg-orange-600">
              <Plus className="w-4 h-4 mr-2" />
              Suggest Resource
            </Button>
          </div>

          {/* Category Tabs */}
          <div className="flex flex-wrap gap-2 mb-6">
            {categories.map(category => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  selectedCategory === category.id
                    ? 'bg-white text-blue-600'
                    : 'bg-blue-500 text-white hover:bg-blue-400'
                }`}
              >
                {category.name}
                {category.count && (
                  <span className="ml-1 text-xs opacity-75">({category.count})</span>
                )}
              </button>
            ))}
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              placeholder="Search resources, guides, templates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-12 pr-4 py-3 w-full text-gray-900 bg-white border-0 rounded-lg shadow-sm"
            />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Featured Resources */}
        {selectedCategory === 'all' && !searchTerm && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-6">Featured Resources</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredResources.slice(0, 3).map(resource => {
                const TypeIcon = getTypeIcon(resource.type);
                return (
                  <Card key={resource.id} className="hover:shadow-lg transition-shadow border-l-4 border-l-orange-500">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className={`p-3 rounded-lg ${getTypeColor(resource.type)}`}>
                          <TypeIcon className="w-6 h-6" />
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleSaveResource(resource.id)}
                          className="text-gray-400 hover:text-orange-500"
                        >
                          <Bookmark className={`w-4 h-4 ${savedResources.has(resource.id) ? 'fill-orange-500 text-orange-500' : ''}`} />
                        </Button>
                      </div>
                      
                      <h3 className="font-semibold text-lg mb-2">{resource.title}</h3>
                      <p className="text-gray-600 text-sm mb-4 line-clamp-2">{resource.description}</p>
                      
                      <div className="flex items-center gap-2 mb-4">
                        <Badge className={getTypeColor(resource.type)}>
                          {resource.type.charAt(0).toUpperCase() + resource.type.slice(1)}
                        </Badge>
                        <span className="text-sm text-gray-500">
                          {resource.readTime || resource.duration}
                        </span>
                        <span className="text-sm text-gray-500">•</span>
                        <span className="text-sm text-gray-500">{resource.downloads} downloads</span>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1">
                          {renderStars(resource.rating)}
                          <span className="text-sm text-gray-600 ml-1">({resource.reviews})</span>
                        </div>
                        <Button size="sm" className="bg-orange-500 hover:bg-orange-600">
                          <Download className="w-4 h-4 mr-2" />
                          Download
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Filters Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Filter className="w-5 h-5" />
                  Filters
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Resource Type</label>
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    {resourceTypes.map(type => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Sort By</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="popular">Most Downloaded</option>
                    <option value="recent">Most Recent</option>
                    <option value="rating">Highest Rated</option>
                    <option value="views">Most Viewed</option>
                  </select>
                </div>
                
                <Button
                  variant="outline"
                  onClick={() => {
                    setSelectedCategory('all');
                    setSelectedType('all');
                    setSearchTerm('');
                  }}
                  className="w-full"
                >
                  Clear Filters
                </Button>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Resource Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Resources</span>
                    <span className="font-semibold">156</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Downloads</span>
                    <span className="font-semibold">12,450</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Average Rating</span>
                    <span className="font-semibold">4.7 ⭐</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">New This Month</span>
                    <span className="font-semibold text-green-600">8</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Popular Tags */}
            <Card>
              <CardHeader>
                <CardTitle>Popular Tags</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {['beginner', 'template', 'guide', 'video', 'planning', 'budget', 'community'].map(tag => (
                    <Badge key={tag} variant="outline" className="cursor-pointer hover:bg-gray-100">
                      #{tag}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {/* Results Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold">
                  {filteredResources.length} Resource{filteredResources.length !== 1 ? 's' : ''} Found
                </h2>
                <p className="text-gray-600">
                  {selectedCategory !== 'all' && `in ${categories.find(c => c.id === selectedCategory)?.name}`}
                  {selectedType !== 'all' && ` • ${resourceTypes.find(t => t.id === selectedType)?.name} only`}
                </p>
              </div>
            </div>

            {/* Resources Grid */}
            <div className="space-y-4">
              {sortedResources.map(resource => {
                const TypeIcon = getTypeIcon(resource.type);
                return (
                  <Card key={resource.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-lg ${getTypeColor(resource.type)} flex-shrink-0`}>
                          <TypeIcon className="w-6 h-6" />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <h3 className="font-semibold text-lg mb-1">{resource.title}</h3>
                              <p className="text-gray-600 text-sm mb-3">{resource.description}</p>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleSaveResource(resource.id)}
                              className="text-gray-400 hover:text-orange-500 ml-4"
                            >
                              <Bookmark className={`w-4 h-4 ${savedResources.has(resource.id) ? 'fill-orange-500 text-orange-500' : ''}`} />
                            </Button>
                          </div>
                          
                          <div className="flex items-center gap-4 mb-3">
                            <Badge className={getTypeColor(resource.type)}>
                              {resource.type.charAt(0).toUpperCase() + resource.type.slice(1)}
                            </Badge>
                            <span className="text-sm text-gray-500">
                              {resource.readTime || resource.duration}
                            </span>
                            <span className="text-sm text-gray-500">
                              {formatFileSize(resource.fileSize)} • {resource.format}
                            </span>
                            <span className="text-sm text-gray-500">
                              by {resource.author}
                            </span>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4 text-sm text-gray-500">
                              <div className="flex items-center gap-1">
                                <Download className="w-4 h-4" />
                                <span>{resource.downloads}</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <Eye className="w-4 h-4" />
                                <span>{resource.views}</span>
                              </div>
                              <div className="flex items-center gap-1">
                                {renderStars(resource.rating)}
                                <span className="ml-1">({resource.reviews})</span>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-2">
                              <Button variant="outline" size="sm">
                                <Eye className="w-4 h-4 mr-2" />
                                Preview
                              </Button>
                              <Button size="sm" className="bg-orange-500 hover:bg-orange-600">
                                <Download className="w-4 h-4 mr-2" />
                                Download
                              </Button>
                            </div>
                          </div>
                          
                          {/* Tags */}
                          <div className="flex flex-wrap gap-1 mt-3">
                            {resource.tags.map(tag => (
                              <Badge key={tag} variant="outline" className="text-xs">
                                #{tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Load More */}
            {sortedResources.length > 0 && (
              <div className="text-center mt-8">
                <Button variant="outline">
                  Load More Resources
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResourceHub;

