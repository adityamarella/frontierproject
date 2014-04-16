#!/usr/bin/env python

"""
This file contains code to mark the noun phrases given a privacy url.
Outputs several html files with nounphrases marked as HTML spans. These spans
are initially not colored but change to red color when you click on them.

Usage:
 
#> python noun_phrase_marker.py "http://www.amazon.com/gp/help/customer/display.html/ref=footer_privacy?ie=UTF8&nodeId=468496"
"""

import socket
import os, sys
import config
import jpype
import urlparse
import nltk
import utils
from jpype import *
from sectioner import HeadingBasedSectioner
from stanford_utils import Parser, Tokenizer, POSTagger
from fetcher import URLIterator

OUT_FILE_PREFIX="out"

HTML_START = '''
<html>
<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        
<style>
       
.red {
    color: red;
}
.green {
    color: green;
}
.underline {
    text-decoration:underline;
}

</style>
        
<script type="text/javascript">

function setResult() {

    var tb = document.getElementById("result");

    var result = "";
    for(var i=0; i<%d; i++) {
        var np = document.getElementById("np"+i);
        if(np.className == "red") {
            if(result.length != 0 )
                result = result + ";";
            result = result+np.innerHTML;
        }
    }
    tb.value = result;
}

function setPhrase(elem) {
    if(elem.className!='red') 
        elem.className='red'; 
    else 
        elem.className=''
}

</script>

</head>
<body>
'''
HTML_END = '''</body></html>'''
SECTION_START = '<div>'
SECTION_END = '</div>'
INPUT_BOX = '<input type="text" id="result" value=""/><br>'
SUBMIT = '<input type="submit" value="Submit" onclick="setResult();">'
SPAN_START = '''<span id="np%d" onclick="setPhrase(this);">'''
SPAN_END = '</span>'

GRAMMAR = r'''

NBAR:
    {<NN.*|JJ>*<NN.*>} # Nouns and Adjectives, terminated with Nouns

NP:
    {<NBAR><-LRB-><NBAR><-RRB-><NBAR>}
    {<NBAR><IN><NBAR>}
    {<NBAR><POS><NBAR>}
    {<RB><NBAR>}
    {<NBAR>}

'''

class MyRegexParser(object):

    def __init__(self, grammar=GRAMMAR):
        self.tokenizer = Tokenizer()
        self.parser = nltk.RegexpParser(grammar)
        self.stanford_tagger = POSTagger()

    def parse(self, paragraph):
        tokens = self.tokenizer.span_tokenize(paragraph)
        words = [token[0] for token in tokens]
        pos_tagged_tokens = self.stanford_tagger.tag(words)

        tree = self.parser.parse(pos_tagged_tokens)
        return tokens, tree

    def getIndicesForLabel(self, tokens, tree, label):

        ret = []
        words = [token[0] for token in tokens]
        lst = self.getTreesForLabel(tree, label)
        last_token_idx = 0
        for item in lst:
            leaves = item.leaves()
            size = len(leaves)
            idx = words.index(leaves[0][0], last_token_idx)
            for i in xrange(size):
                if words[idx+i] != leaves[i][0]:
                    break
            else:
                ret.append((tokens[idx][1], tokens[idx+size-1][2]))
                last_token_idx = idx + size
        
        return ret
            
    def getTreesForLabel(self, ptree, lb):
        if ptree.node == lb:
            return [ptree]

        ret = []
        for child in ptree:
            if type(child) == nltk.tree.Tree:
                ret.extend(self.getTreesForLabel(child, lb))
     
        return ret


class NounPhraseMarker(object):

    def __init__(self):
        self.parser = MyRegexParser(GRAMMAR)

    def mark(self, url, soup):
        
        website = urlparse.urlparse(url).netloc
        if website.startswith("www"):
            website = website.split(".")[1]
        else:
            website = website.split(".")[0]

        sectioner = HeadingBasedSectioner(url, soup) 
        headings, sections = sectioner.sectionize()

        if not sections:
            return

        for i, section in enumerate(sections):
            marked_section = ""
            st = 0
            end = 0
            cnt_spans = 0

            tokens, tree = self.parser.parse(section)
             
            arr = self.parser.getIndicesForLabel(tokens, tree, "NP")
            for item in arr:
                end = item[0]
                #st is prev start index here;
                #st is updated after this statement; do not mess with the order of these stmts
                marked_section = marked_section + section[st:end] 
                st = item[1]
                marked_section = "%s%s%s%s"%(marked_section, SPAN_START%(cnt_spans), section[end:st], SPAN_END)
                cnt_spans = cnt_spans + 1

            f = open("%s_%d.html"%(website,i), "w")
            f.write(HTML_START%(cnt_spans))
            f.write(SECTION_START)
            f.write(marked_section.encode("utf-8"))
            f.write(SECTION_END)
            
            f.write(SECTION_START)
            f.write(INPUT_BOX)
            f.write(SUBMIT)
            f.write(SECTION_END)
            
            f.write(HTML_END)
            f.close()

def process(urls):
    n = NounPhraseMarker()
    it = URLIterator(urls)
    for url, soup in it.generate_soup():
        n.mark(url, soup)

if __name__=='__main__':
    config.create_output_dir()
    utils.loginit("%s.log"%(__file__.split(".")[0]))
    
    if len(sys.argv) == 1:
        urls = config.URLS
    else:
        urls = [sys.argv[1]]

    process(urls)
