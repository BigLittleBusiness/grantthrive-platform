import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  Button,
  IconButton,
  Avatar,
  Divider,
} from '@mui/material';
import {
  BookmarkBorder,
  Bookmark,
  Share,
  AccessTime,
  AttachMoney,
  LocationOn,
  Person,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const StyledCard = styled(Card)(({ theme }) => ({
  borderRadius: 12,
  boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.08)',
  transition: 'all 0.3s ease-in-out',
  '&:hover': {
    boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.12)',
    transform: 'translateY(-2px)',
  },
}));

const StatusChip = styled(Chip)(({ theme, status }) => ({
  fontWeight: 500,
  fontSize: '0.75rem',
  height: 24,
  ...(status === 'open' && {
    backgroundColor: theme.palette.success.main,
    color: theme.palette.success.contrastText,
  }),
  ...(status === 'closing-soon' && {
    backgroundColor: theme.palette.warning.main,
    color: theme.palette.warning.contrastText,
  }),
  ...(status === 'closed' && {
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText,
  }),
  ...(status === 'draft' && {
    backgroundColor: theme.palette.grey[400],
    color: theme.palette.grey[800],
  }),
}));

const GrantThriveCard = ({
  title,
  description,
  amount,
  deadline,
  status = 'open',
  category,
  location,
  applicants,
  isBookmarked = false,
  onBookmark,
  onShare,
  onApply,
  onView,
  variant = 'grant', // grant, application, success-story, professional
  ...props
}) => {
  const getStatusLabel = (status) => {
    switch (status) {
      case 'open':
        return 'Open';
      case 'closing-soon':
        return 'Closing Soon';
      case 'closed':
        return 'Closed';
      case 'draft':
        return 'Draft';
      case 'approved':
        return 'Approved';
      case 'rejected':
        return 'Rejected';
      case 'under-review':
        return 'Under Review';
      default:
        return status;
    }
  };

  const formatAmount = (amount) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return `$${amount.toLocaleString()}`;
  };

  const formatDeadline = (deadline) => {
    const date = new Date(deadline);
    const now = new Date();
    const diffTime = date - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return 'Closed';
    } else if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Tomorrow';
    } else if (diffDays <= 7) {
      return `${diffDays} days left`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <StyledCard {...props}>
      <CardContent sx={{ pb: 1 }}>
        {/* Header with status and actions */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <StatusChip 
            label={getStatusLabel(status)} 
            status={status}
            size="small"
          />
          <Box>
            <IconButton 
              size="small" 
              onClick={onBookmark}
              sx={{ color: isBookmarked ? 'primary.main' : 'text.secondary' }}
            >
              {isBookmarked ? <Bookmark /> : <BookmarkBorder />}
            </IconButton>
            <IconButton size="small" onClick={onShare} sx={{ color: 'text.secondary' }}>
              <Share />
            </IconButton>
          </Box>
        </Box>

        {/* Title and Description */}
        <Typography variant="h6" component="h3" gutterBottom sx={{ fontWeight: 600 }}>
          {title}
        </Typography>
        <Typography 
          variant="body2" 
          color="text.secondary" 
          sx={{ 
            mb: 2,
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {description}
        </Typography>

        {/* Category */}
        {category && (
          <Chip 
            label={category} 
            size="small" 
            variant="outlined"
            sx={{ mb: 2, mr: 1 }}
          />
        )}

        <Divider sx={{ my: 2 }} />

        {/* Grant Details */}
        <Box display="flex" flexDirection="column" gap={1}>
          {amount && (
            <Box display="flex" alignItems="center" gap={1}>
              <AttachMoney sx={{ fontSize: 18, color: 'success.main' }} />
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {formatAmount(amount)}
              </Typography>
            </Box>
          )}
          
          {deadline && (
            <Box display="flex" alignItems="center" gap={1}>
              <AccessTime sx={{ fontSize: 18, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                {formatDeadline(deadline)}
              </Typography>
            </Box>
          )}
          
          {location && (
            <Box display="flex" alignItems="center" gap={1}>
              <LocationOn sx={{ fontSize: 18, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                {location}
              </Typography>
            </Box>
          )}
          
          {applicants !== undefined && (
            <Box display="flex" alignItems="center" gap={1}>
              <Person sx={{ fontSize: 18, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                {applicants} applicants
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>

      {/* Actions */}
      <CardActions sx={{ px: 2, pb: 2, pt: 0 }}>
        <Button 
          variant="contained" 
          fullWidth 
          onClick={onApply}
          sx={{ mr: 1 }}
        >
          {variant === 'grant' ? 'Apply Now' : 'View Details'}
        </Button>
        <Button 
          variant="outlined" 
          onClick={onView}
          sx={{ minWidth: 'auto', px: 2 }}
        >
          View
        </Button>
      </CardActions>
    </StyledCard>
  );
};

export default GrantThriveCard;

