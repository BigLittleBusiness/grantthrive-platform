import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { CheckCircle, XCircle, Star, TrendingUp, DollarSign, Users } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { 
  generateCompetitiveComparison, 
  getFeaturesByCategory, 
  generateCompetitiveSummary,
  FEATURE_COMPARISON 
} from '../lib/competitiveAnalysis.js'

export default function CompetitiveComparison({ councilSize, features = {} }) {
  const [showAllFeatures, setShowAllFeatures] = useState(false);
  
  const comparison = generateCompetitiveComparison(councilSize, features);
  const summary = generateCompetitiveSummary(councilSize);
  const featureCategories = getFeaturesByCategory();

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const costComparisonData = [
    {
      name: 'Annual Subscription',
      GrantThrive: comparison.grantThrive.annualCost,
      SmartyGrants: comparison.smartyGrants.annualCost
    },
    {
      name: 'First Year Total',
      GrantThrive: comparison.grantThrive.annualCost,
      SmartyGrants: comparison.smartyGrants.firstYearTotal
    }
  ];

  const FeatureIcon = ({ available }) => {
    return available ? (
      <CheckCircle className="h-5 w-5 text-green-600" />
    ) : (
      <XCircle className="h-5 w-5 text-red-400" />
    );
  };

  return (
    <div className="space-y-6">
      {/* Competitive Summary */}
      <Card className="border-2 border-blue-200 bg-blue-50">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Star className="h-6 w-6 text-yellow-500 fill-current" />
            <CardTitle className="text-2xl text-blue-900">{summary.headline}</CardTitle>
            <Star className="h-6 w-6 text-yellow-500 fill-current" />
          </div>
          <CardDescription className="text-lg text-blue-700">
            {summary.subheadline}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {summary.keyPoints.map((point, index) => (
              <div key={index} className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
                <span className="text-sm font-medium">{point}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Cost Overview</TabsTrigger>
          <TabsTrigger value="features">Feature Comparison</TabsTrigger>
          <TabsTrigger value="savings">Savings Analysis</TabsTrigger>
        </TabsList>

        {/* Cost Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* GrantThrive Card */}
            <Card className="border-2 border-green-200">
              <CardHeader className="bg-green-50">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-green-800">GrantThrive</CardTitle>
                  <Badge className="bg-green-600">Recommended</Badge>
                </div>
                <CardDescription>Revolutionary community-centric platform</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {formatCurrency(comparison.grantThrive.annualCost)}
                    </div>
                    <div className="text-sm text-gray-600">per year, all inclusive</div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span>Setup & Training</span>
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        Included
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Ongoing Support</span>
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        Included
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Community Features</span>
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        Available
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Total Features</span>
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        {comparison.grantThrive.features}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* SmartyGrants Card */}
            <Card className="border-2 border-gray-200">
              <CardHeader className="bg-gray-50">
                <CardTitle className="text-gray-800">SmartyGrants</CardTitle>
                <CardDescription>Traditional grant management system</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-gray-600">
                      {formatCurrency(comparison.smartyGrants.annualCost)}
                    </div>
                    <div className="text-sm text-gray-600">per year subscription</div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span>Setup Fee</span>
                      <span className="font-medium text-red-600">
                        +{formatCurrency(comparison.smartyGrants.setupFee)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Training Fee</span>
                      <span className="font-medium text-red-600">
                        +{formatCurrency(comparison.smartyGrants.trainingFee)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Community Features</span>
                      <Badge variant="secondary" className="bg-red-100 text-red-800">
                        Not Available
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Total Features</span>
                      <Badge variant="secondary" className="bg-gray-100 text-gray-800">
                        {comparison.smartyGrants.features}
                      </Badge>
                    </div>
                  </div>

                  <div className="pt-2 border-t">
                    <div className="flex items-center justify-between font-bold">
                      <span>First Year Total</span>
                      <span className="text-red-600">
                        {formatCurrency(comparison.smartyGrants.firstYearTotal)}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Cost Comparison Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Cost Comparison Chart</CardTitle>
              <CardDescription>
                Annual and first-year costs side by side
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={costComparisonData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis tickFormatter={(value) => formatCurrency(value)} />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Bar dataKey="GrantThrive" fill="#10b981" name="GrantThrive" />
                  <Bar dataKey="SmartyGrants" fill="#6b7280" name="SmartyGrants" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Feature Comparison Tab */}
        <TabsContent value="features" className="space-y-6">
          {Object.entries(featureCategories).map(([categoryKey, category]) => (
            <Card key={categoryKey}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {categoryKey === 'community' && <Users className="h-5 w-5 text-blue-600" />}
                  {categoryKey === 'core' && <Star className="h-5 w-5 text-yellow-600" />}
                  {categoryKey === 'advanced' && <TrendingUp className="h-5 w-5 text-purple-600" />}
                  {categoryKey === 'integrations' && <DollarSign className="h-5 w-5 text-green-600" />}
                  {category.title}
                </CardTitle>
                {categoryKey === 'community' && (
                  <CardDescription className="text-blue-600 font-medium">
                    Revolutionary features exclusive to GrantThrive
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 font-medium">Feature</th>
                        <th className="text-center py-2 font-medium">GrantThrive</th>
                        <th className="text-center py-2 font-medium">SmartyGrants</th>
                      </tr>
                    </thead>
                    <tbody>
                      {category.features.map((featureKey) => {
                        const feature = FEATURE_COMPARISON[featureKey];
                        return (
                          <tr key={featureKey} className="border-b">
                            <td className="py-3">
                              <div>
                                <div className="font-medium">
                                  {feature.description}
                                </div>
                              </div>
                            </td>
                            <td className="text-center py-3">
                              <FeatureIcon available={feature.grantThrive} />
                            </td>
                            <td className="text-center py-3">
                              <FeatureIcon available={feature.smartyGrants} />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Savings Analysis Tab */}
        <TabsContent value="savings" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-green-600" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Annual Savings</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(comparison.comparison.annualSavings)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">First Year Savings</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {formatCurrency(comparison.comparison.firstYearSavings)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-2">
                  <Star className="h-5 w-5 text-purple-600" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">3-Year Savings</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {formatCurrency(comparison.comparison.threeYearSavings)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Value Proposition Summary */}
          <Card className="border-2 border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
            <CardHeader>
              <CardTitle className="text-center text-blue-900">
                Why GrantThrive is the Clear Choice
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3 text-green-700">Financial Benefits</h4>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span>{Math.abs(comparison.comparison.savingsPercentage)}% lower annual costs</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span>No setup or training fees</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span>Included ongoing support</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span>Transparent, predictable pricing</span>
                    </li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-3 text-blue-700">Competitive Advantages</h4>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-blue-600" />
                      <span>{comparison.comparison.uniqueFeatures} exclusive community features</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-blue-600" />
                      <span>Revolutionary community engagement</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-blue-600" />
                      <span>Modern, AI-powered platform</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-blue-600" />
                      <span>15+ system integrations</span>
                    </li>
                  </ul>
                </div>
              </div>
              
              <div className="mt-6 text-center">
                <p className="text-lg font-medium text-gray-800 mb-4">
                  {summary.callToAction}
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
                    Schedule Competitive Demo
                  </Button>
                  <Button size="lg" variant="outline">
                    Download Comparison Report
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

