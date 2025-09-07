#!/usr/bin/env python3
"""
Enhanced Grant Scraper v2 for GrantThrive
Improved location extraction from grants.gov.au
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, parse_qs, urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedGrantScraperV2:
    def __init__(self):
        self.base_url = "https://www.grants.gov.au"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.grants_data = []
        
    def search_grants(self, start_date="01-Mar-2025", end_date="03-Sep-2025", max_pages=10):
        """
        Search for grants within the specified date range
        """
        logger.info(f"Searching for grants from {start_date} to {end_date}")
        
        # Prepare search parameters
        search_params = {
            'SearchFrom': 'AdvancedSearch',
            'Type': 'Gd',
            'AgencyStatus': '0',  # All Active Agencies
            'DateStart': start_date,
            'DateEnd': end_date,
            'Page': '1',
            'ItemsPerPage': '0',
            'OrderBy': 'Relevance'
        }
        
        # Perform the search
        search_result_url = f"{self.base_url}/Gd/ListResult"
        response = self.session.get(search_result_url, params=search_params)
        
        if response.status_code != 200:
            logger.error(f"Failed to perform search: {response.status_code}")
            return []
            
        return self.parse_search_results(response.text, max_pages)
    
    def parse_search_results(self, html_content, max_pages=10):
        """
        Parse the search results page to extract grant decision IDs
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        grant_decisions = []
        
        # Find all grant decision links
        gd_links = soup.find_all('a', href=re.compile(r'/Gd/Show/'))
        
        for link in gd_links:
            gd_id = link.get_text(strip=True)
            gd_url = urljoin(self.base_url, link['href'])
            grant_decisions.append({
                'gd_id': gd_id,
                'gd_url': gd_url
            })
            
        logger.info(f"Found {len(grant_decisions)} grant decisions")
        return grant_decisions
    
    def get_grant_awards_from_decision(self, gd_info):
        """
        Get grant awards associated with a grant decision
        """
        logger.info(f"Processing grant decision: {gd_info['gd_id']}")
        
        try:
            # Get the grant decision page
            response = self.session.get(gd_info['gd_url'])
            if response.status_code != 200:
                logger.error(f"Failed to get grant decision page: {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for "View Related Grant Awards" link
            awards_link = soup.find('a', string=re.compile(r'View Related Grant Awards'))
            if not awards_link:
                logger.warning(f"No grant awards found for {gd_info['gd_id']}")
                return []
                
            awards_url = urljoin(self.base_url, awards_link['href'])
            
            # Get the grant awards page
            awards_response = self.session.get(awards_url)
            if awards_response.status_code != 200:
                logger.error(f"Failed to get grant awards page: {awards_response.status_code}")
                return []
                
            return self.parse_grant_awards_page(awards_response.text)
            
        except Exception as e:
            logger.error(f"Error processing grant decision {gd_info['gd_id']}: {str(e)}")
            return []
    
    def parse_grant_awards_page(self, html_content):
        """
        Parse the grant awards page to extract individual grant award IDs
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        grant_awards = []
        
        # Find all grant award links (GA IDs)
        ga_links = soup.find_all('a', href=re.compile(r'/Ga/Show/'))
        
        for link in ga_links:
            ga_id = link.get_text(strip=True)
            ga_url = urljoin(self.base_url, link['href'])
            grant_awards.append({
                'ga_id': ga_id,
                'ga_url': ga_url
            })
            
        logger.info(f"Found {len(grant_awards)} grant awards")
        return grant_awards
    
    def scrape_grant_award_details(self, ga_info):
        """
        Scrape detailed information from a grant award page with improved location extraction
        """
        logger.info(f"Scraping grant award: {ga_info['ga_id']}")
        
        try:
            response = self.session.get(ga_info['ga_url'])
            if response.status_code != 200:
                logger.error(f"Failed to get grant award page: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract grant details
            grant_data = {
                'ga_id': ga_info['ga_id'],
                'url': ga_info['ga_url']
            }
            
            # Extract title from the main heading or description
            title_element = soup.find('h1')
            if title_element:
                grant_data['title'] = title_element.get_text(strip=True)
            
            # Extract structured data from the page
            self.extract_grant_fields_v2(soup, grant_data)
            
            # Enhanced recipient and location information extraction
            self.extract_recipient_info_v2(soup, grant_data)
            
            # Enhanced delivery location extraction
            self.extract_delivery_location_v2(soup, grant_data)
            
            return grant_data
            
        except Exception as e:
            logger.error(f"Error scraping grant award {ga_info['ga_id']}: {str(e)}")
            return None
    
    def extract_grant_fields_v2(self, soup, grant_data):
        """
        Enhanced extraction of standard grant fields from the page
        """
        # Get the full page text for analysis
        page_text = soup.get_text()
        
        # Define field mappings with multiple possible patterns
        field_patterns = {
            'agency': [r'Agency:\s*([^\n\r]+)', r'Department of ([^\n\r]+)'],
            'approval_date': [r'Approval Date:\s*([^\n\r]+)'],
            'publish_date': [r'Publish Date:\s*([^\n\r]+)'],
            'category': [r'Category:\s*([^\n\r]+)'],
            'grant_term': [r'Grant Term:\s*([^\n\r]+)'],
            'value': [r'Value \(AUD\):\s*([^\n\r]+)', r'\$([0-9,]+\.?[0-9]*)'],
            'program': [r'Grant Program:\s*([^\n\r]+)'],
            'activity': [r'Grant Activity:\s*([^\n\r]+)'],
            'purpose': [r'Purpose:\s*([^\n\r]+)']
        }
        
        # Extract fields using regex patterns
        for field_name, patterns in field_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    grant_data[field_name] = match.group(1).strip()
                    break
    
    def extract_recipient_info_v2(self, soup, grant_data):
        """
        Enhanced extraction of recipient information with better parsing
        """
        page_text = soup.get_text()
        
        # Extract recipient name
        recipient_patterns = [
            r'Recipient Name:\s*([^\n\r]+)',
            r'Grant Recipient Details[^:]*Recipient Name:\s*([^\n\r]+)'
        ]
        
        for pattern in recipient_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)
            if match:
                grant_data['recipient_name'] = match.group(1).strip()
                break
        
        # Extract recipient ABN
        abn_patterns = [
            r'Recipient ABN:\s*([^\n\r]+)',
            r'ABN:\s*([0-9\s]+)'
        ]
        
        for pattern in abn_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)
            if match:
                grant_data['recipient_abn'] = match.group(1).strip()
                break
        
        # Enhanced recipient location extraction
        location_info = {}
        
        # Look for location patterns in the text
        location_patterns = {
            'suburb': [r'Suburb:\s*([^\n\r]+)'],
            'city': [r'Town/City:\s*([^\n\r]+)', r'City:\s*([^\n\r]+)'],
            'postcode': [r'Postcode:\s*([0-9]+)'],
            'state': [r'State/Territory:\s*([A-Z]{2,3})', r'State:\s*([A-Z]{2,3})']
        }
        
        for field, patterns in location_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    location_info[field] = match.group(1).strip()
                    break
        
        # Also look for address patterns like "ADELAIDE, SA 5000"
        address_pattern = r'([A-Z\s]+),\s*([A-Z]{2,3})\s*([0-9]{4})'
        address_match = re.search(address_pattern, page_text)
        if address_match:
            if not location_info.get('city'):
                location_info['city'] = address_match.group(1).strip()
            if not location_info.get('state'):
                location_info['state'] = address_match.group(2).strip()
            if not location_info.get('postcode'):
                location_info['postcode'] = address_match.group(3).strip()
        
        grant_data['recipient_location'] = location_info
    
    def extract_delivery_location_v2(self, soup, grant_data):
        """
        Enhanced extraction of grant delivery location
        """
        page_text = soup.get_text()
        
        delivery_info = {}
        
        # Look for delivery location patterns
        delivery_patterns = {
            'state': [r'Grant Delivery Location[^:]*State/Territory:\s*([A-Z]{2,3})', 
                     r'Delivery.*State:\s*([A-Z]{2,3})'],
            'postcode': [r'Grant Delivery Location[^:]*Postcode:\s*([0-9]+)',
                        r'Delivery.*Postcode:\s*([0-9]+)']
        }
        
        for field, patterns in delivery_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    delivery_info[field] = match.group(1).strip()
                    break
        
        grant_data['delivery_location'] = delivery_info
    
    def scrape_all_grants(self, start_date="01-Mar-2025", end_date="03-Sep-2025", max_grants=50):
        """
        Main method to scrape all grants within the date range
        """
        logger.info("Starting comprehensive grant scraping with enhanced location extraction...")
        
        # Step 1: Search for grant decisions
        grant_decisions = self.search_grants(start_date, end_date)
        
        if not grant_decisions:
            logger.warning("No grant decisions found")
            return []
        
        # Step 2: Process each grant decision to get grant awards
        all_grant_awards = []
        for gd_info in grant_decisions[:10]:  # Limit to first 10 for testing
            grant_awards = self.get_grant_awards_from_decision(gd_info)
            all_grant_awards.extend(grant_awards)
            time.sleep(1)  # Be respectful to the server
        
        logger.info(f"Found {len(all_grant_awards)} total grant awards")
        
        # Step 3: Scrape detailed information for each grant award
        scraped_grants = []
        for i, ga_info in enumerate(all_grant_awards[:max_grants]):
            logger.info(f"Processing grant {i+1}/{min(len(all_grant_awards), max_grants)}")
            
            grant_data = self.scrape_grant_award_details(ga_info)
            if grant_data:
                scraped_grants.append(grant_data)
                
                # Log location extraction success
                recipient_loc = grant_data.get('recipient_location', {})
                delivery_loc = grant_data.get('delivery_location', {})
                if recipient_loc.get('state') or delivery_loc.get('state'):
                    logger.info(f"  ✓ Location extracted: {recipient_loc.get('city', 'N/A')}, {recipient_loc.get('state', delivery_loc.get('state', 'N/A'))}")
                else:
                    logger.warning(f"  ✗ No location data found for {ga_info['ga_id']}")
            
            time.sleep(2)  # Be respectful to the server
        
        self.grants_data = scraped_grants
        logger.info(f"Successfully scraped {len(scraped_grants)} grants")
        return scraped_grants
    
    def save_data(self, filename_base="real_grants_data_v2"):
        """
        Save the scraped data to JSON and CSV files
        """
        if not self.grants_data:
            logger.warning("No data to save")
            return
        
        # Save as JSON
        json_filename = f"{filename_base}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.grants_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.grants_data)} grants to {json_filename}")
        
        # Save as CSV
        if self.grants_data:
            csv_filename = f"{filename_base}.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.grants_data[0].keys())
                writer.writeheader()
                writer.writerows(self.grants_data)
            logger.info(f"Saved {len(self.grants_data)} grants to {csv_filename}")

def main():
    """
    Main function to run the enhanced scraper
    """
    scraper = EnhancedGrantScraperV2()
    
    # Scrape grants from the last 6 months with enhanced location extraction
    grants = scraper.scrape_all_grants(
        start_date="01-Mar-2025",
        end_date="03-Sep-2025",
        max_grants=25  # Limit for initial testing
    )
    
    if grants:
        # Save the data
        scraper.save_data("real_australian_grants_6months_v2")
        
        # Print summary with location stats
        print(f"\n=== ENHANCED SCRAPING SUMMARY ===")
        print(f"Total grants scraped: {len(grants)}")
        
        # Count grants with location data
        grants_with_location = 0
        states_found = set()
        
        for grant in grants:
            recipient_loc = grant.get('recipient_location', {})
            delivery_loc = grant.get('delivery_location', {})
            
            state = recipient_loc.get('state') or delivery_loc.get('state')
            if state:
                grants_with_location += 1
                states_found.add(state)
        
        print(f"Grants with location data: {grants_with_location}/{len(grants)} ({grants_with_location/len(grants)*100:.1f}%)")
        print(f"States found: {', '.join(sorted(states_found))}")
        
        if grants:
            sample = grants[0]
            print(f"\nSample grant:")
            print(f"  Title: {sample.get('title', 'N/A')}")
            print(f"  Agency: {sample.get('agency', 'N/A')}")
            print(f"  Value: {sample.get('value', 'N/A')}")
            print(f"  Recipient: {sample.get('recipient_name', 'N/A')}")
            print(f"  Location: {sample.get('recipient_location', {})}")
    else:
        print("No grants were scraped successfully")

if __name__ == "__main__":
    main()

