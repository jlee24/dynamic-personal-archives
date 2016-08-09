from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
import sys, os, subprocess, operator, argparse
from gensim import corpora, models, utils, similarities
import numpy  # for arrays, array broadcasting etc.
import numbers

my_dictionary = corpora.Dictionary.load('static/data/my_dictionary.dict')
my_corpus = corpora.MmCorpus('static/data/my_corpus.mm')
lsi = models.LsiModel(my_corpus, id2word=my_dictionary, num_topics=2)

tokenizer = RegexpTokenizer(r'[a-zA-Z]+\'[a-zA-Z]+|[a-zA-Z]+')
en_stop = get_stop_words('en') # create English stop words list
stop_words = open('./stop_words.txt', 'r').readlines()
for word in stop_words:
	en_stop.append(word.rstrip('\r\n'))
p_stemmer = PorterStemmer()

def clean_text(query):
	raw = query.lower()
	tokens = tokenizer.tokenize(raw)
	stopped_tokens = [i for i in tokens if not i in en_stop]
	stemmed_tokens = [p_stemmer.stem(i) for i in stopped_tokens]
	return stemmed_tokens

def get_related_works(query):
	vec_bow = my_dictionary.doc2bow(clean_text(query))
	vec_lsi = lsi[vec_bow] # convert the query to LSI space

	# only appropriate when the whole set of vectors fits into memory
	index = similarities.MatrixSimilarity(lsi[my_corpus]) # transform corpus to LSI space and index it
	# index.save('/tmp/lsi.index')
	# index = similarities.MatrixSimilarity.load('/tmp/lsi.index')

	sims = index[vec_lsi] # perform a similarity query against the corpus
	# print(list(enumerate(sims))) # print (document_number, document_similarity) 2-tuples
	sims = sorted(enumerate(sims), key=lambda item: -item[1])
	# print(sims)
	return sims