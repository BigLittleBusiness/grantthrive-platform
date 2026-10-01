"""
Grant Mapping API — geographic grant data (mounted at /api/mapping).
"""

from flask import Blueprint

mapping = Blueprint('mapping', __name__)

from app.mapping import routes  # noqa: E402,F401
