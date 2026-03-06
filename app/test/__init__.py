from flask import Blueprint

test_bp = Blueprint('test_bp', __name__, template_folder="templates", static_folder="static")

from . import test_database