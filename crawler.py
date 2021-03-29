import html
import os
import pickle
from random import choice, randint
import re
import requests
from time import sleep
import datetime

from utils import CursorCM, QueryQueue

MAX_VIEWS = 2**32 -1



class Crawler:
	def __init__(self, query_queue, video_store, genre_map, logger):
		self.query_queue = query_queue
		self.video_store = video_store
		self.genre_map = genre_map
		self.logger = logger
		self.get_sw = SwGenerator()

		self.EXIT_FLAG = 1
		self.timeout = os.environ.get('CRAWLER_TIMEOUT',5)

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
				 int(duration) / 1000,
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
		while True:
			try:
				vid_id = self._get_random_vid_id()
				vid_info_tup = self._get_video_info_from_watch_page(vid_id)
				
				# one day, one day ill kill u...
				self.logger.info(f'Found video: {vid_info_tup[0]}')		
							
				self.video_store.add(vid_info_tup)
				self.query_queue.append(f"INSERT INTO videos VALUES "
										f"( NULL, { str(vid_info_tup[:4])[1:-1] }, "
										f"SEC_TO_TIME({vid_info_tup[4]}), {vid_info_tup[5]} );")
				
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
			







class SwGenerator:
	def __init__(self):
		cwd = os.path.abspath(os.path.dirname(__file__))
		self.words = self.unpickle(cwd+'/data/words')
		self.names = self.unpickle(cwd+'/data/names')
		self.alphabet = 'abcdefghijklmnopqrstuvwxyz1234567890'
		self.sws = self.sw_gen_factory()

	
	def unpickle(self, fname):
		with open(fname,'rb') as f:
			return pickle.load(f)


	def cut_down(self, word, length):
		if len(word) > length:
			start = choice(range(len(word)-length))
			word = word[start : start+length]
		return word


	def gibberish(self, length):
		return ''.join(choice(self.alphabet) for i in range(length))


	def sw_gen_factory(self):
		while 1:
			yield self.gibberish(randint(3,5))
			yield self.cut_down(choice(self.words), randint(4,7))
			yield self.cut_down(choice(self.names), randint(4,6))


	def __call__(self):
		return next(self.sws)


class swError(Exception):
    def __init__(self,sw):
        super(swError,self).__init__(f'Search failed for: {sw}')

class regexFailure(Exception):
    def __init__(self,vid_id):
        super(regexFailure,self).__init__(f'Regex failed for video: {vid_id}')

