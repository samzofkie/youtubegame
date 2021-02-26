import sys
import re
from time import sleep
import requests
from random import choice, randint, random
import datetime
from collections import namedtuple, UserDict
import html
import pickle
import logging
import os
import traceback
from ..models import Video
from .. import db
from .genreMap import GenreMap


class Crawler:
    
    def __init__(self): 
        self.logger = logging.getLogger('root')
        
        self.genre_map = GenreMap()

        self.get_sw = swGenerator()

        self.timeout = Timeout()


        self.search_url = 'https://www.youtube.com/results?search_query='
        self.watch_url = 'https://www.youtube.com/watch?v='

        self.vid_id_in_search_html_re = re.compile(r'"videoId":"(?P<id>.{11})"')
        self.info_from_watch_html_re =  re.compile(r'''meta\sitemprop="name"\scontent="(?P<title>[^"]*?)".*?
                                                      meta\sitemprop="interactionCount"\scontent="(?P<views>[^"]*?)".*?
                                                      meta\sitemprop="datePublished"\scontent="(?P<date>[^"]*?)".*?
                                                      meta\sitemprop="genre"\scontent="(?P<genre>[^"]*?)".*?
                                                      "approxDurationMs":"(?P<ms>[^"]*?)"''', re.X)
        

        self.logger.info('Successfully initialized crawler')
  

    def _get_random_vid_id(self):
        sw = self.get_sw()
        url = self.search_url + sw
        html = _get_html(url)

        vid_ids = self._extract_vid_ids_from_search_html(html)
        if not vid_ids: raise swError(sw)
            
        return choice(tuple(vid_ids)) 


    def _extract_vid_ids_from_search_html(self, html):
        match_objs = list(set(self.vid_id_in_search_html_re.findall(html)))
        return match_objs


    def _get_raw_video_info(self, vid_id):
        url = self.watch_url + vid_id
        html = _get_html(url)
        
        matchobj = self.info_from_watch_html_re.search(html)
        if matchobj == None: raise regexFailure(vid_id)

        return (vid_id, *matchobj.groups())


    def _video_dict_from_raw_info(self, vid_id, title, views, date, genre, duration): 
        return { 'vid_id' : vid_id,
                 'title' : html.unescape(title),
                 'views' : int(views),
                 'date' : datetime.datetime( *(int(i) for i in date.split('-')) ),
                 'duration' : datetime.timedelta(milliseconds = int(duration)),
                 'genre' : self.genre_map[ html.unescape(genre) ] }
 

    def crawl(self, app):
        with app.app_context():
            while True:
                try:
                    num_vids = Video.query.count()
                    if num_vids % 25 == 0:
                        self.logger.info(f'{num_vids} in database')

                    # Makin first req, possible error for sw warning (and sleep)
                    vid_id = self._get_random_vid_id()

                    self.timeout()

                    # Makes second req, for watch endpoint. 429s would happen here
                    # If a 429 happens, rest o block gets skipped, so deescalate could happen after here
                    raw_info = self._get_raw_video_info( vid_id )

                    # These lines could maybe be combined?
                    video_dict = self._video_dict_from_raw_info( *raw_info )
                    video_row_obj = Video( **video_dict )
                    db.session.add( video_row_obj )
                    db.session.commit()
                    self.logger.info(f'Committed {video_row_obj} to database')

                except (swError, regexFailure) as err:
                    self.logger.error(err)
                except requests.exceptions.HTTPError as err:
                    self.logger.error(err)
                    self.timeout.escalate()
                except:
                    traceback.print_tb(sys.exc_info()[0])
                    self.logger.error(f'unknown error: {sys.exc_info[0]}')
                
                self.timeout()

class Timeout:
    def __init__(self):
        self.timeout = 5

    def __call__(self):
        t = self.timeout
        self.rsleep(t, t//3)
        if self.timeout > 5: 
            self.deescalate()

    def escalate(self):
        self.timeout = min(self.timeout * 5, 78125)

    def deescalate(self):
        t = self.timeout
        self.timeout = max( t/5 , 5 )

    @staticmethod
    def rsleep(n,dev):
        sleep((random()-0.5)*dev*2+n)



class swGenerator:

    def __init__(self):
        cwd = os.path.abspath(os.path.dirname(__file__))
        self.words = unpickle(cwd+'/data/words')
        self.names = unpickle(cwd+'/data/names')
        self.sw_map = { 0 : self._gib_sw,
                        1 : self._word_sw,
                        2 : self._name_sw }
        self.counter = 0
        
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

    def _gib_sw(self):
        return self.gibberish(randint(3,5))

    def _word_sw(self):
        return self.cut_down(choice(self.words), randint(4,7))

    def _name_sw(self):
        return self.cut_down(choice(self.names), randint(4,6))
    
    def __call__(self):
        self.counter += 1
        return self.sw_map[self.counter%3]()


class swError(Exception):
    def __init__(self,sw):
        super(swError,self).__init__(f'Search failed for sw {sw}')

class regexFailure(Exception):
    def __init__(self,vid_id):
        super(regexFailure,self).__init__(f'Regex failed for video at {vid_id}')



def unpickle(fname):
        with open(fname,'rb') as f:
            return pickle.load(f)


def _get_html(url):
        ''' Get HTML content of url
        '''
        r = requests.get(url)
        r.raise_for_status()
        return r.text
