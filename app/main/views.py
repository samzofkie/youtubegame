from flask import current_app, render_template, jsonify, url_for, abort
from random import sample
import json
from .. import db, limiter
from ..models import Video, Genre
from . import main


@limiter.limit("1/minute")
@main.route('/')
@main.route('/<letter>')
def index(letter=None):

    if letter == 'm':
        music_genre = Genre.query.filter_by(name='Music').all()[0]
        query = Video.query.filter_by(genre=music_genre)
        xhr_endpoint='"/more_music_vids"'
    elif letter == None:
        query = Video.query
        xhr_endpoint='"/more_vids"'
    else:
        abort(404)

    if current_app.config['VIDEO_REPLACEMENT']:
         vids = query.all()     # slow af, dev config only
         vids = sample(vids, 10)
    else:
        vids = query.limit(10).all()
        for vid in vids: db.session.delete(vid) 
        db.session.commit()

    ids = json.dumps( [ vid.vid_id for vid in vids ] )
    return render_template('index.html', ids=ids, xhr_endpoint=xhr_endpoint)


@limiter.limit("1/minute")   
@main.route('/more_vids')
def more_vids():
    vids = Video.query.limit(10).all()
    if not current_app.config['VIDEO_REPLACEMENT']: 
        for vid in vids: db.session.delete(vid) 
        db.session.commit()
    ids = [vid.vid_id for vid in vids]
    return jsonify( ids )

@limiter.limit("1/minute")
@main.route('/more_music_vids')
def more_music_vids():
    music_genre = Genre.query.filter_by(name='Music').all()[0]
    vids = Video.query.filter_by(genre=music_genre).limit(10).all()
    if not current_app.config['VIDEO_REPLACEMENT']: 
        for vid in vids: db.session.delete(vid) 
        db.session.commit()
    ids = [vid.vid_id for vid in vids]
    return jsonify( ids )

