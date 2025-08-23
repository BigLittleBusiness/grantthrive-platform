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
import { Calendar, Search, Plus, Edit, Trash2, Eye, Filter, Download, Upload } from 'lucide-react';

const Grants = () => {
  const { user } = useContext(AuthContext);
  const { grants, loading, createGrant, updateGrant, deleteGrant, fetchGrants } = useContext(GrantContext);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedGrant, setSelectedGrant] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    amount: '',
    opens_at: '',
    closes_at: '',
    eligibility_criteria: '',
    required_documents: '',
    contact_email: '',
    contact_phone: '',
    guidelines_url: '',
    status: 'draft'
  });

  const categories = [
    'Community Development',
    'Arts & Culture',
    'Environment',
    'Education',
    'Health & Wellbeing',
    'Sports & Recreation',
    'Infrastructure',
    'Economic Development',
    'Youth Programs',
    'Seniors Programs'
  ];

  const statuses = [
    { value: 'draft', label: 'Draft', color: 'bg-gray-500' },
    { value: 'open', label: 'Open', color: 'bg-green-500' },
    { value: 'closed', label: 'Closed', color: 'bg-red-500' },
    { value: 'under_review', label: 'Under Review', color: 'bg-yellow-500' },
    { value: 'completed', label: 'Completed', color: 'bg-blue-500' }
  ];

  useEffect(() => {
    fetchGrants();
  }, []);

  const filteredGrants = grants.filter(grant => {
    const matchesSearch = grant.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         grant.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || grant.status === statusFilter;
    const matchesCategory = categoryFilter === 'all' || grant.category === categoryFilter;
    
    return matchesSearch && matchesStatus && matchesCategory;
  });

  const handleCreateGrant = async (e) => {
    e.preventDefault();
    try {
      await createGrant(formData);
      setIsCreateDialogOpen(false);
      resetForm();
    } catch (error) {
      console.error('Error creating grant:', error);
    }
  };

  const handleUpdateGrant = async (e) => {
    e.preventDefault();
    try {
      await updateGrant(selectedGrant.id, formData);
      setIsEditDialogOpen(false);
      resetForm();
    } catch (error) {
      console.error('Error updating grant:', error);
    }
  };

  const handleDeleteGrant = async (grantId) => {
    if (window.confirm('Are you sure you want to delete this grant?')) {
      try {
        await deleteGrant(grantId);
      } catch (error) {
        console.error('Error deleting grant:', error);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      category: '',
      amount: '',
      opens_at: '',
      closes_at: '',
      eligibility_criteria: '',
      required_documents: '',
      contact_email: '',
      contact_phone: '',
      guidelines_url: '',
      status: 'draft'
    });
    setSelectedGrant(null);
  };

  const openEditDialog = (grant) => {
    setSelectedGrant(grant);
    setFormData({
      title: grant.title || '',
      description: grant.description || '',
      category: grant.category || '',
      amount: grant.amount || '',
      opens_at: grant.opens_at ? grant.opens_at.split('T')[0] : '',
      closes_at: grant.closes_at ? grant.closes_at.split('T')[0] : '',
      eligibility_criteria: grant.eligibility_criteria || '',
      required_documents: grant.required_documents || '',
      contact_email: grant.contact_email || '',
      contact_phone: grant.contact_phone || '',
      guidelines_url: grant.guidelines_url || '',
      status: grant.status || 'draft'
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
    return (
      <Badge className={`${statusInfo?.color} text-white`}>
        {statusInfo?.label || status}
      </Badge>
    );
  };

  const isCouncilUser = user?.role === 'council_admin' || user?.role === 'council_staff';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Grant Management</h1>
          <p className="text-gray-600 mt-1">
            {isCouncilUser ? 'Manage and monitor your council grants' : 'Browse available grants'}
          </p>
        </div>
        {isCouncilUser && (
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Plus className="w-4 h-4 mr-2" />
                Create Grant
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create New Grant</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreateGrant} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="title">Grant Title *</Label>
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) => setFormData({...formData, title: e.target.value})}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="category">Category *</Label>
                    <Select value={formData.category} onValueChange={(value) => setFormData({...formData, category: value})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map(category => (
                          <SelectItem key={category} value={category}>{category}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="description">Description *</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    rows={3}
                    required
                  />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="amount">Grant Amount (AUD) *</Label>
                    <Input
                      id="amount"
                      type="number"
                      value={formData.amount}
                      onChange={(e) => setFormData({...formData, amount: e.target.value})}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="opens_at">Opens Date *</Label>
                    <Input
                      id="opens_at"
                      type="date"
                      value={formData.opens_at}
                      onChange={(e) => setFormData({...formData, opens_at: e.target.value})}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="closes_at">Closes Date *</Label>
                    <Input
                      id="closes_at"
                      type="date"
                      value={formData.closes_at}
                      onChange={(e) => setFormData({...formData, closes_at: e.target.value})}
                      required
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="eligibility_criteria">Eligibility Criteria</Label>
                  <Textarea
                    id="eligibility_criteria"
                    value={formData.eligibility_criteria}
                    onChange={(e) => setFormData({...formData, eligibility_criteria: e.target.value})}
                    rows={3}
                  />
                </div>

                <div>
                  <Label htmlFor="required_documents">Required Documents</Label>
                  <Textarea
                    id="required_documents"
                    value={formData.required_documents}
                    onChange={(e) => setFormData({...formData, required_documents: e.target.value})}
                    rows={2}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="contact_email">Contact Email</Label>
                    <Input
                      id="contact_email"
                      type="email"
                      value={formData.contact_email}
                      onChange={(e) => setFormData({...formData, contact_email: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="contact_phone">Contact Phone</Label>
                    <Input
                      id="contact_phone"
                      value={formData.contact_phone}
                      onChange={(e) => setFormData({...formData, contact_phone: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="guidelines_url">Guidelines URL</Label>
                    <Input
                      id="guidelines_url"
                      type="url"
                      value={formData.guidelines_url}
                      onChange={(e) => setFormData({...formData, guidelines_url: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="status">Status</Label>
                    <Select value={formData.status} onValueChange={(value) => setFormData({...formData, status: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {statuses.map(status => (
                          <SelectItem key={status.value} value={status.value}>{status.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex justify-end space-x-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit">Create Grant</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search grants..."
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
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map(category => (
                  <SelectItem key={category} value={category}>{category}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Grants Grid */}
      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading grants...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredGrants.map(grant => (
            <Card key={grant.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg line-clamp-2">{grant.title}</CardTitle>
                  {getStatusBadge(grant.status)}
                </div>
                <div className="text-sm text-gray-600">{grant.category}</div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <p className="text-gray-700 line-clamp-3">{grant.description}</p>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-semibold text-green-600">
                      {formatCurrency(grant.amount)}
                    </span>
                    <span className="text-sm text-gray-500">
                      {grant.council_name}
                    </span>
                  </div>

                  {grant.opens_at && grant.closes_at && (
                    <div className="text-sm text-gray-600">
                      <div className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        Opens: {formatDate(grant.opens_at)}
                      </div>
                      <div className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        Closes: {formatDate(grant.closes_at)}
                      </div>
                    </div>
                  )}

                  <div className="flex justify-between items-center pt-2">
                    <Button variant="outline" size="sm">
                      <Eye className="w-4 h-4 mr-1" />
                      View Details
                    </Button>
                    
                    {isCouncilUser && (
                      <div className="flex space-x-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openEditDialog(grant)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteGrant(grant.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {filteredGrants.length === 0 && !loading && (
        <Card>
          <CardContent className="text-center py-8">
            <p className="text-gray-600">No grants found matching your criteria.</p>
            {isCouncilUser && (
              <Button 
                className="mt-4" 
                onClick={() => setIsCreateDialogOpen(true)}
              >
                Create Your First Grant
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Grant</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdateGrant} className="space-y-4">
            {/* Same form fields as create dialog */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-title">Grant Title *</Label>
                <Input
                  id="edit-title"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="edit-category">Category *</Label>
                <Select value={formData.category} onValueChange={(value) => setFormData({...formData, category: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map(category => (
                      <SelectItem key={category} value={category}>{category}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="edit-description">Description *</Label>
              <Textarea
                id="edit-description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                rows={3}
                required
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="edit-amount">Grant Amount (AUD) *</Label>
                <Input
                  id="edit-amount"
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({...formData, amount: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="edit-opens_at">Opens Date *</Label>
                <Input
                  id="edit-opens_at"
                  type="date"
                  value={formData.opens_at}
                  onChange={(e) => setFormData({...formData, opens_at: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="edit-closes_at">Closes Date *</Label>
                <Input
                  id="edit-closes_at"
                  type="date"
                  value={formData.closes_at}
                  onChange={(e) => setFormData({...formData, closes_at: e.target.value})}
                  required
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Update Grant</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Grants;

