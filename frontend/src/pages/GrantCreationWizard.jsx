import React, { useState } from 'react';
import { ArrowLeft, ArrowRight, Save, Eye, CheckCircle, FileText, Calendar, Settings, Lightbulb, DollarSign, Users, Clock } from 'lucide-react';

const GrantCreationWizard = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    title: '',
    category: '',
    description: '',
    eligibility: '',
    requiredDocs: [],
    fundingAmount: '',
    applicationDeadline: '',
    projectDuration: '',
    reviewProcess: '',
    customQuestions: []
  });

  const steps = [
    { id: 1, title: 'Basic Details', icon: FileText, description: 'Grant program information' },
    { id: 2, title: 'Funding & Dates', icon: Calendar, description: 'Budget and timeline' },
    { id: 3, title: 'Application Form', icon: Settings, description: 'Custom questions' },
    { id: 4, title: 'Review & Publish', icon: CheckCircle, description: 'Final review' }
  ];

  const categories = [
    'Community Development',
    'Youth Programs',
    'Environmental Sustainability',
    'Arts & Culture',
    'Sports & Recreation',
    'Education & Training',
    'Health & Wellbeing',
    'Infrastructure',
    'Economic Development',
    'Emergency Relief'
  ];

  const documentOptions = [
    'Organization Registration',
    'Financial Statements',
    'Project Budget',
    'Insurance Certificate',
    'References',
    'Project Plan',
    'Impact Assessment',
    'Partnership Agreements'
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleDocumentToggle = (doc) => {
    setFormData(prev => ({
      ...prev,
      requiredDocs: prev.requiredDocs.includes(doc)
        ? prev.requiredDocs.filter(d => d !== doc)
        : [...prev.requiredDocs, doc]
    }));
  };

  const nextStep = () => {
    if (currentStep < 4) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-12">
            {/* Main Form Content */}
            <div className="xl:col-span-2 space-y-10">
              <div>
                <label className="block text-lg font-semibold text-gray-800 mb-4">
                  Grant Program Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  placeholder="Enter a clear, descriptive title for your grant program"
                  className="w-full px-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-300 bg-white shadow-sm"
                  style={{ minHeight: '60px' }}
                />
              </div>

              <div>
                <label className="block text-lg font-semibold text-gray-800 mb-4">
                  Category *
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => handleInputChange('category', e.target.value)}
                  className="w-full px-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-300 bg-white shadow-sm"
                  style={{ minHeight: '60px' }}
                >
                  <option value="">Select a category...</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-lg font-semibold text-gray-800 mb-4">
                  Program Description *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Describe the purpose, goals, and expected outcomes of this grant program. Include details about what types of projects will be funded, the impact you hope to achieve, and any specific focus areas or priorities."
                  rows={8}
                  className="w-full px-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-300 bg-white shadow-sm resize-none"
                  style={{ minHeight: '200px' }}
                />
              </div>

              <div>
                <label className="block text-lg font-semibold text-gray-800 mb-4">
                  Eligibility Criteria *
                </label>
                <textarea
                  value={formData.eligibility}
                  onChange={(e) => handleInputChange('eligibility', e.target.value)}
                  placeholder="Specify who can apply for this grant. Include details about organization types, geographic requirements, project criteria, minimum/maximum funding amounts, and any other qualification requirements."
                  rows={6}
                  className="w-full px-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-300 bg-white shadow-sm resize-none"
                  style={{ minHeight: '160px' }}
                />
              </div>

              <div>
                <label className="block text-lg font-semibold text-gray-800 mb-6">
                  Required Documents
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {documentOptions.map(doc => (
                    <label key={doc} className="flex items-center p-5 border-2 border-gray-200 rounded-xl hover:bg-blue-50 hover:border-blue-300 cursor-pointer transition-all duration-300 bg-white shadow-sm">
                      <input
                        type="checkbox"
                        checked={formData.requiredDocs.includes(doc)}
                        onChange={() => handleDocumentToggle(doc)}
                        className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-2 border-gray-300 rounded mr-4"
                      />
                      <span className="text-base font-medium text-gray-700">{doc}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* AI Assistant Sidebar */}
            <div className="xl:col-span-1">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-200 rounded-xl p-8 shadow-lg sticky top-8">
                <div className="flex items-center mb-6">
                  <div className="bg-blue-600 p-3 rounded-lg mr-4">
                    <Lightbulb className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-blue-900">AI Assistant</h3>
                </div>
                <div className="space-y-4">
                  <div className="bg-white p-4 rounded-lg border border-blue-200 shadow-sm">
                    <p className="text-sm font-medium text-blue-800">💡 Consider adding community impact criteria to attract high-quality applications</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-blue-200 shadow-sm">
                    <p className="text-sm font-medium text-blue-800">💰 Suggested funding range: $5,000-$50,000 for community development grants</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-blue-200 shadow-sm">
                    <p className="text-sm font-medium text-blue-800">🌱 Include sustainability requirements to ensure long-term project success</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-blue-200 shadow-sm">
                    <p className="text-sm font-medium text-blue-800">🤝 Add partnership opportunities to encourage collaboration</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-blue-200 shadow-sm">
                    <p className="text-sm font-medium text-blue-800">📅 Consider multi-year project support for larger initiatives</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-12">
            {/* Main Form Content */}
            <div className="xl:col-span-2 space-y-10">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div>
                  <label className="block text-lg font-semibold text-gray-800 mb-4">
                    Total Funding Available *
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-4 top-4 h-6 w-6 text-gray-500" />
                    <input
                      type="number"
                      value={formData.fundingAmount}
                      onChange={(e) => handleInputChange('fundingAmount', e.target.value)}
                      placeholder="100,000"
                      className="w-full pl-14 pr-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-300 bg-white shadow-sm"
                      style={{ minHeight: '60px' }}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-lg font-semibold text-gray-800 mb-4">
                    Application Deadline *
                  </label>
                  <div className="relative">
                    <Calendar className="absolute left-4 top-4 h-6 w-6 text-gray-500" />
                    <input
                      type="date"
                      value={formData.applicationDeadline}
                      onChange={(e) => handleInputChange('applicationDeadline', e.target.value)}
                      className="w-full pl-14 pr-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-300 bg-white shadow-sm"
                      style={{ minHeight: '60px' }}
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-lg font-semibold text-gray-800 mb-4">
                  Project Duration
                </label>
                <div className="relative">
                  <Clock className="absolute left-4 top-4 h-6 w-6 text-gray-500" />
                  <select
                    value={formData.projectDuration}
                    onChange={(e) => handleInputChange('projectDuration', e.target.value)}
                    className="w-full pl-14 pr-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-300 bg-white shadow-sm"
                    style={{ minHeight: '60px' }}
                  >
                    <option value="">Select project duration...</option>
                    <option value="3-months">3 Months</option>
                    <option value="6-months">6 Months</option>
                    <option value="12-months">12 Months</option>
                    <option value="18-months">18 Months</option>
                    <option value="24-months">24 Months</option>
                    <option value="ongoing">Ongoing</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-lg font-semibold text-gray-800 mb-4">
                  Review Process
                </label>
                <textarea
                  value={formData.reviewProcess}
                  onChange={(e) => handleInputChange('reviewProcess', e.target.value)}
                  placeholder="Describe how applications will be reviewed and evaluated. Include details about the review committee, scoring criteria, timeline for decisions, and any interview or presentation requirements."
                  rows={6}
                  className="w-full px-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-300 bg-white shadow-sm resize-none"
                  style={{ minHeight: '160px' }}
                />
              </div>
            </div>

            {/* Timeline Suggestions Sidebar */}
            <div className="xl:col-span-1">
              <div className="bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-200 rounded-xl p-8 shadow-lg sticky top-8">
                <div className="flex items-center mb-6">
                  <div className="bg-green-600 p-3 rounded-lg mr-4">
                    <Calendar className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-green-900">Timeline Suggestions</h3>
                </div>
                <div className="space-y-4">
                  <div className="bg-white p-4 rounded-lg border border-green-200 shadow-sm">
                    <p className="text-sm font-medium text-green-800">📅 Allow 4-6 weeks for application period to ensure quality submissions</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-green-200 shadow-sm">
                    <p className="text-sm font-medium text-green-800">⏱️ Schedule 2-3 weeks for thorough review process</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-green-200 shadow-sm">
                    <p className="text-sm font-medium text-green-800">📢 Plan announcement 1 week after review completion</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-green-200 shadow-sm">
                    <p className="text-sm font-medium text-green-800">🔄 Consider quarterly application cycles for ongoing programs</p>
                  </div>
                </div>

                <div className="mt-8 bg-white border-2 border-green-200 rounded-lg p-6">
                  <h4 className="text-lg font-bold text-green-900 mb-4">Funding Distribution</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                      <span className="text-sm font-medium text-green-800">Individual Grant Range</span>
                      <span className="text-sm font-bold text-green-900">$5,000 - $25,000</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                      <span className="text-sm font-medium text-green-800">Expected Applications</span>
                      <span className="text-sm font-bold text-green-900">15-20</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                      <span className="text-sm font-medium text-green-800">Success Rate</span>
                      <span className="text-sm font-bold text-green-900">60-70%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="text-center space-y-12">
            <div>
              <h3 className="text-3xl font-bold text-gray-900 mb-4">Custom Application Questions</h3>
              <p className="text-xl text-gray-600">Add specific questions to gather the information you need from applicants</p>
            </div>
            
            <div className="bg-gradient-to-br from-yellow-50 to-orange-100 border-2 border-yellow-300 rounded-xl p-12 max-w-2xl mx-auto shadow-lg">
              <div className="bg-yellow-500 p-4 rounded-xl mx-auto w-fit mb-6">
                <Settings className="h-12 w-12 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-yellow-900 mb-4">Application Form Builder</h3>
              <p className="text-lg text-yellow-800 mb-8">This advanced feature allows you to create custom questions for your grant application form, including multiple choice, text responses, file uploads, and conditional logic.</p>
              <button className="bg-yellow-600 hover:bg-yellow-700 text-white px-8 py-4 rounded-xl transition-all duration-300 font-semibold text-lg shadow-lg">
                Launch Form Builder
              </button>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-12">
            <div className="text-center">
              <h3 className="text-3xl font-bold text-gray-900 mb-4">Review & Publish</h3>
              <p className="text-xl text-gray-600">Review your grant program details before publishing</p>
            </div>

            <div className="bg-white border-2 border-gray-200 rounded-xl p-8 shadow-lg">
              <h4 className="text-2xl font-bold text-gray-900 mb-6">Grant Program Summary</h4>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <h5 className="text-lg font-bold text-gray-800 mb-4">Basic Information</h5>
                  <div className="space-y-3">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium text-gray-600">Title:</span>
                      <p className="text-base font-semibold text-gray-900">{formData.title || 'Not specified'}</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium text-gray-600">Category:</span>
                      <p className="text-base font-semibold text-gray-900">{formData.category || 'Not specified'}</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium text-gray-600">Funding:</span>
                      <p className="text-base font-semibold text-gray-900">${formData.fundingAmount || '0'}</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium text-gray-600">Deadline:</span>
                      <p className="text-base font-semibold text-gray-900">{formData.applicationDeadline || 'Not specified'}</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <h5 className="text-lg font-bold text-gray-800 mb-4">Requirements</h5>
                  <div className="space-y-3">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium text-gray-600">Required Documents:</span>
                      <p className="text-base font-semibold text-gray-900">{formData.requiredDocs.length} selected</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium text-gray-600">Duration:</span>
                      <p className="text-base font-semibold text-gray-900">{formData.projectDuration || 'Not specified'}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-300 rounded-xl p-12 text-center shadow-lg">
              <div className="bg-blue-600 p-4 rounded-xl mx-auto w-fit mb-6">
                <CheckCircle className="h-12 w-12 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-blue-900 mb-4">Ready to Publish</h3>
              <p className="text-lg text-blue-800 mb-8">Your grant program is ready to be published and made available to applicants in the community.</p>
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-12 py-4 rounded-xl transition-all duration-300 font-bold text-lg shadow-lg">
                Publish Grant Program
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Professional Navigation Header */}
      <div className="bg-white border-b-2 border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center">
              <button className="flex items-center text-gray-700 hover:text-blue-600 transition-colors duration-300 font-medium">
                <ArrowLeft className="h-6 w-6 mr-3" />
                <span className="text-lg">Back to Dashboard</span>
              </button>
            </div>
            <div className="flex items-center space-x-6">
              <button className="flex items-center px-6 py-3 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all duration-300 font-medium">
                <Save className="h-5 w-5 mr-2" />
                Save Draft
              </button>
              <button className="flex items-center px-6 py-3 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all duration-300 font-medium">
                <Eye className="h-5 w-5 mr-2" />
                Preview
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-12">
        {/* Professional Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">Create New Grant Program</h1>
          <p className="text-xl text-gray-600 font-medium">Mount Isa Council</p>
        </div>

        {/* Professional Progress Steps */}
        <div className="mb-16">
          <div className="flex items-center justify-between max-w-4xl mx-auto">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className={`flex flex-col items-center ${currentStep >= step.id ? 'text-blue-600' : 'text-gray-400'}`}>
                  <div className={`flex items-center justify-center w-16 h-16 rounded-full border-3 transition-all duration-300 ${
                    currentStep >= step.id 
                      ? 'bg-blue-600 border-blue-600 text-white shadow-lg' 
                      : 'bg-white border-gray-300 text-gray-400'
                  }`}>
                    <step.icon className="h-8 w-8" />
                  </div>
                  <div className="mt-4 text-center">
                    <p className={`text-sm font-bold ${
                      currentStep >= step.id ? 'text-blue-600' : 'text-gray-500'
                    }`}>
                      Step {step.id}
                    </p>
                    <p className={`text-base font-semibold ${
                      currentStep >= step.id ? 'text-gray-900' : 'text-gray-500'
                    }`}>
                      {step.title}
                    </p>
                    <p className={`text-sm ${
                      currentStep >= step.id ? 'text-gray-600' : 'text-gray-400'
                    }`}>
                      {step.description}
                    </p>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div className={`flex-1 h-1 mx-8 rounded-full transition-all duration-300 ${
                    currentStep > step.id ? 'bg-blue-600' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Professional Step Content */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-12 mb-12">
          {renderStepContent()}
        </div>

        {/* Professional Navigation */}
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <button
            onClick={prevStep}
            disabled={currentStep === 1}
            className={`flex items-center px-8 py-4 rounded-xl font-bold text-lg transition-all duration-300 ${
              currentStep === 1
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gray-300 text-gray-700 hover:bg-gray-400 shadow-lg'
            }`}
          >
            <ArrowLeft className="h-5 w-5 mr-3" />
            Previous
          </button>

          <div className="flex items-center space-x-4">
            <span className="text-lg font-medium text-gray-600">
              Step {currentStep} of {steps.length}
            </span>
            <div className="w-48 bg-gray-300 rounded-full h-3">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${(currentStep / steps.length) * 100}%` }}
              />
            </div>
          </div>

          <button
            onClick={nextStep}
            disabled={currentStep === 4}
            className={`flex items-center px-8 py-4 rounded-xl font-bold text-lg transition-all duration-300 ${
              currentStep === 4
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg'
            }`}
          >
            Next
            <ArrowRight className="h-5 w-5 ml-3" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default GrantCreationWizard;

