
class TOCBasedHeadingExtractor(Sectioner):


    def sectionize(self):
        a_nodes = soup.findAll("a")
        headings = []
        matched_node = None
        for node in a_nodes:
            matched = False
            for pattern in Sectioner.PATTERN_LABELS:
                tt = node.get_text().encode("utf-8").lower()
                if pattern.search(tt):
                    tags = pt.tag(tt.split())
                    for word, tag in tags:
                        if tag.startswith("VB"):
                            matched = True
                            break
                    if matched:
                        break

            if matched:
                link = node.attrs.get("href", "")
                if link.find("#")!=-1:
                    matched = False
                    parent = node.findParent()
                    while True:
                        children = parent.findChildren("a")
                        if len(children) > 1:
                            if parent.name == "ul":
                                headings = list(parent.children)
                                matched = True
                                break
                        parent = parent.findParent()
                        if not parent:
                            break

                    if matched:
                        break

        lst = []
        for heading in headings:
            if type(heading) == bs4.element.NavigableString:
                continue
            if heading.name != 'li':
                continue

            child = heading.findChild('a')
            if not child:
                break

            href = child.attrs.get("href", None)
            if not href:
                break
            index = href.find("#")
            if index == -1:
                break

            href = href[index+1:]

            node_list = soup.findAll("a", attrs={"name":href})
            if len(node_list) != 1:
                break

            if len(node_list[0].get_text().strip().lower()) == 0:
                break

            lst.append(node_list[0])

        if len(lst) != len(headings):
            lst = []

            for heading in headings:
                if type(heading) == bs4.element.NavigableString:
                    continue
                text = heading.get_text()
                node_list = soup.body.findAll(text = re.compile(text.strip(), re.I))
                if len(node_list) != 2:
                    return None, None
                lst.append(node_list[1])

        if not lst or len(lst) == 0:
            return None, None

        tmp_lst = [get_text_string(item).strip() for item in lst]
        re_text = ")|(".join(tmp_lst)
        re_text = "(%s)"%(re_text)

        re_obj = re.compile(re_text, re.I)

        headings = None
        parent = lst[0].findParent()
        while True:
            children = parent.findChildren(text=re_obj)
            if len(children) > 1:
                headings = children
                break
            parent = parent.findParent()
            if not parent:
                return None, None

        return parent, headings



def create_hierarchy(soup, parent, headings):
    new_tags = []
    for header in headings:
        new_tag = soup.new_tag("div")
        start = False
        lst = list(parent.children)
        for node in lst:
            try:
                if type(node) == bs4.element.NavigableString:
                    if start:
                        new_tag.append(node.extract())

                elif ( (node.name==header.name and repr(node.attrs) == repr(header.attrs))\
                        or node.findChild(header.name, attrs=header.attrs) ):
                    #print "###%s###%s"%(header, node)
                    if start:
                        start = False
                        break
                    else:
                        new_tag.append(node.extract())
                        start = True
                else:
                    if start:
                        new_tag.append(node.extract())
            except Exception,e:
                pass

        new_tags.append(new_tag)

    for tag in new_tags:
        parent.append(tag)

def print_term_counts_per_paragraph(url, sections):
    global displayfilewriter
    
    row_str = "<tr><td>%s</td>"%url

    terms = ["collect", "use", "shar", "stor", "retain", "retention", "provid", "receiv", "disclos", "using"]
    for section in sections:
        
        text = section.replace("\n", " ")
        if len(text) < 30:
            continue
        freq = ["%s:%d"%(term, text.lower().count(term)) for term in terms]
        row_str = row_str + "<td><table><tr><td>%s</td></tr><tr><td><b>%s</b></td></tr></table></td>"%(text.strip(), ','.join(freq))
                 
    row_str = row_str + "</tr>"
    displayfilewriter.write(row_str.encode("utf-8"))


#chunker code

import re
import nltk
from nltk.tag.stanford import POSTagger
from nltk.tokenize import word_tokenize, sent_tokenize
from parser import Parser

tag_patterns = [
    (r'[,;]', 'COMMA'),
    (r'includ(e|es|ing)|such', 'L'),
    (r'information|data', 'D'),
    (r'as', 'AS'),
    (r':', 'COLON'),
    (r'\w', 'ANY'),
    (r'[\(\{\[]', 'OB'),
    (r'[\)\}\]]', 'CB')
]

grammar = r'''
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

#PT = POSTagger('/usr/share/stanford-postagger/models/english-left3words-distsim.tagger',\
#                    '/usr/share/stanford-postagger/stanford-postagger.jar')
PT = POSTagger('/usr/share/stanford-postagger/models/english-bidirectional-distsim.tagger',\
                    '/usr/share/stanford-postagger/stanford-postagger.jar')

def get_nodes(tree):
    ret = []
    for node in tree:
        if type(node) == nltk.Tree:
            ret.extend(get_leaves(node))
        else:
            ret.append(node)
    return ret

def get_data_chunks(tree, name="EXAMPLE"):

    examples = []
    for child in tree:
        if type(child) == nltk.Tree and child.node == name:
            if name == "EXAMPLE":
                examples.extend(get_data_chunks(child, "EX"))
            for c in child:
                if type(c) == nltk.Tree:
                    if c.node == "NP":
                        examples.append(c.leaves())
    return examples

def cleanup_word(word):
    if word[-1] in ['.', '!', '"', "'", "?", ")"]:
        word = word[:-1]

    return word.lower()

def extract_information_types(paragraph):

    data = set([])

    words = word_tokenize(paragraph)
    pos_tagged_tokens = PT.tag(words)

    regexp_tagger = nltk.RegexpTagger(tag_patterns, backoff=nltk.DefaultTagger('ANY'))
    tagged_tokens = regexp_tagger.tag(words)
    
    for i, tag in enumerate(tagged_tokens):
        if tag[1] != "ANY":
            pos_tagged_tokens[i] = tag

    rd_parser = nltk.RegexpParser(grammar)
    tree = rd_parser.parse(pos_tagged_tokens)

    print tree
    examples = get_data_chunks(tree, "EXAMPLE")

    for ex in examples:
        s = ""
        for item in ex:
            s = "%s %s"%(s, item[0])
        s = s[1:]
        data.add(cleanup_word(s).lower())
    return data

#util function to iterate through sections blobs and extract information types from each section
def get_information_types(sections):
    rset = set([])
    for section in sections:
        s = section.replace("<br>", "\n")
        #s = s.replace("\n", " ")
        s = s.encode("utf-8")
        iset = extract_information_types(s)
        rset = rset.union(iset)
    return rset


if __name__=='__main__':

    sents = [
            "We collect information that personally identifies you, such as your name, mailing address, e-mail address, phone number (including your cell phone number), credit card numbers, gender, occupation, personal interests and your child's date of birth, only if you choose to share such information with us",
    ]

    for sent in sents:
        print sent.encode("utf-8")
        print extract_information_types(sent.encode("utf-8"))
