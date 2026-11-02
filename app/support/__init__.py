"""Role-scoped Help & Guidance API."""

from flask import Blueprint

bp = Blueprint("support", __name__)

from app.support import routes  # noqa: E402,F401
