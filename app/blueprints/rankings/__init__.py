from flask import Blueprint

# name, file(location reference), url_prefix
bp = Blueprint('rankings', __name__, url_prefix='/rankings')

from .import routes