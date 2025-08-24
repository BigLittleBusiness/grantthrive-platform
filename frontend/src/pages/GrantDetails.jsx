import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Button } from '../components/ui/button.jsx';
import { 
  ArrowLeft,
  Calendar,
  DollarSign,
  Clock,
  MapPin,
  Users,
  FileText,
  Download,
  Share2,
  Heart,
  AlertCircle,
  CheckCircle,
  Phone,
  Mail,
  ExternalLink,
  Facebook,
  Twitter,
  MessageSquare,
  TrendingUp,
  Award,
  Target
} from 'lucide-react';

const GrantDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [isSaved, setIsSaved] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);

  // Enhanced grant data with comprehensive details
  const grant = {
    id: 1,
    title: 'Community Development Grant',
    category: 'Community',
    amount: 10000,
    status: 'Open',
    daysLeft: 22,
    deadline: '17 May 2024',
    deadlineTime: '11:59 pm',
    openDate: '1 April 2024',
    outcomeDate: 'June 2024',
    completionDate: 'June 2025',
    description: 'This Grant aims to support community projects that foster social cohesion, cultural enrichment, and overall community well-being. We encourage innovative approaches that bring people together and create lasting positive impact.',
    longDescription: `The Community Development Grant is designed to strengthen local communities through targeted funding for projects that demonstrate measurable social impact. This program prioritizes initiatives that address community-identified needs and create sustainable, long-term benefits for residents.

    Our funding supports a wide range of community-driven projects including neighborhood improvement initiatives, cultural celebrations, educational programs, and social services that enhance quality of life for all community members.

    Successful applicants will demonstrate strong community support, clear project planning, and the capacity to deliver meaningful outcomes within the specified timeframe.`,
    eligibilityCriteria: [
      'Applicants must be not-for-profit organizations or community groups',
      'Be registered within Mount Isa local government area, or directly benefit Mount Isa residents',
      'Demonstrate community support and engagement',
      'Have appropriate insurance and governance structures',
      'Show capacity to complete the project within the specified timeframe'
    ],
    documentsRequired: [
      'Completed application form',
      'Project plan with timeline and milestones',
      'Detailed budget breakdown',
      'Letters of support from community members',
      'Proof of insurance and registration',
      'Risk management plan'
    ],
    applicationProcess: [
      { stage: 'Application Opens', date: '1 April 2024', status: 'completed' },
      { stage: 'Application Deadline', date: '17 May 2024', status: 'current' },
      { stage: 'Assessment Period', date: 'May - June 2024', status: 'upcoming' },
      { stage: 'Outcome Notification', date: 'June 2024', status: 'upcoming' },
      { stage: 'Project Completion', date: 'June 2025', status: 'upcoming' }
    ],
    contact: {
      email: 'grants@mountisa.qld.gov.au',
      phone: '(07) 4747 3200',
      office: 'Community Services Department',
      hours: 'Monday - Friday, 8:30 AM - 4:30 PM'
    },
    relatedGrants: [
      { id: 2, title: 'Event Support Grant', category: 'Community', amount: 5000 },
      { id: 3, title: 'Cultural Heritage Grant', category: 'Arts', amount: 8000 },
      { id: 4, title: 'Youth Leadership Program', category: 'Education', amount: 12000 }
    ],
    statistics: {
      totalApplicants: 45,
      successRate: 68,
      averageAward: 7500,
      totalFunded: 15,
      communityImpact: '2,500+ residents benefited'
    },
    tags: ['Community Building', 'Social Cohesion', 'Cultural Enrichment', 'Neighborhood Development'],
    location: 'Mount Isa',
    councilArea: 'Mount Isa City Council'
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'current': return 'bg-blue-500';
      case 'upcoming': return 'bg-gray-300';
      default: return 'bg-gray-300';
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Community': 'bg-blue-100 text-blue-800',
      'Arts': 'bg-purple-100 text-purple-800',
      'Sports': 'bg-orange-100 text-orange-800',
      'Environment': 'bg-green-100 text-green-800',
      'Education': 'bg-indigo-100 text-indigo-800',
      'Business': 'bg-yellow-100 text-yellow-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const shareGrant = (platform) => {
    const url = window.location.href;
    const text = `Check out this grant opportunity: ${grant.title}`;
    
    switch (platform) {
      case 'facebook':
        window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`);
        break;
      case 'twitter':
        window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`);
        break;
      case 'email':
        window.location.href = `mailto:?subject=${encodeURIComponent(grant.title)}&body=${encodeURIComponent(text + ' ' + url)}`;
        break;
      default:
        navigator.clipboard.writeText(url);
        alert('Link copied to clipboard!');
    }
    setShowShareModal(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-6">
          {/* Breadcrumb */}
          <nav className="flex items-center space-x-2 text-blue-100 mb-4">
            <button onClick={() => navigate('/')} className="hover:text-white">Home</button>
            <span>›</span>
            <button onClick={() => navigate('/grants')} className="hover:text-white">Grants</button>
            <span>›</span>
            <span className="text-white">{grant.title}</span>
          </nav>

          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <Badge className={getCategoryColor(grant.category)}>
                  {grant.category}
                </Badge>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="text-blue-100">{grant.status}</span>
                </div>
              </div>
              <h1 className="text-3xl font-bold mb-2">{grant.title}</h1>
              <p className="text-blue-100 text-lg">{grant.description}</p>
            </div>
            
            <div className="flex items-center gap-3 ml-6">
              <Button
                variant="outline"
                onClick={() => setIsSaved(!isSaved)}
                className="text-white border-white hover:bg-white hover:text-blue-600"
              >
                <Heart className={`w-4 h-4 mr-2 ${isSaved ? 'fill-current' : ''}`} />
                {isSaved ? 'Saved' : 'Save'}
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowShareModal(true)}
                className="text-white border-white hover:bg-white hover:text-blue-600"
              >
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Grant Overview */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Grant Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <DollarSign className="w-8 h-8 text-green-600 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-green-600">${grant.amount.toLocaleString()}</div>
                    <div className="text-sm text-gray-600">Funding Available</div>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <Clock className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-blue-600">{grant.daysLeft}</div>
                    <div className="text-sm text-gray-600">Days Left</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <Users className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-purple-600">{grant.statistics.totalApplicants}</div>
                    <div className="text-sm text-gray-600">Total Applicants</div>
                  </div>
                </div>

                <div className="prose max-w-none">
                  <h3>About This Grant</h3>
                  <p>{grant.longDescription}</p>
                </div>
              </CardContent>
            </Card>

            {/* Eligibility Criteria */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  Eligibility Criteria
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {grant.eligibilityCriteria.map((criteria, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>{criteria}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Documents Required */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Documents Required
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {grant.documentsRequired.map((doc, index) => (
                    <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <span className="text-sm">{doc}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Application Process Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Application Process
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {grant.applicationProcess.map((step, index) => (
                    <div key={index} className="flex items-center gap-4">
                      <div className={`w-4 h-4 rounded-full ${getStatusColor(step.status)}`}></div>
                      <div className="flex-1">
                        <div className="font-medium">{step.stage}</div>
                        <div className="text-sm text-gray-600">{step.date}</div>
                      </div>
                      {step.status === 'completed' && <CheckCircle className="w-5 h-5 text-green-500" />}
                      {step.status === 'current' && <Clock className="w-5 h-5 text-blue-500" />}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Grant Statistics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Grant Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{grant.statistics.successRate}%</div>
                    <div className="text-sm text-gray-600">Success Rate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">${grant.statistics.averageAward.toLocaleString()}</div>
                    <div className="text-sm text-gray-600">Average Award</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{grant.statistics.totalFunded}</div>
                    <div className="text-sm text-gray-600">Projects Funded</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-orange-600">{grant.statistics.communityImpact}</div>
                    <div className="text-sm text-gray-600">Community Impact</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Key Information */}
            <Card>
              <CardHeader>
                <CardTitle>Key Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">Category</span>
                  <Badge className={getCategoryColor(grant.category)}>{grant.category}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status</span>
                  <span className="font-medium text-green-600">{grant.status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Funding</span>
                  <span className="font-medium">${grant.amount.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Deadline</span>
                  <div className="text-right">
                    <div className="font-medium">{grant.deadline}</div>
                    <div className="text-sm text-gray-500">{grant.deadlineTime}</div>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Location</span>
                  <span className="font-medium">{grant.location}</span>
                </div>
              </CardContent>
            </Card>

            {/* Apply Now */}
            <Card className="border-orange-200 bg-orange-50">
              <CardContent className="pt-6">
                <div className="text-center mb-4">
                  <AlertCircle className="w-8 h-8 text-orange-600 mx-auto mb-2" />
                  <div className="font-semibold text-orange-800">Application Deadline</div>
                  <div className="text-2xl font-bold text-orange-600">{grant.daysLeft} days left</div>
                </div>
                <Button className="w-full bg-orange-500 hover:bg-orange-600 text-white">
                  Apply Now
                </Button>
                <div className="text-center mt-3">
                  <button className="text-sm text-orange-600 hover:underline">
                    Save for later
                  </button>
                </div>
              </CardContent>
            </Card>

            {/* Contact Information */}
            <Card>
              <CardHeader>
                <CardTitle>Contact</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-3">
                  <Mail className="w-4 h-4 text-gray-500" />
                  <a href={`mailto:${grant.contact.email}`} className="text-blue-600 hover:underline">
                    {grant.contact.email}
                  </a>
                </div>
                <div className="flex items-center gap-3">
                  <Phone className="w-4 h-4 text-gray-500" />
                  <a href={`tel:${grant.contact.phone}`} className="text-blue-600 hover:underline">
                    {grant.contact.phone}
                  </a>
                </div>
                <div className="text-sm text-gray-600">
                  <div className="font-medium">{grant.contact.office}</div>
                  <div>{grant.contact.hours}</div>
                </div>
              </CardContent>
            </Card>

            {/* Downloads */}
            <Card>
              <CardHeader>
                <CardTitle>Downloads</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="outline" className="w-full justify-start">
                  <Download className="w-4 h-4 mr-2" />
                  Application Form
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Download className="w-4 h-4 mr-2" />
                  Grant Guidelines
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Download className="w-4 h-4 mr-2" />
                  Budget Template
                </Button>
              </CardContent>
            </Card>

            {/* Related Grants */}
            <Card>
              <CardHeader>
                <CardTitle>Related Grants</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {grant.relatedGrants.map(relatedGrant => (
                  <div key={relatedGrant.id} className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                    <div className="font-medium text-sm">{relatedGrant.title}</div>
                    <div className="flex items-center justify-between mt-1">
                      <Badge className={getCategoryColor(relatedGrant.category)} variant="outline">
                        {relatedGrant.category}
                      </Badge>
                      <span className="text-sm font-medium text-green-600">
                        ${relatedGrant.amount.toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Share this grant</h3>
            <div className="grid grid-cols-2 gap-3">
              <Button onClick={() => shareGrant('facebook')} className="bg-blue-600 hover:bg-blue-700">
                <Facebook className="w-4 h-4 mr-2" />
                Facebook
              </Button>
              <Button onClick={() => shareGrant('twitter')} className="bg-blue-400 hover:bg-blue-500">
                <Twitter className="w-4 h-4 mr-2" />
                Twitter
              </Button>
              <Button onClick={() => shareGrant('email')} variant="outline">
                <Mail className="w-4 h-4 mr-2" />
                Email
              </Button>
              <Button onClick={() => shareGrant('copy')} variant="outline">
                <ExternalLink className="w-4 h-4 mr-2" />
                Copy Link
              </Button>
            </div>
            <Button 
              onClick={() => setShowShareModal(false)} 
              variant="outline" 
              className="w-full mt-4"
            >
              Close
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default GrantDetails;

