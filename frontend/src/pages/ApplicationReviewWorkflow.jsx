import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { 
  Search, 
  Filter, 
  Eye, 
  Star, 
  MessageSquare, 
  Download, 
  CheckCircle, 
  XCircle,
  Clock,
  TrendingUp,
  Users,
  FileText,
  Calendar,
  DollarSign,
  BarChart3,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  Send,
  Lightbulb
} from 'lucide-react';

const ApplicationReviewWorkflow = ({ grantId = 'community-development-grant' }) => {
  const [applications, setApplications] = useState([]);
  const [filteredApplications, setFilteredApplications] = useState([]);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [activeTab, setActiveTab] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('latest');
  const [isLoading, setIsLoading] = useState(true);
  const [showScoring, setShowScoring] = useState(false);
  const [scores, setScores] = useState({});

  // Mock data - will be replaced with real API calls
  const mockApplications = [
    {
      id: 'app-001',
      applicantName: 'Alexander Morales',
      organization: 'Neighborhood Alliance',
      submissionDate: '2024-03-18',
      status: 'under_review',
      score: null,
      amount: 25000,
      projectTitle: 'Community Garden Initiative',
      category: 'Community Development',
      priority: 'high',
      reviewers: ['Sarah Johnson', 'Michael Chen'],
      documents: ['project_plan.pdf', 'budget.xlsx', 'references.pdf'],
      summary: 'Establishing community gardens to improve food security and social cohesion in underserved neighborhoods.'
    },
    {
      id: 'app-002',
      applicantName: 'Lily Stevens',
      organization: 'City Volunteers',
      submissionDate: '2024-03-14',
      status: 'under_review',
      score: null,
      amount: 15000,
      projectTitle: 'Youth Mentorship Program',
      category: 'Youth Programs',
      priority: 'medium',
      reviewers: ['Sarah Johnson'],
      documents: ['program_outline.pdf', 'budget.xlsx'],
      summary: 'Connecting at-risk youth with positive role models through structured mentorship activities.'
    },
    {
      id: 'app-003',
      applicantName: 'Tim Robinson',
      organization: 'Green Spaces',
      submissionDate: '2024-03-11',
      status: 'under_review',
      score: null,
      amount: 35000,
      projectTitle: 'Urban Tree Planting Initiative',
      category: 'Environmental',
      priority: 'medium',
      reviewers: ['Michael Chen', 'Lisa Wong'],
      documents: ['environmental_plan.pdf', 'budget.xlsx', 'permits.pdf'],
      summary: 'Large-scale tree planting program to improve air quality and urban heat island effects.'
    },
    {
      id: 'app-004',
      applicantName: 'Emma Fisher',
      organization: 'Youth Initiatives',
      submissionDate: '2024-03-09',
      status: 'approved',
      score: 62,
      amount: 20000,
      projectTitle: 'After School Arts Program',
      category: 'Arts & Culture',
      priority: 'high',
      reviewers: ['Sarah Johnson', 'Michael Chen'],
      documents: ['arts_curriculum.pdf', 'budget.xlsx', 'facility_agreement.pdf'],
      summary: 'Providing creative arts education and mentorship for children in low-income areas.'
    },
    {
      id: 'app-005',
      applicantName: 'Sophie Turner',
      organization: 'Local Connect',
      submissionDate: '2024-02-28',
      status: 'approved',
      score: 78,
      amount: 18000,
      projectTitle: 'Digital Literacy Workshops',
      category: 'Education',
      priority: 'medium',
      reviewers: ['Lisa Wong'],
      documents: ['curriculum.pdf', 'budget.xlsx'],
      summary: 'Teaching essential digital skills to seniors and disadvantaged community members.'
    }
  ];

  const analytics = {
    underReview: 46,
    approved: 31,
    declined: 23,
    commonThemes: [
      'Community engagement',
      'Youth programs',
      'Urban renewal'
    ],
    recommendation: 'Prioritize initiatives targeting at-risk youth'
  };

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setApplications(mockApplications);
      setFilteredApplications(mockApplications);
      setIsLoading(false);
    }, 1000);
  }, []);

  useEffect(() => {
    let filtered = applications;

    // Filter by status
    if (activeTab !== 'all') {
      filtered = filtered.filter(app => app.status === activeTab);
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(app => 
        app.applicantName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        app.organization.toLowerCase().includes(searchTerm.toLowerCase()) ||
        app.projectTitle.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Sort applications
    filtered.sort((a, b) => {
      switch(sortBy) {
        case 'latest':
          return new Date(b.submissionDate) - new Date(a.submissionDate);
        case 'oldest':
          return new Date(a.submissionDate) - new Date(b.submissionDate);
        case 'amount_high':
          return b.amount - a.amount;
        case 'amount_low':
          return a.amount - b.amount;
        case 'priority':
          const priorityOrder = { high: 3, medium: 2, low: 1 };
          return priorityOrder[b.priority] - priorityOrder[a.priority];
        default:
          return 0;
      }
    });

    setFilteredApplications(filtered);
  }, [applications, activeTab, searchTerm, sortBy]);

  const getStatusBadge = (status, score) => {
    switch(status) {
      case 'under_review':
        return <Badge variant="outline" className="text-orange-600 border-orange-600">Under Review</Badge>;
      case 'approved':
        return <Badge variant="outline" className="text-green-600 border-green-600">Approved</Badge>;
      case 'declined':
        return <Badge variant="outline" className="text-red-600 border-red-600">Declined</Badge>;
      case 'submitted':
        return <Badge variant="outline" className="text-blue-600 border-blue-600">Submitted</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getScoreBadge = (score) => {
    if (!score) return null;
    
    let colorClass = 'bg-gray-100 text-gray-800';
    if (score >= 70) colorClass = 'bg-green-100 text-green-800';
    else if (score >= 60) colorClass = 'bg-yellow-100 text-yellow-800';
    else colorClass = 'bg-red-100 text-red-800';
    
    return (
      <div className={`px-2 py-1 rounded-full text-sm font-medium ${colorClass}`}>
        {score}
      </div>
    );
  };

  const handleScoreApplication = (applicationId, criteria, score) => {
    setScores(prev => ({
      ...prev,
      [applicationId]: {
        ...prev[applicationId],
        [criteria]: score
      }
    }));
  };

  const submitReview = async (applicationId, decision, finalScore, comments) => {
    try {
      // API call to submit review
      console.log('Submitting review:', { applicationId, decision, finalScore, comments });
      
      // Update local state
      setApplications(prev => prev.map(app => 
        app.id === applicationId 
          ? { ...app, status: decision, score: finalScore }
          : app
      ));
      
      setSelectedApplication(null);
      alert(`Application ${decision} successfully!`);
    } catch (error) {
      alert('Error submitting review');
    }
  };

  const ApplicationCard = ({ application }) => (
    <Card className="mb-4 hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{application.applicantName}</h3>
            <p className="text-gray-600">{application.organization}</p>
          </div>
          <div className="flex items-center space-x-2">
            {getStatusBadge(application.status)}
            {getScoreBadge(application.score)}
          </div>
        </div>
        
        <div className="mb-4">
          <h4 className="font-medium text-gray-900 mb-1">{application.projectTitle}</h4>
          <p className="text-gray-600 text-sm">{application.summary}</p>
        </div>
        
        <div className="flex justify-between items-center text-sm text-gray-500 mb-4">
          <span>Application</span>
          <span>{new Date(application.submissionDate).toLocaleDateString()}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="text-lg font-semibold text-green-600">
            ${application.amount.toLocaleString()}
          </div>
          <div className="flex space-x-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setSelectedApplication(application)}
            >
              <Eye className="h-4 w-4 mr-1" />
              View
            </Button>
            <Button variant="outline" size="sm">
              <Star className="h-4 w-4 mr-1" />
              Rate
            </Button>
            <Button variant="outline" size="sm">
              <MessageSquare className="h-4 w-4 mr-1" />
              Message
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const ApplicationDetailModal = ({ application, onClose }) => {
    const [reviewData, setReviewData] = useState({
      scores: {
        impact: 0,
        feasibility: 0,
        budget: 0,
        sustainability: 0,
        innovation: 0
      },
      comments: '',
      recommendation: ''
    });

    const scoringCriteria = [
      { key: 'impact', label: 'Community Impact', weight: 30 },
      { key: 'feasibility', label: 'Project Feasibility', weight: 25 },
      { key: 'budget', label: 'Budget Appropriateness', weight: 20 },
      { key: 'sustainability', label: 'Long-term Sustainability', weight: 15 },
      { key: 'innovation', label: 'Innovation & Creativity', weight: 10 }
    ];

    const calculateTotalScore = () => {
      return scoringCriteria.reduce((total, criteria) => {
        return total + (reviewData.scores[criteria.key] * criteria.weight / 100);
      }, 0);
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto m-4">
          <div className="p-6 border-b">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">{application.projectTitle}</h2>
              <Button variant="outline" onClick={onClose}>×</Button>
            </div>
            <p className="text-gray-600">{application.applicantName} - {application.organization}</p>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Application Details */}
              <div>
                <h3 className="text-lg font-semibold mb-4">Application Details</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Project Summary</label>
                    <p className="mt-1 text-gray-900">{application.summary}</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Requested Amount</label>
                      <p className="mt-1 text-lg font-semibold text-green-600">
                        ${application.amount.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Category</label>
                      <p className="mt-1 text-gray-900">{application.category}</p>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Submission Date</label>
                    <p className="mt-1 text-gray-900">
                      {new Date(application.submissionDate).toLocaleDateString()}
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Assigned Reviewers</label>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {application.reviewers.map(reviewer => (
                        <Badge key={reviewer} variant="outline">{reviewer}</Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Documents</label>
                    <div className="mt-1 space-y-2">
                      {application.documents.map(doc => (
                        <div key={doc} className="flex items-center justify-between p-2 border rounded">
                          <span className="text-sm">{doc}</span>
                          <Button variant="outline" size="sm">
                            <Download className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Scoring Section */}
              <div>
                <h3 className="text-lg font-semibold mb-4">Review & Scoring</h3>
                
                <div className="space-y-4">
                  {scoringCriteria.map(criteria => (
                    <div key={criteria.key}>
                      <div className="flex justify-between items-center mb-2">
                        <label className="text-sm font-medium text-gray-700">
                          {criteria.label} ({criteria.weight}%)
                        </label>
                        <span className="text-sm text-gray-500">
                          {reviewData.scores[criteria.key]}/10
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="10"
                        value={reviewData.scores[criteria.key]}
                        onChange={(e) => setReviewData(prev => ({
                          ...prev,
                          scores: {
                            ...prev.scores,
                            [criteria.key]: parseInt(e.target.value)
                          }
                        }))}
                        className="w-full"
                      />
                    </div>
                  ))}
                  
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">Total Score:</span>
                      <span className="text-xl font-bold text-blue-600">
                        {calculateTotalScore().toFixed(1)}/10
                      </span>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Review Comments
                    </label>
                    <textarea
                      value={reviewData.comments}
                      onChange={(e) => setReviewData(prev => ({
                        ...prev,
                        comments: e.target.value
                      }))}
                      rows={4}
                      className="w-full p-3 border rounded-lg"
                      placeholder="Provide detailed feedback on the application..."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Recommendation
                    </label>
                    <select
                      value={reviewData.recommendation}
                      onChange={(e) => setReviewData(prev => ({
                        ...prev,
                        recommendation: e.target.value
                      }))}
                      className="w-full p-3 border rounded-lg"
                    >
                      <option value="">Select recommendation...</option>
                      <option value="approve">Approve</option>
                      <option value="approve_with_conditions">Approve with Conditions</option>
                      <option value="request_more_info">Request More Information</option>
                      <option value="decline">Decline</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="mt-6 flex justify-end space-x-3">
              <Button variant="outline" onClick={onClose}>
                Save Draft
              </Button>
              <Button 
                variant="outline"
                className="text-red-600 border-red-600 hover:bg-red-50"
                onClick={() => submitReview(application.id, 'declined', calculateTotalScore(), reviewData.comments)}
              >
                <XCircle className="h-4 w-4 mr-2" />
                Decline
              </Button>
              <Button 
                className="bg-green-600 hover:bg-green-700"
                onClick={() => submitReview(application.id, 'approved', calculateTotalScore(), reviewData.comments)}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Approve
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading applications...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-600 text-white p-6">
        <h1 className="text-2xl font-bold">Community Development Grant</h1>
        <div className="flex items-center space-x-4 mt-2">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>New reports</span>
          </div>
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5" />
            <span>Help</span>
          </div>
          <div className="flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <span>Profile</span>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="flex gap-6">
          {/* Main Content */}
          <div className="flex-1">
            {/* Applications Header */}
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-4">
                <h2 className="text-2xl font-bold">Applications</h2>
                <Badge variant="outline" className="text-lg px-3 py-1">
                  {filteredApplications.length}
                </Badge>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search applications..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 w-64"
                  />
                </div>
                
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-2 border rounded-lg"
                >
                  <option value="latest">Sort by: Latest</option>
                  <option value="oldest">Sort by: Oldest</option>
                  <option value="amount_high">Sort by: Amount (High)</option>
                  <option value="amount_low">Sort by: Amount (Low)</option>
                  <option value="priority">Sort by: Priority</option>
                </select>
              </div>
            </div>

            {/* Status Tabs */}
            <div className="flex space-x-1 mb-6">
              {[
                { key: 'all', label: 'All' },
                { key: 'submitted', label: 'Submitted' },
                { key: 'under_review', label: 'Under Review' },
                { key: 'approved', label: 'Approved' },
                { key: 'declined', label: 'Declined' }
              ].map(tab => (
                <Button
                  key={tab.key}
                  variant={activeTab === tab.key ? "default" : "outline"}
                  onClick={() => setActiveTab(tab.key)}
                  className="px-4 py-2"
                >
                  {tab.label}
                </Button>
              ))}
            </div>

            {/* Applications Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {filteredApplications.map(application => (
                <ApplicationCard key={application.id} application={application} />
              ))}
            </div>

            {filteredApplications.length === 0 && (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No applications found</h3>
                <p className="text-gray-600">Try adjusting your search or filter criteria.</p>
              </div>
            )}
          </div>

          {/* AI Insights Sidebar */}
          <div className="w-80">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Lightbulb className="h-5 w-5 text-yellow-500" />
                  <span>AI Insights</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <h3 className="font-semibold mb-3">Application Analytics</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Under Review</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div className="bg-orange-500 h-2 rounded-full" style={{width: `${analytics.underReview}%`}}></div>
                          </div>
                          <span className="text-sm font-medium">{analytics.underReview}%</span>
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Approved</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div className="bg-green-500 h-2 rounded-full" style={{width: `${analytics.approved}%`}}></div>
                          </div>
                          <span className="text-sm font-medium">{analytics.approved}%</span>
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Declined</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div className="bg-red-500 h-2 rounded-full" style={{width: `${analytics.declined}%`}}></div>
                          </div>
                          <span className="text-sm font-medium">{analytics.declined}%</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-3">Common Themes</h3>
                    <ul className="space-y-2">
                      {analytics.commonThemes.map(theme => (
                        <li key={theme} className="text-sm flex items-center space-x-2">
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                          <span>{theme}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-3">Recommendation</h3>
                    <p className="text-sm text-gray-600">{analytics.recommendation}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Application Detail Modal */}
      {selectedApplication && (
        <ApplicationDetailModal 
          application={selectedApplication} 
          onClose={() => setSelectedApplication(null)} 
        />
      )}
    </div>
  );
};

export default ApplicationReviewWorkflow;

