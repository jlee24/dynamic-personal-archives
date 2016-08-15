from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
import sys, os, subprocess, operator, argparse
from gensim import corpora, models, utils
import numpy  # for arrays, array broadcasting etc.
import numbers
import json
import re

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
	# command = "sumy luhn --file=" + doc_location # summarize document string
	# raw = subprocess.check_output(command, shell=True)
	file = open(doc_location, 'r')
	raw = file.read()
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
	if model == 'lda':
		ldamodel = generate_lda()
		for topic in ldamodel.print_topics(num_topics=5, num_words=15):
			print(topic)
			print('\n')

	elif model == 'dtm':
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

	elif model == 'dim':
		# [-1968, 1968-1984, 1984-1988, 1988-]
		my_timeslices = [0, 8, 11, 15, 0]
		num_slices = len(my_timeslices)
		num_topics = 10
		num_words = 5

		# dimmodel = generate_dim(num_topics, my_timeslices)
		# dimmodel.save('tmp/dimmodel2.model')
		# dimmodel = models.wrappers.DtmModel.load('tmp/dimmodel.model')
		dimmodel = models.wrappers.DtmModel.load('tmp/dimmodel1.model')

		# structure: {time_slice: {doc: [influence of each topic]}, topics_from_time_slice: [composition of each topic]}
		dim_influences = {}

		topics_per_slice = []

		# printing out the topics
		topics = dimmodel.show_topics(topics=num_topics, times=num_slices, topn=num_words, log=False, formatted=True)
		for i in range(0, num_slices):
			topics_slice = []
			for j in range(0, num_topics):
				# topics_slice.append(tuple(sorted(re.findall(r'0.\d*\*(\w+)', topics[i*j]))))
				topics_slice.append(topics[i*j])
			topics_per_slice.append(set(topics_slice));

		def print_topics(topics_set):
			for topic in topics_set:
				print(topic)
				print('\n')

		print('Topics Spanning Time_Slices 1 to 3\n')
		themes = list(topics_per_slice[1] & topics_per_slice[2] & topics_per_slice[3])
		dim_influences['themes'] = []
		# print_topics(themes)
		for i in range(2):
			dim_influences['themes'].append(themes[i])

		# for i in range(1, 4):
		# 	print('Topics Unique to Time_Slice ' + str(i) + '\n')
		# 	unique = topics_per_slice[i]
		# 	for j in range(1, 4):
		# 		if j != i:
		# 			unique = unique - topics_per_slice[j]
		# 	print_topics(unique)

		# print('Topics Spanning Time_Slices 1 to 2\n')
		# print_topics(topics_per_slice[1] & topics_per_slice[2] - topics_per_slice[3])
		# print('Topics Spanning Time_Slices 2 to 3\n')
		# print_topics(topics_per_slice[2] & topics_per_slice[3] - topics_per_slice[1])

		time_slice_count = 0
		docs_count = 0
		for time_slice in dimmodel.influences_time:
			print("Time_Slice " + str(time_slice_count))

			# add topics
			dim_influences["time_slice_" + str(time_slice_count) + "_topics"] = []
			for j in range(0, num_topics):
				dim_influences["time_slice_" + str(time_slice_count) + "_topics"].append(topics[time_slice_count*j])

			# add document influences
			dim_influences["time_slice_" + str(time_slice_count)] = {}
			for doc in time_slice:
				print("Doc " + str(docs_count))
				dim_influences["time_slice_" + str(time_slice_count)]["doc_" + str(docs_count)] = []
				topics_count = 0
				for topic in doc:
					print("Topic " + str(topics_count) + ": " + str(topic))
					dim_influences["time_slice_" + str(time_slice_count)]["doc_" + str(docs_count)].append(topic)
					topics_count += 1
				dim_influences["time_slice_" + str(time_slice_count)]["doc_" + str(docs_count)] = sorted(dim_influences["time_slice_" + str(time_slice_count)]["doc_" + str(docs_count)])
				docs_count += 1
			time_slice_count += 1

		with open('../timeline/static/data/dim.json', 'w') as output:
			dim_influences['info'] = {}
			dim_influences['info']['num_topics'] = num_topics
			dim_influences['info']['num_slices'] = num_slices
			dim_influences['info']['time_slices'] = my_timeslices
			json.dump(dim_influences, output, sort_keys=True, indent=4, separators=(',',': '))

	else:
		generate_tfidf()

if __name__ == "__main__":
	main()