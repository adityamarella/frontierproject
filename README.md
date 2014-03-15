
@Author: Aditya Marella
@Date: 03-14-2014

This code was developed and tested on Ubuntu 13.10

** Software Package Requirements

    - NLTK (python)
    - Jype (python)
    - Standford Tagger, Parser (Java)

-----------------------------------

** Files
    - config.py: this file contains various configuration settings used by different scripts for example the output directories and stanford parser home directory path are configure in this file
    - fetcher.py: wrapper to handle the privacy URL GET requests 
    - sectioner.py: contains sectioning part of the code, mainly the headings are used to sections privacy policies
    - classify.py: contains code to classify the sections into collection, sharing, retention, etc
    - information_type_extractor.py: contains code to extract information types from the sections produced by sectioner
    - noun_phrase_extractor.py: extracts noun phrases as a python set
    - noun_phrase_marker.py: marks noun phrases in the privacy policy (makes them clickable)
    - stanford_utils.py: jype interface the JAVA stanford tools  
    - utils.py: util functions
    - evaluate.py: has code to calculate precision and recall against the manually annotated datasets(Travis, Fei datasets)

-----------------------------------

** Running the code

All the scripts have two modes of operation viz. single privacy url and multiple privacy urls

To demo the scripts, I will be using Amazon's privacy policy. This can be changed any other privacy policy url. If no argument is given to this script it will start running on the list of URLS from config.py. Many privacy policies are not supported, if they are not supported test_sectioner.py script will output an error in the log file.

#> python test_sectioner.py "http://www.amazon.com/gp/help/customer/display.html/ref=footer_privacy?ie=UTF8&nodeId=468496"

#> python classify.py "http://www.amazon.com/gp/help/customer/display.html/ref=footer_privacy?ie=UTF8&nodeId=468496" > amazon.html


#> python information_type_extractor.py "http://www.amazon.com/gp/help/customer/display.html/ref=footer_privacy?ie=UTF8&nodeId=468496" > info_type.out

output for this script is html files with marked sections
#> python noun_phrase_marker.py "http://www.amazon.com/gp/help/customer/display.html/ref=footer_privacy?ie=UTF8&nodeId=468496"

this script was used for computing noun phrase frequencies in the privacy policies
#> python noun_phrase_extractor.py np.out "http://www.amazon.com/gp/help/customer/display.html/ref=footer_privacy?ie=UTF8&nodeId=468496"


