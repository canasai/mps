import os
import sys

import scorer_pairwise
import scorer_muc
import scorer_bcubed

def calc_pairwise(data):
    return scorer_pairwise.calc_rpf1(data)

def calc_muc(data):
    return scorer_muc.calc_rpf1(data)

def calc_bcubed(data):
    return scorer_bcubed.calc_rpf1(data)
