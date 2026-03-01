from flask import Blueprint
bp = Blueprint('grants', __name__)
from app.grants import routes
