import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { GrantContext } from '../contexts/GrantContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Progress } from '../components/ui/progress';
import { FileText, Search, Plus, Edit, Trash2, Eye, Download, Upload, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

const Applications = () => {
  const { user } = useContext(AuthContext);
  const { applications, grants, loading, createApplication, updateApplication, deleteApplication, fetchApplications, fetchGrants } = useContext(GrantContext);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [grantFilter, setGrantFilter] = useState('all');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [formData, setFormData] = useState({
    grant_id: '',
    applicant_name: '',
    applicant_email: '',
    applicant_phone: '',
    organization_name: '',
    abn_acn: '',
    project_title: '',
    project_description: '',
    requested_amount: '',
    project_start_date: '',
    project_end_date: '',
    project_location: '',
    target_beneficiaries: '',
    expected_outcomes: '',
    budget_breakdown: '',
    previous_grants: '',
    references: ''
  });

  const statuses = [
    { value: 'draft', label: 'Draft', color: 'bg-gray-500', icon: FileText },
    { value: 'submitted', label: 'Submitted', color: 'bg-blue-500', icon: Clock },
    { value: 'under_review', label: 'Under Review', color: 'bg-yellow-500', icon: AlertCircle },
    { value: 'approved', label: 'Approved', color: 'bg-green-500', icon: CheckCircle },
    { value: 'rejected', label: 'Rejected', color: 'bg-red-500', icon: XCircle },
    { value: 'completed', label: 'Completed', color: 'bg-purple-500', icon: CheckCircle }
  ];

  useEffect(() => {
    fetchApplications();
    fetchGrants();
  }, []);

  const filteredApplications = applications.filter(application => {
    const matchesSearch = application.project_title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         application.applicant_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         application.organization_name?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || application.status === statusFilter;
    const matchesGrant = grantFilter === 'all' || application.grant_id === parseInt(grantFilter);
    
    return matchesSearch && matchesStatus && matchesGrant;
  });

  const handleCreateApplication = async (e) => {
    e.preventDefault();
    try {
      await createApplication(formData);
      setIsCreateDialogOpen(false);
      resetForm();
    } catch (error) {
      console.error('Error creating application:', error);
    }
  };

  const handleUpdateApplication = async (e) => {
    e.preventDefault();
    try {
      await updateApplication(selectedApplication.id, formData);
      setIsEditDialogOpen(false);
      resetForm();
    } catch (error) {
      console.error('Error updating application:', error);
    }
  };

  const handleDeleteApplication = async (applicationId) => {
    if (window.confirm('Are you sure you want to delete this application?')) {
      try {
        await deleteApplication(applicationId);
      } catch (error) {
        console.error('Error deleting application:', error);
      }
    }
  };

  const handleStatusUpdate = async (applicationId, newStatus) => {
    try {
      await updateApplication(applicationId, { status: newStatus });
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      grant_id: '',
      applicant_name: '',
      applicant_email: '',
      applicant_phone: '',
      organization_name: '',
      abn_acn: '',
      project_title: '',
      project_description: '',
      requested_amount: '',
      project_start_date: '',
      project_end_date: '',
      project_location: '',
      target_beneficiaries: '',
      expected_outcomes: '',
      budget_breakdown: '',
      previous_grants: '',
      references: ''
    });
    setSelectedApplication(null);
  };

  const openEditDialog = (application) => {
    setSelectedApplication(application);
    setFormData({
      grant_id: application.grant_id || '',
      applicant_name: application.applicant_name || '',
      applicant_email: application.applicant_email || '',
      applicant_phone: application.applicant_phone || '',
      organization_name: application.organization_name || '',
      abn_acn: application.abn_acn || '',
      project_title: application.project_title || '',
      project_description: application.project_description || '',
      requested_amount: application.requested_amount || '',
      project_start_date: application.project_start_date || '',
      project_end_date: application.project_end_date || '',
      project_location: application.project_location || '',
      target_beneficiaries: application.target_beneficiaries || '',
      expected_outcomes: application.expected_outcomes || '',
      budget_breakdown: application.budget_breakdown || '',
      previous_grants: application.previous_grants || '',
      references: application.references || ''
    });
    setIsEditDialogOpen(true);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-AU');
  };

  const getStatusBadge = (status) => {
    const statusInfo = statuses.find(s => s.value === status);
    const IconComponent = statusInfo?.icon || FileText;
    return (
      <Badge className={`${statusInfo?.color} text-white flex items-center gap-1`}>
        <IconComponent className="w-3 h-3" />
        {statusInfo?.label || status}
      </Badge>
    );
  };

  const getApplicationProgress = (status) => {
    const progressMap = {
      'draft': 20,
      'submitted': 40,
      'under_review': 60,
      'approved': 80,
      'completed': 100,
      'rejected': 0
    };
    return progressMap[status] || 0;
  };

  const isCouncilUser = user?.role === 'council_admin' || user?.role === 'council_staff';
  const isCommunityUser = user?.role === 'community_member';

  const getAvailableGrants = () => {
    return grants.filter(grant => grant.status === 'open');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Applications</h1>
          <p className="text-gray-600 mt-1">
            {isCouncilUser ? 'Review and manage grant applications' : 'Track your grant applications'}
          </p>
        </div>
        {isCommunityUser && (
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-green-600 hover:bg-green-700">
                <Plus className="w-4 h-4 mr-2" />
                New Application
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Submit Grant Application</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreateApplication} className="space-y-6">
                {/* Grant Selection */}
                <div>
                  <Label htmlFor="grant_id">Select Grant *</Label>
                  <Select value={formData.grant_id} onValueChange={(value) => setFormData({...formData, grant_id: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Choose a grant to apply for" />
                    </SelectTrigger>
                    <SelectContent>
                      {getAvailableGrants().map(grant => (
                        <SelectItem key={grant.id} value={grant.id.toString()}>
                          {grant.title} - {formatCurrency(grant.amount)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Applicant Information */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Applicant Information</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="applicant_name">Full Name *</Label>
                      <Input
                        id="applicant_name"
                        value={formData.applicant_name}
                        onChange={(e) => setFormData({...formData, applicant_name: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="applicant_email">Email Address *</Label>
                      <Input
                        id="applicant_email"
                        type="email"
                        value={formData.applicant_email}
                        onChange={(e) => setFormData({...formData, applicant_email: e.target.value})}
                        required
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="applicant_phone">Phone Number</Label>
                      <Input
                        id="applicant_phone"
                        value={formData.applicant_phone}
                        onChange={(e) => setFormData({...formData, applicant_phone: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label htmlFor="organization_name">Organization Name</Label>
                      <Input
                        id="organization_name"
                        value={formData.organization_name}
                        onChange={(e) => setFormData({...formData, organization_name: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label htmlFor="abn_acn">ABN/ACN</Label>
                      <Input
                        id="abn_acn"
                        value={formData.abn_acn}
                        onChange={(e) => setFormData({...formData, abn_acn: e.target.value})}
                      />
                    </div>
                  </div>
                </div>

                {/* Project Information */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Project Information</h3>
                  <div>
                    <Label htmlFor="project_title">Project Title *</Label>
                    <Input
                      id="project_title"
                      value={formData.project_title}
                      onChange={(e) => setFormData({...formData, project_title: e.target.value})}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="project_description">Project Description *</Label>
                    <Textarea
                      id="project_description"
                      value={formData.project_description}
                      onChange={(e) => setFormData({...formData, project_description: e.target.value})}
                      rows={4}
                      required
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="requested_amount">Requested Amount (AUD) *</Label>
                      <Input
                        id="requested_amount"
                        type="number"
                        value={formData.requested_amount}
                        onChange={(e) => setFormData({...formData, requested_amount: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="project_start_date">Project Start Date</Label>
                      <Input
                        id="project_start_date"
                        type="date"
                        value={formData.project_start_date}
                        onChange={(e) => setFormData({...formData, project_start_date: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label htmlFor="project_end_date">Project End Date</Label>
                      <Input
                        id="project_end_date"
                        type="date"
                        value={formData.project_end_date}
                        onChange={(e) => setFormData({...formData, project_end_date: e.target.value})}
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="project_location">Project Location</Label>
                    <Input
                      id="project_location"
                      value={formData.project_location}
                      onChange={(e) => setFormData({...formData, project_location: e.target.value})}
                    />
                  </div>
                </div>

                {/* Additional Details */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Additional Details</h3>
                  <div>
                    <Label htmlFor="target_beneficiaries">Target Beneficiaries</Label>
                    <Textarea
                      id="target_beneficiaries"
                      value={formData.target_beneficiaries}
                      onChange={(e) => setFormData({...formData, target_beneficiaries: e.target.value})}
                      rows={2}
                    />
                  </div>
                  <div>
                    <Label htmlFor="expected_outcomes">Expected Outcomes</Label>
                    <Textarea
                      id="expected_outcomes"
                      value={formData.expected_outcomes}
                      onChange={(e) => setFormData({...formData, expected_outcomes: e.target.value})}
                      rows={3}
                    />
                  </div>
                  <div>
                    <Label htmlFor="budget_breakdown">Budget Breakdown</Label>
                    <Textarea
                      id="budget_breakdown"
                      value={formData.budget_breakdown}
                      onChange={(e) => setFormData({...formData, budget_breakdown: e.target.value})}
                      rows={3}
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit">Submit Application</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {statuses.slice(1).map(status => {
          const count = applications.filter(app => app.status === status.value).length;
          return (
            <Card key={status.value}>
              <CardContent className="pt-6">
                <div className="flex items-center">
                  <status.icon className={`h-8 w-8 ${status.color.replace('bg-', 'text-')}`} />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">{status.label}</p>
                    <p className="text-2xl font-bold">{count}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search applications..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {statuses.map(status => (
                  <SelectItem key={status.value} value={status.value}>{status.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={grantFilter} onValueChange={setGrantFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by grant" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Grants</SelectItem>
                {grants.map(grant => (
                  <SelectItem key={grant.id} value={grant.id.toString()}>{grant.title}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Applications List */}
      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading applications...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredApplications.map(application => (
            <Card key={application.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="pt-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold">{application.project_title}</h3>
                    <p className="text-gray-600">{application.applicant_name} • {application.organization_name}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      Grant: {grants.find(g => g.id === application.grant_id)?.title}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusBadge(application.status)}
                    <span className="text-lg font-semibold text-green-600">
                      {formatCurrency(application.requested_amount)}
                    </span>
                  </div>
                </div>

                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Application Progress</span>
                    <span>{getApplicationProgress(application.status)}%</span>
                  </div>
                  <Progress value={getApplicationProgress(application.status)} className="h-2" />
                </div>

                <p className="text-gray-700 mb-4 line-clamp-2">{application.project_description}</p>

                <div className="flex justify-between items-center">
                  <div className="text-sm text-gray-600">
                    Submitted: {formatDate(application.created_at)}
                  </div>
                  
                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm">
                      <Eye className="w-4 h-4 mr-1" />
                      View Details
                    </Button>
                    
                    {isCouncilUser && application.status === 'submitted' && (
                      <>
                        <Button
                          size="sm"
                          onClick={() => handleStatusUpdate(application.id, 'under_review')}
                          className="bg-yellow-600 hover:bg-yellow-700"
                        >
                          Review
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleStatusUpdate(application.id, 'approved')}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleStatusUpdate(application.id, 'rejected')}
                          className="bg-red-600 hover:bg-red-700"
                        >
                          Reject
                        </Button>
                      </>
                    )}
                    
                    {isCommunityUser && application.status === 'draft' && (
                      <Button
                        size="sm"
                        onClick={() => openEditDialog(application)}
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        Edit
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {filteredApplications.length === 0 && !loading && (
        <Card>
          <CardContent className="text-center py-8">
            <p className="text-gray-600">No applications found matching your criteria.</p>
            {isCommunityUser && (
              <Button 
                className="mt-4" 
                onClick={() => setIsCreateDialogOpen(true)}
              >
                Submit Your First Application
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Applications;

