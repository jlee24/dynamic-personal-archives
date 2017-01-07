from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
import nltk.data
from gensim import corpora, models, utils, similarities
import json
import os, operator
import re
import codecs
import pprint

pp = pprint.PrettyPrinter(indent=4)

my_dictionary = corpora.Dictionary.load('tmp/my_dictionary.dict')
my_corpus = corpora.MmCorpus('tmp/my_corpus.mm')
lsi = models.LsiModel(my_corpus, id2word=my_dictionary, num_topics=2)

tokenizer = RegexpTokenizer(r'[a-zA-Z]+\'[a-zA-Z]+|[a-zA-Z]+|\d+|\_+')
en_stop = get_stop_words('en') # create English stop words list
stop_words = open('./stop_words.txt', 'r').readlines()
for word in stop_words:
	en_stop.append(word.rstrip('\r\n'))
p_stemmer = PorterStemmer()

def clean_text(raw):
	raw = raw.lower()
	raw = "".join(c for c in raw if c not in ('!','.',':',';',"?",'"',','))
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
	return sims

with open('tmp/tfidf_scores.json', 'r') as tfidf:
	tfidf_scores = json.load(tfidf)
	# pp.pprint(tfidf_scores)
	resources = []
	docs = os.listdir('docs')
	doc_count = 0
	for doc in docs:
		file = codecs.open('docs/' + doc, 'r', "utf-8")
		text = file.read()
		doc_text = text
		if "photos" not in doc:
			sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
			sentences = sent_detector.tokenize(text.strip())

			resource = {}
			ranked_words = tfidf_scores[str(doc_count)]
			ranked_words_tokens = ranked_words.keys()

			sentence_scores = {}
			sentence_scores_raw = {}
			for sentence in sentences:
				score = 0
				stopped_tokens = clean_text(sentence)
				num_tokens = 0
				for token in stopped_tokens:
					if token in ranked_words:
						num_tokens += 1
						score += ranked_words[token] 
				if score != 0 and score > 0.10:
					sentence_scores_raw[sentence] = score
					for word in tokenizer.tokenize(sentence):
						stem = p_stemmer.stem(word)
						ranked_words_tokens = ranked_words.keys()
						if stem in ranked_words_tokens:
							sentence = sentence.replace(word, "<b>" + word + "</b>")
							ranked_words_tokens.remove(stem)
					sentence = sentence.replace("\r\n\r\n", "<br>")
					sentence_scores[sentence] = score 
			
			sentence_scores = sorted(sentence_scores.items(), key=operator.itemgetter(1), reverse=True)
			sentence_scores_raw = sorted(sentence_scores_raw.items(), key=operator.itemgetter(1), reverse=True)
			highest_ranked = [x[0] for x in sentence_scores[0:5]]
			highest_ranked_raw = [x[0] for x in sentence_scores_raw[0:5]]

			resource["overview"] = []
			for index, sent in enumerate(highest_ranked):
				resource["overview"].append("<div id='overview_" + str(index) + "'>" + sent + "</div>")

			ranked_words_tokens = ranked_words.keys()

			transcript = os.path.splitext(doc)[0] + ".json"
			if transcript in os.listdir("aligned_transcripts"):
				true_text = ""
				info = json.loads(codecs.open('aligned_transcripts/' + transcript, 'r', "utf-8").read())
				alignment_times = info["words"]
				transcript_sentences = sent_detector.tokenize(info["transcript"])

				word_counter = 0
				seek_time = 0
				for transcript_sentence in transcript_sentences:
					# print(word_counter)
					if alignment_times[word_counter]["case"] == "success":
						seek_time = alignment_times[word_counter]["start"]
					else:
						count = word_counter + 1
						while alignment_times[count]["case"] != "success":
							count += 1
						seek_time = alignment_times[count]["start"]
					# print(seek_time)

					if transcript_sentence in highest_ranked_raw:
						true_text += "<span id='full_" + str(highest_ranked_raw.index(transcript_sentence)) + "' onclick='player.seekTo(" + str(seek_time) + ")'><mark>" + transcript_sentence + " </mark></span><br><br>"
					else:
						true_text += "<span onclick='player.seekTo(" + str(seek_time) + ")'>" + transcript_sentence + " </span><br><br>"
					
					for token in tokenizer.tokenize(transcript_sentence):
						# token = re.findall(ur'(\w+\'\w+|\w+)', token, re.UNICODE)[0]
						if token == alignment_times[word_counter]["word"]:
							word_counter += 1

				for word in tokenizer.tokenize(true_text):
					stem = p_stemmer.stem(word)
					if stem in ranked_words_tokens:
						true_text = true_text.replace(word, "<b>" + word + "</b>")
						ranked_words_tokens.remove(stem)

				resource["full"] = true_text
			
			else: 
				for index, sentence_raw in enumerate(highest_ranked_raw):
					text = text.replace(sentence_raw, "</div><div id='full_" + str(index) + "'><mark>" + sentence_raw + "</mark></div><div>")
				for word in tokenizer.tokenize(text):
					stem = p_stemmer.stem(word)
					if stem in ranked_words_tokens:
						text = text.replace(word, "<b>" + word + "</b>")
						ranked_words_tokens.remove(stem)
				# text = text.replace("\r\n\r\n", "</div><br><div>")
				text = text.replace("\r\n", "<br>")
				text = "<div>" + text + "</div>"
				resource["full"] = text
		else:
			resource = {}
			resource["overview"] = "<div>" + doc_text + "</div>"
			

		resource["related"] = []
		related_works = get_related_works(doc_text)
		for index, work in enumerate(related_works):
			if index == 10:
				break
			if index < 5:
				resource["related"].append(work[0])
			else: 
				if work[1] > 0.97 and work[1] != 1.0:
					resource["related"].append(work[0])

		resources.append(resource)
		doc_count += 1
		

	# pp.pprint(resources)
	with open('../timeline/static/data/doc_views.json', 'w') as output:
		json.dump(resources, output, sort_keys=True, indent=4, separators=(',',': '))
