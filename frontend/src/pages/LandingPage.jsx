import React from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  Brain, 
  Building2, 
  Users, 
  BarChart3, 
  Shield, 
  Lock, 
  CheckCircle,
  ArrowRight,
  Star,
  Quote
} from 'lucide-react';

const LandingPage = () => {
  const features = [
    {
      icon: <Brain className="h-8 w-8 text-green-600" />,
      title: "AI-Assisted Grant Creation",
      description: "Intelligent grant program creation with AI-powered suggestions and templates"
    },
    {
      icon: <Building2 className="h-8 w-8 text-green-600" />,
      title: "Multi-Tenant Architecture",
      description: "Secure, scalable platform supporting multiple councils and organizations"
    },
    {
      icon: <Users className="h-8 w-8 text-green-600" />,
      title: "Community Building Tools",
      description: "Foster stronger community connections through integrated collaboration features"
    },
    {
      icon: <BarChart3 className="h-8 w-8 text-green-600" />,
      title: "Advanced Analytics",
      description: "Comprehensive reporting and insights to optimize your grant programs"
    }
  ];

  const trustFeatures = [
    {
      icon: <Shield className="h-6 w-6 text-blue-600" />,
      title: "GDPR Compliant",
      description: "Full compliance with data protection regulations"
    },
    {
      icon: <Lock className="h-6 w-6 text-blue-600" />,
      title: "Secure",
      description: "Enterprise-grade security and encryption"
    },
    {
      icon: <CheckCircle className="h-6 w-6 text-green-600" />,
      title: "99.9% Uptime",
      description: "Reliable platform you can depend on"
    }
  ];

  const clients = [
    { name: "Riverview Council", logo: "RC" },
    { name: "Greensboro Council", logo: "GC" },
    { name: "Littlewood Council", logo: "LC" },
    { name: "Clearwater Council", logo: "CC" }
  ];

  const testimonials = [
    {
      quote: "GrantThrive has transformed how we manage our community grants. The AI-assisted creation saves us hours of work, and our community engagement has increased by 40%.",
      author: "Sarah Mitchell",
      position: "Grants Manager",
      organization: "City of Melbourne"
    },
    {
      quote: "The analytics and reporting features give us insights we never had before. We can now make data-driven decisions about our grant programs.",
      author: "Michael Chen",
      position: "Community Services Director",
      organization: "Brisbane City Council"
    },
    {
      quote: "Our application approval time has decreased by 60% since implementing GrantThrive. The workflow automation is incredible.",
      author: "Emma Rodriguez",
      position: "Senior Grants Officer",
      organization: "City of Perth"
    }
  ];

  const stats = [
    { number: "500+", label: "Councils Served" },
    { number: "$2.5B", label: "Grants Processed" },
    { number: "50,000+", label: "Applications Managed" },
    { number: "99.9%", label: "Uptime Guarantee" }
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
      <section className="bg-gradient-to-r from-blue-700 to-blue-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="text-5xl font-bold mb-6 leading-tight">
              Transform Your Grant Management Process
            </h1>
            <p className="text-xl mb-8 text-blue-100">
              Streamline your grant applications and build stronger community connections with our AI-powered platform.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" className="bg-yellow-500 hover:bg-yellow-600 text-black font-semibold">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-blue-700">
                Watch Demo
              </Button>
            </div>
          </div>
          <div className="relative">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-8">
              <img 
                src="/api/placeholder/500/300" 
                alt="Diverse community members smiling" 
                className="rounded-lg w-full h-64 object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl font-bold text-blue-700 mb-2">{stat.number}</div>
                <div className="text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-16">
            <div>
              <h2 className="text-4xl font-bold text-gray-900 mb-8">Features</h2>
              <div className="grid gap-8">
                {features.map((feature, index) => (
                  <div key={index} className="flex gap-4">
                    <div className="flex-shrink-0">
                      {feature.icon}
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-gray-600">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h2 className="text-4xl font-bold text-gray-900 mb-8">What our clients say</h2>
              <div className="grid gap-6">
                {clients.map((client, index) => (
                  <div key={index} className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                    <div className="w-12 h-12 bg-gray-300 rounded-lg flex items-center justify-center font-semibold text-gray-700">
                      {client.logo}
                    </div>
                    <div className="font-medium text-gray-900">{client.name}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Features */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8">
            {trustFeatures.map((feature, index) => (
              <div key={index} className="text-center">
                <div className="flex justify-center mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-16">
            Trusted by Leading Councils
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="p-6">
                <CardContent className="p-0">
                  <Quote className="h-8 w-8 text-blue-600 mb-4" />
                  <p className="text-gray-600 mb-6 italic">
                    "{testimonial.quote}"
                  </p>
                  <div>
                    <div className="font-semibold text-gray-900">
                      {testimonial.author}
                    </div>
                    <div className="text-sm text-gray-600">
                      {testimonial.position}
                    </div>
                    <div className="text-sm text-blue-600">
                      {testimonial.organization}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-blue-700 text-white">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold mb-6">
            Ready to Transform Your Grant Management?
          </h2>
          <p className="text-xl mb-8 text-blue-100">
            Join hundreds of councils already using GrantThrive to streamline their grant processes and build stronger communities.
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

export default LandingPage;

