from flask import Blueprint

main = Blueprint('main', __name__)

from . import views
from . import errors
from .crawler import Crawler
from .genreMap import GenreMap
