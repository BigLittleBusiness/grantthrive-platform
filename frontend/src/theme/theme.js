import { createTheme } from '@mui/material/styles';

// GrantThrive Design System Theme
export const grantThriveTheme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // GrantThrive Blue
      light: '#42a5f5',
      dark: '#1565c0',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#4caf50', // Success Green
      light: '#81c784',
      dark: '#388e3c',
      contrastText: '#ffffff',
    },
    success: {
      main: '#4caf50', // Success Green
      light: '#81c784',
      dark: '#388e3c',
    },
    info: {
      main: '#00acc1', // Growth Teal
      light: '#4dd0e1',
      dark: '#00838f',
    },
    warning: {
      main: '#ff9800', // Warning Amber
      light: '#ffb74d',
      dark: '#f57c00',
    },
    error: {
      main: '#f44336', // Error Red
      light: '#e57373',
      dark: '#d32f2f',
    },
    innovation: {
      main: '#7b1fa2', // Innovation Purple
      light: '#ba68c8',
      dark: '#4a148c',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.6,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.43,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  spacing: 8,
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 24px',
          fontSize: '0.875rem',
          fontWeight: 500,
          textTransform: 'none',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)',
          },
        },
        contained: {
          '&:hover': {
            boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.15)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.08)',
          '&:hover': {
            boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.12)',
            transform: 'translateY(-2px)',
            transition: 'all 0.3s ease-in-out',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: 'rgba(0, 0, 0, 0.87)',
          boxShadow: '0px 1px 3px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#fafafa',
          borderRight: '1px solid rgba(0, 0, 0, 0.08)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: '#1976d2',
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          fontWeight: 500,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          fontSize: '0.875rem',
        },
      },
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 960,
      lg: 1280,
      xl: 1920,
    },
  },
});

// Custom theme extensions
export const customColors = {
  grantThriveBlue: '#1976d2',
  successGreen: '#4caf50',
  growthTeal: '#00acc1',
  innovationPurple: '#7b1fa2',
  warningAmber: '#ff9800',
  errorRed: '#f44336',
  neutralGray: '#757575',
};

// Elevation system for consistent shadows
export const elevations = {
  card: '0px 2px 8px rgba(0, 0, 0, 0.08)',
  cardHover: '0px 4px 16px rgba(0, 0, 0, 0.12)',
  modal: '0px 8px 32px rgba(0, 0, 0, 0.16)',
  dropdown: '0px 4px 12px rgba(0, 0, 0, 0.1)',
};

// Animation system
export const animations = {
  cardHover: {
    transform: 'translateY(-2px)',
    transition: 'all 0.3s ease-in-out',
  },
  fadeIn: {
    animation: 'fadeIn 0.3s ease-in-out',
  },
  slideUp: {
    animation: 'slideUp 0.4s ease-out',
  },
};

export default grantThriveTheme;

