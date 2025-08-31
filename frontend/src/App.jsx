import React, { useState } from 'react';
import Login from './pages/Login.jsx';
import Registration from './pages/Registration.jsx';
import AdminApprovalDashboard from './pages/AdminApprovalDashboard.jsx';
import CouncilAdminDashboard from './dashboards/CouncilAdminDashboard.jsx';
import CouncilStaffDashboard from './dashboards/CouncilStaffDashboard.jsx';
import CommunityMemberDashboard from './dashboards/CommunityMemberDashboard.jsx';
import ProfessionalConsultantDashboard from './dashboards/ProfessionalConsultantDashboard.jsx';
import GrantsListing from './pages/GrantsListing.jsx';
import GrantDetails from './pages/GrantDetails.jsx';
import ApplicationForm from './pages/ApplicationForm.jsx';
import CommunityForum from './pages/CommunityForum.jsx';
import ResourceHub from './pages/ResourceHub.jsx';
import WinnersShowcase from './pages/WinnersShowcase.jsx';
import GrantCreationWizard from './pages/GrantCreationWizard.jsx';
import CommunicationSettings from './pages/CommunicationSettings.jsx';
import QRCodeManagement from './pages/QRCodeManagement.jsx';
import CommunityVoting from './pages/CommunityVoting.jsx';
import PublicGrantMap from './pages/PublicGrantMap.jsx';

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [currentPage, setCurrentPage] = useState('login');

  const handleLogin = (userData) => {
    setCurrentUser(userData);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setCurrentPage('login');
  };

  const navigateToPage = (page) => {
    setCurrentPage(page);
  };

  // Show login page if no user is authenticated
  if (!currentUser) {
    if (currentPage === 'register') {
      return <Registration />;
    }
    return <Login onLogin={handleLogin} />;
  }

  // Route to appropriate dashboard based on user type
  const renderDashboard = () => {
    switch (currentUser.userType) {
      case 'council_admin':
        return <CouncilAdminDashboard user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
      case 'council_staff':
        return <CouncilStaffDashboard user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
      case 'community_member':
        return <CommunityMemberDashboard user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
      case 'professional_consultant':
        return <ProfessionalConsultantDashboard user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
      default:
        return <CommunityMemberDashboard user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    }
  };

  // Route to specific pages
  switch (currentPage) {
    case 'dashboard':
      return renderDashboard();
    case 'admin-approvals':
      return <AdminApprovalDashboard user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    case 'create-grant':
      return <GrantCreationWizard user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    case 'grants':
      return <GrantsListing user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    case 'grant-details':
      return <GrantDetails user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    case 'application-form':
      return <ApplicationForm user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    case 'community-forum':
      return <CommunityForum user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    case 'resource-hub':
      return <ResourceHub user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    case 'winners-showcase':
      return <WinnersShowcase user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    case 'communication-settings':
      return <CommunicationSettings user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    case 'qr-code-management':
      return <QRCodeManagement user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    case 'community-voting':
      return <CommunityVoting user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    case 'grant-map':
      return <PublicGrantMap user={currentUser} onNavigate={navigateToPage} onLogout={handleLogout} />;
    default:
      return renderDashboard();
  }
}

export default App;

