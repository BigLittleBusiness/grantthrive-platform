import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Progress } from './components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from './components/ui/avatar';
import { 
  LayoutDashboard, 
  Users, 
  Database, 
  Settings, 
  BarChart3, 
  MessageSquare, 
  Shield, 
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Activity,
  Server,
  Globe,
  Bell,
  Search,
  Filter,
  Download,
  RefreshCw,
  Eye,
  Edit,
  Trash2,
  Plus,
  MoreHorizontal,
  MapPin,
  FileText,
  Zap,
  Target,
  Calendar,
  Mail,
  Phone,
  Building,
  CreditCard,
  UserCheck,
  AlertCircle,
  Info
} from 'lucide-react';
import './App.css';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Sample data for the dashboard
  const dashboardStats = {
    totalUsers: 1247,
    activeCouncils: 89,
    monthlyRevenue: 156780,
    grantsProcessed: 2341,
    systemUptime: 99.97,
    dataFreshness: 'Updated 2 hours ago'
  };

  const recentAlerts = [
    { id: 1, type: 'warning', message: 'High API usage detected for Xero integration', time: '5 min ago' },
    { id: 2, type: 'success', message: 'Daily grant data scraping completed successfully', time: '2 hours ago' },
    { id: 3, type: 'info', message: 'New council registration: Ballarat City Council', time: '4 hours ago' },
    { id: 4, type: 'error', message: 'Failed to sync data with QuickBooks for 2 accounts', time: '6 hours ago' }
  ];

  const recentUsers = [
    { id: 1, name: 'Sarah Johnson', email: 'sarah.j@melbourne.vic.gov.au', council: 'Melbourne City Council', status: 'Active', lastLogin: '2 hours ago' },
    { id: 2, name: 'Michael Chen', email: 'm.chen@brisbane.qld.gov.au', council: 'Brisbane City Council', status: 'Active', lastLogin: '1 day ago' },
    { id: 3, name: 'Emma Wilson', email: 'e.wilson@adelaide.sa.gov.au', council: 'Adelaide City Council', status: 'Pending', lastLogin: 'Never' },
    { id: 4, name: 'David Brown', email: 'd.brown@perth.wa.gov.au', council: 'Perth City Council', status: 'Active', lastLogin: '3 hours ago' }
  ];

  const systemMetrics = [
    { name: 'API Requests', value: '2.4M', change: '+12%', trend: 'up' },
    { name: 'Database Queries', value: '847K', change: '+8%', trend: 'up' },
    { name: 'Error Rate', value: '0.02%', change: '-15%', trend: 'down' },
    { name: 'Avg Response Time', value: '245ms', change: '-5%', trend: 'down' }
  ];

  const sidebarItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'users', label: 'User Management', icon: Users },
    { id: 'data', label: 'Data Pipeline', icon: Database },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'support', label: 'Support', icon: MessageSquare },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'billing', label: 'Billing', icon: DollarSign },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  const getAlertIcon = (type) => {
    switch (type) {
      case 'error': return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'success': return <CheckCircle className="w-4 h-4 text-green-500" />;
      default: return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      'Active': 'bg-green-100 text-green-800',
      'Pending': 'bg-yellow-100 text-yellow-800',
      'Inactive': 'bg-gray-100 text-gray-800'
    };
    return variants[status] || variants['Inactive'];
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className={`bg-white shadow-lg transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-64'}`}>
        <div className="p-4 border-b">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <LayoutDashboard className="w-6 h-6 text-white" />
            </div>
            {!sidebarCollapsed && (
              <div>
                <h1 className="text-xl font-bold text-gray-900">GrantThrive</h1>
                <p className="text-sm text-gray-600">Admin Dashboard</p>
              </div>
            )}
          </div>
        </div>

        <nav className="mt-6">
          {sidebarItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center px-4 py-3 text-left hover:bg-blue-50 transition-colors ${
                  activeTab === item.id ? 'bg-blue-50 border-r-2 border-blue-600 text-blue-600' : 'text-gray-700'
                }`}
              >
                <Icon className="w-5 h-5" />
                {!sidebarCollapsed && <span className="ml-3">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        <div className="absolute bottom-4 left-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          >
            <MoreHorizontal className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {sidebarItems.find(item => item.id === activeTab)?.label || 'Dashboard'}
              </h2>
              <p className="text-gray-600">Manage your GrantThrive platform</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input placeholder="Search..." className="pl-10 w-64" />
              </div>
              
              <Button variant="outline" size="sm">
                <Bell className="w-4 h-4 mr-2" />
                Alerts
                <Badge variant="destructive" className="ml-2">3</Badge>
              </Button>
              
              <Avatar>
                <AvatarImage src="/api/placeholder/32/32" />
                <AvatarFallback>AD</AvatarFallback>
              </Avatar>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <main className="p-6 overflow-y-auto h-full">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Total Users</p>
                        <p className="text-3xl font-bold text-gray-900">{dashboardStats.totalUsers.toLocaleString()}</p>
                        <p className="text-sm text-green-600 flex items-center mt-1">
                          <TrendingUp className="w-4 h-4 mr-1" />
                          +12% from last month
                        </p>
                      </div>
                      <Users className="w-8 h-8 text-blue-600" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Active Councils</p>
                        <p className="text-3xl font-bold text-gray-900">{dashboardStats.activeCouncils}</p>
                        <p className="text-sm text-green-600 flex items-center mt-1">
                          <TrendingUp className="w-4 h-4 mr-1" />
                          +8% from last month
                        </p>
                      </div>
                      <Building className="w-8 h-8 text-green-600" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Monthly Revenue</p>
                        <p className="text-3xl font-bold text-gray-900">${dashboardStats.monthlyRevenue.toLocaleString()}</p>
                        <p className="text-sm text-green-600 flex items-center mt-1">
                          <TrendingUp className="w-4 h-4 mr-1" />
                          +15% from last month
                        </p>
                      </div>
                      <DollarSign className="w-8 h-8 text-purple-600" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Grants Processed</p>
                        <p className="text-3xl font-bold text-gray-900">{dashboardStats.grantsProcessed.toLocaleString()}</p>
                        <p className="text-sm text-green-600 flex items-center mt-1">
                          <TrendingUp className="w-4 h-4 mr-1" />
                          +23% from last month
                        </p>
                      </div>
                      <FileText className="w-8 h-8 text-orange-600" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* System Health & Alerts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Activity className="w-5 h-5 mr-2" />
                      System Health
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">System Uptime</span>
                        <span className="text-sm text-green-600">{dashboardStats.systemUptime}%</span>
                      </div>
                      <Progress value={dashboardStats.systemUptime} className="h-2" />
                      
                      <div className="grid grid-cols-2 gap-4 mt-4">
                        {systemMetrics.map((metric, index) => (
                          <div key={index} className="text-center p-3 bg-gray-50 rounded-lg">
                            <p className="text-xs text-gray-600">{metric.name}</p>
                            <p className="text-lg font-semibold">{metric.value}</p>
                            <p className={`text-xs flex items-center justify-center ${
                              metric.trend === 'up' ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {metric.trend === 'up' ? 
                                <TrendingUp className="w-3 h-3 mr-1" /> : 
                                <TrendingDown className="w-3 h-3 mr-1" />
                              }
                              {metric.change}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <div className="flex items-center">
                        <Bell className="w-5 h-5 mr-2" />
                        Recent Alerts
                      </div>
                      <Button variant="outline" size="sm">
                        View All
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {recentAlerts.map((alert) => (
                        <div key={alert.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                          {getAlertIcon(alert.type)}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-gray-900">{alert.message}</p>
                            <p className="text-xs text-gray-500">{alert.time}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Recent Activity */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <div className="flex items-center">
                        <Users className="w-5 h-5 mr-2" />
                        Recent Users
                      </div>
                      <Button variant="outline" size="sm">
                        <Plus className="w-4 h-4 mr-2" />
                        Add User
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {recentUsers.map((user) => (
                        <div key={user.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <Avatar className="w-8 h-8">
                              <AvatarFallback>{user.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="text-sm font-medium">{user.name}</p>
                              <p className="text-xs text-gray-600">{user.council}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <Badge className={getStatusBadge(user.status)}>
                              {user.status}
                            </Badge>
                            <p className="text-xs text-gray-500 mt-1">{user.lastLogin}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Database className="w-5 h-5 mr-2" />
                      Data Pipeline Status
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <div>
                            <p className="text-sm font-medium">Grant Data Scraper</p>
                            <p className="text-xs text-gray-600">Last run: 2 hours ago</p>
                          </div>
                        </div>
                        <Badge className="bg-green-100 text-green-800">Active</Badge>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <Clock className="w-5 h-5 text-blue-600" />
                          <div>
                            <p className="text-sm font-medium">Data Processing</p>
                            <p className="text-xs text-gray-600">Processing 1,247 records</p>
                          </div>
                        </div>
                        <Badge className="bg-blue-100 text-blue-800">Running</Badge>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <RefreshCw className="w-5 h-5 text-gray-600" />
                          <div>
                            <p className="text-sm font-medium">API Integrations</p>
                            <p className="text-xs text-gray-600">8/10 services healthy</p>
                          </div>
                        </div>
                        <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>
                      </div>
                    </div>

                    <div className="mt-4 pt-4 border-t">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Data Freshness</span>
                        <span className="text-green-600">{dashboardStats.dataFreshness}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Quick Actions */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Zap className="w-5 h-5 mr-2" />
                    Quick Actions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Button variant="outline" className="h-20 flex-col">
                      <RefreshCw className="w-6 h-6 mb-2" />
                      Refresh Data
                    </Button>
                    <Button variant="outline" className="h-20 flex-col">
                      <Users className="w-6 h-6 mb-2" />
                      Add Council
                    </Button>
                    <Button variant="outline" className="h-20 flex-col">
                      <Mail className="w-6 h-6 mb-2" />
                      Send Broadcast
                    </Button>
                    <Button variant="outline" className="h-20 flex-col">
                      <Download className="w-6 h-6 mb-2" />
                      Export Data
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Other tab content would go here */}
          {activeTab !== 'overview' && (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <Settings className="w-16 h-16 mx-auto" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {sidebarItems.find(item => item.id === activeTab)?.label} Section
              </h3>
              <p className="text-gray-600">
                This section is under development. The full admin interface will include comprehensive management tools for this area.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default AdminDashboard;
