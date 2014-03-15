
import os, sys
import urllib2
from fetcher import PrivacyURLChecker
from config import LOT_OF_URLS as URLS

def main():
    c = PrivacyURLChecker("http://www.wrestlinginc.com/wi/pages/privacy-policy.shtml")
    if c.check():
        print "privacy url"
    else:
        print "not a privacy url"
    return 

    cnt = 0
    for url in URLS:
        c = PrivacyURLChecker(url)
        if c.check():
            print url
            cnt = cnt + 1

    print "%d out of %d are valid"%(cnt, len(URLS))


if __name__=='__main__':
    main()
