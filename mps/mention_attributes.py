import logging
import sys

import coreference as coref
import dictionaries
import my_constant

logger = logging.getLogger(__name__)

def is_generic_you(attr, ment, sents):
    if not (ment[2] - ment[1] == 1 and attr['head_word'] == 'you'):
        return False

    if ment[2] + 1 <= len(sents[ment[0]]):
        next_word = coref.mention_text((ment[0], ment[2], ment[2] + 1), sents)
        if next_word.lower() == 'know':
            return True

    if ment[1] - 1 >= 0:
        prev_word = coref.mention_text((ment[0], ment[1] - 1, ment[1]), sents)
        if prev_word.lower() == 'thank':
            return True

    return False

def is_pleonastic(attr, ment, sents, gold_ments=None):
    if attr['type']  != my_constant.MAP_MTYPES['pronoun']:
        return False

    if attr['surface'] == 'it':
        if ment[2] + 1 <= len(sents[ment[0]]):
            next_word = coref.mention_text((ment[0], ment[2], ment[2] + 1), sents)
            if next_word.lower() in dictionaries.pleonastic_words:
                return True

    if attr['surface'] == 'you':
        if ment[2] + 1 <= len(sents[ment[0]]):
            next_word = coref.mention_text((ment[0], ment[2], ment[2] + 1), sents)
            if next_word.lower() == 'know':
                return True
        if ment[1] - 1 >= 0:
            prev_word = coref.mention_text((ment[0], ment[1] - 1, ment[1]), sents)
            if prev_word.lower() == 'thank':
                return True

    return False

def set_speaker(attr, ment, speakers):
    attr['speaker'] = 'PER0'
    for key, val in speakers[ment[0]].items():
        if key[1] <= attr['head_idx'] and attr['head_idx'] <= key[2]:
            attr['speaker'] = val

def set_animacy(attr):
    if (attr['type'] == my_constant.MAP_MTYPES['name'] and
        attr['ner'] is not 'O'):
        ner = attr['ner']
        if ner == 'PERSON':
            return coref.PRO_ANIMATE
        elif ner == 'LOC':
            return coref.PRO_INANIMATE
        elif ner == 'MONEY':
            return  coref.PRO_INANIMATE
        elif ner == 'NUMBER':
            return coref.PRO_INANIMATE
        elif ner == 'PERCENT':
            return coref.PRO_INANIMATE
        elif ner == 'DATE':
            return coref.PRO_INANIMATE
        elif ner == 'TIME':
            return coref.PRO_INANIMATE
        elif ner.startswith('FAC'):
            return coref.PRO_INANIMATE
        elif ner.startswith('GPE'):
            return coref.PRO_INANIMATE
        elif ner.startswith('WEA'):
            return coref.PRO_INANIMATE
        elif ner.startswith('ORG'):
            return coref.PRO_INANIMATE
        else:
            return  coref.PRO_UNKNOWN
    else:
        if attr['head_word'] in dictionaries.animate_words:
            return coref.PRO_ANIMATE
        elif attr['head_word'] in dictionaries.inanimate_words:
            return coref.PRO_INANIMATE
        else:
            return  coref.PRO_UNKNOWN

def set_gender(attr):
    if attr['head_word'] in dictionaries.male_words:
        return coref.PRO_MALE
    elif attr['head_word'] in dictionaries.female_words:
        return coref.PRO_FEMALE
    else:
        return coref.PRO_UNKNOWN

def set_number(attr):
    if (attr['type'] == my_constant.MAP_MTYPES['name'] and
        attr['ner'] is not 'O'):
        if not attr['ner'].startswith('ORG'):
            return coref.PRO_SINGLE
        else:
            return coref.PRO_UNKNOWN
    else:
        if (attr['head_pos'].startswith('N') and
            attr['head_pos'].endswith('S')):
            return coref.PRO_PLURAL
        elif attr['head_pos'].startswith('N'):
            return coref.PRO_SINGLE
        else:
            return coref.PRO_UNKNOWN

def set_properties(attr, ment):
    number = set_number(attr)
    gender = set_gender(attr)
    person = coref.PRO_UNKNOWN
    animacy = set_animacy(attr)

    return gender, number, person, animacy

def extract_properties(attr, ment, sents):
    attr['properties'] = (coref.PRO_UNKNOWN, coref.PRO_UNKNOWN,
                          coref.PRO_UNKNOWN, coref.PRO_UNKNOWN)
    if (attr['type'] == my_constant.MAP_MTYPES['pronoun'] and
        attr['head_word'] in coref.pronoun_properties):
        attr['properties'] = coref.pronoun_properties[attr['head_word']]
    else:
        attr['properties'] = set_properties(attr, ment)

def extract_modifiers(attr, ment, sents, trees, heads):
    ret = set()
    for i in xrange(ment[1], ment[2]):
        span, word, pos = \
            coref.mention_head((ment[0], i, i + 1), sents, trees, heads)
        word = word.lower()
        if (not (pos.startswith('N') or
                 pos.startswith('V') or
                 pos.startswith('JJ') or pos == 'CD') or
            word == attr['head_word']):
           continue
        ret.add(word)

    return ret

def extract_word_list(attr):
    ret = set()
    for word in attr['surface'].split():
        ret.add(word)

    return ret

def remove_phrase_after_head(attr, ment, sents, trees, heads):
    comma_idx = -1
    wh_idx = -1
    sent_idx, start_idx, end_idx = ment

    head_idx = attr['head_idx']
    surface = attr['surface']
    if head_idx + 2 > end_idx: # Unlikely to have a pharse
        return surface

    tmp = (sent_idx, head_idx + 1, head_idx + 2)
    span, word, pos = coref.mention_head(tmp, sents, trees, heads)
    if comma_idx == -1 and pos == ',':
        comma_idx = head_idx + 1
    if wh_idx == -1 and pos.startswith('W'):
        wh_idx = head_idx + 1

    ret = surface
    if comma_idx != -1 and head_idx < comma_idx:
        ret = ' '.join(sents[sent_idx][start_idx:comma_idx])

    if comma_idx == -1 and wh_idx != -1 and head_idx < wh_idx:
        ret = ' '.join(sents[sent_idx][start_idx:wh_idx])

    return ret.lower()

def set_ner(attr, ment, sner):
    attr['ner'] = 'O'
    for key, val in sner[ment[0]].items():
        if key[1] <= attr['head_idx'] and attr['head_idx'] <= key[2]:
            attr['ner'] = val
    attr['disagreed_parse_ne'] = False

def set_first_word(attr, ment, sents, trees, heads):
    ment_ = (ment[0], ment[1], ment[1] + 1)
    first_span, first_word, first_pos = \
        coref.mention_head(ment_, sents, trees, heads)
    attr['first_word'] = first_word.lower()
    attr['first_pos'] = first_pos

def set_head(attr, ment, sents, trees, heads):
    head_span, head_word, head_pos = \
        coref.mention_head(ment, sents, trees, heads)
    attr['head_idx'] = head_span[0]
    attr['head_word'] = head_word.lower()
    attr['head_pos'] = head_pos

def init(doc_ments, sents, trees, heads, sner, speakers):
    doc_attrs  = {}
    for sent_ments in doc_ments:
        for ment in sent_ments:
            attr = {}
            attr['type'] = my_constant.MAP_MTYPES[coref.mention_type(
                ment, sents, trees, heads)]
            attr['surface'] = coref.mention_text(ment, sents).lower()
            set_head(attr, ment, sents, trees, heads)
            set_first_word(attr, ment, sents, trees, heads)
            set_ner(attr, ment, sner)
            attr['relaxed_surface'] = remove_phrase_after_head(
                attr, ment, sents, trees, heads)
            attr['word_list'] = extract_word_list(attr)
            attr['modifiers'] = extract_modifiers(
                attr, ment, sents, trees, heads)
            extract_properties(attr, ment, sents)
            set_speaker(attr, ment, speakers)
            attr['pleonastic'] = is_pleonastic(attr, ment, sents)
            doc_attrs[ment] = attr

    return doc_attrs
