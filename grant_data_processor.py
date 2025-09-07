#!/usr/bin/env python3
"""
GrantThrive Grant Data Processor
Processes and categorizes grant data for mapping visualization
"""

import json
import csv
import pandas as pd
import numpy as np
from datetime import datetime
import re
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GrantDataProcessor:
    def __init__(self):
        self.grants_data = []
        self.processed_data = []
        self.categories = {
            'Health & Social Services': {
                'keywords': ['health', 'social', 'medical', 'disability', 'aged care', 'mental health', 
                           'healthcare', 'wellbeing', 'support services', 'community health'],
                'color': '#e74c3c',
                'icon': 'heart'
            },
            'Education & Training': {
                'keywords': ['education', 'training', 'school', 'university', 'research', 'student',
                           'learning', 'academic', 'scholarship', 'curriculum'],
                'color': '#3498db',
                'icon': 'graduation-cap'
            },
            'Infrastructure & Development': {
                'keywords': ['infrastructure', 'construction', 'development', 'transport', 'roads',
                           'building', 'facilities', 'maintenance', 'upgrade', 'capital works'],
                'color': '#95a5a6',
                'icon': 'building'
            },
            'Environment & Sustainability': {
                'keywords': ['environment', 'sustainability', 'climate', 'renewable', 'conservation',
                           'green', 'carbon', 'biodiversity', 'ecosystem', 'pollution'],
                'color': '#27ae60',
                'icon': 'leaf'
            },
            'Arts & Culture': {
                'keywords': ['arts', 'culture', 'creative', 'heritage', 'museum', 'festival',
                           'cultural', 'artistic', 'performance', 'exhibition'],
                'color': '#9b59b6',
                'icon': 'palette'
            },
            'Technology & Innovation': {
                'keywords': ['technology', 'innovation', 'digital', 'tech', 'startup', 'research',
                           'innovation', 'digital transformation', 'IT', 'software'],
                'color': '#f39c12',
                'icon': 'laptop'
            },
            'Community Services': {
                'keywords': ['community', 'volunteer', 'local', 'neighbourhood', 'civic',
                           'community development', 'social cohesion', 'engagement'],
                'color': '#1abc9c',
                'icon': 'users'
            },
            'Emergency & Safety': {
                'keywords': ['emergency', 'disaster', 'safety', 'security', 'fire', 'flood',
                           'resilience', 'preparedness', 'response', 'recovery'],
                'color': '#e67e22',
                'icon': 'shield'
            },
            'Economic Development': {
                'keywords': ['economic', 'business', 'employment', 'jobs', 'industry',
                           'commerce', 'trade', 'investment', 'entrepreneurship'],
                'color': '#34495e',
                'icon': 'briefcase'
            }
        }
        
        # Australian state/territory mapping
        self.state_mapping = {
            'NSW': {'name': 'New South Wales', 'capital': 'Sydney'},
            'VIC': {'name': 'Victoria', 'capital': 'Melbourne'},
            'QLD': {'name': 'Queensland', 'capital': 'Brisbane'},
            'SA': {'name': 'South Australia', 'capital': 'Adelaide'},
            'WA': {'name': 'Western Australia', 'capital': 'Perth'},
            'TAS': {'name': 'Tasmania', 'capital': 'Hobart'},
            'NT': {'name': 'Northern Territory', 'capital': 'Darwin'},
            'ACT': {'name': 'Australian Capital Territory', 'capital': 'Canberra'}
        }
        
        # Postcode to coordinates mapping (sample data - would need full dataset)
        self.postcode_coordinates = {
            '5000': {'lat': -34.9285, 'lng': 138.6007, 'city': 'Adelaide', 'state': 'SA'},
            '3000': {'lat': -37.8136, 'lng': 144.9631, 'city': 'Melbourne', 'state': 'VIC'},
            '2000': {'lat': -33.8688, 'lng': 151.2093, 'city': 'Sydney', 'state': 'NSW'},
            '4000': {'lat': -27.4698, 'lng': 153.0251, 'city': 'Brisbane', 'state': 'QLD'},
            '6000': {'lat': -31.9505, 'lng': 115.8605, 'city': 'Perth', 'state': 'WA'},
            '7000': {'lat': -42.8821, 'lng': 147.3272, 'city': 'Hobart', 'state': 'TAS'},
            '0800': {'lat': -12.4634, 'lng': 130.8456, 'city': 'Darwin', 'state': 'NT'},
            '2600': {'lat': -35.2809, 'lng': 149.1300, 'city': 'Canberra', 'state': 'ACT'}
        }
    
    def load_sample_data(self):
        """Load sample grant data for demonstration"""
        sample_grants = [
            {
                'ga_id': 'GA385269',
                'agency': 'Department of Social Services',
                'approval_date': '25-Jan-2024',
                'publish_date': '27-Jun-2024',
                'category': 'Services for People with Disabilities',
                'grant_term': '26-Jun-2024 to 30-Jun-2027',
                'value_aud': 8620954.34,
                'grant_program': 'Pre-emptive Early Intervention Pilot',
                'grant_activity': 'Pre-emptive early intervention pilot for infants showing early signs of difference in social communication',
                'purpose': 'Pre-emptive early intervention for infants showing early signs of neurodiversity and their families.',
                'recipient_name': 'Department of the Premier and Cabinet',
                'recipient_abn': '94 500 415 644',
                'recipient_suburb': 'ADELAIDE',
                'recipient_city': 'ADELAIDE',
                'recipient_postcode': '5000',
                'recipient_state': 'SA',
                'recipient_country': 'AUSTRALIA',
                'delivery_state': 'SA',
                'delivery_postcode': '5000',
                'delivery_country': 'AUSTRALIA'
            },
            {
                'ga_id': 'GA385270',
                'agency': 'Department of Education',
                'approval_date': '15-Feb-2024',
                'publish_date': '20-Mar-2024',
                'category': 'Education and Training',
                'grant_term': '01-Apr-2024 to 31-Dec-2025',
                'value_aud': 2500000.00,
                'grant_program': 'Digital Learning Initiative',
                'grant_activity': 'Implementation of digital learning platforms in regional schools',
                'purpose': 'Enhance digital literacy and access to technology in rural and remote schools.',
                'recipient_name': 'Victorian Department of Education',
                'recipient_abn': '12 345 678 901',
                'recipient_suburb': 'MELBOURNE',
                'recipient_city': 'MELBOURNE',
                'recipient_postcode': '3000',
                'recipient_state': 'VIC',
                'recipient_country': 'AUSTRALIA',
                'delivery_state': 'VIC',
                'delivery_postcode': '3000',
                'delivery_country': 'AUSTRALIA'
            },
            {
                'ga_id': 'GA385271',
                'agency': 'Department of Climate Change, Energy, the Environment and Water',
                'approval_date': '10-Mar-2024',
                'publish_date': '15-Apr-2024',
                'category': 'Environment and Sustainability',
                'grant_term': '01-May-2024 to 30-Apr-2027',
                'value_aud': 5750000.00,
                'grant_program': 'Community Solar Initiative',
                'grant_activity': 'Installation of community solar panels and battery storage systems',
                'purpose': 'Reduce carbon emissions and provide renewable energy access to rural communities.',
                'recipient_name': 'Brisbane City Council',
                'recipient_abn': '98 765 432 109',
                'recipient_suburb': 'BRISBANE',
                'recipient_city': 'BRISBANE',
                'recipient_postcode': '4000',
                'recipient_state': 'QLD',
                'recipient_country': 'AUSTRALIA',
                'delivery_state': 'QLD',
                'delivery_postcode': '4000',
                'delivery_country': 'AUSTRALIA'
            }
        ]
        
        self.grants_data = sample_grants
        logger.info(f"Loaded {len(sample_grants)} sample grants")
        return sample_grants
    
    def load_data_from_file(self, filename):
        """Load grant data from JSON or CSV file"""
        try:
            if filename.endswith('.json'):
                with open(filename, 'r', encoding='utf-8') as f:
                    self.grants_data = json.load(f)
            elif filename.endswith('.csv'):
                df = pd.read_csv(filename)
                self.grants_data = df.to_dict('records')
            
            logger.info(f"Loaded {len(self.grants_data)} grants from {filename}")
            return self.grants_data
        except Exception as e:
            logger.error(f"Error loading data from {filename}: {e}")
            return []
    
    def categorize_grant(self, grant):
        """Categorize a grant based on its content"""
        # Combine text fields for analysis
        text_fields = [
            grant.get('category', ''),
            grant.get('grant_program', ''),
            grant.get('grant_activity', ''),
            grant.get('purpose', ''),
            grant.get('agency', '')
        ]
        combined_text = ' '.join(text_fields).lower()
        
        # Find matching categories
        matched_categories = []
        category_scores = {}
        
        for category_name, category_info in self.categories.items():
            score = 0
            for keyword in category_info['keywords']:
                if keyword in combined_text:
                    score += 1
            
            if score > 0:
                category_scores[category_name] = score
                matched_categories.append(category_name)
        
        # Return primary category (highest score) and all matches
        if category_scores:
            primary_category = max(category_scores, key=category_scores.get)
            return {
                'primary_category': primary_category,
                'all_categories': matched_categories,
                'category_scores': category_scores
            }
        else:
            return {
                'primary_category': 'Other',
                'all_categories': ['Other'],
                'category_scores': {'Other': 1}
            }
    
    def determine_grant_size(self, value_aud):
        """Categorize grant by funding amount"""
        if not value_aud or value_aud == 0:
            return 'Unknown'
        
        if value_aud < 50000:
            return 'Small'
        elif value_aud < 500000:
            return 'Medium'
        elif value_aud < 5000000:
            return 'Large'
        else:
            return 'Major'
    
    def get_coordinates(self, postcode, state=None):
        """Get latitude/longitude for a postcode"""
        if postcode in self.postcode_coordinates:
            return self.postcode_coordinates[postcode]
        
        # For unknown postcodes, return approximate state center
        state_centers = {
            'NSW': {'lat': -32.0, 'lng': 147.0},
            'VIC': {'lat': -37.0, 'lng': 144.0},
            'QLD': {'lat': -22.0, 'lng': 144.0},
            'SA': {'lat': -30.0, 'lng': 135.0},
            'WA': {'lat': -25.0, 'lng': 122.0},
            'TAS': {'lat': -42.0, 'lng': 147.0},
            'NT': {'lat': -19.0, 'lng': 133.0},
            'ACT': {'lat': -35.3, 'lng': 149.1}
        }
        
        if state and state in state_centers:
            coords = state_centers[state].copy()
            coords['city'] = 'Unknown'
            coords['state'] = state
            return coords
        
        # Default to center of Australia
        return {'lat': -25.0, 'lng': 133.0, 'city': 'Unknown', 'state': 'Unknown'}
    
    def process_grants(self):
        """Process all grants and add categorization and mapping data"""
        processed_grants = []
        
        for grant in self.grants_data:
            # Create processed grant record
            processed_grant = grant.copy()
            
            # Add categorization
            categorization = self.categorize_grant(grant)
            processed_grant.update(categorization)
            
            # Add size category
            processed_grant['size_category'] = self.determine_grant_size(
                grant.get('value_aud', 0)
            )
            
            # Add geographic data
            postcode = grant.get('recipient_postcode') or grant.get('delivery_postcode')
            state = grant.get('recipient_state') or grant.get('delivery_state')
            
            if postcode or state:
                coords = self.get_coordinates(postcode, state)
                processed_grant['latitude'] = coords['lat']
                processed_grant['longitude'] = coords['lng']
                processed_grant['mapped_city'] = coords['city']
                processed_grant['mapped_state'] = coords['state']
            
            # Add category styling
            primary_cat = processed_grant['primary_category']
            if primary_cat in self.categories:
                processed_grant['category_color'] = self.categories[primary_cat]['color']
                processed_grant['category_icon'] = self.categories[primary_cat]['icon']
            
            # Add processed timestamp
            processed_grant['processed_at'] = datetime.now().isoformat()
            
            # Parse dates
            for date_field in ['approval_date', 'publish_date']:
                if date_field in grant and grant[date_field]:
                    try:
                        # Handle different date formats
                        date_str = grant[date_field]
                        if '-' in date_str and len(date_str.split('-')) == 3:
                            # Format: dd-Mmm-yyyy
                            processed_grant[f'{date_field}_parsed'] = datetime.strptime(
                                date_str, '%d-%b-%Y'
                            ).isoformat()
                    except ValueError:
                        logger.warning(f"Could not parse date: {grant[date_field]}")
            
            processed_grants.append(processed_grant)
        
        self.processed_data = processed_grants
        logger.info(f"Processed {len(processed_grants)} grants")
        return processed_grants
    
    def generate_mapping_data(self):
        """Generate data specifically formatted for mapping visualization"""
        mapping_data = {
            'grants': [],
            'summary': {
                'total_grants': len(self.processed_data),
                'total_value': sum(g.get('value_aud', 0) for g in self.processed_data),
                'categories': {},
                'states': {},
                'size_distribution': {}
            },
            'categories': self.categories,
            'states': self.state_mapping
        }
        
        # Process each grant for mapping
        for grant in self.processed_data:
            mapping_grant = {
                'id': grant.get('ga_id'),
                'title': grant.get('grant_activity', 'Unknown Grant'),
                'description': grant.get('purpose', ''),
                'value': grant.get('value_aud', 0),
                'value_formatted': f"${grant.get('value_aud', 0):,.2f}",
                'agency': grant.get('agency', 'Unknown Agency'),
                'recipient': grant.get('recipient_name', 'Unknown Recipient'),
                'location': {
                    'lat': grant.get('latitude'),
                    'lng': grant.get('longitude'),
                    'city': grant.get('mapped_city'),
                    'state': grant.get('mapped_state'),
                    'postcode': grant.get('recipient_postcode')
                },
                'category': {
                    'primary': grant.get('primary_category'),
                    'all': grant.get('all_categories', []),
                    'color': grant.get('category_color'),
                    'icon': grant.get('category_icon')
                },
                'size_category': grant.get('size_category'),
                'dates': {
                    'approval': grant.get('approval_date'),
                    'publish': grant.get('publish_date'),
                    'term': grant.get('grant_term')
                },
                'program': grant.get('grant_program', ''),
                'url': f"https://www.grants.gov.au/Ga/Show/{grant.get('ga_id', '')}"
            }
            
            mapping_data['grants'].append(mapping_grant)
            
            # Update summary statistics
            primary_cat = grant.get('primary_category', 'Other')
            mapping_data['summary']['categories'][primary_cat] = \
                mapping_data['summary']['categories'].get(primary_cat, 0) + 1
            
            state = grant.get('mapped_state', 'Unknown')
            mapping_data['summary']['states'][state] = \
                mapping_data['summary']['states'].get(state, 0) + 1
            
            size_cat = grant.get('size_category', 'Unknown')
            mapping_data['summary']['size_distribution'][size_cat] = \
                mapping_data['summary']['size_distribution'].get(size_cat, 0) + 1
        
        return mapping_data
    
    def save_mapping_data(self, filename='grant_mapping_data.json'):
        """Save processed mapping data to JSON file"""
        mapping_data = self.generate_mapping_data()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Mapping data saved to {filename}")
        return mapping_data
    
    def generate_summary_report(self):
        """Generate a summary report of the processed data"""
        if not self.processed_data:
            return "No data to summarize"
        
        total_grants = len(self.processed_data)
        total_value = sum(g.get('value_aud', 0) for g in self.processed_data)
        
        # Category distribution
        category_counts = defaultdict(int)
        for grant in self.processed_data:
            category_counts[grant.get('primary_category', 'Other')] += 1
        
        # State distribution
        state_counts = defaultdict(int)
        for grant in self.processed_data:
            state_counts[grant.get('mapped_state', 'Unknown')] += 1
        
        # Size distribution
        size_counts = defaultdict(int)
        for grant in self.processed_data:
            size_counts[grant.get('size_category', 'Unknown')] += 1
        
        report = f"""
=== GRANT DATA PROCESSING SUMMARY ===

Total Grants Processed: {total_grants:,}
Total Grant Value: ${total_value:,.2f}
Average Grant Value: ${total_value/total_grants:,.2f}

=== CATEGORY DISTRIBUTION ===
"""
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_grants) * 100
            report += f"{category}: {count} ({percentage:.1f}%)\\n"
        
        report += f"""
=== STATE DISTRIBUTION ===
"""
        for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_grants) * 100
            report += f"{state}: {count} ({percentage:.1f}%)\\n"
        
        report += f"""
=== SIZE DISTRIBUTION ===
"""
        for size, count in sorted(size_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_grants) * 100
            report += f"{size}: {count} ({percentage:.1f}%)\\n"
        
        return report

def main():
    """Main execution function"""
    processor = GrantDataProcessor()
    
    # Load sample data (in real implementation, would load from scraper output)
    processor.load_sample_data()
    
    # Process the grants
    processed_grants = processor.process_grants()
    
    # Generate mapping data
    mapping_data = processor.save_mapping_data()
    
    # Generate and print summary report
    report = processor.generate_summary_report()
    print(report)
    
    # Save processed data
    with open('processed_grants.json', 'w', encoding='utf-8') as f:
        json.dump(processed_grants, f, indent=2, ensure_ascii=False)
    
    print(f"\\nProcessing complete!")
    print(f"- Processed grants saved to: processed_grants.json")
    print(f"- Mapping data saved to: grant_mapping_data.json")
    print(f"- Ready for visualization in GrantThrive mapping component")

if __name__ == "__main__":
    main()

