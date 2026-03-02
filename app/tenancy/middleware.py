"""
GrantThrive — Tenant Resolution Middleware
==========================================
Resolves the incoming HTTP request to a Council tenant by reading the
subdomain from the ``Host`` header.

Architecture
------------
Every request to ``<subdomain>.grantthrive.com`` passes through
``resolve_tenant()``, which:

1. Extracts the leftmost label from the ``Host`` header.
2. Looks up the matching ``Council`` record by ``subdomain``.
3. Stores the result in Flask's ``g`` object for the duration of the request.

Route handlers and decorators then call ``get_current_council()`` to obtain
the resolved tenant, or ``require_tenant()`` to enforce that one exists.

Special subdomains
------------------
The following subdomains are reserved and do NOT map to a council tenant:

  ``app``    — legacy catch-all portal (redirects to council-specific URL)
  ``admin``  — GrantThrive system-admin dashboard
  ``api``    — REST API (tenant is resolved from the JWT, not the subdomain)
  ``www``    — Marketing website
  ``map``    — Interactive grant map (public)
  ``roi``    — ROI calculator (public)

For these reserved subdomains ``g.council`` is set to ``None``.

Development
-----------
In development (``localhost``), the subdomain is read from the optional
``X-GT-Subdomain`` request header so that engineers can test any tenant
without configuring local DNS.  Set the header in your API client or Vite
proxy config::

    X-GT-Subdomain: cityofmelbourne
"""

import logging
from functools import wraps

from flask import g, request, jsonify, current_app

logger = logging.getLogger(__name__)

# Subdomains that are reserved by GrantThrive and do not map to a council.
_RESERVED_SUBDOMAINS = frozenset({
    'www', 'app', 'admin', 'api', 'map', 'roi',
    'staging', 'dev', 'test', 'mail', 'smtp',
})


def _extract_subdomain(host: str) -> str | None:
    """
    Extract the leftmost subdomain label from a Host header value.

    Examples::

        "cityofmelbourne.grantthrive.com"  →  "cityofmelbourne"
        "grantthrive.com"                  →  None
        "localhost:5000"                   →  None
        "admin.grantthrive.com"            →  "admin"
    """
    # Strip port
    host = host.split(':')[0].lower()

    # Localhost / IP — no subdomain
    if host in ('localhost', '127.0.0.1', '::1') or host.replace('.', '').isdigit():
        return None

    parts = host.split('.')
    # e.g. ["cityofmelbourne", "grantthrive", "com"]
    if len(parts) >= 3:
        return parts[0]
    return None


def resolve_tenant():
    """
    Flask ``before_request`` hook — resolves the current council tenant.

    Sets ``g.council`` to the matching ``Council`` instance, or ``None`` if
    the request is not scoped to a tenant (reserved subdomain, system-admin
    request, or development localhost without the override header).
    """
    from app.models import Council

    g.council = None

    # Development override: allow engineers to spoof a subdomain via header
    subdomain = request.headers.get('X-GT-Subdomain')

    if not subdomain:
        host = request.headers.get('Host', '')
        subdomain = _extract_subdomain(host)

    if not subdomain or subdomain in _RESERVED_SUBDOMAINS:
        return  # Not a tenant-scoped request

    council = Council.query.filter_by(subdomain=subdomain, is_active=True).first()
    if council:
        g.council = council
        logger.debug("Tenant resolved: %s (id=%d)", council.subdomain, council.id)
    else:
        logger.warning("Unknown or inactive subdomain requested: %s", subdomain)
        # Do NOT 404 here — the route handler decides whether a tenant is required.


def get_current_council():
    """Return the ``Council`` resolved for this request, or ``None``."""
    return getattr(g, 'council', None)


def require_tenant(f):
    """
    Decorator: reject the request with 404 if no council tenant was resolved.

    Use on any route that must be scoped to a specific council::

        @bp.route('/grants')
        @require_tenant
        def list_grants():
            council = get_current_council()
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_council():
            return jsonify({
                'error': 'Council not found.',
                'detail': (
                    'This URL does not correspond to an active GrantThrive council. '
                    'Please check the subdomain and try again.'
                ),
            }), 404
        return f(*args, **kwargs)
    return decorated


def council_scope(query, model):
    """
    Apply a ``council_id`` filter to a SQLAlchemy query using the current tenant.

    Usage::

        grants = council_scope(Grant.query, Grant).filter_by(status='open').all()

    If no tenant is resolved (e.g. system-admin context), the query is returned
    unfiltered so that system admins can see all data.
    """
    council = get_current_council()
    if council is not None and hasattr(model, 'council_id'):
        return query.filter(model.council_id == council.id)
    return query
