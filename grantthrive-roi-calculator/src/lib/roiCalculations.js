// GrantThrive ROI Calculation Library
// Based on the comprehensive ROI framework

export const COUNCIL_SIZES = {
  SMALL: 'small',
  MEDIUM: 'medium',
  LARGE: 'large'
};

export const PRICING_TIERS = {
  [COUNCIL_SIZES.SMALL]: {
    basePrice: 2400,    // $200/month
    communityVoting: 600,
    grantMapping: 600,
    bundleDiscount: 0.1
  },
  [COUNCIL_SIZES.MEDIUM]: {
    basePrice: 6000,    // $500/month
    communityVoting: 1200,
    grantMapping: 1200,
    bundleDiscount: 0.1
  },
  [COUNCIL_SIZES.LARGE]: {
    basePrice: 13200,   // $1100/month
    communityVoting: 2400,
    grantMapping: 2400,
    bundleDiscount: 0.1
  }
};

export const DEFAULT_METRICS = {
  [COUNCIL_SIZES.SMALL]: {
    applications: 100,
    currentStaffHours: 4.25, // Average of 4.0-4.5 hours per application
    grantThriveHours: 0.5, // 30 minutes
    staffHourlyRate: 40,
    currentTechCosts: 3000,
    currentAdminCosts: 2000,
    techSavings: 3000,
    adminSavings: 1500
  },
  [COUNCIL_SIZES.MEDIUM]: {
    applications: 300,
    currentStaffHours: 4.25,
    grantThriveHours: 0.5,
    staffHourlyRate: 42,
    currentTechCosts: 8000,
    currentAdminCosts: 5000,
    techSavings: 8000,
    adminSavings: 3500
  },
  [COUNCIL_SIZES.LARGE]: {
    applications: 600,
    currentStaffHours: 4.25,
    grantThriveHours: 0.5,
    staffHourlyRate: 45,
    currentTechCosts: 25000,
    currentAdminCosts: 12000,
    techSavings: 25000,
    adminSavings: 8000
  }
};

export function calculateGrantThriveAnnualCost(councilSize, features = {}) {
  const pricing = PRICING_TIERS[councilSize];
  if (!pricing) throw new Error('Invalid council size');

  let totalCost = pricing.basePrice;
  let addOnCosts = 0;

  if (features.communityVoting && features.grantMapping) {
    // Bundle pricing with discount
    const bundleCost = (pricing.communityVoting + pricing.grantMapping) * (1 - pricing.bundleDiscount);
    addOnCosts = bundleCost;
  } else {
    if (features.communityVoting) addOnCosts += pricing.communityVoting;
    if (features.grantMapping) addOnCosts += pricing.grantMapping;
  }

  return {
    basePrice: pricing.basePrice,
    addOnCosts: Math.round(addOnCosts),
    totalAnnualCost: Math.round(totalCost + addOnCosts)
  };
}

export function calculateCurrentStateCosts(inputs) {
  const {
    applications,
    currentStaffHours,
    staffHourlyRate,
    currentTechCosts,
    currentAdminCosts
  } = inputs;

  const staffCosts = applications * currentStaffHours * staffHourlyRate;
  const totalCurrentCosts = staffCosts + currentTechCosts + currentAdminCosts;

  return {
    staffCosts: Math.round(staffCosts),
    techCosts: currentTechCosts,
    adminCosts: currentAdminCosts,
    totalCurrentCosts: Math.round(totalCurrentCosts)
  };
}

export function calculateBenefits(inputs) {
  const {
    applications,
    currentStaffHours,
    grantThriveHours,
    staffHourlyRate,
    techSavings,
    adminSavings
  } = inputs;

  const hoursSavedPerApplication = currentStaffHours - grantThriveHours;
  const totalHoursSaved = applications * hoursSavedPerApplication;
  const staffTimeSavings = totalHoursSaved * staffHourlyRate;
  const totalBenefits = staffTimeSavings + techSavings + adminSavings;

  return {
    hoursSavedPerApplication: Math.round(hoursSavedPerApplication * 10) / 10,
    totalHoursSaved: Math.round(totalHoursSaved),
    staffTimeSavings: Math.round(staffTimeSavings),
    techSavings,
    adminSavings,
    totalBenefits: Math.round(totalBenefits)
  };
}

export function calculateROI(inputs, councilSize, features = {}) {
  const currentCosts = calculateCurrentStateCosts(inputs);
  const benefits = calculateBenefits(inputs);
  const grantThriveCosts = calculateGrantThriveAnnualCost(councilSize, features);

  const netAnnualBenefit = benefits.totalBenefits - grantThriveCosts.totalAnnualCost;
  const roiPercentage = (netAnnualBenefit / grantThriveCosts.totalAnnualCost) * 100;
  const paybackMonths = grantThriveCosts.totalAnnualCost / (netAnnualBenefit / 12);

  return {
    currentCosts,
    benefits,
    grantThriveCosts,
    netAnnualBenefit: Math.round(netAnnualBenefit),
    roiPercentage: Math.round(roiPercentage),
    paybackMonths: Math.round(paybackMonths * 10) / 10,
    totalSavings: Math.round(currentCosts.totalCurrentCosts - grantThriveCosts.totalAnnualCost)
  };
}

export function calculateNPV(inputs, councilSize, features = {}, years = 5, discountRate = 0.08) {
  const roi = calculateROI(inputs, councilSize, features);
  const annualNetBenefit = roi.netAnnualBenefit;
  
  let npv = -roi.grantThriveCosts.totalAnnualCost; // Initial investment (negative)
  
  for (let year = 1; year <= years; year++) {
    const discountedBenefit = annualNetBenefit / Math.pow(1 + discountRate, year);
    npv += discountedBenefit;
  }

  return {
    npv: Math.round(npv),
    totalBenefitsOverPeriod: Math.round(annualNetBenefit * years),
    averageAnnualReturn: Math.round(npv / years)
  };
}

export function generateROIReport(inputs, councilSize, features = {}) {
  const roi = calculateROI(inputs, councilSize, features);
  const npv = calculateNPV(inputs, councilSize, features);

  return {
    summary: {
      councilSize: councilSize.charAt(0).toUpperCase() + councilSize.slice(1),
      applications: inputs.applications,
      roiPercentage: roi.roiPercentage,
      paybackMonths: roi.paybackMonths,
      annualSavings: roi.netAnnualBenefit,
      fiveYearValue: npv.totalBenefitsOverPeriod
    },
    costs: {
      current: roi.currentCosts,
      grantThrive: roi.grantThriveCosts
    },
    benefits: roi.benefits,
    financial: {
      roi: roi.roiPercentage,
      payback: roi.paybackMonths,
      npv: npv.npv,
      totalSavings: roi.totalSavings
    },
    features: {
      baseIncluded: [
        'Grant Creation Wizard',
        'Application Review Workflow',
        'Automated Communications',
        'Digital Document Management',
        'Real-time Analytics',
        'API Integrations',
        'Mobile Responsive Design',
        'Cloud-based Security'
      ],
      addOns: {
        communityVoting: features.communityVoting ? 'Included' : 'Not Selected',
        grantMapping: features.grantMapping ? 'Included' : 'Not Selected'
      }
    }
  };
}

export function getCouncilSizeRecommendation(applications) {
  if (applications <= 150) return COUNCIL_SIZES.SMALL;
  if (applications <= 400) return COUNCIL_SIZES.MEDIUM;
  return COUNCIL_SIZES.LARGE;
}

export function validateInputs(inputs) {
  const errors = [];
  
  if (!inputs.applications || inputs.applications < 1) {
    errors.push('Applications per year must be at least 1');
  }
  
  if (!inputs.currentStaffHours || inputs.currentStaffHours < 0.1) {
    errors.push('Current staff hours per application must be at least 0.1');
  }
  
  if (!inputs.staffHourlyRate || inputs.staffHourlyRate < 10) {
    errors.push('Staff hourly rate must be at least $10');
  }
  
  if (inputs.currentTechCosts < 0) {
    errors.push('Current technology costs cannot be negative');
  }
  
  if (inputs.currentAdminCosts < 0) {
    errors.push('Current administrative costs cannot be negative');
  }

  return errors;
}

