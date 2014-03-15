#!/usr/bin/env python

import config
import re
import logging
from utils import get_text_string

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

HEADING_START = "@@headingstart@@"
HEADING_END = "@@headingend@@"

#Base class Sectioner with constructor and sectionize function
class Sectioner:

    PATTERN_LABELS = [
        CHOICES_PATTERN,
        SECURITY_PATTERN,
        ACCESS_UPDATE_PATTERN,
        SHARE_PATTERN,
        USE_PATTERN,
        COLLECT_PATTERN,
    ]

    def __init__(self, url, soup):
        self.url = url
        self.soup = soup

    def sectionize(self):
        return None, None


class HeadingBasedSectioner(Sectioner):

    __MIN_SECTIONS = 4

    def sectionize(self):
        sections = []
         
        if not self.soup:
            logging.error("soup not generated correctly")
            return None, None

        headings = self.find_headings_from_bold_tags()
        if not headings:
            logging.error("bold tags not found")
            return None, None

        #find least common ancestor
        parent, headings = self.find_least_common_ancestor(headings)
        if not parent:
            logging.error("ambiguous common parent")
            return None, None

        #check if any of the headings match the PATTERNS
        headings = self.validate_headings(headings)
        if not headings:
            logging.error("invalid headings")
            return None, None

        #expecting atleast 4 sections
        #if not either the headings are wrong or something else is wrong
        if len(headings) < HeadingBasedSectioner.__MIN_SECTIONS:
            logging.error("Something went wrong? Expecting atleast 4 headings")
            return None, None

        #add seperator strings around tag to ease lookup
        sections = self.split_into_sections_using_headings(headings, parent)
        if len(sections) != len(headings):
            logging.error("Error num sections != num headings")
            return None, None

        for section in sections:
            if len(section.strip())!=0:
                break
        else:
            #all sections have zero length;
            #which means we found the the headings in TOC
            #try to find the next occurance of the same heading
            parent, headings = self.find_next_occurance_of_headings(headings)
            if not parent:
                logging.error("ambiguous common parent - 2")
                return None, None

            #add seperator strings around tag to ease lookup
            sections = self.split_into_sections_using_headings(headings, parent)
            if len(sections) != len(headings):
                logging.error("Error num sections != num headings")
                return None, None

        logging.info("Sectioning complete. %d sections identified"%len(sections))

        return headings, sections

    def find_next_occurance_of_headings(self, headings):
        '''
        This function is written to handle policies with TOC and headings in the same font eg.
        http://www.sears.com/csprivacy/nb-100000000022508

        This function is called only when main line(first try) fails to find headings.
        Here we try to find the second occurance of bold tags with same tag structure.
        '''

        hs = []
        self.add_h3_tags_to_text_tags_with_bold_font()
        bold_nodes = self.soup.findAll(config.BOLD_TAGS)
        if not bold_nodes:
            logging.error("bold tags not found - 2")
            return None, None
        
        for node in bold_nodes:
            text = node.get_text().lower()
            if node.findChild(config.BOLD_TAGS):
                continue
            hs.append(node)

        ret = []
        text_headings = [get_text_string(heading).strip().lower() for heading in headings]
        headings_dict = {}
        for h in hs:
            tt = get_text_string(h).strip().lower()
            if tt in text_headings:
                if not headings_dict.get(tt, False):
                    headings_dict[tt] = True
                else:
                    ret.append(h)

        parent, hs = self.find_least_common_ancestor(ret, 0)
        #ignore the hs return by least common ancestor because we already 
        #have the correct list of headings
        return parent, ret

    def split_into_sections_using_headings(self, headings, parent):
         
        for i, heading in enumerate(headings):
            n1 = self.soup.new_string(HEADING_START)
            heading.insert_before(n1)
            n1 = self.soup.new_string(HEADING_END)
            heading.insert_after(n1)

        text = parent.get_text()
        sections = text.split(HEADING_START)[1:]
        sections = [section.split(HEADING_END)[1] if len(section.split(HEADING_END))>1 else section for section in sections]

        nodes = self.soup.findAll([HEADING_START, HEADING_END])
        for node in nodes:
            node.extract()

        return sections

    def add_h3_tags_to_text_tags_with_bold_font(self):
        tags = self.soup.findAll(config.TEXT_TAGS)
        for tag in tags:
            style = tag.attrs.get("style", "")
            if style.find("bold")!=-1:
                new_tag = self.soup.new_tag("h3")
                try:
                    tag.string.wrap(new_tag)
                except:
                    pass

    def find_least_common_ancestor(self, headings, target = 0):
        parent = headings[target].findParent()
        tag_name = headings[target].name
        attrs = headings[target].attrs
        while True:
            children = parent.findChildren(tag_name, attrs = attrs)
            if len(children) > HeadingBasedSectioner.__MIN_SECTIONS:
                headings = children
                break
            parent = parent.findParent()
            if not parent:
                return None, None

        return parent, headings

    def validate_headings(self, headings):
        for heading in headings:
            matched = False
            for pattern in Sectioner.PATTERN_LABELS:
                tt = heading.get_text().lower()
                if pattern.search(tt):
                    matched = True
            if matched:
                break
        else:
            #no match in the headings, so most probably we got the wrong headings
            headings = None

        return headings

    def find_headings_from_bold_tags(self):
        headings = []
        self.add_h3_tags_to_text_tags_with_bold_font()

        #find all the node with bold font and among them select
        #those with config.BOLD_TEXT_PATTERN
        bold_nodes = self.soup.findAll(config.BOLD_TAGS)
        for node in bold_nodes:
            text = node.get_text().lower()
            if node.findChild(config.BOLD_TAGS):
                continue
            if config.BOLD_TEXT_PATTERN.search(text):
                headings.append(node)

        if len(headings)==0:
            return None

        return headings

def main():
    pass
