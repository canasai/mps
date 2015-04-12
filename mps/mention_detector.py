import logging
import os
import sys

from collections import defaultdict

import coreference as coref
import dictionaries
import mention_scorer
import my_constant
import error_analyzer

logger = logging.getLogger(__name__)

def evaluate(data, eval_, tracking):
    if eval_['mention_detection']:
        if tracking['missing_gold_mentions']:
            error_analyzer.print_missing_gold_mentions(data)
        mention_scorer.evaluate(data, tracking['mention_detection_by_types'])

    return True

def count_non_constituent_names(data):
    count = 0
    count_all = 0
    for doc in data:
        for part in data[doc]:
            sents = data[doc][part]['text']
            trees = data[doc][part]['parses']
            heads = data[doc][part]['heads']
            sner = split_named_entities_by_sentence(data[doc][part]['ner'],
                                                    sents)
            for i in sner.keys():
                count_all += len(sner[i])
                for n in sner[i]:
                    found = False
                    for node in trees[i]:
                        if node.span[0] == n[1] and node.span[1] == n[2]:
                            found = True
                            break
                    if not found:
                        count += 1

    if count_all == 0:
        logger.warn("Cannot find any name in data")

    if count > 0:
        percent = (100.0 * count) / count_all
        logger.info("Summary: %.2f%% (%d/%d) are not constituents" %
                    (percent, count, count_all))

    return True

def evaluate(data, eval_, tracking):
    if eval_['mention_detection']:
        if tracking['missing_gold_mentions']:
            error_analyzer.print_missing_gold_mentions(data)
        mention_scorer.evaluate(data, tracking['mention_detection_by_types'])

    return True

def sort_by_tree_traversal_order(nodes_to_keep, tree_order,
                                 sents, trees, heads):
    for node in nodes_to_keep.keys():
        span =  (node[1], node[2])
        if span in tree_order:
            nodes_to_keep[node] = tree_order[span]
        else:
            head_span, head_word, head_pos = \
                coref.mention_head(node, sents, trees, heads)
            if head_span in tree_order:
                nodes_to_keep[node] = tree_order[head_span]
            else:
                logger.error("Cannot find node '(%d, %d, %d)' in tree" %
                             (node[0], node[1], node[2]))
                sys.exit(1)

    return [x[0] for x in sorted(nodes_to_keep.items(), key=lambda x: x[1])]

def end_with_stop_suffixes(string):
    for p in dictionaries.stop_suffixes:
        if string.endswith(p):
            return True

    return False

def start_with_stop_prefixes(string):
    for p in dictionaries.stop_prefixes:
        if string.startswith(p):
            return True

    return False

def is_generic(ment, sents, trees, heads):
    surface_len = ment[2] - ment[1]
    head_span, head_word, head_pos = \
        coref.mention_head(ment, sents, trees, heads)
    first_span, first_word, first_pos = \
        coref.mention_head((ment[0], ment[1], ment[1] + 1),
                           sents, trees, heads)

    if (head_pos == 'NN' and head_word not in dictionaries.temporals and
        (surface_len == 1 or first_pos in {'JJ', 'RB'})):
        return True

    if first_word in dictionaries.quantifiers:
        return True

    return False

def remove_conll_spurious_mentions(ments, sents, trees, heads, sner, params):
    ments_to_remove = []
    for ment in ments.keys():
        if is_generic(ment, sents, trees, heads):
            ments_to_remove.append(ment)

        surface = coref.mention_text(ment, sents).lower()

        if (ment in sner[ment[0]] and
            sner[ment[0]][ment] == 'GPE' and
            surface in dictionaries.gpe_acronyms):
            ments_to_remove.append(ment)

        if surface in dictionaries.stop_words:
            ments_to_remove.append(ment)

        if start_with_stop_prefixes(surface):
            ments_to_remove.append(ment)

        if end_with_stop_suffixes(surface):
            ments_to_remove.append(ment)

        head_span, head_word, head_pos = \
            coref.mention_head(ment, sents, trees, heads)
        tmp = (ment[0], head_span[0], head_span[1])
        if (tmp in sner[ment[0]] and
            sner[ment[0]][tmp] in {'PERCENT', 'MONEY'}): 
            ments_to_remove.append(ment)

    for r in ments_to_remove:
        if r in ments:
            ments.pop(r)

def keep_subpatterns(nodes_to_keep, head_span, ments, largest,
                     sents, trees, heads):
    for ment in ments:
        if largest[1] == ment[1] and ment[2] == largest[2]:
            continue

        if largest[1] == ment[1] and ment[2] < largest[2]:
            tmp = (ment[0], ment[2], ment[2] + 1)
            span, word, pos = coref.mention_head(tmp, sents, trees, heads)
            if pos == ',' or pos == 'CC':
                nodes_to_keep[ment] = True

        if largest[1] < ment[1] and ment[2] == largest[2]:
            tmp = (ment[0], ment[1] - 1, ment[1])
            span, word, pos = coref.mention_head(tmp, sents, trees, heads)
            if pos == 'CC':
                nodes_to_keep[ment] = True

def find_largest_mentions(head_span, ments, sents, trees, heads):
    largest = None
    for ment in ments:
        if largest is None:
            largest = ment
        if ment[1] <= largest[1] and largest[2] <= ment[2]:
            largest = ment

    return largest

def extract_mentions_from_clusters(clusters_by_head, nodes_to_keep, sents,
                                   trees, heads, params):
    for head_span, ments in clusters_by_head.items():
        largest = find_largest_mentions(head_span, ments, sents, trees, heads)
        nodes_to_keep[largest] = True
        if params['keep_subpatterns']:
             keep_subpatterns(nodes_to_keep, head_span, ments, largest, sents,
                              trees, heads)

def inside_named_entities(ment, name_list):
    for n in name_list:
        if n[1] <= ment[1] and ment[2] <= n[2]:
            return True

    return False

def extract_parse_mentions(clusters_by_head, tree_order, i, sents, trees,
                            heads, sner):
    idx = 0
    for node in trees[i]:
        if node.label in my_constant.PARSE_TYPES_TO_KEEP:
            ment = (i, node.span[0], node.span[1])
            if not inside_named_entities(ment, sner[i]):
                head_span, head_word, head_pos = \
                    coref.mention_head(ment, sents, trees, heads)
                clusters_by_head[head_span][ment] = True
        tree_order[node.span] = idx
        idx += 1

def extract_named_entitiy_mentions(clusters_by_head, sent_idx, sents, trees,
                                   heads, sner):
    found = False
    for ment in sner[sent_idx].keys():
        head_span, head_word, head_pos = \
            coref.mention_head(ment, sents, trees, heads)
        clusters_by_head[head_span][ment] = True

def extract_sentence_mentions(sent_idx, sents, trees, heads, sner, params):
    clusters_by_head = defaultdict(lambda: {}) 
    nodes_to_keep = {}
    tree_order = {}
    extract_named_entitiy_mentions(clusters_by_head, sent_idx, sents, trees,
                                   heads, sner)
    extract_parse_mentions(clusters_by_head, tree_order, sent_idx, sents,
                           trees, heads, sner)
    extract_mentions_from_clusters(clusters_by_head, nodes_to_keep, sents,
                                   trees, heads, params)
    if params['remove_conll_spurious_mentions']:
        remove_conll_spurious_mentions(nodes_to_keep, sents, trees, heads,
                                       sner, params)

    return sort_by_tree_traversal_order(nodes_to_keep, tree_order, sents,
                                        trees, heads)

def extract_doc_mentions(doc, part, sents, trees, heads, sner, params):
    doc_ments = []
    found = False
    for i in xrange(len(sents)):
        ments = extract_sentence_mentions(i, sents, trees, heads, sner, params)
        if len(ments) > 0:
            found = True
        doc_ments.append(ments)

    if not found:
        logger.error("Cannot find any candidate mentions in document '%s:%s'" %
                     (doc, part))
        sys.exit(1)

    return doc_ments

def has_following_apostrophe(ment, sents):
    if ment[2] + 1 <= len(sents[ment[0]]):
        next_word = coref.mention_text((ment[0], ment[2], ment[2] + 1), sents)
        if next_word == "'s":
            return True

    return False

def split_named_entities_by_sentence(ner, sents):
    sner = defaultdict(lambda: {})
    for n, ne_type in ner.items():
        if ne_type not in my_constant.NE_TYPES_TO_EXCLUDE:
            if has_following_apostrophe(n, sents):
                sner[n[0]][(n[0], n[1], n[2] + 1)] = ne_type
            else:
                sner[n[0]][n] = ne_type

    return sner

def extract_all_mentions(data, params):
    logger.info("Mention detection")
    for doc in data:
        for part in data[doc]:
            logger.info("    document (%s); part %s" % (doc, part))
            sents = data[doc][part]['text']
            trees = data[doc][part]['parses']
            heads = data[doc][part]['heads']
            sner = split_named_entities_by_sentence(data[doc][part]['ner'],
                                                    sents)
            doc_ments = extract_doc_mentions(doc, part, sents, trees, heads,
                                             sner, params)
            data[doc][part]['doc_mentions'] = doc_ments
            data[doc][part]['sner'] = sner

