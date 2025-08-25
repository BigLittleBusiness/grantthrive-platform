import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  Check, 
  X, 
  ArrowRight,
  Users,
  Database,
  Headphones,
  Shield,
  Zap,
  Building,
  Globe,
  BarChart3
} from 'lucide-react';

const PricingPage = () => {
  const [billingCycle, setBillingCycle] = useState('monthly');

  const plans = [
    {
      name: 'Starter',
      description: 'For small councils',
      monthlyPrice: 99,
      annualPrice: 990,
      popular: false,
      features: [
        'Key features',
        'Up to 10 users',
        '5 GB storage',
        'Basic support',
        'Grant creation wizard',
        'Application management',
        'Basic analytics',
        'Email notifications'
      ],
      limits: {
        users: 10,
        storage: '5 GB',
        grants: 25,
        applications: 500
      }
    },
    {
      name: 'Professional',
      description: 'For medium councils',
      monthlyPrice: 299,
      annualPrice: 2990,
      popular: true,
      features: [
        'All Starter features',
        'Up to 25 users',
        '20 GB storage',
        'Priority support',
        'Advanced analytics',
        'Community forum',
        'Custom branding',
        'API access',
        'Workflow automation',
        'Document templates'
      ],
      limits: {
        users: 25,
        storage: '20 GB',
        grants: 100,
        applications: 2500
      }
    },
    {
      name: 'Enterprise',
      description: 'For large organizations',
      monthlyPrice: 'Custom',
      annualPrice: 'Custom',
      popular: false,
      features: [
        'All Professional features',
        'Unlimited users',
        'Unlimited storage',
        'Dedicated support',
        'Custom integrations',
        'Advanced security',
        'Multi-tenant architecture',
        'White-label solution',
        'SLA guarantee',
        'Training & onboarding'
      ],
      limits: {
        users: 'Unlimited',
        storage: 'Unlimited',
        grants: 'Unlimited',
        applications: 'Unlimited'
      }
    }
  ];

  const features = [
    {
      name: 'Grant Creation Wizard',
      starter: true,
      professional: true,
      enterprise: true
    },
    {
      name: 'Application Management',
      starter: true,
      professional: true,
      enterprise: true
    },
    {
      name: 'Basic Analytics',
      starter: true,
      professional: true,
      enterprise: true
    },
    {
      name: 'Email Notifications',
      starter: true,
      professional: true,
      enterprise: true
    },
    {
      name: 'Community Forum',
      starter: false,
      professional: true,
      enterprise: true
    },
    {
      name: 'Advanced Analytics',
      starter: false,
      professional: true,
      enterprise: true
    },
    {
      name: 'Custom Branding',
      starter: false,
      professional: true,
      enterprise: true
    },
    {
      name: 'API Access',
      starter: false,
      professional: true,
      enterprise: true
    },
    {
      name: 'Workflow Automation',
      starter: false,
      professional: true,
      enterprise: true
    },
    {
      name: 'White-label Solution',
      starter: false,
      professional: false,
      enterprise: true
    },
    {
      name: 'Custom Integrations',
      starter: false,
      professional: false,
      enterprise: true
    },
    {
      name: 'SLA Guarantee',
      starter: false,
      professional: false,
      enterprise: true
    }
  ];

  const faqs = [
    {
      question: 'Can I switch plans at any time?',
      answer: 'Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately, and billing is prorated.'
    },
    {
      question: 'What payment methods do you accept?',
      answer: 'We accept all major credit cards, bank transfers, and can arrange invoicing for annual plans.'
    },
    {
      question: 'Is there a free trial?',
      answer: 'Yes, we offer a 30-day free trial with full access to Professional features. No credit card required.'
    },
    {
      question: 'What kind of support do you provide?',
      answer: 'Starter plans include email support, Professional plans get priority support, and Enterprise customers receive dedicated support with guaranteed response times.'
    },
    {
      question: 'Can I cancel anytime?',
      answer: 'Yes, you can cancel your subscription at any time. Your access continues until the end of your billing period.'
    },
    {
      question: 'Do you offer discounts for annual billing?',
      answer: 'Yes, annual billing provides approximately 17% savings compared to monthly billing.'
    }
  ];

  const getPrice = (plan) => {
    if (plan.monthlyPrice === 'Custom') return 'Custom';
    return billingCycle === 'monthly' ? `$${plan.monthlyPrice}` : `$${Math.round(plan.annualPrice / 12)}`;
  };

  const getBillingText = (plan) => {
    if (plan.monthlyPrice === 'Custom') return 'Contact us for pricing';
    return billingCycle === 'monthly' ? '/month' : '/month (billed annually)';
  };

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

      {/* Header */}
      <section className="py-16 text-center">
        <div className="max-w-4xl mx-auto px-6">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Select the perfect plan for your council's needs. Start with a free trial and upgrade anytime.
          </p>
          
          {/* Billing Toggle */}
          <div className="flex items-center justify-center mb-12">
            <span className={`mr-3 ${billingCycle === 'monthly' ? 'text-gray-900 font-semibold' : 'text-gray-500'}`}>
              Monthly
            </span>
            <button
              onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'annual' : 'monthly')}
              className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  billingCycle === 'annual' ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`ml-3 ${billingCycle === 'annual' ? 'text-gray-900 font-semibold' : 'text-gray-500'}`}>
              Annual
            </span>
            {billingCycle === 'annual' && (
              <Badge className="ml-2 bg-green-100 text-green-800">Save 17%</Badge>
            )}
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8">
            {plans.map((plan, index) => (
              <Card key={index} className={`relative ${plan.popular ? 'border-green-500 border-2' : ''}`}>
                {plan.popular && (
                  <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-green-500 text-white">
                    POPULAR
                  </Badge>
                )}
                <CardHeader className="text-center pb-4">
                  <CardTitle className="text-2xl font-bold text-gray-900">
                    {plan.name}
                  </CardTitle>
                  <p className="text-gray-600">{plan.description}</p>
                  <div className="mt-4">
                    <span className="text-4xl font-bold text-gray-900">
                      {getPrice(plan)}
                    </span>
                    <span className="text-gray-600 ml-1">
                      {getBillingText(plan)}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-center">
                        <Check className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  
                  <div className="space-y-2 mb-8 p-4 bg-gray-50 rounded-lg">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Users:</span>
                      <span className="font-semibold">{plan.limits.users}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Storage:</span>
                      <span className="font-semibold">{plan.limits.storage}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Grant Programs:</span>
                      <span className="font-semibold">{plan.limits.grants}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Applications:</span>
                      <span className="font-semibold">{plan.limits.applications}</span>
                    </div>
                  </div>
                  
                  <Button 
                    className={`w-full ${plan.popular ? 'bg-green-600 hover:bg-green-700' : 'bg-yellow-500 hover:bg-yellow-600'} text-black font-semibold`}
                  >
                    {plan.monthlyPrice === 'Custom' ? 'Contact Sales' : 'Choose Plan'}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Comparison */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Compare Features
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full bg-white rounded-lg shadow">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-4 font-semibold text-gray-900">Feature</th>
                  <th className="text-center p-4 font-semibold text-gray-900">Starter</th>
                  <th className="text-center p-4 font-semibold text-gray-900">Professional</th>
                  <th className="text-center p-4 font-semibold text-gray-900">Enterprise</th>
                </tr>
              </thead>
              <tbody>
                {features.map((feature, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="p-4 text-gray-700">{feature.name}</td>
                    <td className="p-4 text-center">
                      {feature.starter ? (
                        <Check className="h-5 w-5 text-green-500 mx-auto" />
                      ) : (
                        <X className="h-5 w-5 text-gray-300 mx-auto" />
                      )}
                    </td>
                    <td className="p-4 text-center">
                      {feature.professional ? (
                        <Check className="h-5 w-5 text-green-500 mx-auto" />
                      ) : (
                        <X className="h-5 w-5 text-gray-300 mx-auto" />
                      )}
                    </td>
                    <td className="p-4 text-center">
                      {feature.enterprise ? (
                        <Check className="h-5 w-5 text-green-500 mx-auto" />
                      ) : (
                        <X className="h-5 w-5 text-gray-300 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Frequently Asked Questions
          </h2>
          <div className="space-y-6">
            {faqs.map((faq, index) => (
              <Card key={index}>
                <CardContent className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {faq.question}
                  </h3>
                  <p className="text-gray-600">
                    {faq.answer}
                  </p>
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
            Ready to Get Started?
          </h2>
          <p className="text-xl mb-8 text-blue-100">
            Start your free trial today and see how GrantThrive can transform your grant management process.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-yellow-500 hover:bg-yellow-600 text-black font-semibold">
              Start Free Trial
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-blue-700">
              Contact Sales
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

export default PricingPage;

