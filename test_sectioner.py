#!/usr/bin/env python

import os,sys
import config
from fetcher import URLIterator
from bs4 import BeautifulSoup
from sectioner import HeadingBasedSectioner
import utils
import logging
import urlparse

class Tester:

    def __init__(self, output_dir, urls):
        self.urls = urls
        self.odir = output_dir

    def test_sectioner(self):
        it = URLIterator(self.urls)
        for url, soup in it.generate_soup():
            logging.info("sectioning %s"%(url))
            s = HeadingBasedSectioner(url, soup)
            headings, sections = s.sectionize()
            if headings:
                self.write_sections(url, headings, sections)

    def write_sections(self, url, headings, sections):

        website = urlparse.urlparse(url).netloc
        if website.startswith("www"):
            website = website.split(".")[1]
        else:
            website = website.split(".")[0]

        f = open("%s/%s.html"%(self.odir, website), "w")
        f.write('''
        <html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>
        <body><h2>%s(%s)</h2>
        '''%(website, url))
       
        for i, heading in enumerate(headings):
            f.write("<div>")
            f.write("<b>%s</b><br>"%heading.encode("utf-8"))
            f.write(sections[i].encode("utf-8"))
            f.write("</div><br><br>")

        f.write("</body></html>")
        f.close()

def main():
    config.create_output_dir()
    utils.loginit("test_sectioner.log")
    urls = config.URLS

    logging.info("START")
    t = Tester("output", urls)
    t.test_sectioner()
    logging.info("END")

if __name__=='__main__':
    main()
