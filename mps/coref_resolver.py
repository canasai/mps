import logging
import os
import sys

from collections import defaultdict

import coreference as coref
import coref_rules
import coref_scorer
import dictionaries
import error_analyzer
import mention_attributes
import my_constant

logger = logging.getLogger(__name__)

def evaluate(data, eval_, tracking):
    logger.info("Performance of coreference resolution:")

    if tracking['coref_pairwise_by_types']:
        error_analyzer.coref_pairwise_by_types(data)

    if eval_['coref_pairwise']:
       coref_scorer.calc_pairwise(data)

    if eval_['coref_muc']:
       coref_scorer.calc_muc(data)

    if eval_['coref_bcubed']:
       coref_scorer.calc_bcubed(data)

    if tracking['cluster_errors']:
        error_analyzer.print_cluster_errors(data)

    return True

def merge_clusters(mention, antecedent, pred_ments, pred_clusts):
    m_cluster_id = pred_ments[mention]
    a_cluster_id = pred_ments[antecedent]
    for ment in pred_clusts[m_cluster_id]:
        pred_ments[ment] = a_cluster_id
        pred_clusts[a_cluster_id].append(ment)
    pred_clusts.pop(m_cluster_id)

def is_more_representative(m, n, ment_attr):
    # Larger span
    if ment_attr[m]['head_idx'] - m[0] > ment_attr[n]['head_idx'] - n[0]:
        return True
    else:    
        return False

    #  Earlier sentence
    if m[0] < n[0]:
        return True
    else:   
        return False

    # Earlier head
    if m[0] == n[0] and ment_attr[m]['head_idx'] < ment_attr[n]['head_idx']:
        return True
    else:    
        return False

    # Short mentions, take longer
    if (len(ment_attr[m]['word_list']) <= 5 and
        len(ment_attr[m]['word_list']) > len(ment_attr[n]['word_list'])):
        return True
    else:    
        return False

    # Long mentions, take shorter
    if len(ment_attr[m]['word_list']) < len(ment_attr[n]['word_list']):
        return True
    else:    
        return False

def get_representative_mention(ment, ment_attr, pred_ments, pred_clusts):
    cluster = pred_clusts[pred_ments[ment]]
    cluster_size = len(cluster)
    if cluster_size == 1:
        return ment

    rment = None 
    for i in xrange(cluster_size):
        m = cluster[i]
        if rment == None:
            rment = m
        if is_more_representative(m, rment, ment_attr):
            rment = m
        
    if rment == None:
        logger.error("Can not find a representative mention")
        sys.exit(1)

    return rment

def swap(l, ment_attr):
    # Example
    # (3, 0, 7)      Prince Charles and his new wife Camilla
    # (3, 0, 2)      Prince Charles
    # [(3, 0, 7), (3, 0, 2)] -> [(3, 0, 2), (3, 0, 7)]
    for i in xrange(0, len(l)):
        for j in xrange(i + 1, len(l)):
            if (ment_attr[l[i]]['head_word'] == \
                ment_attr[l[j]]['head_word'] and
                l[i][0] == l[j][0] and # same sentence
                l[i][1] == l[j][1] and # same position
                len(ment_attr[l[i]]['surface']) > \
                len(ment_attr[l[j]]['surface'])): # shorter first
                l[j], l[i] = l[i], l[j] 
    return l

def sort_mentions_for_pronoun(ment, ant_list, ment_attr, sents, trees, heads):
    head_span, head_word, head_pos = \
        coref.mention_head(ment, sents, trees, heads)
    node = trees[ment[0]].get_nodes('lowest', head_span[0], head_span[1])
    if node is None:
        return ant_list
    tree = node
    nodes_to_keep = {}
    idx = 0
    while tree is not None:
        if tree.label.startswith('S') or tree.parent is None:
            for a in ant_list:
                if (a not in nodes_to_keep and
                    tree.span[0] <= a[1] and a[2] <= tree.span[1]):
                    nodes_to_keep[a] = idx
                    idx += 1 
        tree = tree.parent

    sorted_ant_list =  [x[0] for x in \
        sorted(nodes_to_keep.items(), key=lambda x: x[1])]
    if len(sorted_ant_list) != len(ant_list):
        logger.error("Inconsistent size 'ant_list': %d != %d" %
                     (len(sorted_ant_list), len(ant_list)))
        sys.exit(1)

    return sorted_ant_list

def sub_mention_list(mentions, ment):
    sub = []
    for m in mentions:
        if m[2] <= ment[1]:
            sub.append(m)
    return sub

def get_candidate_antecedents(ment, s_i, s_j, doc_ments, ment_attr,
                              sents, trees, heads):
    if s_i == s_j: # same sentence
        ant_list = sub_mention_list(doc_ments[s_i], ment)
        if ment_attr[ment]['type'] == my_constant.MAP_MTYPES['pronoun']:
            return sort_mentions_for_pronoun(ment, ant_list, ment_attr,
                                             sents, trees, heads)
        else:
            return ant_list
    else: 
        return doc_ments[s_j]

def try_sent_coref(ment, s_i, pass_, doc_ments, ment_attr, sents, trees, heads,
                   pred_ments, pred_clusts, params, incompatible_clusters):
    for s_j in range(s_i, -1, -1):
        if (abs(s_i - s_j) > params['max_sent_dist'] and
            params['max_sent_dist'] != -1):
            return False
        ants = get_candidate_antecedents(ment, s_i, s_j, doc_ments,
                                         ment_attr, sents, trees, heads)
        ants = swap(ants, ment_attr)
        rment = get_representative_mention(ment, ment_attr,
                                           pred_ments, pred_clusts)
        for ant in ants:
            if coref_rules.is_coref(
                   pass_['rules'], rment, ment, ant, ment_attr,
                   pred_ments, pred_clusts, incompatible_clusters):
                merge_clusters(ment, ant, pred_ments, pred_clusts)
                return True # Break inner and outer loops

    return False

def start_with_indefinite_article(ment, attr):
    if attr['first_word'] in {'a', 'an'}:
        return True

    return False

def start_with_indefinite_pronoun(ment, attr):
    if attr['first_word'] in dictionaries.indefinite_pronouns:
        return True

    return False

def is_bare_plural(ment, attr):
    if (attr['head_pos'] == 'NNS' and
        (ment[2] - ment[1] == 1 or attr['first_pos'] in {'JJ', 'RB'})):
        return True
    else:
        return False

def skip_antecedent_search(ment, ment_attr, pred_ments, pred_clusts, params):
    if len(pred_clusts[pred_ments[ment]]) > 1:
        return False

    attr = ment_attr[ment]
    if params['skip_disagreed_parse_ne'] and attr['disagreed_parse_ne']:
        return True

    if params['skip_bare_plurals'] and is_bare_plural(ment, attr):
        return True

    if (params['skip_indefinite_pronoun'] and
        start_with_indefinite_pronoun(ment, attr)):
        return True

    if (params['skip_indefinite_article'] and
        start_with_indefinite_article(ment, attr)):
        return True

    return False

def try_doc_coref(pass_, doc_ments, ment_attr, sents, trees, heads,
                  pred_ments, pred_clusts, params, ):
    incompatible_clusters = {} # Reset when starting new pass
    for i in xrange(len(doc_ments)):
        for ment in doc_ments[i]:
            if skip_antecedent_search(ment, ment_attr, pred_ments,
                                      pred_clusts, params):
                continue
            try_sent_coref(
                ment, i, pass_, doc_ments, ment_attr, sents, trees, heads,
                pred_ments, pred_clusts, params, incompatible_clusters)

def init_pred_clusters(pred_ments):
    clusters = defaultdict(lambda: [])
    for span, id in pred_ments.items():
        clusters[id].append(span)

    return clusters

def init_pred_mentions(doc_ments):
    mentions = {}
    id = 0
    for sent_ments in doc_ments:
        for ment in sent_ments:
           mentions[ment] = id
           id += 1

    return mentions

def try_coref(data, passes, params):
    logger.info("Coreference resolution")
    for doc in data:
        for part in data[doc]:
            logger.info("    document (%s); part %s" % (doc, part))
            sents = data[doc][part]['text']
            trees = data[doc][part]['parses']
            heads = data[doc][part]['heads']
            sner = data[doc][part]['sner']
            speakers = data[doc][part]['speakers']
            doc_ments = data[doc][part]['doc_mentions']
            doc_incompatible_clusters = {}
            pred_ments = init_pred_mentions(doc_ments)
            pred_clusts = init_pred_clusters(pred_ments)
            ment_attr = mention_attributes.init(
                doc_ments, sents, trees, heads, sner, speakers)
            for i in xrange(len(passes)):
                try_doc_coref(
                    passes[str(i)], doc_ments, ment_attr, sents, trees,
                    heads, pred_ments, pred_clusts, params)
            data[doc][part]['pred_mentions'] = pred_ments
            data[doc][part]['pred_clusters'] = pred_clusts
            data[doc][part]['ment_attr'] = ment_attr

    return True
