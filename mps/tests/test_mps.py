import json
import logging
import logging.config
import os
import sys
import types
import unittest

from collections import defaultdict

from .. import conll
from .. import coreference
from .. import coref_resolver
from .. import coref_rules
from .. import dictionaries
from .. import mention_detector
from .. import post_processing
from .. import logging_config

class TestCase(unittest.TestCase):

    def write_docs(self):
        self.assertTrue(conll.write(self.data, config['general']['output']))

    def evaluate_coref(self):
        self.assertTrue(coref_resolver.evaluate(self.data,
                                                config['evaluation'],
                                                config['tracking']))

    def evaluate_extracted_mentions(self):
        self.assertTrue(mention_detector.evaluate(self.data,
                                                  config['evaluation'],
                                                  config['tracking']))

    def do_post_processing(self):
        self.assertTrue(post_processing.do(self.data,
                                           config['post_processing']))

    def try_coref(self):
        self.assertTrue(
            coref_resolver.try_coref(
                self.data, config['passes'], config['params']))

    def check_ordered_mentions(self):
        # Check all mentions are in tree-traversal order
        data = self.data
        for doc in data:
            for part in data[doc]:
                sents = data[doc][part]['text']
                trees = data[doc][part]['parses']
                heads = data[doc][part]['heads']
                for i in xrange(len(sents)):
                    sent_ments = data[doc][part]['doc_mentions'][i]
                    idx = 0
                    tree_order = {}
                    for node in trees[i]:
                        tree_order[node.span] = idx
                        idx += 1
                    prev_idx = -1
                    for ment in sent_ments:
                        self.assertEqual(ment[0], i)
                        span = (ment[1], ment[2])
                        idx = -1
                        if span in tree_order:
                            idx = tree_order[span]
                        else:
                            head_span, head_word, head_pos = \
                                coreference.mention_head(
                                    ment, sents, trees, heads)
                            idx = tree_order[head_span]
                        self.assertGreaterEqual(idx, prev_idx)
                        prev_idx = idx

    def extract_all_mentions(self):
        mention_detector.extract_all_mentions(self.data, config['params'])
        mention_detector.count_non_constituent_names(self.data)

    def check_data(self):
        data = self.data
        for doc in data:
            for part in data[doc]: 
                sents = data[doc][part]['text']
                trees = data[doc][part]['parses']
                heads = data[doc][part]['heads']
                for s_i in xrange(len(sents)):
                    self.assertEqual(type(sents[s_i]), types.ListType)
                    self.assertEqual(type(trees[s_i]), types.InstanceType)
                    self.assertEqual(type(heads[s_i]), types.DictType)
                names = data[doc][part]['ner']
                mentions = data[doc][part]['mentions']
                clusters = data[doc][part]['clusters']
                speakers = data[doc][part]['speakers']
                self.assertEqual(type(names), types.DictType)
                self.assertEqual(type(mentions), types.DictType)
                self.assertEqual(type(clusters), defaultdict)
                self.assertEqual(type(speakers), defaultdict)

    def load_data(self):
        self.data = conll.load_data(config['general']['data_dir'],
                                    config['general']['suffix'])
        self.assertNotEqual(0, len(self.data))

    def load_dict(self):
        self.assertTrue(dictionaries.init(config['dict_files']))

    def verify_passes(self):
        self.assertTrue(coref_rules.verify_passes(config['passes']))

    def runTest(self):
        self.verify_passes()
        self.load_dict()
        self.load_data()
        self.check_data()
        self.extract_all_mentions()
        self.check_ordered_mentions()
        self.try_coref()
        self.do_post_processing()
        self.evaluate_extracted_mentions()
        self.evaluate_coref()
        self.write_docs()

if __name__ == '__main__':
    logging.config.dictConfig(logging_config.LOGGING)
    MY_ARGS = sys.argv[1:]
    del sys.argv[1:]
    config = json.load(open(MY_ARGS[0]))
    unittest.main()
