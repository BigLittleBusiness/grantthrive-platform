import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Typography,
  Box,
  Divider,
  Chip,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Dashboard,
  Assignment,
  AssignmentTurnedIn,
  People,
  Forum,
  EmojiEvents,
  Event,
  Business,
  LibraryBooks,
  Analytics,
  Settings,
  Help,
  ExpandLess,
  ExpandMore,
  Add,
  Notifications,
  TrendingUp,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { useAuth } from '../../contexts/AuthContext';

const drawerWidth = 280;

const StyledDrawer = styled(Drawer)(({ theme }) => ({
  width: drawerWidth,
  flexShrink: 0,
  '& .MuiDrawer-paper': {
    width: drawerWidth,
    boxSizing: 'border-box',
    backgroundColor: '#fafafa',
    borderRight: '1px solid rgba(0, 0, 0, 0.08)',
  },
}));

const SidebarHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
  marginBottom: theme.spacing(1),
}));

const QuickActionButton = styled(ListItemButton)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  borderRadius: theme.spacing(1),
  margin: theme.spacing(0, 1, 1, 1),
  '&:hover': {
    backgroundColor: theme.palette.primary.dark,
  },
}));

const StatsCard = styled(Box)(({ theme }) => ({
  margin: theme.spacing(1),
  padding: theme.spacing(2),
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.spacing(1),
  boxShadow: '0px 1px 3px rgba(0, 0, 0, 0.08)',
}));

const ProfessionalSidebar = ({ open, onClose, selectedItem, onItemSelect }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { user } = useAuth();
  
  const [expandedSections, setExpandedSections] = useState({
    grants: true,
    community: true,
    professional: false,
  });

  const handleSectionToggle = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const getNavigationStructure = () => {
    const baseStructure = {
      main: [
        {
          id: 'dashboard',
          label: 'Dashboard',
          icon: <Dashboard />,
          path: '/dashboard',
          badge: null,
        },
      ],
      grants: [
        {
          id: 'grants',
          label: 'Browse Grants',
          icon: <Assignment />,
          path: '/grants',
          badge: '12 New',
        },
        {
          id: 'my-applications',
          label: 'My Applications',
          icon: <AssignmentTurnedIn />,
          path: '/applications',
          badge: '3',
        },
      ],
      community: [
        {
          id: 'community-hub',
          label: 'Community Hub',
          icon: <People />,
          path: '/community',
          badge: null,
        },
        {
          id: 'forum',
          label: 'Discussion Forum',
          icon: <Forum />,
          path: '/forum',
          badge: '5 New',
        },
        {
          id: 'success-stories',
          label: 'Success Stories',
          icon: <EmojiEvents />,
          path: '/success-stories',
          badge: null,
        },
        {
          id: 'events',
          label: 'Events & Webinars',
          icon: <Event />,
          path: '/events',
          badge: '2 Today',
        },
        {
          id: 'resources',
          label: 'Resource Hub',
          icon: <LibraryBooks />,
          path: '/resources',
          badge: null,
        },
      ],
      professional: [
        {
          id: 'marketplace',
          label: 'Professional Services',
          icon: <Business />,
          path: '/marketplace',
          badge: null,
        },
      ],
    };

    // Add admin-specific items
    if (user?.role === 'council_admin' || user?.role === 'council_staff') {
      baseStructure.admin = [
        {
          id: 'analytics',
          label: 'Analytics',
          icon: <Analytics />,
          path: '/analytics',
          badge: null,
        },
        {
          id: 'manage-grants',
          label: 'Manage Grants',
          icon: <Settings />,
          path: '/admin/grants',
          badge: null,
        },
      ];
    }

    return baseStructure;
  };

  const navigationStructure = getNavigationStructure();

  const renderNavigationItem = (item) => (
    <ListItem key={item.id} disablePadding>
      <ListItemButton
        selected={selectedItem === item.id}
        onClick={() => onItemSelect(item.id, item.path)}
        sx={{
          borderRadius: 1,
          mx: 1,
          mb: 0.5,
          '&.Mui-selected': {
            backgroundColor: theme.palette.primary.main,
            color: theme.palette.primary.contrastText,
            '& .MuiListItemIcon-root': {
              color: theme.palette.primary.contrastText,
            },
          },
        }}
      >
        <ListItemIcon sx={{ minWidth: 40 }}>
          {item.icon}
        </ListItemIcon>
        <ListItemText 
          primary={item.label}
          primaryTypographyProps={{
            fontSize: '0.875rem',
            fontWeight: selectedItem === item.id ? 600 : 500,
          }}
        />
        {item.badge && (
          <Chip
            label={item.badge}
            size="small"
            sx={{
              height: 20,
              fontSize: '0.75rem',
              backgroundColor: selectedItem === item.id 
                ? 'rgba(255, 255, 255, 0.2)' 
                : theme.palette.primary.main,
              color: selectedItem === item.id 
                ? theme.palette.primary.contrastText 
                : theme.palette.primary.contrastText,
            }}
          />
        )}
      </ListItemButton>
    </ListItem>
  );

  const renderSection = (title, items, sectionKey) => (
    <>
      <ListItem disablePadding>
        <ListItemButton
          onClick={() => handleSectionToggle(sectionKey)}
          sx={{ mx: 1, borderRadius: 1 }}
        >
          <ListItemText
            primary={title}
            primaryTypographyProps={{
              fontSize: '0.75rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              color: 'text.secondary',
            }}
          />
          {expandedSections[sectionKey] ? <ExpandLess /> : <ExpandMore />}
        </ListItemButton>
      </ListItem>
      <Collapse in={expandedSections[sectionKey]} timeout="auto" unmountOnExit>
        <List component="div" disablePadding>
          {items.map(renderNavigationItem)}
        </List>
      </Collapse>
    </>
  );

  const drawerContent = (
    <>
      {/* Header */}
      <SidebarHeader>
        <Box
          component="img"
          src="/logo-icon.png"
          alt="GrantThrive"
          sx={{ height: 32, width: 32 }}
        />
        <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
          GrantThrive
        </Typography>
      </SidebarHeader>

      {/* Quick Action */}
      <QuickActionButton onClick={() => onItemSelect('new-application', '/grants')}>
        <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
          <Add />
        </ListItemIcon>
        <ListItemText
          primary="Apply for Grant"
          primaryTypographyProps={{
            fontSize: '0.875rem',
            fontWeight: 600,
          }}
        />
      </QuickActionButton>

      {/* Navigation */}
      <List sx={{ px: 0 }}>
        {/* Main Items */}
        {navigationStructure.main.map(renderNavigationItem)}
        
        <Divider sx={{ my: 1, mx: 2 }} />
        
        {/* Grants Section */}
        {renderSection('Grants & Applications', navigationStructure.grants, 'grants')}
        
        <Divider sx={{ my: 1, mx: 2 }} />
        
        {/* Community Section */}
        {renderSection('Community', navigationStructure.community, 'community')}
        
        <Divider sx={{ my: 1, mx: 2 }} />
        
        {/* Professional Section */}
        {renderSection('Professional Services', navigationStructure.professional, 'professional')}
        
        {/* Admin Section */}
        {navigationStructure.admin && (
          <>
            <Divider sx={{ my: 1, mx: 2 }} />
            {renderSection('Administration', navigationStructure.admin, 'admin')}
          </>
        )}
      </List>

      {/* Stats Card */}
      <StatsCard>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
          Your Progress
        </Typography>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="body2" color="text.secondary">
            Applications
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            3 Active
          </Typography>
        </Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="body2" color="text.secondary">
            Success Rate
          </Typography>
          <Box display="flex" alignItems="center" gap={0.5}>
            <TrendingUp sx={{ fontSize: 16, color: 'success.main' }} />
            <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
              75%
            </Typography>
          </Box>
        </Box>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="body2" color="text.secondary">
            Total Funding
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            $125K
          </Typography>
        </Box>
      </StatsCard>

      {/* Help Section */}
      <List sx={{ mt: 'auto', px: 0 }}>
        <Divider sx={{ my: 1, mx: 2 }} />
        <ListItem disablePadding>
          <ListItemButton sx={{ mx: 1, borderRadius: 1 }}>
            <ListItemIcon sx={{ minWidth: 40 }}>
              <Help />
            </ListItemIcon>
            <ListItemText
              primary="Help & Support"
              primaryTypographyProps={{
                fontSize: '0.875rem',
                fontWeight: 500,
              }}
            />
          </ListItemButton>
        </ListItem>
      </List>
    </>
  );

  if (isMobile) {
    return (
      <Drawer
        variant="temporary"
        open={open}
        onClose={onClose}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        {drawerContent}
      </Drawer>
    );
  }

  return (
    <StyledDrawer variant="permanent" open>
      {drawerContent}
    </StyledDrawer>
  );
};

export default ProfessionalSidebar;

