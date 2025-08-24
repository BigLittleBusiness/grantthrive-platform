import { createContext, useContext, useState, useEffect } from 'react'
import { useAuth } from './AuthContext'

export const GrantContext = createContext({})

export const useGrants = () => {
  const context = useContext(GrantContext)
  if (!context) {
    throw new Error('useGrants must be used within a GrantProvider')
  }
  return context
}

export const GrantProvider = ({ children }) => {
  const { getAuthHeaders, isAuthenticated } = useAuth()
  const [grants, setGrants] = useState([])
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    status: 'all',
    category: 'all',
    search: '',
    dateRange: null,
  })

  // Fetch grants from API
  const fetchGrants = async () => {
    if (!isAuthenticated) return
    
    try {
      setLoading(true)
      const response = await fetch('/api/grants', {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      })

      if (response.ok) {
        const data = await response.json()
        setGrants(data.grants || [])
      }
    } catch (error) {
      console.error('Error fetching grants:', error)
    } finally {
      setLoading(false)
    }
  }

  // Fetch applications from API
  const fetchApplications = async () => {
    if (!isAuthenticated) return
    
    try {
      setLoading(true)
      const response = await fetch('/api/applications', {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      })

      if (response.ok) {
        const data = await response.json()
        setApplications(data.applications || [])
      }
    } catch (error) {
      console.error('Error fetching applications:', error)
    } finally {
      setLoading(false)
    }
  }

  // Create new grant
  const createGrant = async (grantData) => {
    try {
      setLoading(true)
      const response = await fetch('/api/grants', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(grantData),
      })

      if (response.ok) {
        const newGrant = await response.json()
        setGrants(prev => [newGrant, ...prev])
        return { success: true, grant: newGrant }
      } else {
        throw new Error('Failed to create grant')
      }
    } catch (error) {
      console.error('Error creating grant:', error)
      return { success: false, error: error.message }
    } finally {
      setLoading(false)
    }
  }

  // Update grant
  const updateGrant = async (grantId, updates) => {
    try {
      setLoading(true)
      const response = await fetch(`/api/grants/${grantId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(updates),
      })

      if (response.ok) {
        const updatedGrant = await response.json()
        setGrants(prev => prev.map(grant => 
          grant.id === grantId ? updatedGrant : grant
        ))
        return { success: true, grant: updatedGrant }
      } else {
        throw new Error('Failed to update grant')
      }
    } catch (error) {
      console.error('Error updating grant:', error)
      return { success: false, error: error.message }
    } finally {
      setLoading(false)
    }
  }

  // Delete grant
  const deleteGrant = async (grantId) => {
    try {
      setLoading(true)
      const response = await fetch(`/api/grants/${grantId}`, {
        method: 'DELETE',
        headers: {
          ...getAuthHeaders(),
        },
      })

      if (response.ok) {
        setGrants(prev => prev.filter(grant => grant.id !== grantId))
        return { success: true }
      } else {
        throw new Error('Failed to delete grant')
      }
    } catch (error) {
      console.error('Error deleting grant:', error)
      return { success: false, error: error.message }
    } finally {
      setLoading(false)
    }
  }

  // Submit application
  const submitApplication = async (applicationData) => {
    try {
      setLoading(true)
      const response = await fetch('/api/applications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(applicationData),
      })

      if (response.ok) {
        const newApplication = await response.json()
        setApplications(prev => [newApplication, ...prev])
        return { success: true, application: newApplication }
      } else {
        throw new Error('Failed to submit application')
      }
    } catch (error) {
      console.error('Error submitting application:', error)
      return { success: false, error: error.message }
    } finally {
      setLoading(false)
    }
  }

  // Update application status
  const updateApplicationStatus = async (applicationId, status, notes = '') => {
    try {
      setLoading(true)
      const response = await fetch(`/api/applications/${applicationId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ status, notes }),
      })

      if (response.ok) {
        const updatedApplication = await response.json()
        setApplications(prev => prev.map(app => 
          app.id === applicationId ? updatedApplication : app
        ))
        return { success: true, application: updatedApplication }
      } else {
        throw new Error('Failed to update application status')
      }
    } catch (error) {
      console.error('Error updating application status:', error)
      return { success: false, error: error.message }
    } finally {
      setLoading(false)
    }
  }

  // Filter grants based on current filters
  const filteredGrants = grants.filter(grant => {
    if (filters.status !== 'all' && grant.status !== filters.status) return false
    if (filters.category !== 'all' && grant.category !== filters.category) return false
    if (filters.search && !grant.title.toLowerCase().includes(filters.search.toLowerCase())) return false
    return true
  })

  // Filter applications based on current filters
  const filteredApplications = applications.filter(application => {
    if (filters.status !== 'all' && application.status !== filters.status) return false
    if (filters.search && !application.title.toLowerCase().includes(filters.search.toLowerCase())) return false
    return true
  })

  // Load data when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchGrants()
      fetchApplications()
    }
  }, [isAuthenticated])

  const value = {
    grants,
    applications,
    filteredGrants,
    filteredApplications,
    loading,
    filters,
    setFilters,
    fetchGrants,
    fetchApplications,
    createGrant,
    updateGrant,
    deleteGrant,
    submitApplication,
    updateApplicationStatus,
  }

  return (
    <GrantContext.Provider value={value}>
      {children}
    </GrantContext.Provider>
  )
}

