from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
from gensim import corpora, models, utils
import sys, os, subprocess, operator
import csv, json, math, string

tokenizer = RegexpTokenizer(r'[a-zA-Z]+\'[a-zA-Z]+|[a-zA-Z]+')
en_stop = get_stop_words('en') # create English stop words list
stop_words = open('./stop_words.txt', 'r').readlines()
for word in stop_words:
	en_stop.append(word.rstrip('\r\n'))
p_stemmer = PorterStemmer()

doc_dict = []
total_dict = {}
num_words = []

def clean_text(doc_location):
	# command = "sumy luhn --file=" + doc_location # summarize document string
	# raw = subprocess.check_output(command, shell=True)
	file = open(doc_location, 'r')
	raw = file.read()
	raw = raw.lower()
	raw = "".join(c for c in raw if c not in ('!','.',':','-',';',"'","?",'"',','))
	raw = unicode(raw, errors='replace')
	tokens = tokenizer.tokenize(raw)
	stopped_tokens = [i for i in tokens if not i in en_stop]
	stemmed_tokens = [p_stemmer.stem(i) for i in stopped_tokens]
	return stemmed_tokens

def get_word_counts(file):
	_doc_dict = {}
	num_words.append(0)
	stemmed_tokens = clean_text('docs/' + file)
	num_words[len(num_words)-1] += len(stemmed_tokens)
	for token in stemmed_tokens:
		if token in _doc_dict:
			_doc_dict[token] += 1
		else:
			_doc_dict[token] = 1
		if token in total_dict:
			total_dict[token] += 1
		else:
			total_dict[token] = 1

	return _doc_dict

def main():

	# time periods: 1961-1968, 1970-1987, 1989-2004
	# getting probabilities per document
	for file in os.listdir('docs'):
		doc_dict.append(get_word_counts(file))

	total_num_words  = sum(num_words)

	# { w: [P(w;doc0), P(w;doc1), ... ], w1: ... }
	condit_prob_dict = {}
	for word in total_dict:
		condit_prob_dict[word] = []
		ndoc = 0

		# P(w;doc) = P(w,doc)/P(w)P(doc)
		# P(w) = P(w|doc0)P(doc0) + P(w|doc1)P(doc1) + ...

		Pw = 0
		# the loop below performs: P(w|doc) = P(w,doc)/P(doc) and calculates P(w)
		for doc in doc_dict:
			condit_prob = 0
			if word in doc:
				w = doc[word] # count of word in this doc
				Pwdoc = float(w) / num_words[ndoc]
				Pw += w
				Pdoc = float(num_words[ndoc]) / total_num_words
				condit_prob = Pwdoc / Pdoc
			condit_prob_dict[word].append(condit_prob)
			ndoc += 1

		Pw = float(Pw) / total_num_words
		for prob in condit_prob_dict[word]:
			prob = math.log(float(prob) / Pw)

	# print(condit_prob_dict)

	with open('tmp/simple_doc.json', 'w') as output:
		json.dump(condit_prob_dict, output, sort_keys=True, indent=4, separators=(',',': '))

	header_row = ["Doc " + str(i) for i in range(len(num_words)-1)]

	f = csv.writer(open("tmp/simple_doc.csv", "wb+"))
	f.writerow(["Word"] + header_row)	

	for x in condit_prob_dict:
		f.writerow([x] + [condit_prob_dict[x][i] for i in range(len(condit_prob_dict[x])-1)])


if __name__ == "__main__":
	main()