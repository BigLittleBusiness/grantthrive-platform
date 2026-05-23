"""Performance optimization utilities for GrantThrive platform"""
import os
from functools import wraps
from flask import request, jsonify, current_app
from flask_caching import Cache
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging

# Initialize cache
cache = Cache()

def init_optimizations(app):
    """Initialize performance optimizations"""

    # Use Redis as the cache backend when REDIS_URL is set (production/staging).
    # Falls back to SimpleCache for local development when Redis is not available.
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        cache_config = {
            'CACHE_TYPE': 'RedisCache',
            'CACHE_REDIS_URL': redis_url,
            'CACHE_DEFAULT_TIMEOUT': 300,
        }
    else:
        cache_config = {
            'CACHE_TYPE': 'SimpleCache',
            'CACHE_DEFAULT_TIMEOUT': 300,
        }

    cache.init_app(app, config=cache_config)
    
    # Add database query logging in debug mode
    if app.debug:
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
            
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)
            if total > 0.1:  # Log slow queries (>100ms)
                current_app.logger.warning(f"Slow query: {total:.3f}s - {statement[:100]}...")

def cache_key(*args, **kwargs):
    """Generate cache key from arguments"""
    return f"{request.endpoint}:{hash(str(args) + str(sorted(kwargs.items())))}"

def cached_route(timeout=300):
    """Decorator for caching route responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = cache_key(*args, **kwargs)
            result = cache.get(key)
            if result is None:
                result = f(*args, **kwargs)
                cache.set(key, result, timeout=timeout)
            return result
        return decorated_function
    return decorator

def invalidate_cache_pattern(pattern):
    """Invalidate cache entries matching a key pattern.

    When the cache backend is Redis, uses SCAN-based pattern matching to
    delete only the matching keys.  Falls back to a full cache clear for
    non-Redis backends (e.g., SimpleCache in local development).
    """
    try:
        redis_client = cache.cache._write_client  # type: ignore[attr-defined]
        keys = redis_client.keys(f"flask_cache_{pattern}*")
        if keys:
            redis_client.delete(*keys)
    except Exception:
        # Non-Redis backend or client not available — clear everything
        cache.clear()

class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def eager_load_grants():
        """Optimized query for loading grants with related data"""
        from app.models import Grant, GrantCriteria, User
        return Grant.query.options(
            db.joinedload(Grant.criteria),
            db.joinedload(Grant.creator)
        )
    
    @staticmethod
    def eager_load_applications():
        """Optimized query for loading applications with related data"""
        from app.models import Application, Grant, User
        return Application.query.options(
            db.joinedload(Application.grant),
            db.joinedload(Application.applicant),
            db.joinedload(Application.documents)
        )
    
    @staticmethod
    def eager_load_reviews():
        """Optimized query for loading reviews with related data"""
        from app.models import Review, Application, Grant, User
        return Review.query.options(
            db.joinedload(Review.application).joinedload(Application.grant),
            db.joinedload(Review.reviewer),
            db.joinedload(Review.criteria_scores)
        )

def add_database_indexes():
    """Add database indexes for better performance"""
    from app import db
    
    # Add indexes for commonly queried fields
    indexes = [
        # Grant indexes
        "CREATE INDEX IF NOT EXISTS idx_grants_status ON grants(status)",
        "CREATE INDEX IF NOT EXISTS idx_grants_published ON grants(is_published)",
        "CREATE INDEX IF NOT EXISTS idx_grants_dates ON grants(opens_at, closes_at)",
        "CREATE INDEX IF NOT EXISTS idx_grants_creator ON grants(created_by)",
        
        # Application indexes
        "CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)",
        "CREATE INDEX IF NOT EXISTS idx_applications_grant ON applications(grant_id)",
        "CREATE INDEX IF NOT EXISTS idx_applications_applicant ON applications(applicant_id)",
        "CREATE INDEX IF NOT EXISTS idx_applications_submitted ON applications(submitted_at)",
        
        # Review indexes
        "CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(status)",
        "CREATE INDEX IF NOT EXISTS idx_reviews_reviewer ON reviews(reviewer_id)",
        "CREATE INDEX IF NOT EXISTS idx_reviews_application ON reviews(application_id)",
        
        # User indexes (already have unique indexes, but add role index)
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
        "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
    ]
    
    for index_sql in indexes:
        try:
            db.engine.execute(index_sql)
        except Exception as e:
            current_app.logger.warning(f"Index creation failed: {e}")

def optimize_static_files():
    """Optimize static file serving"""
    return {
        'SEND_FILE_MAX_AGE_DEFAULT': 31536000,  # 1 year cache for static files
        'PERMANENT_SESSION_LIFETIME': 1800,     # 30 minute sessions
    }

class PerformanceMiddleware:
    """Middleware for performance monitoring"""
    
    def __init__(self, app):
        self.app = app
        self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        request.start_time = time.time()
    
    def after_request(self, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            if duration > 1.0:  # Log slow requests (>1s)
                current_app.logger.warning(
                    f"Slow request: {duration:.3f}s - {request.method} {request.path}"
                )
        return response

# Pagination helpers
def paginate_query(query, page=1, per_page=20, max_per_page=100):
    """Optimized pagination with limits"""
    per_page = min(per_page, max_per_page)
    return query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False,
        max_per_page=max_per_page
    )

# Database connection optimization
def optimize_db_connection(app):
    """Optimize database connection settings"""
    app.config.update({
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_size': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'max_overflow': 20
        }
    })
