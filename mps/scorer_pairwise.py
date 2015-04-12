import logging
import os
import sys

from collections import defaultdict

import error_analyzer as ea  
import my_constant as mc

logger = logging.getLogger(__name__)

def prepare_r(stat, gold_mentions, pred_mentions,
              gold_clusters, pred_clusters):
    correct_pairs = 0.0
    total_pairs = 0.0
    for id, cluster in gold_clusters.items():
        cluster_size = len(cluster)
        total_pairs += cluster_size * (cluster_size - 1) / 2
        for i in xrange(cluster_size):
            if cluster[i] not in pred_mentions:
                continue
            for j in xrange(0, i):
                if cluster[j] not in pred_mentions:
                    continue
                if pred_mentions[cluster[i]] == pred_mentions[cluster[j]]:
                    correct_pairs += 1

    stat['num_rec'] += correct_pairs 
    stat['den_rec'] += total_pairs

def prepare_p(stat, gold_mentions, pred_mentions,
              gold_clusters, pred_clusters):
    correct_pairs = 0.0
    total_pairs = 0.0
    for id, cluster in pred_clusters.items():
        cluster_size = len(cluster)
        total_pairs += cluster_size * (cluster_size - 1) / 2
        for i in xrange(cluster_size):
            if cluster[i] not in gold_mentions:
                continue
            for j in xrange(0, i):
                if cluster[j] not in gold_mentions:
                    continue
                if gold_mentions[cluster[i]] == gold_mentions[cluster[j]]:
                    correct_pairs += 1

    stat['num_pre'] += correct_pairs 
    stat['den_pre'] += total_pairs

def calc_rpf1(data):
    stat = {'num_rec': 0.0, 'den_rec': 0.0, 'num_pre': 0.0, 'den_pre': 0.0}
    for doc in data:
        for part in data[doc]:
            prepare_r(stat,
                      data[doc][part]['mentions'],
                      data[doc][part]['pred_mentions'],
                      data[doc][part]['clusters'],
                      data[doc][part]['pred_clusters'])
            prepare_p(stat,
                      data[doc][part]['mentions'],
                      data[doc][part]['pred_mentions'],
                      data[doc][part]['clusters'],
                      data[doc][part]['pred_clusters'])

    if stat['num_pre'] != stat['num_rec']:
        logger.error("Inconsistent value 'num_pre': %d != %d"
                     % (stat['num_pre'], stat['num_rec']))
        sys.exit(1)

    r, p, f1 = ea.calc_rpf1(stat)
    logger.info("Pairwise scores:\n    "
                "P = %2.2lf%% (%d/%d), R = %2.2lf%% (%d/%d), F1 = %2.2lf%%"
                % ((p * 100), stat['num_pre'], stat['den_pre'],
                   (r * 100), stat['num_rec'], stat['den_rec'],
                   (f1 * 100)))

    return True

