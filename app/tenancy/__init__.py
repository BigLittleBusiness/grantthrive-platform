from flask import Blueprint
log_bp = Blueprint('tenancy', __name__)
from app.tenancy import logo, routes
