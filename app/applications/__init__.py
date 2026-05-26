from flask import Blueprint
bp = Blueprint('applications', __name__)
from app.applications import routes
from app.applications import documents  # noqa: F401 — registers S3 document upload/download routes
