"""System Admin blueprint — CRUD management of system_admin (GrantThrive staff) users."""
from flask import Blueprint

bp = Blueprint('system_admin', __name__)

from app.system_admin import routes       # noqa: E402, F401
from app.system_admin import admin_auth   # noqa: E402, F401
