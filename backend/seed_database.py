"""
GrantThrive Database Seeding Script
Creates comprehensive sample data for development and testing
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add the app directory to the Python path
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.user import User, UserRole, UserStatus
from app.models.grant import Grant, Application, GrantStatus, ApplicationStatus
from app.models.community import *
from app.models.marketplace import *
from app.models.success_stories import *
from app.models.gamification import *
from app.models.feature_toggles import *
from app.core.security import get_password_hash


def create_sample_users(db: Session):
    """Create sample users with different roles"""
    print("Creating sample users...")
    
    users_data = [
        # Super Admin
        {
            "email": "admin@grantthrive.com",
            "username": "admin",
            "first_name": "System",
            "last_name": "Administrator",
            "role": UserRole.SUPER_ADMIN,
            "status": UserStatus.ACTIVE,
            "bio": "System administrator for GrantThrive platform"
        },
        # Council Admins
        {
            "email": "council.admin@citycouncil.gov",
            "username": "council_admin",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "role": UserRole.CLIENT_ADMIN,
            "status": UserStatus.ACTIVE,
            "organization_id": 1,
            "organization_name": "City Council",
            "bio": "Grant program administrator for the city council"
        },
        {
            "email": "grants@stateagency.gov",
            "username": "state_admin",
            "first_name": "Michael",
            "last_name": "Chen",
            "role": UserRole.CLIENT_ADMIN,
            "status": UserStatus.ACTIVE,
            "organization_id": 2,
            "organization_name": "State Environmental Agency",
            "bio": "Environmental grants coordinator"
        },
        # Grant Applicants
        {
            "email": "director@nonprofitorg.org",
            "username": "nonprofit_director",
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "role": UserRole.APPLICANT,
            "status": UserStatus.ACTIVE,
            "organization_name": "Community Development Nonprofit",
            "bio": "Executive Director focused on community development and social impact"
        },
        {
            "email": "founder@techstartup.com",
            "username": "tech_founder",
            "first_name": "David",
            "last_name": "Kim",
            "role": UserRole.APPLICANT,
            "status": UserStatus.ACTIVE,
            "organization_name": "GreenTech Innovations",
            "bio": "Founder of sustainable technology startup"
        },
        {
            "email": "researcher@university.edu",
            "username": "researcher",
            "first_name": "Dr. Lisa",
            "last_name": "Thompson",
            "role": UserRole.APPLICANT,
            "status": UserStatus.ACTIVE,
            "organization_name": "University Research Institute",
            "bio": "Research scientist specializing in renewable energy"
        },
        # Professional Service Providers
        {
            "email": "consultant@grantpro.com",
            "username": "grant_consultant",
            "first_name": "Robert",
            "last_name": "Williams",
            "role": UserRole.PROFESSIONAL,
            "status": UserStatus.ACTIVE,
            "organization_name": "Grant Pro Consulting",
            "bio": "Professional grant writer with 15+ years experience"
        },
        {
            "email": "advisor@financialconsult.com",
            "username": "financial_advisor",
            "first_name": "Jennifer",
            "last_name": "Davis",
            "role": UserRole.PROFESSIONAL,
            "status": UserStatus.ACTIVE,
            "organization_name": "Financial Advisory Services",
            "bio": "Financial advisor specializing in nonprofit and startup funding"
        }
    ]
    
    created_users = []
    for user_data in users_data:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            user = User(
                **user_data,
                hashed_password=get_password_hash("password123"),
                is_active=True,
                is_verified=True,
                created_at=datetime.utcnow()
            )
            db.add(user)
            created_users.append(user)
    
    db.commit()
    print(f"Created {len(created_users)} users")
    return created_users


def create_sample_grants(db: Session):
    """Create sample grants"""
    print("Creating sample grants...")
    
    # Get council admins
    council_admin = db.query(User).filter(User.username == "council_admin").first()
    state_admin = db.query(User).filter(User.username == "state_admin").first()
    
    grants_data = [
        {
            "title": "Community Development Grant 2024",
            "slug": "community-development-grant-2024",
            "description": "Supporting local community development projects that improve quality of life for residents. This grant focuses on infrastructure improvements, community centers, and social programs.",
            "total_funding": Decimal("50000.00"),
            "max_amount": Decimal("10000.00"),
            "application_open_date": datetime.utcnow(),
            "application_close_date": datetime.utcnow() + timedelta(days=30),
            "project_start_date": datetime.utcnow() + timedelta(days=60),
            "project_end_date": datetime.utcnow() + timedelta(days=425),
            "status": GrantStatus.PUBLISHED,
            "category": "community",
            "eligibility_criteria": "Nonprofit organizations serving the local community for at least 2 years",
            "application_guidelines": "Project proposal, budget breakdown, organizational documents, letters of support",
            "organization_name": "City Council",
            "contact_email": "grants@citycouncil.gov",
            "contact_person": "Sarah Johnson",
            "created_by": council_admin.id if council_admin else 1,
            "organization_id": 1
        },
        {
            "title": "Environmental Innovation Fund",
            "slug": "environmental-innovation-fund",
            "description": "Funding for innovative environmental solutions and sustainable technology projects. Priority given to projects addressing climate change and environmental conservation.",
            "total_funding": Decimal("100000.00"),
            "max_amount": Decimal("25000.00"),
            "application_open_date": datetime.utcnow(),
            "application_close_date": datetime.utcnow() + timedelta(days=45),
            "project_start_date": datetime.utcnow() + timedelta(days=75),
            "project_end_date": datetime.utcnow() + timedelta(days=440),
            "status": GrantStatus.PUBLISHED,
            "category": "environment",
            "eligibility_criteria": "Startups, research institutions, and nonprofits working on environmental solutions",
            "application_guidelines": "Technical proposal, environmental impact assessment, team qualifications, budget",
            "organization_name": "State Environmental Agency",
            "contact_email": "grants@stateagency.gov",
            "contact_person": "Michael Chen",
            "created_by": state_admin.id if state_admin else 2,
            "organization_id": 2
        },
        {
            "title": "Small Business Recovery Grant",
            "slug": "small-business-recovery-grant",
            "description": "Supporting small businesses affected by economic challenges. Provides funding for operational costs, equipment, and business development.",
            "total_funding": Decimal("25000.00"),
            "max_amount": Decimal("5000.00"),
            "application_open_date": datetime.utcnow(),
            "application_close_date": datetime.utcnow() + timedelta(days=20),
            "project_start_date": datetime.utcnow() + timedelta(days=40),
            "project_end_date": datetime.utcnow() + timedelta(days=405),
            "status": GrantStatus.PUBLISHED,
            "category": "economic_development",
            "eligibility_criteria": "Small businesses with fewer than 50 employees",
            "application_guidelines": "Business plan, financial statements, impact statement",
            "organization_name": "City Council",
            "contact_email": "business@citycouncil.gov",
            "contact_person": "Sarah Johnson",
            "created_by": council_admin.id if council_admin else 1,
            "organization_id": 1
        }
    ]
    
    created_grants = []
    for grant_data in grants_data:
        grant = Grant(**grant_data, created_at=datetime.utcnow())
        db.add(grant)
        created_grants.append(grant)
    
    db.commit()
    print(f"Created {len(created_grants)} grants")
    return created_grants


def create_sample_applications(db: Session, grants, users):
    """Create sample grant applications"""
    print("Creating sample applications...")
    
    # Get applicant users
    applicants = [u for u in users if u.role == UserRole.APPLICANT]
    
    applications_data = []
    for grant in grants[:2]:  # Apply to first 2 grants
        for i, applicant in enumerate(applicants[:2]):  # First 2 applicants
            applications_data.append({
                "grant_id": grant.id,
                "applicant_id": applicant.id,
                "organization_name": applicant.organization_name,
                "project_title": f"Project by {applicant.organization_name}",
                "project_description": f"Innovative project proposal from {applicant.organization_name} addressing the grant objectives.",
                "requested_amount": grant.total_funding * Decimal("0.8"),  # Request 80% of available
                "status": ApplicationStatus.SUBMITTED.value if i == 0 else ApplicationStatus.UNDER_REVIEW.value,
                "submitted_at": datetime.utcnow() - timedelta(days=random.randint(1, 10))
            })
    
    created_applications = []
    for app_data in applications_data:
        application = Application(**app_data, created_at=datetime.utcnow())
        db.add(application)
        created_applications.append(application)
    
    db.commit()
    print(f"Created {len(created_applications)} applications")
    return created_applications


def create_community_data(db: Session, users):
    """Create sample community forum data"""
    print("Creating community forum data...")
    
    # Forum Categories
    categories = [
        {"name": "Grant Writing Tips", "slug": "grant-writing-tips", "description": "Share and discuss grant writing strategies"},
        {"name": "Funding Opportunities", "slug": "funding-opportunities", "description": "Discuss new funding opportunities and trends"},
        {"name": "Success Stories", "slug": "success-stories", "description": "Share your grant success stories"},
        {"name": "General Discussion", "slug": "general-discussion", "description": "General community discussions"}
    ]
    
    created_categories = []
    for cat_data in categories:
        category = ForumCategory(**cat_data, created_at=datetime.utcnow())
        db.add(category)
        created_categories.append(category)
    
    db.commit()
    
    # Forum Topics
    topics_data = [
        {
            "category_id": created_categories[0].id,
            "title": "Best practices for writing compelling grant narratives",
            "author_id": users[3].id,  # nonprofit director
            "is_pinned": True
        },
        {
            "category_id": created_categories[1].id,
            "title": "New environmental grants available for 2024",
            "author_id": users[4].id,  # tech founder
            "is_pinned": False
        },
        {
            "category_id": created_categories[2].id,
            "title": "How we secured $100K for our community project",
            "author_id": users[5].id,  # researcher
            "is_pinned": False
        }
    ]
    
    created_topics = []
    for topic_data in topics_data:
        topic = ForumTopic(**topic_data, created_at=datetime.utcnow())
        db.add(topic)
        created_topics.append(topic)
    
    db.commit()
    
    # Forum Posts
    posts_data = [
        {
            "topic_id": created_topics[0].id,
            "author_id": users[6].id,  # grant consultant
            "content": "Great topic! I always recommend starting with a compelling story that demonstrates the need for your project. Make sure to clearly articulate the problem you're solving and how your solution is unique."
        },
        {
            "topic_id": created_topics[1].id,
            "author_id": users[7].id,  # financial advisor
            "content": "Thanks for sharing! I've been tracking several new environmental funding opportunities. The key is to align your project with current policy priorities and demonstrate measurable environmental impact."
        }
    ]
    
    for post_data in posts_data:
        post = ForumPost(**post_data, created_at=datetime.utcnow())
        db.add(post)
    
    db.commit()
    print("Created community forum data")


def create_marketplace_data(db: Session, users):
    """Create sample marketplace data"""
    print("Creating marketplace data...")
    
    # Get professional users
    professionals = [u for u in users if u.role == UserRole.PROFESSIONAL]
    
    for professional in professionals:
        # Professional Profile
        profile = ProfessionalProfile(
            user_id=professional.id,
            business_name=professional.organization_name,
            title="Senior Grant Consultant" if "consultant" in professional.username else "Financial Advisor",
            bio=professional.bio,
            specializations=["Grant Writing", "Nonprofit Funding"] if "consultant" in professional.username else ["Financial Planning", "Funding Strategy"],
            experience_years=15 if "consultant" in professional.username else 12,
            city="San Francisco",
            state="CA",
            country="USA",
            remote_services=True,
            application_status="approved",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(profile)
        db.commit()
        
        # Professional Services
        if "consultant" in professional.username:
            services = [
                {
                    "professional_id": profile.id,
                    "title": "Grant Proposal Writing",
                    "description": "Comprehensive grant proposal writing service including research, writing, and review.",
                    "category": "grant_writing",
                    "pricing_model": "project",
                    "base_price": Decimal("2500.00"),
                    "duration_hours": 40,
                    "is_active": True
                },
                {
                    "professional_id": profile.id,
                    "title": "Grant Strategy Consultation",
                    "description": "Strategic consultation to identify funding opportunities and develop grant strategy.",
                    "category": "strategic_consulting",
                    "pricing_model": "hourly",
                    "base_price": Decimal("150.00"),
                    "duration_hours": 2,
                    "is_active": True
                }
            ]
        else:
            services = [
                {
                    "professional_id": profile.id,
                    "title": "Financial Planning for Nonprofits",
                    "description": "Comprehensive financial planning and budgeting services for nonprofit organizations.",
                    "category": "financial_advisory",
                    "pricing_model": "project",
                    "base_price": Decimal("1500.00"),
                    "duration_hours": 20,
                    "is_active": True
                }
            ]
        
        for service_data in services:
            service = ProfessionalService(**service_data, created_at=datetime.utcnow())
            db.add(service)
    
    db.commit()
    print("Created marketplace data")


def create_gamification_data(db: Session, users):
    """Create sample gamification data"""
    print("Creating gamification data...")
    
    # Achievements
    achievements_data = [
        {
            "name": "First Application",
            "description": "Submit your first grant application",
            "category": "milestone",
            "type": "application",
            "points_reward": 100,
            "rarity": "common",
            "is_active": True
        },
        {
            "name": "Grant Winner",
            "description": "Successfully receive a grant award",
            "category": "success",
            "type": "award",
            "points_reward": 500,
            "rarity": "rare",
            "is_active": True
        },
        {
            "name": "Community Helper",
            "description": "Help 10 community members in the forum",
            "category": "community",
            "type": "social",
            "points_reward": 250,
            "rarity": "uncommon",
            "is_active": True
        }
    ]
    
    for achievement_data in achievements_data:
        achievement = Achievement(**achievement_data, created_at=datetime.utcnow())
        db.add(achievement)
    
    db.commit()
    
    # User Levels and Points
    for user in users:
        if user.role in [UserRole.APPLICANT, UserRole.PROFESSIONAL]:
            level = UserLevel(
                user_id=user.id,
                category="overall",
                level=random.randint(1, 5),
                total_points=random.randint(100, 1000),
                current_streak=random.randint(0, 10),
                longest_streak=random.randint(5, 20),
                last_activity=datetime.utcnow() - timedelta(days=random.randint(0, 7))
            )
            db.add(level)
    
    db.commit()
    print("Created gamification data")


def main():
    """Main seeding function"""
    print("🌱 Starting GrantThrive database seeding...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create sample data
        users = create_sample_users(db)
        grants = create_sample_grants(db)
        applications = create_sample_applications(db, grants, users)
        create_community_data(db, users)
        create_marketplace_data(db, users)
        create_gamification_data(db, users)
        
        print("\n✅ Database seeding completed successfully!")
        print(f"Created:")
        print(f"  - {len(users)} users")
        print(f"  - {len(grants)} grants") 
        print(f"  - {len(applications)} applications")
        print(f"  - Community forum data")
        print(f"  - Professional marketplace data")
        print(f"  - Gamification data")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

