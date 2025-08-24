import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Button } from '../components/ui/button.jsx';
import { Input } from '../components/ui/input.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { 
  Mail, 
  Lock, 
  Eye, 
  EyeOff, 
  AlertCircle, 
  CheckCircle,
  Building,
  Shield,
  Clock,
  UserCheck
} from 'lucide-react';

const Login = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loginAttempt, setLoginAttempt] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Demo accounts for different user types
  const demoAccounts = [
    {
      email: 'sarah.johnson@melbourne.vic.gov.au',
      password: 'demo123',
      userType: 'council_admin',
      name: 'Sarah Johnson',
      organization: 'Melbourne City Council',
      role: 'Council Administrator',
      status: 'active',
      avatar: 'SJ'
    },
    {
      email: 'michael.chen@melbourne.vic.gov.au',
      password: 'demo123',
      userType: 'council_staff',
      name: 'Michael Chen',
      organization: 'Melbourne City Council',
      role: 'Council Staff',
      status: 'active',
      avatar: 'MC'
    },
    {
      email: 'james.smith@auckland.govt.nz',
      password: 'demo123',
      userType: 'council_staff',
      name: 'James Smith',
      organization: 'Auckland Council',
      role: 'Council Staff (NZ)',
      status: 'active',
      avatar: 'JS'
    },
    {
      email: 'emma.thompson@communityarts.org.au',
      password: 'demo123',
      userType: 'community_member',
      name: 'Emma Thompson',
      organization: 'Community Arts Collective',
      role: 'Community Member',
      status: 'active',
      avatar: 'ET'
    },
    {
      email: 'david.wilson@grantsuccess.com.au',
      password: 'demo123',
      userType: 'professional_consultant',
      name: 'David Wilson',
      organization: 'Grant Success Partners',
      role: 'Professional Consultant',
      status: 'active',
      avatar: 'DW'
    },
    {
      email: 'pending.staff@council.gov.au',
      password: 'demo123',
      userType: 'council_staff',
      name: 'Pending Staff',
      organization: 'Sample Council',
      role: 'Council Staff',
      status: 'pending_approval',
      avatar: 'PS'
    }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setLoginAttempt(null);

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Find matching account
    const account = demoAccounts.find(
      acc => acc.email.toLowerCase() === formData.email.toLowerCase() && 
             acc.password === formData.password
    );

    if (!account) {
      setLoginAttempt({
        success: false,
        message: 'Invalid email or password. Please check your credentials and try again.'
      });
      setIsLoading(false);
      return;
    }

    if (account.status === 'pending_approval') {
      setLoginAttempt({
        success: false,
        message: 'Your account is pending approval. Please wait for administrator verification.',
        isPending: true
      });
      setIsLoading(false);
      return;
    }

    // Successful login
    setLoginAttempt({
      success: true,
      message: `Welcome back, ${account.name}!`,
      account: account
    });

    // Call the onLogin callback with user data
    setTimeout(() => {
      onLogin(account);
    }, 1500);

    setIsLoading(false);
  };

  const fillDemoCredentials = (account) => {
    setFormData({
      email: account.email,
      password: account.password,
      rememberMe: false
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-8">
      <div className="max-w-md w-full px-4">
        <Card className="bg-white shadow-xl">
          <CardHeader className="text-center pb-6">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <Building className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-gray-900">
              Welcome to GrantThrive
            </CardTitle>
            <p className="text-gray-600 mt-2">
              Sign in to your account to continue
            </p>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    placeholder="Enter your email"
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    placeholder="Enter your password"
                    className="pl-10 pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.rememberMe}
                    onChange={(e) => handleInputChange('rememberMe', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-600">Remember me</span>
                </label>
                <a href="#" className="text-sm text-blue-600 hover:text-blue-500">
                  Forgot password?
                </a>
              </div>

              {/* Login Result */}
              {loginAttempt && (
                <div className={`p-4 rounded-lg border ${
                  loginAttempt.success 
                    ? 'bg-green-50 border-green-200' 
                    : loginAttempt.isPending
                    ? 'bg-yellow-50 border-yellow-200'
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="flex items-center gap-3">
                    {loginAttempt.success ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : loginAttempt.isPending ? (
                      <Clock className="w-5 h-5 text-yellow-600" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-600" />
                    )}
                    <div>
                      <p className={`text-sm font-medium ${
                        loginAttempt.success 
                          ? 'text-green-900' 
                          : loginAttempt.isPending
                          ? 'text-yellow-900'
                          : 'text-red-900'
                      }`}>
                        {loginAttempt.message}
                      </p>
                      {loginAttempt.success && loginAttempt.account && (
                        <p className="text-xs text-green-700 mt-1">
                          Logging in as {loginAttempt.account.role}...
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <Button 
                type="submit" 
                className="w-full bg-blue-600 hover:bg-blue-700"
                disabled={isLoading}
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>

            {/* Demo Accounts */}
            <div className="border-t pt-6">
              <h3 className="text-sm font-medium text-gray-900 mb-4 text-center">
                Demo Accounts
              </h3>
              <div className="space-y-2">
                {demoAccounts.filter(acc => acc.status === 'active').map((account, index) => (
                  <button
                    key={index}
                    onClick={() => fillDemoCredentials(account)}
                    className="w-full p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-semibold">
                          {account.avatar}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{account.name}</div>
                          <div className="text-xs text-gray-600">{account.organization}</div>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {account.role}
                      </Badge>
                    </div>
                  </button>
                ))}
              </div>
              
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <Shield className="w-4 h-4 text-blue-600 mt-0.5" />
                  <div>
                    <p className="text-xs text-blue-900 font-medium">Demo Mode</p>
                    <p className="text-xs text-blue-800">
                      Click any account above to auto-fill credentials. Password: demo123
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Registration Link */}
            <div className="text-center pt-4 border-t">
              <p className="text-sm text-gray-600">
                Don't have an account?{' '}
                <a href="/register" className="text-blue-600 hover:text-blue-500 font-medium">
                  Register here
                </a>
              </p>
            </div>

            {/* Account Status Info */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Account Status Information</h4>
              <div className="space-y-2 text-xs text-gray-600">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-3 h-3 text-green-600" />
                  <span><strong>Active:</strong> Full platform access</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-3 h-3 text-yellow-600" />
                  <span><strong>Pending:</strong> Awaiting admin approval</span>
                </div>
                <div className="flex items-center gap-2">
                  <UserCheck className="w-3 h-3 text-blue-600" />
                  <span><strong>Government Staff:</strong> Requires .gov.au or .govt.nz email verification</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Login;

