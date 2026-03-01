"""reviews blueprint — placeholder routes."""
from app.reviews import bp
@bp.route('/')
def index():
    return '', 204
