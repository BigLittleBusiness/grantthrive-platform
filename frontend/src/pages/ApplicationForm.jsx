import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Button } from '../components/ui/button.jsx';
import { Input } from '../components/ui/input.jsx';
import { 
  ArrowLeft,
  ArrowRight,
  Save,
  Upload,
  X,
  Plus,
  Minus,
  Users,
  FileText,
  DollarSign,
  Calendar,
  CheckCircle,
  AlertCircle,
  Clock,
  User,
  Building,
  Mail,
  Phone,
  MapPin,
  Globe,
  Target,
  TrendingUp
} from 'lucide-react';

const ApplicationForm = () => {
  const { grantId } = useParams();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    // Step 1: Organization Details
    organizationName: '',
    organizationType: '',
    abn: '',
    address: '',
    city: '',
    postcode: '',
    website: '',
    establishedYear: '',
    
    // Step 2: Contact Information
    primaryContactName: '',
    primaryContactTitle: '',
    primaryContactEmail: '',
    primaryContactPhone: '',
    secondaryContactName: '',
    secondaryContactEmail: '',
    
    // Step 3: Project Details
    projectTitle: '',
    projectDescription: '',
    projectCategory: '',
    projectLocation: '',
    projectStartDate: '',
    projectEndDate: '',
    
    // Step 4: Budget
    totalProjectCost: '',
    amountRequested: '',
    budgetItems: [
      { category: '', description: '', amount: '' }
    ],
    otherFunding: '',
    inKindContributions: '',
    
    // Step 5: Supporting Information
    communityNeed: '',
    projectImpact: '',
    sustainability: '',
    riskManagement: '',
    teamExperience: '',
    
    // Step 6: Documents
    uploadedFiles: [],
    
    // Step 7: Declaration
    declarationAccepted: false,
    privacyAccepted: false,
    termsAccepted: false
  });

  const [errors, setErrors] = useState({});
  const [isAutoSaving, setIsAutoSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const [collaborators, setCollaborators] = useState([]);

  const steps = [
    { id: 1, title: 'Organization', icon: Building, description: 'Basic organization information' },
    { id: 2, title: 'Contact Details', icon: User, description: 'Primary and secondary contacts' },
    { id: 3, title: 'Project Details', icon: Target, description: 'Project overview and timeline' },
    { id: 4, title: 'Budget', icon: DollarSign, description: 'Financial breakdown and funding' },
    { id: 5, title: 'Impact & Planning', icon: TrendingUp, description: 'Community impact and sustainability' },
    { id: 6, title: 'Documents', icon: FileText, description: 'Supporting documentation' },
    { id: 7, title: 'Review & Submit', icon: CheckCircle, description: 'Final review and declaration' }
  ];

  // Auto-save functionality
  useEffect(() => {
    const autoSave = setTimeout(() => {
      if (Object.keys(formData).some(key => formData[key] !== '')) {
        setIsAutoSaving(true);
        // Simulate auto-save
        setTimeout(() => {
          setIsAutoSaving(false);
          setLastSaved(new Date());
        }, 1000);
      }
    }, 2000);

    return () => clearTimeout(autoSave);
  }, [formData]);

  const updateFormData = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const addBudgetItem = () => {
    setFormData(prev => ({
      ...prev,
      budgetItems: [...prev.budgetItems, { category: '', description: '', amount: '' }]
    }));
  };

  const removeBudgetItem = (index) => {
    setFormData(prev => ({
      ...prev,
      budgetItems: prev.budgetItems.filter((_, i) => i !== index)
    }));
  };

  const updateBudgetItem = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      budgetItems: prev.budgetItems.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const validateStep = (step) => {
    const newErrors = {};
    
    switch (step) {
      case 1:
        if (!formData.organizationName) newErrors.organizationName = 'Organization name is required';
        if (!formData.organizationType) newErrors.organizationType = 'Organization type is required';
        if (!formData.abn) newErrors.abn = 'ABN is required';
        break;
      case 2:
        if (!formData.primaryContactName) newErrors.primaryContactName = 'Primary contact name is required';
        if (!formData.primaryContactEmail) newErrors.primaryContactEmail = 'Primary contact email is required';
        if (!formData.primaryContactPhone) newErrors.primaryContactPhone = 'Primary contact phone is required';
        break;
      case 3:
        if (!formData.projectTitle) newErrors.projectTitle = 'Project title is required';
        if (!formData.projectDescription) newErrors.projectDescription = 'Project description is required';
        if (!formData.projectCategory) newErrors.projectCategory = 'Project category is required';
        break;
      case 4:
        if (!formData.amountRequested) newErrors.amountRequested = 'Amount requested is required';
        if (!formData.totalProjectCost) newErrors.totalProjectCost = 'Total project cost is required';
        break;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(7, prev + 1));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(1, prev - 1));
  };

  const handleFileUpload = (files) => {
    const newFiles = Array.from(files).map(file => ({
      id: Date.now() + Math.random(),
      name: file.name,
      size: file.size,
      type: file.type,
      file: file
    }));
    
    setFormData(prev => ({
      ...prev,
      uploadedFiles: [...prev.uploadedFiles, ...newFiles]
    }));
  };

  const removeFile = (fileId) => {
    setFormData(prev => ({
      ...prev,
      uploadedFiles: prev.uploadedFiles.filter(file => file.id !== fileId)
    }));
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Organization Name *</label>
              <Input
                value={formData.organizationName}
                onChange={(e) => updateFormData('organizationName', e.target.value)}
                placeholder="Enter your organization name"
                className={errors.organizationName ? 'border-red-500' : ''}
              />
              {errors.organizationName && <p className="text-red-500 text-sm mt-1">{errors.organizationName}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Organization Type *</label>
              <select
                value={formData.organizationType}
                onChange={(e) => updateFormData('organizationType', e.target.value)}
                className={`w-full border rounded-lg px-3 py-2 ${errors.organizationType ? 'border-red-500' : 'border-gray-300'}`}
              >
                <option value="">Select organization type</option>
                <option value="charity">Registered Charity</option>
                <option value="nonprofit">Non-profit Organization</option>
                <option value="community">Community Group</option>
                <option value="school">Educational Institution</option>
                <option value="sports">Sports Club</option>
                <option value="arts">Arts Organization</option>
                <option value="other">Other</option>
              </select>
              {errors.organizationType && <p className="text-red-500 text-sm mt-1">{errors.organizationType}</p>}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">ABN *</label>
                <Input
                  value={formData.abn}
                  onChange={(e) => updateFormData('abn', e.target.value)}
                  placeholder="12 345 678 901"
                  className={errors.abn ? 'border-red-500' : ''}
                />
                {errors.abn && <p className="text-red-500 text-sm mt-1">{errors.abn}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Established Year</label>
                <Input
                  type="number"
                  value={formData.establishedYear}
                  onChange={(e) => updateFormData('establishedYear', e.target.value)}
                  placeholder="2020"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Address</label>
              <Input
                value={formData.address}
                onChange={(e) => updateFormData('address', e.target.value)}
                placeholder="Street address"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">City</label>
                <Input
                  value={formData.city}
                  onChange={(e) => updateFormData('city', e.target.value)}
                  placeholder="Mount Isa"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Postcode</label>
                <Input
                  value={formData.postcode}
                  onChange={(e) => updateFormData('postcode', e.target.value)}
                  placeholder="4825"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Website</label>
              <Input
                value={formData.website}
                onChange={(e) => updateFormData('website', e.target.value)}
                placeholder="https://www.example.com"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-medium text-blue-900 mb-2">Primary Contact</h3>
              <p className="text-sm text-blue-700">This person will be the main point of contact for this application.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Full Name *</label>
                <Input
                  value={formData.primaryContactName}
                  onChange={(e) => updateFormData('primaryContactName', e.target.value)}
                  placeholder="John Smith"
                  className={errors.primaryContactName ? 'border-red-500' : ''}
                />
                {errors.primaryContactName && <p className="text-red-500 text-sm mt-1">{errors.primaryContactName}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Job Title</label>
                <Input
                  value={formData.primaryContactTitle}
                  onChange={(e) => updateFormData('primaryContactTitle', e.target.value)}
                  placeholder="Project Manager"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Email Address *</label>
                <Input
                  type="email"
                  value={formData.primaryContactEmail}
                  onChange={(e) => updateFormData('primaryContactEmail', e.target.value)}
                  placeholder="john@example.com"
                  className={errors.primaryContactEmail ? 'border-red-500' : ''}
                />
                {errors.primaryContactEmail && <p className="text-red-500 text-sm mt-1">{errors.primaryContactEmail}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Phone Number *</label>
                <Input
                  type="tel"
                  value={formData.primaryContactPhone}
                  onChange={(e) => updateFormData('primaryContactPhone', e.target.value)}
                  placeholder="(07) 1234 5678"
                  className={errors.primaryContactPhone ? 'border-red-500' : ''}
                />
                {errors.primaryContactPhone && <p className="text-red-500 text-sm mt-1">{errors.primaryContactPhone}</p>}
              </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-2">Secondary Contact (Optional)</h3>
              <p className="text-sm text-gray-600 mb-4">Provide an alternative contact person for this application.</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Full Name</label>
                  <Input
                    value={formData.secondaryContactName}
                    onChange={(e) => updateFormData('secondaryContactName', e.target.value)}
                    placeholder="Jane Doe"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Email Address</label>
                  <Input
                    type="email"
                    value={formData.secondaryContactEmail}
                    onChange={(e) => updateFormData('secondaryContactEmail', e.target.value)}
                    placeholder="jane@example.com"
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Project Title *</label>
              <Input
                value={formData.projectTitle}
                onChange={(e) => updateFormData('projectTitle', e.target.value)}
                placeholder="Enter a clear, descriptive project title"
                className={errors.projectTitle ? 'border-red-500' : ''}
              />
              {errors.projectTitle && <p className="text-red-500 text-sm mt-1">{errors.projectTitle}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Project Description *</label>
              <textarea
                value={formData.projectDescription}
                onChange={(e) => updateFormData('projectDescription', e.target.value)}
                placeholder="Describe your project, its objectives, and how it will benefit the community..."
                rows={6}
                className={`w-full border rounded-lg px-3 py-2 ${errors.projectDescription ? 'border-red-500' : 'border-gray-300'}`}
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>{formData.projectDescription.length} / 2000 characters</span>
                {errors.projectDescription && <span className="text-red-500">{errors.projectDescription}</span>}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Project Category *</label>
                <select
                  value={formData.projectCategory}
                  onChange={(e) => updateFormData('projectCategory', e.target.value)}
                  className={`w-full border rounded-lg px-3 py-2 ${errors.projectCategory ? 'border-red-500' : 'border-gray-300'}`}
                >
                  <option value="">Select category</option>
                  <option value="community">Community Development</option>
                  <option value="arts">Arts & Culture</option>
                  <option value="sports">Sports & Recreation</option>
                  <option value="environment">Environment</option>
                  <option value="education">Education</option>
                  <option value="health">Health & Wellbeing</option>
                  <option value="youth">Youth Programs</option>
                  <option value="seniors">Seniors Programs</option>
                </select>
                {errors.projectCategory && <p className="text-red-500 text-sm mt-1">{errors.projectCategory}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Project Location</label>
                <Input
                  value={formData.projectLocation}
                  onChange={(e) => updateFormData('projectLocation', e.target.value)}
                  placeholder="Mount Isa"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Project Start Date</label>
                <Input
                  type="date"
                  value={formData.projectStartDate}
                  onChange={(e) => updateFormData('projectStartDate', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Project End Date</label>
                <Input
                  type="date"
                  value={formData.projectEndDate}
                  onChange={(e) => updateFormData('projectEndDate', e.target.value)}
                />
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Total Project Cost *</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                  <Input
                    type="number"
                    value={formData.totalProjectCost}
                    onChange={(e) => updateFormData('totalProjectCost', e.target.value)}
                    placeholder="10000"
                    className={`pl-8 ${errors.totalProjectCost ? 'border-red-500' : ''}`}
                  />
                </div>
                {errors.totalProjectCost && <p className="text-red-500 text-sm mt-1">{errors.totalProjectCost}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Amount Requested *</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                  <Input
                    type="number"
                    value={formData.amountRequested}
                    onChange={(e) => updateFormData('amountRequested', e.target.value)}
                    placeholder="8000"
                    className={`pl-8 ${errors.amountRequested ? 'border-red-500' : ''}`}
                  />
                </div>
                {errors.amountRequested && <p className="text-red-500 text-sm mt-1">{errors.amountRequested}</p>}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium">Budget Breakdown</h3>
                <Button onClick={addBudgetItem} variant="outline" size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Item
                </Button>
              </div>
              
              <div className="space-y-3">
                {formData.budgetItems.map((item, index) => (
                  <div key={index} className="grid grid-cols-1 md:grid-cols-4 gap-3 p-3 border rounded-lg">
                    <div>
                      <Input
                        placeholder="Category"
                        value={item.category}
                        onChange={(e) => updateBudgetItem(index, 'category', e.target.value)}
                      />
                    </div>
                    <div className="md:col-span-2">
                      <Input
                        placeholder="Description"
                        value={item.description}
                        onChange={(e) => updateBudgetItem(index, 'description', e.target.value)}
                      />
                    </div>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                        <Input
                          type="number"
                          placeholder="0"
                          value={item.amount}
                          onChange={(e) => updateBudgetItem(index, 'amount', e.target.value)}
                          className="pl-8"
                        />
                      </div>
                      {formData.budgetItems.length > 1 && (
                        <Button
                          onClick={() => removeBudgetItem(index)}
                          variant="outline"
                          size="sm"
                          className="text-red-500 hover:text-red-700"
                        >
                          <Minus className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Other Funding Sources</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                  <Input
                    type="number"
                    value={formData.otherFunding}
                    onChange={(e) => updateFormData('otherFunding', e.target.value)}
                    placeholder="0"
                    className="pl-8"
                  />
                </div>
                <p className="text-sm text-gray-500 mt-1">Funding from other sources</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">In-Kind Contributions</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                  <Input
                    type="number"
                    value={formData.inKindContributions}
                    onChange={(e) => updateFormData('inKindContributions', e.target.value)}
                    placeholder="0"
                    className="pl-8"
                  />
                </div>
                <p className="text-sm text-gray-500 mt-1">Volunteer time, donated materials, etc.</p>
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Community Need</label>
              <textarea
                value={formData.communityNeed}
                onChange={(e) => updateFormData('communityNeed', e.target.value)}
                placeholder="Describe the community need your project addresses..."
                rows={4}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Expected Impact</label>
              <textarea
                value={formData.projectImpact}
                onChange={(e) => updateFormData('projectImpact', e.target.value)}
                placeholder="Describe the expected outcomes and benefits for the community..."
                rows={4}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Sustainability Plan</label>
              <textarea
                value={formData.sustainability}
                onChange={(e) => updateFormData('sustainability', e.target.value)}
                placeholder="How will the project continue or maintain its impact after completion?"
                rows={4}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Risk Management</label>
              <textarea
                value={formData.riskManagement}
                onChange={(e) => updateFormData('riskManagement', e.target.value)}
                placeholder="Identify potential risks and how you plan to manage them..."
                rows={4}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Team Experience</label>
              <textarea
                value={formData.teamExperience}
                onChange={(e) => updateFormData('teamExperience', e.target.value)}
                placeholder="Describe your team's relevant experience and qualifications..."
                rows={4}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
          </div>
        );

      case 6:
        return (
          <div className="space-y-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-medium text-blue-900 mb-2">Required Documents</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Completed application form (auto-generated)</li>
                <li>• Project plan with timeline</li>
                <li>• Detailed budget breakdown</li>
                <li>• Letters of support</li>
                <li>• Proof of insurance and registration</li>
                <li>• Risk management plan</li>
              </ul>
            </div>

            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Upload Supporting Documents</h3>
              <p className="text-gray-600 mb-4">Drag and drop files here, or browse</p>
              <input
                type="file"
                multiple
                onChange={(e) => handleFileUpload(e.target.files)}
                className="hidden"
                id="file-upload"
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              />
              <Button onClick={() => document.getElementById('file-upload').click()}>
                Browse Files
              </Button>
              <p className="text-sm text-gray-500 mt-2">
                Supported formats: PDF, DOC, DOCX, JPG, PNG (Max 10MB per file)
              </p>
            </div>

            {formData.uploadedFiles.length > 0 && (
              <div>
                <h3 className="font-medium mb-3">Uploaded Files</h3>
                <div className="space-y-2">
                  {formData.uploadedFiles.map(file => (
                    <div key={file.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-gray-500" />
                        <div>
                          <div className="font-medium">{file.name}</div>
                          <div className="text-sm text-gray-500">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </div>
                        </div>
                      </div>
                      <Button
                        onClick={() => removeFile(file.id)}
                        variant="outline"
                        size="sm"
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 7:
        return (
          <div className="space-y-6">
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-medium text-green-900 mb-2">Application Summary</h3>
              <p className="text-sm text-green-700">Please review your application before submitting.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Organization Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div><strong>Name:</strong> {formData.organizationName}</div>
                  <div><strong>Type:</strong> {formData.organizationType}</div>
                  <div><strong>ABN:</strong> {formData.abn}</div>
                  <div><strong>Contact:</strong> {formData.primaryContactName}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Project Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div><strong>Title:</strong> {formData.projectTitle}</div>
                  <div><strong>Category:</strong> {formData.projectCategory}</div>
                  <div><strong>Amount Requested:</strong> ${formData.amountRequested}</div>
                  <div><strong>Total Cost:</strong> ${formData.totalProjectCost}</div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-4">
              <h3 className="font-medium">Declaration</h3>
              
              <div className="space-y-3">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.declarationAccepted}
                    onChange={(e) => updateFormData('declarationAccepted', e.target.checked)}
                    className="mt-1"
                  />
                  <span className="text-sm">
                    I declare that the information provided in this application is true and correct to the best of my knowledge.
                  </span>
                </label>

                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.privacyAccepted}
                    onChange={(e) => updateFormData('privacyAccepted', e.target.checked)}
                    className="mt-1"
                  />
                  <span className="text-sm">
                    I consent to the collection and use of personal information as outlined in the Privacy Policy.
                  </span>
                </label>

                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.termsAccepted}
                    onChange={(e) => updateFormData('termsAccepted', e.target.checked)}
                    className="mt-1"
                  />
                  <span className="text-sm">
                    I agree to the Terms and Conditions of this grant program.
                  </span>
                </label>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const canSubmit = formData.declarationAccepted && formData.privacyAccepted && formData.termsAccepted;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-600 text-white">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => navigate(-1)}
                variant="outline"
                size="sm"
                className="text-white border-white hover:bg-white hover:text-blue-600"
              >
                <ArrowLeft className="w-4 h-4" />
              </Button>
              <div>
                <h1 className="text-2xl font-bold">Community Development Grant</h1>
                <p className="text-blue-100">Application Form</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-blue-100">
                {isAutoSaving ? (
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 animate-spin" />
                    Saving...
                  </div>
                ) : lastSaved ? (
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" />
                    Saved {lastSaved.toLocaleTimeString()}
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              Step {currentStep} of {steps.length}: {steps[currentStep - 1].title}
            </h2>
            <Badge variant="outline">
              {Math.round((currentStep / steps.length) * 100)}% Complete
            </Badge>
          </div>
          
          <div className="flex items-center gap-2 mb-2">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className={`flex-1 h-2 rounded-full ${
                  index + 1 <= currentStep ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              />
            ))}
          </div>
          
          <div className="grid grid-cols-7 gap-2 text-xs text-gray-600">
            {steps.map((step) => (
              <div key={step.id} className="text-center">
                <div className={`font-medium ${step.id === currentStep ? 'text-blue-600' : ''}`}>
                  {step.title}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Form Content */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {React.createElement(steps[currentStep - 1].icon, { className: "w-5 h-5" })}
              {steps[currentStep - 1].title}
            </CardTitle>
            <p className="text-gray-600">{steps[currentStep - 1].description}</p>
          </CardHeader>
          <CardContent>
            {renderStepContent()}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-8">
          <Button
            onClick={prevStep}
            variant="outline"
            disabled={currentStep === 1}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>

          <div className="flex items-center gap-3">
            <Button variant="outline">
              <Save className="w-4 h-4 mr-2" />
              Save Draft
            </Button>
            
            {currentStep < 7 ? (
              <Button onClick={nextStep} className="bg-orange-500 hover:bg-orange-600">
                Next
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            ) : (
              <Button
                disabled={!canSubmit}
                className="bg-green-600 hover:bg-green-700"
              >
                Submit Application
                <CheckCircle className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApplicationForm;

