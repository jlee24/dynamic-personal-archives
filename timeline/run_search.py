from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
import sys, os, subprocess, operator, argparse
from gensim import corpora, models, utils, similarities
import numpy  # for arrays, array broadcasting etc.
import numbers
import math
import pprint

my_dictionary = corpora.Dictionary.load('static/data/my_dictionary.dict')
my_corpus = corpora.MmCorpus('static/data/my_corpus.mm')
lsi = models.LsiModel(my_corpus, id2word=my_dictionary, num_topics=2)

tokenizer = RegexpTokenizer(r'[a-zA-Z]+\'[a-zA-Z]+|[a-zA-Z]+')
en_stop = get_stop_words('en') # create English stop words list
stop_words = open('./stop_words.txt', 'r').readlines()
for word in stop_words:
	en_stop.append(word.rstrip('\r\n'))
p_stemmer = PorterStemmer()

def clean_text(raw):
	raw = raw.lower()
	raw = "".join(c for c in raw if c not in ('!','.',':',';',"?",'"',','))
	# raw = unicode(raw, errors='replace')
	tokens = tokenizer.tokenize(raw)
	stopped_tokens = [i for i in tokens if not i in en_stop]
	stemmed_tokens = [p_stemmer.stem(i) for i in stopped_tokens if i != 'nls']
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
	print(sims)
	return sims

# def get_related_works(query):
# 	mutual_info_scores = []
# 	query = clean_text(query)[0]
# 	docs = []
# 	# docs[1].count("word")
# 	# word count of docs[1] = len(docs[1])
# 	# total num words = sum([len(x) for x in docs])

# 	for doc in os.listdir('../nlp_testing/docs'):
# 		doc_location = '../nlp_testing/docs/' + doc
# 		file = open(doc_location, 'r')
# 		words = clean_text(file.read())
# 		docs.append(words)
	
# 	total_num_docs = len(docs)

# 	for doc in docs:
# 		doc_select = doc
# 		mutual_info = 0

# 		# X = event that query appears in doc
# 		# Y = event that d is doc
	
# 		# P(X=0,Y=0)log_2(P(X=0,Y=0)/(P(X=0)P(Y=0)))	
# 		# P(X=1,Y=0)log_2(P(X=1,Y=0)/(P(X=1)P(Y=0)))
# 		# P(X=0,Y=1)log_2(P(X=0,Y=1)/(P(X=0)P(Y=1)))
# 		# P(X=1,Y=1)log_2(P(X=1,Y=1)/(P(X=1)P(Y=1)))

# 		PY_0 = float(total_num_docs-1)/total_num_docs
# 		PY_1 = float(1)/total_num_docs

# 		PX_0 = 0
# 		PX_1 = 0

# 		PX_0Y_0 = 0
# 		PX_1Y_0 = 0
# 		PX_0Y_1 = 0
# 		PX_1Y_1 = 0

# 		for d in docs:
# 			if d != doc_select:
# 				if query not in d:
# 					PX_0 += float(1)/total_num_docs
# 					PX_0Y_0 += float(1)/total_num_docs
# 				else:
# 					PX_1 += float(1)/total_num_docs
# 					PX_1Y_0 += float(1)/total_num_docs
# 			else:
# 				if query not in d:
# 					PX_0 += float(1)/total_num_docs
# 					PX_0Y_1 += float(1)/total_num_docs
# 				else:
# 					PX_1 += float(1)/total_num_docs
# 					PX_1Y_1 += float(1)/total_num_docs
		
# 		mutual_info = mutual_info + PX_0Y_0*math.log((PX_0Y_0/(PX_0*PY_0)), 2) if PX_0Y_0 != 0 else mutual_info
# 		mutual_info = mutual_info + PX_1Y_0*math.log((PX_1Y_0/(PX_1*PY_0)), 2) if PX_1Y_0 != 0 else mutual_info
# 		mutual_info = mutual_info + PX_0Y_1*math.log((PX_0Y_1/(PX_0*PY_1)), 2) if PX_0Y_1 != 0 else mutual_info
# 		mutual_info = mutual_info + PX_1Y_1*math.log((PX_1Y_1/(PX_1*PY_1)), 2) if PX_1Y_1 != 0 else mutual_info

# 		mutual_info_scores.append(mutual_info)

# 	print(mutual_info_scores)

# get_related_works("mouse")
