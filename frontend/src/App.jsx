import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from 'next-themes'
import './App.css'

// Layout Components
import Navbar from './components/layout/Navbar'
import Sidebar from './components/layout/Sidebar'
import Footer from './components/layout/Footer'

// Page Components
import Dashboard from './pages/Dashboard'
import Grants from './pages/Grants'
import Applications from './pages/Applications'
import Analytics from './pages/Analytics'
import Community from './pages/Community'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Register from './pages/Register'

// Context Providers
import { AuthProvider } from './contexts/AuthContext'
import { GrantProvider } from './contexts/GrantContext'

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
      <AuthProvider>
        <GrantProvider>
          <Router>
            <div className="min-h-screen bg-background">
              <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                
                {/* Protected Routes with Layout */}
                <Route path="/*" element={
                  <div className="flex h-screen">
                    <Sidebar />
                    <div className="flex-1 flex flex-col overflow-hidden">
                      <Navbar />
                      <main className="flex-1 overflow-x-hidden overflow-y-auto bg-background">
                        <Routes>
                          <Route path="/" element={<Dashboard />} />
                          <Route path="/dashboard" element={<Dashboard />} />
                          <Route path="/grants" element={<Grants />} />
                          <Route path="/applications" element={<Applications />} />
                          <Route path="/analytics" element={<Analytics />} />
                          <Route path="/community" element={<Community />} />
                          <Route path="/settings" element={<Settings />} />
                        </Routes>
                      </main>
                      <Footer />
                    </div>
                  </div>
                } />
              </Routes>
            </div>
          </Router>
        </GrantProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
