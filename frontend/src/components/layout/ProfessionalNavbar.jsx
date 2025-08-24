import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Box,
  Badge,
  InputBase,
  Divider,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Search,
  Notifications,
  AccountCircle,
  Menu as MenuIcon,
  Dashboard,
  Assignment,
  People,
  Forum,
  EmojiEvents,
  Event,
  Business,
  Settings,
  ExitToApp,
} from '@mui/icons-material';
import { styled, alpha } from '@mui/material/styles';
import { useAuth } from '../../contexts/AuthContext';

const SearchContainer = styled('div')(({ theme }) => ({
  position: 'relative',
  borderRadius: theme.shape.borderRadius,
  backgroundColor: alpha(theme.palette.common.black, 0.05),
  '&:hover': {
    backgroundColor: alpha(theme.palette.common.black, 0.08),
  },
  marginLeft: 0,
  width: '100%',
  [theme.breakpoints.up('sm')]: {
    marginLeft: theme.spacing(1),
    width: 'auto',
  },
}));

const SearchIconWrapper = styled('div')(({ theme }) => ({
  padding: theme.spacing(0, 2),
  height: '100%',
  position: 'absolute',
  pointerEvents: 'none',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
  color: 'inherit',
  '& .MuiInputBase-input': {
    padding: theme.spacing(1, 1, 1, 0),
    paddingLeft: `calc(1em + ${theme.spacing(4)})`,
    transition: theme.transitions.create('width'),
    width: '100%',
    [theme.breakpoints.up('sm')]: {
      width: '20ch',
      '&:focus': {
        width: '30ch',
      },
    },
  },
}));

const LogoContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  cursor: 'pointer',
}));

const ProfessionalNavbar = ({ onMenuClick, onSearch }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { user, logout } = useAuth();
  
  const [anchorEl, setAnchorEl] = useState(null);
  const [notificationAnchor, setNotificationAnchor] = useState(null);
  const [searchValue, setSearchValue] = useState('');

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationMenuOpen = (event) => {
    setNotificationAnchor(event.currentTarget);
  };

  const handleNotificationMenuClose = () => {
    setNotificationAnchor(null);
  };

  const handleSearchChange = (event) => {
    setSearchValue(event.target.value);
    if (onSearch) {
      onSearch(event.target.value);
    }
  };

  const handleLogout = () => {
    logout();
    handleProfileMenuClose();
  };

  const getNavigationItems = () => {
    const baseItems = [
      { label: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
      { label: 'Grants', icon: <Assignment />, path: '/grants' },
      { label: 'Applications', icon: <Assignment />, path: '/applications' },
    ];

    const communityItems = [
      { label: 'Community', icon: <People />, path: '/community' },
      { label: 'Forum', icon: <Forum />, path: '/forum' },
      { label: 'Success Stories', icon: <EmojiEvents />, path: '/success-stories' },
      { label: 'Events', icon: <Event />, path: '/events' },
    ];

    const professionalItems = [
      { label: 'Marketplace', icon: <Business />, path: '/marketplace' },
    ];

    if (user?.role === 'council_admin' || user?.role === 'council_staff') {
      return [...baseItems, ...communityItems, ...professionalItems];
    }

    return [...baseItems, ...communityItems, ...professionalItems];
  };

  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        zIndex: theme.zIndex.drawer + 1,
        backgroundColor: 'background.paper',
        color: 'text.primary',
        boxShadow: '0px 1px 3px rgba(0, 0, 0, 0.1)',
      }}
    >
      <Toolbar>
        {/* Mobile Menu Button */}
        {isMobile && (
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={onMenuClick}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
        )}

        {/* Logo */}
        <LogoContainer>
          <Box
            component="img"
            src="/logo-icon.png"
            alt="GrantThrive"
            sx={{ height: 32, width: 32 }}
          />
          <Typography
            variant="h6"
            component="div"
            sx={{
              fontWeight: 600,
              color: 'primary.main',
              display: { xs: 'none', sm: 'block' },
            }}
          >
            GrantThrive
          </Typography>
        </LogoContainer>

        {/* Desktop Navigation */}
        {!isMobile && (
          <Box sx={{ display: 'flex', ml: 4, gap: 1 }}>
            {getNavigationItems().slice(0, 4).map((item) => (
              <Button
                key={item.label}
                color="inherit"
                startIcon={item.icon}
                sx={{
                  textTransform: 'none',
                  fontWeight: 500,
                  px: 2,
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.primary.main, 0.08),
                  },
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>
        )}

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Search */}
        <SearchContainer>
          <SearchIconWrapper>
            <Search />
          </SearchIconWrapper>
          <StyledInputBase
            placeholder="Search grants, resources..."
            inputProps={{ 'aria-label': 'search' }}
            value={searchValue}
            onChange={handleSearchChange}
          />
        </SearchContainer>

        {/* Notifications */}
        <IconButton
          size="large"
          color="inherit"
          onClick={handleNotificationMenuOpen}
          sx={{ ml: 1 }}
        >
          <Badge badgeContent={3} color="error">
            <Notifications />
          </Badge>
        </IconButton>

        {/* Profile Menu */}
        <IconButton
          size="large"
          edge="end"
          onClick={handleProfileMenuOpen}
          color="inherit"
          sx={{ ml: 1 }}
        >
          <Avatar
            sx={{
              width: 32,
              height: 32,
              bgcolor: 'primary.main',
              fontSize: '0.875rem',
            }}
          >
            {user?.name?.charAt(0) || 'U'}
          </Avatar>
        </IconButton>
      </Toolbar>

      {/* Profile Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleProfileMenuClose}
        onClick={handleProfileMenuClose}
        PaperProps={{
          elevation: 3,
          sx: {
            mt: 1.5,
            minWidth: 200,
            '& .MuiMenuItem-root': {
              px: 2,
              py: 1,
            },
          },
        }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            {user?.name || 'User'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {user?.email}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {user?.role?.replace('_', ' ').toUpperCase()}
          </Typography>
        </Box>
        <Divider />
        <MenuItem>
          <AccountCircle sx={{ mr: 2 }} />
          Profile
        </MenuItem>
        <MenuItem>
          <Settings sx={{ mr: 2 }} />
          Settings
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>
          <ExitToApp sx={{ mr: 2 }} />
          Logout
        </MenuItem>
      </Menu>

      {/* Notifications Menu */}
      <Menu
        anchorEl={notificationAnchor}
        open={Boolean(notificationAnchor)}
        onClose={handleNotificationMenuClose}
        PaperProps={{
          elevation: 3,
          sx: {
            mt: 1.5,
            minWidth: 300,
            maxHeight: 400,
          },
        }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Notifications
          </Typography>
        </Box>
        <Divider />
        <MenuItem>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              New grant opportunity available
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Community Development Grant - $50,000
            </Typography>
          </Box>
        </MenuItem>
        <MenuItem>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              Application deadline approaching
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Youth Programs Grant closes in 3 days
            </Typography>
          </Box>
        </MenuItem>
        <MenuItem>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              New forum discussion
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Tips for successful grant applications
            </Typography>
          </Box>
        </MenuItem>
      </Menu>
    </AppBar>
  );
};

export default ProfessionalNavbar;

