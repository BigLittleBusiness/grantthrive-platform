import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Button } from '../components/ui/button.jsx';
import { Input } from '../components/ui/input.jsx';
import { Avatar } from '../components/ui/avatar.jsx';
import { 
  Search,
  MessageSquare,
  Users,
  Star,
  TrendingUp,
  Clock,
  Pin,
  Eye,
  ThumbsUp,
  MessageCircle,
  Plus,
  Filter,
  Calendar,
  Award,
  CheckCircle,
  AlertCircle,
  BookOpen,
  Lightbulb,
  Target,
  Heart,
  Share2
} from 'lucide-react';

const CommunityForum = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('recent');
  const [showNewTopicModal, setShowNewTopicModal] = useState(false);

  // Enhanced forum categories with icons and descriptions
  const categories = [
    {
      id: 'general',
      name: 'General Discussion',
      icon: MessageSquare,
      color: 'bg-blue-100 text-blue-800',
      description: 'General community discussions and announcements',
      topics: 156,
      posts: 1247
    },
    {
      id: 'grant-tips',
      name: 'Grant Writing Tips',
      icon: BookOpen,
      color: 'bg-green-100 text-green-800',
      description: 'Share and learn grant writing strategies',
      topics: 89,
      posts: 634
    },
    {
      id: 'collaboration',
      name: 'Project Collaboration',
      icon: Users,
      color: 'bg-purple-100 text-purple-800',
      description: 'Find partners and collaborate on projects',
      topics: 67,
      posts: 423
    },
    {
      id: 'success-stories',
      name: 'Success Stories',
      icon: Star,
      color: 'bg-yellow-100 text-yellow-800',
      description: 'Celebrate successful grant applications and projects',
      topics: 45,
      posts: 289
    },
    {
      id: 'qa-council',
      name: 'Q&A with Council',
      icon: AlertCircle,
      color: 'bg-orange-100 text-orange-800',
      description: 'Direct questions and answers with council staff',
      topics: 34,
      posts: 178
    },
    {
      id: 'resources',
      name: 'Resources & Tools',
      icon: Lightbulb,
      color: 'bg-indigo-100 text-indigo-800',
      description: 'Share useful resources, templates, and tools',
      topics: 52,
      posts: 312
    }
  ];

  // Enhanced discussion data with more realistic content
  const discussions = [
    {
      id: 1,
      title: 'Welcome to the Community Forum!',
      author: {
        name: 'Jenny Wilson',
        avatar: '/api/placeholder/40/40',
        role: 'Community Manager',
        reputation: 2450,
        badge: 'Staff'
      },
      category: 'general',
      replies: 12,
      views: 234,
      lastActivity: '2 hours ago',
      isPinned: true,
      isLocked: false,
      tags: ['welcome', 'community', 'guidelines'],
      excerpt: 'Welcome to our new community forum! This is a space for grant applicants, community organizations, and council staff to connect, share knowledge, and collaborate on projects that benefit our community.',
      likes: 18
    },
    {
      id: 2,
      title: 'Partnership ideas for local projects',
      author: {
        name: 'Leslie Alexander',
        avatar: '/api/placeholder/40/40',
        role: 'Project Coordinator',
        reputation: 1890,
        badge: 'Contributor'
      },
      category: 'collaboration',
      replies: 54,
      views: 892,
      lastActivity: '5 hours ago',
      isPinned: false,
      isLocked: false,
      tags: ['partnership', 'collaboration', 'local-projects'],
      excerpt: 'Looking for organizations interested in partnering on community development projects. We have some great ideas for improving local infrastructure and would love to collaborate.',
      likes: 23
    },
    {
      id: 3,
      title: 'Tips for writing a grant proposal',
      author: {
        name: 'Robert Fox',
        avatar: '/api/placeholder/40/40',
        role: 'Grant Writer',
        reputation: 3200,
        badge: 'Expert'
      },
      category: 'grant-tips',
      replies: 8,
      views: 456,
      lastActivity: '1 day ago',
      isPinned: false,
      isLocked: false,
      tags: ['grant-writing', 'tips', 'best-practices'],
      excerpt: 'After successfully securing over $500K in grants, here are my top 10 tips for writing compelling grant proposals that get funded.',
      likes: 45
    },
    {
      id: 4,
      title: 'AZZ funding for tourism initiatives',
      author: {
        name: 'Dariene Robertson',
        avatar: '/api/placeholder/40/40',
        role: 'Tourism Officer',
        reputation: 1560,
        badge: 'Regular'
      },
      category: 'qa-council',
      replies: 7,
      views: 234,
      lastActivity: '3 days ago',
      isPinned: false,
      isLocked: false,
      tags: ['tourism', 'funding', 'council-programs'],
      excerpt: 'Can anyone provide information about the AZZ funding program for tourism initiatives? What are the eligibility criteria and application deadlines?',
      likes: 12
    },
    {
      id: 5,
      title: 'Successful Community Garden Project - Lessons Learned',
      author: {
        name: 'Marcus Johnson',
        avatar: '/api/placeholder/40/40',
        role: 'Community Leader',
        reputation: 2100,
        badge: 'Contributor'
      },
      category: 'success-stories',
      replies: 15,
      views: 567,
      lastActivity: '4 days ago',
      isPinned: false,
      isLocked: false,
      tags: ['success-story', 'community-garden', 'lessons-learned'],
      excerpt: 'Our community garden project was fully funded and completed last month! Here are the key lessons we learned and tips for other organizations considering similar projects.',
      likes: 31
    },
    {
      id: 6,
      title: 'Budget Template for Community Events',
      author: {
        name: 'Sarah Chen',
        avatar: '/api/placeholder/40/40',
        role: 'Event Coordinator',
        reputation: 1750,
        badge: 'Regular'
      },
      category: 'resources',
      replies: 22,
      views: 789,
      lastActivity: '1 week ago',
      isPinned: false,
      isLocked: false,
      tags: ['budget-template', 'events', 'resources'],
      excerpt: 'I\'ve created a comprehensive budget template specifically for community events. It includes all the categories you need to consider when planning your event budget.',
      likes: 28
    }
  ];

  // Active community members
  const activeMembers = [
    { name: 'Dariene', avatar: '/api/placeholder/40/40', status: 'online' },
    { name: 'Cameron', avatar: '/api/placeholder/40/40', status: 'online' },
    { name: 'Artnette', avatar: '/api/placeholder/40/40', status: 'away' },
    { name: 'Marcus', avatar: '/api/placeholder/40/40', status: 'online' },
    { name: 'Sarah', avatar: '/api/placeholder/40/40', status: 'offline' }
  ];

  // Upcoming events
  const upcomingEvents = [
    {
      title: 'Community Workshop',
      date: 'Apr 28',
      type: 'Workshop',
      attendees: 23
    },
    {
      title: 'Grant Writing Masterclass',
      date: 'May 5',
      type: 'Training',
      attendees: 45
    },
    {
      title: 'Project Showcase',
      date: 'May 12',
      type: 'Event',
      attendees: 67
    }
  ];

  const filteredDiscussions = discussions.filter(discussion => {
    const matchesSearch = discussion.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         discussion.excerpt.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         discussion.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesCategory = selectedCategory === 'all' || discussion.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  const sortedDiscussions = [...filteredDiscussions].sort((a, b) => {
    switch (sortBy) {
      case 'recent':
        return new Date(b.lastActivity) - new Date(a.lastActivity);
      case 'popular':
        return b.replies - a.replies;
      case 'likes':
        return b.likes - a.likes;
      default:
        return 0;
    }
  });

  const getBadgeColor = (badge) => {
    switch (badge) {
      case 'Staff': return 'bg-blue-500 text-white';
      case 'Expert': return 'bg-purple-500 text-white';
      case 'Contributor': return 'bg-green-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'bg-green-400';
      case 'away': return 'bg-yellow-400';
      default: return 'bg-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Community Forum</h1>
              <p className="text-gray-600">Connect, share knowledge, and collaborate with fellow community members</p>
            </div>
            <Button className="bg-orange-500 hover:bg-orange-600">
              <Plus className="w-4 h-4 mr-2" />
              Start Discussion
            </Button>
          </div>

          {/* Search and Filter */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                placeholder="Search discussions, topics, or tags..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="all">All Categories</option>
                {categories.map(category => (
                  <option key={category.id} value={category.id}>{category.name}</option>
                ))}
              </select>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="recent">Most Recent</option>
                <option value="popular">Most Replies</option>
                <option value="likes">Most Liked</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* Category Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map(category => {
                const IconComponent = category.icon;
                return (
                  <Card 
                    key={category.id} 
                    className="hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => setSelectedCategory(category.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <div className={`p-2 rounded-lg ${category.color}`}>
                          <IconComponent className="w-5 h-5" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-medium">{category.name}</h3>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 mb-3">{category.description}</p>
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>{category.topics} topics</span>
                        <span>{category.posts} posts</span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Recent Discussions */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />
                    Recent Discussions
                  </CardTitle>
                  <Badge variant="outline">
                    {filteredDiscussions.length} discussions
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {sortedDiscussions.map(discussion => (
                    <div key={discussion.id} className="border-b border-gray-100 pb-4 last:border-b-0">
                      <div className="flex items-start gap-4">
                        <div className="relative">
                          <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                            <span className="text-sm font-medium text-gray-600">
                              {discussion.author.name.charAt(0)}
                            </span>
                          </div>
                          {discussion.isPinned && (
                            <Pin className="absolute -top-1 -right-1 w-4 h-4 text-orange-500" />
                          )}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <h3 className="font-medium text-gray-900 hover:text-blue-600 cursor-pointer">
                                {discussion.title}
                                {discussion.isPinned && (
                                  <Pin className="inline w-4 h-4 ml-1 text-orange-500" />
                                )}
                              </h3>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-sm text-gray-600">{discussion.author.name}</span>
                                <Badge className={`text-xs ${getBadgeColor(discussion.author.badge)}`}>
                                  {discussion.author.badge}
                                </Badge>
                                <Badge className={categories.find(c => c.id === discussion.category)?.color}>
                                  {categories.find(c => c.id === discussion.category)?.name}
                                </Badge>
                              </div>
                            </div>
                            <div className="text-right text-sm text-gray-500">
                              <div>{discussion.lastActivity}</div>
                            </div>
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-3 line-clamp-2">{discussion.excerpt}</p>
                          
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4 text-sm text-gray-500">
                              <div className="flex items-center gap-1">
                                <MessageCircle className="w-4 h-4" />
                                <span>{discussion.replies} replies</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <Eye className="w-4 h-4" />
                                <span>{discussion.views} views</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <ThumbsUp className="w-4 h-4" />
                                <span>{discussion.likes} likes</span>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-2">
                              <Button variant="ghost" size="sm">
                                <Heart className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="sm">
                                <Share2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                          
                          {/* Tags */}
                          <div className="flex flex-wrap gap-1 mt-2">
                            {discussion.tags.map(tag => (
                              <Badge key={tag} variant="outline" className="text-xs">
                                #{tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Active Members */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Active Members
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {activeMembers.map((member, index) => (
                    <div key={index} className="flex items-center gap-3">
                      <div className="relative">
                        <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                          <span className="text-xs font-medium text-gray-600">
                            {member.name.charAt(0)}
                          </span>
                        </div>
                        <div className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white ${getStatusColor(member.status)}`}></div>
                      </div>
                      <span className="text-sm font-medium">{member.name}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Upcoming Events */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Upcoming Events
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {upcomingEvents.map((event, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <div className="font-medium text-sm">{event.title}</div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-600">{event.date}</span>
                        <Badge variant="outline" className="text-xs">
                          {event.attendees} attending
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Popular Topics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Popular Topics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm">General Discussion</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm">Project Collaboration</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm">Grant Writing Tips</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span className="text-sm">Success Stories</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Forum Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Forum Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Topics</span>
                    <span className="font-medium">443</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Posts</span>
                    <span className="font-medium">3,083</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Active Members</span>
                    <span className="font-medium">156</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Online Now</span>
                    <span className="font-medium text-green-600">23</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommunityForum;

