// Competitive Analysis Data for GrantThrive vs SmartyGrants
// Based on market research and feature comparison

export const COMPETITORS = {
  SMARTYGRANTS: 'smartygrants',
  MANUAL_PROCESS: 'manual'
};

export const SMARTYGRANTS_PRICING = {
  small: {
    basePrice: 8000,      // Estimated annual cost for small councils
    setupFee: 3000,       // One-time setup fee
    trainingFee: 2000,    // Training costs
    supportFee: 1500      // Annual support fee
  },
  medium: {
    basePrice: 15000,     // Estimated annual cost for medium councils
    setupFee: 5000,
    trainingFee: 3000,
    supportFee: 2500
  },
  large: {
    basePrice: 22000,     // Estimated annual cost for large councils
    setupFee: 8000,
    trainingFee: 5000,
    supportFee: 4000
  }
};

export const FEATURE_COMPARISON = {
  // Core Platform Features
  grantCreationWizard: {
    grantThrive: true,
    smartyGrants: false,
    description: "AI-powered step-by-step grant creation with templates"
  },
  applicationReviewWorkflow: {
    grantThrive: true,
    smartyGrants: true,
    description: "Structured review and scoring workflow"
  },
  automatedCommunications: {
    grantThrive: true,
    smartyGrants: false,
    description: "Automated emails, SMS, and notifications"
  },
  digitalDocumentManagement: {
    grantThrive: true,
    smartyGrants: true,
    description: "Cloud-based document storage and management"
  },
  realTimeAnalytics: {
    grantThrive: true,
    smartyGrants: false,
    description: "Live dashboards and performance metrics"
  },
  apiIntegrations: {
    grantThrive: true,
    smartyGrants: false,
    description: "15+ integrations with council systems"
  },
  mobileResponsiveDesign: {
    grantThrive: true,
    smartyGrants: true,
    description: "Fully responsive mobile interface"
  },
  cloudBasedSecurity: {
    grantThrive: true,
    smartyGrants: true,
    description: "Enterprise-grade security and compliance"
  },

  // Community Engagement Features (GrantThrive Unique)
  communityVoting: {
    grantThrive: true,
    smartyGrants: false,
    description: "Public voting on grant priorities and applications"
  },
  interactiveGrantMapping: {
    grantThrive: true,
    smartyGrants: false,
    description: "Visual map showing grant locations and outcomes"
  },
  publicTransparencyPortal: {
    grantThrive: true,
    smartyGrants: false,
    description: "Public portal showing grant outcomes and impact"
  },
  communityFeedbackSystem: {
    grantThrive: true,
    smartyGrants: false,
    description: "Collect and manage community feedback on grants"
  },

  // Advanced Features
  aiPoweredRecommendations: {
    grantThrive: true,
    smartyGrants: false,
    description: "AI suggests optimal grant allocations"
  },
  predictiveAnalytics: {
    grantThrive: true,
    smartyGrants: false,
    description: "Predict application success and community impact"
  },
  automatedReporting: {
    grantThrive: true,
    smartyGrants: false,
    description: "Auto-generate compliance and performance reports"
  },
  customWorkflows: {
    grantThrive: true,
    smartyGrants: true,
    description: "Configurable approval and review workflows"
  },

  // Integration Capabilities
  salesforceIntegration: {
    grantThrive: true,
    smartyGrants: false,
    description: "Native Salesforce CRM integration"
  },
  quickbooksIntegration: {
    grantThrive: true,
    smartyGrants: false,
    description: "Direct QuickBooks financial integration"
  },
  xeroIntegration: {
    grantThrive: true,
    smartyGrants: false,
    description: "Seamless Xero accounting integration"
  },
  myobIntegration: {
    grantThrive: true,
    smartyGrants: false,
    description: "MYOB financial system integration"
  },
  technologyOneIntegration: {
    grantThrive: true,
    smartyGrants: false,
    description: "TechnologyOne council system integration"
  }
};

export function calculateCompetitiveAdvantage(councilSize, features = {}) {
  const grantThriveFeatures = Object.keys(FEATURE_COMPARISON).filter(
    feature => FEATURE_COMPARISON[feature].grantThrive
  ).length;

  const smartyGrantsFeatures = Object.keys(FEATURE_COMPARISON).filter(
    feature => FEATURE_COMPARISON[feature].smartyGrants
  ).length;

  const uniqueFeatures = Object.keys(FEATURE_COMPARISON).filter(
    feature => FEATURE_COMPARISON[feature].grantThrive && !FEATURE_COMPARISON[feature].smartyGrants
  ).length;

  const featureAdvantage = ((grantThriveFeatures - smartyGrantsFeatures) / smartyGrantsFeatures) * 100;

  return {
    grantThriveFeatures,
    smartyGrantsFeatures,
    uniqueFeatures,
    featureAdvantage: Math.round(featureAdvantage),
    competitiveGap: grantThriveFeatures - smartyGrantsFeatures
  };
}

export function calculateSmartyGrantsTotalCost(councilSize, includeOneTimeFees = true) {
  const pricing = SMARTYGRANTS_PRICING[councilSize];
  if (!pricing) throw new Error('Invalid council size for SmartyGrants pricing');

  const annualCost = pricing.basePrice + pricing.supportFee;
  const oneTimeCosts = includeOneTimeFees ? (pricing.setupFee + pricing.trainingFee) : 0;

  return {
    annualSubscription: pricing.basePrice,
    annualSupport: pricing.supportFee,
    totalAnnualCost: annualCost,
    setupFee: pricing.setupFee,
    trainingFee: pricing.trainingFee,
    totalOneTimeCosts: oneTimeCosts,
    firstYearTotal: annualCost + oneTimeCosts,
    threeYearTotal: (annualCost * 3) + oneTimeCosts
  };
}

export function generateCompetitiveComparison(councilSize, grantThriveFeatures = {}) {
  const smartyGrantsCosts = calculateSmartyGrantsTotalCost(councilSize);
  const competitiveAdvantage = calculateCompetitiveAdvantage(councilSize, grantThriveFeatures);

  // Get GrantThrive costs from our pricing model
  const grantThrivePricing = {
    small: { basePrice: 7200, communityVoting: 1200, grantMapping: 1200 },
    medium: { basePrice: 14400, communityVoting: 2400, grantMapping: 2400 },
    large: { basePrice: 21600, communityVoting: 3600, grantMapping: 3600 }
  };

  const pricing = grantThrivePricing[councilSize];
  let grantThriveTotal = pricing.basePrice;
  
  if (grantThriveFeatures.communityVoting && grantThriveFeatures.grantMapping) {
    // Bundle discount
    grantThriveTotal += (pricing.communityVoting + pricing.grantMapping) * 0.9;
  } else {
    if (grantThriveFeatures.communityVoting) grantThriveTotal += pricing.communityVoting;
    if (grantThriveFeatures.grantMapping) grantThriveTotal += pricing.grantMapping;
  }

  const annualSavings = smartyGrantsCosts.totalAnnualCost - grantThriveTotal;
  const firstYearSavings = smartyGrantsCosts.firstYearTotal - grantThriveTotal;
  const threeYearSavings = smartyGrantsCosts.threeYearTotal - (grantThriveTotal * 3);

  return {
    grantThrive: {
      annualCost: Math.round(grantThriveTotal),
      setupIncluded: true,
      trainingIncluded: true,
      supportIncluded: true,
      features: competitiveAdvantage.grantThriveFeatures
    },
    smartyGrants: {
      annualCost: smartyGrantsCosts.totalAnnualCost,
      setupFee: smartyGrantsCosts.setupFee,
      trainingFee: smartyGrantsCosts.trainingFee,
      firstYearTotal: smartyGrantsCosts.firstYearTotal,
      features: competitiveAdvantage.smartyGrantsFeatures
    },
    comparison: {
      annualSavings: Math.round(annualSavings),
      firstYearSavings: Math.round(firstYearSavings),
      threeYearSavings: Math.round(threeYearSavings),
      featureAdvantage: competitiveAdvantage.featureAdvantage,
      uniqueFeatures: competitiveAdvantage.uniqueFeatures,
      savingsPercentage: Math.round((annualSavings / smartyGrantsCosts.totalAnnualCost) * 100)
    }
  };
}

export function getFeaturesByCategory() {
  return {
    core: {
      title: "Core Platform Features",
      features: [
        'grantCreationWizard',
        'applicationReviewWorkflow',
        'automatedCommunications',
        'digitalDocumentManagement',
        'realTimeAnalytics',
        'mobileResponsiveDesign',
        'cloudBasedSecurity'
      ]
    },
    community: {
      title: "Community Engagement (GrantThrive Exclusive)",
      features: [
        'communityVoting',
        'interactiveGrantMapping',
        'publicTransparencyPortal',
        'communityFeedbackSystem'
      ]
    },
    advanced: {
      title: "Advanced Capabilities",
      features: [
        'aiPoweredRecommendations',
        'predictiveAnalytics',
        'automatedReporting',
        'customWorkflows'
      ]
    },
    integrations: {
      title: "System Integrations",
      features: [
        'apiIntegrations',
        'salesforceIntegration',
        'quickbooksIntegration',
        'xeroIntegration',
        'myobIntegration',
        'technologyOneIntegration'
      ]
    }
  };
}

export function generateCompetitiveSummary(councilSize) {
  const comparison = generateCompetitiveComparison(councilSize, { 
    communityVoting: true, 
    grantMapping: true 
  });

  return {
    headline: `Save ${Math.abs(comparison.comparison.savingsPercentage)}% annually vs SmartyGrants`,
    subheadline: `${comparison.comparison.featureAdvantage}% more features with revolutionary community engagement`,
    keyPoints: [
      `$${comparison.comparison.annualSavings.toLocaleString()} annual savings`,
      `$${comparison.comparison.firstYearSavings.toLocaleString()} first-year savings (including setup costs)`,
      `${comparison.comparison.uniqueFeatures} exclusive community features`,
      `${comparison.grantThrive.features} total features vs ${comparison.smartyGrants.features}`,
      'Setup, training, and support included at no extra cost'
    ],
    callToAction: "Switch to GrantThrive and transform your community engagement while saving money"
  };
}

