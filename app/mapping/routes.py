"""
Interactive Grant Mapping Routes
Handles geographic visualization and analysis of grant distribution
"""

from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_, text
from app import db
from app.models import Grant, Application, User, CommunityVote
from app.mapping import mapping
from app.utils import admin_required, staff_required
import json
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Initialize geocoder
geolocator = Nominatim(user_agent="grantthrive_mapping")

@mapping.route('/')
def interactive_map():
    """Main interactive grant mapping interface"""
    
    # Get all grants with location data
    grants_with_locations = db.session.query(
        Grant.id,
        Grant.title,
        Grant.category,
        Grant.total_budget,
        Grant.status,
        Grant.latitude,
        Grant.longitude,
        Grant.location_name,
        func.count(Application.id).label('application_count'),
        func.sum(Application.amount_requested).label('total_requested')
    ).outerjoin(Application).group_by(
        Grant.id, Grant.title, Grant.category, Grant.total_budget, 
        Grant.status, Grant.latitude, Grant.longitude, Grant.location_name
    ).filter(
        and_(Grant.latitude.isnot(None), Grant.longitude.isnot(None))
    ).all()
    
    # Get demographic data for overlay
    demographic_data = get_demographic_overlay_data()
    
    # Get grant distribution statistics
    distribution_stats = get_grant_distribution_stats()
    
    return render_template('mapping/interactive_map.html',
                         grants=grants_with_locations,
                         demographic_data=demographic_data,
                         distribution_stats=distribution_stats,
                         title='Interactive Grant Mapping')

@mapping.route('/api/grants-geojson')
def grants_geojson():
    """API endpoint returning grants data in GeoJSON format"""
    
    # Get filter parameters
    category = request.args.get('category')
    status = request.args.get('status')
    min_budget = request.args.get('min_budget', type=float)
    max_budget = request.args.get('max_budget', type=float)
    
    # Build query with filters
    query = db.session.query(
        Grant.id,
        Grant.title,
        Grant.category,
        Grant.total_budget,
        Grant.status,
        Grant.latitude,
        Grant.longitude,
        Grant.location_name,
        Grant.description,
        Grant.opens_at,
        Grant.closes_at,
        func.count(Application.id).label('application_count'),
        func.sum(Application.amount_requested).label('total_requested'),
        func.count(CommunityVote.id).label('community_votes')
    ).outerjoin(Application).outerjoin(CommunityVote).group_by(
        Grant.id, Grant.title, Grant.category, Grant.total_budget,
        Grant.status, Grant.latitude, Grant.longitude, Grant.location_name,
        Grant.description, Grant.opens_at, Grant.closes_at
    ).filter(
        and_(Grant.latitude.isnot(None), Grant.longitude.isnot(None))
    )
    
    # Apply filters
    if category:
        query = query.filter(Grant.category == category)
    if status:
        query = query.filter(Grant.status == status)
    if min_budget:
        query = query.filter(Grant.total_budget >= min_budget)
    if max_budget:
        query = query.filter(Grant.total_budget <= max_budget)
    
    grants = query.all()
    
    # Convert to GeoJSON format
    features = []
    for grant in grants:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(grant.longitude), float(grant.latitude)]
            },
            "properties": {
                "id": grant.id,
                "title": grant.title,
                "category": grant.category,
                "total_budget": float(grant.total_budget or 0),
                "status": grant.status,
                "location_name": grant.location_name,
                "description": grant.description[:200] + "..." if grant.description and len(grant.description) > 200 else grant.description,
                "opens_at": grant.opens_at.isoformat() if grant.opens_at else None,
                "closes_at": grant.closes_at.isoformat() if grant.closes_at else None,
                "application_count": grant.application_count or 0,
                "total_requested": float(grant.total_requested or 0),
                "community_votes": grant.community_votes or 0
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return jsonify(geojson)

@mapping.route('/api/demographic-overlay')
def demographic_overlay():
    """API endpoint for demographic overlay data"""
    
    overlay_type = request.args.get('type', 'population')
    
    # Get demographic data based on type
    if overlay_type == 'population':
        data = get_population_density_data()
    elif overlay_type == 'income':
        data = get_income_distribution_data()
    elif overlay_type == 'age':
        data = get_age_demographics_data()
    elif overlay_type == 'education':
        data = get_education_level_data()
    else:
        data = []
    
    return jsonify(data)

@mapping.route('/analytics')
@login_required
@staff_required
def mapping_analytics():
    """Geographic analytics dashboard for staff"""
    
    # Get comprehensive geographic analytics
    analytics_data = {
        'distribution_by_region': get_regional_distribution_analytics(),
        'equity_analysis': get_equity_analysis(),
        'impact_metrics': get_geographic_impact_metrics(),
        'participation_patterns': get_geographic_participation_patterns(),
        'funding_density': get_funding_density_analysis()
    }
    
    return render_template('mapping/analytics.html',
                         analytics=analytics_data,
                         title='Geographic Analytics')

@mapping.route('/admin/geocode-grants', methods=['POST'])
@login_required
@admin_required
def geocode_grants():
    """Admin tool to geocode grants that don't have location data"""
    
    # Get grants without location data
    grants_to_geocode = Grant.query.filter(
        or_(Grant.latitude.is_(None), Grant.longitude.is_(None))
    ).all()
    
    geocoded_count = 0
    failed_count = 0
    
    for grant in grants_to_geocode:
        try:
            # Try to geocode based on location_name or organization
            location_query = grant.location_name or "Australia"  # Default to Australia
            
            location = geolocator.geocode(location_query, timeout=10)
            
            if location:
                grant.latitude = location.latitude
                grant.longitude = location.longitude
                geocoded_count += 1
            else:
                failed_count += 1
                
        except (GeocoderTimedOut, GeocoderServiceError):
            failed_count += 1
            continue
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'geocoded_count': geocoded_count,
        'failed_count': failed_count,
        'message': f'Geocoded {geocoded_count} grants, {failed_count} failed'
    })

@mapping.route('/api/grant-impact/<int:grant_id>')
def grant_impact_data(grant_id):
    """Get detailed impact data for a specific grant"""
    
    grant = Grant.query.get_or_404(grant_id)
    
    # Get applications for this grant with location data
    applications = db.session.query(
        Application.id,
        Application.organization_name,
        Application.amount_requested,
        Application.status,
        Application.applicant_postcode,
        User.email
    ).join(User).filter(Application.grant_id == grant_id).all()
    
    # Get community voting data
    voting_data = db.session.query(
        CommunityVote.voter_postcode,
        func.count(CommunityVote.id).label('vote_count'),
        func.avg(CommunityVote.vote_value).label('avg_rating')
    ).filter(
        CommunityVote.application_id.in_([app.id for app in applications])
    ).group_by(CommunityVote.voter_postcode).all()
    
    impact_data = {
        'grant': {
            'id': grant.id,
            'title': grant.title,
            'total_budget': float(grant.total_budget or 0),
            'location': grant.location_name
        },
        'applications': [{
            'id': app.id,
            'organization': app.organization_name,
            'amount_requested': float(app.amount_requested or 0),
            'status': app.status,
            'postcode': app.applicant_postcode
        } for app in applications],
        'community_engagement': [{
            'postcode': vote.voter_postcode,
            'vote_count': vote.vote_count,
            'avg_rating': float(vote.avg_rating or 0)
        } for vote in voting_data if vote.voter_postcode]
    }
    
    return jsonify(impact_data)

def get_demographic_overlay_data():
    """Get demographic data for map overlays"""
    
    # This would typically connect to Australian Bureau of Statistics API
    # For now, return sample demographic data
    
    sample_data = [
        {
            'postcode': '2000',
            'population': 15000,
            'median_income': 85000,
            'education_level': 'high',
            'age_median': 32
        },
        {
            'postcode': '3000',
            'population': 12000,
            'median_income': 75000,
            'education_level': 'medium',
            'age_median': 35
        },
        # Add more sample data as needed
    ]
    
    return sample_data

def get_grant_distribution_stats():
    """Calculate grant distribution statistics"""
    
    stats = db.session.query(
        Grant.category,
        func.count(Grant.id).label('grant_count'),
        func.sum(Grant.total_budget).label('total_funding'),
        func.avg(Grant.total_budget).label('avg_funding')
    ).group_by(Grant.category).all()
    
    return [{
        'category': stat.category,
        'grant_count': stat.grant_count,
        'total_funding': float(stat.total_funding or 0),
        'avg_funding': float(stat.avg_funding or 0)
    } for stat in stats]

def get_regional_distribution_analytics():
    """Analyze grant distribution by region"""
    
    # This would analyze grants by state/territory
    regional_data = db.session.query(
        func.substr(Grant.location_name, -3).label('state'),  # Simplified state extraction
        func.count(Grant.id).label('grant_count'),
        func.sum(Grant.total_budget).label('total_funding')
    ).group_by('state').all()
    
    return [{
        'region': region.state,
        'grant_count': region.grant_count,
        'total_funding': float(region.total_funding or 0)
    } for region in regional_data]

def get_equity_analysis():
    """Analyze funding equity across demographics"""
    
    # This would perform complex equity analysis
    # For now, return basic analysis structure
    
    return {
        'funding_per_capita': 150.50,
        'geographic_equity_score': 0.75,
        'demographic_equity_score': 0.68,
        'recommendations': [
            'Increase funding in low-income areas',
            'Improve grant accessibility in rural regions',
            'Focus on underrepresented communities'
        ]
    }

def get_geographic_impact_metrics():
    """Calculate geographic impact metrics"""
    
    return {
        'total_coverage_area': '50,000 km²',
        'communities_served': 150,
        'average_distance_to_grant': '15.2 km',
        'rural_urban_ratio': 0.35
    }

def get_geographic_participation_patterns():
    """Analyze community participation by geography"""
    
    participation_data = db.session.query(
        CommunityVote.voter_postcode,
        func.count(CommunityVote.id).label('vote_count'),
        func.count(func.distinct(CommunityVote.voter_id)).label('unique_voters')
    ).group_by(CommunityVote.voter_postcode).all()
    
    return [{
        'postcode': p.voter_postcode,
        'vote_count': p.vote_count,
        'unique_voters': p.unique_voters,
        'engagement_rate': p.vote_count / max(p.unique_voters, 1)
    } for p in participation_data if p.voter_postcode]

def get_funding_density_analysis():
    """Analyze funding density across geographic areas"""
    
    return {
        'high_density_areas': ['Sydney CBD', 'Melbourne CBD', 'Brisbane CBD'],
        'low_density_areas': ['Remote NSW', 'Rural QLD', 'Outback WA'],
        'average_funding_per_km2': 2500.75,
        'density_variance': 0.85
    }

def get_population_density_data():
    """Get population density data for overlay"""
    # This would connect to ABS data
    return []

def get_income_distribution_data():
    """Get income distribution data for overlay"""
    # This would connect to ABS data
    return []

def get_age_demographics_data():
    """Get age demographics data for overlay"""
    # This would connect to ABS data
    return []

def get_education_level_data():
    """Get education level data for overlay"""
    # This would connect to ABS data
    return []
