"""
Tenant Isolation Helpers — GrantThrive
=======================================
Centralised helpers that enforce council-scoped data isolation.

Usage pattern
-------------
    from app.common.tenant import scope_grants, scope_applications, assert_council_scope

    # In a route:
    grants_query = scope_grants(current_user, Grant.query)
    apps_query   = scope_applications(current_user, Application.query)

    # For a single object already fetched:
    assert_council_scope(current_user, grant)   # aborts with 403 if wrong council
"""
from flask import abort
from app.models import Grant, Application


def _is_system_admin(user) -> bool:
    return getattr(user, 'role', None) == 'system_admin'


def scope_grants(user, query=None):
    """Return a Grant query scoped to the user's council.

    system_admin receives an unfiltered query.
    All other roles receive a query filtered to their council_id.
    If no base query is provided, Grant.query is used.
    """
    if query is None:
        query = Grant.query
    if _is_system_admin(user):
        return query
    return query.filter(Grant.council_id == user.council_id)


def scope_applications(user, query=None):
    """Return an Application query scoped to the user's council.

    system_admin receives an unfiltered query.
    All other roles receive a query joined to Grant and filtered by council_id.
    If no base query is provided, Application.query is used.
    """
    if query is None:
        query = Application.query
    if _is_system_admin(user):
        return query
    return query.join(Grant).filter(Grant.council_id == user.council_id)


def assert_council_scope(user, obj):
    """Abort with 403 if the user does not have access to the given object.

    Accepts a Grant or Application instance.
    system_admin always passes.
    """
    if _is_system_admin(user):
        return
    if isinstance(obj, Grant):
        if obj.council_id != user.council_id:
            abort(403)
    elif isinstance(obj, Application):
        grant = obj.grant if hasattr(obj, 'grant') else None
        if grant is None:
            from app import db
            grant = db.session.get(Grant, obj.grant_id)
        if not grant or grant.council_id != user.council_id:
            abort(403)
    else:
        # For any other model with a council_id attribute
        if hasattr(obj, 'council_id') and obj.council_id != user.council_id:
            abort(403)
