import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Button } from '../components/ui/button.jsx';
import { 
  Users, 
  FileText, 
  DollarSign, 
  Clock, 
  AlertTriangle,
  TrendingUp,
  CheckCircle,
  XCircle,
  Eye,
  MessageSquare,
  Calendar,
  Settings,
  BarChart3,
  Plus,
  UserCheck
} from 'lucide-react';

const CouncilAdminDashboard = ({ onNavigate }) => {
  const adminMetrics = {
    totalPrograms: 8,
    activeApplications: 47,
    pendingReviews: 12,
    totalBudget: 2500000,
    approvedThisMonth: 15,
    rejectedThisMonth: 3,
    communityMembers: 1247,
    averageProcessingTime: 14
  };

  const pendingApplications = [
    {
      id: 1,
      applicant: 'Westside Community Centre',
      program: 'Community Development Grant',
      amount: 45000,
      submittedDate: '2024-02-10',
      daysWaiting: 5,
      priority: 'high',
      status: 'under_review'
    },
    {
      id: 2,
      applicant: 'Youth Sports Alliance',
      program: 'Youth Programs Initiative',
      amount: 22000,
      submittedDate: '2024-02-08',
      daysWaiting: 7,
      priority: 'medium',
      status: 'pending_documents'
    },
    {
      id: 3,
      applicant: 'Green Future Collective',
      program: 'Environmental Sustainability',
      amount: 67000,
      submittedDate: '2024-02-05',
      daysWaiting: 10,
      priority: 'high',
      status: 'committee_review'
    }
  ];

  const grantPrograms = [
    {
      id: 1,
      name: 'Community Development Grant',
      budget: 500000,
      allocated: 320000,
      applications: 23,
      approved: 8,
      status: 'active',
      deadline: '2024-03-15'
    },
    {
      id: 2,
      name: 'Youth Programs Initiative',
      budget: 300000,
      allocated: 180000,
      applications: 15,
      approved: 5,
      status: 'active',
      deadline: '2024-02-28'
    },
    {
      id: 3,
      name: 'Environmental Sustainability',
      budget: 750000,
      allocated: 425000,
      applications: 31,
      approved: 12,
      status: 'active',
      deadline: '2024-04-01'
    }
  ];

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'under_review': return 'bg-blue-100 text-blue-800';
      case 'pending_documents': return 'bg-yellow-100 text-yellow-800';
      case 'committee_review': return 'bg-purple-100 text-purple-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Council Administration Dashboard
        </h1>
        <p className="text-gray-600">
          Manage grant programs, review applications, and oversee community funding.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Button 
          className="h-14 bg-blue-600 hover:bg-blue-700"
          onClick={() => onNavigate('create-grant')}
        >
          <Plus className="w-5 h-5 mr-2" />
          Create Grant Program
        </Button>
        <Button variant="outline" className="h-14">
          <FileText className="w-5 h-5 mr-2" />
          Review Applications
        </Button>
        <Button variant="outline" className="h-14">
          <UserCheck className="w-5 h-5 mr-2" />
          Staff Approvals
        </Button>
        <Button variant="outline" className="h-14">
          <BarChart3 className="w-5 h-5 mr-2" />
          Generate Reports
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Programs</p>
                <p className="text-3xl font-bold text-blue-600">{adminMetrics.totalPrograms}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Reviews</p>
                <p className="text-3xl font-bold text-orange-600">{adminMetrics.pendingReviews}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Budget</p>
                <p className="text-3xl font-bold text-green-600">{formatCurrency(adminMetrics.totalBudget)}</p>
              </div>
              <DollarSign className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Community Members</p>
                <p className="text-3xl font-bold text-purple-600">{adminMetrics.communityMembers.toLocaleString()}</p>
              </div>
              <Users className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Pending Applications Requiring Attention */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Applications Requiring Review</span>
              <Badge variant="destructive">{adminMetrics.pendingReviews} Pending</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {pendingApplications.map((app) => (
                <div key={app.id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="font-semibold text-gray-900">{app.applicant}</h4>
                      <p className="text-sm text-gray-600">{app.program}</p>
                    </div>
                    <div className="flex gap-2">
                      <Badge className={getPriorityColor(app.priority)}>
                        {app.priority}
                      </Badge>
                      <Badge className={getStatusColor(app.status)}>
                        {app.status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-semibold text-green-600">
                      {formatCurrency(app.amount)}
                    </span>
                    <span className="text-gray-500">
                      {app.daysWaiting} days waiting
                    </span>
                  </div>
                  <div className="flex gap-2 mt-3">
                    <Button size="sm" className="flex-1">
                      <Eye className="w-4 h-4 mr-1" />
                      Review
                    </Button>
                    <Button size="sm" variant="outline">
                      <MessageSquare className="w-4 h-4 mr-1" />
                      Contact
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Grant Programs Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Grant Programs Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {grantPrograms.map((program) => (
                <div key={program.id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="font-semibold text-gray-900">{program.name}</h4>
                      <p className="text-sm text-gray-600">
                        {program.applications} applications • {program.approved} approved
                      </p>
                    </div>
                    <Badge className="bg-green-100 text-green-800">
                      Active
                    </Badge>
                  </div>
                  
                  <div className="mb-3">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Budget Allocated</span>
                      <span>{Math.round((program.allocated / program.budget) * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${(program.allocated / program.budget) * 100}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>{formatCurrency(program.allocated)}</span>
                      <span>{formatCurrency(program.budget)}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Deadline: {program.deadline}</span>
                    <Button size="sm" variant="outline">
                      <Settings className="w-4 h-4 mr-1" />
                      Manage
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Performance Summary */}
      <div className="mt-8">
        <Card>
          <CardHeader>
            <CardTitle>This Month's Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mx-auto mb-2">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <p className="text-2xl font-bold text-green-600">{adminMetrics.approvedThisMonth}</p>
                <p className="text-sm text-gray-600">Applications Approved</p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center w-12 h-12 bg-red-100 rounded-lg mx-auto mb-2">
                  <XCircle className="w-6 h-6 text-red-600" />
                </div>
                <p className="text-2xl font-bold text-red-600">{adminMetrics.rejectedThisMonth}</p>
                <p className="text-sm text-gray-600">Applications Rejected</p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mx-auto mb-2">
                  <Clock className="w-6 h-6 text-blue-600" />
                </div>
                <p className="text-2xl font-bold text-blue-600">{adminMetrics.averageProcessingTime}</p>
                <p className="text-sm text-gray-600">Avg. Processing Days</p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mx-auto mb-2">
                  <TrendingUp className="w-6 h-6 text-purple-600" />
                </div>
                <p className="text-2xl font-bold text-purple-600">
                  {Math.round((adminMetrics.approvedThisMonth / (adminMetrics.approvedThisMonth + adminMetrics.rejectedThisMonth)) * 100)}%
                </p>
                <p className="text-sm text-gray-600">Approval Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CouncilAdminDashboard;

