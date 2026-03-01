"""applications blueprint — placeholder routes."""
from app.applications import bp
@bp.route('/')
def index():
    return '', 204
