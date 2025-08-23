// API utility for GrantThrive frontend-backend integration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('authToken');
  }

  // Set authentication token
  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('authToken');
    }
  }

  // Get authentication headers
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: this.getHeaders(),
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      // Handle authentication errors
      if (response.status === 401) {
        this.setToken(null);
        window.location.href = '/login';
        throw new Error('Authentication required');
      }

      // Handle rate limiting
      if (response.status === 429) {
        throw new Error('Too many requests. Please try again later.');
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // GET request
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  // POST request
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // PUT request
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // DELETE request
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // Authentication endpoints
  async login(email, password) {
    const response = await this.post('/auth/login', { email, password });
    if (response.success && response.data.token) {
      this.setToken(response.data.token);
    }
    return response;
  }

  async register(userData) {
    return this.post('/auth/register', userData);
  }

  async logout() {
    try {
      await this.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.setToken(null);
    }
  }

  async verifyToken() {
    if (!this.token) return { success: false };
    return this.post('/auth/verify', { token: this.token });
  }

  async refreshToken() {
    return this.post('/auth/refresh');
  }

  // User endpoints
  async getCurrentUser() {
    return this.get('/users/me');
  }

  async updateProfile(userData) {
    return this.put('/users/me', userData);
  }

  async changePassword(passwordData) {
    return this.post('/auth/change-password', passwordData);
  }

  // Grant endpoints
  async getGrants(filters = {}) {
    const queryParams = new URLSearchParams(filters).toString();
    return this.get(`/grants${queryParams ? `?${queryParams}` : ''}`);
  }

  async getGrant(id) {
    return this.get(`/grants/${id}`);
  }

  async createGrant(grantData) {
    return this.post('/grants', grantData);
  }

  async updateGrant(id, grantData) {
    return this.put(`/grants/${id}`, grantData);
  }

  async deleteGrant(id) {
    return this.delete(`/grants/${id}`);
  }

  async getGrantCategories() {
    return this.get('/grants/categories');
  }

  async getPublicGrants() {
    return this.get('/grants/public');
  }

  // Application endpoints
  async getApplications(filters = {}) {
    const queryParams = new URLSearchParams(filters).toString();
    return this.get(`/applications${queryParams ? `?${queryParams}` : ''}`);
  }

  async getApplication(id) {
    return this.get(`/applications/${id}`);
  }

  async createApplication(applicationData) {
    return this.post('/applications', applicationData);
  }

  async updateApplication(id, applicationData) {
    return this.put(`/applications/${id}`, applicationData);
  }

  async updateApplicationStatus(id, status, notes = '') {
    return this.put(`/applications/${id}/status`, { status, notes });
  }

  async deleteApplication(id) {
    return this.delete(`/applications/${id}`);
  }

  async getApplicationStats() {
    return this.get('/applications/stats');
  }

  // Analytics endpoints
  async getDashboardMetrics() {
    return this.get('/analytics/dashboard');
  }

  async getTrendsData(months = 12) {
    return this.get(`/analytics/trends?months=${months}`);
  }

  async getCategoryDistribution() {
    return this.get('/analytics/categories');
  }

  async getStatusDistribution() {
    return this.get('/analytics/status-distribution');
  }

  async getPerformanceMetrics() {
    return this.get('/analytics/performance');
  }

  async getInsights() {
    return this.get('/analytics/insights');
  }

  async exportAnalyticsData(exportType = 'json', dateRange = '12months') {
    return this.post('/analytics/export', { type: exportType, date_range: dateRange });
  }

  // Health check
  async healthCheck() {
    return this.get('/health');
  }

  async getApiStatus() {
    return this.get('/status');
  }
}

// Create and export a singleton instance
const apiClient = new ApiClient();

export default apiClient;

// Export individual methods for convenience
export const {
  login,
  register,
  logout,
  verifyToken,
  refreshToken,
  getCurrentUser,
  updateProfile,
  changePassword,
  getGrants,
  getGrant,
  createGrant,
  updateGrant,
  deleteGrant,
  getGrantCategories,
  getPublicGrants,
  getApplications,
  getApplication,
  createApplication,
  updateApplication,
  updateApplicationStatus,
  deleteApplication,
  getApplicationStats,
  getDashboardMetrics,
  getTrendsData,
  getCategoryDistribution,
  getStatusDistribution,
  getPerformanceMetrics,
  getInsights,
  exportAnalyticsData,
  healthCheck,
  getApiStatus
} = apiClient;

