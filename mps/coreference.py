#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:

import sys
from collections import defaultdict
import string

import head_finder

# TODO: Look into semantic head finding (current is syntactically biased)

def confusion_groups(gold_mentions, auto_mentions, gold_clusters, auto_clusters):
	groups = []
	mentions = set()
	for mention in gold_mentions:
		mentions.add(mention)
	for mention in auto_mentions:
		mentions.add(mention)
	while len(mentions) > 0:
		# Choose a random mention and DFS to create the confusion group
		auto = []
		gold = []
		seed = mentions.pop()
		stack = []
		seen_gold = set()
		seen_auto = set()
		if seed in gold_mentions:
			stack.append((gold_mentions[seed], True))
			seen_gold.add(stack[0][0])
		else:
			stack.append((auto_mentions[seed], False))
			seen_auto.add(stack[0][0])

		while len(stack) > 0:
			cluster, is_gold = stack.pop()
			if is_gold:
				gold.append(set(gold_clusters[cluster]))
				for mention in gold_clusters[cluster]:
					auto_cluster = auto_mentions.get(mention)
					if auto_cluster is not None:
						if auto_cluster not in seen_auto:
							stack.append((auto_cluster, False))
							seen_auto.add(auto_cluster)
					mentions.discard(mention)
			else:
				auto.append(set(auto_clusters[cluster]))
				for mention in auto_clusters[cluster]:
					gold_cluster = gold_mentions.get(mention)
					if gold_cluster is not None:
						if gold_cluster not in seen_gold:
							stack.append((gold_cluster, True))
							seen_gold.add(gold_cluster)
					mentions.discard(mention)
		groups.append((auto, gold))
	return groups

# Canasai's addition begin
# Try to find the correct head position of special cases of NPs.
def find_appositive(mention, text, parses, heads):
	'''
	Yes:
	nw/wsj/24/wsj_2422   0    0    Investcorp    NNP     (TOP(S(NP(NP*)      (ORG)     (5
	nw/wsj/24/wsj_2422   0    1             ,      ,                 *          *       -
	nw/wsj/24/wsj_2422   0    2           New    NNP              (NP*      (GPE*       -
	nw/wsj/24/wsj_2422   0    3          York    NNP                 *)         *)      -
	nw/wsj/24/wsj_2422   0    4             ,      ,                 *)         *       5)

	Yes:
	nw/wsj/00/wsj_0089   0   24          John    NNP     (NP(NP*     (PERSON*     (12
	nw/wsj/00/wsj_0089   0   25            C.    NNP           *            *       -
	nw/wsj/00/wsj_0089   0   26       Baldwin    NNP           *)           *)      -
	nw/wsj/00/wsj_0089   0   27             ,      ,           *            *       -
	nw/wsj/00/wsj_0089   0   28     president     NN        (NP*))          *      12)
	nw/wsj/00/wsj_0089   0   29             .      .           *))          *       -

	No:
	nw/wsj/24/wsj_2412   0    8            D.     NNP      (NP(NP*)         *)    -
	nw/wsj/24/wsj_2412   0    9             ,       ,            *          *     -
	nw/wsj/24/wsj_2412   0   10            Ga     NNP         (NP*      (GPE*     -
	nw/wsj/24/wsj_2412   0   11             .       .           *))         *)    -

	The head finding should perform on the first constituent.'''
        comma_idx = -1
	sentence, start, end = mention
	node = parses[sentence].get_nodes('lowest', start, end)
	if node is not None and node.label == 'NP':
		if (len(node.subtrees) == 4 and
			node.subtrees[0].label == 'NP' and
			node.subtrees[1].label == ',' and
			node.subtrees[2].label == 'NP' and
			node.subtrees[3].label == ',' and
			not node.subtrees[0].word_yield().endswith('.')):
			comma_idx = node.subtrees[0].span[1]
		if (len(node.subtrees) == 3 and
			node.subtrees[0].label == 'NP' and
			node.subtrees[1].label == ',' and
			node.subtrees[2].label == 'NP' and
			not node.subtrees[0].word_yield().endswith('.')):
			comma_idx = node.subtrees[0].span[1]
	return comma_idx

def find_possessive(mention, text, parses, heads):
	'''
	Yes:
	nw/wsj/24/wsj_2431   0   14           Mr.     NNP      (NP(NP*            *      (9
	nw/wsj/24/wsj_2431   0   15    Papandreou     NNP            *      (PERSON)      -
	nw/wsj/24/wsj_2431   0   16            's     POS            *)           *       9)

	No:
	bc/cnn/00/cnn_0000   13   26              a    DT      (NP(NP*            -         -
	bc/cnn/00/cnn_0000   13   27       personal    JJ            *            -         -
	bc/cnn/00/cnn_0000   13   28         friend    NN            *)           -         -
	bc/cnn/00/cnn_0000   13   29             of    IN         (PP*            -         -
	bc/cnn/00/cnn_0000   13   30          Brown   NNP         (NP*      (PERSON)      (91
	bc/cnn/00/cnn_0000   13   31             's   POS            *)))         *        91)

	NP spans should share the same head with NE which is "Papandreou", not "'s".
	The head finding should perform on the span without "'s".'''
        apostrophe_idx = -1
	sentence, start, end = mention 
	#if text[sentence][end - 1:end][0] in {"'s", "'"}:
	#	apostrophe_idx = end - 1

	return apostrophe_idx

def special_cases(mention, text, parses, heads):
	sentence, start, end = mention
	if end - start <= 1:
		return mention

        comma_idx = find_appositive(mention, text, parses, heads)
	apostrophe_idx = find_possessive(mention, text, parses, heads)
	if apostrophe_idx != -1 and start < apostrophe_idx:
		ret = (sentence, start, apostrophe_idx)
	elif apostrophe_idx == -1 and comma_idx != -1 and start < comma_idx:
		ret = (sentence, start, comma_idx)
	else:
		ret = mention

	return ret
# Canasai's addition end

def mention_head(mention, text, parses, heads, default_last=True):
	# Canasai's addition begin
	#mention = special_cases(mention, text, parses, heads)
	# Canasai's addition end

	sentence, start, end = mention
	node = parses[sentence].get_nodes('lowest', start, end)
	if node is None:
		if default_last:
			node = parses[sentence].get_nodes('lowest', end - 1, end)
		else:
			return None
	return head_finder.get_head(heads[sentence], node)

def mention_type(mention, text, parses, heads):
	head_span, head_word, head_pos = mention_head(mention, text, parses, heads)
	# Canasai' comment out: if mention[2] - mention[1] == 1 and (head_pos in ["PRP", "PRP$", "WP", "WP$", "WDT", "WRB", "DT"] or head_word.lower() in pronoun_properties):
	if mention[2] - mention[1] == 1 and (head_pos in ["PRP", "PRP$"] or head_word.lower() in pronoun_properties):
		return "pronoun"
	elif head_pos in ["NNP", "NNPS"]:
		return "name"
	else:
		return 'nominal'

def mention_text(mention, text):
	sentence, start, end = mention
	ans = text[sentence][start:end]
	return ' '.join(ans)

def set_of_clusters(clusters):
	ans = set()
	for cluster in clusters:
		mentions = clusters[cluster][:]
		mentions.sort()
		ans.add(tuple(mentions))
	return ans

def set_of_mentions(clusters):
	ans = set()
	for cluster in clusters:
		for mention in clusters[cluster]:
			ans.add(mention)
	return ans

def hash_clustering(clustering):
	clustering = [list(v) for v in clustering]
	for i in xrange(len(clustering)):
		clustering[i].sort()
		clustering[i] = tuple(clustering[i])
	clustering.sort()
	return tuple(clustering)

PRO_FIRST = 1
PRO_SECOND = 2
PRO_THIRD = 3
PRO_PLURAL = 2
PRO_SINGLE = 1
PRO_UNKNOWN = 0
PRO_FEMALE = 1
PRO_MALE = 2
PRO_NEUTER = 3
# Canasai's addition begin
PRO_ANIMATE = 1
PRO_INANIMATE = 2
class Property: 
    gender, number, person, animacy = range(4)

    @staticmethod
    def get_text(nums):
	gender = 'unknown'
	number = 'unknown'
	person = 'unknown'
	animacy = 'unknown'
        if nums[0] == PRO_FEMALE:
            gender = 'female'
        elif nums[0] == PRO_MALE:
            gender = 'male'
        elif nums[0] == PRO_NEUTER:
            gender = 'neuter'

        if nums[1] == PRO_SINGLE:
            number = 'single'
        elif nums[1] == PRO_PLURAL:
            number = 'plural'

        if nums[2] == PRO_FIRST:
            person = 'first'
        elif nums[2] == PRO_SECOND:
            person = 'second'
        elif nums[2] == PRO_THIRD:
            person = 'third'

        if nums[3] == PRO_ANIMATE:
            animacy = 'animate'
        elif nums[3] == PRO_INANIMATE:
            animacy = 'inanimate'

        return gender, number, person, animacy
    
    
# Canasai's addition end

def pronoun_properties_text(text):
	gender = 'unknown'
	number = 'unknown'
	person = 'unknown'
	# Canasai's addition begin
	animacy = 'unknown'
	# Canasai's addition end
	text = text.lower()
	if text in pronoun_properties:
		nums = pronoun_properties[text]

		if nums[0] == PRO_FEMALE:
			gender = 'female'
		elif nums[0] == PRO_MALE:
			gender = 'male'
		elif nums[0] == PRO_NEUTER:
			gender = 'neuter'

		if nums[1] == PRO_SINGLE:
			number = 'single'
		elif nums[1] == PRO_PLURAL:
			number = 'plural'

		if nums[2] == PRO_FIRST:
			# Canasai's comment out: gender = 'first'
			 person = 'first'
		elif nums[2] == PRO_SECOND:
			# Canasai's comment out: gender = 'second'
			person = 'second'
		elif nums[2] == PRO_THIRD:
			# Canasai's comment out: gender = 'third'
			person = 'third'

		# Canasai's addition begin
		if nums[3] == PRO_ANIMATE:
			animacy = 'animate'
		elif nums[3] == PRO_INANIMATE:
			animacy = 'inanimate'
		# Canasai's addition end

		
	# Canasai's comment out: return gender, number, person
	return gender, number, person, animacy

# Notes:
# Plural and singular are defined in terms of the property of the entity being
# denoted.
# Canasai's addition begin: append animacy (PRO_ANIMATE or PRO_INANIMATE) to tuples
pronoun_properties = {
	"her": (PRO_FEMALE, PRO_SINGLE, PRO_THIRD, PRO_ANIMATE),
	"hers": (PRO_FEMALE, PRO_SINGLE, PRO_THIRD, PRO_ANIMATE),
	"herself": (PRO_FEMALE, PRO_SINGLE, PRO_THIRD, PRO_ANIMATE),
	"she": (PRO_FEMALE, PRO_SINGLE, PRO_THIRD, PRO_ANIMATE),
	"he": (PRO_MALE, PRO_SINGLE, PRO_THIRD, PRO_ANIMATE),
	"him": (PRO_MALE, PRO_SINGLE, PRO_THIRD, PRO_ANIMATE),
	"himself": (PRO_MALE, PRO_SINGLE, PRO_THIRD, PRO_ANIMATE),
	"his": (PRO_MALE, PRO_SINGLE, PRO_THIRD, PRO_ANIMATE),
	"our": (PRO_UNKNOWN, PRO_PLURAL, PRO_FIRST, PRO_ANIMATE),
	"ours": (PRO_UNKNOWN, PRO_PLURAL, PRO_FIRST, PRO_ANIMATE),
	"yours": (PRO_UNKNOWN, PRO_SINGLE, PRO_SECOND, PRO_ANIMATE),
	"ourselves": (PRO_UNKNOWN, PRO_PLURAL, PRO_FIRST, PRO_ANIMATE),
	"yourselves": (PRO_UNKNOWN, PRO_PLURAL, PRO_SECOND, PRO_ANIMATE),
	# Canasai's comment out: "they": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_THIRD, PRO_ANIMATE), # Note, technically plural
	# Canasai's comment out: "their": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_THIRD, PRO_ANIMATE),
	# Canasai's comment out: "theirs": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_THIRD, PRO_ANIMATE),
        # Canasai's addition begin
	"they": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_ANIMATE), # Note, technically plural
	"their": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_ANIMATE),
	"theirs": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_ANIMATE),
        # Canasai's addition end
	"them": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_ANIMATE),
	"'em": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_ANIMATE),
	"em": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_ANIMATE),
	"themselves": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_ANIMATE),
	"us": (PRO_UNKNOWN, PRO_PLURAL, PRO_FIRST, PRO_ANIMATE),
	"we": (PRO_UNKNOWN, PRO_PLURAL, PRO_FIRST, PRO_ANIMATE),
	"whoever": (PRO_UNKNOWN, PRO_SINGLE, PRO_UNKNOWN, PRO_ANIMATE),
	"whomever": (PRO_UNKNOWN, PRO_SINGLE, PRO_UNKNOWN, PRO_ANIMATE),
	"whose": (PRO_UNKNOWN, PRO_SINGLE, PRO_UNKNOWN, PRO_ANIMATE),
	"i": (PRO_UNKNOWN, PRO_SINGLE, PRO_FIRST, PRO_ANIMATE),
	"me": (PRO_UNKNOWN, PRO_SINGLE, PRO_FIRST, PRO_ANIMATE),
	"mine": (PRO_UNKNOWN, PRO_SINGLE, PRO_FIRST, PRO_ANIMATE),
	"my": (PRO_UNKNOWN, PRO_SINGLE, PRO_FIRST, PRO_ANIMATE),
	"myself": (PRO_UNKNOWN, PRO_SINGLE, PRO_FIRST, PRO_ANIMATE),
	"one": (PRO_UNKNOWN, PRO_SINGLE, PRO_FIRST, PRO_ANIMATE),
	"thyself": (PRO_UNKNOWN, PRO_SINGLE, PRO_SECOND, PRO_ANIMATE),
	"ya": (PRO_UNKNOWN, PRO_SINGLE, PRO_SECOND, PRO_ANIMATE),
	"you": (PRO_UNKNOWN, PRO_SINGLE, PRO_SECOND, PRO_ANIMATE),
	"your": (PRO_UNKNOWN, PRO_SINGLE, PRO_SECOND, PRO_ANIMATE),
	"yourself": (PRO_UNKNOWN, PRO_SINGLE, PRO_SECOND, PRO_ANIMATE),
	"it": (PRO_NEUTER, PRO_SINGLE, PRO_THIRD, PRO_INANIMATE),
	"its": (PRO_NEUTER, PRO_SINGLE, PRO_THIRD, PRO_INANIMATE),
	"itself": (PRO_NEUTER, PRO_SINGLE, PRO_THIRD, PRO_INANIMATE),
	"what": (PRO_NEUTER, PRO_SINGLE, PRO_UNKNOWN, PRO_INANIMATE),
	"when": (PRO_NEUTER, PRO_SINGLE, PRO_UNKNOWN, PRO_INANIMATE),
	"where": (PRO_NEUTER, PRO_SINGLE, PRO_UNKNOWN, PRO_INANIMATE),
	"which": (PRO_NEUTER, PRO_SINGLE, PRO_UNKNOWN, PRO_INANIMATE),
	"how": (PRO_NEUTER, PRO_SINGLE, PRO_UNKNOWN, PRO_INANIMATE),

	#Canasai's comment out: "everybody": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_ANIMATE),
	#"everyone": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_ANIMATE),
	#"anybody": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_THIRD, PRO_ANIMATE),
	#"anyone": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_THIRD, PRO_ANIMATE),
	#"somebody": (PRO_UNKNOWN, PRO_SINGLE, PRO_THIRD, PRO_ANIMATE),
	#"someone": (PRO_UNKNOWN, PRO_SINGLE, PRO_THIRD, PRO_ANIMATE),
	#"nobody": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_THIRD, PRO_ANIMATE),

	#Canasai's comment out: "all": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_UNKNOWN),
	#"few": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_UNKNOWN),
	#"several": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_UNKNOWN),
	#"some": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_UNKNOWN),
	#"many": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_UNKNOWN),
	#"most": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_UNKNOWN),
	#"none": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_THIRD, PRO_UNKNOWN),
	#"noone": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_THIRD, PRO_UNKNOWN),

	"that": (PRO_UNKNOWN, PRO_SINGLE, PRO_THIRD, PRO_UNKNOWN),
	#Canasai's comment out: "this": (PRO_UNKNOWN, PRO_SINGLE, PRO_THIRD, PRO_UNKNOWN),
	#"these": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_UNKNOWN),
	#"those": (PRO_UNKNOWN, PRO_PLURAL, PRO_THIRD, PRO_UNKNOWN),

	"whatever": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_UNKNOWN, PRO_UNKNOWN),
	"who": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_UNKNOWN, PRO_ANIMATE),
	"whom": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_UNKNOWN, PRO_ANIMATE),

	#Canasai's comment out: "something": (PRO_UNKNOWN, PRO_SINGLE, PRO_UNKNOWN, PRO_INANIMATE),
	#"nothing": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_UNKNOWN, PRO_INANIMATE),
	#"everything": (PRO_UNKNOWN, PRO_UNKNOWN, PRO_UNKNOWN, PRO_INANIMATE)

###another
###any
###anything
###both
###each
###eachother
###either
###little
###more
###much
###neither
###oneanother
###other
###others
###whichever
}
# Canasai's addition end

if __name__ == '__main__':
	print "Running doctest"
	import doctest
	doctest.testmod()

