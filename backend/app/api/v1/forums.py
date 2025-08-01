"""
GrantThrive Forum API Endpoints
RESTful API for discussion forums
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...db.database import get_db
from ...api.deps import get_current_user, get_current_active_user
from ...models.user import User
from ...schemas.community import (
    ForumCategory, ForumCategoryCreate, ForumCategoryUpdate,
    ForumTopic, ForumTopicCreate, ForumTopicUpdate, ForumTopicSummary,
    ForumPost, ForumPostCreate, ForumPostUpdate,
    TopicLike, PostLike, LikeCreate
)
from ...crud.community import (
    create_forum_category, get_forum_categories, get_forum_category, 
    update_forum_category, delete_forum_category,
    create_forum_topic, get_forum_topics, get_forum_topic, 
    update_forum_topic, increment_topic_views,
    create_forum_post, get_forum_posts, get_forum_post, update_forum_post,
    toggle_topic_like, toggle_post_like
)

router = APIRouter()


# Forum Categories
@router.get("/categories", response_model=List[ForumCategory])
def list_forum_categories(
    organization_id: Optional[int] = Query(None),
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get forum categories"""
    return get_forum_categories(
        db=db, 
        organization_id=organization_id,
        is_active=is_active,
        skip=skip, 
        limit=limit
    )


@router.post("/categories", response_model=ForumCategory)
def create_category(
    category: ForumCategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new forum category (admin only)"""
    # Check if user has permission to create categories
    if current_user.role not in ["super_admin", "client_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return create_forum_category(db=db, category=category, user_id=current_user.id)


@router.get("/categories/{category_id}", response_model=ForumCategory)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Get forum category by ID"""
    category = get_forum_category(db=db, category_id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/categories/{category_id}", response_model=ForumCategory)
def update_category(
    category_id: int,
    category_update: ForumCategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update forum category (admin only)"""
    if current_user.role not in ["super_admin", "client_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    category = update_forum_category(db=db, category_id=category_id, category_update=category_update)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete forum category (admin only)"""
    if current_user.role not in ["super_admin", "client_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    success = delete_forum_category(db=db, category_id=category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}


# Forum Topics
@router.get("/topics", response_model=List[ForumTopicSummary])
def list_forum_topics(
    category_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    is_featured: Optional[bool] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get forum topics with filters"""
    return get_forum_topics(
        db=db,
        category_id=category_id,
        organization_id=organization_id,
        is_featured=is_featured,
        is_pinned=is_pinned,
        search=search,
        skip=skip,
        limit=limit
    )


@router.post("/topics", response_model=ForumTopic)
def create_topic(
    topic: ForumTopicCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new forum topic"""
    # Verify category exists
    category = get_forum_category(db=db, category_id=topic.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category requires approval and user has permission
    if category.moderator_only and current_user.role not in ["super_admin", "client_admin"]:
        raise HTTPException(status_code=403, detail="This category is restricted to moderators")
    
    return create_forum_topic(db=db, topic=topic, user_id=current_user.id)


@router.get("/topics/{topic_id}", response_model=ForumTopic)
def get_topic(
    topic_id: int,
    db: Session = Depends(get_db)
):
    """Get forum topic by ID"""
    topic = get_forum_topic(db=db, topic_id=topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Increment view count
    increment_topic_views(db=db, topic_id=topic_id)
    
    return topic


@router.put("/topics/{topic_id}", response_model=ForumTopic)
def update_topic(
    topic_id: int,
    topic_update: ForumTopicUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update forum topic"""
    topic = get_forum_topic(db=db, topic_id=topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Check permissions (author or admin)
    if topic.author_id != current_user.id and current_user.role not in ["super_admin", "client_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return update_forum_topic(db=db, topic_id=topic_id, topic_update=topic_update)


@router.post("/topics/{topic_id}/like", response_model=dict)
def like_topic(
    topic_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Toggle topic like"""
    topic = get_forum_topic(db=db, topic_id=topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    liked = toggle_topic_like(db=db, topic_id=topic_id, user_id=current_user.id)
    return {"liked": liked, "message": "Topic liked" if liked else "Topic unliked"}


# Forum Posts
@router.get("/topics/{topic_id}/posts", response_model=List[ForumPost])
def list_topic_posts(
    topic_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get posts for a topic"""
    # Verify topic exists
    topic = get_forum_topic(db=db, topic_id=topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return get_forum_posts(db=db, topic_id=topic_id, skip=skip, limit=limit)


@router.post("/topics/{topic_id}/posts", response_model=ForumPost)
def create_post(
    topic_id: int,
    post: ForumPostCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new forum post"""
    # Verify topic exists and is not locked
    topic = get_forum_topic(db=db, topic_id=topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    if topic.is_locked:
        raise HTTPException(status_code=403, detail="Topic is locked")
    
    # Set topic_id from URL
    post.topic_id = topic_id
    
    return create_forum_post(db=db, post=post, user_id=current_user.id)


@router.get("/posts/{post_id}", response_model=ForumPost)
def get_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get forum post by ID"""
    post = get_forum_post(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/posts/{post_id}", response_model=ForumPost)
def update_post(
    post_id: int,
    post_update: ForumPostUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update forum post"""
    post = get_forum_post(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check permissions (author or admin)
    if post.author_id != current_user.id and current_user.role not in ["super_admin", "client_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return update_forum_post(db=db, post_id=post_id, post_update=post_update, user_id=current_user.id)


@router.post("/posts/{post_id}/like", response_model=dict)
def like_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Toggle post like"""
    post = get_forum_post(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    liked = toggle_post_like(db=db, post_id=post_id, user_id=current_user.id)
    return {"liked": liked, "message": "Post liked" if liked else "Post unliked"}

