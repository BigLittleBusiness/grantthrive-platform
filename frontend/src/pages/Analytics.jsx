import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { GrantContext } from '../contexts/GrantContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { 
  TrendingUp, TrendingDown, DollarSign, Users, FileText, Award,
  Calendar, Download, Filter, RefreshCw, Target, Clock, CheckCircle
} from 'lucide-react';

const Analytics = () => {
  const { user } = useContext(AuthContext);
  const { grants, applications, loading } = useContext(GrantContext);
  
  const [timeRange, setTimeRange] = useState('12months');
  const [selectedMetric, setSelectedMetric] = useState('applications');
  const [refreshing, setRefreshing] = useState(false);

  // Calculate key metrics
  const calculateMetrics = () => {
    const totalGrants = grants.length;
    const totalApplications = applications.length;
    const totalGrantValue = grants.reduce((sum, grant) => sum + (parseFloat(grant.amount) || 0), 0);
    const totalRequestedAmount = applications.reduce((sum, app) => sum + (parseFloat(app.requested_amount) || 0), 0);
    
    const approvedApplications = applications.filter(app => app.status === 'approved');
    const totalApprovedAmount = approvedApplications.reduce((sum, app) => sum + (parseFloat(app.requested_amount) || 0), 0);
    
    const successRate = totalApplications > 0 ? (approvedApplications.length / totalApplications * 100) : 0;
    
    const openGrants = grants.filter(grant => grant.status === 'open').length;
    const pendingApplications = applications.filter(app => ['submitted', 'under_review'].includes(app.status)).length;

    return {
      totalGrants,
      totalApplications,
      totalGrantValue,
      totalRequestedAmount,
      totalApprovedAmount,
      successRate,
      openGrants,
      pendingApplications,
      approvedApplications: approvedApplications.length
    };
  };

  const metrics = calculateMetrics();

  // Generate time series data for charts
  const generateTimeSeriesData = () => {
    const months = [];
    const now = new Date();
    
    for (let i = 11; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const monthKey = date.toISOString().slice(0, 7); // YYYY-MM format
      
      const monthApplications = applications.filter(app => 
        app.created_at && app.created_at.startsWith(monthKey)
      );
      
      const monthGrants = grants.filter(grant => 
        grant.created_at && grant.created_at.startsWith(monthKey)
      );

      months.push({
        month: date.toLocaleDateString('en-AU', { month: 'short', year: 'numeric' }),
        applications: monthApplications.length,
        grants: monthGrants.length,
        approved: monthApplications.filter(app => app.status === 'approved').length,
        value: monthApplications.reduce((sum, app) => sum + (parseFloat(app.requested_amount) || 0), 0)
      });
    }
    
    return months;
  };

  // Generate category distribution data
  const generateCategoryData = () => {
    const categoryCount = {};
    grants.forEach(grant => {
      const category = grant.category || 'Other';
      categoryCount[category] = (categoryCount[category] || 0) + 1;
    });

    return Object.entries(categoryCount).map(([category, count]) => ({
      name: category,
      value: count,
      percentage: ((count / grants.length) * 100).toFixed(1)
    }));
  };

  // Generate status distribution data
  const generateStatusData = () => {
    const statusCount = {};
    applications.forEach(app => {
      const status = app.status || 'unknown';
      statusCount[status] = (statusCount[status] || 0) + 1;
    });

    const statusColors = {
      'draft': '#6B7280',
      'submitted': '#3B82F6',
      'under_review': '#F59E0B',
      'approved': '#10B981',
      'rejected': '#EF4444',
      'completed': '#8B5CF6'
    };

    return Object.entries(statusCount).map(([status, count]) => ({
      name: status.replace('_', ' ').toUpperCase(),
      value: count,
      color: statusColors[status] || '#6B7280'
    }));
  };

  const timeSeriesData = generateTimeSeriesData();
  const categoryData = generateCategoryData();
  const statusData = generateStatusData();

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate data refresh
    setTimeout(() => setRefreshing(false), 1000);
  };

  const exportData = () => {
    const data = {
      metrics,
      timeSeriesData,
      categoryData,
      statusData,
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `grantthrive-analytics-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const MetricCard = ({ title, value, icon: Icon, trend, trendValue, color = "blue" }) => (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center">
          <Icon className={`h-8 w-8 text-${color}-600`} />
          <div className="ml-4 flex-1">
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {trend && (
              <div className="flex items-center mt-1">
                {trend === 'up' ? (
                  <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                )}
                <span className={`text-sm ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                  {trendValue}
                </span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const isCouncilUser = user?.role === 'council_admin' || user?.role === 'council_staff';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics & Reporting</h1>
          <p className="text-gray-600 mt-1">
            {isCouncilUser ? 'Monitor grant performance and community impact' : 'Track your application progress'}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" onClick={exportData}>
            <Download className="w-4 h-4 mr-2" />
            Export Data
          </Button>
        </div>
      </div>

      {/* Time Range Selector */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center space-x-4">
            <Label className="text-sm font-medium">Time Range:</Label>
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="3months">Last 3 Months</SelectItem>
                <SelectItem value="6months">Last 6 Months</SelectItem>
                <SelectItem value="12months">Last 12 Months</SelectItem>
                <SelectItem value="24months">Last 24 Months</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Grants"
          value={metrics.totalGrants}
          icon={Award}
          color="blue"
        />
        <MetricCard
          title="Total Applications"
          value={metrics.totalApplications}
          icon={FileText}
          color="green"
        />
        <MetricCard
          title="Success Rate"
          value={formatPercentage(metrics.successRate)}
          icon={Target}
          color="purple"
        />
        <MetricCard
          title="Total Grant Value"
          value={formatCurrency(metrics.totalGrantValue)}
          icon={DollarSign}
          color="yellow"
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Open Grants"
          value={metrics.openGrants}
          icon={Clock}
          color="blue"
        />
        <MetricCard
          title="Pending Applications"
          value={metrics.pendingApplications}
          icon={Users}
          color="yellow"
        />
        <MetricCard
          title="Approved Applications"
          value={metrics.approvedApplications}
          icon={CheckCircle}
          color="green"
        />
      </div>

      {/* Charts Section */}
      <Tabs defaultValue="trends" className="space-y-4">
        <TabsList>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="distribution">Distribution</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="trends" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Applications Over Time */}
            <Card>
              <CardHeader>
                <CardTitle>Applications Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="applications" stroke="#3B82F6" strokeWidth={2} />
                    <Line type="monotone" dataKey="approved" stroke="#10B981" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Grant Value Trends */}
            <Card>
              <CardHeader>
                <CardTitle>Grant Value Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                    <Area type="monotone" dataKey="value" stroke="#8B5CF6" fill="#8B5CF6" fillOpacity={0.6} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="distribution" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Grant Categories */}
            <Card>
              <CardHeader>
                <CardTitle>Grant Categories</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name} (${percentage}%)`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={`hsl(${index * 45}, 70%, 60%)`} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Application Status */}
            <Card>
              <CardHeader>
                <CardTitle>Application Status Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={statusData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Performance Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Application Success Rate</span>
                  <Badge variant="secondary">{formatPercentage(metrics.successRate)}</Badge>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full" 
                    style={{ width: `${metrics.successRate}%` }}
                  ></div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Grant Utilization</span>
                  <Badge variant="secondary">
                    {formatPercentage((metrics.totalApprovedAmount / metrics.totalGrantValue) * 100)}
                  </Badge>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${(metrics.totalApprovedAmount / metrics.totalGrantValue) * 100}%` }}
                  ></div>
                </div>

                <div className="pt-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Requested</span>
                    <span className="text-sm font-medium">{formatCurrency(metrics.totalRequestedAmount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Approved</span>
                    <span className="text-sm font-medium">{formatCurrency(metrics.totalApprovedAmount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Available Funding</span>
                    <span className="text-sm font-medium">{formatCurrency(metrics.totalGrantValue - metrics.totalApprovedAmount)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Top Categories */}
            <Card>
              <CardHeader>
                <CardTitle>Top Grant Categories</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {categoryData.slice(0, 5).map((category, index) => (
                    <div key={category.name} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className={`w-3 h-3 rounded-full mr-3`} style={{ backgroundColor: `hsl(${index * 45}, 70%, 60%)` }}></div>
                        <span className="text-sm font-medium">{category.name}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold">{category.value}</div>
                        <div className="text-xs text-gray-500">{category.percentage}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Key Insights */}
            <Card>
              <CardHeader>
                <CardTitle>Key Insights</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-800">Application Trends</h4>
                  <p className="text-sm text-blue-700 mt-1">
                    Applications have {timeSeriesData.length > 1 && timeSeriesData[timeSeriesData.length - 1].applications > timeSeriesData[timeSeriesData.length - 2].applications ? 'increased' : 'decreased'} 
                    compared to the previous month.
                  </p>
                </div>

                <div className="p-4 bg-green-50 rounded-lg">
                  <h4 className="font-medium text-green-800">Success Rate</h4>
                  <p className="text-sm text-green-700 mt-1">
                    Your current success rate of {formatPercentage(metrics.successRate)} is 
                    {metrics.successRate > 60 ? ' above' : ' below'} the typical benchmark of 60%.
                  </p>
                </div>

                <div className="p-4 bg-yellow-50 rounded-lg">
                  <h4 className="font-medium text-yellow-800">Popular Categories</h4>
                  <p className="text-sm text-yellow-700 mt-1">
                    {categoryData[0]?.name} is the most popular grant category, 
                    representing {categoryData[0]?.percentage}% of all grants.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {metrics.successRate < 50 && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h4 className="font-medium text-red-800">Improve Success Rate</h4>
                    <p className="text-sm text-red-700 mt-1">
                      Consider providing more guidance to applicants or reviewing grant criteria.
                    </p>
                  </div>
                )}

                {metrics.pendingApplications > 10 && (
                  <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                    <h4 className="font-medium text-orange-800">Review Backlog</h4>
                    <p className="text-sm text-orange-700 mt-1">
                      You have {metrics.pendingApplications} pending applications that need review.
                    </p>
                  </div>
                )}

                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-800">Expand Popular Categories</h4>
                  <p className="text-sm text-blue-700 mt-1">
                    Consider creating more grants in {categoryData[0]?.name} due to high demand.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Analytics;

