#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Artyom Topchyan <artyom.topchyan@live.com>
# Licensed under the GNU LGPL v2.1 - http://www.gnu.org/licenses/lgpl.html
# Based on Copyright (C) 2014 Radim Rehurek <radimrehurek@seznam.cz>


import logging
import random
import tempfile
import os
from subprocess import PIPE
import numpy as np
import numpy
import six

from gensim import utils, corpora, matutils
from gensim.utils import check_output

from scipy.special import gammaln, psi  # gamma function utils

logger = logging.getLogger(__name__)

def dirichlet_expectation(alpha):
	"""
	For a vector `theta~Dir(alpha)`, compute `E[log(theta)]`.
	"""
	if (len(alpha.shape) == 1):
		result = psi(alpha) - psi(numpy.sum(alpha))
	else:
		result = psi(alpha) - psi(numpy.sum(alpha, 1))[:, numpy.newaxis]
	return result.astype(alpha.dtype)  # keep the same precision as input


def update_dir_prior(prior, N, logphat, rho):
	"""
	Updates a given prior using Newton's method, described in
	**Huang: Maximum Likelihood Estimation of Dirichlet Distribution Parameters.**
	http://jonathan-huang.org/research/dirichlet/dirichlet.pdf
	"""
	dprior = numpy.copy(prior)
	gradf = N * (psi(numpy.sum(prior)) - psi(prior) + logphat)

	c = N * polygamma(1, numpy.sum(prior))
	q = -N * polygamma(1, prior)

	b = numpy.sum(gradf / q) / (1 / c + numpy.sum(1 / q))

	dprior = -(gradf - b) / q

	if all(rho * dprior + prior > 0):
		prior += rho * dprior
	else:
		logger.warning("updated prior not positive")

	return prior

def get_random_state(seed):
	 """ Turn seed into a np.random.RandomState instance.
		 Method originally from maciejkula/glove-python, and written by @joshloyal
	 """
	 if seed is None or seed is numpy.random:
		 return numpy.random.mtrand._rand
	 if isinstance(seed, (numbers.Integral, numpy.integer)):
		 return numpy.random.RandomState(seed)
	 if isinstance(seed, numpy.random.RandomState):
		return seed
	 raise ValueError('%r cannot be used to seed a numpy.random.RandomState'
					  ' instance' % seed)

class LdaState(utils.SaveLoad):
	"""
	Encapsulate information for distributed computation of LdaModel objects.
	Objects of this class are sent over the network, so try to keep them lean to
	reduce traffic.
	"""
	def __init__(self, eta, shape):
		self.eta = eta
		self.sstats = numpy.zeros(shape)
		self.numdocs = 0

	def reset(self):
		"""
		Prepare the state for a new EM iteration (reset sufficient stats).
		"""
		self.sstats[:] = 0.0
		self.numdocs = 0

	def merge(self, other):
		"""
		Merge the result of an E step from one node with that of another node
		(summing up sufficient statistics).
		The merging is trivial and after merging all cluster nodes, we have the
		exact same result as if the computation was run on a single node (no
		approximation).
		"""
		assert other is not None
		self.sstats += other.sstats
		self.numdocs += other.numdocs

	def blend(self, rhot, other, targetsize=None):
		"""
		Given LdaState `other`, merge it with the current state. Stretch both to
		`targetsize` documents before merging, so that they are of comparable
		magnitude.
		Merging is done by average weighting: in the extremes, `rhot=0.0` means
		`other` is completely ignored; `rhot=1.0` means `self` is completely ignored.
		This procedure corresponds to the stochastic gradient update from Hoffman
		et al., algorithm 2 (eq. 14).
		"""
		assert other is not None
		if targetsize is None:
			targetsize = self.numdocs

		# stretch the current model's expected n*phi counts to target size
		if self.numdocs == 0 or targetsize == self.numdocs:
			scale = 1.0
		else:
			scale = 1.0 * targetsize / self.numdocs
		self.sstats *= (1.0 - rhot) * scale

		# stretch the incoming n*phi counts to target size
		if other.numdocs == 0 or targetsize == other.numdocs:
			scale = 1.0
		else:
			logger.info("merging changes from %i documents into a model of %i documents",
						other.numdocs, targetsize)
			scale = 1.0 * targetsize / other.numdocs
		self.sstats += rhot * scale * other.sstats

		self.numdocs = targetsize

	def blend2(self, rhot, other, targetsize=None):
		"""
		Alternative, more simple blend.
		"""
		assert other is not None
		if targetsize is None:
			targetsize = self.numdocs

		# merge the two matrices by summing
		self.sstats += other.sstats
		self.numdocs = targetsize

	def get_lambda(self):
		return self.eta + self.sstats

	def get_Elogbeta(self):
		return dirichlet_expectation(self.get_lambda())
# endclass LdaState

class DtmModel(utils.SaveLoad):
	"""
	Class for DTM training using DTM binary. Communication between DTM and Python
	takes place by passing around data files on disk and executing the DTM binary as a subprocess.
	"""
	def __getitem__(self, bow, eps=None):
		"""
		Return topic distribution for the given document `bow`, as a list of
		(topic_id, topic_probability) 2-tuples.
		Ignore topics with very low probability (below `eps`).
		"""
		return self.get_document_topics(bow, eps)

	def __init__(
			self, dtm_path, corpus=None, time_slices=None, mode='fit', model='dtm', num_topics=100, id2word=None, prefix=None,
			lda_sequence_min_iter=6, lda_sequence_max_iter=20, lda_max_em_iter=10, alpha=0.01, eta=None, top_chain_var=0.005, random_state=None, rng_seed=0, initialize_lda=True):
		"""
		`dtm_path` is path to the dtm executable, e.g. `C:/dtm/dtm-win64.exe`.
		`corpus` is a gensim corpus, aka a stream of sparse document vectors.
		`id2word` is a mapping between tokens ids and token.
		`mode` controls the mode of the mode: 'fit' is for training, 'time' for
		analyzing documents through time according to a DTM, basically a held out set.
		`model` controls the choice of model. 'fixed' is for DIM and 'dtm' for DTM.
		`lda_sequence_min_iter` min iteration of LDA.
		`lda_sequence_max_iter` max iteration of LDA.
		`lda_max_em_iter` max em optiimzatiion iterations in LDA.
		`alpha` is a hyperparameter that affects sparsity of the document-topics for the LDA models in each timeslice.
		`top_chain_var` is a hyperparameter that affects.
		`rng_seed` is the random seed.
		`initialize_lda` initialize DTM with LDA.
		"""

		# START 

		self.random_state = get_random_state(random_state)

		# END 

		if not os.path.isfile(dtm_path):
			raise ValueError("dtm_path must point to the binary file, not to a folder")

		self.dtm_path = dtm_path
		self.id2word = id2word
		if self.id2word is None:
			logger.warning("no word id mapping provided; initializing from corpus, assuming identity")
			self.id2word = utils.dict_from_corpus(corpus)
			self.num_terms = len(self.id2word)
		else:
			self.num_terms = 0 if not self.id2word else 1 + max(self.id2word.keys())
		if self.num_terms == 0:
			raise ValueError("cannot compute DTM over an empty collection (no terms)")
		self.num_topics = num_topics

		try:
			lencorpus = len(corpus)
		except:
			logger.warning("input corpus stream has no len(); counting documents")
			lencorpus = sum(1 for _ in corpus)
		if lencorpus == 0:
			raise ValueError("cannot compute DTM over an empty corpus")
		if lencorpus != sum(time_slices):
			raise ValueError("mismatched timeslices %{slices} for corpus of len {clen}".format(
				slices=sum(time_slices), clen=lencorpus))
		self.lencorpus = lencorpus
		if prefix is None:
			rand_prefix = hex(random.randint(0, 0xffffff))[2:] + '_'
			prefix = os.path.join(tempfile.gettempdir(), rand_prefix)

		self.prefix = prefix
		self.time_slices = time_slices
		self.lda_sequence_min_iter = int(lda_sequence_min_iter)
		self.lda_sequence_max_iter = int(lda_sequence_max_iter)
		self.lda_max_em_iter = int(lda_max_em_iter)
		self.alpha = alpha
		self.top_chain_var = top_chain_var
		self.rng_seed = rng_seed
		self.initialize_lda = str(initialize_lda).lower()

		self.eta, self.optimize_eta = self.init_dir_prior(eta, 'eta')

		self.lambda_ = None
		self.obs_ = None
		self.lhood_ = None
		self.gamma_ = None
		self.init_alpha = None
		self.init_beta = None
		self.init_ss = None
		self.em_steps = []
		self.influences_time = []

		# Initialize the variational distribution q(beta|lambda)
		self.state = LdaState(self.eta, (self.num_topics, self.num_terms))
		self.state.sstats = self.random_state.gamma(100., 1. / 100., (self.num_topics, self.num_terms))
		self.expElogbeta = numpy.exp(dirichlet_expectation(self.state.sstats))

		if corpus is not None:
			self.train(corpus, time_slices, mode, model)

	def fout_liklihoods(self):
		return self.prefix + 'train_out/lda-seq/' + 'lhoods.dat'

	def fout_gamma(self):
		return self.prefix + 'train_out/lda-seq/' + 'gam.dat'

	def fout_prob(self):
		return self.prefix + 'train_out/lda-seq/' + 'topic-{i}-var-e-log-prob.dat'

	def fout_observations(self):
		return self.prefix + 'train_out/lda-seq/' + 'topic-{i}-var-obs.dat'

	def fout_influence(self):
		return self.prefix + 'train_out/lda-seq/' + 'influence_time-{i}'

	def foutname(self):
		return self.prefix + 'train_out'

	def fem_steps(self):
		return self.prefix + 'train_out/' + 'em_log.dat'

	def finit_alpha(self):
		return self.prefix + 'train_out/' + 'initial-lda.alpha'

	def finit_beta(self):
		return self.prefix + 'train_out/' + 'initial-lda.beta'

	def flda_ss(self):
		return self.prefix + 'train_out/' + 'initial-lda-ss.dat'

	def fcorpustxt(self):
		return self.prefix + 'train-mult.dat'

	def fcorpus(self):
		return self.prefix + 'train'

	def ftimeslices(self):
		return self.prefix + 'train-seq.dat'

	def convert_input(self, corpus, time_slices):
		"""
		Serialize documents in LDA-C format to a temporary text file,.
		"""
		logger.info("serializing temporary corpus to %s" % self.fcorpustxt())
		# write out the corpus in a file format that DTM understands:
		corpora.BleiCorpus.save_corpus(self.fcorpustxt(), corpus)

		with utils.smart_open(self.ftimeslices(), 'wb') as fout:
			fout.write(utils.to_utf8(str(len(self.time_slices)) + "\n"))
			for sl in time_slices:
				fout.write(utils.to_utf8(str(sl) + "\n"))

	def train(self, corpus, time_slices, mode, model):
		"""
		Train DTM model using specified corpus and time slices.
		"""
		self.convert_input(corpus, time_slices)

		arguments = "--ntopics={p0} --model={mofrl}  --mode={p1} --initialize_lda={p2} --corpus_prefix={p3} --outname={p4} --alpha={p5}".format(
			p0=self.num_topics, mofrl=model, p1=mode, p2=self.initialize_lda, p3=self.fcorpus(), p4=self.foutname(), p5=self.alpha)

		params = "--lda_max_em_iter={p0} --lda_sequence_min_iter={p1}  --lda_sequence_max_iter={p2} --top_chain_var={p3} --rng_seed={p4} ".format(
			p0=self.lda_max_em_iter, p1=self.lda_sequence_min_iter, p2=self.lda_sequence_max_iter, p3=self.top_chain_var, p4=self.rng_seed)

		arguments = arguments + " " + params
		logger.info("training DTM with args %s" % arguments)

		cmd = [self.dtm_path] + arguments.split()
		logger.info("Running command %s" % cmd)
		check_output(cmd, stderr=PIPE)

		self.em_steps = np.loadtxt(self.fem_steps())
		self.init_ss = np.loadtxt(self.flda_ss())

		if self.initialize_lda:
			self.init_alpha = np.loadtxt(self.finit_alpha())
			self.init_beta = np.loadtxt(self.finit_beta())

		self.lhood_ = np.loadtxt(self.fout_liklihoods())

		# document-topic proportions
		self.gamma_ = np.loadtxt(self.fout_gamma())
		# cast to correct shape, gamme[5,10] is the proprtion of the 10th topic
		# in doc 5
		self.gamma_.shape = (self.lencorpus, self.num_topics)
		# normalize proportions
		self.gamma_ /= self.gamma_.sum(axis=1)[:, np.newaxis]

		self.lambda_ = np.zeros((self.num_topics, self.num_terms * len(self.time_slices)))
		self.obs_ = np.zeros((self.num_topics, self.num_terms * len(self.time_slices)))

		for t in range(self.num_topics):
				topic = "%03d" % t
				self.lambda_[t, :] = np.loadtxt(self.fout_prob().format(i=topic))
				self.obs_[t, :] = np.loadtxt(self.fout_observations().format(i=topic))
		# cast to correct shape, lambda[5,10,0] is the proportion of the 10th
		# topic in doc 5 at time 0
		self.lambda_.shape = (self.num_topics, self.num_terms, len(self.time_slices))
		self.obs_.shape = (self.num_topics, self.num_terms, len(self.time_slices))
		# extract document influence on topics for each time slice
		# influences_time[0] , influences at time 0
		if model == 'fixed':
			for k, t in enumerate(self.time_slices):
				stamp = "%03d" % k
				influence = np.loadtxt(self.fout_influence().format(i=stamp))
				influence.shape = (t, self.num_topics)
				# influence[2,5] influence of document 2 on topic 5
				self.influences_time.append(influence)

	def print_topics(self, num_topics=10, times=5, num_words=10):
		return self.show_topics(num_topics, times, num_words, log=True)

	def show_topics(self, num_topics=10, times=5, num_words=10, log=False, formatted=True):
		"""
		Print the `num_words` most probable words for `num_topics` number of topics at 'times' time slices.
		Set `topics=-1` to print all topics.
		Set `formatted=True` to return the topics as a list of strings, or `False` as lists of (weight, word) pairs.
		"""
		if num_topics < 0 or num_topics >= self.num_topics:
			num_topics = self.num_topics
			chosen_topics = range(num_topics)
		else:
			num_topics = min(num_topics, self.num_topics)
			chosen_topics = range(num_topics)
			 # add a little random jitter, to randomize results around the same
			# alpha
			# sort_alpha = self.alpha + 0.0001 * \
			#     numpy.random.rand(len(self.alpha))
			# sorted_topics = list(numpy.argsort(sort_alpha))
			# chosen_topics = sorted_topics[: topics / 2] + \
			#     sorted_topics[-topics / 2:]

		if times < 0 or times >= len(self.time_slices):
			times = len(self.time_slices)
			chosen_times = range(times)
		else:
			times = min(times, len(self.time_slices))
			chosen_times = range(times)

		shown = []
		for time in chosen_times:
			for i in chosen_topics:
				if formatted:
					topic = self.print_topic(i, time, num_words=num_words)
				else:
					topic = self.show_topic(i, time, num_words=num_words)
				shown.append(topic)
				# if log:
				# logger.info("topic #%i (%.3f): %s" % (i, self.alpha[i],
				#     topic))
		return shown

	def show_topic(self, topicid, time, num_words=50):
		"""
		Return `num_words` most probable words for the given `topicid`, as a list of
		`(word_probability, word)` 2-tuples.
		"""
		topics = self.lambda_[:, :, time]
		topic = topics[topicid]
		# liklihood to probability
		topic = np.exp(topic)
		# normalize to probability dist
		topic = topic / topic.sum()
		# sort according to prob
		bestn = matutils.argsort(topic, num_words, reverse=True)
		beststr = [(topic[id], self.id2word[id]) for id in bestn]
		return beststr

	def print_topic(self, topicid, time, num_words=10):
		"""Return the given topic, formatted as a string."""
		return ' + '.join(['%.3f*%s' % v for v in self.show_topic(topicid, time, num_words)])

	def inference(self, chunk, collect_sstats=False):
			"""
			Given a chunk of sparse document vectors, estimate gamma (parameters
			controlling the topic weights) for each document in the chunk.
			This function does not modify the model (=is read-only aka const). The
			whole input chunk of document is assumed to fit in RAM; chunking of a
			large corpus must be done earlier in the pipeline.
			If `collect_sstats` is True, also collect sufficient statistics needed
			to update the model's topic-word distributions, and return a 2-tuple
			`(gamma, sstats)`. Otherwise, return `(gamma, None)`. `gamma` is of shape
			`len(chunk) x self.num_topics`.
			Avoids computing the `phi` variational parameter directly using the
			optimization presented in **Lee, Seung: Algorithms for non-negative matrix factorization, NIPS 2001**.
			"""

			try:
				_ = len(chunk)
			except:
				# convert iterators/generators to plain list, so we have len() etc.
				chunk = list(chunk)
			if len(chunk) > 1:
				logger.debug("performing inference on a chunk of %i documents", len(chunk))

			# Initialize the variational distribution q(theta|gamma) for the chunk
			gamma = self.random_state.gamma(100., 1. / 100., (len(chunk), self.num_topics))
			Elogtheta = dirichlet_expectation(gamma)
			expElogtheta = numpy.exp(Elogtheta)
			if collect_sstats:
				sstats = numpy.zeros_like(self.expElogbeta)
			else:
				sstats = None
			converged = 0

			# Now, for each document d update that document's gamma and phi
			# Inference code copied from Hoffman's `onlineldavb.py` (esp. the
			# Lee&Seung trick which speeds things up by an order of magnitude, compared
			# to Blei's original LDA-C code, cool!).
			for d, doc in enumerate(chunk):
				if doc and not isinstance(doc[0][0], six.integer_types):
					# make sure the term IDs are ints, otherwise numpy will get upset
					ids = [int(id) for id, _ in doc]
				else:
					ids = [id for id, _ in doc]
				cts = numpy.array([cnt for _, cnt in doc])
				gammad = gamma[d, :]
				Elogthetad = Elogtheta[d, :]
				expElogthetad = expElogtheta[d, :]
				expElogbetad = self.expElogbeta[:, ids]

				# The optimal phi_{dwk} is proportional to expElogthetad_k * expElogbetad_w.
				# phinorm is the normalizer.
				# TODO treat zeros explicitly, instead of adding 1e-100?
				phinorm = numpy.dot(expElogthetad, expElogbetad) + 1e-100

				# Iterate between gamma and phi until convergence
				for _ in xrange(self.iterations):
					lastgamma = gammad
					# We represent phi implicitly to save memory and time.
					# Substituting the value of the optimal phi back into
					# the update for gamma gives this update. Cf. Lee&Seung 2001.
					gammad = self.alpha + expElogthetad * numpy.dot(cts / phinorm, expElogbetad.T)
					Elogthetad = dirichlet_expectation(gammad)
					expElogthetad = numpy.exp(Elogthetad)
					phinorm = numpy.dot(expElogthetad, expElogbetad) + 1e-100
					# If gamma hasn't changed much, we're done.
					meanchange = numpy.mean(abs(gammad - lastgamma))
					if (meanchange < self.gamma_threshold):
						converged += 1
						break
				gamma[d, :] = gammad
				if collect_sstats:
					# Contribution of document d to the expected sufficient
					# statistics for the M step.
					sstats[:, ids] += numpy.outer(expElogthetad.T, cts / phinorm)

			if len(chunk) > 1:
				logger.debug("%i/%i documents converged within %i iterations",
							 converged, len(chunk), self.iterations)

			if collect_sstats:
				# This step finishes computing the sufficient statistics for the
				# M step, so that
				# sstats[k, w] = \sum_d n_{dw} * phi_{dwk}
				# = \sum_d n_{dw} * exp{Elogtheta_{dk} + Elogbeta_{kw}} / phinorm_{dw}.
				sstats *= self.expElogbeta
			return gamma, sstats

	def get_document_topics(self, bow, minimum_probability=None, minimum_phi_value=None, per_word_topics=False):
			"""
			Return topic distribution for the given document `bow`, as a list of
			(topic_id, topic_probability) 2-tuples.
			Ignore topics with very low probability (below `minimum_probability`).
			If per_word_topics is True, it also returns a list of topics, sorted in descending order of most likely topics for that word.
			It also returns a list of word_ids and each words corresponding topics' phi_values, multiplied by feature length (i.e, word count)
			"""
			# if minimum_probability is None:
			# 	minimum_probability = self.minimum_probability
			minimum_probability = max(minimum_probability, 1e-8)  # never allow zero values in sparse output

			# if minimum_phi_value is None:
			# 	minimum_phi_value = self.minimum_probability
			minimum_phi_value = max(minimum_phi_value, 1e-8)  # never allow zero values in sparse output

			# if the input vector is a corpus, return a transformed corpus
			is_corpus, corpus = utils.is_corpus(bow)
			if is_corpus:
				return self._apply(corpus)

			gamma, phis = self.inference([bow], collect_sstats=True)
			topic_dist = gamma[0] / sum(gamma[0])  # normalize distribution

			document_topics = [(topicid, topicvalue) for topicid, topicvalue in enumerate(topic_dist)
						if topicvalue >= minimum_probability]

			if not per_word_topics:
				return document_topics
			else:
				word_topic = [] # contains word and corresponding topic
				word_phi = [] # contains word and phi values
				for word_type, weight in bow:
					phi_values = [] # contains (phi_value, topic) pairing to later be sorted
					phi_topic = [] # contains topic and corresponding phi value to be returned 'raw' to user
					for topic_id in range(0, self.num_topics):
						if phis[topic_id][word_type] >= minimum_phi_value:
							# appends phi values for each topic for that word
							# these phi values are scaled by feature length
							phi_values.append((phis[topic_id][word_type], topic_id))
							phi_topic.append((topic_id, phis[topic_id][word_type]))

					# list with ({word_id => [(topic_0, phi_value), (topic_1, phi_value) ...]).
					word_phi.append((word_type, phi_topic))
					# sorts the topics based on most likely topic
					# returns a list like ({word_id => [topic_id_most_probable, topic_id_second_most_probable, ...]).
					sorted_phi_values = sorted(phi_values, reverse=True)
					topics_sorted = [x[1] for x in sorted_phi_values]
					word_topic.append((word_type, topics_sorted))
				return (document_topics, word_topic, word_phi) # returns 2-tuple

	def init_dir_prior(self, prior, name):
		if prior is None:
			prior = 'symmetric'

		is_auto = False

		if isinstance(prior, six.string_types):
			if prior == 'symmetric':
				logger.info("using symmetric %s at %s", name, 1.0 / self.num_topics)
				init_prior = numpy.asarray([1.0 / self.num_topics for i in xrange(self.num_topics)])
			elif prior == 'asymmetric':
				init_prior = numpy.asarray([1.0 / (i + numpy.sqrt(self.num_topics)) for i in xrange(self.num_topics)])
				init_prior /= init_prior.sum()
				logger.info("using asymmetric %s %s", name, list(init_prior))
			elif prior == 'auto':
				is_auto = True
				init_prior = numpy.asarray([1.0 / self.num_topics for i in xrange(self.num_topics)])
				logger.info("using autotuned %s, starting with %s", name, list(init_prior))
			else:
				raise ValueError("Unable to determine proper %s value given '%s'" % (name, prior))
		elif isinstance(prior, list):
			init_prior = numpy.asarray(prior)
		elif isinstance(prior, numpy.ndarray):
			init_prior = prior
		elif isinstance(prior, numpy.number) or isinstance(prior, numbers.Real):
			init_prior = numpy.asarray([prior] * self.num_topics)
		else:
			raise ValueError("%s must be either a numpy array of scalars, list of scalars, or scalar" % name)

		if name == 'eta':
			# please note the difference in shapes between alpha and eta:
			# alpha is a row: [0.1, 0.1]
			# eta is a column: [[0.1],
			#                   [0.1]]
			if init_prior.shape == (self.num_topics,) or init_prior.shape == (1, self.num_topics):
				init_prior = init_prior.reshape((self.num_topics, 1))  # this statement throws ValueError if eta did not match self.num_topics

		return init_prior, is_auto