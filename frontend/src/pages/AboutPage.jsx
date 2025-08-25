import React from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  ArrowRight,
  Lightbulb,
  Shield,
  Users,
  Lock,
  Target,
  Heart,
  Globe,
  Award
} from 'lucide-react';

const AboutPage = () => {
  const teamMembers = [
    {
      name: 'Sarah Johnson',
      role: 'CEO',
      experience: 'Brings over 15 years of experience in public administration.',
      image: '/api/placeholder/150/150',
      bio: 'Former Director of Community Services with extensive experience in grant management and public sector innovation.'
    },
    {
      name: 'David Kim',
      role: 'CTO',
      experience: 'Leads the technology strategy with a focus on scalable solutions.',
      image: '/api/placeholder/150/150',
      bio: 'Software architect with 12+ years building enterprise platforms for government and non-profit sectors.'
    },
    {
      name: 'Maria Garcia',
      role: 'CFO',
      experience: 'Oversees expertise in financial management and strategic planning.',
      image: '/api/placeholder/150/150',
      bio: 'Former finance director with deep understanding of public sector budgeting and grant administration.'
    },
    {
      name: 'James Smith',
      role: 'COO',
      experience: 'Oversees daily operations and expertise in process optimization.',
      image: '/api/placeholder/150/150',
      bio: 'Operations specialist focused on streamlining workflows and improving organizational efficiency.'
    }
  ];

  const values = [
    {
      icon: <Lightbulb className="h-8 w-8 text-blue-600" />,
      title: 'Innovation',
      description: 'We commit to develop cutting-edge solutions for grant management.'
    },
    {
      icon: <Shield className="h-8 w-8 text-blue-600" />,
      title: 'Transparency',
      description: 'We believe in open and complete transparency in all our interactions.'
    },
    {
      icon: <Users className="h-8 w-8 text-blue-600" />,
      title: 'Community Focus',
      description: 'We understand and prioritize the unique needs of local councils.'
    },
    {
      icon: <Lock className="h-8 w-8 text-blue-600" />,
      title: 'Security',
      description: 'We prioritize robust security measures to protect sensitive data.'
    }
  ];

  const stats = [
    { number: '1,200+', label: 'Clients Served' },
    { number: '50,000', label: 'Grants Processed' },
    { number: '$750M', label: 'Funding Distributed' },
    { number: '99.9%', label: 'Uptime' }
  ];

  const milestones = [
    {
      year: '2020',
      title: 'Company Founded',
      description: 'Started with a vision to transform grant management for Australian councils'
    },
    {
      year: '2021',
      title: 'First 100 Clients',
      description: 'Reached our first major milestone with councils across three states'
    },
    {
      year: '2022',
      title: 'Platform 2.0 Launch',
      description: 'Introduced AI-powered features and advanced analytics capabilities'
    },
    {
      year: '2023',
      title: 'International Expansion',
      description: 'Extended services to New Zealand councils and organizations'
    },
    {
      year: '2024',
      title: 'Enterprise Features',
      description: 'Launched enterprise-grade security and multi-tenant architecture'
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-blue-700 text-white px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="text-2xl font-bold">GAP</div>
          <div className="hidden md:flex space-x-8">
            <a href="#features" className="hover:text-blue-200 transition-colors">Features</a>
            <a href="#pricing" className="hover:text-blue-200 transition-colors">Pricing</a>
            <a href="#about" className="hover:text-blue-200 transition-colors">About</a>
            <a href="#contact" className="hover:text-blue-200 transition-colors">Contact</a>
          </div>
          <Button className="bg-yellow-500 hover:bg-yellow-600 text-black font-semibold">
            Get Started
          </Button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 bg-gradient-to-r from-blue-50 to-blue-100">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Our Mission
            </h1>
            <p className="text-xl text-gray-700 max-w-3xl mx-auto mb-8">
              We are transforming grant management so communities can thrive.
            </p>
            <p className="text-lg text-gray-600 max-w-4xl mx-auto mb-8">
              GAP provides an innovative platform that empowers local councils to efficiently manage and distribute grants, 
              ensuring resources reach those who need them most.
            </p>
            <p className="text-lg text-gray-600 max-w-4xl mx-auto">
              Our mission is to foster positive change and sustainable development through seamless technology.
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl font-bold text-blue-700 mb-2">{stat.number}</div>
                <div className="text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-4xl font-bold text-gray-900 mb-16 text-center">
            Team
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {teamMembers.map((member, index) => (
              <Card key={index} className="text-center">
                <CardContent className="p-6">
                  <div className="w-24 h-24 bg-gray-200 rounded-full mx-auto mb-4 overflow-hidden">
                    <img 
                      src={member.image} 
                      alt={member.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-1">
                    {member.name}
                  </h3>
                  <p className="text-blue-600 font-medium mb-3">
                    {member.role}
                  </p>
                  <p className="text-sm text-gray-600 mb-3">
                    {member.experience}
                  </p>
                  <p className="text-xs text-gray-500">
                    {member.bio}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Company Values */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-4xl font-bold text-gray-900 mb-16 text-center">
            Company Values
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {values.map((value, index) => (
              <div key={index} className="text-center">
                <div className="flex justify-center mb-4">
                  {value.icon}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  {value.title}
                </h3>
                <p className="text-gray-600">
                  {value.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-4xl font-bold text-gray-900 mb-16 text-center">
            Our Journey
          </h2>
          <div className="space-y-8">
            {milestones.map((milestone, index) => (
              <div key={index} className="flex gap-6">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                    {milestone.year.slice(-2)}
                  </div>
                </div>
                <div className="flex-grow">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-semibold text-gray-900">
                      {milestone.title}
                    </h3>
                    <Badge variant="outline" className="text-blue-600 border-blue-600">
                      {milestone.year}
                    </Badge>
                  </div>
                  <p className="text-gray-600">
                    {milestone.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Join Our Platform CTA */}
      <section className="py-20 bg-blue-700 text-white">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold mb-6">
            Join Our Platform
          </h2>
          <p className="text-xl mb-8 text-blue-100">
            Ready to transform how your council manages grants? Partner with GAP to drive positive change in your community.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-yellow-500 hover:bg-yellow-600 text-black font-semibold">
              Start Free Trial
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-blue-700">
              Schedule Demo
            </Button>
          </div>
          <p className="text-sm text-blue-200 mt-4">
            No credit card required • 30-day free trial • Cancel anytime
          </p>
        </div>
      </section>

      {/* Awards & Recognition */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Awards & Recognition
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <Award className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                GovTech Innovation Award 2023
              </h3>
              <p className="text-gray-600">
                Recognized for excellence in government technology solutions
              </p>
            </div>
            <div className="text-center">
              <Globe className="h-12 w-12 text-blue-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Best SaaS Platform 2023
              </h3>
              <p className="text-gray-600">
                Australian Software Industry Association award winner
              </p>
            </div>
            <div className="text-center">
              <Heart className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Community Impact Award 2024
              </h3>
              <p className="text-gray-600">
                Recognized for positive impact on local communities
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="text-2xl font-bold mb-4">GAP</div>
              <p className="text-gray-400">
                Transforming grant management for councils and communities across Australia and New Zealand.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Integrations</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Press</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API Reference</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Status</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Grant Application Portal (GAP). All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AboutPage;

