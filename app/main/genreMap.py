from collections import UserDict
from ..models import Genre
from .. import db

class GenreMap(UserDict):
    def __init__(self):
        super().__init__(self)
        for genre in Genre.query.all():
            self.data[ genre.name ] = genre
        
    def __missing__(self, key):
        self.data[key] = Genre(name=key)
        db.session.add(self.data[key])
        db.session.commit()
        return self.data[key]

