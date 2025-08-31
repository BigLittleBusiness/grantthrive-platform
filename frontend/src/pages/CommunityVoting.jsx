import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { 
  Vote, 
  Users, 
  Calendar, 
  TrendingUp, 
  MessageSquare,
  MapPin,
  DollarSign,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

const CommunityVoting = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [votingResults, setVotingResults] = useState(null);
  const [userVotes, setUserVotes] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Mock data for demonstration
  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      const mockCampaigns = [
        {
          id: 1,
          title: "2024 Community Grant Priorities",
          description: "Help us decide which community projects should receive funding priority in 2024. Your voice matters in shaping our community's future.",
          start_date: "2024-08-01T00:00:00Z",
          end_date: "2024-09-15T23:59:59Z",
          max_votes_per_user: 3,
          total_votes: 1247,
          unique_voters: 892,
          status: "active",
          options: [
            {
              id: 1,
              title: "Community Sports Complex Upgrade",
              description: "Modernize our local sports facilities with new equipment, improved lighting, and accessible amenities for all community members.",
              category: "Recreation & Sports",
              estimated_budget: 150000,
              priority_level: "High",
              image_url: "/images/sports-complex.jpg",
              vote_count: 324,
              percentage: 26.0
            },
            {
              id: 2,
              title: "Youth Arts & Culture Center",
              description: "Create a dedicated space for young artists to learn, create, and showcase their talents through workshops and exhibitions.",
              category: "Arts & Culture",
              estimated_budget: 120000,
              priority_level: "High",
              image_url: "/images/arts-center.jpg",
              vote_count: 298,
              percentage: 23.9
            },
            {
              id: 3,
              title: "Community Garden Network",
              description: "Establish multiple community gardens across different neighborhoods to promote sustainable living and community connection.",
              category: "Environment",
              estimated_budget: 75000,
              priority_level: "Medium",
              image_url: "/images/community-garden.jpg",
              vote_count: 267,
              percentage: 21.4
            },
            {
              id: 4,
              title: "Senior Citizens Support Hub",
              description: "Develop a comprehensive support center offering health services, social activities, and technology training for seniors.",
              category: "Community Services",
              estimated_budget: 200000,
              priority_level: "High",
              image_url: "/images/senior-hub.jpg",
              vote_count: 245,
              percentage: 19.6
            },
            {
              id: 5,
              title: "Public Wi-Fi Infrastructure",
              description: "Install free public Wi-Fi hotspots in parks, community centers, and public spaces to improve digital accessibility.",
              category: "Technology",
              estimated_budget: 90000,
              priority_level: "Medium",
              image_url: "/images/wifi-infrastructure.jpg",
              vote_count: 113,
              percentage: 9.1
            }
          ]
        }
      ];
      
      setCampaigns(mockCampaigns);
      setSelectedCampaign(mockCampaigns[0]);
      setLoading(false);
    }, 1000);
  }, []);

  const handleVote = async (optionId) => {
    try {
      // Check if user has reached vote limit
      const currentVotes = Object.keys(userVotes).length;
      if (currentVotes >= selectedCampaign.max_votes_per_user) {
        setError(`You can only vote for ${selectedCampaign.max_votes_per_user} options.`);
        return;
      }

      // Toggle vote
      const newVotes = { ...userVotes };
      if (newVotes[optionId]) {
        delete newVotes[optionId];
      } else {
        newVotes[optionId] = true;
      }
      
      setUserVotes(newVotes);
      setError(null);
      
      // In real implementation, this would call the API
      console.log('Vote submitted for option:', optionId);
      
    } catch (err) {
      setError('Failed to submit vote. Please try again.');
    }
  };

  const submitAllVotes = async () => {
    try {
      setLoading(true);
      
      // In real implementation, submit all votes to API
      const votePromises = Object.keys(userVotes).map(optionId => {
        return fetch(`/api/community/voting/campaigns/${selectedCampaign.id}/vote`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            option_id: parseInt(optionId),
            postcode: '2000', // Would get from user input
            age_group: '25-34' // Would get from user input
          })
        });
      });
      
      await Promise.all(votePromises);
      
      // Show success message
      alert('Your votes have been submitted successfully!');
      setUserVotes({});
      
    } catch (err) {
      setError('Failed to submit votes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-AU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Recreation & Sports': 'bg-blue-100 text-blue-800',
      'Arts & Culture': 'bg-purple-100 text-purple-800',
      'Environment': 'bg-green-100 text-green-800',
      'Community Services': 'bg-orange-100 text-orange-800',
      'Technology': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'High': 'bg-red-100 text-red-800',
      'Medium': 'bg-yellow-100 text-yellow-800',
      'Low': 'bg-green-100 text-green-800'
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading voting campaigns...</p>
        </div>
      </div>
    );
  }

  if (!selectedCampaign) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <Vote className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">No Active Voting Campaigns</h2>
          <p className="text-gray-600">Check back later for new community voting opportunities.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <Vote className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Community Voting</h1>
        </div>
        <p className="text-gray-600 text-lg">
          Have your say in shaping our community's future. Vote for the projects that matter most to you.
        </p>
      </div>

      {/* Campaign Overview */}
      <Card className="mb-8">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-2xl mb-2">{selectedCampaign.title}</CardTitle>
              <p className="text-gray-600 mb-4">{selectedCampaign.description}</p>
            </div>
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
              <CheckCircle className="h-4 w-4 mr-1" />
              Active
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="flex items-center gap-3">
              <Calendar className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm text-gray-500">Voting Period</p>
                <p className="font-semibold">
                  {formatDate(selectedCampaign.start_date)} - {formatDate(selectedCampaign.end_date)}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Users className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm text-gray-500">Participants</p>
                <p className="font-semibold">{selectedCampaign.unique_voters.toLocaleString()} voters</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <TrendingUp className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-sm text-gray-500">Total Votes</p>
                <p className="font-semibold">{selectedCampaign.total_votes.toLocaleString()} votes</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Vote className="h-5 w-5 text-orange-600" />
              <div>
                <p className="text-sm text-gray-500">Your Votes</p>
                <p className="font-semibold">
                  {Object.keys(userVotes).length} / {selectedCampaign.max_votes_per_user}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Voting Options */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {selectedCampaign.options.map((option) => (
          <Card 
            key={option.id} 
            className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${
              userVotes[option.id] ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
            }`}
            onClick={() => handleVote(option.id)}
          >
            <CardHeader>
              <div className="flex items-start justify-between mb-3">
                <CardTitle className="text-xl">{option.title}</CardTitle>
                <div className="flex items-center gap-2">
                  {userVotes[option.id] && (
                    <CheckCircle className="h-5 w-5 text-blue-600" />
                  )}
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mb-3">
                <Badge className={getCategoryColor(option.category)}>
                  {option.category}
                </Badge>
                <Badge className={getPriorityColor(option.priority_level)}>
                  {option.priority_level} Priority
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">{option.description}</p>
              
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-green-600" />
                  <span className="font-semibold text-green-700">
                    {formatCurrency(option.estimated_budget)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-blue-600" />
                  <span className="font-semibold">
                    {option.vote_count} votes ({option.percentage}%)
                  </span>
                </div>
              </div>
              
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Community Support</span>
                  <span>{option.percentage}%</span>
                </div>
                <Progress value={option.percentage} className="h-2" />
              </div>
              
              <Button 
                variant={userVotes[option.id] ? "default" : "outline"}
                className="w-full"
                onClick={(e) => {
                  e.stopPropagation();
                  handleVote(option.id);
                }}
              >
                {userVotes[option.id] ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Voted
                  </>
                ) : (
                  <>
                    <Vote className="h-4 w-4 mr-2" />
                    Vote for this project
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Submit Votes */}
      {Object.keys(userVotes).length > 0 && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-blue-900 mb-1">
                  Ready to submit your votes?
                </h3>
                <p className="text-blue-700">
                  You have selected {Object.keys(userVotes).length} project{Object.keys(userVotes).length !== 1 ? 's' : ''} to support.
                </p>
              </div>
              <Button 
                onClick={submitAllVotes}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Submitting...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Submit My Votes
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Information Footer */}
      <div className="mt-12 p-6 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">How Community Voting Works</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-gray-600">
          <div className="flex items-start gap-3">
            <Vote className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <p className="font-semibold text-gray-900 mb-1">Cast Your Votes</p>
              <p>Select up to {selectedCampaign.max_votes_per_user} projects that you believe should receive priority funding.</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Users className="h-5 w-5 text-green-600 mt-0.5" />
            <div>
              <p className="font-semibold text-gray-900 mb-1">Community Decision</p>
              <p>Your votes are combined with other community members to determine funding priorities.</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="h-5 w-5 text-purple-600 mt-0.5" />
            <div>
              <p className="font-semibold text-gray-900 mb-1">See Results</p>
              <p>Track voting progress in real-time and see how your community's priorities are shaping up.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommunityVoting;

