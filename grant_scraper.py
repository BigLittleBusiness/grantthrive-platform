#!/usr/bin/env python3
"""
GrantThrive Grant Data Scraper for grants.gov.au
Scrapes historical grant data for mapping and analysis features
"""

import requests
import json
import csv
import time
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GrantsGovAuScraper:
    def __init__(self):
        self.base_url = "https://www.grants.gov.au"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GrantThrive Data Collector (Educational/Research Purpose)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.grants_data = []
        self.rate_limit_delay = 2  # seconds between requests
        
    def get_page(self, url, params=None, retries=3):
        """Get a page with error handling and rate limiting"""
        for attempt in range(retries):
            try:
                time.sleep(self.rate_limit_delay)
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
                time.sleep(5)  # Wait longer between retries
        return None
    
    def search_grant_decisions(self, start_date=None, end_date=None, agency=None, page=1):
        """Search for grant decisions with optional filters"""
        search_url = f"{self.base_url}/Gd/ListResult"
        
        params = {
            'Page': page,
            'ItemsPerPage': 0,  # Show all items
            'SearchFrom': 'AdvancedSearch',
            'Type': 'Gd',
            'AgencyStatus': 0,  # All active agencies
            'OrderBy': 'Relevance'
        }
        
        if start_date:
            params['FromDate'] = start_date.strftime('%d-%b-%Y')
        if end_date:
            params['ToDate'] = end_date.strftime('%d-%b-%Y')
        if agency:
            params['Agency'] = agency
            
        response = self.get_page(search_url, params=params)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract grant decision IDs and links
        grant_decisions = []
        
        # Look for grant decision links (GD IDs)
        gd_links = soup.find_all('a', href=re.compile(r'/Gd/Show/'))
        for link in gd_links:
            gd_id = link.get_text().strip()
            if gd_id.startswith('GD'):
                grant_decisions.append({
                    'gd_id': gd_id,
                    'url': urljoin(self.base_url, link['href'])
                })
        
        logger.info(f"Found {len(grant_decisions)} grant decisions on page {page}")
        return grant_decisions
    
    def get_grant_decision_details(self, gd_url):
        """Get details of a specific grant decision"""
        response = self.get_page(gd_url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic grant decision info
        gd_data = {}
        
        # Extract GD ID
        gd_id_elem = soup.find('td', string='GD ID:')
        if gd_id_elem:
            gd_data['gd_id'] = gd_id_elem.find_next_sibling('td').get_text().strip()
        
        # Extract Agency
        agency_elem = soup.find('td', string='Agency:')
        if agency_elem:
            gd_data['agency'] = agency_elem.find_next_sibling('td').get_text().strip()
        
        # Extract Publish Date
        publish_elem = soup.find('td', string='Publish Date:')
        if publish_elem:
            gd_data['publish_date'] = publish_elem.find_next_sibling('td').get_text().strip()
        
        # Extract Decision Maker
        decision_elem = soup.find('td', string='Decision Maker:')
        if decision_elem:
            gd_data['decision_maker'] = decision_elem.find_next_sibling('td').get_text().strip()
        
        # Find link to related grant awards
        awards_link = soup.find('a', string='View Related Grant Awards')
        if awards_link:
            gd_data['awards_url'] = urljoin(self.base_url, awards_link['href'])
        
        return gd_data
    
    def get_grant_awards(self, awards_url):
        """Get grant awards associated with a grant decision"""
        response = self.get_page(awards_url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find grant award links (GA IDs)
        award_links = soup.find_all('a', href=re.compile(r'/Ga/Show/'))
        awards = []
        
        for link in award_links:
            ga_id = link.get_text().strip()
            if ga_id.startswith('GA'):
                awards.append({
                    'ga_id': ga_id,
                    'url': urljoin(self.base_url, link['href'])
                })
        
        logger.info(f"Found {len(awards)} grant awards")
        return awards
    
    def get_grant_award_details(self, ga_url):
        """Get detailed information about a specific grant award"""
        response = self.get_page(ga_url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        grant_data = {}
        
        # Helper function to extract field value
        def extract_field(label_text):
            label = soup.find('td', string=lambda text: text and label_text in text)
            if label:
                value_cell = label.find_next_sibling('td')
                if value_cell:
                    return value_cell.get_text().strip()
            return None
        
        # Extract basic information
        grant_data['ga_id'] = extract_field('GA ID:')
        grant_data['agency'] = extract_field('Agency:')
        grant_data['approval_date'] = extract_field('Approval Date:')
        grant_data['publish_date'] = extract_field('Publish Date:')
        grant_data['category'] = extract_field('Category:')
        grant_data['grant_term'] = extract_field('Grant Term:')
        
        # Extract value with special handling for currency
        value_text = extract_field('Value (AUD):')
        if value_text:
            # Extract numeric value from currency string
            value_match = re.search(r'\\$([\\d,]+(?:\\.\\d{2})?)', value_text)
            if value_match:
                grant_data['value_aud'] = float(value_match.group(1).replace(',', ''))
            grant_data['value_text'] = value_text
        
        # Extract program information
        grant_data['pbs_program'] = extract_field('PBS Program Name:')
        grant_data['grant_program'] = extract_field('Grant Program:')
        grant_data['grant_activity'] = extract_field('Grant Activity:')
        grant_data['purpose'] = extract_field('Purpose:')
        
        # Extract recipient information
        grant_data['recipient_name'] = extract_field('Recipient Name:')
        grant_data['recipient_abn'] = extract_field('Recipient ABN:')
        
        # Extract recipient location
        grant_data['recipient_suburb'] = extract_field('Suburb:')
        grant_data['recipient_city'] = extract_field('Town/City:')
        grant_data['recipient_postcode'] = extract_field('Postcode:')
        grant_data['recipient_state'] = extract_field('State/Territory:')
        grant_data['recipient_country'] = extract_field('Country:')
        
        # Extract delivery location (may be different from recipient)
        delivery_section = soup.find('h2', string='Grant Delivery Location')
        if delivery_section:
            delivery_parent = delivery_section.find_parent()
            grant_data['delivery_state'] = self._extract_field_in_section(delivery_parent, 'State/Territory:')
            grant_data['delivery_postcode'] = self._extract_field_in_section(delivery_parent, 'Postcode:')
            grant_data['delivery_country'] = self._extract_field_in_section(delivery_parent, 'Country:')
        
        # Extract additional flags
        grant_data['one_off'] = extract_field('One-off/Ad hoc:')
        grant_data['aggregate_award'] = extract_field('Aggregate Grant Award:')
        grant_data['confidential_contract'] = extract_field('Confidentiality - Contract:')
        grant_data['confidential_outputs'] = extract_field('Confidentiality - Outputs:')
        
        return grant_data
    
    def _extract_field_in_section(self, section, field_name):
        """Extract field value within a specific section"""
        field_elem = section.find('td', string=lambda text: text and field_name in text)
        if field_elem:
            value_cell = field_elem.find_next_sibling('td')
            if value_cell:
                return value_cell.get_text().strip()
        return None
    
    def categorize_grant(self, grant_data):
        """Categorize grant based on program, purpose, and category"""
        categories = []
        
        # Category mapping based on keywords
        category_keywords = {
            'Health & Social Services': ['health', 'social', 'medical', 'disability', 'aged care', 'mental health'],
            'Education & Training': ['education', 'training', 'school', 'university', 'research', 'student'],
            'Infrastructure & Development': ['infrastructure', 'construction', 'development', 'transport', 'roads'],
            'Environment & Sustainability': ['environment', 'sustainability', 'climate', 'renewable', 'conservation'],
            'Arts & Culture': ['arts', 'culture', 'creative', 'heritage', 'museum', 'festival'],
            'Technology & Innovation': ['technology', 'innovation', 'digital', 'tech', 'startup', 'research'],
            'Community Services': ['community', 'volunteer', 'local', 'neighbourhood', 'civic'],
            'Emergency & Safety': ['emergency', 'disaster', 'safety', 'security', 'fire', 'flood']
        }
        
        # Text to analyze (combine relevant fields)
        text_fields = [
            grant_data.get('category', ''),
            grant_data.get('grant_program', ''),
            grant_data.get('grant_activity', ''),
            grant_data.get('purpose', '')
        ]
        combined_text = ' '.join(text_fields).lower()
        
        # Check for keyword matches
        for category, keywords in category_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                categories.append(category)
        
        # Default category if none found
        if not categories:
            categories.append('Other')
        
        return categories
    
    def determine_grant_size(self, value_aud):
        """Categorize grant by size"""
        if not value_aud:
            return 'Unknown'
        
        if value_aud < 50000:
            return 'Small'
        elif value_aud < 500000:
            return 'Medium'
        elif value_aud < 5000000:
            return 'Large'
        else:
            return 'Major'
    
    def scrape_grants(self, start_date=None, end_date=None, max_pages=5):
        """Main scraping function"""
        logger.info("Starting grant data scraping...")
        
        # Default to last 6 months if no dates provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=180)
        
        logger.info(f"Scraping grants from {start_date.strftime('%d-%b-%Y')} to {end_date.strftime('%d-%b-%Y')}")
        
        all_grants = []
        
        # Search for grant decisions
        for page in range(1, max_pages + 1):
            logger.info(f"Processing page {page}...")
            
            grant_decisions = self.search_grant_decisions(start_date, end_date, page=page)
            if not grant_decisions:
                logger.info("No more grant decisions found")
                break
            
            # Process each grant decision
            for gd in grant_decisions:
                logger.info(f"Processing {gd['gd_id']}...")
                
                # Get grant decision details
                gd_details = self.get_grant_decision_details(gd['url'])
                if not gd_details:
                    continue
                
                # Get associated grant awards
                if 'awards_url' in gd_details:
                    awards = self.get_grant_awards(gd_details['awards_url'])
                    
                    # Process each grant award
                    for award in awards:
                        logger.info(f"Processing award {award['ga_id']}...")
                        
                        award_details = self.get_grant_award_details(award['url'])
                        if award_details:
                            # Combine decision and award data
                            combined_data = {**gd_details, **award_details}
                            
                            # Add categorization
                            combined_data['categories'] = self.categorize_grant(combined_data)
                            combined_data['size_category'] = self.determine_grant_size(
                                combined_data.get('value_aud')
                            )
                            
                            # Add timestamp
                            combined_data['scraped_at'] = datetime.now().isoformat()
                            
                            all_grants.append(combined_data)
                            
                            logger.info(f"Collected grant: {award['ga_id']} - "
                                      f"{combined_data.get('recipient_name', 'Unknown')} - "
                                      f"${combined_data.get('value_aud', 0):,.2f}")
        
        self.grants_data = all_grants
        logger.info(f"Scraping completed. Collected {len(all_grants)} grants.")
        return all_grants
    
    def save_to_json(self, filename='grants_data.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.grants_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {filename}")
    
    def save_to_csv(self, filename='grants_data.csv'):
        """Save scraped data to CSV file"""
        if not self.grants_data:
            logger.warning("No data to save")
            return
        
        # Get all unique keys for CSV headers
        all_keys = set()
        for grant in self.grants_data:
            all_keys.update(grant.keys())
        
        # Handle list fields (like categories)
        fieldnames = sorted(all_keys)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for grant in self.grants_data:
                # Convert list fields to strings
                row = grant.copy()
                for key, value in row.items():
                    if isinstance(value, list):
                        row[key] = ', '.join(value)
                writer.writerow(row)
        
        logger.info(f"Data saved to {filename}")
    
    def get_summary_stats(self):
        """Generate summary statistics of scraped data"""
        if not self.grants_data:
            return {}
        
        stats = {
            'total_grants': len(self.grants_data),
            'total_value': sum(g.get('value_aud', 0) for g in self.grants_data),
            'agencies': {},
            'states': {},
            'categories': {},
            'size_categories': {}
        }
        
        for grant in self.grants_data:
            # Count by agency
            agency = grant.get('agency', 'Unknown')
            stats['agencies'][agency] = stats['agencies'].get(agency, 0) + 1
            
            # Count by state
            state = grant.get('recipient_state', 'Unknown')
            stats['states'][state] = stats['states'].get(state, 0) + 1
            
            # Count by categories
            categories = grant.get('categories', [])
            for cat in categories:
                stats['categories'][cat] = stats['categories'].get(cat, 0) + 1
            
            # Count by size
            size = grant.get('size_category', 'Unknown')
            stats['size_categories'][size] = stats['size_categories'].get(size, 0) + 1
        
        return stats

def main():
    """Main execution function"""
    scraper = GrantsGovAuScraper()
    
    # Scrape recent grants (last 3 months, max 3 pages for testing)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    grants = scraper.scrape_grants(start_date=start_date, end_date=end_date, max_pages=3)
    
    # Save data
    scraper.save_to_json('grants_data.json')
    scraper.save_to_csv('grants_data.csv')
    
    # Print summary
    stats = scraper.get_summary_stats()
    print(f"\\n=== SCRAPING SUMMARY ===")
    print(f"Total Grants: {stats['total_grants']}")
    print(f"Total Value: ${stats['total_value']:,.2f}")
    print(f"\\nTop Agencies:")
    for agency, count in sorted(stats['agencies'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {agency}: {count}")
    print(f"\\nStates:")
    for state, count in sorted(stats['states'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {state}: {count}")
    print(f"\\nCategories:")
    for cat, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    main()

