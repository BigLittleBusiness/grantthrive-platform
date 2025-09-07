#!/usr/bin/env python3
"""
Enhanced Grant Scraper for GrantThrive
Scrapes real Australian Government grant data from grants.gov.au
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

class EnhancedGrantScraper:
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
        
        # First, get the search form
        search_url = f"{self.base_url}/gd/list"
        
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
        Scrape detailed information from a grant award page
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
            self.extract_grant_fields(soup, grant_data)
            
            # Extract recipient and location information
            self.extract_recipient_info(soup, grant_data)
            
            # Extract delivery location
            self.extract_delivery_location(soup, grant_data)
            
            return grant_data
            
        except Exception as e:
            logger.error(f"Error scraping grant award {ga_info['ga_id']}: {str(e)}")
            return None
    
    def extract_grant_fields(self, soup, grant_data):
        """
        Extract standard grant fields from the page
        """
        # Define field mappings
        field_mappings = {
            'Agency:': 'agency',
            'Approval Date:': 'approval_date',
            'Publish Date:': 'publish_date',
            'Category:': 'category',
            'Grant Term:': 'grant_term',
            'Value (AUD):': 'value',
            'Grant Program:': 'program',
            'Grant Activity:': 'activity',
            'Purpose:': 'purpose'
        }
        
        # Extract fields using various methods
        for label, field_name in field_mappings.items():
            value = self.find_field_value(soup, label)
            if value:
                grant_data[field_name] = value
    
    def find_field_value(self, soup, label):
        """
        Find the value for a specific field label
        """
        # Method 1: Look for label followed by value
        label_element = soup.find(string=re.compile(re.escape(label)))
        if label_element:
            # Try to find the next sibling or parent's next sibling
            parent = label_element.parent
            if parent:
                next_element = parent.find_next_sibling()
                if next_element:
                    return next_element.get_text(strip=True)
                    
                # Try looking within the same parent
                text = parent.get_text(strip=True)
                if label in text:
                    parts = text.split(label, 1)
                    if len(parts) > 1:
                        return parts[1].strip()
        
        # Method 2: Look for dt/dd pairs
        dt_element = soup.find('dt', string=re.compile(re.escape(label)))
        if dt_element:
            dd_element = dt_element.find_next_sibling('dd')
            if dd_element:
                return dd_element.get_text(strip=True)
        
        return None
    
    def extract_recipient_info(self, soup, grant_data):
        """
        Extract recipient information
        """
        # Look for recipient section
        recipient_section = soup.find(string=re.compile(r'Grant Recipient Details'))
        if recipient_section:
            section_parent = recipient_section.find_parent()
            if section_parent:
                # Extract recipient name and ABN
                name = self.find_field_value_in_section(section_parent, 'Recipient Name:')
                abn = self.find_field_value_in_section(section_parent, 'Recipient ABN:')
                
                if name:
                    grant_data['recipient_name'] = name
                if abn:
                    grant_data['recipient_abn'] = abn
        
        # Extract recipient location
        location_section = soup.find(string=re.compile(r'Grant Recipient Location'))
        if location_section:
            section_parent = location_section.find_parent()
            if section_parent:
                suburb = self.find_field_value_in_section(section_parent, 'Suburb:')
                city = self.find_field_value_in_section(section_parent, 'Town/City:')
                postcode = self.find_field_value_in_section(section_parent, 'Postcode:')
                state = self.find_field_value_in_section(section_parent, 'State/Territory:')
                
                grant_data['recipient_location'] = {
                    'suburb': suburb,
                    'city': city,
                    'postcode': postcode,
                    'state': state
                }
    
    def extract_delivery_location(self, soup, grant_data):
        """
        Extract grant delivery location
        """
        delivery_section = soup.find(string=re.compile(r'Grant Delivery Location'))
        if delivery_section:
            section_parent = delivery_section.find_parent()
            if section_parent:
                state = self.find_field_value_in_section(section_parent, 'State/Territory:')
                postcode = self.find_field_value_in_section(section_parent, 'Postcode:')
                
                grant_data['delivery_location'] = {
                    'state': state,
                    'postcode': postcode
                }
    
    def find_field_value_in_section(self, section, label):
        """
        Find field value within a specific section
        """
        label_element = section.find(string=re.compile(re.escape(label)))
        if label_element:
            parent = label_element.parent
            if parent:
                # Look for the value in the next element
                next_element = parent.find_next_sibling()
                if next_element:
                    return next_element.get_text(strip=True)
        return None
    
    def scrape_all_grants(self, start_date="01-Mar-2025", end_date="03-Sep-2025", max_grants=50):
        """
        Main method to scrape all grants within the date range
        """
        logger.info("Starting comprehensive grant scraping...")
        
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
            
            time.sleep(2)  # Be respectful to the server
        
        self.grants_data = scraped_grants
        logger.info(f"Successfully scraped {len(scraped_grants)} grants")
        return scraped_grants
    
    def save_data(self, filename_base="real_grants_data"):
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
    Main function to run the scraper
    """
    scraper = EnhancedGrantScraper()
    
    # Scrape grants from the last 6 months
    grants = scraper.scrape_all_grants(
        start_date="01-Mar-2025",
        end_date="03-Sep-2025",
        max_grants=25  # Limit for initial testing
    )
    
    if grants:
        # Save the data
        scraper.save_data("real_australian_grants_6months")
        
        # Print summary
        print(f"\n=== SCRAPING SUMMARY ===")
        print(f"Total grants scraped: {len(grants)}")
        print(f"Sample grant:")
        if grants:
            sample = grants[0]
            print(f"  Title: {sample.get('title', 'N/A')}")
            print(f"  Agency: {sample.get('agency', 'N/A')}")
            print(f"  Value: {sample.get('value', 'N/A')}")
            print(f"  Recipient: {sample.get('recipient_name', 'N/A')}")
    else:
        print("No grants were scraped successfully")

if __name__ == "__main__":
    main()

