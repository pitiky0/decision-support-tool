from flask import Blueprint

bp = Blueprint('dictionary', __name__)

from app.dictionary import routes
