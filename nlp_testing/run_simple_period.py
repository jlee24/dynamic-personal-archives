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

period_dict = []
total_dict = {}
num_words = []

def clean_text(doc_location):
	# command = "sumy luhn --file=" + doc_location # summarize document string
	# raw = subprocess.check_output(command, shell=True)
	file = open(doc_location, 'r')
	raw = file.read()
	raw = raw.lower()
	raw = "".join(c for c in raw if c not in ('!','.',':',';','-',"'","?",'"',','))
	raw = unicode(raw, errors='replace')
	tokens = tokenizer.tokenize(raw)
	stopped_tokens = [i for i in tokens if not i in en_stop]
	stemmed_tokens = [p_stemmer.stem(i) for i in stopped_tokens]
	return stemmed_tokens

def get_word_counts(start, end):
	_period_dict = {}
	num_words.append(0)
	for file in os.listdir('docs'):
		if (int(file[0:4]) >= start) & (int(file[0:4]) <= end):
			print(start, end, int(file[0:4]))
			stemmed_tokens = clean_text('docs/' + file)
			num_words[len(num_words)-1] += len(stemmed_tokens)
			for token in stemmed_tokens:
				if token in _period_dict:
					_period_dict[token] += 1
				else:
					_period_dict[token] = 1
				if token in total_dict:
					total_dict[token] += 1
				else:
					total_dict[token] = 1
	return _period_dict

def main():

	# time periods: 1961-1968, 1970-1987, 1989-2004
	period_dict.append(get_word_counts(1961, 1968))
	period_dict.append(get_word_counts(1970, 1987))
	period_dict.append(get_word_counts(1989, 2004))

	total_num_words  = sum(num_words)

	# { w: [P(w|TP0), P(w|TP1), ... ], w1: ... }
	condit_prob_dict = {}
	for word in total_dict:
		condit_prob_dict[word] = []
		nperiod = 0

		# P(w|TP) = P(w,TP)/P(w)P(TP)
		# P(w) = P(w|TP0)P(TP0) + P(w|TP1)P(TP1)

		Pw = 0
		# the loop below performs: P(w|TP) = P(w,TP)/P(TP) and calculates P(w)
		for period in period_dict:
			condit_prob = 0
			if word in period:
				w = period[word] # count of word in this period
				PwTP = float(w) / num_words[nperiod]
				Pw += w
				PTP = float(num_words[nperiod]) / total_num_words
				condit_prob = PwTP / PTP
			condit_prob_dict[word].append(condit_prob)
			nperiod += 1

		Pw = float(Pw) / total_num_words
		print(condit_prob_dict[word])
		for prob in condit_prob_dict[word]:
			prob = float(prob) / Pw
		# 	# prob = math.log(prob / Pw)
		# 	prob = math.log(prob/Pw)
		print(condit_prob_dict[word])

	# print(condit_prob_dict)

	with open('tmp/simple.json', 'w') as output:
		json.dump(condit_prob_dict, output, sort_keys=True, indent=4, separators=(',',': '))

	f = csv.writer(open("tmp/simple.csv", "wb+"))
	f.writerow(["Word", "Time Period 0", "Time Period 1", "Time Period 2"])	

	for x in condit_prob_dict:
		f.writerow([x, condit_prob_dict[x][0], condit_prob_dict[x][1], condit_prob_dict[x][2]])


if __name__ == "__main__":
	main()