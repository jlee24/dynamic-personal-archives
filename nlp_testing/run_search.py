import sys, os, subprocess, operator, argparse
from gensim import corpora, models, utils, similarities
import numpy  # for arrays, array broadcasting etc.
import numbers

import logging
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('query', type=str)
args = parser.parse_args()
doc = args.query

my_dictionary = corpora.Dictionary.load('tmp/my_dictionary.dict')
my_corpus = corpora.MmCorpus('tmp/my_corpus.mm')
lsi = models.LsiModel(my_corpus, id2word=my_dictionary, num_topics=2)

vec_bow = my_dictionary.doc2bow(doc.lower().split())
vec_lsi = lsi[vec_bow] # convert the query to LSI space

# only appropriate when the whole set of vectors fits into memory
index = similarities.MatrixSimilarity(lsi[my_corpus]) # transform corpus to LSI space and index it
# index.save('/tmp/lsi.index')
# index = similarities.MatrixSimilarity.load('/tmp/lsi.index')

sims = index[vec_lsi] # perform a similarity query against the corpus
# print(list(enumerate(sims))) # print (document_number, document_similarity) 2-tuples
sims = sorted(enumerate(sims), key=lambda item: -item[1])
print(sims)