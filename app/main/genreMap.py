from collections import UserDict
import logging
from ..models import Genre
from .. import db

class GenreMap(UserDict):
    def __init__(self):
        #self.db=db
        #self.Genre = Genre
        super().__init__(self)
        for genre in Genre.query.all():
            self.data[ genre.name ] = genre
        logging.info('Successfully initialized GenreMap')
        
    def __missing__(self, key):
        self.data[key] = Genre(name=key)
        logging.info('Added new Genre: {}'.format(key))
        db.session.add(self.data[key])
        db.session.commit()
        return self.data[key]

