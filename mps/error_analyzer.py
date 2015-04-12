import logging
import os
import sys

from collections import defaultdict

import coreference as coref
import coreference_rendering as coref_rendering
import my_constant

logger = logging.getLogger(__name__)

def calc_rpf1(stat):
    r = 0.0
    if stat['den_rec'] != 0:
        r = stat['num_rec'] / stat['den_rec']
    p = 0.0
    if stat['den_pre'] != 0:
        p = stat['num_pre'] / stat['den_pre']
    f1 = 0.0
    if p + r != 0.0:
        f1 = (2 * p * r) / (p + r)

    return r, p, f1

def print_missing_gold_mentions(data):
    out = open('missing_gold_mentions.log', 'w')
    order = []
    for doc in data:
        for part in data[doc]:
            order.append((doc, part))
    order.sort()
    for doc, part in order:
        sents = data[doc][part]['text']
        trees = data[doc][part]['parses']
        names = data[doc][part]['ner']
        gold_mentions = data[doc][part]['mentions']
        doc_mentions = data[doc][part]['doc_mentions']
        print >> out, "# %s %s\n" % (doc, part)
        num_missing = 0
        num_not_con = 0

        pred = {}
        for ments in doc_mentions:
            for m in ments: 
                pred[m] = True

        gold = [g for g in gold_mentions]
        gold.sort() 
        for g in gold:
            if g not in pred:
                num_missing += 1
                node = trees[g[0]].get_nodes('lowest', g[1], g[2])
                con = 1
                if node is None:
                    num_not_con += 1
                    con = 0
                ner = 1
                if g not in names:
                    ner = 0
                print >> out, "%s\t%d\t%d\t%s" % (g, con, ner,
                    coref.mention_text(g, sents))

        if num_missing > 0:
            print >> out, "\n#missing mentions = %d" % num_missing,
            print >> out, "(%d are not constituents)\n" % num_not_con

    return True

def print_cluster_errors(data):
    cluster_errors = open('cluster_errors.log', 'w')
    cluster_context = open('cluster_context.log', 'w')
    cluster_missing = open('cluster_missing.log', 'w')
    cluster_extra = open('cluster_extra.log', 'w')
    mention_list = open('mention_list.log', 'w')
    mention_text = open('mention_text.log', 'w')
    order = []
    for doc in data:
        for part in data[doc]:
            order.append((doc, part))

    order.sort()
    for doc, part in order:
        print >> cluster_errors, "# %s %s\n" % (doc, part)
        print >> cluster_context, "# %s %s\n" % (doc, part)
        print >> cluster_missing, "# %s %s\n" % (doc, part)
        print >> cluster_extra, "# %s %s\n" % (doc, part)
        print >> mention_list, "# %s %s\n" % (doc, part)
        print >> mention_text, "# %s %s\n" % (doc, part)
        pred_mentions = data[doc][part]['pred_mentions']
        pred_clusters = data[doc][part]['pred_clusters']
        gold_mentions = data[doc][part]['mentions']
        gold_clusters = data[doc][part]['clusters']
        sents = data[doc][part]['text']
        trees = data[doc][part]['parses']
        heads = data[doc][part]['heads']

        gold_cluster_set = coref.set_of_clusters(gold_clusters)
        pred_cluster_set = coref.set_of_clusters(pred_clusters)
        gold_mention_set = coref.set_of_mentions(gold_clusters)
        pred_mention_set = coref.set_of_mentions(pred_clusters)

        groups = coref.confusion_groups(
            gold_mentions, pred_mentions,
            gold_clusters, pred_clusters)
        covered = coref_rendering.print_cluster_errors(
            groups, cluster_errors, cluster_context, sents, trees, heads,
            pred_clusters, gold_clusters, gold_mentions)
        coref_rendering.print_cluster_missing_only(
            cluster_missing, sents, gold_cluster_set,
            covered, trees, heads)
        coref_rendering.print_cluster_extra_only(
            cluster_extra, sents, pred_cluster_set, covered, trees, heads)
        coref_rendering.print_mention_list(
            mention_list, gold_mentions, pred_mention_set,
            trees, heads, sents)
        coref_rendering.print_mention_text(
            mention_text, gold_mentions, pred_mention_set,
            trees, heads, sents)

    return True

def calc_matrix(matrix, gold_mentions, pred_mentions, gold_clusters,
                pred_clusters, sents, trees, heads):
    for id, cluster in gold_clusters.items():
        cluster_size = len(cluster)
        cluster = sorted(cluster)
        for i in xrange(cluster_size):
            for j in xrange(0, i):
                type_i = coref.mention_type(cluster[i], sents, trees, heads)
                type_j = coref.mention_type(cluster[j], sents, trees, heads)
                matrix[type_i, type_j, 'total_gold_pairs'] += 1
                if (cluster[i] in pred_mentions and
                    cluster[j] in pred_mentions and
                    pred_mentions[cluster[i]] == pred_mentions[cluster[j]]):
                    matrix[type_i, type_j, 'correct_gold_pairs'] += 1

    for id, cluster in pred_clusters.items():
        cluster_size = len(cluster)
        cluster = sorted(cluster)
        for i in xrange(cluster_size):
            for j in xrange(0, i):
                type_i = coref.mention_type(cluster[i], sents, trees, heads)
                type_j = coref.mention_type(cluster[j], sents, trees, heads)
                matrix[type_i, type_j, 'total_pred_pairs'] += 1
                if (cluster[i] in gold_mentions and
                    cluster[j] in gold_mentions and
                    gold_mentions[cluster[i]] == gold_mentions[cluster[j]]):
                    matrix[type_i, type_j, 'correct_pred_pairs'] += 1
 
def coref_pairwise_by_types(data):
    matrix = defaultdict(lambda: 0.0)
    for doc in data:
        for part in data[doc]:
            sents = data[doc][part]['text']
            trees = data[doc][part]['parses']
            heads = data[doc][part]['heads']
            calc_matrix(
                matrix,
                data[doc][part]['mentions'], data[doc][part]['pred_mentions'],
                data[doc][part]['clusters'], data[doc][part]['pred_clusters'],
                sents, trees, heads)
    sum_correct_pred = 0
    sum_correct_gold = 0
    for key, val in matrix.items():
        if key[2] == 'correct_pred_pairs':
            sum_correct_pred += val
        if key[2] == 'correct_gold_pairs':
            sum_correct_gold += val

    if sum_correct_pred != sum_correct_gold:
        logger.error("Inconsistent value 'sum_correct_pred': %d != %d"
                     % (sum_correct_pred, sum_correct_gold))
        sys.exit(1)

    logger.info("Pairwise P/R/F1 by types:")
    thead = "%10s" % ' '
    for type_i in my_constant.MTYPES:
       thead += "{0:25}".format(type_i)
    logger.info(thead)
    for type_i in my_constant.MTYPES:
        trow = "{0:10}".format(type_i)
        for type_j in my_constant.MTYPES:
            stat = {'num_rec': 0.0, 'den_rec': 0.0, 'num_pre': 0.0,
                    'den_pre': 0.0}
            stat['num_pre'] = matrix[type_i, type_j, 'correct_pred_pairs']
            stat['num_rec'] = matrix[type_i, type_j, 'correct_gold_pairs']
            stat['den_pre'] = matrix[type_i, type_j, 'total_pred_pairs']
            stat['den_rec'] = matrix[type_i, type_j, 'total_gold_pairs'] 
            r, p, f1 = calc_rpf1(stat) 
            tmp = "%2.2lf/%2.2lf/%2.2lf" % (p * 100, r * 100, f1 * 100 )
            trow += "{:25}".format(tmp)
        logger.info(trow)
 
    return True
