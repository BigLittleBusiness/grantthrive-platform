import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Button } from '../components/ui/button.jsx';
import { 
  Briefcase, 
  Users, 
  DollarSign,
  Star,
  TrendingUp,
  Clock,
  Calendar,
  MessageSquare,
  FileText,
  Award,
  Plus,
  Eye,
  Phone,
  Mail,
  MapPin,
  CheckCircle,
  AlertCircle,
  Target
} from 'lucide-react';

const ProfessionalConsultantDashboard = () => {
  const consultantMetrics = {
    activeClients: 8,
    totalProjects: 24,
    successRate: 89,
    totalEarnings: 145000,
    averageProjectValue: 6500,
    clientSatisfaction: 4.8,
    monthlyRevenue: 18500,
    pendingProposals: 5
  };

  const activeProjects = [
    {
      id: 1,
      client: 'Riverside Community Centre',
      contact: 'Maria Santos',
      email: 'maria@riverside.org.au',
      phone: '0412 345 678',
      project: 'Community Development Grant Application',
      value: 8500,
      status: 'in_progress',
      progress: 75,
      deadline: '2024-02-20',
      grantAmount: 45000,
      stage: 'Final review and submission'
    },
    {
      id: 2,
      client: 'Youth Basketball League',
      contact: 'James Wilson',
      email: 'james@ybl.org.au',
      phone: '0423 456 789',
      project: 'Youth Programs Grant Strategy',
      value: 5500,
      status: 'awaiting_approval',
      progress: 90,
      deadline: '2024-02-18',
      grantAmount: 25000,
      stage: 'Client review of final application'
    },
    {
      id: 3,
      client: 'Green Schools Network',
      contact: 'Dr. Sarah Chen',
      email: 'sarah@greenschools.edu.au',
      phone: '0434 567 890',
      project: 'Environmental Sustainability Funding',
      value: 12000,
      status: 'planning',
      progress: 25,
      deadline: '2024-03-15',
      grantAmount: 75000,
      stage: 'Research and strategy development'
    }
  ];

  const marketplaceOpportunities = [
    {
      id: 1,
      title: 'Arts & Culture Grant Application Support',
      client: 'Melbourne Arts Collective',
      budget: 7500,
      deadline: '2024-02-25',
      grantValue: 50000,
      requirements: ['Grant writing experience', 'Arts sector knowledge', 'Melbourne location preferred'],
      proposals: 3,
      matchScore: 95
    },
    {
      id: 2,
      title: 'Community Health Program Funding Strategy',
      client: 'Wellbeing Community Hub',
      budget: 9500,
      deadline: '2024-03-01',
      grantValue: 65000,
      requirements: ['Health sector experience', 'Strategic planning', 'Budget development'],
      proposals: 5,
      matchScore: 88
    },
    {
      id: 3,
      title: 'Digital Innovation Grant Consultation',
      client: 'Tech for Good Initiative',
      budget: 6000,
      deadline: '2024-02-28',
      grantValue: 40000,
      requirements: ['Technology grants experience', 'Innovation sector knowledge'],
      proposals: 7,
      matchScore: 82
    }
  ];

  const upcomingDeadlines = [
    {
      id: 1,
      task: 'Submit Riverside Community Centre application',
      client: 'Riverside Community Centre',
      deadline: '2024-02-20',
      priority: 'high',
      type: 'submission'
    },
    {
      id: 2,
      task: 'Client meeting - Youth Basketball League',
      client: 'Youth Basketball League',
      deadline: '2024-02-18',
      priority: 'medium',
      type: 'meeting'
    },
    {
      id: 3,
      task: 'Proposal deadline - Arts Collective opportunity',
      client: 'Melbourne Arts Collective',
      deadline: '2024-02-25',
      priority: 'high',
      type: 'proposal'
    },
    {
      id: 4,
      task: 'Strategy presentation - Green Schools Network',
      client: 'Green Schools Network',
      deadline: '2024-02-22',
      priority: 'medium',
      type: 'presentation'
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
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'awaiting_approval': return 'bg-yellow-100 text-yellow-800';
      case 'planning': return 'bg-purple-100 text-purple-800';
      case 'completed': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTaskIcon = (type) => {
    switch (type) {
      case 'submission': return <FileText className="w-4 h-4" />;
      case 'meeting': return <Users className="w-4 h-4" />;
      case 'proposal': return <Briefcase className="w-4 h-4" />;
      case 'presentation': return <Award className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Professional Services Dashboard 💼
        </h1>
        <p className="text-gray-600">
          Manage your grant consulting projects, find new opportunities, and grow your practice.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Button className="h-14 bg-blue-600 hover:bg-blue-700">
          <Plus className="w-5 h-5 mr-2" />
          New Project
        </Button>
        <Button variant="outline" className="h-14">
          <Briefcase className="w-5 h-5 mr-2" />
          Browse Opportunities
        </Button>
        <Button variant="outline" className="h-14">
          <MessageSquare className="w-5 h-5 mr-2" />
          Client Communication
        </Button>
        <Button variant="outline" className="h-14">
          <Award className="w-5 h-5 mr-2" />
          Portfolio
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Clients</p>
                <p className="text-3xl font-bold text-blue-600">{consultantMetrics.activeClients}</p>
              </div>
              <Users className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-3xl font-bold text-green-600">{consultantMetrics.successRate}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Monthly Revenue</p>
                <p className="text-3xl font-bold text-teal-600">{formatCurrency(consultantMetrics.monthlyRevenue)}</p>
              </div>
              <DollarSign className="w-8 h-8 text-teal-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Client Rating</p>
                <p className="text-3xl font-bold text-yellow-600">{consultantMetrics.clientSatisfaction}</p>
              </div>
              <Star className="w-8 h-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Projects */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Active Projects</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {activeProjects.map((project) => (
                  <div key={project.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-semibold text-gray-900">{project.client}</h4>
                        <p className="text-sm text-gray-600">{project.project}</p>
                        <p className="text-sm font-semibold text-green-600">
                          {formatCurrency(project.value)} • Grant: {formatCurrency(project.grantAmount)}
                        </p>
                      </div>
                      <Badge className={getStatusColor(project.status)}>
                        {project.status.replace('_', ' ')}
                      </Badge>
                    </div>

                    {/* Contact Information */}
                    <div className="bg-gray-50 rounded-lg p-3 mb-3">
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <Users className="w-4 h-4 text-gray-500" />
                          <span className="font-medium">{project.contact}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Mail className="w-4 h-4 text-gray-500" />
                          <span>{project.email}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Phone className="w-4 h-4 text-gray-500" />
                          <span>{project.phone}</span>
                        </div>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span>Project Progress</span>
                        <span>{project.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${project.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="text-sm text-gray-600 mb-3">
                      <p><strong>Current Stage:</strong> {project.stage}</p>
                      <p><strong>Deadline:</strong> {project.deadline}</p>
                    </div>

                    <div className="flex gap-2">
                      <Button size="sm" className="flex-1">
                        <Eye className="w-4 h-4 mr-1" />
                        View Project
                      </Button>
                      <Button size="sm" variant="outline">
                        <MessageSquare className="w-4 h-4 mr-1" />
                        Contact Client
                      </Button>
                      <Button size="sm" variant="outline">
                        <FileText className="w-4 h-4 mr-1" />
                        Update
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Marketplace Opportunities */}
          <Card className="mt-8">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>New Opportunities</span>
                <Badge variant="outline">{consultantMetrics.pendingProposals} Proposals Pending</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {marketplaceOpportunities.map((opp) => (
                  <div key={opp.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-semibold text-gray-900">{opp.title}</h4>
                        <p className="text-sm text-gray-600">{opp.client}</p>
                      </div>
                      <Badge className="bg-green-100 text-green-800">
                        {opp.matchScore}% Match
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                      <div>
                        <span className="text-gray-500">Your Fee:</span>
                        <span className="font-semibold text-green-600 ml-2">
                          {formatCurrency(opp.budget)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Grant Value:</span>
                        <span className="font-semibold ml-2">
                          {formatCurrency(opp.grantValue)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Deadline:</span>
                        <span className="font-semibold ml-2">{opp.deadline}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Proposals:</span>
                        <span className="font-semibold ml-2">{opp.proposals}</span>
                      </div>
                    </div>

                    <div className="mb-3">
                      <p className="text-sm text-gray-600 mb-2"><strong>Requirements:</strong></p>
                      <div className="flex flex-wrap gap-1">
                        {opp.requirements.map((req, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {req}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button size="sm" className="flex-1">
                        Submit Proposal
                      </Button>
                      <Button size="sm" variant="outline">
                        <Eye className="w-4 h-4 mr-1" />
                        View Details
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div>
          {/* Upcoming Deadlines */}
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Deadlines</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {upcomingDeadlines.map((deadline) => (
                  <div key={deadline.id} className="border rounded-lg p-3">
                    <div className="flex items-start gap-3">
                      <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-lg">
                        {getTaskIcon(deadline.type)}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{deadline.task}</p>
                        <p className="text-xs text-gray-600">{deadline.client}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge className={getPriorityColor(deadline.priority)} size="sm">
                            {deadline.priority}
                          </Badge>
                          <span className="text-xs text-gray-500">{deadline.deadline}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Performance Stats */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>This Month's Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Projects Completed</span>
                  <span className="font-semibold">4</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">New Clients</span>
                  <span className="font-semibold">2</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Proposals Submitted</span>
                  <span className="font-semibold">7</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Win Rate</span>
                  <span className="font-semibold text-green-600">71%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Avg Project Value</span>
                  <span className="font-semibold">{formatCurrency(consultantMetrics.averageProjectValue)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Professional Development */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Professional Growth</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-center">
                  <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mx-auto mb-2">
                    <Award className="w-6 h-6 text-blue-600" />
                  </div>
                  <p className="text-2xl font-bold text-blue-600">{consultantMetrics.totalProjects}</p>
                  <p className="text-sm text-gray-600">Total Projects</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mx-auto mb-2">
                    <Target className="w-6 h-6 text-green-600" />
                  </div>
                  <p className="text-2xl font-bold text-green-600">{formatCurrency(consultantMetrics.totalEarnings)}</p>
                  <p className="text-sm text-gray-600">Total Earnings</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-lg mx-auto mb-2">
                    <Star className="w-6 h-6 text-yellow-600" />
                  </div>
                  <p className="text-2xl font-bold text-yellow-600">{consultantMetrics.clientSatisfaction}/5.0</p>
                  <p className="text-sm text-gray-600">Client Rating</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ProfessionalConsultantDashboard;

