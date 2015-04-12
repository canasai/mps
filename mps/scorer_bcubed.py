import logging
import os
import sys

from collections import defaultdict

import error_analyzer as ea  
import my_constant as mc

logger = logging.getLogger(__name__)

def prepare_r(stat, gold_mentions, pred_mentions,
              gold_clusters, pred_clusters):
    num_rec = 0.0
    den_rec = 0.0
    for m, c_id in gold_mentions.items():
        correct = 0.0
        total = 0.0
        for m2 in gold_clusters[c_id]:
            if (m == m2 or (m in pred_mentions and m2 in pred_mentions and 
                            pred_mentions[m] == pred_mentions[m2])):
                correct += 1
            total += 1
        num_rec += (correct / total)
        den_rec += 1

    stat['num_rec'] += num_rec
    stat['den_rec'] += den_rec

def prepare_p(stat, gold_mentions, pred_mentions,
              gold_clusters, pred_clusters):
    num_pre = 0.0
    den_pre = 0.0
    for m, c_id in pred_mentions.items():
        if m not in gold_mentions and len(pred_clusters[c_id]) == 1:
            continue
        correct = 0.0
        total = 0.0
        for m2 in pred_clusters[c_id]:
            if (m == m2 or (m in gold_mentions and m2 in gold_mentions and
                            gold_mentions[m] == gold_mentions[m2])):
                correct += 1
            total += 1
        num_pre += (correct / total)
        den_pre += 1

    for m, c_id in gold_mentions.items():
        if m not in pred_mentions:
            num_pre += 1
            den_pre += 1

    stat['num_pre'] += num_pre
    stat['den_pre'] += den_pre

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

    r, p, f1 = ea.calc_rpf1(stat)
    logger.info("B-cubed scores:\n    "
                "P = %2.2lf%% (%d/%d), R = %2.2lf%% (%d/%d), F1 = %2.2lf%%"
                % ((p * 100), stat['num_pre'], stat['den_pre'],
                   (r * 100), stat['num_rec'], stat['den_rec'],
                   (f1 * 100)))

    return True

