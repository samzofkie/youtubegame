import os
import logging
from collections import deque, namedtuple, OrderedDict, UserDict
import itertools
import mysql.connector
import mysql.connector.pooling
import mysql.connector.errorcode as errorcode
import threading
from time import perf_counter



class CursorCM:
	def __init__(self, cn_pool):
		self.cn_pool = cn_pool

	def __enter__(self):
		self.cn = self.cn_pool.get_connection()
		self.cursor = self.cn.cursor()
		return self.cursor

	def __exit__(self, *args):
		self.cursor.close()
		self.cn.commit()
		self.cn.close()




def connect_to_db(logger):
    
    # Get the necessary env vars, or tell me what I'm missing
	prefix = os.environ['DB_PREFIX'] 
	nec_env_vars = { prefix+suffix:None for suffix in ['_USERNAME','_PASSWORD',
													   '_HOSTNAME','_DB_NAME'] }
	for ev in nec_env_vars:
		try:
			nec_env_vars[ev] = os.environ[ev]
		except:
			pass
	missing = [ ev for ev in nec_env_vars if nec_env_vars[ev] == None ]
	if missing:
		raise( Exception(f'Missing environment variables: {missing}') )

	# Get together database connection pool constructor arguments
	db_cn_args =  dict(zip(['user','password','host','db'], nec_env_vars.values()))
	db_cn_args['pool_name'] = 'ytg_connection_pool'
	db_cn_args['pool_size'] = 2

	# Try n connect to DB
	logger.info('Got all DB connection environment variables')
	cn_pool = mysql.connector.pooling.MySQLConnectionPool( **db_cn_args )
	logger.info('Created connection pool')
	
	# Create tables, if they aren't already created
	from tables import tables
	with CursorCM(cn_pool) as cursor:
		for table_name in tables:
			table_description = tables[table_name]
			try: 
				cursor.execute(table_description)
				logger.info(f'Created table "{table_name}"')
			except mysql.connector.Error as err:
				if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
					logger.info(f'"{table_name}" table already exists')
				else:
					raise(err) 

	return cn_pool





class VideoStore:
	''' self.filter_map is Ordered, so every video is put in the group corresponding
		to the filter that finds it true first. For example, if the first filter is
		True if the video has 20 views, and the second filter is True if the video's
		genre is Travel, a Travel video with 20 views will get put into the first group,
		because that group's filter came first. This is to prevent storing any uri twice.
		ATM, sorting all the videos as they're initially read from the database into the
		VideoStore is noticibly slow (as in it takes approx. 1 sec) for 20k-ish videos.
	'''
	def __init__(self, genre_map):
		self.genre_map = genre_map
		self.filter_map = OrderedDict({
				lambda vid : vid.genre_id == self.genre_map['Music'] and vid.views <= 100 : '/om',
				lambda vid : vid.genre_id == self.genre_map['Music'] 					  : '/m',
				lambda vid : vid.duration.total_seconds() > 3600 	   					  : '/tv',
				lambda vid : True 									   					  : '/'
				})

		self.route_map = { route:[] for route in self.filter_map.values() }
		
		self.vid_tup = namedtuple('vid_tup', ['uri', 'title', 'views',
											  'date', 'duration', 'genre_id'])
		
	def add(self, vid):
		''' VideoStore Ellis Island '''
		vid_tup = self.vid_tup(*vid)
		for f in self.filter_map:
			if f(vid_tup):
				self.route_map[self.filter_map[f]].append(vid_tup.uri)
				break

	def __getitem__(self, key):
		''' If you wanted to include videos from other groups in a particular route,
			you could do it here (see what it does for'/') '''
		if key == '/':
			return list(itertools.chain( *[vids for vids in self.route_map.values()] ))
		else:
			return self.route_map[key]

	def __repr__(self):
		return 'VideoStore('+str({ route:len(self.route_map[route]) for route in self.route_map})+')'

	def __contains__(self, uri):
		for store in self.route_map.values():
			if uri in store:
				return True
		return False



class QueryQueue:
	''' This is ok bc deques are threadsafe for append and popleft only,
		and no other methods get used. 
		This da primary interface for communicating w/ DB for crawler
		and for interaction data, after initial setup
	'''
	def __init__(self, cn_pool, logger):
		self.logger = logger
		self.cn_pool = cn_pool
		self.data = deque()
		self.queries_per_commit = int(os.environ.get('QUERIES_PER_COMMIT', 50))

	def append(self, query):
		self.data.append(query)
		if len(self.data) > self.queries_per_commit:
			self._commit()

	def _commit(self):
		num_queries = len(self.data)
		start = perf_counter()
		with CursorCM(self.cn_pool) as cursor:
			while len(self.data) > 0:
				try:
					query = self.data.popleft()
					print('\n'+query+'\n')
					cursor.execute(query)
				except mysql.connector.errors.IntegrityError as err:
					if err.errno == 1062:
						self.logger.info(f'Skipped duplicate')
					else:
						raise(err)
				except mysql.connector.errors.DataError as err:
					if err.errno == 1406:
						self.logger.info(f'Title too long for query:\n{query}')
					else:
						raise err
		self.logger.info(f'Did {num_queries} queries in {round(perf_counter()-start,3)}s ')



class GenreMap(UserDict):
    def __init__(self, cn_pool, query_queue, logger):
        super().__init__(self)
        self.logger = logger
        self.query_queue = query_queue

        with CursorCM(cn_pool) as cursor:
            cursor.execute('SELECT * FROM genres;')
            genres = dict(cursor.fetchall())
        self.data = { genres[gid]:int(gid) for gid in genres }
        
        self.logger.info('Successfully initialized GenreMap')


    def __missing__(self, genre):
        self.logger.info(f'New genre discovered: {genre}')
        gid = len(self.data)+1
        self.query_queue.append(f'INSERT INTO genres VALUES ( {gid}, "{genre}" );')
        self.data[genre] = gid
        return gid



def start_crawler(crawler):
	crawler.EXIT_FLAG = 0
	th = threading.Thread(target=crawler.crawl)
	th.start()
	crawler.logger.info('Started crawler thread')
	

def stop_crawler(crawler):
	crawler.EXIT_FLAG = 1	
