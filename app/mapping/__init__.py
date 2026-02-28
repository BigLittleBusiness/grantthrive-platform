"""
Interactive Grant Mapping Blueprint
Provides geographic visualization and analysis of grant distribution
"""

from flask import Blueprint

mapping = Blueprint('mapping', __name__, url_prefix='/mapping')

from app.mapping import routes
