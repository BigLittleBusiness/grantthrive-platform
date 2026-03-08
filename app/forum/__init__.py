from flask import Blueprint
forum_bp = Blueprint('forum', __name__)
from app.forum import routes  # noqa: F401, E402
