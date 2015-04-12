MTYPES = ['name', 'nominal', 'pronoun']
MAP_MTYPES = {'name': 0, 'nominal': 1, 'pronoun': 2}

NE_TYPES_TO_EXCLUDE = {'O', 'QUANTITY', 'CARDINAL', 'PERCENT', 'DATE',
                       'DURATION', 'TIME', 'SET', 'ORDINAL'}

PARSE_TYPES_TO_KEEP = {'NP', 'PRP', 'PRP$'}

RULE_NAMES = {'exact_match',             
              'relaxed_exact_match',
              'iwithini',
              'cluster_head_match',
              'word_inclusion',
              'compatible_modifiers',
              'relaxed_head_match',
              'compatible_properties',
              'pronoun_match'}

HLINE = "---------------------------------------------------------------------"
