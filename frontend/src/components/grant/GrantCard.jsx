import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Calendar, MapPin, Users, DollarSign, Clock, Edit, Trash2, Eye } from 'lucide-react';

const GrantCard = ({ 
  grant, 
  onView, 
  onEdit, 
  onDelete, 
  onApply, 
  showActions = true, 
  isCouncilUser = false 
}) => {
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-AU');
  };

  const getStatusColor = (status) => {
    const colors = {
      'draft': 'bg-gray-500',
      'open': 'bg-green-500',
      'closed': 'bg-red-500',
      'under_review': 'bg-yellow-500',
      'completed': 'bg-blue-500'
    };
    return colors[status] || 'bg-gray-500';
  };

  const getStatusLabel = (status) => {
    const labels = {
      'draft': 'Draft',
      'open': 'Open',
      'closed': 'Closed',
      'under_review': 'Under Review',
      'completed': 'Completed'
    };
    return labels[status] || status;
  };

  const getDaysRemaining = () => {
    if (!grant.closes_at) return null;
    const today = new Date();
    const closeDate = new Date(grant.closes_at);
    const diffTime = closeDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const daysRemaining = getDaysRemaining();
  const isClosingSoon = daysRemaining !== null && daysRemaining <= 7 && daysRemaining > 0;
  const isClosed = daysRemaining !== null && daysRemaining <= 0;

  return (
    <Card className="hover:shadow-lg transition-all duration-200 border-l-4 border-l-blue-500">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <CardTitle className="text-lg line-clamp-2 mb-2">{grant.title}</CardTitle>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Badge variant="secondary">{grant.category}</Badge>
              <Badge className={`${getStatusColor(grant.status)} text-white`}>
                {getStatusLabel(grant.status)}
              </Badge>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(grant.amount)}
            </div>
            {grant.council_name && (
              <div className="text-sm text-gray-500">{grant.council_name}</div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <p className="text-gray-700 line-clamp-3">{grant.description}</p>

        {/* Grant Details */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          {grant.opens_at && (
            <div className="flex items-center text-gray-600">
              <Calendar className="w-4 h-4 mr-2" />
              Opens: {formatDate(grant.opens_at)}
            </div>
          )}
          {grant.closes_at && (
            <div className="flex items-center text-gray-600">
              <Calendar className="w-4 h-4 mr-2" />
              Closes: {formatDate(grant.closes_at)}
            </div>
          )}
          {grant.target_beneficiaries && (
            <div className="flex items-center text-gray-600">
              <Users className="w-4 h-4 mr-2" />
              {grant.target_beneficiaries}
            </div>
          )}
          {grant.project_location && (
            <div className="flex items-center text-gray-600">
              <MapPin className="w-4 h-4 mr-2" />
              {grant.project_location}
            </div>
          )}
        </div>

        {/* Time Remaining Alert */}
        {grant.status === 'open' && daysRemaining !== null && (
          <div className={`p-3 rounded-lg ${
            isClosed 
              ? 'bg-red-50 border border-red-200' 
              : isClosingSoon 
                ? 'bg-yellow-50 border border-yellow-200' 
                : 'bg-green-50 border border-green-200'
          }`}>
            <div className="flex items-center">
              <Clock className={`w-4 h-4 mr-2 ${
                isClosed 
                  ? 'text-red-600' 
                  : isClosingSoon 
                    ? 'text-yellow-600' 
                    : 'text-green-600'
              }`} />
              <span className={`text-sm font-medium ${
                isClosed 
                  ? 'text-red-800' 
                  : isClosingSoon 
                    ? 'text-yellow-800' 
                    : 'text-green-800'
              }`}>
                {isClosed 
                  ? 'Applications closed' 
                  : daysRemaining === 1 
                    ? '1 day remaining' 
                    : `${daysRemaining} days remaining`
                }
              </span>
            </div>
          </div>
        )}

        {/* Eligibility Criteria Preview */}
        {grant.eligibility_criteria && (
          <div className="bg-blue-50 p-3 rounded-lg">
            <h4 className="text-sm font-medium text-blue-800 mb-1">Eligibility</h4>
            <p className="text-sm text-blue-700 line-clamp-2">{grant.eligibility_criteria}</p>
          </div>
        )}

        {/* Action Buttons */}
        {showActions && (
          <div className="flex justify-between items-center pt-2 border-t">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => onView && onView(grant)}
            >
              <Eye className="w-4 h-4 mr-1" />
              View Details
            </Button>
            
            <div className="flex space-x-2">
              {isCouncilUser ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onEdit && onEdit(grant)}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onDelete && onDelete(grant)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </>
              ) : (
                grant.status === 'open' && !isClosed && (
                  <Button
                    size="sm"
                    onClick={() => onApply && onApply(grant)}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    Apply Now
                  </Button>
                )
              )}
            </div>
          </div>
        )}

        {/* Contact Information */}
        {(grant.contact_email || grant.contact_phone) && (
          <div className="text-xs text-gray-500 pt-2 border-t">
            <div>Contact: {grant.contact_email}</div>
            {grant.contact_phone && <div>Phone: {grant.contact_phone}</div>}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default GrantCard;

