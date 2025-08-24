import React, { useState } from 'react';
import { Button } from './components/ui/button.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card.jsx';
import { Badge } from './components/ui/badge.jsx';
import { Avatar, AvatarFallback, AvatarImage } from './components/ui/avatar.jsx';
import { Input } from './components/ui/input.jsx';
import { 
  Search, 
  Bell, 
  User, 
  Menu, 
  Home, 
  FileText, 
  Users, 
  MessageSquare, 
  Trophy, 
  Calendar,
  Building,
  TrendingUp,
  DollarSign,
  Clock,
  Plus,
  ArrowRight,
  Star,
  Briefcase
} from 'lucide-react';
import './App.css';

// Import role-specific dashboards
import CouncilAdminDashboard from './dashboards/CouncilAdminDashboard.jsx';
import CouncilStaffDashboard from './dashboards/CouncilStaffDashboard.jsx';
import CommunityMemberDashboard from './dashboards/CommunityMemberDashboard.jsx';
import ProfessionalConsultantDashboard from './dashboards/ProfessionalConsultantDashboard.jsx';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedDemo, setSelectedDemo] = useState('role-selector');
  const [selectedRole, setSelectedRole] = useState(null);

  const userRoles = [
    {
      id: 'council_admin',
      name: 'Council Administrator',
      description: 'Manage grant programs, review applications, and oversee community funding',
      icon: Building,
      color: 'blue',
      user: {
        name: 'Sarah Johnson',
        organization: 'Melbourne City Council',
        avatar: 'SJ'
      }
    },
    {
      id: 'council_staff',
      name: 'Council Staff',
      description: 'Process applications, engage with community, and conduct grant reviews',
      icon: FileText,
      color: 'green',
      user: {
        name: 'Michael Chen',
        organization: 'Melbourne City Council',
        avatar: 'MC'
      }
    },
    {
      id: 'community_member',
      name: 'Community Member',
      description: 'Apply for grants, access resources, and connect with the community',
      icon: Users,
      color: 'purple',
      user: {
        name: 'Emma Thompson',
        organization: 'Community Arts Collective',
        avatar: 'ET'
      }
    },
    {
      id: 'professional_consultant',
      name: 'Professional Consultant',
      description: 'Provide grant writing services and consulting through the marketplace',
      icon: Briefcase,
      color: 'orange',
      user: {
        name: 'David Wilson',
        organization: 'Grant Success Partners',
        avatar: 'DW'
      }
    }
  ];

  const currentUser = selectedRole ? userRoles.find(role => role.id === selectedRole)?.user : null;

  const Sidebar = () => (
    <div className={`fixed left-0 top-0 h-full bg-white border-r border-gray-200 transition-all duration-300 z-40 ${sidebarOpen ? 'w-72' : 'w-16'}`}>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Building className="w-5 h-5 text-white" />
          </div>
          {sidebarOpen && (
            <div>
              <h1 className="text-xl font-bold text-blue-600">GrantThrive</h1>
            </div>
          )}
        </div>
      </div>

      <div className="p-4">
        <Button 
          className="w-full bg-blue-600 hover:bg-blue-700 text-white mb-4"
          onClick={() => setSelectedDemo('role-selector')}
        >
          <Plus className="w-4 h-4 mr-2" />
          {sidebarOpen ? 'Switch Role' : ''}
        </Button>

        <nav className="space-y-2">
          {[
            { id: 'dashboard', icon: Home, label: 'Dashboard' },
            { id: 'grants', icon: FileText, label: 'Browse Grants' },
            { id: 'applications', icon: FileText, label: 'Applications' },
            { id: 'community', icon: Users, label: 'Community Hub' },
            { id: 'forum', icon: MessageSquare, label: 'Discussion Forum' },
            { id: 'success', icon: Trophy, label: 'Success Stories' },
            { id: 'events', icon: Calendar, label: 'Events & Webinars' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setSelectedDemo(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                selectedDemo === item.id 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <item.icon className="w-5 h-5" />
              {sidebarOpen && <span className="font-medium">{item.label}</span>}
            </button>
          ))}
        </nav>

        {sidebarOpen && selectedRole && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-sm text-gray-700 mb-2">Current Role</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">User Type</span>
                <span className="font-semibold">{userRoles.find(r => r.id === selectedRole)?.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Organization</span>
                <span className="font-semibold">{currentUser?.organization}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const Header = () => (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <Menu className="w-5 h-5" />
          </Button>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search grants, resources..."
              className="pl-10 w-80"
            />
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm">
            <Bell className="w-5 h-5" />
          </Button>
          {currentUser && (
            <div className="flex items-center gap-3">
              <Avatar>
                <AvatarFallback className="bg-blue-600 text-white">
                  {currentUser.avatar}
                </AvatarFallback>
              </Avatar>
              <div className="text-sm">
                <div className="font-semibold">{currentUser.name}</div>
                <div className="text-gray-500">{userRoles.find(r => r.id === selectedRole)?.name}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );

  const RoleSelector = () => (
    <div className="p-6">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to GrantThrive! 🌟
        </h1>
        <p className="text-xl text-gray-600 mb-2">
          Choose your role to see the tailored dashboard experience
        </p>
        <p className="text-gray-500">
          Each user type has a completely different interface designed for their specific needs
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl mx-auto">
        {userRoles.map((role) => (
          <Card 
            key={role.id} 
            className="hover:shadow-lg transition-all duration-300 cursor-pointer border-2 hover:border-blue-200"
            onClick={() => {
              setSelectedRole(role.id);
              setSelectedDemo('dashboard');
            }}
          >
            <CardHeader className="text-center pb-4">
              <div className={`w-16 h-16 bg-${role.color}-100 rounded-full flex items-center justify-center mx-auto mb-4`}>
                <role.icon className={`w-8 h-8 text-${role.color}-600`} />
              </div>
              <CardTitle className="text-xl">{role.name}</CardTitle>
            </CardHeader>
            <CardContent className="text-center">
              <p className="text-gray-600 mb-6">{role.description}</p>
              
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-center gap-3 mb-2">
                  <Avatar>
                    <AvatarFallback className={`bg-${role.color}-600 text-white`}>
                      {role.user.avatar}
                    </AvatarFallback>
                  </Avatar>
                  <div className="text-left">
                    <div className="font-semibold text-gray-900">{role.user.name}</div>
                    <div className="text-sm text-gray-600">{role.user.organization}</div>
                  </div>
                </div>
              </div>

              <Button className={`w-full bg-${role.color}-600 hover:bg-${role.color}-700`}>
                View {role.name} Dashboard
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-12 text-center">
        <Card className="max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle>Why Role-Specific Dashboards Matter</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">For Councils</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Administrative oversight and program management</li>
                  <li>• Application review workflows and approval processes</li>
                  <li>• Budget tracking and performance analytics</li>
                  <li>• Community engagement and communication tools</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">For Community & Professionals</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Grant discovery and application management</li>
                  <li>• Progress tracking and status updates</li>
                  <li>• Resource access and educational content</li>
                  <li>• Professional marketplace and networking</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderContent = () => {
    if (selectedDemo === 'role-selector' || !selectedRole) {
      return <RoleSelector />;
    }

    if (selectedDemo === 'dashboard') {
      switch (selectedRole) {
        case 'council_admin':
          return <CouncilAdminDashboard />;
        case 'council_staff':
          return <CouncilStaffDashboard />;
        case 'community_member':
          return <CommunityMemberDashboard />;
        case 'professional_consultant':
          return <ProfessionalConsultantDashboard />;
        default:
          return <RoleSelector />;
      }
    }

    // For other navigation items, show placeholder
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            {selectedDemo.charAt(0).toUpperCase() + selectedDemo.slice(1)} Page
          </h2>
          <p className="text-gray-600 mb-6">
            This section would be customized for the {userRoles.find(r => r.id === selectedRole)?.name} role.
          </p>
          <Button onClick={() => setSelectedDemo('dashboard')}>
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className={`transition-all duration-300 ${sidebarOpen ? 'ml-72' : 'ml-16'}`}>
        <Header />
        <main>
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App;

