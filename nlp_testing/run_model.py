from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
import sys
import os
import subprocess
from gensim import corpora, models
from pprint import pprint

import logging
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# if flag on, stores corpus in memory; else, streams docs one at a time 
save_memory = True

doc_folder = sys.argv[1] # where corpus files are located
dict_name = 'my_dictionary.dict'
# ldamodel_name = 'lda.model'
# dtmmodel_name = 'dtm.model'
texts = [] # all the cleaned, tokenized documents

tokenizer = RegexpTokenizer(r'[a-zA-Z]+\'[a-zA-Z]+|[a-zA-Z]+')
# create English stop words list
en_stop = get_stop_words('en')
stop_words = open('./stop_words.txt', 'r').readlines()
for word in stop_words:
	en_stop.append(word.rstrip('\r\n'))
# create p_stemmer of class PorterStemmer
p_stemmer = PorterStemmer()

def clean_text(doc_location):
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
	for doc in os.listdir(doc_folder):
		doc_location = doc_folder + '/' + doc
		texts.append(clean_text(doc_location))
	my_dictionary = corpora.Dictionary(texts)
	my_dictionary.save('./my_dictionary.dict')
	return my_dictionary

# stream one document at a time so that corpus does not need to be stored in memory
class MyCorpus(object):
	def __init__(self, dictionary):
		self.dictionary = dictionary
	def __iter__(self):
		for doc in os.listdir(doc_folder):
			doc_location = doc_folder + '/' + doc
			print('streamed a doc')
			yield self.dictionary.doc2bow(clean_text(doc_location))

def generate_dtm():
	if save_memory:
		# must create dictionary every time to fill up texts array, which will be used to create corpus
		my_dictionary = create_dictionary()
		my_corpus = [my_dictionary.doc2bow(text) for text in texts]
		my_timeslices = [6, 5, 5, 6, 4]
		dtmmodel = models.wrappers.DtmModel('./dtm-win64.exe', my_corpus, my_timeslices, num_topics=5, id2word=my_dictionary, prefix='./dtm-')
		
	else: 
		names = os.listdir(os.getcwd())
		# if dtmmodel_name in names:
		# 	print('model already exists')
		# 	dtmmodel = models.wrappers.DtmModel.load(dtmmodel_name)
		# else:
		my_dictionary = corpora.Dictionary
		if dict_name in names:
			my_dictionary = corpora.Dictionary.load(dict_name)
			print('loaded dict')
		else:
			my_dictionary = create_dictionary()
			print('created dict')
		my_corpus = MyCorpus(my_dictionary)
		print('starting to generate model')
		my_timeslices = [6, 5, 5, 6, 4]
		dtmmodel = models.wrappers.DtmModel('./dtm-win64.exe', my_corpus, my_timeslices, num_topics=5, id2word=my_dictionary, prefix='./dtm-')
		dtmmodel.save('./dtm.model')

	return dtmmodel
		
def generate_lda():
	if save_memory:
		my_dictionary = create_dictionary()
		my_corpus = [my_dictionary.doc2bow(text) for text in texts]
		ldamodel = models.ldamodel.LdaModel(my_corpus, num_topics=5, id2word=my_dictionary, passes=15)
	else: 
		# the method below does not store the corpus in memory but takes much longer 
		names = os.listdir(os.getcwd())
		# if ldamodel_name not in names:
		# 	print('model already exists')
		# 	return models.ldamodel.LdaModel.load(ldamodel_name)
		# else:
		my_dictionary = corpora.Dictionary
		if dict_name in names:
			my_dictionary = corpora.Dictionary.load(dict_name)
			print('loaded dict')
		else:
			my_dictionary = create_dictionary()
			print('created dict')
		my_corpus = MyCorpus(my_dictionary)
		print('starting to generate model')
		ldamodel = models.ldamodel.LdaModel(my_corpus, num_topics=5, id2word=my_dictionary, passes=10)
		ldamodel.save('./lda.model')
	return ldamodel

def main():
	if sys.argv[2] == 'dtm':
		dtmmodel = generate_dtm()

		num_slices = 5
		num_topics = 5

		topics = dtmmodel.show_topics(topics=num_topics, times=num_slices, topn=15, log=False, formatted=True)
		for i in range(0, num_slices):
			print(i)
			for j in range(0, num_topics):
				print(j)
				print(topics[i*j])
			print('\n')

	else:
		ldamodel = generate_lda()
		for topic in ldamodel.print_topics(num_topics=5, num_words=15):
			print(topic)
			print('\n')

if __name__ == "__main__":
	main()