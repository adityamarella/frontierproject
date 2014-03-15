
import os, sys
import urllib2
from bs4 import BeautifulSoup
import config as c
from fetcher import fetch_url
from fetcher import fetch_privacy_url

def extract_privacy_url(url):
    try:
        data = fetch_url(url)
        soup = BeautifulSoup(data)
    except Exception as e:
        return "%s"%(e)

    a_list = soup.findAll("a")
    lst = []
    for node in a_list:
        if node.get_text().lower().find("privacy") != -1:
            lst.append(node)
    if len(lst)==1:
        return lst[0]    
        
    for node in lst:
       if node.get_text().lower().find("policy")!=-1 or\
          node.get_text().lower().find("notice")!=-1 or\
          node.get_text().lower().find("promise")!=-1:
           return node
    return None

def crawl_alexa_category(category):
    URLFORMAT="http://www.alexa.com/topsites/category%s/Top/%s"
    urls = []
    for i in xrange(10,20):
        if i==0:
            url = URLFORMAT%('', category)
        else:
            url = URLFORMAT%(";%d"%i, category)
        try:
            data = fetch_url(url)
            soup = BeautifulSoup(data)
        except:
            continue
        links = soup.findAll("a")
        for link in links:
            if link.has_attr("href"):
                url = link.attrs["href"]
                offset = url.find("/siteinfo/")
                if offset!=-1:
                    urls.append(url[len("/siteinfo/"):])
        
    urls = ["http://%s"%u for u in urls]
    return urls

def get_privacy_url(websites):

    privacy_urls = []
    cnt = len(websites)
    for i,url in enumerate(websites):
        ourl = url
        try:
            if url.find("http") == -1:
                url= "http://www.%s"%url
            u = extract_privacy_url(url)
            if u and type(u) is not str and u.has_attr("href"):
                u = u.attrs["href"]

            if u and u.find("http")==-1:
                privacy_url = "%s%s"%(url, u)
            else:
                privacy_url = "%s"%(u)

            sys.stderr.write( ("#%d of %d#%s:\n"%(i+1, cnt, privacy_url)).encode("utf-8"))
        except:
            pass
        privacy_urls.append(privacy_url)

    for url in privacy_urls:
        try:
            data = fetch_privacy_url(url)
        except Exception as e:
            continue
        if data:
            print url.encode("utf-8")
    
    sys.stdin.flush()
    

def main(category=None):
    
    if not category: 
        if len(sys.argv) !=2:
            print """Usage: python privacy_url_extractor.py <Alexa Category>\nAlexa categories are listed here http://www.alexa.com/topsites/category. For eg: you could say python privacy_url_extractor.py News"""
            return
        else:
            category = sys.argv[1]

    websites = crawl_alexa_category(category)

    get_privacy_url(websites) 

def loop_over_websites():

    websites = []
    fp = open(sys.argv[1])
    for line in fp:
        url = line.strip().split(",")[1]
        websites.append(url)

    get_privacy_url(websites[34000:100000])

if __name__=='__main__':
    #for c in ['Arts', 'Games', 'Science', 'Home']:
    #    main(c)
    #main(None)
    loop_over_websites()
