from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
from gensim import corpora, models
import gensim
import sys
import os
import subprocess
import operator

tokenizer = RegexpTokenizer(r'[a-zA-Z]+\'[a-zA-Z]+|[a-zA-Z]+')
# create English stop words list
en_stop = get_stop_words('en')
stop_words = open('./stop_words.txt', 'r').readlines()
for word in stop_words:
	en_stop.append(word.rstrip('\r\n'))

# Create p_stemmer of class PorterStemmer
p_stemmer = PorterStemmer()

# list for tokenized documents in loop
texts = []

# get the folder
doc_folder = sys.argv[1]
doc_names = []

# loop through document list
for doc in os.listdir(doc_folder):
    # clean and tokenize document string

    doc_location = doc_folder + '/' + doc

    #raw = open(doc_location, 'r').read()
    #raw = unicode(raw, errors='replace')

    command = "sumy luhn --file=" + doc_location
    raw = subprocess.check_output(command, shell=True)
    raw = unicode(raw, errors='replace')
    raw = raw.lower()
    tokens = tokenizer.tokenize(raw)

    # remove stop words from tokens
    stopped_tokens = [i for i in tokens if not i in en_stop]
    
    # stem tokens
    stemmed_tokens = [p_stemmer.stem(i) for i in stopped_tokens if i != 'nls']
    
    # add tokens to list
    texts.append(stemmed_tokens)

    doc_names.append(doc)

# turn our tokenized documents into a id <-> term dictionary
dictionary = corpora.Dictionary(texts)

# convert tokenized documents into a document-term matrix
corpus = [dictionary.doc2bow(text) for text in texts]

tfidf = gensim.models.tfidfmodel.TfidfModel(corpus)
corpus_tfidf = tfidf[corpus]

count = 0
for doc in corpus_tfidf:
    doc.sort(key=operator.itemgetter(1), reverse=True)
    print(count)
    count += 1
    for i in range(0,10):
        word = doc[i]
        print(dictionary[word[0]], word[1])
    # print doc
