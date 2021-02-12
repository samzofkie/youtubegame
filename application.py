from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import json
from app.Crawler import Crawler
from collections import UserDict
from time import sleep
import logging
from threading import Thread

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    db.init_app(app)
    return app

application = create_app()
application.app_context().push()

basedir = os.path.abspath(os.path.dirname(__file__))
application.config['SQLALCHEMY_DATABASE_URI'] =\
                  'sqlite:///' + os.path.join(basedir, 'data.sqlite')
application.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False




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


class GenreMap(UserDict):
    def __init__(self, db, Genre):
        self.db=db
        self.Genre = Genre
        super().__init__(self)
        for genre in self.Genre.query.all():
            self.data[ genre.name ] = genre
        logging.info('Successfully initialized GenreMap')
        
    def __missing__(self, key):
        self.data[key] = self.Genre(name=key)
        logging.info('Added new Genre: {}'.format(key))
        self.db.session.add(self.data[key])
        self.db.session.commit()
        return self.data[key]



genre_map = GenreMap(db, Genre)
crawler = Crawler(db, Video, genre_map)
thr = Thread(target=crawler.crawl, args=[application])
with application.app_context():
    thr.start()
logging.info('Successfully started crawler')



@application.route('/')
def index():
    vids = Video.query.limit(10).all()
    for vid in vids: db.session.delete(vid) 
    db.session.commit()
    ids = [ vid.vid_id for vid in vids ]
    ids = json.dumps(ids)
    return render_template('index.html', ids=ids, xhr_endpoint='"/more_vids"')


@application.route('/m')
def music():
    music_genre = Genre.query.filter_by(name='Music').all()[0]
    vids = Video.query.filter_by(genre=music_genre).limit(10).all()
    for vid in vids: db.session.delete(vid) 
    db.session.commit()
    ids = [ vid.vid_id for vid in vids ]
    return render_template('index.html', ids=ids, xhr_endpoint='"/more_music_vids"')
    
    
@application.route('/more_vids')
def more_vids():
    vids = Video.query.limit(10).all()
    for vid in vids: db.session.delete(vid) 
    db.session.commit()
    ids = [vid.vid_id for vid in vids]
    return jsonify( ids )


@application.route('/more_music_vids')
def more_music_vids():
    music_genre = Genre.query.filter_by(name='Music').all()[0]
    vids = Video.query.filter_by(genre=music_genre).limit(10).all()
    for vid in vids: db.session.delete(vid) 
    db.session.commit()
    ids = [vid.vid_id for vid in vids]
    return jsonify( ids )



if __name__=='__main__':
    application.run()
