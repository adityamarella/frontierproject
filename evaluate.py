#!/usr/bin/env python


import sys, os
import csv
import glob
from sectioner import HeadingBasedSectioner
from fetcher import URLIterator
from ngram import NGram
from utils import get_text_string
from nltk.tokenize import word_tokenize, sent_tokenize
from itertools import combinations
from utils import CSVUnicodeReader
from utils import fuzzy_substring_score
import subdist
import xml.dom.minidom as DOM

class Evaluator(object):

    def __init__(self, categories_relevant, categories_extracted):
        self.cr = categories_relevant
        self.ce = categories_extracted

    def evaluate_using_ngrams(self, n):
        '''
        @param n suggests n-gram evaluation
        '''
        
        p = r = cnt = 0
        for category, section in self.ce.iteritems():
            
            rtokens = word_tokenize(self.cr[category])
            etokens = word_tokenize(section)
 
            elen = len(etokens)
            rlen = len(rtokens)

            rngram_set = set([])
            engram_set = set([])

            for i in xrange(rlen):
                if i== (rlen - n + 1):
                    continue
                rngram_set.add(tuple(rtokens[i:i+n]))

            for i in xrange(elen):
                if i== (elen - n + 1):
                    continue
                engram_set.add(tuple(etokens[i:i+n]))

            intersection = rngram_set.intersection(engram_set)
            
            positives = len(intersection)
            num_engrams = len(engram_set)
            num_rngrams = len(rngram_set)
            
            if elen == 0:
                p = 1
            else:
                p = p + float(positives) / float(num_engrams)
            
            if rlen == 0:
                r = 1
            else:
                r = r + float(positives) / float(num_rngrams)

            cnt = cnt + 1

        if cnt == 0:
            return 0,0

        return (p*100)/cnt, (r*100)/cnt
 
    def evaluate_using_sentence_pairs(self):

        rsents = []
        esents = []

        for category, section in self.cr.iteritems():
            rsents.extend([ (category, sent) for sent in sent_tokenize(section)])
        for category, section in self.ce.iteritems():
            esents.extend([ (category, sent) for sent in sent_tokenize(section)])

        rlen = len(rsents)
        elen = len(esents)
        
        num_pair_rsents = (rlen * (rlen-1))/2
        num_pair_esents = (elen * (elen-1))/2
        truepositives = 0
        
        for i,j in combinations(range(elen), 2):
            iflag = False
            jflag = False
            
            ctgi, senti = esents[i]
            ctgj, sentj = esents[j]

            rsection = self.cr[ctgi]
            if fuzzy_substring_score(senti.strip().lower(), rsection.strip().lower()) > .95:
                iflag = True

            rsection = self.cr[ctgj]
            if fuzzy_substring_score(sentj.strip().lower(), rsection.strip().lower()) > .95:
                jflag = True

            if iflag and jflag:
                truepositives = truepositives + 1

        precision = float(truepositives)/float(num_pair_esents)
        recall = float(truepositives)/float(num_pair_rsents)

        print num_pair_esents, num_pair_rsents

        return precision, recall
    

def get_privacy_url(f):
    
    name = f.split("/")[-1].split(".")[0]
    for url in URLS:
        if url.find(name)!=-1:
            return url
    return None

def get_csv_file(url):
    files = glob.glob("travis_data/*.csv")
    for f in files:
        fn = f.split("/")[-1].split(".")[0]
        if url.find(fn) != -1:
            return f
    return None

def get_headings_and_sections(url):

    headings = {}
    f = get_csv_file(url)
    fp = open(f, "rb")
    r = CSVUnicodeReader(fp, delimiter=",", quotechar='"')
    for row in r:
        headings[row[1]] = "%s %s"%(headings.setdefault(row[1], ''), row[2])
    fp.close()

    return headings.keys(), headings.values()

def get_first_child_text(node, childtagname):

    children = node.getElementsByTagName(childtagname)
    if len(children) == 1:
        if len(children[0].childNodes) == 1:
            return children[0].childNodes[0].nodeValue
    return ""

def get_headings_and_sections_fei():
    ret = []
    files = glob.glob("fei_data/Annotation_Input/Phase_*/*.xml")
    for fn in files:
        document = DOM.parse(fn)
        url = document.getElementsByTagName('POLICY')[0].attributes["policy_url"].value
        sections = document.getElementsByTagName('SECTION')
        headings = [get_first_child_text(section, "SUBTITLE") for section in sections]
        sections = [get_first_child_text(section, "SUBTEXT") for section in sections]
        ret.append( (url, headings, sections) )
    return ret

def get_headings_and_sections_1(url, soup):
   
    if not soup:
        return None, None

    s = HeadingBasedSectioner(url, soup)
    return s.sectionize()

def truncate(s):
    l = len(s)
    if l > 20:
        return s[:20]+".."
    return s + " "*(22-l)

def process(hr,sr,he,se):

    categories_relevant = {}
    categories_extracted = {}

    category_idx_list = []
    for i,h in enumerate(hr):
        for j,h1 in enumerate(he):
            if NGram.compare(hr[i], he[j]) > 0.95:
                category_idx_list.append((i,j))

    if he:
        if len(he) != len(se):
            return 0 , 0
    for i,C in enumerate(category_idx_list):
        categories_relevant[i] = sr[C[0]]
        tmp = se[C[1]].replace('\r', '').replace('\n','')
        categories_extracted[i] = tmp

    e = Evaluator(categories_relevant, categories_extracted)
    p, r = e.evaluate_using_ngrams(3)

    return p, r

def evaluate_travis_data():

    urls = config.TRAVIS_URLS
    ap = 0
    ar = 0
    cnt = 0
    it = URLIterator(urls)
    for url, soup in it.generate_soup():
        print url
        hs, s = get_headings_and_sections(url)
        hs1, s1 = get_headings_and_sections_1(url, soup)
        if not hs1:
            ths1 = []
        else:
            ths1 = [get_text_string(th).strip() for th in hs1]

        p, r = process(hs, s, ths1, s1)
        ap = ap + p
        ar = ar + r
        cnt = cnt + 1

    print ap/float(cnt), ar/float(cnt)

def evaluate_fei_data():
    
    arr = get_headings_and_sections_fei()
    ap = 0
    ar = 0
    cnt = 0

    for url, hs, s in arr:
        it = URLIterator([url])
        for url, soup in it.generate_soup():
            hs1, s1 = get_headings_and_sections_1(url, soup)
            if not hs1:
                ths1 = []
            else:
                ths1 = [get_text_string(th).strip() for th in hs1]
       
        p, r = process(hs, s, ths1, s1)
        if p*r != 0:
            ap = ap + p
            ar = ar + r
            cnt = cnt + 1
        else:
            print url
            print hs
            print s
            print ths1
            print s1
            break

    print "%d of %d processed successfully"%(cnt, len(arr))
    print ap/float(cnt), ar/float(cnt)
    

if __name__=='__main__':

    evaluate_travis_data()
    evaluate_fei_data()
