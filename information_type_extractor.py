#!/usr/bin/env python

import os, sys
import config
import jpype
import nltk
import re
import utils
from jpype import *
from classify import ClassificationManager
from nltk.tokenize import word_tokenize
from stanford_utils import Parser, Tokenizer, POSTagger
from fetcher import URLIterator

TAG_PATTERNS = [
    (r'[,;]', 'COMMA'),
    (r'includ(e|es|ing)|such', 'L'),
    (r'information|data', 'D'),
    (r'as', 'AS'),
    (r':', 'COLON'),
    (r'\w', 'ANY'),
    (r'[\(\{\[]', 'OB'),
    (r'[\)\}\]]', 'CB')
]

GRAMMAR = r'''
NP: 
    {<NN[A-Z]?>+ <D> }
    {(<JJ> | <NN[A-Z]?>)* (<NN[A-Z]?> <IN>)? (<JJ> | <NN[A-Z]?>)* <NN[A-Z]?> }
    
LST:
    {<D><L><AS>?}
    {<L><D><AS>}
    {<L><[A-Z$]+>*<COLON>}
    {<L><AS>}
    {<L>}

EX:  
    {<LST><[A-Z$]+>?(<[A-Z$]+>?<NP><COMMA>?<CC>?)+}

EXAMPLE:
    {<EX> <OB> <EX>* <OTH>* <CB> (<COMMA>?<NP><COMMA>?<CC>?)+}
    {<EX>}

'''

class InformationTypeExtractor(object):

    def __init__(self):
        self.tokenizer = Tokenizer()
        self.parser = nltk.RegexpParser(GRAMMAR)
        self.stanford_tagger = POSTagger()
        self.re_tagger = nltk.RegexpTagger(TAG_PATTERNS, backoff=nltk.DefaultTagger('ANY'))

    def extract(self, paragraph):
        data = set([])

        words = self.tokenizer.tokenize(paragraph)
        
        pos_tagged_tokens = self.stanford_tagger.tag(words)
        re_tagged_tokens = self.re_tagger.tag(words)
       
        if len(pos_tagged_tokens) != len(re_tagged_tokens):
            import pdb; pdb.set_trace()

        #merge re tags and pos tags
        for i, tag in enumerate(re_tagged_tokens):
            if tag[1] != "ANY":
                pos_tagged_tokens[i] = tag

        tree = self.parser.parse(pos_tagged_tokens)

        examples = self.get_data_chunks(tree, "EXAMPLE")

        for ex in examples:
            s = ""
            for item in ex:
                s = "%s %s"%(s, item[0])
            s = s[1:]
            data.add(cleanup_word(s).lower())
        return data
    
    def get_data_chunks(self, tree, name="EXAMPLE"):

        examples = []
        for child in tree:
            if type(child) == nltk.Tree and child.node == name:
                if name == "EXAMPLE":
                    examples.extend(self.get_data_chunks(child, "EX"))
                for c in child:
                    if type(c) == nltk.Tree:
                        if c.node == "NP":
                            examples.append(c.leaves())
        return examples

class ExtractionManager(object):

    def __init__(self):
        self.extractor = InformationTypeExtractor()

    def extract(self, url, soup):
        manager = ClassificationManager(url, soup) 
        collection_data = self.merge(manager.get_collection_section())
        sharing_data = self.merge(manager.get_sharing_section())
        use_data = self.merge(manager.get_use_section())
        return collection_data, sharing_data, use_data

    def merge(self, sections):
        rset = set([])
        for i, section in enumerate(sections):
            s = section.replace("<br>", "\n")
            s = unicode(s)
            iset = self.extractor.extract(s)
            rset = rset.union(iset)
        return rset


def cleanup_word(word):
    if word[-1] in ['.', '!', '"', "'", "?", ")"]:
        word = word[:-1]
    return word.lower()

def process(urls):
    extraction_manager = ExtractionManager()
    it = URLIterator(urls)
    for url, soup in it.generate_soup():
        print url
        c, s, u = extraction_manager.extract(url, soup)
        print "Collection = %s"%repr(c)
        print "Sharing = %s"%repr(s)
        print "Use = %s"%repr(u)

if __name__=='__main__':
    config.create_output_dir()
    utils.loginit("%s.log"%(__file__.split(".")[0]))
    
    if len(sys.argv) == 1:
        urls = config.URLS
    else:
        urls = [sys.argv[1]]
    process(urls)
