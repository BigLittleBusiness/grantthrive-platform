from flask import Blueprint
bp = Blueprint('workflows', __name__)
from app.workflows import routes
