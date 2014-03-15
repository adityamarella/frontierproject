#!/usr/bin/env python

import sys, os
import re
import logging
import utils
from fetcher import URLIterator
import config
from utils import get_text_string
import csv
from sectioner import HeadingBasedSectioner
from stanford_utils import POSTagger

_ckw = 'ask|collect|gather|obtain|receive|hold|provide'
_skw = 'disclos|send|shar|transfer'
_ukw = 'integrat|process|use|utiliz|using|stor'
_sekw = 'encryption|ssl|security|safeguard|protect'
_ackw = 'updat|modify|view'
_chkw = 'choice|consent|opt[ -]out|opt[ -]in'

COLLECT_PATTERN = re.compile(_ckw)
SHARE_PATTERN = re.compile(_skw)
USE_PATTERN = re.compile('((?<!collect and )(%s).*?information)|(usage)'%_ukw)
SECURITY_PATTERN = re.compile('(?<!social )(%s)'%_sekw)
ACCESS_UPDATE_PATTERN = re.compile(_ackw)
CHOICES_PATTERN = re.compile(_chkw)


prior_doc_count = {}

class Classifier:

    LABELS = ("Collection", "Use", "Share", "Access", "Security", "Choice", "Notice")

    def __init__(self):
        pass

    def assign_label(self, heading, section):
        pass

class RegexClassifier(Classifier):
    
    PATTERN_LABELS = [
        (CHOICES_PATTERN, Classifier.LABELS[5]),
        (SECURITY_PATTERN, Classifier.LABELS[4]),
        (ACCESS_UPDATE_PATTERN, Classifier.LABELS[3]),
        (SHARE_PATTERN, Classifier.LABELS[2]),
        (USE_PATTERN, Classifier.LABELS[1]),
        (COLLECT_PATTERN, Classifier.LABELS[0]),
    ]

    
    def assign_label(self, heading, section):
        '''
        assigns label to the section based on heading; if that is not conclusive then the whole
        section blob is used
        @param heading: heading of the  of the section
        @param section: the whole section blob
        '''
        child_label = None
        text = get_text_string(heading).encode('utf-8')
        for pattern,label in RegexClassifier.PATTERN_LABELS:
            if pattern.search(text.lower()):
                child_label = label
                break

        #still not labelled.. try to label it using the description string
        if not child_label:
            for pattern, label in RegexClassifier.PATTERN_LABELS:
                if pattern.search(section.lower()):
                    child_label = label
                    break
        return child_label 

class ClassificationManager:
    '''
      * invokes the sectioning code
      * classifies each section into collection, sharing, use, etc categories
      * provides an interface to get the collection, sharing and use text blobs
    '''

    def __init__(self, url, soup):
        self.url = url
        self.soup = soup
        self.categories = self.__categorize(url, soup)

    #private function
    def __categorize(self, url, soup):

        heading_based_sectioner = HeadingBasedSectioner(url, soup)
        headings, sections = heading_based_sectioner.sectionize()
        if not sections:
            return {}

        categories = {}
        rc = RegexClassifier()
        for i,section in enumerate(sections):
            label = rc.assign_label(headings[i], section)
            categories.setdefault(label, []).append(section)

        if not categories or len(categories)==0:
            return None

        return categories

    #returns the list of sections which are classified as collection
    def get_collection_section(self):
        return self.categories.get(Classifier.LABELS[0], [])
    
    #returns the list of sections which are classified as sharing
    def get_sharing_section(self):
        return self.categories.get(Classifier.LABELS[2], [])
    
    #returns the list of sections which are classified as use
    def get_use_section(self):
        return self.categories.get(Classifier.LABELS[1], [])

    #pretty print categories in a HTML file
    def pretty_print_categories(self, f=sys.stdout):
        '''
            categories = {lable:node_list]
        '''
        output = '''
        <html>
        <head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>
        <body>
        <h2>Click <a href="%s">here</a> to go the source website</h2>
        <br>
        %s
        
        </body>
        </html>'''

        info_types = ""

        section = '<div><h1><font color="red">LABEL: %s </font></h1>%s</div>'
        blob=""
        if not self.categories:
            output = output%(url, blob)
            f.write(output)
            return

        for label,node_list in self.categories.iteritems():
            sec_blob = ""
            for node in node_list:
                 sec_blob = sec_blob + u'%s'%(node)
            blob = blob + section%(label, sec_blob)

        blob = blob.replace("\n", "<br>")
        output = output%(self.url, info_types, blob)
        f.write(output.encode('utf-8'))

def process(urls):
    it = URLIterator(urls)
    cnt = 0
    for url, soup in it.generate_soup():
        manager = ClassificationManager(url, soup)
        if manager.categories:
            cnt = cnt + 1
            f = sys.stdout #open("display.html", "w")
            manager.pretty_print_categories(f=f)
            f.close()
        else:
            logging.error("Error: %s"%url)
    logging.info("%d of %d websites gave valid output"%(cnt, len(urls)))

if __name__=='__main__':
    config.create_output_dir()
    utils.loginit("%s.log"%(__file__.split(".")[0]))

    if len(sys.argv) == 1:
        urls = config.URLS
    else:
        urls = [sys.argv[1]]
    process(urls)
