import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Button } from '../components/ui/button.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Input } from '../components/ui/input.jsx';
import { 
  Search, 
  Filter, 
  Eye, 
  Check, 
  X, 
  Clock, 
  Mail, 
  Phone, 
  Building, 
  User, 
  FileText, 
  Download,
  AlertCircle,
  CheckCircle,
  XCircle,
  Calendar,
  MessageSquare,
  Shield,
  ExternalLink
} from 'lucide-react';

const AdminApprovalDashboard = ({ user, onNavigate, onLogout }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedApplication, setSelectedApplication] = useState(null);

  // Mock pending applications data
  const pendingApplications = [
    {
      id: 'APP-001',
      applicant: {
        name: 'James Wilson',
        email: 'james.wilson@brisbane.qld.gov.au',
        phone: '+61 7 3403 8888',
        position: 'Grants Coordinator',
        department: 'Community Development'
      },
      organization: 'Brisbane City Council',
      submittedDate: '2024-08-20',
      status: 'pending_review',
      verificationStatus: {
        emailVerified: true,
        employmentVerified: false,
        adminReviewed: false
      },
      notes: []
    },
    {
      id: 'APP-002',
      applicant: {
        name: 'Maria Rodriguez',
        email: 'maria.rodriguez@wellington.govt.nz',
        phone: '+64 4 499 4444',
        position: 'Community Funding Officer',
        department: 'Social and Recreation'
      },
      organization: 'Wellington City Council',
      submittedDate: '2024-08-18',
      status: 'employment_verification',
      verificationStatus: {
        emailVerified: true,
        employmentVerified: true,
        adminReviewed: false
      },
      notes: [
        {
          date: '2024-08-19',
          author: 'System Admin',
          content: 'Employment confirmed via internal staff directory check.'
        }
      ]
    },
    {
      id: 'APP-003',
      applicant: {
        name: 'Robert Thompson',
        email: 'robert.thompson@perth.wa.gov.au',
        phone: '+61 8 9461 3333',
        position: 'Senior Grants Analyst',
        department: 'Economic Development'
      },
      organization: 'City of Perth',
      submittedDate: '2024-08-15',
      status: 'requires_clarification',
      verificationStatus: {
        emailVerified: true,
        employmentVerified: false,
        adminReviewed: true
      },
      notes: [
        {
          date: '2024-08-17',
          author: 'Admin Review Team',
          content: 'Unable to verify employment - please confirm this person works in the Economic Development department.'
        }
      ]
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending_review': return 'bg-yellow-100 text-yellow-800';
      case 'employment_verification': return 'bg-blue-100 text-blue-800';
      case 'requires_clarification': return 'bg-orange-100 text-orange-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending_review': return <Clock className="w-4 h-4" />;
      case 'employment_verification': return <MessageSquare className="w-4 h-4" />;
      case 'requires_clarification': return <AlertCircle className="w-4 h-4" />;
      case 'approved': return <CheckCircle className="w-4 h-4" />;
      case 'rejected': return <XCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const handleApproveApplication = (applicationId) => {
    // Implementation for approving application
    console.log('Approving application:', applicationId);
    // This would typically make an API call to approve the application
  };

  const handleRejectApplication = (applicationId) => {
    // Implementation for rejecting application
    console.log('Rejecting application:', applicationId);
    // This would typically make an API call to reject the application
  };

  const handleRequestDocuments = (applicationId) => {
    // Implementation for requesting documents from applicant
    console.log('Requesting documents for application:', applicationId);
    // This would typically send an email to the applicant requesting documents
  };

  const filteredApplications = pendingApplications.filter(app => {
    const matchesSearch = app.applicant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         app.applicant.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         app.organization.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterStatus === 'all' || app.status === filterStatus;
    
    return matchesSearch && matchesFilter;
  });

  if (selectedApplication) {
    const app = selectedApplication;
    
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={() => setSelectedApplication(null)}
              >
                ← Back to Applications
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Application Review</h1>
                <p className="text-gray-600">ID: {app.id}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Badge className={getStatusColor(app.status)}>
                {getStatusIcon(app.status)}
                <span className="ml-1 capitalize">{app.status.replace('_', ' ')}</span>
              </Badge>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Application Details */}
            <div className="lg:col-span-2 space-y-6">
              {/* Applicant Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="w-5 h-5 text-blue-600" />
                    Applicant Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Full Name</label>
                      <p className="text-gray-900">{app.applicant.name}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Email Address</label>
                      <p className="text-gray-900 flex items-center gap-2">
                        {app.applicant.email}
                        {app.verificationStatus.emailVerified && (
                          <CheckCircle className="w-4 h-4 text-green-600" />
                        )}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Phone Number</label>
                      <p className="text-gray-900">{app.applicant.phone}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Position</label>
                      <p className="text-gray-900">{app.applicant.position}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Department</label>
                      <p className="text-gray-900">{app.applicant.department}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Organization Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building className="w-5 h-5 text-blue-600" />
                    Organization Information
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Organization</label>
                    <p className="text-gray-900">{app.organization}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Employment Verification */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="w-5 h-5 text-blue-600" />
                    Employment Verification
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-blue-900 mb-1">Verification Instructions</h4>
                        <p className="text-sm text-blue-800 mb-3">
                          As the GrantThrive administrator, please verify this person's employment with your organization:
                        </p>
                        <ul className="text-sm text-blue-800 space-y-1">
                          <li>• Check if they work in the stated department</li>
                          <li>• Confirm their position/role is accurate</li>
                          <li>• Ask reception or HR if you don't recognize the name</li>
                          <li>• Request documents only if additional verification is needed</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-3 pt-4 border-t">
                    <Button
                      onClick={() => handleRequestDocuments(app.id)}
                      variant="outline"
                      className="flex items-center gap-2"
                    >
                      <FileText className="w-4 h-4" />
                      Request Documents
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => window.open(`mailto:${app.applicant.email}?subject=GrantThrive Account Verification`)}
                      className="flex items-center gap-2"
                    >
                      <Mail className="w-4 h-4" />
                      Contact Applicant
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Notes and Comments */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-blue-600" />
                    Review Notes
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {app.notes.length > 0 ? (
                    <div className="space-y-4">
                      {app.notes.map((note, index) => (
                        <div key={index} className="border-l-4 border-blue-200 pl-4">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-gray-900">{note.author}</span>
                            <span className="text-sm text-gray-500">{note.date}</span>
                          </div>
                          <p className="text-gray-700">{note.content}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 italic">No notes added yet.</p>
                  )}
                  
                  <div className="mt-4 pt-4 border-t">
                    <textarea
                      placeholder="Add a note about this application..."
                      className="w-full p-3 border border-gray-300 rounded-lg resize-none"
                      rows="3"
                    />
                    <Button className="mt-2">Add Note</Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar - Verification Status and Actions */}
            <div className="space-y-6">
              {/* Verification Checklist */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Verification Status</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">Email Verified</span>
                    {app.verificationStatus.emailVerified ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-600" />
                    )}
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">Employment Verified</span>
                    {app.verificationStatus.employmentVerified ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <Clock className="w-5 h-5 text-yellow-600" />
                    )}
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">Admin Reviewed</span>
                    {app.verificationStatus.adminReviewed ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <Clock className="w-5 h-5 text-yellow-600" />
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Application Timeline */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Application Timeline</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                      <div>
                        <p className="text-sm font-medium">Application Submitted</p>
                        <p className="text-xs text-gray-500">{app.submittedDate}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-yellow-600 rounded-full"></div>
                      <div>
                        <p className="text-sm font-medium">Under Review</p>
                        <p className="text-xs text-gray-500">Current Status</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Action Buttons */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button
                    onClick={() => handleApproveApplication(app.id)}
                    className="w-full bg-green-600 hover:bg-green-700"
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Approve Application
                  </Button>
                  
                  <Button
                    onClick={() => handleRejectApplication(app.id)}
                    variant="outline"
                    className="w-full border-red-300 text-red-700 hover:bg-red-50"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Reject Application
                  </Button>
                  
                  <Button
                    variant="outline"
                    className="w-full"
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Request Clarification
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Staff Application Approvals</h1>
            <p className="text-gray-600">Review and approve government staff applications</p>
          </div>
          
          <div className="flex items-center gap-4">
            <Badge className="bg-yellow-100 text-yellow-800">
              {pendingApplications.length} Pending Review
            </Badge>
            <Button onClick={onLogout} variant="outline">
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Search and Filter */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search applications..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="pending_review">Pending Review</option>
            <option value="employment_verification">Employment Verification</option>
            <option value="requires_clarification">Requires Clarification</option>
          </select>
        </div>

        {/* Applications List */}
        <div className="space-y-4">
          {filteredApplications.map((app) => (
            <Card key={app.id} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <User className="w-6 h-6 text-blue-600" />
                    </div>
                    
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{app.applicant.name}</h3>
                      <p className="text-gray-600">{app.applicant.position} • {app.organization}</p>
                      <p className="text-sm text-gray-500">{app.applicant.email}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <Badge className={getStatusColor(app.status)}>
                        {getStatusIcon(app.status)}
                        <span className="ml-1 capitalize">{app.status.replace('_', ' ')}</span>
                      </Badge>
                      <p className="text-sm text-gray-500 mt-1">
                        Submitted: {app.submittedDate}
                      </p>
                    </div>
                    
                    <Button
                      onClick={() => setSelectedApplication(app)}
                      className="flex items-center gap-2"
                    >
                      <Eye className="w-4 h-4" />
                      Review
                    </Button>
                  </div>
                </div>
                
                {/* Quick verification status */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center gap-6 text-sm">
                    <div className="flex items-center gap-2">
                      {app.verificationStatus.emailVerified ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600" />
                      )}
                      <span className="text-gray-600">Email Verified</span>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {app.verificationStatus.employmentVerified ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <Clock className="w-4 h-4 text-yellow-600" />
                      )}
                      <span className="text-gray-600">Employment Verified</span>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {app.verificationStatus.adminReviewed ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <Clock className="w-4 h-4 text-yellow-600" />
                      )}
                      <span className="text-gray-600">Admin Reviewed</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredApplications.length === 0 && (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No applications found</h3>
            <p className="text-gray-600">
              {searchTerm || filterStatus !== 'all' 
                ? 'Try adjusting your search or filter criteria.'
                : 'All staff applications have been processed.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminApprovalDashboard;

