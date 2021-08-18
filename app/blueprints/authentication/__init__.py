from flask import Blueprint

# name, file(location reference), url_prefix
bp = Blueprint('authentication', __name__, url_prefix='/authentication')

from .import routes