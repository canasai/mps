## A multi-pass sieve for coreference resolution in Python

#### Introduction
This is an implementation of  a multi-pass sieve for coreference resolution (Raghunathan et al., 2010; Lee et al., 2011) in Python.
I extend the [Berkeley Coreference Analyser](http://code.google.com/p/berkeley-coreference-analyser) that is originally written to perform error analysis on coreference resolution output (Kummerfeld and Klein, 2013).
The mps program conducts end-to-end coreference resolution.
The code is implemented and tested on Python 2.7.5 and does not work properly on Python 3.

#### Quick start
Clone the code to your machine:
```
$ git clone https://github.com/canasai/mps
$ cd mps
```

Download the trial data from the CoNLL-2012 shared task:
```
$ wget http://conll.cemantix.org/2012/download/conll-2012-trial-data.tar.gz
```

Uncompress:
```
$ tar xvfz conll-2012-trial-data.tar.gz
```

Suppose the working directory looks like:
```
mps
├── conll-2012
├── dict
├── mps
├── Makefile
└── README.md
```

In the base directory, type:
```
$ make test
```

You should see something like:
```
python -m mps.tests.test_mps mps/default_config.json
Add pass 0: [exact_match]
Add pass 1: [relaxed_exact_match]
Add pass 2: [iwithini]
Add pass 2: [cluster_head_match]
Add pass 2: [word_inclusion]
Add pass 2: [compatible_modifiers]
Add pass 3: [iwithini]
Add pass 3: [cluster_head_match]
Add pass 3: [word_inclusion]
Add pass 4: [iwithini]
Add pass 4: [cluster_head_match]
Add pass 4: [compatible_modifiers]
Add pass 5: [iwithini]
Add pass 5: [relaxed_head_match]
Add pass 5: [word_inclusion]
Add pass 5: [compatible_properties]
Add pass 6: [iwithini]
Add pass 6: [pronoun_match]
Add pass 6: [compatible_properties]
Loading [dict/animate.unigrams.txt]
Loading [dict/inanimate.unigrams.txt]
Loading [dict/male.unigrams.txt]
Loading [dict/female.unigrams.txt]
Loading [dict/singular.unigrams.txt]
Loading [dict/plural.unigrams.txt]
Loading [dict/country.abbreviations.txt]
Loading [dict/state.abbreviations.txt]
Loading data in [conll-2012/trial/data/english] with suffix [.conll]
Mention detection
    document (nw/xinhua/01/chtb_0192); part 000
    document (bn/cnn/03/cnn_0324); part 000
    document (bc/msnbc/00/msnbc_0004); part 022
    document (bc/msnbc/00/msnbc_0004); part 010
    document (bc/msnbc/00/msnbc_0004); part 011
    document (bc/msnbc/00/msnbc_0004); part 012
    document (bc/msnbc/00/msnbc_0004); part 013
    document (bc/msnbc/00/msnbc_0004); part 014
    document (bc/msnbc/00/msnbc_0004); part 015
    document (bc/msnbc/00/msnbc_0004); part 016
    document (bc/msnbc/00/msnbc_0004); part 017
    document (bc/msnbc/00/msnbc_0004); part 018
    document (bc/msnbc/00/msnbc_0004); part 019
    document (bc/msnbc/00/msnbc_0004); part 003
    document (bc/msnbc/00/msnbc_0004); part 002
    document (bc/msnbc/00/msnbc_0004); part 001
    document (bc/msnbc/00/msnbc_0004); part 000
    document (bc/msnbc/00/msnbc_0004); part 007
    document (bc/msnbc/00/msnbc_0004); part 020
    document (bc/msnbc/00/msnbc_0004); part 005
    document (bc/msnbc/00/msnbc_0004); part 004
    document (bc/msnbc/00/msnbc_0004); part 009
    document (bc/msnbc/00/msnbc_0004); part 008
    document (bc/msnbc/00/msnbc_0004); part 021
    document (bc/msnbc/00/msnbc_0004); part 006
    document (bn/cnn/01/cnn_0122); part 000
    document (bc/phoenix/00/phoenix_0002); part 003
    document (bc/phoenix/00/phoenix_0002); part 002
    document (bc/phoenix/00/phoenix_0002); part 001
    document (bc/phoenix/00/phoenix_0002); part 000
    document (bc/phoenix/00/phoenix_0002); part 006
    document (bc/phoenix/00/phoenix_0002); part 005
    document (bc/phoenix/00/phoenix_0002); part 004
    document (mz/sinorama/10/ectb_1072); part 003
    document (mz/sinorama/10/ectb_1072); part 002
    document (mz/sinorama/10/ectb_1072); part 001
    document (mz/sinorama/10/ectb_1072); part 000
    document (wb/eng/00/eng_0014); part 003
    document (wb/eng/00/eng_0014); part 002
    document (wb/eng/00/eng_0014); part 001
    document (wb/eng/00/eng_0014); part 000
    document (wb/eng/00/eng_0012); part 003
    document (wb/eng/00/eng_0012); part 002
    document (wb/eng/00/eng_0012); part 001
    document (wb/eng/00/eng_0012); part 000
    document (mz/sinorama/10/ectb_1074); part 002
    document (mz/sinorama/10/ectb_1074); part 001
    document (mz/sinorama/10/ectb_1074); part 000
    document (nw/wsj/10/wsj_1024); part 000
Summary: 5.49% (62/1130) are not constituents
Coreference resolution
    document (nw/xinhua/01/chtb_0192); part 000
    document (bn/cnn/03/cnn_0324); part 000
    document (bc/msnbc/00/msnbc_0004); part 022
    document (bc/msnbc/00/msnbc_0004); part 010
    document (bc/msnbc/00/msnbc_0004); part 011
    document (bc/msnbc/00/msnbc_0004); part 012
    document (bc/msnbc/00/msnbc_0004); part 013
    document (bc/msnbc/00/msnbc_0004); part 014
    document (bc/msnbc/00/msnbc_0004); part 015
    document (bc/msnbc/00/msnbc_0004); part 016
    document (bc/msnbc/00/msnbc_0004); part 017
    document (bc/msnbc/00/msnbc_0004); part 018
    document (bc/msnbc/00/msnbc_0004); part 019
    document (bc/msnbc/00/msnbc_0004); part 003
    document (bc/msnbc/00/msnbc_0004); part 002
    document (bc/msnbc/00/msnbc_0004); part 001
    document (bc/msnbc/00/msnbc_0004); part 000
    document (bc/msnbc/00/msnbc_0004); part 007
    document (bc/msnbc/00/msnbc_0004); part 020
    document (bc/msnbc/00/msnbc_0004); part 005
    document (bc/msnbc/00/msnbc_0004); part 004
    document (bc/msnbc/00/msnbc_0004); part 009
    document (bc/msnbc/00/msnbc_0004); part 008
    document (bc/msnbc/00/msnbc_0004); part 021
    document (bc/msnbc/00/msnbc_0004); part 006
    document (bn/cnn/01/cnn_0122); part 000
    document (bc/phoenix/00/phoenix_0002); part 003
    document (bc/phoenix/00/phoenix_0002); part 002
    document (bc/phoenix/00/phoenix_0002); part 001
    document (bc/phoenix/00/phoenix_0002); part 000
    document (bc/phoenix/00/phoenix_0002); part 006
    document (bc/phoenix/00/phoenix_0002); part 005
    document (bc/phoenix/00/phoenix_0002); part 004
    document (mz/sinorama/10/ectb_1072); part 003
    document (mz/sinorama/10/ectb_1072); part 002
    document (mz/sinorama/10/ectb_1072); part 001
    document (mz/sinorama/10/ectb_1072); part 000
    document (wb/eng/00/eng_0014); part 003
    document (wb/eng/00/eng_0014); part 002
    document (wb/eng/00/eng_0014); part 001
    document (wb/eng/00/eng_0014); part 000
    document (wb/eng/00/eng_0012); part 003
    document (wb/eng/00/eng_0012); part 002
    document (wb/eng/00/eng_0012); part 001
    document (wb/eng/00/eng_0012); part 000
    document (mz/sinorama/10/ectb_1074); part 002
    document (mz/sinorama/10/ectb_1074); part 001
    document (mz/sinorama/10/ectb_1074); part 000
    document (nw/wsj/10/wsj_1024); part 000
Do post processing
    document (nw/xinhua/01/chtb_0192); part 000
        Remove singletons
    document (bn/cnn/03/cnn_0324); part 000
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 022
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 010
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 011
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 012
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 013
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 014
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 015
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 016
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 017
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 018
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 019
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 003
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 002
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 001
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 000
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 007
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 020
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 005
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 004
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 009
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 008
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 021
        Remove singletons
    document (bc/msnbc/00/msnbc_0004); part 006
        Remove singletons
    document (bn/cnn/01/cnn_0122); part 000
        Remove singletons
    document (bc/phoenix/00/phoenix_0002); part 003
        Remove singletons
    document (bc/phoenix/00/phoenix_0002); part 002
        Remove singletons
    document (bc/phoenix/00/phoenix_0002); part 001
        Remove singletons
    document (bc/phoenix/00/phoenix_0002); part 000
        Remove singletons
    document (bc/phoenix/00/phoenix_0002); part 006
        Remove singletons
    document (bc/phoenix/00/phoenix_0002); part 005
        Remove singletons
    document (bc/phoenix/00/phoenix_0002); part 004
        Remove singletons
    document (mz/sinorama/10/ectb_1072); part 003
        Remove singletons
    document (mz/sinorama/10/ectb_1072); part 002
        Remove singletons
    document (mz/sinorama/10/ectb_1072); part 001
        Remove singletons
    document (mz/sinorama/10/ectb_1072); part 000
        Remove singletons
    document (wb/eng/00/eng_0014); part 003
        Remove singletons
    document (wb/eng/00/eng_0014); part 002
        Remove singletons
    document (wb/eng/00/eng_0014); part 001
        Remove singletons
    document (wb/eng/00/eng_0014); part 000
        Remove singletons
    document (wb/eng/00/eng_0012); part 003
        Remove singletons
    document (wb/eng/00/eng_0012); part 002
        Remove singletons
    document (wb/eng/00/eng_0012); part 001
        Remove singletons
    document (wb/eng/00/eng_0012); part 000
        Remove singletons
    document (mz/sinorama/10/ectb_1074); part 002
        Remove singletons
    document (mz/sinorama/10/ectb_1074); part 001
        Remove singletons
    document (mz/sinorama/10/ectb_1074); part 000
        Remove singletons
    document (nw/wsj/10/wsj_1024); part 000
        Remove singletons
Data statistics:
    files = 10, docs = 49, sentences = 1364, words = 25030
Performance of mention detection:
    P = 71.66% (2096/2925), R = 77.43% (2096/2707), F1 = 74.43%
Performance of coreference resolution:
Pairwise P/R/F1 by types:
          name                     nominal                  pronoun                  
name      79.43/66.95/72.66        77.14/12.22/21.09        77.65/22.29/34.63
nominal   60.53/8.85/15.44         39.67/51.57/44.84        8.47/4.02/5.45
pronoun   55.57/21.51/31.02        24.93/25.25/25.09        58.27/40.78/47.98
Pairwise scores:
    P = 55.80% (3979/7131), R = 35.54% (3979/11197), F1 = 43.42%
MUC scores:
    P = 61.33% (1291/2105), R = 63.04% (1291/2048), F1 = 62.17%
B-cubed scores:
    P = 70.86% (2505/3536), R = 54.98% (1488/2707), F1 = 61.92%
Writing output to [result.out]
.
----------------------------------------------------------------------
Ran 1 test in 46.930s

OK
```

The output file is `result.out`:

You can specify the input data folder and parameters by editing the `mps/default_config.json` file.


#### References

* A Multi-Pass Sieve for Coreference Resolution.
 Karthik Raghunathan, Heeyoung Lee, Sudarshan Rangarajan, Nathanael Chambers, Mihai Surdeanu, Dan Jurafsky, Christopher Manning.
  EMNLP-2010. 

* Stanford's Multi-Pass Sieve Coreference Resolution System at the CoNLL-2011 Shared Task.
  Heeyoung Lee, Yves Peirsman, Angel Chang, Nathanael Chambers, Mihai Surdeanu, Dan Jurafsky.
  In Proceedings of the CoNLL-2011 Shared Task. 

* Error-Driven Analysis of Challenges in Coreference Resolution.
  Jonathan K. Kummerfeld and Dan Klein.
  EMNLP 2013.
