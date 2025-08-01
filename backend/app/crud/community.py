"""
GrantThrive Community CRUD Operations
Database operations for community features
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.community import (
    ForumCategory, ForumTopic, ForumPost, ForumTopicLike, ForumPostLike,
    ResourceCategory, Resource, ResourceLike, ResourceRating,
    UserFollow
)
from ..schemas.community import (
    ForumCategoryCreate, ForumCategoryUpdate,
    ForumTopicCreate, ForumTopicUpdate,
    ForumPostCreate, ForumPostUpdate,
    ResourceCategoryCreate, ResourceCategoryUpdate,
    ResourceCreate, ResourceUpdate,
    ResourceRatingCreate, ResourceRatingUpdate,
    UserFollowCreate
)


# Forum Category CRUD
def create_forum_category(db: Session, category: ForumCategoryCreate, user_id: int) -> ForumCategory:
    """Create a new forum category"""
    db_category = ForumCategory(
        **category.model_dump(),
        created_by=user_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_forum_categories(
    db: Session, 
    organization_id: Optional[int] = None,
    is_active: bool = True,
    skip: int = 0, 
    limit: int = 100
) -> List[ForumCategory]:
    """Get forum categories"""
    query = db.query(ForumCategory).filter(ForumCategory.is_active == is_active)
    
    if organization_id:
        query = query.filter(
            or_(
                ForumCategory.is_global == True,
                ForumCategory.organization_id == organization_id
            )
        )
    else:
        query = query.filter(ForumCategory.is_global == True)
    
    return query.order_by(ForumCategory.sort_order, ForumCategory.name).offset(skip).limit(limit).all()


def get_forum_category(db: Session, category_id: int) -> Optional[ForumCategory]:
    """Get forum category by ID"""
    return db.query(ForumCategory).filter(ForumCategory.id == category_id).first()


def update_forum_category(
    db: Session, 
    category_id: int, 
    category_update: ForumCategoryUpdate
) -> Optional[ForumCategory]:
    """Update forum category"""
    db_category = get_forum_category(db, category_id)
    if not db_category:
        return None
    
    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_forum_category(db: Session, category_id: int) -> bool:
    """Delete forum category"""
    db_category = get_forum_category(db, category_id)
    if not db_category:
        return False
    
    db.delete(db_category)
    db.commit()
    return True


# Forum Topic CRUD
def create_forum_topic(db: Session, topic: ForumTopicCreate, user_id: int) -> ForumTopic:
    """Create a new forum topic"""
    # Generate slug from title
    slug = topic.title.lower().replace(" ", "-").replace("'", "")[:255]
    
    db_topic = ForumTopic(
        **topic.model_dump(),
        slug=slug,
        author_id=user_id,
        last_post_at=datetime.utcnow(),
        last_post_by=user_id
    )
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    
    # Update category topic count
    category = get_forum_category(db, topic.category_id)
    if category:
        category.topic_count += 1
        db.commit()
    
    return db_topic


def get_forum_topics(
    db: Session,
    category_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    is_featured: Optional[bool] = None,
    is_pinned: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> List[ForumTopic]:
    """Get forum topics with filters"""
    query = db.query(ForumTopic).filter(ForumTopic.is_approved == True)
    
    if category_id:
        query = query.filter(ForumTopic.category_id == category_id)
    
    if organization_id:
        query = query.filter(
            or_(
                ForumTopic.organization_id == organization_id,
                ForumTopic.organization_id.is_(None)
            )
        )
    
    if is_featured is not None:
        query = query.filter(ForumTopic.is_featured == is_featured)
    
    if is_pinned is not None:
        query = query.filter(ForumTopic.is_pinned == is_pinned)
    
    if search:
        query = query.filter(
            or_(
                ForumTopic.title.contains(search),
                ForumTopic.content.contains(search)
            )
        )
    
    # Order by pinned first, then by last activity
    return query.order_by(
        desc(ForumTopic.is_pinned),
        desc(ForumTopic.last_post_at)
    ).offset(skip).limit(limit).all()


def get_forum_topic(db: Session, topic_id: int) -> Optional[ForumTopic]:
    """Get forum topic by ID"""
    return db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()


def update_forum_topic(
    db: Session,
    topic_id: int,
    topic_update: ForumTopicUpdate
) -> Optional[ForumTopic]:
    """Update forum topic"""
    db_topic = get_forum_topic(db, topic_id)
    if not db_topic:
        return None
    
    update_data = topic_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_topic, field, value)
    
    db_topic.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_topic)
    return db_topic


def increment_topic_views(db: Session, topic_id: int) -> None:
    """Increment topic view count"""
    db_topic = get_forum_topic(db, topic_id)
    if db_topic:
        db_topic.view_count += 1
        db.commit()


# Forum Post CRUD
def create_forum_post(db: Session, post: ForumPostCreate, user_id: int) -> ForumPost:
    """Create a new forum post"""
    db_post = ForumPost(
        **post.model_dump(),
        author_id=user_id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    # Update topic reply count and last post info
    topic = get_forum_topic(db, post.topic_id)
    if topic:
        topic.reply_count += 1
        topic.last_post_at = datetime.utcnow()
        topic.last_post_by = user_id
        db.commit()
        
        # Update category post count
        category = get_forum_category(db, topic.category_id)
        if category:
            category.post_count += 1
            db.commit()
    
    return db_post


def get_forum_posts(
    db: Session,
    topic_id: int,
    skip: int = 0,
    limit: int = 50
) -> List[ForumPost]:
    """Get forum posts for a topic"""
    return db.query(ForumPost).filter(
        and_(
            ForumPost.topic_id == topic_id,
            ForumPost.is_approved == True
        )
    ).order_by(ForumPost.created_at).offset(skip).limit(limit).all()


def get_forum_post(db: Session, post_id: int) -> Optional[ForumPost]:
    """Get forum post by ID"""
    return db.query(ForumPost).filter(ForumPost.id == post_id).first()


def update_forum_post(
    db: Session,
    post_id: int,
    post_update: ForumPostUpdate,
    user_id: int
) -> Optional[ForumPost]:
    """Update forum post"""
    db_post = get_forum_post(db, post_id)
    if not db_post:
        return None
    
    update_data = post_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_post, field, value)
    
    db_post.updated_at = datetime.utcnow()
    db_post.edited_at = datetime.utcnow()
    db_post.edited_by = user_id
    
    db.commit()
    db.refresh(db_post)
    return db_post


# Like Operations
def toggle_topic_like(db: Session, topic_id: int, user_id: int) -> bool:
    """Toggle topic like (returns True if liked, False if unliked)"""
    existing_like = db.query(ForumTopicLike).filter(
        and_(
            ForumTopicLike.topic_id == topic_id,
            ForumTopicLike.user_id == user_id
        )
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        # Decrement like count
        topic = get_forum_topic(db, topic_id)
        if topic and topic.like_count > 0:
            topic.like_count -= 1
        db.commit()
        return False
    else:
        # Like
        new_like = ForumTopicLike(topic_id=topic_id, user_id=user_id)
        db.add(new_like)
        # Increment like count
        topic = get_forum_topic(db, topic_id)
        if topic:
            topic.like_count += 1
        db.commit()
        return True


def toggle_post_like(db: Session, post_id: int, user_id: int) -> bool:
    """Toggle post like (returns True if liked, False if unliked)"""
    existing_like = db.query(ForumPostLike).filter(
        and_(
            ForumPostLike.post_id == post_id,
            ForumPostLike.user_id == user_id
        )
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        # Decrement like count
        post = get_forum_post(db, post_id)
        if post and post.like_count > 0:
            post.like_count -= 1
        db.commit()
        return False
    else:
        # Like
        new_like = ForumPostLike(post_id=post_id, user_id=user_id)
        db.add(new_like)
        # Increment like count
        post = get_forum_post(db, post_id)
        if post:
            post.like_count += 1
        db.commit()
        return True


# Resource Category CRUD
def create_resource_category(db: Session, category: ResourceCategoryCreate, user_id: int) -> ResourceCategory:
    """Create a new resource category"""
    db_category = ResourceCategory(
        **category.model_dump(),
        created_by=user_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_resource_categories(
    db: Session,
    organization_id: Optional[int] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100
) -> List[ResourceCategory]:
    """Get resource categories"""
    query = db.query(ResourceCategory).filter(ResourceCategory.is_active == is_active)
    
    if organization_id:
        query = query.filter(
            or_(
                ResourceCategory.is_global == True,
                ResourceCategory.organization_id == organization_id
            )
        )
    else:
        query = query.filter(ResourceCategory.is_global == True)
    
    return query.order_by(ResourceCategory.sort_order, ResourceCategory.name).offset(skip).limit(limit).all()


# Resource CRUD
def create_resource(db: Session, resource: ResourceCreate, user_id: int) -> Resource:
    """Create a new resource"""
    # Generate slug from title
    slug = resource.title.lower().replace(" ", "-").replace("'", "")[:255]
    
    db_resource = Resource(
        **resource.model_dump(),
        slug=slug,
        author_id=user_id
    )
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    
    # Update category resource count
    category = db.query(ResourceCategory).filter(ResourceCategory.id == resource.category_id).first()
    if category:
        category.resource_count += 1
        db.commit()
    
    return db_resource


def get_resources(
    db: Session,
    category_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    organization_id: Optional[int] = None,
    is_featured: Optional[bool] = None,
    is_public: bool = True,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> List[Resource]:
    """Get resources with filters"""
    query = db.query(Resource).filter(
        and_(
            Resource.is_approved == True,
            Resource.is_public == is_public
        )
    )
    
    if category_id:
        query = query.filter(Resource.category_id == category_id)
    
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)
    
    if organization_id:
        query = query.filter(
            or_(
                Resource.organization_id == organization_id,
                Resource.organization_id.is_(None)
            )
        )
    
    if is_featured is not None:
        query = query.filter(Resource.is_featured == is_featured)
    
    if search:
        query = query.filter(
            or_(
                Resource.title.contains(search),
                Resource.description.contains(search)
            )
        )
    
    return query.order_by(
        desc(Resource.is_featured),
        desc(Resource.created_at)
    ).offset(skip).limit(limit).all()


def get_resource(db: Session, resource_id: int) -> Optional[Resource]:
    """Get resource by ID"""
    return db.query(Resource).filter(Resource.id == resource_id).first()


def increment_resource_views(db: Session, resource_id: int) -> None:
    """Increment resource view count"""
    db_resource = get_resource(db, resource_id)
    if db_resource:
        db_resource.view_count += 1
        db.commit()


def increment_resource_downloads(db: Session, resource_id: int) -> None:
    """Increment resource download count"""
    db_resource = get_resource(db, resource_id)
    if db_resource:
        db_resource.download_count += 1
        db.commit()


# User Follow CRUD
def create_user_follow(db: Session, follow: UserFollowCreate, follower_id: int) -> UserFollow:
    """Create user follow relationship"""
    # Check if already following
    existing = db.query(UserFollow).filter(
        and_(
            UserFollow.follower_id == follower_id,
            UserFollow.following_id == follow.following_id
        )
    ).first()
    
    if existing:
        return existing
    
    db_follow = UserFollow(
        follower_id=follower_id,
        following_id=follow.following_id
    )
    db.add(db_follow)
    db.commit()
    db.refresh(db_follow)
    return db_follow


def delete_user_follow(db: Session, following_id: int, follower_id: int) -> bool:
    """Delete user follow relationship"""
    db_follow = db.query(UserFollow).filter(
        and_(
            UserFollow.follower_id == follower_id,
            UserFollow.following_id == following_id
        )
    ).first()
    
    if not db_follow:
        return False
    
    db.delete(db_follow)
    db.commit()
    return True


def get_user_followers(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[UserFollow]:
    """Get user's followers"""
    return db.query(UserFollow).filter(
        UserFollow.following_id == user_id
    ).offset(skip).limit(limit).all()


def get_user_following(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[UserFollow]:
    """Get users that user is following"""
    return db.query(UserFollow).filter(
        UserFollow.follower_id == user_id
    ).offset(skip).limit(limit).all()

