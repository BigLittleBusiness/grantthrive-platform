import { createContext, useContext, useState, useEffect } from 'react'

export const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  // Initialize auth state from localStorage
  useEffect(() => {
    const token = localStorage.getItem('grantthrive_token')
    const userData = localStorage.getItem('grantthrive_user')
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData)
        setUser(parsedUser)
        setIsAuthenticated(true)
      } catch (error) {
        console.error('Error parsing user data:', error)
        localStorage.removeItem('grantthrive_token')
        localStorage.removeItem('grantthrive_user')
      }
      // Demo login function
  const login = async (email, password) => {
    setLoading(true)
    
    // Demo users for testing
    const demoUsers = {
      'admin@council.gov.au': {
        id: 1,
        name: 'Sarah Johnson',
        email: 'admin@council.gov.au',
        role: 'council_admin',
        organization: 'Melbourne City Council',
        avatar: null,
      },
      'member@community.org.au': {
        id: 2,
        name: 'Michael Chen',
        email: 'member@community.org.au',
        role: 'community_member',
        organization: 'Community Arts Collective',
        avatar: null,
      },
      'consultant@professional.com.au': {
        id: 3,
        name: 'Emma Thompson',
        email: 'consultant@professional.com.au',
        role: 'professional_consultant',
        organization: 'Grant Success Partners',
        avatar: null,
      },
    }

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000))

    if (demoUsers[email] && password === 'demo123') {
      const user = demoUsers[email]
      setUser(user)
      setIsAuthenticated(true)
      
      // Store in localStorage
      localStorage.setItem('grantthrive_token', 'demo-token-' + user.id)
      localStorage.setItem('grantthrive_user', JSON.stringify(user))
      
      setLoading(false)
      return { success: true, user }
    } else {
      setLoading(false)
      return { success: false, message: 'Invalid email or password' }
    }
  } register = async (userData) => {
    try {
      setLoading(true)
      
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      })

      if (!response.ok) {
        throw new Error('Registration failed')
      }

      const data = await response.json()
      
      // Auto-login after registration
      localStorage.setItem('grantthrive_token', data.token)
      localStorage.setItem('grantthrive_user', JSON.stringify(data.user))
      
      setUser(data.user)
      setIsAuthenticated(true)
      
      return { success: true, user: data.user }
    } catch (error) {
      console.error('Registration error:', error)
      return { success: false, error: error.message }
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('grantthrive_token')
    localStorage.removeItem('grantthrive_user')
    setUser(null)
    setIsAuthenticated(false)
  }

  const updateUser = (updatedUser) => {
    setUser(updatedUser)
    localStorage.setItem('grantthrive_user', JSON.stringify(updatedUser))
  }

  const getAuthHeaders = () => {
    const token = localStorage.getItem('grantthrive_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    updateUser,
    getAuthHeaders,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

