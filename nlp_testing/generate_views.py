from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
import nltk.data
import json
import os, operator
import codecs
import pprint

pp = pprint.PrettyPrinter(indent=4)

tokenizer = RegexpTokenizer(r'[a-zA-Z]+\'[a-zA-Z]+|[a-zA-Z]+')
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

with open('tmp/tfidf_scores.json', 'r') as tfidf:
	tfidf_scores = json.load(tfidf)
	# pp.pprint(tfidf_scores)
	resources = []
	docs = os.listdir('docs')
	doc_count = 0
	for doc in docs:
		file = codecs.open('docs/' + doc, 'r', "utf-8")
		text = file.read()
		sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
		sentences = sent_detector.tokenize(text.strip())

		resource = {}

		sentence_scores = {}
		sentence_scores_raw = {}
		for index, sentence in enumerate(sentences):
			score = 0
			stopped_tokens = clean_text(sentence)
			num_tokens = 0
			ranked_words = tfidf_scores[str(doc_count)]
			for token in stopped_tokens:
				if token in ranked_words:
					num_tokens += 1
					score += ranked_words[token] 
			if score != 0 and score > 0.10:
				sentence_scores_raw[sentence] = score
				for word in tokenizer.tokenize(sentence):
					stem = p_stemmer.stem(word)
					if stem in ranked_words.keys():
						sentence = sentence.replace(word, "<b>" + word + "</b>")
				sentence = sentence.replace("\r\n\r\n", "<br>")
				sentence = "<div id='overview_" + str(index) + "'>" + sentence + "</div>"
				sentence_scores[sentence] = score 
		
		sentence_scores = sorted(sentence_scores.items(), key=operator.itemgetter(1), reverse=True)
		sentence_scores_raw = sorted(sentence_scores_raw.items(), key=operator.itemgetter(1), reverse=True)
		sentences = [x[0] for x in sentence_scores[0:5]]
		sentences_raw = [x[0] for x in sentence_scores_raw[0:5]]

		resource["overview"] = sentences

		for sentence_raw in sentences_raw:
			text = text.replace(sentence_raw, "<mark id='full_" + str(index) + "'>" + sentence_raw + "</mark>")

		for word in tokenizer.tokenize(text):
			stem = p_stemmer.stem(word)
			if stem in ranked_words.keys():
				text = text.replace(word, "<b>" + word + "</b>")
		# text = text.replace("\r\n\r\n", "</div><br><div>")
		text = text.replace("\r\n", "<br>")
		# text = "<div>" + text + "</div>"
		
		resource["full"] = text
		resources.append(resource)
		doc_count += 1
		

	# pp.pprint(resources)
	with open('../timeline/static/data/doc_views.json', 'w') as output:
		json.dump(resources, output, sort_keys=True, indent=4, separators=(',',': '))
