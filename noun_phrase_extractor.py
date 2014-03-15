#!/usr/bin/env python

"""
Extracts the unique noun phrases and dumps them to stdout
The output is a python set.
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
from fetcher import URLIterator
from stanford_utils import Parser, Tokenizer, POSTagger

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

class MyRegexParser:

    def __init__(self, grammar=GRAMMAR):
        self.tokenizer = Tokenizer()
        self.parser = nltk.RegexpParser(grammar)
        self.stanford_tagger = POSTagger()

    def parse(self, paragraph):
        tokens = self.tokenizer.span_tokenize(paragraph)
        pos_tagged_tokens = []
        max_size = 500
        if len(tokens)>max_size:
            num_words = len(tokens)
            for i in xrange(1+num_words/max_size):
                end = (i+1)*max_size
                if end > num_words:
                    end = num_words
                tks = tokens[i*max_size:end]
                words = [token[0].encode("utf-8") for token in tks]
                pos_tagged_tokens.extend(self.stanford_tagger.tag(words))
        else:
            words = [token[0].encode("utf-8") for token in tokens]
            pos_tagged_tokens.extend(self.stanford_tagger.tag(words))

        tree = self.parser.parse(pos_tagged_tokens)
        return tokens, tree

    def getIndicesForLabel(self, tokens, tree, label):

        ret = []
        words = [token[0].encode("utf-8") for token in tokens]
        lst = self.getTreesForLabel(tree, label)
        last_token_idx = 0
        for item in lst:
            leaves = item.leaves()
            size = len(leaves)
            try:
                idx = words.index(leaves[0][0], last_token_idx)
            except:
                continue
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


class NounPhraseMarker:

    def __init__(self):
        self.parser = MyRegexParser()

    def mark(self, url, soup):
        website = urlparse.urlparse(url).netloc
        if website.startswith("www"):
            website = website.split(".")[1]
        else:
            website = website.split(".")[0]

        sectioner = HeadingBasedSectioner(url, soup) 
        headings, sections = sectioner.sectionize()

        nphrases = set([])
        for i, section in enumerate(sections):
            marked_section = ""
            st = 0
            end = 0
            cnt_spans = 0

            section_lower = section.lower()

            terms = ["collect", "use", "shar", "stor", "retain", "retention", "provid", "receiv", "disclos", "using"]

            for term in terms:
                if section_lower.find(term) != -1:
                    break
            else:
                continue

            tokens, tree = self.parser.parse(section)
            arr = self.parser.getIndicesForLabel(tokens, tree, "NP")
            for item in arr:
                end = item[0]
                #st is prev start index here;
                #st is updated after this statement; do not mess with the order of these stmts
                marked_section = marked_section + section[st:end] 
                st = item[1]
                np = section[end:st]
                if np.find('\n')!=-1:
                    continue
                nphrases.add(np.lower())
                marked_section = "%s%s%s%s"%(marked_section, SPAN_START%(cnt_spans), np, SPAN_END)
                cnt_spans = cnt_spans + 1
        return nphrases

def process(arg):
    urls, outfile = arg
    ofp = open(outfile, "w")

    n = NounPhraseMarker()
    cnt = 0
    nphrases = set([])
    it = URLIterator(urls)
    for url, soup in it.generate_soup():
        nps = n.mark(url, soup)
        if nps and len(nps) > 0:
            cnt = cnt + 1
            ofp.write("%s\n"%url)
            ofp.write("%s\n"%repr(nps))
    ofp.close()

if __name__=='__main__':
    config.create_output_dir()
    utils.loginit("%s.log"%(__file__.split(".")[0]))

    n = NounPhraseMarker()
    if len(sys.argv) == 2:
        urls = config.URLS
    elif len(sys.argv) == 3:
        urls = [sys.argv[2]]
    else:
        print "Usage: python <script> <outputfile> <optional: url>"
        sys.exit(1)

    process((urls, sys.argv[1]))
