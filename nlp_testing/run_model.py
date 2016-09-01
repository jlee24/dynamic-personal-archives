from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
import nltk.data
import sys, os, subprocess, operator, argparse
from gensim import corpora, models, utils
import json
import re
import pprint
import codecs 

# import logging
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

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

def clean_text(raw):
	raw = raw.lower()
	raw = "".join(c for c in raw if c not in ('!','.',':',';',"?",'"',','))
	if model != 'tfidf':
		raw = unicode(raw, errors='replace')
	tokens = tokenizer.tokenize(raw)
	stopped_tokens = [i for i in tokens if not i in en_stop]
	stemmed_tokens = [p_stemmer.stem(i) for i in stopped_tokens if i != 'nls']
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
			file = codecs.open('docs/' + doc, 'r', "utf-8")
			raw = file.read()
			texts.append(clean_text(raw))
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
	tfidf_scores = {}
	my_dictionary = create_dictionary()
	# convert tokenized documents into a document-term matrix
	my_corpus = create_corpus(my_dictionary)
	tfidf = models.tfidfmodel.TfidfModel(my_corpus)
	corpus_tfidf = tfidf[my_corpus]

	count = 0
	for doc in corpus_tfidf:
		tfidf_scores[count] = {}
		doc.sort(key=operator.itemgetter(1), reverse=True)
		for word in doc:
			if word[1] >= 0.10:
				tfidf_scores[count][my_dictionary[word[0]]] = word[1]
			else:
				break
		count += 1
	return tfidf_scores

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
		num_topics = 5
		num_words = 7

		dimmodel = generate_dim(num_topics, my_timeslices)
		dimmodel.save('tmp/dimmodel3.model')
		# dimmodel = models.wrappers.DtmModel.load('tmp/dimmodel.model')
		# dimmodel = models.wrappers.DtmModel.load('tmp/dimmodel1.model')

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

		themes = list(topics_per_slice[1] & topics_per_slice[2] & topics_per_slice[3])
		dim_influences['themes'] = []
		for i in range(3):
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
			# print("Time_Slice " + str(time_slice_count))
			# add topics
			dim_influences["time_slice_" + str(time_slice_count) + "_topics"] = []
			for j in range(0, num_topics):
				dim_influences["time_slice_" + str(time_slice_count) + "_topics"].append(topics[time_slice_count*j])

			# add document influences
			dim_influences["time_slice_" + str(time_slice_count)] = {}
			for doc in time_slice:
				# print("Doc " + str(docs_count))
				dim_influences["time_slice_" + str(time_slice_count)]["doc_" + str(docs_count)] = []
				topics_count = 0
				for topic in doc:
					# print("Topic " + str(topics_count) + ": " + str(topic))
					dim_influences["time_slice_" + str(time_slice_count)]["doc_" + str(docs_count)].append(topic)
					topics_count += 1
				dim_influences["time_slice_" + str(time_slice_count)]["doc_" + str(docs_count)] = sorted(dim_influences["time_slice_" + str(time_slice_count)]["doc_" + str(docs_count)])
				docs_count += 1
			time_slice_count += 1

		with open('tmp/dim_influences.json', 'w') as output:
			dim_influences['info'] = {}
			dim_influences['info']['num_topics'] = num_topics
			dim_influences['info']['num_slices'] = num_slices
			dim_influences['info']['time_slices'] = my_timeslices
			json.dump(dim_influences, output, sort_keys=True, indent=4, separators=(',',': '))

	else:
		tfidf_scores = generate_tfidf()
		print(tfidf_scores)
		with open('tmp/tfidf_scores.json', 'w') as output:
			json.dump(tfidf_scores, output, sort_keys=True, indent=4, separators=(',',': '))			

		# summaries = []
		# docs = os.listdir('docs')
		# doc_count = 0
		# for doc in docs:
		# 	file = codecs.open('docs/' + doc, 'r', "utf-8")
		# 	text = file.read()
		# 	sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
		# 	sentences = sent_detector.tokenize(text.strip())

		# 	sentence_scores = {}
		# 	for sentence in sentences:
		# 		score = 0
		# 		stopped_tokens = clean_text(sentence)
		# 		num_tokens = 0
		# 		for token in stopped_tokens:
		# 			if token in tfidf_scores[doc_count]:
		# 				num_tokens += 1
		# 				score += tfidf_scores[doc_count][token] 
		# 		if score != 0 and score > 0.10:
		# 			sentence_scores[sentence] = score 

		# 	doc_count += 1

		# 	sentence_scores = sorted(sentence_scores.items(), key=operator.itemgetter(1), reverse=True)
		# 	sentence_scores = [x[0] for x in sentence_scores[0:10]]
		# 	# pp.pprint(sentence_scores)
		# 	summaries.append(sentence_scores)

		# pp.pprint(summaries)

if __name__ == "__main__":
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

	main()