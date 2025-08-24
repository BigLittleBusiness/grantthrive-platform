import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Button } from '../components/ui/button.jsx';
import { 
  FileText, 
  Clock, 
  DollarSign,
  Star,
  TrendingUp,
  Users,
  Calendar,
  MessageSquare,
  Trophy,
  BookOpen,
  Plus,
  Eye,
  ArrowRight,
  CheckCircle,
  AlertCircle,
  Download
} from 'lucide-react';

const CommunityMemberDashboard = () => {
  const memberMetrics = {
    totalApplications: 5,
    activeApplications: 2,
    approvedApplications: 2,
    totalFundingReceived: 85000,
    successRate: 67,
    communityRank: 'Gold Member'
  };

  const myApplications = [
    {
      id: 1,
      title: 'Youth Music Program Expansion',
      program: 'Youth Programs Initiative',
      amount: 25000,
      status: 'under_review',
      submittedDate: '2024-02-10',
      council: 'Melbourne City Council',
      progress: 60,
      nextStep: 'Awaiting committee review',
      estimatedDecision: '2024-02-25'
    },
    {
      id: 2,
      title: 'Community Garden Sustainability Project',
      program: 'Environmental Sustainability Fund',
      amount: 45000,
      status: 'approved',
      submittedDate: '2024-01-15',
      council: 'Melbourne City Council',
      progress: 100,
      nextStep: 'Funding agreement signed',
      estimatedDecision: 'Completed'
    },
    {
      id: 3,
      title: 'Senior Citizens Digital Literacy',
      program: 'Community Development Grant',
      amount: 15000,
      status: 'in_progress',
      submittedDate: '2024-02-05',
      council: 'Melbourne City Council',
      progress: 30,
      nextStep: 'Provide additional documentation',
      estimatedDecision: '2024-03-01'
    }
  ];

  const recommendedGrants = [
    {
      id: 1,
      title: 'Arts & Culture Development Grant',
      description: 'Support for community arts initiatives, cultural events, and creative programs.',
      amount: 50000,
      deadline: '2024-03-15',
      council: 'Melbourne City Council',
      category: 'Arts & Culture',
      applicants: 18,
      matchScore: 95
    },
    {
      id: 2,
      title: 'Community Health & Wellbeing Initiative',
      description: 'Funding for health promotion programs, mental health support, and wellness activities.',
      amount: 35000,
      deadline: '2024-02-28',
      council: 'Port Phillip Council',
      category: 'Health',
      applicants: 12,
      matchScore: 88
    },
    {
      id: 3,
      title: 'Digital Innovation for Community',
      description: 'Support for technology projects that enhance community connectivity and digital inclusion.',
      amount: 40000,
      deadline: '2024-04-01',
      council: 'Yarra City Council',
      category: 'Technology',
      applicants: 25,
      matchScore: 82
    }
  ];

  const upcomingEvents = [
    {
      id: 1,
      title: 'Grant Writing Workshop',
      date: '2024-02-20',
      time: '2:00 PM - 4:00 PM',
      type: 'Workshop',
      location: 'Melbourne Town Hall',
      spots: 15
    },
    {
      id: 2,
      title: 'Community Funding Information Session',
      date: '2024-02-25',
      time: '6:00 PM - 7:30 PM',
      type: 'Information Session',
      location: 'Online',
      spots: 50
    },
    {
      id: 3,
      title: 'Successful Applicants Networking Event',
      date: '2024-03-05',
      time: '5:30 PM - 8:00 PM',
      type: 'Networking',
      location: 'Federation Square',
      spots: 8
    }
  ];

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'under_review': return 'bg-blue-100 text-blue-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved': return <CheckCircle className="w-4 h-4" />;
      case 'under_review': return <Clock className="w-4 h-4" />;
      case 'in_progress': return <AlertCircle className="w-4 h-4" />;
      default: return <FileText className="w-4 h-4" />;
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome to Your Grant Journey! 🌟
        </h1>
        <p className="text-gray-600">
          Discover funding opportunities, track your applications, and connect with the community.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Button className="h-14 bg-blue-600 hover:bg-blue-700">
          <Plus className="w-5 h-5 mr-2" />
          Apply for Grant
        </Button>
        <Button variant="outline" className="h-14">
          <MessageSquare className="w-5 h-5 mr-2" />
          Join Discussion
        </Button>
        <Button variant="outline" className="h-14">
          <Calendar className="w-5 h-5 mr-2" />
          View Events
        </Button>
        <Button variant="outline" className="h-14">
          <BookOpen className="w-5 h-5 mr-2" />
          Resources
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">My Applications</p>
                <p className="text-3xl font-bold text-blue-600">{memberMetrics.totalApplications}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-3xl font-bold text-green-600">{memberMetrics.successRate}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Funding</p>
                <p className="text-3xl font-bold text-teal-600">{formatCurrency(memberMetrics.totalFundingReceived)}</p>
              </div>
              <DollarSign className="w-8 h-8 text-teal-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Community Status</p>
                <p className="text-lg font-bold text-yellow-600">{memberMetrics.communityRank}</p>
              </div>
              <Trophy className="w-8 h-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* My Applications */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>My Applications</span>
                <Badge variant="outline">{memberMetrics.activeApplications} Active</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {myApplications.map((app) => (
                  <div key={app.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-semibold text-gray-900">{app.title}</h4>
                        <p className="text-sm text-gray-600">{app.program}</p>
                        <p className="text-sm font-semibold text-green-600">{formatCurrency(app.amount)}</p>
                      </div>
                      <Badge className={getStatusColor(app.status)}>
                        <span className="flex items-center gap-1">
                          {getStatusIcon(app.status)}
                          {app.status.replace('_', ' ')}
                        </span>
                      </Badge>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span>Application Progress</span>
                        <span>{app.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${app.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="text-sm text-gray-600 mb-3">
                      <p><strong>Next Step:</strong> {app.nextStep}</p>
                      <p><strong>Expected Decision:</strong> {app.estimatedDecision}</p>
                      <p><strong>Council:</strong> {app.council}</p>
                    </div>

                    <div className="flex gap-2">
                      <Button size="sm" className="flex-1">
                        <Eye className="w-4 h-4 mr-1" />
                        View Details
                      </Button>
                      {app.status === 'in_progress' && (
                        <Button size="sm" variant="outline">
                          <FileText className="w-4 h-4 mr-1" />
                          Update
                        </Button>
                      )}
                      {app.status === 'approved' && (
                        <Button size="sm" variant="outline">
                          <Download className="w-4 h-4 mr-1" />
                          Agreement
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recommended Grants */}
          <Card className="mt-8">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Recommended for You</span>
                <Button variant="outline" size="sm">
                  View All Grants
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recommendedGrants.slice(0, 2).map((grant) => (
                  <div key={grant.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <Badge className="bg-green-100 text-green-800">
                        {grant.matchScore}% Match
                      </Badge>
                      <Button variant="ghost" size="sm">
                        <Star className="w-4 h-4" />
                      </Button>
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-2">{grant.title}</h4>
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                      {grant.description}
                    </p>
                    <div className="space-y-1 mb-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Amount</span>
                        <span className="font-semibold text-green-600">
                          {formatCurrency(grant.amount)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Deadline</span>
                        <span className="font-semibold">{grant.deadline}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Applicants</span>
                        <span className="font-semibold">{grant.applicants}</span>
                      </div>
                    </div>
                    <Button className="w-full bg-blue-600 hover:bg-blue-700" size="sm">
                      Apply Now
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div>
          {/* Upcoming Events */}
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Events</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {upcomingEvents.map((event) => (
                  <div key={event.id} className="border rounded-lg p-3">
                    <h5 className="font-semibold text-sm text-gray-900">{event.title}</h5>
                    <p className="text-xs text-gray-600 mt-1">{event.date} • {event.time}</p>
                    <p className="text-xs text-gray-600">{event.location}</p>
                    <div className="flex items-center justify-between mt-2">
                      <Badge variant="outline" size="sm">{event.type}</Badge>
                      <span className="text-xs text-gray-500">{event.spots} spots left</span>
                    </div>
                    <Button size="sm" className="w-full mt-2" variant="outline">
                      Register
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Community Stats */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Community Impact</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center">
                  <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mx-auto mb-2">
                    <Users className="w-6 h-6 text-blue-600" />
                  </div>
                  <p className="text-2xl font-bold text-blue-600">1,247</p>
                  <p className="text-sm text-gray-600">Community Members</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mx-auto mb-2">
                    <DollarSign className="w-6 h-6 text-green-600" />
                  </div>
                  <p className="text-2xl font-bold text-green-600">$2.5M</p>
                  <p className="text-sm text-gray-600">Funding Distributed</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mx-auto mb-2">
                    <Trophy className="w-6 h-6 text-purple-600" />
                  </div>
                  <p className="text-2xl font-bold text-purple-600">342</p>
                  <p className="text-sm text-gray-600">Successful Projects</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Tips */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Grant Success Tips</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Start applications early to allow time for revisions</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Attend workshops to improve your application quality</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Connect with other community members for advice</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Follow up promptly on any requests for information</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CommunityMemberDashboard;

