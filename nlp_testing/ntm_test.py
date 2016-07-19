from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer

import sys
import os
import subprocess

import gensim
from gensim import corpora, models
import gensim.models.wrappers as wrappers

# where corpus files are located
doc_folder = sys.argv[1]

def clean_text(doc_location):
	tokenizer = RegexpTokenizer(r'[a-zA-Z]+\'[a-zA-Z]+|[a-zA-Z]+')
	# create English stop words list
	en_stop = get_stop_words('en')
	stop_words = open('./stop_words.txt', 'r').readlines()
	for word in stop_words:
		en_stop.append(word.rstrip('\r\n'))
	# Create p_stemmer of class PorterStemmer
	p_stemmer = PorterStemmer()

	# summarize, clean, and tokenize document string
	command = "sumy luhn --file=" + doc_location
	raw = subprocess.check_output(command, shell=True)
	raw = unicode(raw, errors='replace')
	raw = raw.lower()
	tokens = tokenizer.tokenize(raw)
	# remove stop words from tokens
	stopped_tokens = [i for i in tokens if not i in en_stop]
	# stem tokens
	stemmed_tokens = [p_stemmer.stem(i) for i in stopped_tokens]
	return stemmed_tokens

def create_dictionary():
	# list for tokenized documents in loop
	texts = []
	for doc in os.listdir(doc_folder):
				doc_location = doc_folder + '/' + doc
				texts.append(clean_text(doc_location))
	my_dictionary = corpora.Dictionary(texts)
	my_dictionary.save('./my_dictionary.dict')
	return my_dictionary

# stream one document at a time so that corpus does not need to be stored in memory
class MyCorpus(object):
	 def __iter__(self):
		for doc in os.listdir(doc_folder):
			doc_location = doc_folder + '/' + doc
			yield my_dictionary.doc2bow(clean_text(doc_location))

def generate_dtm():
	dtmmodel = gensim.models.wrappers.DtmModel
	my_dictionary = corpora.Dictionary

	for i in os.listdir(os.path.join(os.getcwd(), 'dtm')):
		if i.endswith('.dict'):
			my_dictionary = corpora.Dictionary.load(i)

		if i is 'dtm.model':
			dtmmodel = gensim.models.wrappers.DtmModel.load(i)
		else:
			my_dictionary = create_dictionary()
			my_corpus = MyCorpus()
			my_timeslices = [6, 5, 5, 6, 4]
			dtmmodel = gensim.models.wrappers.DtmModel('./dtm-win64.exe', my_corpus, my_timeslices, num_topics=5, id2word=my_dictionary, prefix='./dtm/dtm-')
			dtmmodel.save('./dtm/dtm.model')
	
	return dtmmodel

def generate_lda():
	ldamodel = gensim.models.LdaModel
	my_dictionary = corpora.Dictionary
	for i in os.listdir(os.getcwd()):
		if os.path.isdir(os.path.join(os.getcwd(), 'lda')):
			if i.endswith('.dict'):
				my_dictionary = corpora.Dictionary.load(i)
			if i is 'lda.model':
				ldamodel = gensim.models.LdaModel.load(i)
		else:
			my_dictionary = create_dictionary()
			my_corpus = MyCorpus()
			my_timeslices = [6, 5, 5, 6, 4]
			ldamodel = gensim.models.LdaModel('./dtm-win64.exe', my_corpus, my_timeslices, num_topics=5, id2word=my_dictionary, prefix='./lda/lda-')
			ldamodel.save('./lda/lda.model')
	return ldamodel


def main():
	if sys.argv[2] is 'dtm':
		dtmmodel = generate_dtm()
		dtmmodel.show_topics(num_topics=5, times=5, num_words=15, log=False, formatted=True)
	else:
		ldamodel = generate_lda()
		ldamodel.show_topics(num_topics=5, num_words=15, log=False, formatted=True)

if __name__ == "__main__":
	main()