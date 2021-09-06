from flask import Blueprint

# name, file(location reference), url_prefix
bp = Blueprint('players', __name__, url_prefix='/players')

from .import routes