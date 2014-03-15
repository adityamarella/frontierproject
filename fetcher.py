
import os, sys
import urllib3
import socket
import config
import logging
from bs4 import BeautifulSoup


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0',
    'Cookie': 'a=b',
}

class Fetcher(object):

    def __init__(self, pool_size=1):
        socket.setdefaulttimeout(20)
        self.http = urllib3.PoolManager(pool_size)

    def fetch_url(self, url):
        try:
            return self.http.urlopen('GET', url, headers=HEADERS, assert_same_host=False, timeout=20).data
        except urllib3.exceptions.TimeoutError:
            return None

fetcher = Fetcher(1)

def fetch_url(url):
    url_dict = {}
    if not os.path.exists("%s/url"%config.CACHE_DIR):
        if not os.path.exists(config.CACHE_DIR):
            os.makedirs(config.CACHE_DIR)

        fp = open("%s/url"%config.CACHE_DIR, "w")
        fp.close()
    fp = open("%s/url"%config.CACHE_DIR, "r+")
    i=0
    for line in fp:
        url_dict.setdefault(line.strip(), "%d"%i)
        i = i + 1
    
    f = url_dict.get(url)
    if f is None:
        data = fetcher.fetch_url(url)
        out = open("%s/%d"%(config.CACHE_DIR, i), "w")
        out.write(data)
        out.close()
        fp.write("%s\n"%url)
    else:
        data = open("%s/%s"%(config.CACHE_DIR, f)).read()

    fp.close()

    return data


class URLIterator:

    def __init__(self, urls):
        self.urls = urls
        self.iterpos = 0

    def next(self):
        if self.iterpos%10==0:
            logging.info("processing state %d of %d"%(self.iterpos+1, len(self.urls)))
        if self.iterpos == len(self.urls):
            return None
        self.iterpos = self.iterpos + 1
        return self.urls[self.iterpos-1]

    def has_next(self):
        if self.iterpos < len(self.urls):
            return True
        return False

    def iterate(self):
        for i, url in enumerate(self.urls):
            if i%10==0:
                logging.info("processing state %d of %d"%(i+1, len(self.urls)))
            yield url

    def generate_soup(self):

        for i, url in enumerate(self.urls):
            if i%10==0:
                print "iteration state %d of %d"%(i+1, len(self.urls))
            try:
                data = fetch_privacy_url(url)
            except Exception, e:
                print e
                data = None

            if not data:
                print "not a privacy url: %s"%url
                soup = None
            else:
                soup = BeautifulSoup(data)

                exclude_nodes = soup.findAll(config.EXCLUDE_TAGS)
                for node in exclude_nodes:
                    node.decompose() #deletes and destroys exclude tags

            yield url, soup

class PrivacyURLChecker:

    def __init__(self, url, data=None):
        self.url = url
        if data:
            self.data = data
        else:
            try:
                self.data = fetch_url(url)
            except Exception as e:
                print e
                raise Exception("url fetch error")

    def check(self):
        data = self.data 
        if config.PRIVACY_TEXT_PATTERN1.search(data) and \
                config.PRIVACY_TEXT_PATTERN2.search(data) and \
                config.PRIVACY_TEXT_PATTERN3.search(data):
            return True
        return False

def fetch_privacy_url(url):
    data = fetch_url(url)
    c = PrivacyURLChecker(url, data)
    if c.check():
        return data
    return None

