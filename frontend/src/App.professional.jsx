import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Box, Toolbar } from '@mui/material';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { GrantProvider } from './contexts/GrantContext';

// Theme
import { grantThriveTheme } from './theme/theme';

// Professional Components
import ProfessionalNavbar from './components/layout/ProfessionalNavbar';
import ProfessionalSidebar from './components/layout/ProfessionalSidebar';

// Pages
import ProfessionalDashboard from './pages/ProfessionalDashboard';
import Grants from './pages/Grants';
import Applications from './pages/Applications';
import Analytics from './pages/Analytics';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';

function AppContent() {
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState('dashboard');

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleItemSelect = (itemId, path) => {
    setSelectedItem(itemId);
    // Handle navigation here
    console.log('Navigate to:', path);
  };

  const handleSearch = (searchTerm) => {
    console.log('Search:', searchTerm);
  };

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    );
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <ProfessionalNavbar 
        onMenuClick={handleSidebarToggle} 
        onSearch={handleSearch}
      />
      <ProfessionalSidebar 
        open={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        selectedItem={selectedItem}
        onItemSelect={handleItemSelect}
      />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          minHeight: '100vh',
          backgroundColor: 'background.default',
          ml: { md: '280px' },
        }}
      >
        <Toolbar />
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" />} />
          <Route path="/dashboard" element={<ProfessionalDashboard />} />
          <Route path="/grants" element={<Grants />} />
          <Route path="/applications" element={<Applications />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </Box>
    </Box>
  );
}

function ProfessionalApp() {
  return (
    <ThemeProvider theme={grantThriveTheme}>
      <CssBaseline />
      <AuthProvider>
        <GrantProvider>
          <Router>
            <AppContent />
          </Router>
        </GrantProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default ProfessionalApp;

