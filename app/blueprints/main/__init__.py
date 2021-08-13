from flask import Blueprint

# name, file(location reference), url_prefix
bp = Blueprint('main', __name__, url_prefix='/')

from .import routes