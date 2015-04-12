import logging
import os
import sys

from collections import defaultdict

import error_analyzer as ea  
import my_constant as mc

logger = logging.getLogger(__name__)

def prepare_r(stat, gold_mentions, pred_mentions,
              gold_clusters, pred_clusters):
    correct_links = 0.0
    total_links = 0.0
    for id, cluster in gold_clusters.items():
        cluster_size = len(cluster)
        if cluster_size == 0:
            continue
        total_links += (cluster_size - 1)    
        correct_links += cluster_size
        partition_idx = {}
        for m in cluster:
            if m not in pred_mentions:
                correct_links -= 1
            else:
                partition_idx[pred_mentions[m]] = True
        correct_links -= len(partition_idx)

    if total_links != len(gold_mentions) - len (gold_clusters):
        logger.error("Inconsistent value 'total_links': %d != %d"
                     % (total_links, len(gold_mentions) - len(gold_clusters)))
        sys.exit(1)

    stat['num_rec'] += correct_links
    stat['den_rec'] += total_links

def prepare_p(stat, gold_mentions, pred_mentions,
              gold_clusters, pred_clusters):
    correct_links = 0.0
    total_links = 0.0
    for id, cluster in pred_clusters.items():
        cluster_size = len(cluster)
        if cluster_size == 0:
            continue
        total_links += (cluster_size - 1)
        correct_links += cluster_size
        partition_idx = {}
        for m in cluster:
            if m not in gold_mentions:
                correct_links -= 1
            else:
                partition_idx[gold_mentions[m]] = True
        correct_links -= len(partition_idx)

    if total_links != len(pred_mentions) - len(pred_clusters):
        logger.error("Inconsistent value 'total_links': %d != %d"
                     % (total_links, len(pred_mentions) - len(pred_clusters)))
        sys.exit(1)

    stat['num_pre'] += correct_links
    stat['den_pre'] += total_links

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
    logger.info("MUC scores:\n    "
                "P = %2.2lf%% (%d/%d), R = %2.2lf%% (%d/%d), F1 = %2.2lf%%"
                % ((p * 100), stat['num_pre'], stat['den_pre'],
                   (r * 100), stat['num_rec'], stat['den_rec'],
                   (f1 * 100)))

    return True

