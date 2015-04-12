import logging
import os
import sys

from collections import defaultdict

import coreference
import error_analyzer
import my_constant

logger = logging.getLogger(__name__)

def evaluate(data, eval_by_types=False):
    data_stat = {'files': 0, 'docs': 0, 'sents': 0, 'words': 0}
    stat = {'num_rec': 0.0, 'den_rec': 0.0, 'num_pre': 0.0, 'den_pre': 0.0}
    type_stat = {'name': {'num_rec': 0.0, 'den_rec': 0.0, 'num_pre': 0.0,
                          'den_pre': 0.0},
                 'nominal': {'num_rec': 0.0, 'den_rec': 0.0, 'num_pre': 0.0,
                             'den_pre': 0.0},
                 'pronoun': {'num_rec': 0.0, 'den_rec': 0.0, 'num_pre': 0.0,
                             'den_pre': 0.0}}
    for doc in data:
        data_stat['files'] += 1
        for part in data[doc]:
            sents = data[doc][part]['text']
            trees = data[doc][part]['parses']
            heads = data[doc][part]['heads']
            gold = data[doc][part]['mentions']
            for i in xrange(len(sents)):
                data_stat['words'] += len(sents[i])
            data_stat['docs'] += 1
            data_stat['sents'] += len(sents)

            for m in data[doc][part]['pred_mentions']:
                    stat['den_pre'] +=  1
                    mtype = coreference.mention_type(m, sents, trees, heads)
                    type_stat[mtype]['den_pre'] += 1
                    if m in gold:
                        type_stat[mtype]['num_pre'] += 1
                        type_stat[mtype]['num_rec'] += 1
                        stat['num_pre'] += 1
                        stat['num_rec'] += 1

            for g in gold:                    
                mtype = coreference.mention_type(g, sents, trees, heads)
                type_stat[mtype]['den_rec'] += 1
                stat['den_rec'] += 1

    r, p, f1 = error_analyzer.calc_rpf1(stat) 
    logger.info("Data statistics:\n    "
                "files = %d, docs = %d, sentences = %d, words = %d" % (
                data_stat['files'], data_stat['docs'],
                data_stat['sents'], data_stat['words']))

    if eval_by_types:
        print_rpf1_by_types(type_stat, stat)

    logger.info("Performance of mention detection:\n    "
                "P = %2.2lf%% (%d/%d), R = %2.2lf%% (%d/%d), F1 = %2.2lf%%"
                % ((p * 100), stat['num_pre'], stat['den_pre'],
                   (r * 100), stat['num_rec'], stat['den_rec'],
                   (f1 * 100)))

    return True

def print_rpf1_by_types(type_stat, stat):
    sum_num_pre = (type_stat['name']['num_pre'] +
                   type_stat['nominal']['num_pre'] +
                   type_stat['pronoun']['num_pre'])
    if stat['num_pre'] != sum_num_pre:
        logger.error("Inconsistent value 'num_pre': %d != %d"
                     % (stat['num_pre'], sum_num_pre))
        sys.exit(1)

    logger.info("Performance of mention detection by types:")
    logger.info("{:10}{:25}{:25}{:10}".format('', 'R', 'P', 'F1'))
    for mtype in my_constant.MTYPES:
        r, p, f1 = error_analyzer.calc_rpf1(type_stat[mtype])
        r_ = "%2.2lf%% (%d/%d)" % ((r * 100), stat['num_rec'], stat['den_rec'])
        p_ = "%2.2lf%% (%d/%d)" % ((p * 100), stat['num_pre'], stat['den_pre'])
        f1_ = "%2.2lf%%" % (f1 * 100)
        logger.info("{:10}{:25}{:25}{:10}".format(mtype, r_, p_, f1_))

    return True
