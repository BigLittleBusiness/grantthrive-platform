import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Link,
  Alert,
  Divider,
  Chip,
  Avatar,
  Container,
  Grid,
  Paper,
} from '@mui/material';
import {
  Email,
  Lock,
  Visibility,
  VisibilityOff,
  Business,
  People,
  EmojiEvents,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { useAuth } from '../contexts/AuthContext';

const LoginContainer = styled(Container)(({ theme }) => ({
  minHeight: '100vh',
  display: 'flex',
  alignItems: 'center',
  background: `linear-gradient(135deg, ${theme.palette.primary.main}15 0%, ${theme.palette.info.main}10 100%)`,
}));

const LoginCard = styled(Card)(({ theme }) => ({
  borderRadius: 16,
  boxShadow: '0px 8px 32px rgba(0, 0, 0, 0.12)',
  overflow: 'visible',
  position: 'relative',
}));

const FeatureCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  borderRadius: 12,
  textAlign: 'center',
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: theme.spacing(2),
  transition: 'all 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: '0px 8px 24px rgba(0, 0, 0, 0.12)',
  },
}));

const ProfessionalLogin = () => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await login(formData.email, formData.password);
      if (!result.success) {
        setError(result.message || 'Login failed');
      }
    } catch (err) {
      setError('An error occurred during login');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (role) => {
    setLoading(true);
    setError('');

    const demoCredentials = {
      council_admin: { email: 'admin@council.gov.au', password: 'demo123' },
      community_member: { email: 'member@community.org.au', password: 'demo123' },
      professional: { email: 'consultant@professional.com.au', password: 'demo123' },
    };

    try {
      const creds = demoCredentials[role];
      const result = await login(creds.email, creds.password);
      if (!result.success) {
        setError(result.message || 'Demo login failed');
      }
    } catch (err) {
      setError('Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <LoginContainer maxWidth="lg">
      <Grid container spacing={4} alignItems="center">
        {/* Left Side - Features */}
        <Grid item xs={12} md={6}>
          <Box sx={{ mb: 4 }}>
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <Avatar
                sx={{
                  width: 48,
                  height: 48,
                  bgcolor: 'primary.main',
                }}
              >
                <Business />
              </Avatar>
              <Typography variant="h3" sx={{ fontWeight: 700, color: 'primary.main' }}>
                GrantThrive
              </Typography>
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
              Transform Your Grant Management Experience
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
              Join Australia's leading grant management platform. Connect councils, 
              community organizations, and professional services in one powerful ecosystem.
            </Typography>
          </Box>

          <Grid container spacing={3}>
            <Grid item xs={12} sm={4}>
              <FeatureCard elevation={2}>
                <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
                  <Business />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  537 Councils
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Connected across Australia
                </Typography>
              </FeatureCard>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FeatureCard elevation={2}>
                <Avatar sx={{ bgcolor: 'success.main', width: 56, height: 56 }}>
                  <People />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  10,000+
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Community organizations
                </Typography>
              </FeatureCard>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FeatureCard elevation={2}>
                <Avatar sx={{ bgcolor: 'info.main', width: 56, height: 56 }}>
                  <EmojiEvents />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  $2.5B+
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Grants managed annually
                </Typography>
              </FeatureCard>
            </Grid>
          </Grid>
        </Grid>

        {/* Right Side - Login Form */}
        <Grid item xs={12} md={6}>
          <LoginCard>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                Welcome Back
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                Sign in to your GrantThrive account
              </Typography>

              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}

              <Box component="form" onSubmit={handleSubmit}>
                <TextField
                  fullWidth
                  label="Email Address"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  sx={{ mb: 3 }}
                  InputProps={{
                    startAdornment: <Email sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                />

                <TextField
                  fullWidth
                  label="Password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleChange}
                  required
                  sx={{ mb: 3 }}
                  InputProps={{
                    startAdornment: <Lock sx={{ mr: 1, color: 'text.secondary' }} />,
                    endAdornment: (
                      <Button
                        onClick={() => setShowPassword(!showPassword)}
                        sx={{ minWidth: 'auto', p: 1 }}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </Button>
                    ),
                  }}
                />

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  size="large"
                  disabled={loading}
                  sx={{ mb: 3, py: 1.5 }}
                >
                  {loading ? 'Signing In...' : 'Sign In'}
                </Button>
              </Box>

              <Divider sx={{ my: 3 }}>
                <Chip label="Or try a demo account" size="small" />
              </Divider>

              <Box display="flex" flexDirection="column" gap={2}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => handleDemoLogin('council_admin')}
                  disabled={loading}
                  startIcon={<Business />}
                >
                  Demo: Council Administrator
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => handleDemoLogin('community_member')}
                  disabled={loading}
                  startIcon={<People />}
                >
                  Demo: Community Member
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => handleDemoLogin('professional')}
                  disabled={loading}
                  startIcon={<EmojiEvents />}
                >
                  Demo: Professional Consultant
                </Button>
              </Box>

              <Box textAlign="center" sx={{ mt: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Don't have an account?{' '}
                  <Link href="/register" sx={{ fontWeight: 600 }}>
                    Sign up here
                  </Link>
                </Typography>
              </Box>
            </CardContent>
          </LoginCard>
        </Grid>
      </Grid>
    </LoginContainer>
  );
};

export default ProfessionalLogin;

