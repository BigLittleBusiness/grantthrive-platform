import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  LinearProgress,
  IconButton,
  Paper,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  Assignment,
  EmojiEvents,
  People,
  AttachMoney,
  AccessTime,
  Notifications,
  ArrowForward,
  Add,
  Forum,
  Event,
  Star,
  CheckCircle,
  Schedule,
  Cancel,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { styled } from '@mui/material/styles';
import { useAuth } from '../contexts/AuthContext';
import GrantThriveCard from '../components/common/GrantThriveCard';

const StyledCard = styled(Card)(({ theme }) => ({
  borderRadius: 12,
  boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.08)',
  transition: 'all 0.3s ease-in-out',
  '&:hover': {
    boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.12)',
    transform: 'translateY(-2px)',
  },
}));

const MetricCard = styled(Card)(({ theme, color = 'primary' }) => ({
  borderRadius: 12,
  boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.08)',
  background: `linear-gradient(135deg, ${theme.palette[color].main}15 0%, ${theme.palette[color].main}05 100%)`,
  border: `1px solid ${theme.palette[color].main}20`,
  transition: 'all 0.3s ease-in-out',
  '&:hover': {
    boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.12)',
    transform: 'translateY(-2px)',
  },
}));

const QuickActionButton = styled(Button)(({ theme }) => ({
  borderRadius: 12,
  padding: theme.spacing(1.5, 3),
  textTransform: 'none',
  fontWeight: 600,
  boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.08)',
  '&:hover': {
    boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.12)',
    transform: 'translateY(-1px)',
  },
}));

const ProfessionalDashboard = () => {
  const theme = useTheme();
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Mock data - in real app, this would come from API
  const mockData = {
    metrics: {
      totalApplications: 12,
      activeApplications: 3,
      successRate: 75,
      totalFunding: 125000,
      pendingReviews: user?.role?.includes('council') ? 8 : 0,
      communityMembers: user?.role?.includes('council') ? 1247 : 0,
    },
    recentActivity: [
      {
        id: 1,
        type: 'application_submitted',
        title: 'Youth Development Grant Application Submitted',
        description: 'Application for $25,000 youth program funding',
        timestamp: '2 hours ago',
        status: 'pending',
      },
      {
        id: 2,
        type: 'grant_approved',
        title: 'Community Garden Grant Approved',
        description: 'Congratulations! Your application was approved for $15,000',
        timestamp: '1 day ago',
        status: 'approved',
      },
      {
        id: 3,
        type: 'forum_post',
        title: 'New Discussion: Grant Writing Tips',
        description: 'Join the conversation about successful grant applications',
        timestamp: '2 days ago',
        status: 'info',
      },
    ],
    chartData: {
      applications: [
        { month: 'Jan', submitted: 2, approved: 1, rejected: 0 },
        { month: 'Feb', submitted: 3, approved: 2, rejected: 1 },
        { month: 'Mar', submitted: 4, approved: 3, rejected: 0 },
        { month: 'Apr', submitted: 3, approved: 2, rejected: 1 },
      ],
      funding: [
        { category: 'Community Development', value: 45000, color: '#1976d2' },
        { category: 'Youth Programs', value: 35000, color: '#4caf50' },
        { category: 'Arts & Culture', value: 25000, color: '#00acc1' },
        { category: 'Environment', value: 20000, color: '#7b1fa2' },
      ],
    },
    upcomingDeadlines: [
      {
        id: 1,
        title: 'Environmental Sustainability Grant',
        deadline: '2024-02-15',
        amount: 50000,
        daysLeft: 5,
      },
      {
        id: 2,
        title: 'Community Arts Program',
        deadline: '2024-02-20',
        amount: 30000,
        daysLeft: 10,
      },
    ],
    recommendedGrants: [
      {
        id: 1,
        title: 'Digital Innovation Grant',
        description: 'Support for technology-driven community initiatives and digital literacy programs.',
        amount: 75000,
        deadline: '2024-03-01',
        category: 'Technology',
        status: 'open',
        applicants: 23,
      },
      {
        id: 2,
        title: 'Health & Wellness Initiative',
        description: 'Funding for community health programs, mental health support, and wellness activities.',
        amount: 40000,
        deadline: '2024-02-28',
        category: 'Health',
        status: 'open',
        applicants: 15,
      },
    ],
  };

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setDashboardData(mockData);
      setLoading(false);
    }, 1000);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'pending':
        return <Schedule sx={{ color: 'warning.main' }} />;
      case 'rejected':
        return <Cancel sx={{ color: 'error.main' }} />;
      default:
        return <Notifications sx={{ color: 'info.main' }} />;
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Loading Dashboard...
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Welcome Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          Welcome back, {user?.name || 'User'}! 👋
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here's what's happening with your grants and community activity.
        </Typography>
      </Box>

      {/* Quick Actions */}
      <Box sx={{ mb: 4 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <QuickActionButton
              variant="contained"
              fullWidth
              startIcon={<Add />}
              sx={{ height: 56 }}
            >
              Apply for Grant
            </QuickActionButton>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <QuickActionButton
              variant="outlined"
              fullWidth
              startIcon={<Forum />}
              sx={{ height: 56 }}
            >
              Join Discussion
            </QuickActionButton>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <QuickActionButton
              variant="outlined"
              fullWidth
              startIcon={<Event />}
              sx={{ height: 56 }}
            >
              View Events
            </QuickActionButton>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <QuickActionButton
              variant="outlined"
              fullWidth
              startIcon={<EmojiEvents />}
              sx={{ height: 56 }}
            >
              Success Stories
            </QuickActionButton>
          </Grid>
        </Grid>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard color="primary">
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    {dashboardData.metrics.totalApplications}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Applications
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
                  <Assignment />
                </Avatar>
              </Box>
            </CardContent>
          </MetricCard>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard color="success">
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main' }}>
                    {dashboardData.metrics.successRate}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Success Rate
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main', width: 56, height: 56 }}>
                  <TrendingUp />
                </Avatar>
              </Box>
            </CardContent>
          </MetricCard>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard color="info">
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'info.main' }}>
                    {formatCurrency(dashboardData.metrics.totalFunding)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Funding
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'info.main', width: 56, height: 56 }}>
                  <AttachMoney />
                </Avatar>
              </Box>
            </CardContent>
          </MetricCard>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard color="warning">
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'warning.main' }}>
                    {dashboardData.metrics.activeApplications}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Applications
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'warning.main', width: 56, height: 56 }}>
                  <AccessTime />
                </Avatar>
              </Box>
            </CardContent>
          </MetricCard>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Application Trends Chart */}
        <Grid item xs={12} lg={8}>
          <StyledCard>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Application Trends
                </Typography>
                <Button size="small" endIcon={<ArrowForward />}>
                  View Details
                </Button>
              </Box>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={dashboardData.chartData.applications}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="submitted"
                    stackId="1"
                    stroke={theme.palette.primary.main}
                    fill={theme.palette.primary.main}
                    fillOpacity={0.6}
                    name="Submitted"
                  />
                  <Area
                    type="monotone"
                    dataKey="approved"
                    stackId="2"
                    stroke={theme.palette.success.main}
                    fill={theme.palette.success.main}
                    fillOpacity={0.6}
                    name="Approved"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </StyledCard>
        </Grid>

        {/* Funding Distribution */}
        <Grid item xs={12} lg={4}>
          <StyledCard>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Funding by Category
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={dashboardData.chartData.funding}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {dashboardData.chartData.funding.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </StyledCard>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} lg={6}>
          <StyledCard>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Recent Activity
                </Typography>
                <Button size="small" endIcon={<ArrowForward />}>
                  View All
                </Button>
              </Box>
              <List>
                {dashboardData.recentActivity.map((activity, index) => (
                  <React.Fragment key={activity.id}>
                    <ListItem alignItems="flex-start" sx={{ px: 0 }}>
                      <ListItemAvatar>
                        {getStatusIcon(activity.status)}
                      </ListItemAvatar>
                      <ListItemText
                        primary={activity.title}
                        secondary={
                          <>
                            <Typography variant="body2" color="text.secondary">
                              {activity.description}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {activity.timestamp}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                    {index < dashboardData.recentActivity.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </StyledCard>
        </Grid>

        {/* Upcoming Deadlines */}
        <Grid item xs={12} lg={6}>
          <StyledCard>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Upcoming Deadlines
                </Typography>
                <Button size="small" endIcon={<ArrowForward />}>
                  View All
                </Button>
              </Box>
              <List>
                {dashboardData.upcomingDeadlines.map((deadline, index) => (
                  <React.Fragment key={deadline.id}>
                    <ListItem alignItems="flex-start" sx={{ px: 0 }}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'warning.main' }}>
                          <AccessTime />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={deadline.title}
                        secondary={
                          <>
                            <Typography variant="body2" color="text.secondary">
                              {formatCurrency(deadline.amount)} • {deadline.daysLeft} days left
                            </Typography>
                            <Chip
                              label={`${deadline.daysLeft} days left`}
                              size="small"
                              color={deadline.daysLeft <= 7 ? 'error' : 'warning'}
                              sx={{ mt: 1 }}
                            />
                          </>
                        }
                      />
                      <Button size="small" variant="outlined">
                        Apply
                      </Button>
                    </ListItem>
                    {index < dashboardData.upcomingDeadlines.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </StyledCard>
        </Grid>

        {/* Recommended Grants */}
        <Grid item xs={12}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              Recommended for You
            </Typography>
            <Button endIcon={<ArrowForward />}>
              View All Grants
            </Button>
          </Box>
          <Grid container spacing={3}>
            {dashboardData.recommendedGrants.map((grant) => (
              <Grid item xs={12} md={6} key={grant.id}>
                <GrantThriveCard
                  title={grant.title}
                  description={grant.description}
                  amount={grant.amount}
                  deadline={grant.deadline}
                  status={grant.status}
                  category={grant.category}
                  applicants={grant.applicants}
                  onApply={() => console.log('Apply to grant:', grant.id)}
                  onView={() => console.log('View grant:', grant.id)}
                  onBookmark={() => console.log('Bookmark grant:', grant.id)}
                  onShare={() => console.log('Share grant:', grant.id)}
                />
              </Grid>
            ))}
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProfessionalDashboard;

