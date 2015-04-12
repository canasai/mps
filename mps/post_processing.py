import logging

logger = logging.getLogger(__name__)

def remove_singletons(pred_ments, pred_clusts):
    ids_to_remove = {}
    for id, cluster in pred_clusts.items():
        if len(cluster) == 1:
            pred_ments.pop(cluster[0])
            ids_to_remove[id] = True

    c = 0
    for id in ids_to_remove.keys():
        pred_clusts.pop(id)
        c += 1

def get_larger(m, n):
    if m[0] == n[0]:
        if m[1] <= n[1] and n[2] <= m[2]:
            return True

    return False

def remove_nested_mentions(pred_ments, pred_clusts, ment_attr):
    for id, cluster in pred_clusts.items():
        cluster_size = len(cluster)
        ments_to_remove = {}
        for i in xrange(cluster_size):
            for j in xrange(0, i):
                m = cluster[i]
                n = cluster[j]
                # Same cluster, sentence, head
                if (m != n and
                    m[0] == n[0] and
                    ment_attr[m]['head_idx'] == ment_attr[n]['head_idx']):
                    if m[1] <= n[1] and n[2] <= m[2]:
                        ments_to_remove[n] = True
                    elif n[1] <= m[1] and m[2] <= n[2]:
                        ments_to_remove[m] = True
                    else:
                        logger.warn("Found a non-overlapping pattern")

        for ment in ments_to_remove:
            pred_clusts[id].remove(ment)
            pred_ments.pop(ment)

def do(data, params):
    logger.info("Do post processing")
    for doc in data:
        for part in data[doc]:
            logger.info("    document (%s); part %s" % (doc, part))
            if params['remove_nested_mentions']:
                logger.info("        Remove nested mentions")
                remove_nested_mentions(
                    data[doc][part]['pred_mentions'],
                    data[doc][part]['pred_clusters'],
                    data[doc][part]['ment_attr'])

            if params['remove_singletons']:
                logger.info("        Remove singletons")
                remove_singletons(
                    data[doc][part]['pred_mentions'],
                    data[doc][part]['pred_clusters'])

    return True
