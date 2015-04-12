import logging
import math
import os
import sys

from collections import defaultdict

import coreference as coref
import dictionaries
import my_constant

logger = logging.getLogger(__name__)

def has_pronoun_property(ment, ment_attr):
    if ment_attr[ment]['type'] == my_constant.MAP_MTYPES['pronoun']:
        return True 
    else:
        return False

def exact_match(ment, ant, m_cluster, a_cluster, ment_attr):
    for m in m_cluster:
        if has_pronoun_property(m, ment_attr):
            continue 

        for a in a_cluster:
            if has_pronoun_property(a, ment_attr):
                continue 
            if ment_attr[m]['surface'] == ment_attr[a]['surface']:
                return True
            if (ment_attr[m]['surface'] == ment_attr[a]['surface'] + " 's" or
                ment_attr[a]['surface'] == ment_attr[m]['surface'] + " 's"):
                return True

    return False

def relaxed_exact_match(ment, ant, m_cluster, a_cluster, ment_attr):
    if (has_pronoun_property(ment, ment_attr) or
        has_pronoun_property(ant, ment_attr)):
        return False

    if ment_attr[ment]['relaxed_surface'] == ment_attr[ant]['relaxed_surface']:
        return True

    if (ment_attr[ment]['relaxed_surface'] == 
        ment_attr[ant]['relaxed_surface'] + " 's" or
        ment_attr[ant]['relaxed_surface'] == 
        ment_attr[ment]['relaxed_surface'] + " 's"):
        return True

    return False

def cluster_head_match(ment, ant, m_cluster, a_cluster, ment_attr):
    if (has_pronoun_property(ment, ment_attr) or
        has_pronoun_property(ant, ment_attr)):
        return False

    for a in a_cluster:
        if ment_attr[ment]['head_word'] == ment_attr[a]['head_word']:
            return True
        
    return False

def relaxed_head_match(ment, ant, m_cluster, a_cluster, ment_attr):
    if (has_pronoun_property(ment, ment_attr) or
        has_pronoun_property(ant, ment_attr)):
        return False

    if (ment_attr[ment]['ner'] != 'O' and
        ment_attr[ant]['ner'] != 'O' and
        ment_attr[ment]['ner'] == ment_attr[ant]['ner']):
        if (ment_attr[ment]['head_word'] in ment_attr[ant]['word_list'] or
            ment_attr[ant]['head_word'] in ment_attr[ment]['word_list']):
                return True

    return False

def word_inclusion(ment, ant, m_cluster, a_cluster, ment_attr):
    a_set = set()
    for a in a_cluster:
        a_set.update(ment_attr[a]['word_list'])

    m_set = set()
    for m in m_cluster:
        for word in ment_attr[m]['word_list']:
            if word not in dictionaries.words_to_exclude:
                m_set.add(word)

    if m_set.issubset(a_set):
        return True
    
    return False

def compatible_modifiers(ment, ant, m_cluster, a_cluster, ment_attr):
    if not ment_attr[ment]['modifiers'].issubset(ment_attr[ant]['word_list']):
        return False

    for l in dictionaries.location_modifiers:
        if (l in ment_attr[ant]['modifiers'] and
            l not in ment_attr[ment]['modifiers']):
            return False

    return True

def inside(ment, ant):
    if ment[0] == ant[0]:
        if ment[1] <= ant[1] and ant[2] <= ment[2]:
            return True

    return False

def iwithini(ment, ant, m_cluster, a_cluster, ment_attr):
    for m in m_cluster:
        for a in a_cluster:
            if inside(m, a) or inside(a, m):
               return False

    return True

def is_compatible(mention, any_cluster, ment_attr):
    for a in any_cluster:
        a_prop = ment_attr[a]['properties']
        m_prop = ment_attr[mention]['properties']

        if (m_prop[coref.Property.number] != 0 and
            a_prop[coref.Property.number] != 0 and
            m_prop[coref.Property.number] != a_prop[coref.Property.number]):
            return False
            
        if (m_prop[coref.Property.gender] != 0 and
            a_prop[coref.Property.gender] != 0 and
            m_prop[coref.Property.gender] != a_prop[coref.Property.gender]):
            return False
            
        if (m_prop[coref.Property.animacy] != 0 and
            a_prop[coref.Property.animacy] != 0 and
            m_prop[coref.Property.animacy] != a_prop[coref.Property.animacy]):
            return False

        if (ment_attr[a]['ner'] != 'O' and
            ment_attr[mention]['ner'] != 'O' and 
            ment_attr[a]['ner'] != ment_attr[mention]['ner']):
            return False

    return True

def compatible_properties(ment, ant, m_cluster, a_cluster, ment_attr):
    if not (is_compatible(ment, a_cluster, ment_attr) and
            is_compatible(ant, m_cluster, ment_attr)):
        return False

    return True

def is_third_person(ment, ment_attr):
    if not (ment_attr[ment]['properties'][coref.Property.person]
            == coref.PRO_FIRST
            or ment_attr[ment]['properties'][coref.Property.person]
            == coref.PRO_SECOND):
        return True
    else:
        return False

def is_second_person(ment, ment_attr):
    if ment_attr[ment]['properties'][coref.Property.person] == \
       coref.PRO_SECOND:
        return True
    else:
        return False

def is_first_person(ment, ment_attr):
    if ment_attr[ment]['properties'][coref.Property.person] == coref.PRO_FIRST:
        return True
    else:
        return False

def is_pronoun(ment, ment_attr):
    if (ment[2] - ment[1] == 1 and 
        ment_attr[ment]['head_word'] in coref.pronoun_properties and
        ment_attr[ment]['head_pos'] in {'PRP', 'PRP$'}):
        return True 
    else:
        return False

def skip_pronoun_match(ment, ant, ment_attr):
    if not is_pronoun(ment, ment_attr):
        return True 

    if is_third_person(ment, ment_attr):
        if abs(ment[0] - ant[0]) > 3:
            return True

    if ment_attr[ment]['pleonastic'] or ment_attr[ant]['pleonastic']:
        return True 

    if ment_attr[ment]['speaker'] == ment_attr[ant]['speaker']:
        if (not is_pronoun(ant, ment_attr) and
            (is_first_person(ment, ment_attr) or
             is_second_person(ment, ment_attr))):
            return True 
        m_prop = ment_attr[ment]['properties']
        a_prop = ment_attr[ant]['properties']
        if (m_prop[coref.Property.person] != coref.PRO_UNKNOWN and
            a_prop[coref.Property.person] != coref.PRO_UNKNOWN and
            m_prop[coref.Property.person] != a_prop[coref.Property.person]):
            return True

    return False

def pronoun_match(ment, ant, m_cluster, a_cluster, ment_attr):
    if skip_pronoun_match(ment, ant, ment_attr):
       return False

    return True

def make_pair(id1, id2):
    return (min(id1, id2), max(id1, id2))

def skip_pair(rment, ment, ant, ment_cluster_id, ant_cluster_id,
              m_cluster, a_cluster, ment_attr, incompatible_clusters):
    if ment_cluster_id == ant_cluster_id: 
        return True 

    if inside(rment, ant) or inside(ant, rment):
        return True

    cluster_id_pair = make_pair(ment_cluster_id, ant_cluster_id)
    if (incompatible_clusters is not None and
        cluster_id_pair in incompatible_clusters):
        return True 

def is_coref(rules, rment, ment, ant, ment_attr, pred_ments,
             pred_clusts, incompatible_clusters):
    ment_cluster_id = pred_ments[rment]
    ant_cluster_id = pred_ments[ant]
    m_cluster = pred_clusts[ment_cluster_id]
    a_cluster = pred_clusts[ant_cluster_id]

    if ment_attr[ment]['surface'] == 'this' and abs(ment[0] - ant[0]) > 3:
        return False

    if skip_pair(rment, ment, ant, ment_cluster_id, ant_cluster_id, 
                 m_cluster, a_cluster, ment_attr, incompatible_clusters):
        return False

    for i in xrange(len(rules)):
        if rules[i] == 'pronoun_match':
            rment = ment # Use original mention for pronoun
        if (not globals()[rules[i]](rment, ant, m_cluster, a_cluster,
                                    ment_attr)):
            cluster_id_pair = make_pair(ment_cluster_id, ant_cluster_id)
            incompatible_clusters[cluster_id_pair] = True
            return False

    return  True

def verify_passes(passes):
    for i in xrange(len(passes)):
        for r in passes[str(i)]['rules']:
            if r not in my_constant.RULE_NAMES:
                logger.error("Cannot recognize rule name '%s'" % r)
                sys.exit(1)
            logger.info("Add pass %d: [%s]" % (i, r))

    return True
