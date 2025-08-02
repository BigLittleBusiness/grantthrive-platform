"""
GrantThrive Success Stories API Endpoints
Handles success story showcase and management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud.community import (
    create_success_story, get_success_stories, get_story_by_id,
    update_success_story, delete_success_story, approve_success_story,
    create_story_comment, get_story_comments, like_success_story,
    get_featured_stories
)
from app.models.user import User
from app.schemas.community import (
    SuccessStoryCreate, SuccessStoryResponse, SuccessStoryUpdate,
    StoryCommentCreate, StoryCommentResponse, StoryLikeResponse
)

router = APIRouter()

# Success Stories CRUD
@router.post("/", response_model=SuccessStoryResponse)
def create_story(
    story: SuccessStoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new success story"""
    return create_success_story(
        db=db, story=story, author_id=current_user.id,
        organization_id=current_user.organization_id
    )

@router.get("/", response_model=List[SuccessStoryResponse])
def get_stories(
    status: Optional[str] = Query("approved", description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    featured_only: bool = Query(False, description="Show only featured stories"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get success stories"""
    if featured_only:
        return get_featured_stories(
            db=db, organization_id=current_user.organization_id,
            skip=skip, limit=limit
        )
    
    return get_success_stories(
        db=db, organization_id=current_user.organization_id,
        status=status, category=category, skip=skip, limit=limit
    )

@router.get("/{story_id}", response_model=SuccessStoryResponse)
def get_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific success story"""
    story = get_story_by_id(db=db, story_id=story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Check access permissions
    if story.status != "approved" and story.author_id != current_user.id:
        if current_user.role not in ["client_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return story

@router.put("/{story_id}", response_model=SuccessStoryResponse)
def update_story(
    story_id: int,
    story_update: SuccessStoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update success story"""
    story = get_story_by_id(db=db, story_id=story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Check permissions
    if story.author_id != current_user.id and current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return update_success_story(db=db, story_id=story_id, story_update=story_update)

@router.delete("/{story_id}")
def delete_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete success story"""
    story = get_story_by_id(db=db, story_id=story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Check permissions
    if story.author_id != current_user.id and current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = delete_success_story(db=db, story_id=story_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete story")
    
    return {"message": "Story deleted successfully"}

# Story Approval (Admin only)
@router.put("/{story_id}/approve", response_model=SuccessStoryResponse)
def approve_story(
    story_id: int,
    approved: bool = True,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject success story"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return approve_success_story(
        db=db, story_id=story_id, approved=approved,
        reviewer_id=current_user.id, feedback=feedback
    )

# Story Engagement
@router.post("/{story_id}/like", response_model=StoryLikeResponse)
def like_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Like or unlike a success story"""
    return like_success_story(db=db, story_id=story_id, user_id=current_user.id)

@router.post("/{story_id}/comments", response_model=StoryCommentResponse)
def create_comment(
    story_id: int,
    comment: StoryCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add comment to success story"""
    return create_story_comment(
        db=db, story_id=story_id, comment=comment, author_id=current_user.id
    )

@router.get("/{story_id}/comments", response_model=List[StoryCommentResponse])
def get_comments(
    story_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comments for success story"""
    return get_story_comments(db=db, story_id=story_id, skip=skip, limit=limit)

# Admin endpoints
@router.get("/admin/pending", response_model=List[SuccessStoryResponse])
def get_pending_stories(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending success stories for review"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return get_success_stories(
        db=db, organization_id=current_user.organization_id,
        status="pending", skip=skip, limit=limit
    )

@router.get("/stats")
def get_story_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get success story statistics"""
    all_stories = get_success_stories(
        db=db, organization_id=current_user.organization_id,
        status=None, skip=0, limit=1000
    )
    
    stats = {
        "total_stories": len(all_stories),
        "approved_stories": len([s for s in all_stories if s.status == "approved"]),
        "pending_stories": len([s for s in all_stories if s.status == "pending"]),
        "featured_stories": len([s for s in all_stories if s.is_featured]),
        "total_views": sum(s.view_count for s in all_stories),
        "total_likes": sum(s.like_count for s in all_stories)
    }
    
    return stats

