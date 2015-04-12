import gzip
import logging
import sys

logger = logging.getLogger(__name__)

animate_words = set()
inanimate_words = set()
male_words = set()
female_words = set()
singular_words = set()
plural_words = set()
gender_number = {}
gpe_acronyms = set()

# Used for skipping first mentions
indefinite_pronouns = {"another", "anybody", "anyone", "anything", "each", "either", "enough", "everybody", "everyone", "everything", "less", "little", "much", "neither", "no one", "nobody", "nothing", "one", "other", "plenty", "somebody", "someone", "something", "both", "few", "fewer", "many", "others", "several", "all", "any", "more", "most", "none", "some", "such"}

# Used for spurious mentions 
stop_words = {
"aa",
"ahem",
"er",
"ha", "hmm",
"mm", "mm .", "mhm",
"there",
"um", 
}
stop_prefixes = {"#", "$", "p. ", "%"}
stop_suffixes = {"!", "%", "+", ":"}

# Used for spurious mentions 
quantifiers = {"not", "every", "any", "none", "everything", "anything", "nothing", "all", "enough"}

# Used for extracting bow
words_to_exclude = set()
words_to_exclude.update({"the", "this", "that", "these", "those", "'s", "'"})

# Used for checking pleonastic it
pleonastic_words = {"'s", "is", "was", "be", "seems", "seemed", "appears", "looks", "means", "follows", "turns", "turned", "become", "became"}

# Used for incompatible modifiers
location_modifiers = {"east", "west", "north", "south", "eastern", "western", "northern", "southern", "northwestern", "southwestern", "northeastern", "southeastern", "upper", "lower"}

temporals = {
      "second", "minute", "hour", "day", "week", "month", "year", "decade", "century", "millennium",
      "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "now",
      "yesterday", "tomorrow", "age", "time", "era", "epoch", "morning", "evening", "day", "night", "noon", "afternoon",
      "semester", "trimester", "quarter", "term", "winter", "spring", "summer", "fall", "autumn", "season",
      "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"}

def file_to_dict(filename):
    logger.info("Loading [%s]" % filename)
    ret = set()
    try:
        with open(filename) as f:
            ret =  set(word.strip().lower() for word in f)
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    return ret

def load_gpe_acronyms(gpe_acronyms, filename):
    logger.info("Loading [%s]" % filename)
    try:
        start = False
        with open(filename) as f:
            for line in f:
                for word in line.split('\t')[1:]:
                    gpe_acronyms.add(word.strip().lower())
    except Exception as e:
        logger.error(e)
        sys.exit(1)

def load_gzip_gender_number(filename):
    logger.info("Loading %s..." % filename)
    ret = {}
    try:
        with gzip.open(filename) as f:
            for line in f:
                l = line.strip().lower().split('\t')
                ret[l[0]] = l[1]
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    return ret

def init(files):
    if files['animate']:
        global animate_words
        animate_words = file_to_dict(files['animate'])

    if files['inanimate']:
        global inanimate_words
        inanimate_words = file_to_dict(files['inanimate'])

    if files['male']:
        global male_words
        male_words = file_to_dict(files['male'])

    if files['female']:
        global female_words
        female_words = file_to_dict(files['female'])

    if files['singular']:
        global singular_words
        singular_words = file_to_dict(files['singular'])

    if files['plural']:
        global plural_words
        plural_words = file_to_dict(files['plural'])

    global gpe_acronyms
    if files['country']:
        load_gpe_acronyms(gpe_acronyms, files['country'])

    if files['state']:
        load_gpe_acronyms(gpe_acronyms, files['state'])

    return True
