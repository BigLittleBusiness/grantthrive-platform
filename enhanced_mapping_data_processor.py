#!/usr/bin/env python3
"""
Enhanced Mapping Data Processor for GrantThrive
Adds proper coordinates and geographic data for interactive mapping
"""

import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedMappingDataProcessor:
    def __init__(self):
        # Comprehensive Australian postcode to coordinates mapping
        self.location_coordinates = {
            # South Australia
            'ADELAIDE': {'lat': -34.9285, 'lng': 138.6007, 'state': 'SA', 'postcode': '5000'},
            'HINDMARSH': {'lat': -34.9089, 'lng': 138.5678, 'state': 'SA', 'postcode': '5007'},
            'SEFTON PARK': {'lat': -34.8847, 'lng': 138.5289, 'state': 'SA', 'postcode': '5083'},
            
            # Victoria
            'BRIGHTON': {'lat': -37.9061, 'lng': 145.0000, 'state': 'VIC', 'postcode': '3186'},
            'CRANBOURNE EAST': {'lat': -38.1167, 'lng': 145.2833, 'state': 'VIC', 'postcode': '3977'},
            'DANDENONG': {'lat': -37.9833, 'lng': 145.2167, 'state': 'VIC', 'postcode': '3175'},
            'BLACKBURN': {'lat': -37.8167, 'lng': 145.1500, 'state': 'VIC', 'postcode': '3130'},
            
            # Australian Capital Territory
            'CANBERRA': {'lat': -35.2809, 'lng': 149.1300, 'state': 'ACT', 'postcode': '2600'},
            'ACT': {'lat': -35.2809, 'lng': 149.1300, 'state': 'ACT', 'postcode': '2600'},
            
            # State centers for fallback
            'SA': {'lat': -34.9285, 'lng': 138.6007, 'state': 'SA', 'postcode': '5000'},
            'VIC': {'lat': -37.8136, 'lng': 144.9631, 'state': 'VIC', 'postcode': '3000'},
            'NSW': {'lat': -33.8688, 'lng': 151.2093, 'state': 'NSW', 'postcode': '2000'},
            'QLD': {'lat': -27.4698, 'lng': 153.0251, 'state': 'QLD', 'postcode': '4000'},
            'WA': {'lat': -31.9505, 'lng': 115.8605, 'state': 'WA', 'postcode': '6000'},
            'TAS': {'lat': -42.8821, 'lng': 147.3272, 'state': 'TAS', 'postcode': '7000'},
            'NT': {'lat': -12.4634, 'lng': 130.8456, 'state': 'NT', 'postcode': '0800'},
        }
        
        # Map regions for clustering
        self.regions = {
            'Adelaide Metro': {
                'center': {'lat': -34.9285, 'lng': 138.6007},
                'cities': ['ADELAIDE', 'HINDMARSH', 'SEFTON PARK'],
                'state': 'SA'
            },
            'Melbourne Metro': {
                'center': {'lat': -37.8136, 'lng': 144.9631},
                'cities': ['BRIGHTON', 'CRANBOURNE EAST', 'DANDENONG', 'BLACKBURN'],
                'state': 'VIC'
            },
            'Canberra': {
                'center': {'lat': -35.2809, 'lng': 149.1300},
                'cities': ['CANBERRA', 'ACT'],
                'state': 'ACT'
            }
        }
    
    def load_mapping_data(self, filename="real_grant_mapping_data_v2.json"):
        """Load the processed mapping data"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded mapping data with {len(data['grants'])} grants")
            return data
        except Exception as e:
            logger.error(f"Error loading mapping data: {str(e)}")
            return None
    
    def enhance_grant_coordinates(self, grant):
        """Add proper coordinates to a grant based on location data"""
        location = grant.get('location', {})
        city = location.get('city', '').upper()
        state = location.get('state', '').upper()
        
        # Try to find coordinates by city name first
        if city and city in self.location_coordinates:
            coord_info = self.location_coordinates[city]
            grant['location']['coordinates'] = {
                'lat': coord_info['lat'],
                'lng': coord_info['lng']
            }
            # Ensure postcode is set
            if not location.get('postcode'):
                grant['location']['postcode'] = coord_info['postcode']
            logger.info(f"  ✓ Coordinates added for {city}: {coord_info['lat']}, {coord_info['lng']}")
            return True
        
        # Fallback to state center
        elif state and state in self.location_coordinates:
            coord_info = self.location_coordinates[state]
            grant['location']['coordinates'] = {
                'lat': coord_info['lat'],
                'lng': coord_info['lng']
            }
            if not location.get('city'):
                grant['location']['city'] = state
            if not location.get('postcode'):
                grant['location']['postcode'] = coord_info['postcode']
            logger.info(f"  ✓ State center coordinates added for {state}: {coord_info['lat']}, {coord_info['lng']}")
            return True
        
        logger.warning(f"  ✗ No coordinates found for city: {city}, state: {state}")
        return False
    
    def create_map_markers(self, grants):
        """Create map markers for visualization"""
        markers = []
        
        for grant in grants:
            coordinates = grant.get('location', {}).get('coordinates')
            if coordinates:
                marker = {
                    'id': grant['id'],
                    'lat': coordinates['lat'],
                    'lng': coordinates['lng'],
                    'title': grant['title'],
                    'value': grant['value'],
                    'value_formatted': grant['value_formatted'],
                    'category': grant['category']['primary'],
                    'color': grant['category']['color'],
                    'icon': grant['category']['icon'],
                    'size_category': grant['size_category'],
                    'location_name': f"{grant['location'].get('city', '')}, {grant['location'].get('state', '')}",
                    'recipient': grant['recipient'],
                    'agency': grant['agency'],
                    'url': grant['url']
                }
                markers.append(marker)
        
        logger.info(f"Created {len(markers)} map markers")
        return markers
    
    def create_region_clusters(self, grants):
        """Create regional clusters for map visualization"""
        clusters = []
        
        for region_name, region_info in self.regions.items():
            region_grants = []
            total_value = 0
            
            for grant in grants:
                city = grant.get('location', {}).get('city', '').upper()
                if city in region_info['cities']:
                    region_grants.append(grant)
                    total_value += grant.get('value', 0)
            
            if region_grants:
                cluster = {
                    'name': region_name,
                    'center': region_info['center'],
                    'state': region_info['state'],
                    'grant_count': len(region_grants),
                    'total_value': total_value,
                    'total_value_formatted': f"${total_value:,.2f}",
                    'grants': region_grants,
                    'categories': {}
                }
                
                # Count categories in this region
                for grant in region_grants:
                    category = grant['category']['primary']
                    cluster['categories'][category] = cluster['categories'].get(category, 0) + 1
                
                clusters.append(cluster)
        
        logger.info(f"Created {len(clusters)} regional clusters")
        return clusters
    
    def enhance_mapping_data(self, mapping_data):
        """Enhance the mapping data with coordinates and geographic features"""
        if not mapping_data:
            return None
        
        grants = mapping_data['grants']
        enhanced_grants = []
        coordinates_added = 0
        
        logger.info("Enhancing grants with coordinates...")
        
        for grant in grants:
            if self.enhance_grant_coordinates(grant):
                coordinates_added += 1
            enhanced_grants.append(grant)
        
        logger.info(f"Added coordinates to {coordinates_added}/{len(grants)} grants")
        
        # Create map visualization data
        map_markers = self.create_map_markers(enhanced_grants)
        region_clusters = self.create_region_clusters(enhanced_grants)
        
        # Update the mapping data
        mapping_data['grants'] = enhanced_grants
        mapping_data['map_data'] = {
            'markers': map_markers,
            'clusters': region_clusters,
            'bounds': {
                'north': -12.4634,  # Darwin
                'south': -42.8821,  # Hobart
                'east': 153.0251,   # Brisbane
                'west': 115.8605    # Perth
            },
            'center': {'lat': -25.2744, 'lng': 133.7751}  # Australia center
        }
        
        # Update summary with geographic stats
        mapping_data['summary']['coordinates_coverage'] = f"{coordinates_added}/{len(grants)}"
        mapping_data['summary']['regions'] = len(region_clusters)
        mapping_data['summary']['map_markers'] = len(map_markers)
        
        return mapping_data
    
    def save_enhanced_data(self, mapping_data, filename="enhanced_grant_mapping_data.json"):
        """Save the enhanced mapping data"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(mapping_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved enhanced mapping data to {filename}")
            
            # Create a summary report
            summary_filename = filename.replace('.json', '_summary.txt')
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write("=== ENHANCED GRANT MAPPING DATA SUMMARY ===\n\n")
                f.write(f"Total Grants: {mapping_data['summary']['total_grants']}\n")
                f.write(f"Total Value: ${mapping_data['summary']['total_value']:,.2f}\n")
                f.write(f"Coordinates Coverage: {mapping_data['summary']['coordinates_coverage']}\n")
                f.write(f"Map Markers: {mapping_data['summary']['map_markers']}\n")
                f.write(f"Regional Clusters: {mapping_data['summary']['regions']}\n\n")
                
                f.write("Regional Distribution:\n")
                for cluster in mapping_data['map_data']['clusters']:
                    f.write(f"  {cluster['name']}: {cluster['grant_count']} grants, {cluster['total_value_formatted']}\n")
                
                f.write("\nState Distribution:\n")
                for state, count in mapping_data['summary']['states'].items():
                    percentage = (count / mapping_data['summary']['total_grants']) * 100
                    f.write(f"  {state}: {count} grants ({percentage:.1f}%)\n")
            
            logger.info(f"Saved enhanced summary to {summary_filename}")
            
        except Exception as e:
            logger.error(f"Error saving enhanced data: {str(e)}")

def main():
    """Main function to enhance the mapping data"""
    processor = EnhancedMappingDataProcessor()
    
    # Load the current mapping data
    mapping_data = processor.load_mapping_data("real_grant_mapping_data_v2.json")
    
    if not mapping_data:
        print("Failed to load mapping data")
        return
    
    # Enhance with coordinates and geographic features
    enhanced_data = processor.enhance_mapping_data(mapping_data)
    
    if enhanced_data:
        # Save the enhanced data
        processor.save_enhanced_data(enhanced_data, "enhanced_grant_mapping_data.json")
        
        # Print summary
        print(f"\n=== ENHANCEMENT SUMMARY ===")
        print(f"Total grants: {enhanced_data['summary']['total_grants']}")
        print(f"Coordinates added: {enhanced_data['summary']['coordinates_coverage']}")
        print(f"Map markers created: {enhanced_data['summary']['map_markers']}")
        print(f"Regional clusters: {enhanced_data['summary']['regions']}")
        
        print(f"\nRegional clusters:")
        for cluster in enhanced_data['map_data']['clusters']:
            print(f"  {cluster['name']}: {cluster['grant_count']} grants, {cluster['total_value_formatted']}")
    else:
        print("Failed to enhance mapping data")

if __name__ == "__main__":
    main()

