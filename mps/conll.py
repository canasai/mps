import codecs
import logging
import fnmatch
import os
import sys

import coreference_reading
import coreference_rendering

logger = logging.getLogger(__name__)

def write(data, output):
    logger.info("Writing output to [%s]" % output)
    out = codecs.open(output, 'w', 'utf-8') if output else sys.stdout
    order = []
    for doc in data:
        for part in data[doc]:
            order.append((doc, part))
    order.sort()
    for doc, part in order:
        coreference_rendering.print_conll_style_part(
            out, data[doc][part]['text'], data[doc][part]['pred_mentions'],
            doc,  part)

    return True 

def load_data(dir_prefix, doc_suffix):
    suffix = doc_suffix if doc_suffix else 'auto_conll'     
    logger.info("Loading data in [%s] with suffix [%s]" % (dir_prefix, suffix))

    data = None
    for root, dirnames, filenames in os.walk(dir_prefix):
        for filename in fnmatch.filter(filenames, '*' + suffix):
            data = coreference_reading.read_conll_doc(
                os.path.join(root, filename), data)

    if data is None or len(data) == 0:
        logger.error("Cannot load data in '%s' with suffix '%s'" % 
            (dir_prefix, suffix))
        sys.exit(1)

    return data
