from flask import Blueprint
bp = Blueprint('applications', __name__)
from app.applications import routes
from app.applications import documents
