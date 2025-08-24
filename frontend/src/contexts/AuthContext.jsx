import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '../utils/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check for existing authentication on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      const userData = await apiClient.verifyToken();
      if (userData) {
        setUser(userData);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      // Token is invalid, clear it
      apiClient.setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      setError(null);
      setLoading(true);
      
      const response = await apiClient.login(email, password);
      
      if (response.user && response.token) {
        setUser(response.user);
        return { success: true, user: response.user };
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      const errorMessage = error.message || 'Login failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    try {
      setError(null);
      setLoading(true);
      
      const response = await apiClient.register(userData);
      
      if (response.user) {
        // If user is immediately active, set them as logged in
        if (response.token) {
          setUser(response.user);
        }
        return { 
          success: true, 
          user: response.user,
          requiresApproval: response.requires_approval || false
        };
      } else {
        throw new Error('Registration failed');
      }
    } catch (error) {
      const errorMessage = error.message || 'Registration failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const demoLogin = async (demoType) => {
    try {
      setError(null);
      setLoading(true);
      
      const response = await apiClient.demoLogin(demoType);
      
      if (response.user && response.token) {
        setUser(response.user);
        return { success: true, user: response.user };
      } else {
        throw new Error('Demo login failed');
      }
    } catch (error) {
      const errorMessage = error.message || 'Demo login failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setError(null);
    }
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
  };

  const clearError = () => {
    setError(null);
  };

  // Helper functions for role checking
  const isAdmin = () => {
    return user && (user.role === 'council_admin' || user.role === 'system_admin');
  };

  const isCouncilStaff = () => {
    return user && (user.role === 'council_staff' || user.role === 'council_admin');
  };

  const isCommunityMember = () => {
    return user && user.role === 'community_member';
  };

  const isProfessionalConsultant = () => {
    return user && user.role === 'professional_consultant';
  };

  const hasRole = (role) => {
    return user && user.role === role;
  };

  const getAuthHeaders = () => {
    const token = localStorage.getItem('authToken');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const value = {
    user,
    loading,
    error,
    login,
    register,
    demoLogin,
    logout,
    updateUser,
    clearError,
    checkAuthStatus,
    getAuthHeaders,
    isAuthenticated: !!user,
    isAdmin,
    isCouncilStaff,
    isCommunityMember,
    isProfessionalConsultant,
    hasRole
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export { AuthContext };

