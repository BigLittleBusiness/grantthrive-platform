"""
GrantThrive — Auth Routes (Dispatcher)
========================================
This file is the single entry point imported by app/auth/__init__.py.
It imports the role-scoped route modules so Flask registers their endpoints.

Route modules:
  routes_shared.py    — login, logout, verify-token, demo-login, me, change-password,
                        forgot-password, reset-password  (all roles)
  routes_community.py — POST /register/community  (community_member, professional_consultant)
  routes_council.py   — POST /register/council    (council_admin self-registration)
  registration.py     — stepwise multi-step registration flows (all roles)

Generic registration:
  POST /register      — dispatches to the correct role-scoped handler based on user_type.
"""
import logging
from flask import request

from app import limiter
from app.auth import bp

logger = logging.getLogger(__name__)

# ── Import role-scoped route modules (registers their @bp.route endpoints) ────
from app.auth import routes_shared    # noqa: F401, E402
from app.auth import routes_community # noqa: F401, E402
from app.auth import routes_council   # noqa: F401, E402

# Role set used by the /register dispatcher
_COUNCIL_ROLES = {"council", "council_admin", "council_staff"}


# ── /register dispatcher ────────────────────────────────────────────────────────

@bp.route("/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    """
    Generic registration endpoint.
    Inspects user_type and delegates to the appropriate role-scoped handler.

    user_type values:
      community_member | professional_consultant → routes_community._register_open_user()
      council | council_admin | council_staff    → routes_council._register_council_user()
      (anything else)                            → defaults to community_member
    """
    from app.auth.routes_community import _register_open_user
    from app.auth.routes_council import _register_council_user

    data = request.get_json(silent=True) or {}
    raw_user_type = (data.get("user_type") or data.get("role") or "").strip().lower()

    if raw_user_type in _COUNCIL_ROLES:
        return _register_council_user(data)
    else:
        return _register_open_user(data)
