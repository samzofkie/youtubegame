import os
from app import create_app, db
from app.models import Video, Genre
import logging


basedir = os.path.abspath(os.path.dirname(__file__))

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)

application = create_app( os.environ['FLASK_CONFIG'] )

@application.shell_context_processor
def make_shell_context():
    return dict(db=db, Video=Video, Genre=Genre)
