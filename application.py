'''''''''''''''
Essential environment variables:
	
	DB_PREFIX					Probably RDS or MYSQL
	{DB_PREFIX}_HOSTNAME		Probably Localhost or the url of the SQL server
	{DB_PREFIX}_USERNAME		Probably some dumb shit
	{DB_PREFIX}_PASSWORD		Probably even worse
	{DB_PREFIX}_DB_NAME			
	START_CRAWLER_PW			
	STOP_CRAWLER_PW
	SET_CRAWLER_TIMEOUT

Non essential env vars:

	CLIENT_REUP_SIZE			Number of vid ids to send from /, /m, or /more
								Default is 50
	CLIENT_VIDS_LEFT_REUP_THRESHOLD		How many videos should the client have
										when they GET /more?
										Default is 5
	CRAWL						Anything but "True" will not start the crawler
								Default is "True"
	QUERIES_PER_COMMIT			Only relevant to QueryQueue objects
								How many queries should they have b4 they execute
								them all to the DB?
								Default is 50 (set in utils.QueryQueue)

'''''''''''''''''

from time import sleep
import os
import logging
from flask import Flask
from collections import namedtuple

from utils import CursorCM, start_crawler, connect_to_db, VideoStore, QueryQueue, GenreMap
from crawler import Crawler
from log_config import log_config
from logging.config import dictConfig
from bp import routes


def create_app():
	app = Flask(__name__)

	# Client reup size
	client_reup_size = os.environ.get('CLIENT_REUP_SIZE', 50)
	
	# Logging
	dictConfig(log_config)
	logging.getLogger('werkzeug').setLevel(50)
	app.logger = logging.getLogger('app')

	# Get database connection pool
	cn_pool = connect_to_db( app.logger )
	
	query_queue = QueryQueue(cn_pool, app.logger)
	genre_map = GenreMap(cn_pool, query_queue, app.logger) 
	
	# Create VideoStore, and load all videos from database
	video_store = VideoStore(genre_map)
	with CursorCM(cn_pool) as cursor:	
		cursor.execute('SELECT uri, title, views, published, duration, genre_id FROM videos;')
		for vid in cursor.fetchall():
			video_store.add(vid)
	app.logger.info(f'Loaded {video_store}')

	crawler = Crawler(query_queue, video_store, genre_map, app.logger)


	# Load resources in app.config, so routes registed in bp can access them.
	# video_store needed for serving vidoes
	# query_queue needed for reporting interaction data
	# crawler needed for controlling crawler from /report
	for resource_name in ('video_store','query_queue','crawler'):
		app.config[resource_name] = locals()[resource_name]

	app.config['access_logger'] = logging.getLogger('app.access')	# after requests

	# Crawler commands have no default values
	for env_var in ('START_CRAWLER_PW', 'STOP_CRAWLER_PW', 'SET_CRAWLER_TIMEOUT'):
		app.config[env_var] = os.environ[env_var]

	app.config['CLIENT_REUP_SIZE'] = int(os.environ.get('CLIENT_REUP_SIZE', 50))
	app.config['CLIENT_VIDS_LEFT_REUP_THRESHOLD'] = \
				os.environ.get('CLIENT_VIDS_LEFT_REUP_THRESHOLD', 5)
	app.config['NUM_FAVICONS'] = len([ i for i in os.listdir('static') if 'favicon' in i ])
	
	# If we're starting the crawler, ensure there's enough videos to start
	if os.environ.get('CRAWL', 'True') == 'True':
		start_crawler(crawler)
		while True:
			if len(video_store.vids) + len(video_store.mvids) > app.config['CLIENT_REUP_SIZE']:
				break
			sleep(10)
	
	# Register routes
	app.register_blueprint(routes)

	return app


# AWS likes the application variable outside of if __name__ == "__main__"
application = create_app()
if __name__=='__main__':
	application.run()

