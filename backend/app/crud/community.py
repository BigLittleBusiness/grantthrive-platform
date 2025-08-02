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



# User Connection CRUD Operations
def create_user_connection(db: Session, connection: "UserConnectionCreate", requester_id: int):
    """Create a new user connection request"""
    from ..models.community import UserConnection
    
    # Check if connection already exists
    existing = db.query(UserConnection).filter(
        or_(
            and_(UserConnection.requester_id == requester_id, UserConnection.target_id == connection.target_id),
            and_(UserConnection.requester_id == connection.target_id, UserConnection.target_id == requester_id)
        )
    ).first()
    
    if existing:
        return existing
    
    db_connection = UserConnection(
        requester_id=requester_id,
        target_id=connection.target_id,
        message=connection.message,
        status="pending"
    )
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection

def get_user_connections(db: Session, user_id: int, status: Optional[str] = None, skip: int = 0, limit: int = 100):
    """Get user connections"""
    from ..models.community import UserConnection
    
    query = db.query(UserConnection).filter(
        or_(UserConnection.requester_id == user_id, UserConnection.target_id == user_id)
    )
    
    if status:
        query = query.filter(UserConnection.status == status)
    
    return query.offset(skip).limit(limit).all()

def update_connection_status(db: Session, connection_id: int, status: str, user_id: int):
    """Update connection status"""
    from ..models.community import UserConnection
    
    connection = db.query(UserConnection).filter(UserConnection.id == connection_id).first()
    if not connection:
        return None
    
    # Only target user can accept/reject, both can block
    if status in ["accepted", "rejected"] and connection.target_id != user_id:
        return None
    
    connection.status = status
    connection.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(connection)
    return connection

# Networking Events CRUD
def create_networking_event(db: Session, event: "NetworkingEventCreate", organizer_id: int, organization_id: int):
    """Create a networking event"""
    from ..models.community import NetworkingEvent
    
    db_event = NetworkingEvent(
        **event.model_dump(),
        organizer_id=organizer_id,
        organization_id=organization_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_networking_events(
    db: Session, 
    organization_id: int,
    event_type: Optional[str] = None,
    is_virtual: Optional[bool] = None,
    upcoming_only: bool = True,
    skip: int = 0, 
    limit: int = 50
):
    """Get networking events"""
    from ..models.community import NetworkingEvent
    
    query = db.query(NetworkingEvent).filter(NetworkingEvent.organization_id == organization_id)
    
    if event_type:
        query = query.filter(NetworkingEvent.event_type == event_type)
    
    if is_virtual is not None:
        query = query.filter(NetworkingEvent.is_virtual == is_virtual)
    
    if upcoming_only:
        query = query.filter(NetworkingEvent.start_time > datetime.utcnow())
    
    return query.order_by(NetworkingEvent.start_time).offset(skip).limit(limit).all()

def get_event_by_id(db: Session, event_id: int):
    """Get event by ID"""
    from ..models.community import NetworkingEvent
    return db.query(NetworkingEvent).filter(NetworkingEvent.id == event_id).first()

def register_for_event(db: Session, event_id: int, user_id: int, registration_data: "EventRegistrationCreate"):
    """Register user for event"""
    from ..models.community import EventRegistration
    
    # Check if already registered
    existing = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.user_id == user_id
    ).first()
    
    if existing:
        return existing
    
    db_registration = EventRegistration(
        event_id=event_id,
        user_id=user_id,
        **registration_data.model_dump()
    )
    db.add(db_registration)
    db.commit()
    db.refresh(db_registration)
    return db_registration

def get_event_registrations(db: Session, event_id: int):
    """Get event registrations"""
    from ..models.community import EventRegistration
    return db.query(EventRegistration).filter(EventRegistration.event_id == event_id).all()

# User Interests CRUD
def get_user_interests(db: Session, user_id: int):
    """Get user interests"""
    from ..models.community import UserInterest
    return db.query(UserInterest).filter(UserInterest.user_id == user_id).all()

def create_user_interest(db: Session, user_id: int, interest: "UserInterestCreate"):
    """Create user interest"""
    from ..models.community import UserInterest
    
    db_interest = UserInterest(
        user_id=user_id,
        **interest.model_dump()
    )
    db.add(db_interest)
    db.commit()
    db.refresh(db_interest)
    return db_interest

def delete_user_interest(db: Session, interest_id: int, user_id: int):
    """Delete user interest"""
    from ..models.community import UserInterest
    
    interest = db.query(UserInterest).filter(
        UserInterest.id == interest_id,
        UserInterest.user_id == user_id
    ).first()
    
    if interest:
        db.delete(interest)
        db.commit()
        return True
    return False

# Success Stories CRUD
def create_success_story(db: Session, story: "SuccessStoryCreate", author_id: int, organization_id: int):
    """Create a success story"""
    from ..models.success_stories import SuccessStory
    
    db_story = SuccessStory(
        **story.model_dump(),
        author_id=author_id,
        organization_id=organization_id,
        status="pending"
    )
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    return db_story

def get_success_stories(
    db: Session,
    organization_id: int,
    status: Optional[str] = "approved",
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """Get success stories"""
    from ..models.success_stories import SuccessStory
    
    query = db.query(SuccessStory).filter(SuccessStory.organization_id == organization_id)
    
    if status:
        query = query.filter(SuccessStory.status == status)
    
    if category:
        query = query.filter(SuccessStory.category == category)
    
    return query.order_by(desc(SuccessStory.created_at)).offset(skip).limit(limit).all()

def get_story_by_id(db: Session, story_id: int):
    """Get story by ID"""
    from ..models.success_stories import SuccessStory
    return db.query(SuccessStory).filter(SuccessStory.id == story_id).first()

def update_success_story(db: Session, story_id: int, story_update: "SuccessStoryUpdate"):
    """Update success story"""
    from ..models.success_stories import SuccessStory
    
    story = db.query(SuccessStory).filter(SuccessStory.id == story_id).first()
    if not story:
        return None
    
    for field, value in story_update.model_dump(exclude_unset=True).items():
        setattr(story, field, value)
    
    story.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(story)
    return story

def delete_success_story(db: Session, story_id: int):
    """Delete success story"""
    from ..models.success_stories import SuccessStory
    
    story = db.query(SuccessStory).filter(SuccessStory.id == story_id).first()
    if story:
        db.delete(story)
        db.commit()
        return True
    return False

def approve_success_story(db: Session, story_id: int, approved: bool, reviewer_id: int, feedback: Optional[str] = None):
    """Approve or reject success story"""
    from ..models.success_stories import SuccessStory
    
    story = db.query(SuccessStory).filter(SuccessStory.id == story_id).first()
    if not story:
        return None
    
    story.status = "approved" if approved else "rejected"
    story.reviewed_by = reviewer_id
    story.reviewed_at = datetime.utcnow()
    if feedback:
        story.review_feedback = feedback
    
    db.commit()
    db.refresh(story)
    return story

def get_featured_stories(db: Session, organization_id: int, skip: int = 0, limit: int = 10):
    """Get featured success stories"""
    from ..models.success_stories import SuccessStory
    
    return db.query(SuccessStory).filter(
        SuccessStory.organization_id == organization_id,
        SuccessStory.status == "approved",
        SuccessStory.is_featured == True
    ).order_by(desc(SuccessStory.created_at)).offset(skip).limit(limit).all()

def like_success_story(db: Session, story_id: int, user_id: int):
    """Like or unlike a success story"""
    from ..models.success_stories import StoryLike
    
    existing_like = db.query(StoryLike).filter(
        StoryLike.story_id == story_id,
        StoryLike.user_id == user_id
    ).first()
    
    if existing_like:
        db.delete(existing_like)
        db.commit()
        return {"liked": False, "message": "Like removed"}
    else:
        new_like = StoryLike(story_id=story_id, user_id=user_id)
        db.add(new_like)
        db.commit()
        return {"liked": True, "message": "Story liked"}

def create_story_comment(db: Session, story_id: int, comment: "StoryCommentCreate", author_id: int):
    """Create story comment"""
    from ..models.success_stories import StoryComment
    
    db_comment = StoryComment(
        story_id=story_id,
        author_id=author_id,
        **comment.model_dump()
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_story_comments(db: Session, story_id: int, skip: int = 0, limit: int = 50):
    """Get story comments"""
    from ..models.success_stories import StoryComment
    
    return db.query(StoryComment).filter(
        StoryComment.story_id == story_id
    ).order_by(StoryComment.created_at).offset(skip).limit(limit).all()



# ===== NETWORKING CRUD FUNCTIONS =====

def create_user_connection(db: Session, connection: "UserConnectionCreate", requester_id: int):
    """Create a user connection request"""
    from ..models.community import UserConnection
    
    # Check if connection already exists
    existing = db.query(UserConnection).filter(
        or_(
            and_(UserConnection.requester_id == requester_id, UserConnection.requested_id == connection.requested_id),
            and_(UserConnection.requester_id == connection.requested_id, UserConnection.requested_id == requester_id)
        )
    ).first()
    
    if existing:
        raise ValueError("Connection already exists")
    
    db_connection = UserConnection(
        requester_id=requester_id,
        requested_id=connection.requested_id,
        message=connection.message,
        status="pending"
    )
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection

def get_user_connections(db: Session, user_id: int, status: Optional[str] = None, skip: int = 0, limit: int = 100):
    """Get user connections"""
    from ..models.community import UserConnection
    
    query = db.query(UserConnection).filter(
        or_(UserConnection.requester_id == user_id, UserConnection.requested_id == user_id)
    )
    
    if status:
        query = query.filter(UserConnection.status == status)
    
    return query.order_by(desc(UserConnection.created_at)).offset(skip).limit(limit).all()

def update_connection_status(db: Session, connection_id: int, status: str, user_id: int):
    """Update connection status (accept/reject)"""
    from ..models.community import UserConnection
    
    connection = db.query(UserConnection).filter(UserConnection.id == connection_id).first()
    if not connection:
        raise ValueError("Connection not found")
    
    # Only the requested user can accept/reject
    if connection.requested_id != user_id:
        raise ValueError("Not authorized to update this connection")
    
    connection.status = status
    connection.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(connection)
    return connection

def create_networking_event(db: Session, event: "NetworkingEventCreate", organizer_id: int):
    """Create a networking event"""
    from ..models.community import NetworkingEvent
    
    db_event = NetworkingEvent(
        **event.model_dump(),
        organizer_id=organizer_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_networking_events(db: Session, organization_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    """Get networking events"""
    from ..models.community import NetworkingEvent
    
    query = db.query(NetworkingEvent).filter(NetworkingEvent.is_active == True)
    
    if organization_id:
        query = query.filter(NetworkingEvent.organization_id == organization_id)
    
    return query.order_by(NetworkingEvent.event_date).offset(skip).limit(limit).all()

def get_event_by_id(db: Session, event_id: int):
    """Get event by ID"""
    from ..models.community import NetworkingEvent
    
    return db.query(NetworkingEvent).filter(NetworkingEvent.id == event_id).first()

def register_for_event(db: Session, registration: "EventRegistrationCreate", user_id: int):
    """Register for an event"""
    from ..models.community import EventRegistration
    
    # Check if already registered
    existing = db.query(EventRegistration).filter(
        EventRegistration.event_id == registration.event_id,
        EventRegistration.user_id == user_id
    ).first()
    
    if existing:
        raise ValueError("Already registered for this event")
    
    db_registration = EventRegistration(
        event_id=registration.event_id,
        user_id=user_id,
        registration_notes=registration.registration_notes
    )
    db.add(db_registration)
    db.commit()
    db.refresh(db_registration)
    return db_registration

def get_event_registrations(db: Session, event_id: int, skip: int = 0, limit: int = 100):
    """Get event registrations"""
    from ..models.community import EventRegistration
    
    return db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id
    ).order_by(EventRegistration.created_at).offset(skip).limit(limit).all()

def get_user_interests(db: Session, user_id: int):
    """Get user interests"""
    from ..models.community import UserInterest
    
    return db.query(UserInterest).filter(UserInterest.user_id == user_id).all()

def create_user_interest(db: Session, interest: "UserInterestCreate", user_id: int):
    """Create user interest"""
    from ..models.community import UserInterest
    
    # Check if interest already exists
    existing = db.query(UserInterest).filter(
        UserInterest.user_id == user_id,
        UserInterest.interest_name == interest.interest_name
    ).first()
    
    if existing:
        raise ValueError("Interest already exists")
    
    db_interest = UserInterest(
        user_id=user_id,
        **interest.model_dump()
    )
    db.add(db_interest)
    db.commit()
    db.refresh(db_interest)
    return db_interest

def delete_user_interest(db: Session, interest_id: int, user_id: int):
    """Delete user interest"""
    from ..models.community import UserInterest
    
    interest = db.query(UserInterest).filter(
        UserInterest.id == interest_id,
        UserInterest.user_id == user_id
    ).first()
    
    if not interest:
        raise ValueError("Interest not found")
    
    db.delete(interest)
    db.commit()
    return {"message": "Interest deleted successfully"}

