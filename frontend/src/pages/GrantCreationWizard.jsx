import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { 
  ChevronLeft, 
  ChevronRight, 
  Save, 
  Eye, 
  CheckCircle, 
  Circle,
  Lightbulb,
  Calendar,
  DollarSign,
  FileText,
  Users,
  Target,
  Clock,
  MapPin
} from 'lucide-react';

const GrantCreationWizard = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    // Basic Details
    title: '',
    category: '',
    description: '',
    eligibilityCriteria: '',
    requiredDocuments: [],
    
    // Funding & Dates
    totalFunding: '',
    maxApplicationAmount: '',
    minApplicationAmount: '',
    applicationOpenDate: '',
    applicationCloseDate: '',
    assessmentPeriod: '',
    fundingStartDate: '',
    fundingEndDate: '',
    
    // Application Form
    customQuestions: [],
    budgetRequirements: true,
    projectTimeline: true,
    impactMeasurement: true,
    partnershipDetails: false,
    
    // Review & Publish
    reviewCommittee: [],
    scoringCriteria: [],
    autoPublish: false,
    notificationSettings: {
      emailApplicants: true,
      emailCommittee: true,
      publicAnnouncement: false
    }
  });

  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const steps = [
    { id: 1, title: 'Basic Details', icon: FileText },
    { id: 2, title: 'Funding & Dates', icon: Calendar },
    { id: 3, title: 'Application Form', icon: Users },
    { id: 4, title: 'Review & Publish', icon: CheckCircle }
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

  const documentTypes = [
    'Organization Registration',
    'Financial Statements',
    'Project Budget',
    'Insurance Certificate',
    'References',
    'Project Plan',
    'Impact Assessment',
    'Partnership Agreements'
  ];

  const aiSuggestions = {
    1: [
      'Consider adding community impact criteria',
      'Suggested funding range: $5,000-$50,000',
      'Include sustainability requirements',
      'Add partnership opportunities'
    ],
    2: [
      'Allow 4-6 weeks for assessment',
      'Consider quarterly funding cycles',
      'Set realistic project timelines',
      'Include milestone reporting dates'
    ],
    3: [
      'Add project sustainability questions',
      'Include community engagement metrics',
      'Consider partnership requirements',
      'Add innovation criteria'
    ],
    4: [
      'Assign diverse review committee',
      'Set clear scoring criteria',
      'Plan public announcement',
      'Schedule information sessions'
    ]
  };

  const updateFormData = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const validateStep = (step) => {
    const newErrors = {};
    
    switch(step) {
      case 1:
        if (!formData.title) newErrors.title = 'Grant title is required';
        if (!formData.category) newErrors.category = 'Category is required';
        if (!formData.description) newErrors.description = 'Description is required';
        if (!formData.eligibilityCriteria) newErrors.eligibilityCriteria = 'Eligibility criteria is required';
        break;
      case 2:
        if (!formData.totalFunding) newErrors.totalFunding = 'Total funding is required';
        if (!formData.applicationOpenDate) newErrors.applicationOpenDate = 'Open date is required';
        if (!formData.applicationCloseDate) newErrors.applicationCloseDate = 'Close date is required';
        break;
      case 3:
        // Application form validation
        break;
      case 4:
        if (formData.reviewCommittee.length === 0) newErrors.reviewCommittee = 'At least one reviewer is required';
        break;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 4));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const saveDraft = async () => {
    setIsLoading(true);
    try {
      // API call to save draft
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert('Draft saved successfully!');
    } catch (error) {
      alert('Error saving draft');
    } finally {
      setIsLoading(false);
    }
  };

  const publishGrant = async () => {
    if (validateStep(4)) {
      setIsLoading(true);
      try {
        // API call to publish grant
        await new Promise(resolve => setTimeout(resolve, 1500));
        alert('Grant published successfully!');
      } catch (error) {
        alert('Error publishing grant');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const renderStepContent = () => {
    switch(currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Grant Title *</label>
              <Input
                value={formData.title}
                onChange={(e) => updateFormData('title', e.target.value)}
                placeholder="Enter grant program title"
                className={errors.title ? 'border-red-500' : ''}
              />
              {errors.title && <p className="text-red-500 text-sm mt-1">{errors.title}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Category *</label>
              <select
                value={formData.category}
                onChange={(e) => updateFormData('category', e.target.value)}
                className={`w-full p-3 border rounded-lg ${errors.category ? 'border-red-500' : 'border-gray-300'}`}
              >
                <option value="">Select category...</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              {errors.category && <p className="text-red-500 text-sm mt-1">{errors.category}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Description *</label>
              <textarea
                value={formData.description}
                onChange={(e) => updateFormData('description', e.target.value)}
                placeholder="Describe the grant program, its objectives, and expected outcomes..."
                rows={6}
                className={`w-full p-3 border rounded-lg ${errors.description ? 'border-red-500' : 'border-gray-300'}`}
              />
              {errors.description && <p className="text-red-500 text-sm mt-1">{errors.description}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Eligibility Criteria *</label>
              <textarea
                value={formData.eligibilityCriteria}
                onChange={(e) => updateFormData('eligibilityCriteria', e.target.value)}
                placeholder="Who can apply? What are the requirements?"
                rows={4}
                className={`w-full p-3 border rounded-lg ${errors.eligibilityCriteria ? 'border-red-500' : 'border-gray-300'}`}
              />
              {errors.eligibilityCriteria && <p className="text-red-500 text-sm mt-1">{errors.eligibilityCriteria}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Required Documents</label>
              <div className="grid grid-cols-2 gap-3">
                {documentTypes.map(doc => (
                  <label key={doc} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.requiredDocuments.includes(doc)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          updateFormData('requiredDocuments', [...formData.requiredDocuments, doc]);
                        } else {
                          updateFormData('requiredDocuments', formData.requiredDocuments.filter(d => d !== doc));
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm">{doc}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Total Funding Available *</label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    type="number"
                    value={formData.totalFunding}
                    onChange={(e) => updateFormData('totalFunding', e.target.value)}
                    placeholder="100000"
                    className={`pl-10 ${errors.totalFunding ? 'border-red-500' : ''}`}
                  />
                </div>
                {errors.totalFunding && <p className="text-red-500 text-sm mt-1">{errors.totalFunding}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Maximum Application Amount</label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    type="number"
                    value={formData.maxApplicationAmount}
                    onChange={(e) => updateFormData('maxApplicationAmount', e.target.value)}
                    placeholder="50000"
                    className="pl-10"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Minimum Application Amount</label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    type="number"
                    value={formData.minApplicationAmount}
                    onChange={(e) => updateFormData('minApplicationAmount', e.target.value)}
                    placeholder="5000"
                    className="pl-10"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Applications Open Date *</label>
                <Input
                  type="date"
                  value={formData.applicationOpenDate}
                  onChange={(e) => updateFormData('applicationOpenDate', e.target.value)}
                  className={errors.applicationOpenDate ? 'border-red-500' : ''}
                />
                {errors.applicationOpenDate && <p className="text-red-500 text-sm mt-1">{errors.applicationOpenDate}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Applications Close Date *</label>
                <Input
                  type="date"
                  value={formData.applicationCloseDate}
                  onChange={(e) => updateFormData('applicationCloseDate', e.target.value)}
                  className={errors.applicationCloseDate ? 'border-red-500' : ''}
                />
                {errors.applicationCloseDate && <p className="text-red-500 text-sm mt-1">{errors.applicationCloseDate}</p>}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Assessment Period (weeks)</label>
                <Input
                  type="number"
                  value={formData.assessmentPeriod}
                  onChange={(e) => updateFormData('assessmentPeriod', e.target.value)}
                  placeholder="6"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Funding Start Date</label>
                <Input
                  type="date"
                  value={formData.fundingStartDate}
                  onChange={(e) => updateFormData('fundingStartDate', e.target.value)}
                />
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Standard Application Requirements</h3>
              <div className="space-y-3">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={formData.budgetRequirements}
                    onChange={(e) => updateFormData('budgetRequirements', e.target.checked)}
                    className="rounded"
                  />
                  <span>Detailed Budget Breakdown</span>
                </label>
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={formData.projectTimeline}
                    onChange={(e) => updateFormData('projectTimeline', e.target.checked)}
                    className="rounded"
                  />
                  <span>Project Timeline & Milestones</span>
                </label>
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={formData.impactMeasurement}
                    onChange={(e) => updateFormData('impactMeasurement', e.target.checked)}
                    className="rounded"
                  />
                  <span>Impact Measurement Plan</span>
                </label>
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={formData.partnershipDetails}
                    onChange={(e) => updateFormData('partnershipDetails', e.target.checked)}
                    className="rounded"
                  />
                  <span>Partnership & Collaboration Details</span>
                </label>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-4">Custom Questions</h3>
              <p className="text-gray-600 mb-4">Add specific questions relevant to your grant program</p>
              
              {formData.customQuestions.map((question, index) => (
                <div key={index} className="border rounded-lg p-4 mb-3">
                  <div className="flex justify-between items-start mb-2">
                    <Input
                      value={question.question}
                      onChange={(e) => {
                        const updated = [...formData.customQuestions];
                        updated[index].question = e.target.value;
                        updateFormData('customQuestions', updated);
                      }}
                      placeholder="Enter your question"
                      className="flex-1 mr-2"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const updated = formData.customQuestions.filter((_, i) => i !== index);
                        updateFormData('customQuestions', updated);
                      }}
                    >
                      Remove
                    </Button>
                  </div>
                  <select
                    value={question.type}
                    onChange={(e) => {
                      const updated = [...formData.customQuestions];
                      updated[index].type = e.target.value;
                      updateFormData('customQuestions', updated);
                    }}
                    className="w-full p-2 border rounded"
                  >
                    <option value="text">Text Response</option>
                    <option value="textarea">Long Text</option>
                    <option value="number">Number</option>
                    <option value="date">Date</option>
                    <option value="file">File Upload</option>
                  </select>
                </div>
              ))}

              <Button
                variant="outline"
                onClick={() => {
                  updateFormData('customQuestions', [
                    ...formData.customQuestions,
                    { question: '', type: 'text', required: false }
                  ]);
                }}
              >
                Add Custom Question
              </Button>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Review Committee</h3>
              <p className="text-gray-600 mb-4">Assign reviewers for this grant program</p>
              
              {formData.reviewCommittee.map((reviewer, index) => (
                <div key={index} className="border rounded-lg p-4 mb-3">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <Input
                      value={reviewer.name}
                      onChange={(e) => {
                        const updated = [...formData.reviewCommittee];
                        updated[index].name = e.target.value;
                        updateFormData('reviewCommittee', updated);
                      }}
                      placeholder="Reviewer name"
                    />
                    <Input
                      value={reviewer.email}
                      onChange={(e) => {
                        const updated = [...formData.reviewCommittee];
                        updated[index].email = e.target.value;
                        updateFormData('reviewCommittee', updated);
                      }}
                      placeholder="Email address"
                    />
                    <div className="flex space-x-2">
                      <select
                        value={reviewer.role}
                        onChange={(e) => {
                          const updated = [...formData.reviewCommittee];
                          updated[index].role = e.target.value;
                          updateFormData('reviewCommittee', updated);
                        }}
                        className="flex-1 p-2 border rounded"
                      >
                        <option value="reviewer">Reviewer</option>
                        <option value="lead">Lead Reviewer</option>
                        <option value="specialist">Subject Specialist</option>
                      </select>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const updated = formData.reviewCommittee.filter((_, i) => i !== index);
                          updateFormData('reviewCommittee', updated);
                        }}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                </div>
              ))}

              <Button
                variant="outline"
                onClick={() => {
                  updateFormData('reviewCommittee', [
                    ...formData.reviewCommittee,
                    { name: '', email: '', role: 'reviewer' }
                  ]);
                }}
              >
                Add Reviewer
              </Button>
              {errors.reviewCommittee && <p className="text-red-500 text-sm mt-1">{errors.reviewCommittee}</p>}
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-4">Notification Settings</h3>
              <div className="space-y-3">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={formData.notificationSettings.emailApplicants}
                    onChange={(e) => updateFormData('notificationSettings', {
                      ...formData.notificationSettings,
                      emailApplicants: e.target.checked
                    })}
                    className="rounded"
                  />
                  <span>Email notifications to applicants</span>
                </label>
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={formData.notificationSettings.emailCommittee}
                    onChange={(e) => updateFormData('notificationSettings', {
                      ...formData.notificationSettings,
                      emailCommittee: e.target.checked
                    })}
                    className="rounded"
                  />
                  <span>Email notifications to review committee</span>
                </label>
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={formData.notificationSettings.publicAnnouncement}
                    onChange={(e) => updateFormData('notificationSettings', {
                      ...formData.notificationSettings,
                      publicAnnouncement: e.target.checked
                    })}
                    className="rounded"
                  />
                  <span>Public announcement on website</span>
                </label>
              </div>
            </div>

            <div>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={formData.autoPublish}
                  onChange={(e) => updateFormData('autoPublish', e.target.checked)}
                  className="rounded"
                />
                <span className="font-medium">Publish immediately after creation</span>
              </label>
              <p className="text-sm text-gray-600 mt-1">
                If unchecked, grant will be saved as draft for review
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="bg-blue-600 text-white rounded-t-lg p-6">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold">Create New Grant</h1>
            <div className="flex items-center space-x-2">
              <MapPin className="h-5 w-5" />
              <span>Mount Isa Council</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-b-lg shadow-lg">
          {/* Progress Steps */}
          <div className="border-b p-6">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => {
                const Icon = step.icon;
                const isActive = currentStep === step.id;
                const isCompleted = currentStep > step.id;
                
                return (
                  <div key={step.id} className="flex items-center">
                    <div className={`flex items-center space-x-3 ${isActive ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-400'}`}>
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        isActive ? 'bg-blue-600 text-white' : 
                        isCompleted ? 'bg-green-600 text-white' : 
                        'bg-gray-200'
                      }`}>
                        {isCompleted ? <CheckCircle className="h-5 w-5" /> : <Icon className="h-5 w-5" />}
                      </div>
                      <div>
                        <div className="font-medium">{step.title}</div>
                        <div className="text-sm text-gray-500">Step {step.id}</div>
                      </div>
                    </div>
                    {index < steps.length - 1 && (
                      <div className={`w-16 h-0.5 mx-4 ${isCompleted ? 'bg-green-600' : 'bg-gray-200'}`} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex">
            {/* Main Content */}
            <div className="flex-1 p-6">
              {renderStepContent()}
            </div>

            {/* AI Assistant Sidebar */}
            <div className="w-80 border-l bg-gray-50 p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Lightbulb className="h-5 w-5 text-yellow-500" />
                <h3 className="font-semibold">AI Assistant</h3>
              </div>
              
              <div className="space-y-3">
                {aiSuggestions[currentStep]?.map((suggestion, index) => (
                  <div key={index} className="bg-white p-3 rounded-lg border text-sm">
                    • {suggestion}
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-800 mb-2">Quick Stats</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Completion:</span>
                    <span className="font-medium">{Math.round((currentStep / 4) * 100)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Estimated Time:</span>
                    <span className="font-medium">{5 - currentStep} min</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="border-t p-6 flex justify-between items-center">
            <div className="flex space-x-3">
              <Button
                variant="outline"
                onClick={saveDraft}
                disabled={isLoading}
                className="flex items-center space-x-2"
              >
                <Save className="h-4 w-4" />
                <span>Save Draft</span>
              </Button>
              
              <Button
                variant="outline"
                className="flex items-center space-x-2"
              >
                <Eye className="h-4 w-4" />
                <span>Preview</span>
              </Button>
            </div>

            <div className="flex space-x-3">
              {currentStep > 1 && (
                <Button
                  variant="outline"
                  onClick={prevStep}
                  className="flex items-center space-x-2"
                >
                  <ChevronLeft className="h-4 w-4" />
                  <span>Previous</span>
                </Button>
              )}
              
              {currentStep < 4 ? (
                <Button
                  onClick={nextStep}
                  className="flex items-center space-x-2"
                >
                  <span>Continue</span>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  onClick={publishGrant}
                  disabled={isLoading}
                  className="bg-green-600 hover:bg-green-700 flex items-center space-x-2"
                >
                  <CheckCircle className="h-4 w-4" />
                  <span>{formData.autoPublish ? 'Publish Grant' : 'Save for Review'}</span>
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GrantCreationWizard;

