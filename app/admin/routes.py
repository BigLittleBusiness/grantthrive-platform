"""Admin blueprint — placeholder for council admin web routes."""
from app.admin import bp

@bp.route('/')
def index():
    return '', 204
