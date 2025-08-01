"""
GrantThrive Resource Library API Endpoints
RESTful API for resource management and file sharing
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from pathlib import Path

from ...db.database import get_db
from ...api.deps import get_current_user, get_current_active_user
from ...models.user import User
from ...schemas.community import (
    ResourceCategory, ResourceCategoryCreate, ResourceCategoryUpdate,
    Resource, ResourceCreate, ResourceUpdate, ResourceSummary,
    ResourceRating, ResourceRatingCreate, ResourceRatingUpdate,
    ResourceLike, LikeCreate, ResourceTypeEnum
)
from ...crud.community import (
    create_resource_category, get_resource_categories,
    create_resource, get_resources, get_resource,
    increment_resource_views, increment_resource_downloads
)

router = APIRouter()

# File upload configuration
UPLOAD_DIR = Path("uploads/resources")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.rtf', '.odt', '.ods', '.odp',
    '.jpg', '.jpeg', '.png', '.gif', '.svg',
    '.mp4', '.avi', '.mov', '.wmv', '.flv',
    '.mp3', '.wav', '.ogg',
    '.zip', '.rar', '.7z'
}


# Resource Categories
@router.get("/categories", response_model=List[ResourceCategory])
def list_resource_categories(
    organization_id: Optional[int] = Query(None),
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get resource categories"""
    return get_resource_categories(
        db=db,
        organization_id=organization_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )


@router.post("/categories", response_model=ResourceCategory)
def create_category(
    category: ResourceCategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new resource category (admin only)"""
    if current_user.role not in ["super_admin", "client_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return create_resource_category(db=db, category=category, user_id=current_user.id)


# Resources
@router.get("/", response_model=List[ResourceSummary])
def list_resources(
    category_id: Optional[int] = Query(None),
    resource_type: Optional[ResourceTypeEnum] = Query(None),
    organization_id: Optional[int] = Query(None),
    is_featured: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get resources with filters"""
    return get_resources(
        db=db,
        category_id=category_id,
        resource_type=resource_type.value if resource_type else None,
        organization_id=organization_id,
        is_featured=is_featured,
        search=search,
        skip=skip,
        limit=limit
    )


@router.get("/featured", response_model=List[ResourceSummary])
def list_featured_resources(
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get featured resources"""
    return get_resources(
        db=db,
        is_featured=True,
        limit=limit
    )


@router.get("/recent", response_model=List[ResourceSummary])
def list_recent_resources(
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get recently added resources"""
    return get_resources(
        db=db,
        limit=limit
    )


@router.post("/", response_model=Resource)
def create_resource_item(
    resource: ResourceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new resource"""
    return create_resource(db=db, resource=resource, user_id=current_user.id)


@router.post("/upload", response_model=Resource)
async def upload_resource_file(
    file: UploadFile = File(...),
    title: str = Query(...),
    description: str = Query(...),
    category_id: int = Query(...),
    resource_type: ResourceTypeEnum = Query(...),
    tags: Optional[str] = Query(None),  # Comma-separated tags
    is_public: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a resource file"""
    # Validate file
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else None
    
    # Create resource record
    resource_data = ResourceCreate(
        title=title,
        description=description,
        resource_type=resource_type,
        category_id=category_id,
        file_url=str(file_path),
        organization_id=current_user.organization_id,
        is_public=is_public,
        tags=tag_list
    )
    
    db_resource = create_resource(db=db, resource=resource_data, user_id=current_user.id)
    
    # Update file metadata
    db_resource.file_name = file.filename
    db_resource.file_size = file.size
    db_resource.mime_type = file.content_type
    db.commit()
    db.refresh(db_resource)
    
    return db_resource


@router.get("/{resource_id}", response_model=Resource)
def get_resource_item(
    resource_id: int,
    db: Session = Depends(get_db)
):
    """Get resource by ID"""
    resource = get_resource(db=db, resource_id=resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Increment view count
    increment_resource_views(db=db, resource_id=resource_id)
    
    return resource


@router.get("/{resource_id}/download")
def download_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download resource file"""
    resource = get_resource(db=db, resource_id=resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    if not resource.file_url:
        raise HTTPException(status_code=404, detail="No file available for download")
    
    # Check if file exists
    file_path = Path(resource.file_url)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Increment download count
    increment_resource_downloads(db=db, resource_id=resource_id)
    
    # Return file download response
    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        filename=resource.file_name or f"resource_{resource_id}{file_path.suffix}",
        media_type=resource.mime_type or 'application/octet-stream'
    )


@router.post("/{resource_id}/like", response_model=dict)
def like_resource(
    resource_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Toggle resource like"""
    from ...models.community import ResourceLike
    from sqlalchemy import and_
    
    resource = get_resource(db=db, resource_id=resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Check if already liked
    existing_like = db.query(ResourceLike).filter(
        and_(
            ResourceLike.resource_id == resource_id,
            ResourceLike.user_id == current_user.id
        )
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        if resource.like_count > 0:
            resource.like_count -= 1
        db.commit()
        return {"liked": False, "message": "Resource unliked"}
    else:
        # Like
        new_like = ResourceLike(resource_id=resource_id, user_id=current_user.id)
        db.add(new_like)
        resource.like_count += 1
        db.commit()
        return {"liked": True, "message": "Resource liked"}


@router.post("/{resource_id}/rate", response_model=ResourceRating)
def rate_resource(
    resource_id: int,
    rating_data: ResourceRatingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Rate a resource"""
    from ...models.community import ResourceRating
    from sqlalchemy import and_, func
    
    resource = get_resource(db=db, resource_id=resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Check if user already rated this resource
    existing_rating = db.query(ResourceRating).filter(
        and_(
            ResourceRating.resource_id == resource_id,
            ResourceRating.user_id == current_user.id
        )
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_data.rating
        existing_rating.review = rating_data.review
        db.commit()
        db.refresh(existing_rating)
        db_rating = existing_rating
    else:
        # Create new rating
        db_rating = ResourceRating(
            resource_id=resource_id,
            user_id=current_user.id,
            rating=rating_data.rating,
            review=rating_data.review
        )
        db.add(db_rating)
        db.commit()
        db.refresh(db_rating)
    
    # Update resource rating statistics
    rating_stats = db.query(
        func.avg(ResourceRating.rating).label('avg_rating'),
        func.count(ResourceRating.id).label('count')
    ).filter(ResourceRating.resource_id == resource_id).first()
    
    resource.rating_average = float(rating_stats.avg_rating) if rating_stats.avg_rating else 0.0
    resource.rating_count = rating_stats.count
    db.commit()
    
    return db_rating


@router.get("/{resource_id}/ratings", response_model=List[ResourceRating])
def get_resource_ratings(
    resource_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get ratings for a resource"""
    from ...models.community import ResourceRating
    
    resource = get_resource(db=db, resource_id=resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    return db.query(ResourceRating).filter(
        ResourceRating.resource_id == resource_id
    ).order_by(ResourceRating.created_at.desc()).offset(skip).limit(limit).all()

