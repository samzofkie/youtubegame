from . import db

class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    videos = db.relationship('Video', backref='genre', lazy='dynamic')

    def __repr__(self):
        return '<Genre {}>'.format(self.name)


class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    vid_id = db.Column(db.String(11), unique=True, index=True)
    title = db.Column(db.String(200))
    views = db.Column(db.Integer)
    date = db.Column(db.DateTime)
    duration = db.Column(db.Interval)
 
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'))

    def __repr__(self):
        return '<Video {}>'.format(self.vid_id)

