from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
import sys, os, subprocess, operator
from gensim import corpora, models, utils
import DtmModel as DtmModel
import numpy  # for arrays, array broadcasting etc.
import numbers
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

save_memory = True # if flag on, stores corpus in memory; else, streams docs one at a time 

doc_folder = sys.argv[1] # where corpus files are located
dict_name = 'my_dictionary.dict'
texts = [] # all the cleaned, tokenized documents
my_corpus = []

tokenizer = RegexpTokenizer(r'[a-zA-Z]+\'[a-zA-Z]+|[a-zA-Z]+')
en_stop = get_stop_words('en') # create English stop words list
stop_words = open('./stop_words.txt', 'r').readlines()
for word in stop_words:
	en_stop.append(word.rstrip('\r\n'))
p_stemmer = PorterStemmer()

def clean_text(doc_location):
	command = "sumy luhn --file=" + doc_location # summarize document string
	raw = subprocess.check_output(command, shell=True)
	raw = unicode(raw, errors='replace')
	raw = raw.lower()
	tokens = tokenizer.tokenize(raw)
	stopped_tokens = [i for i in tokens if not i in en_stop]
	stemmed_tokens = [p_stemmer.stem(i) for i in stopped_tokens]
	return stemmed_tokens

def create_dictionary():
	for doc in os.listdir(doc_folder):
		doc_location = doc_folder + '/' + doc
		texts.append(clean_text(doc_location))
	my_dictionary = corpora.Dictionary(texts)
	my_dictionary.save('./my_dictionary.dict')
	return my_dictionary

class MyCorpus(object):
	def __init__(self, dictionary):
		self.dictionary = dictionary
	def __iter__(self):
		for doc in os.listdir(doc_folder):
			doc_location = doc_folder + '/' + doc
			print('streamed a doc')
			yield self.dictionary.doc2bow(clean_text(doc_location))

def generate_dtm(num_topics, my_timeslices):
	if save_memory:
		# must create dictionary every time to fill up texts array, which will be used to create corpus
		my_dictionary = create_dictionary()
		my_corpus = [my_dictionary.doc2bow(text) for text in texts]
		dtmmodel = models.wrappers.DtmModel('./dtm-win64.exe', my_corpus, my_timeslices, num_topics=num_topics, id2word=my_dictionary, prefix='./dtm-')
		# for doc in corpus_dtm:
		#     doc.sort(key=operator.itemgetter(1), reverse=True)
		#     print(count)
		#     count += 1
		#     for i in range(0,10):
		#         word = doc[i]
		#         print(dictionary[word[0]], word[1])
		
	else: 
		names = os.listdir(os.getcwd())
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
		names = os.listdir(os.getcwd())
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

def generate_tfidf():
	my_dictionary = create_dictionary()
	# convert tokenized documents into a document-term matrix
	my_corpus = [my_dictionary.doc2bow(text) for text in texts]
	tfidf = models.tfidfmodel.TfidfModel(my_corpus)
	corpus_tfidf = tfidf[my_corpus]
	count = 0
	for doc in corpus_tfidf:
		doc.sort(key=operator.itemgetter(1), reverse=True)
		print(count)
		count += 1
		for i in range(0,10):
			word = doc[i]
			print(my_dictionary[word[0]], word[1])


def main():
	if sys.argv[2] == 'dtm':
		my_timeslices = [6, 5, 5, 6, 4]
		num_slices = len(my_timeslices)
		num_topics = 7
		num_words = 15

		dtmmodel = generate_dtm(num_topics, my_timeslices)
		corpus_dtm = dtmmodel[my_corpus]
		print(corpus_dtm)

		# topics = dtmmodel.show_topics(topics=num_topics, times=num_slices, topn=num_words, log=False, formatted=True)
		# for i in range(0, num_slices):
		# 	print('Time_Slice ' + str(i))
		# 	for j in range(0, num_topics):
		# 		print('Topic ' + str(j))
		# 		print(topics[i*j])
		# 	print('\n')

	elif sys.argv[2] == 'lda':
		ldamodel = generate_lda()
		for topic in ldamodel.print_topics(num_topics=5, num_words=15):
			print(topic)
			print('\n')

	else:
		print('generating tfidf')
		generate_tfidf()

if __name__ == "__main__":
	main()