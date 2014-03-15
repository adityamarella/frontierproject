#!/usr/bin/env python


from noun_phrase_extractor import process 
from multiprocessing import Pool
from config import LOT_OF_URLS as URLS

BATCH_SIZE = 100

def logresult(a):
    print a

def main():

    try:
        pool_size  = int(sys.argv[1])
    except:
        pool_size = 3

    p = Pool(processes = pool_size)

    args = []
    num_batches = 1 + len(URLS)/BATCH_SIZE
    for i in xrange(num_batches):
        end = min((i+1)*BATCH_SIZE, len(URLS))
        result = p.apply_async(process, args=[(URLS[i*BATCH_SIZE:end], "out_%d"%(i))], callback=logresult)

    p.close()
    p.join()

if __name__=='__main__':
    main()
