import sys
import re
from time import sleep
import requests
from random import choice, randint
import datetime
from collections import namedtuple, UserDict
import html
import pickle
import logging
import os

class Crawler:
    
    def __init__(self, db, Video, genre_map):
        self.db = db
        self.Video = Video
        self.genre_map = genre_map

        self.get_sw = swGenerator()
        self.search_url = 'https://www.youtube.com/results?search_query='
        self.watch_url = 'https://www.youtube.com/watch?v='

        self.vid_id_in_search_html_re = re.compile(r'"videoId":"(?P<id>.{11})"')
        self.info_from_watch_html_re =  re.compile(r'''meta\sitemprop="name"\scontent="(?P<title>[^"]*?)".*?
                                                      meta\sitemprop="interactionCount"\scontent="(?P<views>[^"]*?)".*?
                                                      meta\sitemprop="datePublished"\scontent="(?P<date>[^"]*?)".*?
                                                      meta\sitemprop="genre"\scontent="(?P<genre>[^"]*?)".*?
                                                      "approxDurationMs":"(?P<ms>[^"]*?)"''', re.X)




        logging.info('Successfully initialized Crawler')
  

    def _get_random_vid_id(self):
        sw = self.get_sw()
        url = self.search_url + sw
        html = _get_html(url)
        #logging.info(f'Made request to {url}')

        # this also needs error handling and a test
        vid_ids = self._extract_vid_ids_from_search_html(html)
        if not vid_ids:
            logging.warning(f'Error for searchword "{sw}"')
            return self._get_random_vid_id() 
        
        return choice(tuple(vid_ids)) 


    def _extract_vid_ids_from_search_html(self, html):
        match_objs = list(set(self.vid_id_in_search_html_re.findall(html)))
        return match_objs


    def _get_raw_video_info(self, vid_id):
        url = self.watch_url + vid_id
        html = _get_html(url)
        #logging.info(f'Made request to {url}')
        
        matchobj = self.info_from_watch_html_re.search(html)
        if matchobj == None:
            logging.warning(f'Regex failed for {url}')

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
                num_vids = self.Video.query.count()
                if num_vids < 10000:
                    try:
                        if num_vids % 25 == 0:
                            logging.info(f'{num_vids} in database')
                        vid_id = self._get_random_vid_id()
                        raw_info = self._get_raw_video_info( vid_id )
                        video_dict = self._video_dict_from_raw_info( *raw_info )

                        video_row_obj = self.Video( **video_dict )
                        self.db.session.add( video_row_obj )
                        self.db.session.commit()

                        logging.info(f'Committed {video_row_obj} to database')
                    except:
                        logging.error('crawler error: '+str(sys.exc_info()[0]))
                sleep(8)



class swGenerator:

    def __init__(self):
        self.words = unpickle(os.getcwd()+'/app/data/words')
        self.names = unpickle(os.getcwd()+'/app/data/names')
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



def unpickle(fname):
        with open(fname,'rb') as f:
            return pickle.load(f)


def _get_html(url):
        ''' Get HTML content of url
        '''
        r = requests.get(url)
        return r.text

