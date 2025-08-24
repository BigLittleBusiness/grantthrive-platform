import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Button } from '../components/ui/button.jsx';
import { 
  FileText, 
  Clock, 
  CheckCircle,
  MessageSquare,
  Phone,
  Mail,
  Calendar,
  User,
  AlertCircle,
  Eye,
  Edit,
  Send,
  Download
} from 'lucide-react';

const CouncilStaffDashboard = () => {
  const staffMetrics = {
    assignedApplications: 15,
    completedToday: 3,
    pendingReview: 8,
    awaitingDocuments: 4,
    averageReviewTime: 5.2,
    communityContacts: 12
  };

  const myApplications = [
    {
      id: 1,
      applicant: 'Riverside Community Garden',
      contact: 'Maria Santos',
      email: 'maria@riverside.org.au',
      phone: '0412 345 678',
      program: 'Community Development Grant',
      amount: 35000,
      status: 'review_in_progress',
      priority: 'medium',
      assignedDate: '2024-02-12',
      dueDate: '2024-02-19',
      completionPercent: 60,
      lastAction: 'Requested additional budget breakdown'
    },
    {
      id: 2,
      applicant: 'Youth Basketball League',
      contact: 'James Wilson',
      email: 'james@ybl.org.au',
      phone: '0423 456 789',
      program: 'Youth Programs Initiative',
      amount: 18000,
      status: 'awaiting_documents',
      priority: 'high',
      assignedDate: '2024-02-10',
      dueDate: '2024-02-17',
      completionPercent: 30,
      lastAction: 'Waiting for insurance certificates'
    },
    {
      id: 3,
      applicant: 'Green Schools Network',
      contact: 'Dr. Sarah Chen',
      email: 'sarah@greenschools.edu.au',
      phone: '0434 567 890',
      program: 'Environmental Sustainability',
      amount: 52000,
      status: 'ready_for_approval',
      priority: 'low',
      assignedDate: '2024-02-08',
      dueDate: '2024-02-15',
      completionPercent: 95,
      lastAction: 'Completed assessment - ready for final approval'
    }
  ];

  const todaysTasks = [
    {
      id: 1,
      task: 'Complete review of Riverside Community Garden application',
      type: 'review',
      priority: 'high',
      estimatedTime: '2 hours',
      dueTime: '2:00 PM'
    },
    {
      id: 2,
      task: 'Follow up with Youth Basketball League for missing documents',
      type: 'communication',
      priority: 'high',
      estimatedTime: '30 minutes',
      dueTime: '11:00 AM'
    },
    {
      id: 3,
      task: 'Prepare recommendation report for Green Schools Network',
      type: 'documentation',
      priority: 'medium',
      estimatedTime: '1 hour',
      dueTime: '4:00 PM'
    },
    {
      id: 4,
      task: 'Attend weekly grant committee meeting',
      type: 'meeting',
      priority: 'medium',
      estimatedTime: '1 hour',
      dueTime: '3:00 PM'
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
      case 'review_in_progress': return 'bg-blue-100 text-blue-800';
      case 'awaiting_documents': return 'bg-yellow-100 text-yellow-800';
      case 'ready_for_approval': return 'bg-green-100 text-green-800';
      case 'on_hold': return 'bg-red-100 text-red-800';
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
      case 'review': return <FileText className="w-4 h-4" />;
      case 'communication': return <MessageSquare className="w-4 h-4" />;
      case 'documentation': return <Edit className="w-4 h-4" />;
      case 'meeting': return <Calendar className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          My Grant Reviews Dashboard
        </h1>
        <p className="text-gray-600">
          Manage your assigned applications and community engagement tasks.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Button className="h-14 bg-blue-600 hover:bg-blue-700">
          <FileText className="w-5 h-5 mr-2" />
          Start Review
        </Button>
        <Button variant="outline" className="h-14">
          <MessageSquare className="w-5 h-5 mr-2" />
          Contact Applicant
        </Button>
        <Button variant="outline" className="h-14">
          <Download className="w-5 h-5 mr-2" />
          Generate Report
        </Button>
        <Button variant="outline" className="h-14">
          <Calendar className="w-5 h-5 mr-2" />
          Schedule Meeting
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Assigned to Me</p>
                <p className="text-3xl font-bold text-blue-600">{staffMetrics.assignedApplications}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Review</p>
                <p className="text-3xl font-bold text-orange-600">{staffMetrics.pendingReview}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Completed Today</p>
                <p className="text-3xl font-bold text-green-600">{staffMetrics.completedToday}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Review Time</p>
                <p className="text-3xl font-bold text-purple-600">{staffMetrics.averageReviewTime}d</p>
              </div>
              <Clock className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* My Applications */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>My Assigned Applications</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {myApplications.map((app) => (
                  <div key={app.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-semibold text-gray-900">{app.applicant}</h4>
                        <p className="text-sm text-gray-600">{app.program}</p>
                        <p className="text-sm font-semibold text-green-600">{formatCurrency(app.amount)}</p>
                      </div>
                      <div className="flex flex-col gap-2">
                        <Badge className={getStatusColor(app.status)}>
                          {app.status.replace(/_/g, ' ')}
                        </Badge>
                        <Badge className={getPriorityColor(app.priority)}>
                          {app.priority}
                        </Badge>
                      </div>
                    </div>

                    {/* Contact Information */}
                    <div className="bg-gray-50 rounded-lg p-3 mb-3">
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <User className="w-4 h-4 text-gray-500" />
                          <span className="font-medium">{app.contact}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Mail className="w-4 h-4 text-gray-500" />
                          <span>{app.email}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Phone className="w-4 h-4 text-gray-500" />
                          <span>{app.phone}</span>
                        </div>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span>Review Progress</span>
                        <span>{app.completionPercent}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${app.completionPercent}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="text-sm text-gray-600 mb-3">
                      <p><strong>Last Action:</strong> {app.lastAction}</p>
                      <p><strong>Due:</strong> {app.dueDate}</p>
                    </div>

                    <div className="flex gap-2">
                      <Button size="sm" className="flex-1">
                        <Eye className="w-4 h-4 mr-1" />
                        Review
                      </Button>
                      <Button size="sm" variant="outline">
                        <MessageSquare className="w-4 h-4 mr-1" />
                        Contact
                      </Button>
                      <Button size="sm" variant="outline">
                        <Edit className="w-4 h-4 mr-1" />
                        Update
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Today's Tasks */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Today's Tasks</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {todaysTasks.map((task) => (
                  <div key={task.id} className="border rounded-lg p-3">
                    <div className="flex items-start gap-3">
                      <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-lg">
                        {getTaskIcon(task.type)}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{task.task}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge className={getPriorityColor(task.priority)} size="sm">
                            {task.priority}
                          </Badge>
                          <span className="text-xs text-gray-500">{task.estimatedTime}</span>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">Due: {task.dueTime}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>This Week's Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Applications Reviewed</span>
                  <span className="font-semibold">12</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Recommendations Made</span>
                  <span className="font-semibold">8</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Community Contacts</span>
                  <span className="font-semibold">{staffMetrics.communityContacts}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Avg Response Time</span>
                  <span className="font-semibold">2.3 hours</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CouncilStaffDashboard;

