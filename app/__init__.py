from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
import logging
from threading import Thread

db = SQLAlchemy()

def create_app(config_name):
    app = Flask(__name__) 
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)

    from .main import main as main_blueprint
    from .main import GenreMap, Crawler

    app.register_blueprint(main_blueprint)
    logging.info('Registered main_blueprint (views)')
    
    if app.config['CRAWL']:
        with app.app_context():
            crawler = Crawler() 
            Thread(target=crawler.crawl, args=(app,)).start()

    return app

