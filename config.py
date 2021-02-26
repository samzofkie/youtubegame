import os
import yaml
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    
    with open('logging_config.yaml','r') as f:
        LOGGER_DICT = yaml.load(f, Loader=yaml.Loader)

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    VIDEO_REPLACEMENT = True
    CRAWL = True


class ProductionConfig(Config):
    if 'RDS_HOSTNAME' in os.environ:
        USERNAME = os.environ['RDS_USERNAME']
        PASSWORD = os.environ['RDS_PASSWORD']
        ENDPOINT = os.environ['RDS_HOSTNAME']
        DB_NAME = os.environ['RDS_DB_NAME']
        SQLALCHEMY_DATABASE_URI = f'mysql://{USERNAME}:{PASSWORD}@{ENDPOINT}/{DB_NAME}'
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    VIDEO_REPLACEMENT = False
    CRAWL = True



config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
