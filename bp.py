from flask import ( abort,
					Blueprint,
					current_app,
					jsonify,
					render_template,
					request,
					send_from_directory )
from utils import CursorCM, start_crawler, stop_crawler
import json
import logging
import os
from random import randint, sample


routes = Blueprint('bp', __name__)

@routes.route('/favicon.ico')
def favicon():
	''' Random favicon'''
	fav_num = randint(1, current_app.config['NUM_FAVICONS'])
	return send_from_directory( os.path.join(current_app.root_path, 'static'), 
								f'favicon{fav_num}.ico' )


@routes.route('/more')
def more():
	''' Endpoint for client to reup on uris, so the videos never end...'''
	vs = current_app.config['video_store']
	reup_size = current_app.config['CLIENT_REUP_SIZE']
	try:
		vids = vs[('/' + (request.headers['Referer']+' ').split('/')[-1])[:-1]]
	except:
		abort(404)
	ids = sample(vids, reup_size)
	return jsonify(ids) 


@routes.route('/report', methods=('GET','POST'))
def report():
	''' Report page w/ two purposes:
		GET gives you (me) a report on the number of videos in memory, broken up
			by the route they're associated with. Also, gives magic dangerous HTML input,
			for me to enter my secret passwords (set in environment vars) to start and
			stop the crawler from my phone.
		POST is where the client sends interaction data. Right now I am just using it
			to record my interaction data, when I feel like it. Maybe one day I'll
			open it up to my friends to make filters based on their preferences, if
			they actually go through a lot of videos '''
	if request.method == 'GET':
		vs = current_app.config['video_store']
		return render_template( 'report.html', 
								vs_data = { route:len(vs.route_map[route]) for route in vs.route_map } )

	elif request.method == 'POST':				
		data = request.data.decode('utf8')
		if '{' in data:
			# I think it's interaction data. Let's prevent SQL injection
			idata = json.loads(data)
			for uri in idata:
				if uri not in current_app.config['video_store']:
					abort(404)
			qq = current_app.config['query_queue']
			for uri, seconds in idata.items():
				qq.append(f'INSERT INTO interactions VALUES ( NULL, "{request.remote_addr}", "{uri}", SEC_TO_TIME({seconds}));')
			return 'ok'
		else:
			# I think it's a crawler command.
			crawler = current_app.config['crawler']
			if data == current_app.config['STOP_CRAWLER_PW'] and crawler.EXIT_FLAG == 0:
				stop_crawler(crawler)
			elif data == current_app.config['START_CRAWLER_PW']:
				if crawler.EXIT_FLAG==0:
					current_app.logger.info('Tried to start crawler when it was already going...')
				else:
					start_crawler(crawler)
			elif data[:len(current_app.config['SET_CRAWLER_TIMEOUT'])] == current_app.config['SET_CRAWLER_TIMEOUT']:
				t = float(data[len(current_app.config['SET_CRAWLER_TIMEOUT']):])
				crawler.timeout = t
				current_app.logger.info(f'Set crawler timeout to {t}')	
			else:
				abort(404)
			return 'ok'


@routes.route('/')
@routes.route('/<letter>')
def index(letter=None):
	vs = current_app.config['video_store']
	reup_size = current_app.config['CLIENT_REUP_SIZE']
	try:
		vids = vs['/'+ (letter if letter is not None else '')]
	except:
		abort(404)
	ids = json.dumps( sample(vids, reup_size) )
	return render_template( 'index.html', ids=ids,
							VIDS_LEFT_REUP_THRESHOLD =\
							current_app.config['CLIENT_VIDS_LEFT_REUP_THRESHOLD'] )


@routes.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@routes.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@routes.after_request
def after_request(response):
	current_app.config['access_logger'].info( 
		f'{request.remote_addr}  '
		f'{request.method}  {request.path}  '
		f'{request.scheme}  {response.status}  '
		f'{request.user_agent}' )
	return response

