import html
import os
import pickle
from random import choice, randint
import re
import requests
from time import sleep

from utils import CursorCM, QueryQueue

MAX_VIEWS = 2**32 -1



class Crawler:
	def __init__(self, query_queue, video_store, genre_map, logger):
		self.query_queue = query_queue
		self.video_store = video_store
		self.genre_map = genre_map
		self.logger = logger
		self.get_sw = swGenerator()

		self.EXIT_FLAG = 1
		self.timeout = 0

		self.search_url = 'https://www.youtube.com/results?search_query='
		self.watch_url = 'https://www.youtube.com/watch?v='

		self.vid_id_in_search_html_re = re.compile(r'"videoId":"(?P<id>.{11})"')
		self.info_from_watch_html_re =  re.compile(r'''meta\sitemprop="name"\scontent="(?P<title>[^"]*?)".*?
													   meta\sitemprop="interactionCount"\scontent="(?P<views>[^"]*?)".*?
													   meta\sitemprop="datePublished"\scontent="(?P<date>[^"]*?)".*?
													   meta\sitemprop="genre"\scontent="(?P<genre>[^"]*?)".*?
													   "approxDurationMs":"(?P<ms>[^"]*?)"''', re.X)
		
		self.logger.info('Successfully initialized Crawler')
 

	@staticmethod
	def _get_html(url):
		r = requests.get(url)
		r.raise_for_status()
		return r.text

	'''@staticmethod
	def _ms_to_sql_time(ms):
		ms = int(ms)
		s = ms / 1000
		m, s = s//60, s%60
		h, m = m//60, m%60
		h, m, s = ( str(int(i)).rjust(2,'0') for i in [h,m,s])
		return ':'.join((h,m,s))'''

	def _get_random_vid_id(self):
		sw = self.get_sw()
		url = self.search_url + sw
		html = self._get_html(url)
		vid_ids = list(set(self.vid_id_in_search_html_re.findall(html)))
		if not vid_ids: 
			raise swError(sw)
		return choice(tuple(vid_ids)) 

	def _clean_video_tuple(self, vid_id, title, views, date, genre, duration):
		return ( vid_id,
				 html.unescape(title).replace("'",'')[:99],
				 min(int(views), MAX_VIEWS),
				 date,
				 datetime.timedelta(seconds = duration / 1000),
				 self.genre_map[ html.unescape(genre) ] )

	def _get_video_info_from_watch_page(self, vid_id):
		url = self.watch_url + vid_id
		html = self._get_html(url) 
		matchobj = self.info_from_watch_html_re.search(html)
		if matchobj == None: 
			raise regexFailure(vid_id)        
		info = self._clean_video_tuple(vid_id, *matchobj.groups())
		return info


	def crawl(self):
		self.logger.info('Crawler startine')
		#vid_tup = namedtuple('vid_tup', ['uri','title','views','date','duration','genre'])
		while True:
			try:
				vid_id = self._get_random_vid_id()
				vid_info_tup= self._get_video_info_from_watch_page(vid_id)
				
				# one day, one day ill kill u...
				self.logger.info(f'Found video: {vid_info_tup[0]}')		
							
				self.video_store.add(vid_info_tup)
				#vid_info_tup[-1] = self.genre_map[vid_info_tup[-1]]
				#vid_info_tup[-2] = self._ms_to_sql_time(vid_info_tup[-2]*1000)
				self.query_queue.append(f"INSERT INTO videos VALUES ( NULL, { str(vid_info_tup)[1:-1] } );")
				
				sleep(self.timeout)

				if self.EXIT_FLAG:
					self.logger.info('Crawler stoppine')
					exit()

			except requests.exceptions.HTTPError as err:
				if err.response.status_code == 429:
					self.logger.warning('429!')
					self.EXIT_FLAG = 1
					exit()
				else:
					raise err
			except (regexFailure, swError) as err:
				self.logger.info(err)
				sleep(self.timeout)
			









class swGenerator:
    def __init__(self):
        cwd = os.path.abspath(os.path.dirname(__file__))
        self.words = self.unpickle(cwd+'/data/words')
        self.names = self.unpickle(cwd+'/data/names')
        self.meths = [self._gib, self._word, self._name]
        self.sws = self.infinite_sws()
       
    @staticmethod
    def unpickle(fname):
        with open(fname,'rb') as f:
            return pickle.load(f)

    @staticmethod
    def cut_down(word, length):
        if len(word) > length:
            start = choice(range(len(word)-length))
            word = word[start : start+length]
        return word

    @staticmethod
    def gibberish(length):
        alphabet = 'abcdefghijklmnopqrstuvwxyz1234567890'
        return ''.join(choice(alphabet) for i in range(length))

    def _gib(self):
        return self.gibberish(randint(3,5))

    def _word(self):
        return self.cut_down(choice(self.words), randint(4,7))

    def _name(self):
        return self.cut_down(choice(self.names), randint(4,6))
   
    def infinite_sws(self):
        i = 0
        while True:
            index = i % len(self.meths)
            meth = self.meths[index]
            yield meth()
            i+=1

    def __call__(self):
        return next(self.sws)








class swError(Exception):
    def __init__(self,sw):
        super(swError,self).__init__(f'Search failed for: {sw}')

class regexFailure(Exception):
    def __init__(self,vid_id):
        super(regexFailure,self).__init__(f'Regex failed for video: {vid_id}')

