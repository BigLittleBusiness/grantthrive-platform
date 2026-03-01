"""grants blueprint — placeholder routes."""
from app.grants import bp
@bp.route('/')
def index():
    return '', 204
