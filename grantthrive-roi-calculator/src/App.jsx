import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Checkbox } from '@/components/ui/checkbox.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Calculator, TrendingUp, DollarSign, Clock, CheckCircle, Users, Map, Vote } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import CompetitiveComparison from './components/CompetitiveComparison.jsx'
import { 
  calculateROI, 
  generateROIReport, 
  getCouncilSizeRecommendation, 
  validateInputs,
  DEFAULT_METRICS,
  COUNCIL_SIZES 
} from './lib/roiCalculations.js'
import { downloadROIReport, formatReportForEmail } from './lib/pdfGenerator.js'
import './App.css'

function App() {
  const [inputs, setInputs] = useState({
    applications: 100,
    currentStaffHours: 4.25,
    grantThriveHours: 0.5,
    staffHourlyRate: 40,
    currentTechCosts: 3000,
    currentAdminCosts: 2000,
    techSavings: 3000,
    adminSavings: 1500
  });

  const [councilSize, setCouncilSize] = useState(COUNCIL_SIZES.SMALL);
  const [features, setFeatures] = useState({
    communityVoting: false,
    grantMapping: false
  });

  const [results, setResults] = useState(null);
  const [errors, setErrors] = useState([]);

  // Auto-calculate when inputs change
  useEffect(() => {
    const validationErrors = validateInputs(inputs);
    setErrors(validationErrors);

    if (validationErrors.length === 0) {
      const recommendedSize = getCouncilSizeRecommendation(inputs.applications);
      setCouncilSize(recommendedSize);
      
      const report = generateROIReport(inputs, recommendedSize, features);
      setResults(report);
    }
  }, [inputs, features]);

  // Update inputs when council size changes
  useEffect(() => {
    const defaults = DEFAULT_METRICS[councilSize];
    setInputs(prev => ({
      ...prev,
      ...defaults
    }));
  }, [councilSize]);

  const handleInputChange = (field, value) => {
    setInputs(prev => ({
      ...prev,
      [field]: parseFloat(value) || 0
    }));
  };

  const handleFeatureChange = (feature, checked) => {
    setFeatures(prev => ({
      ...prev,
      [feature]: checked
    }));
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const chartData = results ? [
    {
      name: 'Current Costs',
      value: results.costs.current.totalCurrentCosts,
      color: '#ef4444'
    },
    {
      name: 'GrantThrive Costs',
      value: results.costs.grantThrive.totalAnnualCost,
      color: '#3b82f6'
    }
  ] : [];

  const savingsData = results ? [
    {
      category: 'Staff Time',
      savings: results.benefits.staffTimeSavings,
      color: '#10b981'
    },
    {
      category: 'Technology',
      savings: results.benefits.techSavings,
      color: '#8b5cf6'
    },
    {
      category: 'Administrative',
      savings: results.benefits.adminSavings,
      color: '#f59e0b'
    }
  ] : [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Calculator className="h-10 w-10 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-900">GrantThrive ROI Calculator</h1>
          </div>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Discover how much your council can save with GrantThrive's revolutionary grant management platform
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Panel */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Council Profile
                </CardTitle>
                <CardDescription>
                  Enter your council's current grant management details
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Council Size */}
                <div className="space-y-2">
                  <Label htmlFor="councilSize">Council Size</Label>
                  <Select value={councilSize} onValueChange={setCouncilSize}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={COUNCIL_SIZES.SMALL}>Small (5K-20K population)</SelectItem>
                      <SelectItem value={COUNCIL_SIZES.MEDIUM}>Medium (20K-100K population)</SelectItem>
                      <SelectItem value={COUNCIL_SIZES.LARGE}>Large (100K+ population)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Applications */}
                <div className="space-y-2">
                  <Label htmlFor="applications">Grant Applications per Year</Label>
                  <Input
                    id="applications"
                    type="number"
                    value={inputs.applications}
                    onChange={(e) => handleInputChange('applications', e.target.value)}
                    min="1"
                  />
                </div>

                {/* Staff Hours */}
                <div className="space-y-2">
                  <Label htmlFor="staffHours">Current Hours per Application</Label>
                  <Input
                    id="staffHours"
                    type="number"
                    step="0.25"
                    value={inputs.currentStaffHours}
                    onChange={(e) => handleInputChange('currentStaffHours', e.target.value)}
                    min="0.1"
                  />
                  <p className="text-sm text-gray-500">Average staff time to process one application</p>
                </div>

                {/* Staff Rate */}
                <div className="space-y-2">
                  <Label htmlFor="staffRate">Staff Hourly Rate (AUD)</Label>
                  <Input
                    id="staffRate"
                    type="number"
                    value={inputs.staffHourlyRate}
                    onChange={(e) => handleInputChange('staffHourlyRate', e.target.value)}
                    min="10"
                  />
                  <p className="text-sm text-gray-500">Including benefits and overheads</p>
                </div>

                {/* Technology Costs */}
                <div className="space-y-2">
                  <Label htmlFor="techCosts">Current Technology Costs (AUD/year)</Label>
                  <Input
                    id="techCosts"
                    type="number"
                    value={inputs.currentTechCosts}
                    onChange={(e) => handleInputChange('currentTechCosts', e.target.value)}
                    min="0"
                  />
                </div>

                {/* Admin Costs */}
                <div className="space-y-2">
                  <Label htmlFor="adminCosts">Administrative Costs (AUD/year)</Label>
                  <Input
                    id="adminCosts"
                    type="number"
                    value={inputs.currentAdminCosts}
                    onChange={(e) => handleInputChange('currentAdminCosts', e.target.value)}
                    min="0"
                  />
                  <p className="text-sm text-gray-500">Printing, postage, manual processes</p>
                </div>

                {/* Features */}
                <div className="space-y-4">
                  <Label>Community Engagement Features</Label>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="communityVoting"
                        checked={features.communityVoting}
                        onCheckedChange={(checked) => handleFeatureChange('communityVoting', checked)}
                      />
                      <Label htmlFor="communityVoting" className="flex items-center gap-2">
                        <Vote className="h-4 w-4" />
                        Community Voting System
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="grantMapping"
                        checked={features.grantMapping}
                        onCheckedChange={(checked) => handleFeatureChange('grantMapping', checked)}
                      />
                      <Label htmlFor="grantMapping" className="flex items-center gap-2">
                        <Map className="h-4 w-4" />
                        Interactive Grant Mapping
                      </Label>
                    </div>
                  </div>
                </div>

                {/* Errors */}
                {errors.length > 0 && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <h4 className="text-sm font-medium text-red-800 mb-2">Please fix these issues:</h4>
                    <ul className="text-sm text-red-700 space-y-1">
                      {errors.map((error, index) => (
                        <li key={index}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {results && (
              <Tabs defaultValue="summary" className="space-y-6">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="summary">ROI Summary</TabsTrigger>
                  <TabsTrigger value="breakdown">Cost Breakdown</TabsTrigger>
                  <TabsTrigger value="benefits">Benefits Analysis</TabsTrigger>
                  <TabsTrigger value="competitive">vs SmartyGrants</TabsTrigger>
                </TabsList>

                {/* Summary Tab */}
                <TabsContent value="summary" className="space-y-6">
                  {/* Key Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <Card>
                      <CardContent className="p-6">
                        <div className="flex items-center gap-2">
                          <TrendingUp className="h-5 w-5 text-green-600" />
                          <div>
                            <p className="text-sm font-medium text-gray-600">ROI</p>
                            <p className="text-2xl font-bold text-green-600">
                              {results.financial.roi}%
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="p-6">
                        <div className="flex items-center gap-2">
                          <Clock className="h-5 w-5 text-blue-600" />
                          <div>
                            <p className="text-sm font-medium text-gray-600">Payback</p>
                            <p className="text-2xl font-bold text-blue-600">
                              {results.financial.payback} mo
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="p-6">
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-5 w-5 text-purple-600" />
                          <div>
                            <p className="text-sm font-medium text-gray-600">Annual Savings</p>
                            <p className="text-2xl font-bold text-purple-600">
                              {formatCurrency(results.summary.annualSavings)}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="p-6">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="h-5 w-5 text-orange-600" />
                          <div>
                            <p className="text-sm font-medium text-gray-600">5-Year Value</p>
                            <p className="text-2xl font-bold text-orange-600">
                              {formatCurrency(results.summary.fiveYearValue)}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Cost Comparison Chart */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Annual Cost Comparison</CardTitle>
                      <CardDescription>
                        Your current costs vs GrantThrive investment
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis tickFormatter={(value) => formatCurrency(value)} />
                          <Tooltip formatter={(value) => formatCurrency(value)} />
                          <Bar dataKey="value" fill="#3b82f6" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Value Proposition */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Your GrantThrive Value Proposition</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <h4 className="font-semibold mb-3">Included Features</h4>
                          <div className="space-y-2">
                            {results.features.baseIncluded.map((feature, index) => (
                              <div key={index} className="flex items-center gap-2">
                                <CheckCircle className="h-4 w-4 text-green-600" />
                                <span className="text-sm">{feature}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                        <div>
                          <h4 className="font-semibold mb-3">Community Engagement</h4>
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <Vote className="h-4 w-4 text-blue-600" />
                              <span className="text-sm">Community Voting: </span>
                              <Badge variant={features.communityVoting ? "default" : "secondary"}>
                                {results.features.addOns.communityVoting}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <Map className="h-4 w-4 text-green-600" />
                              <span className="text-sm">Grant Mapping: </span>
                              <Badge variant={features.grantMapping ? "default" : "secondary"}>
                                {results.features.addOns.grantMapping}
                              </Badge>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Breakdown Tab */}
                <TabsContent value="breakdown" className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Current Costs */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Current Annual Costs</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span>Staff Time</span>
                            <span className="font-medium">{formatCurrency(results.costs.current.staffCosts)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Technology</span>
                            <span className="font-medium">{formatCurrency(results.costs.current.techCosts)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Administrative</span>
                            <span className="font-medium">{formatCurrency(results.costs.current.adminCosts)}</span>
                          </div>
                          <hr />
                          <div className="flex justify-between font-bold">
                            <span>Total</span>
                            <span>{formatCurrency(results.costs.current.totalCurrentCosts)}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* GrantThrive Costs */}
                    <Card>
                      <CardHeader>
                        <CardTitle>GrantThrive Annual Costs</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span>Base Platform</span>
                            <span className="font-medium">{formatCurrency(results.costs.grantThrive.basePrice)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Community Features</span>
                            <span className="font-medium">{formatCurrency(results.costs.grantThrive.addOnCosts)}</span>
                          </div>
                          <hr />
                          <div className="flex justify-between font-bold">
                            <span>Total</span>
                            <span>{formatCurrency(results.costs.grantThrive.totalAnnualCost)}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Savings Breakdown */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Annual Savings Breakdown</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={savingsData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ category, savings }) => `${category}: ${formatCurrency(savings)}`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="savings"
                          >
                            {savingsData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value) => formatCurrency(value)} />
                        </PieChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Benefits Tab */}
                <TabsContent value="benefits" className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Time Savings */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Time Efficiency Gains</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div>
                            <p className="text-sm text-gray-600">Hours saved per application</p>
                            <p className="text-2xl font-bold text-blue-600">
                              {results.benefits.hoursSavedPerApplication} hours
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Total annual hours saved</p>
                            <p className="text-2xl font-bold text-green-600">
                              {results.benefits.totalHoursSaved} hours
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Staff time savings value</p>
                            <p className="text-2xl font-bold text-purple-600">
                              {formatCurrency(results.benefits.staffTimeSavings)}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Operational Benefits */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Operational Benefits</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="flex items-center gap-3">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                            <div>
                              <p className="font-medium">75-85% reduction in processing time</p>
                              <p className="text-sm text-gray-600">From 4+ hours to 30 minutes per application</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                            <div>
                              <p className="font-medium">90% reduction in manual errors</p>
                              <p className="text-sm text-gray-600">Automated validation and workflows</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                            <div>
                              <p className="font-medium">60% fewer support queries</p>
                              <p className="text-sm text-gray-600">Self-service portal and clear guidance</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                            <div>
                              <p className="font-medium">Enhanced community engagement</p>
                              <p className="text-sm text-gray-600">Voting and mapping features</p>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Strategic Value */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Strategic Value & Intangible Benefits</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                          <h4 className="font-semibold mb-3 text-blue-600">Community Engagement</h4>
                          <ul className="space-y-2 text-sm">
                            <li>• Increased transparency</li>
                            <li>• Democratic participation</li>
                            <li>• Public accountability</li>
                            <li>• Enhanced reputation</li>
                          </ul>
                        </div>
                        <div>
                          <h4 className="font-semibold mb-3 text-green-600">Staff Satisfaction</h4>
                          <ul className="space-y-2 text-sm">
                            <li>• Reduced manual work</li>
                            <li>• Modern tools</li>
                            <li>• Professional development</li>
                            <li>• Better work-life balance</li>
                          </ul>
                        </div>
                        <div>
                          <h4 className="font-semibold mb-3 text-purple-600">Risk Mitigation</h4>
                          <ul className="space-y-2 text-sm">
                            <li>• Compliance assurance</li>
                            <li>• Error reduction</li>
                            <li>• Security enhancement</li>
                            <li>• Business continuity</li>
                          </ul>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
                
                {/* Competitive Comparison Tab */}
                <TabsContent value="competitive" className="space-y-6">
                  <CompetitiveComparison 
                    councilSize={councilSize} 
                    features={features}
                  />
                </TabsContent>
              </Tabs>
            )}
          </div>
        </div>

        {/* Call to Action */}
        <div className="mt-12 text-center">
          <Card className="max-w-2xl mx-auto">
            <CardContent className="p-8">
              <h3 className="text-2xl font-bold mb-4">Ready to Transform Your Grant Management?</h3>
              <p className="text-gray-600 mb-6">
                Join progressive councils across Australia and New Zealand who are revolutionizing 
                their grant management with GrantThrive's community-centric platform.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
                  Schedule a Demo
                </Button>
                <Button 
                  size="lg" 
                  variant="outline"
                  onClick={() => results && downloadROIReport(results, inputs, councilSize, features)}
                  disabled={!results}
                >
                  Download ROI Report
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default App

