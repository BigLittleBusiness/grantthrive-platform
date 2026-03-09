from flask import Blueprint

bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

from app.notifications import routes  # noqa: F401, E402
