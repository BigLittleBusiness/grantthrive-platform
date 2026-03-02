"""
GrantThrive — Pagination Helpers
==================================
Thin wrappers around SQLAlchemy's ``paginate()`` method that add sensible
defaults and error handling.
"""

import logging
from flask import current_app
from sqlalchemy import or_

logger = logging.getLogger(__name__)

# Maximum number of records allowed per page (prevents abuse)
MAX_PER_PAGE = 100


def paginate_results(query, page: int = 1, per_page: int = 20):
    """Paginate a SQLAlchemy query with safe defaults.

    Args:
        query:    A SQLAlchemy ``Query`` object.
        page:     Page number (1-indexed).
        per_page: Number of results per page. Capped at ``MAX_PER_PAGE``.

    Returns:
        A SQLAlchemy ``Pagination`` object.  Falls back to page 1 on error.
    """
    per_page = min(per_page, MAX_PER_PAGE)
    try:
        return query.paginate(page=page, per_page=per_page, error_out=False)
    except Exception as exc:
        logger.error("Pagination error (page=%d per_page=%d): %s", page, per_page, exc)
        return query.paginate(page=1, per_page=20, error_out=False)


def build_search_query(model, search_term: str, search_fields: list[str]):
    """Build a case-insensitive ``ILIKE`` search query across multiple fields.

    Args:
        model:         SQLAlchemy model class.
        search_term:   String to search for.  Returns the base query unchanged
                       if empty.
        search_fields: List of column names on *model* to search.

    Returns:
        A SQLAlchemy ``Query`` object with the search filter applied.
    """
    if not search_term:
        return model.query

    conditions = [
        getattr(model, field).ilike(f"%{search_term}%")
        for field in search_fields
        if hasattr(model, field)
    ]

    if conditions:
        return model.query.filter(or_(*conditions))
    return model.query
