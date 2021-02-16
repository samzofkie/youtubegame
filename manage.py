import os
from app import create_app, db
from app.models import Video, Genre
import logging

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.DEBUG)

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Video=Video, Genre=Genre)

if __name__=='__main__':
    app.run()
