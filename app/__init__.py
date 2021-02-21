from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config
import logging
from threading import Thread


db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address)


def create_app(config_name):
    app = Flask(__name__) 
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)
    db.init_app(app)
    limiter.init_app(app)
     
    from .main import main as main_blueprint
    from .main import GenreMap, Crawler

    app.register_blueprint(main_blueprint)
    logging.info('Registered main_blueprint (views)')
    
    with app.app_context():
        if not db.engine.has_table('videos'):
            db.create_all()
            logging.info('Created tables')
        else:
            from .models import Video
            logging.info(f'Database holds {Video.query.count()} videos')
        if app.config['CRAWL']:
            crawler = Crawler() 
            Thread(target=crawler.crawl, args=(app,)).start()

    return app

