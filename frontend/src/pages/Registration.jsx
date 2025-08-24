import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Button } from '../components/ui/button.jsx';
import { Input } from '../components/ui/input.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { 
  Building, 
  Users, 
  Briefcase, 
  Shield, 
  CheckCircle, 
  AlertCircle,
  Mail,
  Phone,
  MapPin,
  FileText,
  Upload,
  ArrowRight,
  ArrowLeft
} from 'lucide-react';

const Registration = () => {
  const [step, setStep] = useState(1);
  const [userType, setUserType] = useState('');
  const [formData, setFormData] = useState({
    // Personal Information
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    
    // Organization Information
    organizationName: '',
    organizationType: '',
    abn: '',
    address: '',
    website: '',
    
    // Role-specific Information
    position: '',
    department: '',
    yearsExperience: '',
    
    // Verification Documents
    documents: [],
    
    // Council-specific
    councilName: '',
    councilEmail: '',
    supervisorName: '',
    supervisorEmail: ''
  });

  const userTypes = [
    {
      id: 'community_member',
      name: 'Community Member',
      description: 'Individual or community organization seeking grants',
      icon: Users,
      color: 'purple',
      requirements: [
        'Valid email address',
        'Organization details (if applicable)',
        'Instant approval for most applications'
      ],
      verificationLevel: 'Basic'
    },
    {
      id: 'professional_consultant',
      name: 'Professional Consultant',
      description: 'Grant writing professional or consulting service',
      icon: Briefcase,
      color: 'orange',
      requirements: [
        'Professional credentials verification',
        'Business registration documents',
        'Portfolio or experience evidence',
        'Admin review required (2-3 business days)'
      ],
      verificationLevel: 'Enhanced'
    },
    {
      id: 'council_staff',
      name: 'Council Staff Member',
      description: 'Local government employee with grant responsibilities',
      icon: Building,
      color: 'green',
      requirements: [
        'Official government email address required (.gov.au or .govt.nz)',
        'Position and department information',
        'Admin verification (1-2 business days)',
        'Documents may be requested if needed for verification'
      ],
      verificationLevel: 'High Security'
    }
  ];

  // Government email domain validation for Australia and New Zealand
  const validateGovernmentEmail = (email) => {
    const emailLower = email.toLowerCase();
    
    // Australian government domains (.gov.au)
    const australianGovPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.gov\.au$/;
    
    // New Zealand government domains (.govt.nz)
    const newZealandGovPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.govt\.nz$/;
    
    return australianGovPattern.test(emailLower) || newZealandGovPattern.test(emailLower);
  };

  const getEmailDomainExample = () => {
    return 'name@council.gov.au or name@council.govt.nz';
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const renderUserTypeSelection = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Join GrantThrive</h2>
        <p className="text-lg text-gray-600">
          Choose your account type to get started with the appropriate verification process
        </p>
      </div>

      <div className="grid gap-6">
        {userTypes.map((type) => {
          const IconComponent = type.icon;
          return (
            <Card 
              key={type.id}
              className={`cursor-pointer transition-all duration-300 border-2 hover:shadow-lg ${
                userType === type.id 
                  ? `border-${type.color}-500 bg-${type.color}-50` 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setUserType(type.id)}
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-full bg-${type.color}-100`}>
                    <IconComponent className={`w-6 h-6 text-${type.color}-600`} />
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-gray-900">{type.name}</h3>
                      <Badge variant={type.verificationLevel === 'High Security' ? 'destructive' : 
                                   type.verificationLevel === 'Enhanced' ? 'default' : 'secondary'}>
                        {type.verificationLevel}
                      </Badge>
                    </div>
                    
                    <p className="text-gray-600 mb-4">{type.description}</p>
                    
                    <div className="space-y-2">
                      <h4 className="font-medium text-gray-900">Requirements:</h4>
                      <ul className="space-y-1">
                        {type.requirements.map((req, index) => (
                          <li key={index} className="flex items-center gap-2 text-sm text-gray-600">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            {req}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                  
                  {userType === type.id && (
                    <CheckCircle className={`w-6 h-6 text-${type.color}-600`} />
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-900 mb-1">Security Notice</h4>
            <p className="text-sm text-blue-800">
              Government staff accounts require verification by your organization's GrantThrive administrator. 
              Attempting to register with false credentials is prohibited and may result in account suspension.
              Valid government email domains: .gov.au (Australia) and .govt.nz (New Zealand).
            </p>
          </div>
        </div>
      </div>

      {userType && (
        <Button 
          onClick={() => setStep(2)}
          className="w-full bg-blue-600 hover:bg-blue-700"
        >
          Continue with {userTypes.find(t => t.id === userType)?.name}
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      )}
    </div>
  );

  const renderPersonalInformation = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Personal Information</h2>
        <p className="text-gray-600">
          Registering as: <Badge className="ml-2">{userTypes.find(t => t.id === userType)?.name}</Badge>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            First Name *
          </label>
          <Input
            value={formData.firstName}
            onChange={(e) => handleInputChange('firstName', e.target.value)}
            placeholder="Enter your first name"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Last Name *
          </label>
          <Input
            value={formData.lastName}
            onChange={(e) => handleInputChange('lastName', e.target.value)}
            placeholder="Enter your last name"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email Address *
            {userType === 'council_staff' && (
              <span className="text-red-600 text-xs ml-1">(Must be official government email)</span>
            )}
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder={userType === 'council_staff' ? getEmailDomainExample() : 'your.email@example.com'}
              className="pl-10"
              required
            />
          </div>
          {userType === 'council_staff' && formData.email && !validateGovernmentEmail(formData.email) && (
            <div className="flex items-center gap-2 mt-2 text-red-600 text-sm">
              <AlertCircle className="w-4 h-4" />
              Please use your official government email address (.gov.au for Australia or .govt.nz for New Zealand)
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone Number *
          </label>
          <div className="relative">
            <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              type="tel"
              value={formData.phone}
              onChange={(e) => handleInputChange('phone', e.target.value)}
              placeholder="+61 4XX XXX XXX"
              className="pl-10"
              required
            />
          </div>
        </div>
      </div>

      <div className="flex gap-4">
        <Button 
          variant="outline" 
          onClick={() => setStep(1)}
          className="flex-1"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button 
          onClick={() => setStep(3)}
          className="flex-1 bg-blue-600 hover:bg-blue-700"
          disabled={!formData.firstName || !formData.lastName || !formData.email || !formData.phone}
        >
          Continue
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );

  const renderOrganizationInformation = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Organization Information</h2>
        <p className="text-gray-600">
          {userType === 'council_staff' 
            ? 'Verify your council employment details'
            : 'Tell us about your organization'
          }
        </p>
      </div>

      {userType === 'council_staff' ? (
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Council Name *
            </label>
            <Input
              value={formData.councilName}
              onChange={(e) => handleInputChange('councilName', e.target.value)}
              placeholder="e.g., Melbourne City Council"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Position/Job Title *
            </label>
            <Input
              value={formData.position}
              onChange={(e) => handleInputChange('position', e.target.value)}
              placeholder="e.g., Grants Officer, Community Development Manager"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Department *
            </label>
            <Input
              value={formData.department}
              onChange={(e) => handleInputChange('department', e.target.value)}
              placeholder="e.g., Community Services, Economic Development"
              required
            />
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-900 mb-1">Verification Process</h4>
                <p className="text-sm text-blue-800">
                  Your application will be reviewed by the GrantThrive administrator at your organization. 
                  They may contact you directly if additional verification is needed. 
                  Most applications are processed within 1-2 business days.
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Organization Name *
            </label>
            <Input
              value={formData.organizationName}
              onChange={(e) => handleInputChange('organizationName', e.target.value)}
              placeholder="Enter your organization name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Organization Type *
            </label>
            <select 
              className="w-full p-2 border border-gray-300 rounded-md"
              value={formData.organizationType}
              onChange={(e) => handleInputChange('organizationType', e.target.value)}
              required
            >
              <option value="">Select organization type</option>
              <option value="nonprofit">Non-profit Organization</option>
              <option value="community_group">Community Group</option>
              <option value="sports_club">Sports Club</option>
              <option value="arts_organization">Arts Organization</option>
              <option value="business">Business/Enterprise</option>
              <option value="consulting">Consulting Firm</option>
              <option value="individual">Individual</option>
              <option value="other">Other</option>
            </select>
          </div>

          {formData.organizationType !== 'individual' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ABN (if applicable)
              </label>
              <Input
                value={formData.abn}
                onChange={(e) => handleInputChange('abn', e.target.value)}
                placeholder="XX XXX XXX XXX"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Address *
            </label>
            <div className="relative">
              <MapPin className="absolute left-3 top-3 text-gray-400 w-4 h-4" />
              <textarea
                className="w-full pl-10 p-2 border border-gray-300 rounded-md"
                rows="3"
                value={formData.address}
                onChange={(e) => handleInputChange('address', e.target.value)}
                placeholder="Full address including postcode"
                required
              />
            </div>
          </div>

          {userType === 'professional_consultant' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Years of Experience *
              </label>
              <select 
                className="w-full p-2 border border-gray-300 rounded-md"
                value={formData.yearsExperience}
                onChange={(e) => handleInputChange('yearsExperience', e.target.value)}
                required
              >
                <option value="">Select experience level</option>
                <option value="0-2">0-2 years</option>
                <option value="3-5">3-5 years</option>
                <option value="6-10">6-10 years</option>
                <option value="10+">10+ years</option>
              </select>
            </div>
          )}
        </div>
      )}

      <div className="flex gap-4">
        <Button 
          variant="outline" 
          onClick={() => setStep(2)}
          className="flex-1"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button 
          onClick={() => setStep(4)}
          className="flex-1 bg-blue-600 hover:bg-blue-700"
        >
          Continue
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );

  const renderDocumentUpload = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Document Verification</h2>
        <p className="text-gray-600">
          Upload required documents for account verification
        </p>
      </div>

      <div className="space-y-6">
        {userType === 'council_staff' && (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Employee ID or Business Card</h3>
            <p className="text-gray-600 mb-4">
              Upload a photo of your council employee ID or business card
            </p>
            <Button variant="outline">
              <Upload className="w-4 h-4 mr-2" />
              Upload Document
            </Button>
          </div>
        )}

        {userType === 'professional_consultant' && (
          <>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Professional Credentials</h3>
              <p className="text-gray-600 mb-4">
                Upload certificates, qualifications, or professional memberships
              </p>
              <Button variant="outline">
                <Upload className="w-4 h-4 mr-2" />
                Upload Credentials
              </Button>
            </div>

            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <Briefcase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Portfolio or Work Samples</h3>
              <p className="text-gray-600 mb-4">
                Upload examples of successful grant applications or consulting work
              </p>
              <Button variant="outline">
                <Upload className="w-4 h-4 mr-2" />
                Upload Portfolio
              </Button>
            </div>
          </>
        )}

        {userType === 'community_member' && formData.organizationType !== 'individual' && (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <Building className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Organization Documents</h3>
            <p className="text-gray-600 mb-4">
              Upload incorporation certificate, constitution, or registration documents (optional)
            </p>
            <Button variant="outline">
              <Upload className="w-4 h-4 mr-2" />
              Upload Documents
            </Button>
          </div>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-900 mb-1">Document Security</h4>
            <p className="text-sm text-blue-800">
              All uploaded documents are encrypted and stored securely. They are only used for verification purposes 
              and are not shared with third parties.
            </p>
          </div>
        </div>
      </div>

      <div className="flex gap-4">
        <Button 
          variant="outline" 
          onClick={() => setStep(3)}
          className="flex-1"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button 
          onClick={() => setStep(5)}
          className="flex-1 bg-blue-600 hover:bg-blue-700"
        >
          Continue
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );

  const renderSubmission = () => {
    const selectedUserType = userTypes.find(t => t.id === userType);
    
    return (
      <div className="space-y-6">
        <div className="text-center mb-8">
          <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Registration Submitted!</h2>
          <p className="text-gray-600">
            Your application has been received and is being processed
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>What happens next?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {userType === 'community_member' ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span>Account activated immediately</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span>Welcome email sent to {formData.email}</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span>You can start browsing and applying for grants</span>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-yellow-500 text-white flex items-center justify-center text-xs">1</div>
                  <span>Document verification (1-2 business days)</span>
                </div>
                {userType === 'council_staff' && (
                  <div className="flex items-center gap-3">
                    <div className="w-5 h-5 rounded-full bg-yellow-500 text-white flex items-center justify-center text-xs">2</div>
                    <span>Supervisor confirmation via email</span>
                  </div>
                )}
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs">
                    {userType === 'council_staff' ? '3' : '2'}
                  </div>
                  <span>Admin review and approval</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-green-500 text-white flex items-center justify-center text-xs">
                    {userType === 'council_staff' ? '4' : '3'}
                  </div>
                  <span>Account activation email sent</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="font-medium text-gray-900 mb-4">Registration Summary</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Account Type:</span>
              <span className="font-medium">{selectedUserType?.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Name:</span>
              <span className="font-medium">{formData.firstName} {formData.lastName}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Email:</span>
              <span className="font-medium">{formData.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Organization:</span>
              <span className="font-medium">
                {userType === 'council_staff' ? formData.councilName : formData.organizationName}
              </span>
            </div>
          </div>
        </div>

        <Button 
          onClick={() => window.location.href = '/login'}
          className="w-full bg-green-600 hover:bg-green-700"
        >
          {userType === 'community_member' ? 'Login to Your Account' : 'Return to Login'}
        </Button>
      </div>
    );
  };

  const steps = [
    { number: 1, title: 'Account Type', component: renderUserTypeSelection },
    { number: 2, title: 'Personal Info', component: renderPersonalInformation },
    { number: 3, title: 'Organization', component: renderOrganizationInformation },
    { number: 4, title: 'Verification', component: renderDocumentUpload },
    { number: 5, title: 'Complete', component: renderSubmission }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {steps.map((stepItem, index) => (
              <div key={stepItem.number} className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= stepItem.number 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {step > stepItem.number ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : (
                    stepItem.number
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-16 h-1 mx-2 ${
                    step > stepItem.number ? 'bg-blue-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="text-center">
            <h1 className="text-sm font-medium text-gray-600">
              Step {step} of {steps.length}: {steps[step - 1]?.title}
            </h1>
          </div>
        </div>

        {/* Main Content */}
        <Card className="bg-white shadow-xl">
          <CardContent className="p-8">
            {steps[step - 1]?.component()}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Registration;

