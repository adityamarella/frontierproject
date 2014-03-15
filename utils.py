
import os, sys
import subdist
import bs4
from fetcher import URLIterator
from config import URLS as URLS
import logging
import csv, codecs, cStringIO

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class CSVUnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

def get_text_string(node):
    if not node:
        return None
    if type(node) == bs4.element.NavigableString:
        return node.string
    else:
        return node.get_text()

def fuzzy_substring(needle, haystack):
    """Calculates the fuzzy match of needle in haystack,
    using a modified version of the Levenshtein distance
    algorithm.
    The function is modified from the levenshtein function
    in the bktree module by Adam Hupp"""
    m, n = len(needle), len(haystack)

    # base cases
    if m == 1:
        return not needle in haystack
    if not n:
        return m

    row1 = [0] * (n+1)
    for i in range(0,m):
        row2 = [i+1]
        for j in range(0,n):
            cost = ( needle[i] != haystack[j] )

            row2.append( min(row1[j+1]+1, # deletion
                               row2[j]+1, #insertion
                               row1[j]+cost) #substitution
                           )
        row1 = row2
    return min(row1)

def fuzzy_substring_score(needle, haystack):
    l = len(needle)
    ll = subdist.substring(needle, haystack)
    if l == 0:
        return 1
    return 1-ll/float(l)

def loginit(fn):
    logging.basicConfig(filename=fn, 
            format='%(asctime)s %(filename)s:%(lineno)s->%(levelname)s: %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S', level=logging.INFO)
    logging.info("Logging initialized")

def process(urls):
    it = URLIterator(urls)
    cnt = 0
    for url, soup in it.generate_soup():
        manager = ClassificationManager(url, soup)
        manager.get_collection_section()

    print "%d of %d websites gave valid output"%(cnt, len(urls))

def main():

    config.create_output_dir()
    if len(sys.argv) == 1:
        process(URLS)
    else:
        url = sys.argv[1]
        #url = 'http://www.amazon.com/gp/help/customer/display.html/ref=hp_468496_share?nodeId=468496'
        #url = 'http://www.bestbuy.com/site/Help-Topics/Privacy-Policy/pcmcat204400050062.c?id=pcmcat204400050062'
        process([url])

if __name__=='__main__':
    main()



