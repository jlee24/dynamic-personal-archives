from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
import sys, os, subprocess, operator, argparse
from gensim import corpora, models, utils
import numpy  # for arrays, array broadcasting etc.
import numbers

# import logging
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('model')
parser.add_argument('--save_memory', default='False')
parser.add_argument('--regenerate', default='False')
parser.add_argument('--doc_folder', default='docs')
args = parser.parse_args()
model = args.model
save_memory = (args.save_memory == 'True') # if flag off, stores corpus in memory; else, streams docs one at a time 
regenerate = (args.regenerate == 'True')  # if flag off, uses existing data; else, regenerates dict and corpus
doc_folder = str(args.doc_folder)   # where corpus files are located
dict_name = 'my_dictionary.dict'  # name of dictionary file
texts = [] 						  # all the cleaned, tokenized documents

tokenizer = RegexpTokenizer(r'[a-zA-Z]+\'[a-zA-Z]+|[a-zA-Z]+')
en_stop = get_stop_words('en') # create English stop words list
stop_words = open('./stop_words.txt', 'r').readlines()
for word in stop_words:
	en_stop.append(word.rstrip('\r\n'))
p_stemmer = PorterStemmer()

class MyCorpus(object):
	def __init__(self, dictionary):
		self.dictionary = dictionary
	def __iter__(self):
		for doc in os.listdir(doc_folder):
			doc_location = doc_folder + '/' + doc
			print('streamed a doc')
			yield self.dictionary.doc2bow(clean_text(doc_location))

def clean_text(doc_location):
	command = "sumy luhn --file=" + doc_location # summarize document string
	raw = subprocess.check_output(command, shell=True)
	# file = open(doc_location, 'r')
	# raw = file.read()
	raw = unicode(raw, errors='replace')
	raw = raw.lower()
	tokens = tokenizer.tokenize(raw)
	stopped_tokens = [i for i in tokens if not i in en_stop]
	stemmed_tokens = [p_stemmer.stem(i) for i in stopped_tokens]
	return stemmed_tokens

def create_dictionary():
	names = os.listdir('tmp')
	my_dictionary = corpora.Dictionary
	if regenerate==False and dict_name in names:
		my_dictionary = corpora.Dictionary.load('tmp/' + dict_name)
		print('loaded dict')
	else:
		for doc in os.listdir(doc_folder):
			doc_location = doc_folder + '/' + doc
			texts.append(clean_text(doc_location))
		my_dictionary = corpora.Dictionary(texts)
		my_dictionary.save('tmp/' + dict_name)
		print('created new dict')
	return my_dictionary

def create_corpus(my_dictionary):
	if regenerate:
		if save_memory:
			return MyCorpus(my_dictionary)
		else: 
			my_corpus = [my_dictionary.doc2bow(text) for text in texts]
			corpora.MmCorpus.serialize('tmp/my_corpus.mm', my_corpus)
			return my_corpus
	else:
		return corpora.MmCorpus('tmp/my_corpus.mm')

def generate_dim(num_topics, my_timeslices):
	my_dictionary = create_dictionary()
	my_corpus = create_corpus(my_dictionary)
	dimmodel = models.wrappers.DtmModel('./dtm-win64.exe', my_corpus, my_timeslices, model='fixed', num_topics=num_topics, id2word=my_dictionary, prefix='./tmp/dtm-')
	return dimmodel

def generate_dtm(num_topics, my_timeslices):
	my_dictionary = create_dictionary()
	my_corpus = create_corpus(my_dictionary)
	dtmmodel = models.wrappers.DtmModel('./dtm-win64.exe', my_corpus, my_timeslices, num_topics=5, id2word=my_dictionary, prefix='./tmp/dtm-')
	return dtmmodel
		
def generate_lda():
	my_dictionary = create_dictionary()
	my_corpus = create_corpus(my_dictionary)
	ldamodel = models.ldamodel.LdaModel(my_corpus, num_topics=5, id2word=my_dictionary, passes=10)
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
	if sys.argv[1] == 'lda':
		ldamodel = generate_lda()
		for topic in ldamodel.print_topics(num_topics=5, num_words=15):
			print(topic)
			print('\n')

	elif sys.argv[1] == 'dtm':
		my_timeslices = [6, 5, 5, 6, 4]
		num_slices = len(my_timeslices)
		num_topics = 5
		num_words = 15

		dtmmodel = generate_dtm(num_topics, my_timeslices)
		topics = dtmmodel.show_topics(topics=num_topics, times=num_slices, topn=num_words, log=False, formatted=True)
		for i in range(0, num_slices):
			print('Time_Slice ' + str(i))
			for j in range(0, num_topics):
				print('Topic ' + str(j))
				print(topics[i*j])
			print('\n')

	elif sys.argv[1] == 'dim':
		# [-1968, 1968-1984, 1984-1988, 1988-]
		my_timeslices = [4, 5, 7, 9]
		num_slices = len(my_timeslices)
		num_topics = 7
		num_words = 15

		dimmodel = generate_dim(num_topics, my_timeslices)

		# printing out the topics
		topics = dimmodel.show_topics(topics=num_topics, times=num_slices, topn=num_words, log=False, formatted=True)
		# for i in range(0, num_slices):
		# 	print('Time_Slice ' + str(i))
		# 	for j in range(0, num_topics):
		# 		print('Topic ' + str(j))
		# 		print(topics[i*j])
		# 	print('\n')

		# structure: {time_slice: {doc: [influence of each topic]}, topics_from_time_slice: [composition of each topic]}
		dim = {}

		time_slice_count = 0
		docs_count = 0
		for time_slice in dimmodel.influences_time:
			# print("Time_Slice " + str(time_slice_count))
			dim[time_slice_count] = {}
			dim["topics_" + str(time_slice_count)] = []
			# add topics
			for j in range(0, num_topics):
				dim["topics_" + str(time_slice_count)].append(topics[time_slice_count*j])
			# add document influences
			for doc in time_slice:
				# print("Doc " + str(docs_count))
				dim[time_slice_count][docs_count] = []
				topics_count = 0
				for topic in doc:
					# print("Topic " + str(topics_count) + ": " + str(topic))
					dim[time_slice_count][docs_count].append(topic)
					topics_count += 1
				dim[time_slice_count][docs_count] = sorted(dim[time_slice_count][docs_count])
				docs_count += 1
			time_slice_count += 1

		print(dim)

	else:
		generate_tfidf()

if __name__ == "__main__":
	main()