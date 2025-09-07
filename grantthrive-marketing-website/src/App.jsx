import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { 
  Menu, 
  X, 
  ArrowRight, 
  CheckCircle, 
  Star, 
  Users, 
  Map, 
  Vote, 
  Zap, 
  Shield, 
  Smartphone, 
  BarChart3,
  Calculator,
  Download,
  Mail,
  Phone,
  MapPin,
  Clock,
  DollarSign,
  TrendingUp,
  Award,
  Target,
  Lightbulb,
  Heart,
  Globe
} from 'lucide-react'
import './App.css'

// Navigation Component
function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const location = useLocation()

  const navItems = [
    { name: 'Home', path: '/' },
    { name: 'Features', path: '/features' },
    { name: 'Pricing', path: '/pricing' },
    { name: 'ROI Calculator', path: '/roi-calculator' },
    { name: 'Resources', path: '/resources' },
    { name: 'Contact', path: '/contact' }
  ]

  return (
    <nav className="bg-white/95 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="container-custom">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">G</span>
            </div>
            <span className="text-xl font-bold text-gray-900">GrantThrive</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => (
              <Link
                key={item.name}
                to={item.path}
                className={`text-sm font-medium transition-colors hover:text-primary ${
                  location.pathname === item.path 
                    ? 'text-primary' 
                    : 'text-gray-600'
                }`}
              >
                {item.name}
              </Link>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="hidden md:flex items-center space-x-4">
            <Button variant="outline" size="sm">
              Login
            </Button>
            <Button size="sm" className="bg-primary hover:bg-primary/90">
              Get Started
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <div className="flex flex-col space-y-4">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.path}
                  className="text-sm font-medium text-gray-600 hover:text-primary"
                  onClick={() => setIsMenuOpen(false)}
                >
                  {item.name}
                </Link>
              ))}
              <div className="flex flex-col space-y-2 pt-4">
                <Button variant="outline" size="sm">
                  Login
                </Button>
                <Button size="sm" className="bg-primary hover:bg-primary/90">
                  Get Started
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}

// Hero Section Component
function HeroSection() {
  return (
    <section className="hero-gradient text-white section-padding">
      <div className="container-custom">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-8">
            <div className="space-y-4">
              <Badge className="bg-white/20 text-white border-white/30">
                🚀 Revolutionary Community Engagement
              </Badge>
              <h1 className="text-4xl lg:text-6xl font-bold leading-tight">
                Transform Your
                <span className="block text-yellow-300">Grant Management</span>
              </h1>
              <p className="text-xl text-blue-100 leading-relaxed">
                The only platform that combines powerful grant management with 
                revolutionary community engagement features. Save money, engage citizens, 
                and streamline your processes.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" className="bg-white text-primary hover:bg-gray-100">
                <Calculator className="mr-2 h-5 w-5" />
                Calculate Your ROI
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                <Users className="mr-2 h-5 w-5" />
                See Community Features
              </Button>
            </div>

            <div className="grid grid-cols-3 gap-8 pt-8">
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-300">312%</div>
                <div className="text-sm text-blue-100">Average ROI</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-300">4mo</div>
                <div className="text-sm text-blue-100">Payback Period</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-300">$7.5K+</div>
                <div className="text-sm text-blue-100">Annual Savings</div>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 animate-float">
              <div className="space-y-6">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-green-400 rounded-full flex items-center justify-center">
                    <Vote className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Community Voting</h3>
                    <p className="text-sm text-blue-100">Let citizens vote on grant priorities</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-purple-400 rounded-full flex items-center justify-center">
                    <Map className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Interactive Mapping</h3>
                    <p className="text-sm text-blue-100">Visualize grant impact across your region</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-orange-400 rounded-full flex items-center justify-center">
                    <BarChart3 className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Real-time Analytics</h3>
                    <p className="text-sm text-blue-100">Track performance and engagement</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// Features Section Component
function FeaturesSection() {
  const features = [
    {
      icon: Vote,
      title: "Community Voting System",
      description: "Revolutionary feature that lets citizens vote on grant priorities and applications, creating unprecedented transparency and engagement.",
      badge: "Exclusive to GrantThrive",
      color: "bg-blue-500"
    },
    {
      icon: Map,
      title: "Interactive Grant Mapping",
      description: "Visual mapping system showing grant locations, outcomes, and community impact across your region.",
      badge: "Exclusive to GrantThrive", 
      color: "bg-green-500"
    },
    {
      icon: Zap,
      title: "AI-Powered Grant Wizard",
      description: "Step-by-step grant creation with intelligent templates and automated workflows.",
      badge: "AI-Enhanced",
      color: "bg-purple-500"
    },
    {
      icon: BarChart3,
      title: "Real-time Analytics",
      description: "Live dashboards showing application trends, community engagement, and performance metrics.",
      badge: "Advanced Analytics",
      color: "bg-orange-500"
    },
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "Bank-grade security with compliance features for Australian and New Zealand councils.",
      badge: "Compliant",
      color: "bg-red-500"
    },
    {
      icon: Smartphone,
      title: "Mobile-First Design",
      description: "Fully responsive interface optimized for mobile devices and touch interactions.",
      badge: "Mobile Optimized",
      color: "bg-indigo-500"
    }
  ]

  return (
    <section className="section-padding bg-gray-50">
      <div className="container-custom">
        <div className="text-center space-y-4 mb-16">
          <Badge className="bg-primary/10 text-primary">Revolutionary Features</Badge>
          <h2 className="text-3xl lg:text-5xl font-bold text-gray-900">
            Features No Competitor Offers
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            GrantThrive isn't just another grant management system. We're pioneering 
            community-centric features that transform how councils engage with citizens.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <Card key={index} className="feature-card-hover border-0 shadow-lg">
              <CardHeader>
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 ${feature.color} rounded-lg flex items-center justify-center`}>
                    <feature.icon className="h-6 w-6 text-white" />
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {feature.badge}
                  </Badge>
                </div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}

// Comparison Section Component
function ComparisonSection() {
  const comparisons = [
    { feature: "Community Voting System", grantThrive: true, smartyGrants: false },
    { feature: "Interactive Grant Mapping", grantThrive: true, smartyGrants: false },
    { feature: "AI-Powered Grant Creation", grantThrive: true, smartyGrants: false },
    { feature: "Real-time Analytics Dashboard", grantThrive: true, smartyGrants: false },
    { feature: "15+ System Integrations", grantThrive: true, smartyGrants: false },
    { feature: "Mobile-Responsive Design", grantThrive: true, smartyGrants: true },
    { feature: "Basic Application Management", grantThrive: true, smartyGrants: true },
    { feature: "Document Storage", grantThrive: true, smartyGrants: true },
    { feature: "Setup & Training Included", grantThrive: true, smartyGrants: false },
    { feature: "Transparent Pricing", grantThrive: true, smartyGrants: false }
  ]

  return (
    <section className="section-padding">
      <div className="container-custom">
        <div className="text-center space-y-4 mb-16">
          <Badge className="bg-green-100 text-green-800">Competitive Advantage</Badge>
          <h2 className="text-3xl lg:text-5xl font-bold text-gray-900">
            GrantThrive vs SmartyGrants
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            See why progressive councils are switching to GrantThrive for superior 
            features and better value.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <Card className="overflow-hidden">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-green-50">
              <div className="grid grid-cols-3 gap-4">
                <div></div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center mx-auto mb-2">
                    <span className="text-white font-bold text-xl">G</span>
                  </div>
                  <h3 className="font-bold text-primary">GrantThrive</h3>
                  <Badge className="bg-green-600 text-white mt-1">Recommended</Badge>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-gray-400 rounded-full flex items-center justify-center mx-auto mb-2">
                    <span className="text-white font-bold text-xl">S</span>
                  </div>
                  <h3 className="font-bold text-gray-600">SmartyGrants</h3>
                  <Badge variant="secondary" className="mt-1">Traditional</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {comparisons.map((item, index) => (
                <div key={index} className={`grid grid-cols-3 gap-4 p-4 ${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}`}>
                  <div className="font-medium text-gray-900">{item.feature}</div>
                  <div className="text-center">
                    {item.grantThrive ? (
                      <CheckCircle className="h-6 w-6 text-green-600 mx-auto" />
                    ) : (
                      <X className="h-6 w-6 text-red-400 mx-auto" />
                    )}
                  </div>
                  <div className="text-center">
                    {item.smartyGrants ? (
                      <CheckCircle className="h-6 w-6 text-green-600 mx-auto" />
                    ) : (
                      <X className="h-6 w-6 text-red-400 mx-auto" />
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <div className="text-center mt-8">
            <Button size="lg" className="bg-primary hover:bg-primary/90">
              <Calculator className="mr-2 h-5 w-5" />
              Calculate Your Savings
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}

// ROI Section Component
function ROISection() {
  return (
    <section className="section-padding bg-gradient-to-r from-blue-600 to-green-600 text-white">
      <div className="container-custom">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-8">
            <div className="space-y-4">
              <Badge className="bg-white/20 text-white border-white/30">
                💰 Proven ROI
              </Badge>
              <h2 className="text-3xl lg:text-5xl font-bold">
                Save Money While
                <span className="block text-yellow-300">Gaining Features</span>
              </h2>
              <p className="text-xl text-blue-100">
                GrantThrive costs less than SmartyGrants while providing 320% more features. 
                See your exact savings with our ROI calculator.
              </p>
            </div>

            <div className="space-y-6">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-green-400 rounded-full flex items-center justify-center">
                  <DollarSign className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold">Lower Annual Costs</h3>
                  <p className="text-blue-100">Save 1-24% annually vs SmartyGrants</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-purple-400 rounded-full flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold">No Setup Fees</h3>
                  <p className="text-blue-100">Save $3,000-$8,000 in setup costs</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-orange-400 rounded-full flex items-center justify-center">
                  <Award className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold">More Features</h3>
                  <p className="text-blue-100">21 features vs 5 in SmartyGrants</p>
                </div>
              </div>
            </div>

            <Button size="lg" className="bg-white text-primary hover:bg-gray-100">
              <Calculator className="mr-2 h-5 w-5" />
              Calculate Your ROI Now
            </Button>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8">
            <h3 className="text-2xl font-bold mb-6 text-center">Sample ROI Results</h3>
            <div className="space-y-6">
              <div className="bg-white/20 rounded-lg p-4">
                <h4 className="font-semibold mb-2">Small Council (100 applications/year)</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>ROI: <span className="font-bold text-yellow-300">312%</span></div>
                  <div>Payback: <span className="font-bold text-yellow-300">4 months</span></div>
                  <div>Annual Savings: <span className="font-bold text-yellow-300">$7,500</span></div>
                  <div>vs SmartyGrants: <span className="font-bold text-yellow-300">$4,104/year</span></div>
                </div>
              </div>
              <div className="bg-white/20 rounded-lg p-4">
                <h4 className="font-semibold mb-2">Medium Council (300 applications/year)</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>ROI: <span className="font-bold text-yellow-300">450%+</span></div>
                  <div>Payback: <span className="font-bold text-yellow-300">3 months</span></div>
                  <div>Annual Savings: <span className="font-bold text-yellow-300">$22,500+</span></div>
                  <div>vs SmartyGrants: <span className="font-bold text-yellow-300">$12,312/year</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// CTA Section Component
function CTASection() {
  return (
    <section className="section-padding bg-gray-900 text-white">
      <div className="container-custom text-center">
        <div className="max-w-3xl mx-auto space-y-8">
          <h2 className="text-3xl lg:text-5xl font-bold">
            Ready to Transform Your
            <span className="text-gradient block">Grant Management?</span>
          </h2>
          <p className="text-xl text-gray-300">
            Join progressive councils across Australia and New Zealand who are 
            revolutionizing their grant management with GrantThrive.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-primary hover:bg-primary/90">
              <Users className="mr-2 h-5 w-5" />
              Schedule a Demo
            </Button>
            <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
              <Calculator className="mr-2 h-5 w-5" />
              Calculate ROI
            </Button>
            <Button asChild size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
              <a href="/GrantThrive_Brochure.pdf" download>
                <Download className="mr-2 h-5 w-5" />
                Download Brochure
              </a>
            </Button>
          </div>

          <div className="grid md:grid-cols-3 gap-8 pt-12">
            <div className="text-center">
              <Clock className="h-8 w-8 text-primary mx-auto mb-2" />
              <h3 className="font-semibold mb-1">Quick Setup</h3>
              <p className="text-sm text-gray-400">Go live in 2-4 weeks</p>
            </div>
            <div className="text-center">
              <Shield className="h-8 w-8 text-primary mx-auto mb-2" />
              <h3 className="font-semibold mb-1">Secure & Compliant</h3>
              <p className="text-sm text-gray-400">Enterprise-grade security</p>
            </div>
            <div className="text-center">
              <Heart className="h-8 w-8 text-primary mx-auto mb-2" />
              <h3 className="font-semibold mb-1">Ongoing Support</h3>
              <p className="text-sm text-gray-400">Dedicated success team</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// Footer Component
function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="container-custom">
        <div className="grid md:grid-cols-4 gap-8">
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">G</span>
              </div>
              <span className="text-xl font-bold">GrantThrive</span>
            </div>
            <p className="text-gray-400">
              Revolutionary grant management platform for Australian and New Zealand councils.
            </p>
            <div className="flex space-x-4">
              <Globe className="h-5 w-5 text-gray-400" />
              <Mail className="h-5 w-5 text-gray-400" />
              <Phone className="h-5 w-5 text-gray-400" />
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Product</h3>
            <ul className="space-y-2 text-gray-400">
              <li><Link to="/features" className="hover:text-white">Features</Link></li>
              <li><Link to="/pricing" className="hover:text-white">Pricing</Link></li>
              <li><Link to="/roi-calculator" className="hover:text-white">ROI Calculator</Link></li>
              <li><a href="#" className="hover:text-white">Integrations</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Resources</h3>
            <ul className="space-y-2 text-gray-400">
              <li><a href="#" className="hover:text-white">Documentation</a></li>
              <li><a href="#" className="hover:text-white">Case Studies</a></li>
              <li><a href="#" className="hover:text-white">Blog</a></li>
              <li><a href="#" className="hover:text-white">Support</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Contact</h3>
            <ul className="space-y-2 text-gray-400">
              <li className="flex items-center space-x-2">
                <Mail className="h-4 w-4" />
                <span>info@grantthrive.com.au</span>
              </li>
              <li className="flex items-center space-x-2">
                <Phone className="h-4 w-4" />
                <span>1300 GRANTS</span>
              </li>
              <li className="flex items-center space-x-2">
                <MapPin className="h-4 w-4" />
                <span>Australia & New Zealand</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; 2024 GrantThrive. All rights reserved. Transforming grant management across Australia and New Zealand.</p>
        </div>
      </div>
    </footer>
  )
}

// Home Page Component
function HomePage() {
  return (
    <div>
      <HeroSection />
      <FeaturesSection />
      <ComparisonSection />
      <ROISection />
      <CTASection />
    </div>
  )
}

// Placeholder components for other pages
function FeaturesPage() {
  return (
    <div className="section-padding">
      <div className="container-custom">
        <h1 className="text-4xl font-bold text-center mb-8">Features</h1>
        <p className="text-center text-gray-600">Detailed features page coming soon...</p>
      </div>
    </div>
  )
}

function PricingPage() {
  return (
    <div className="section-padding">
      <div className="container-custom">
        <h1 className="text-4xl font-bold text-center mb-8">Pricing</h1>
        <p className="text-center text-gray-600">Pricing page coming soon...</p>
      </div>
    </div>
  )
}

function ROICalculatorPage() {
  const [councilSize, setCouncilSize] = useState('small')
  const [applications, setApplications] = useState(100)
  const [hoursPerApp, setHoursPerApp] = useState(4.25)
  const [hourlyRate, setHourlyRate] = useState(40)
  const [techCosts, setTechCosts] = useState(3000)
  const [adminCosts, setAdminCosts] = useState(2000)
  const [communityVoting, setCommunityVoting] = useState(false)
  const [grantMapping, setGrantMapping] = useState(false)
  const [activeTab, setActiveTab] = useState('roi-summary')

  // Import calculation functions
  const calculateROI = (inputs) => {
    const currentAnnualCosts = (inputs.applications * inputs.hoursPerApp * inputs.hourlyRate) + inputs.techCosts + inputs.adminCosts
    const grantThriveAnnualCost = inputs.councilSize === 'small' ? 2400 : inputs.councilSize === 'medium' ? 6000 : 13200
    const addOnCosts = (inputs.communityVoting ? 600 : 0) + (inputs.grantMapping ? 600 : 0)
    const totalGrantThriveCost = grantThriveAnnualCost + addOnCosts
    
    const efficiencyGain = 0.45
    const newStaffCosts = currentAnnualCosts * (1 - efficiencyGain)
    const totalNewCosts = newStaffCosts + totalGrantThriveCost
    
    const annualSavings = currentAnnualCosts - totalNewCosts
    const roi = (annualSavings / totalGrantThriveCost) * 100
    const paybackMonths = Math.ceil(totalGrantThriveCost / (annualSavings / 12))
    
    return {
      currentAnnualCosts,
      totalGrantThriveCost,
      annualSavings,
      roi,
      paybackMonths,
      fiveYearSavings: annualSavings * 5
    }
  }

  const inputs = {
    councilSize,
    applications,
    hoursPerApp,
    hourlyRate,
    techCosts,
    adminCosts,
    communityVoting,
    grantMapping
  }

  const results = calculateROI(inputs)

  return (
    <div className="section-padding bg-gray-50">
      <div className="container-custom">
        <div className="text-center space-y-4 mb-12">
          <Badge className="bg-primary/10 text-primary">ROI Calculator</Badge>
          <h1 className="text-3xl lg:text-5xl font-bold text-gray-900">
            Calculate Your GrantThrive ROI
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            See exactly how much your council can save by switching to GrantThrive. 
            Adjust the inputs below to match your current situation.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* Input Form */}
          <Card className="p-6">
            <CardHeader>
              <CardTitle>Your Council Details</CardTitle>
              <CardDescription>
                Enter your current grant management costs and processes
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2">Council Size</label>
                <select 
                  value={councilSize} 
                  onChange={(e) => setCouncilSize(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="small">Small (5K-20K population)</option>
                  <option value="medium">Medium (20K-100K population)</option>
                  <option value="large">Large (100K+ population)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Grant Applications per Year: {applications}
                </label>
                <input
                  type="range"
                  min="50"
                  max="1000"
                  value={applications}
                  onChange={(e) => setApplications(Number(e.target.value))}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Hours per Application: {hoursPerApp}
                </label>
                <input
                  type="range"
                  min="2"
                  max="10"
                  step="0.25"
                  value={hoursPerApp}
                  onChange={(e) => setHoursPerApp(Number(e.target.value))}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Staff Hourly Rate (AUD): ${hourlyRate}
                </label>
                <input
                  type="range"
                  min="30"
                  max="80"
                  value={hourlyRate}
                  onChange={(e) => setHourlyRate(Number(e.target.value))}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Current Technology Costs (AUD/year): ${techCosts}
                </label>
                <input
                  type="range"
                  min="1000"
                  max="20000"
                  step="500"
                  value={techCosts}
                  onChange={(e) => setTechCosts(Number(e.target.value))}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Administrative Costs (AUD/year): ${adminCosts}
                </label>
                <input
                  type="range"
                  min="1000"
                  max="10000"
                  step="500"
                  value={adminCosts}
                  onChange={(e) => setAdminCosts(Number(e.target.value))}
                  className="w-full"
                />
              </div>

              <div className="space-y-3">
                <h3 className="font-medium">Community Engagement Add-ons</h3>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="voting"
                    checked={communityVoting}
                    onChange={(e) => setCommunityVoting(e.target.checked)}
                  />
                  <label htmlFor="voting" className="text-sm">
                    Community Voting (+$600/year)
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="mapping"
                    checked={grantMapping}
                    onChange={(e) => setGrantMapping(e.target.checked)}
                  />
                  <label htmlFor="mapping" className="text-sm">
                    Grant Mapping (+$600/year)
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          <div className="space-y-6">
            <Card className="p-6 bg-gradient-to-r from-green-50 to-blue-50">
              <CardHeader>
                <CardTitle className="text-2xl text-center">Your ROI Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-6 text-center">
                  <div>
                    <div className="text-3xl font-bold text-green-600">
                      {Math.round(results.roi)}%
                    </div>
                    <div className="text-sm text-gray-600">ROI</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-blue-600">
                      {results.paybackMonths}mo
                    </div>
                    <div className="text-sm text-gray-600">Payback Period</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-purple-600">
                      ${results.annualSavings.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">Annual Savings</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-orange-600">
                      ${results.fiveYearSavings.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">5-Year Value</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="p-6">
              <CardHeader>
                <CardTitle>Cost Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Current Annual Costs:</span>
                    <span className="font-semibold">${results.currentAnnualCosts.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>GrantThrive Annual Cost:</span>
                    <span className="font-semibold">${results.totalGrantThriveCost.toLocaleString()}</span>
                  </div>
                  <div className="border-t pt-2 flex justify-between text-lg font-bold text-green-600">
                    <span>Annual Savings:</span>
                    <span>${results.annualSavings.toLocaleString()}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="text-center space-y-4">
              <Button size="lg" className="bg-primary hover:bg-primary/90">
                <Users className="mr-2 h-5 w-5" />
                Schedule a Demo
              </Button>
              <p className="text-sm text-gray-600">
                Ready to see GrantThrive in action? Book a personalized demo.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ResourcesPage() {
  return (
    <div className="section-padding">
      <div className="container-custom">
        <h1 className="text-4xl font-bold text-center mb-8">Resources</h1>
        <p className="text-center text-gray-600">Resources page coming soon...</p>
      </div>
    </div>
  )
}

function ContactPage() {
  return (
    <div className="section-padding">
      <div className="container-custom">
        <h1 className="text-4xl font-bold text-center mb-8">Contact</h1>
        <p className="text-center text-gray-600">Contact page coming soon...</p>
      </div>
    </div>
  )
}

// Main App Component
function App() {
  return (
    <Router>
      <div className="min-h-screen bg-white">
        <Navigation />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/features" element={<FeaturesPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/roi-calculator" element={<ROICalculatorPage />} />
          <Route path="/resources" element={<ResourcesPage />} />
          <Route path="/contact" element={<ContactPage />} />
        </Routes>
        <Footer />
      </div>
    </Router>
  )
}

export default App

