#!/usr/bin/python

import argparse
import os
import glob
import re
import math
import random
from subprocess import Popen, PIPE
from urlparse import urljoin
import subprocess
import time
import csv
import hashlib
import slate
import pickle
import sys
import traceback
from collections import Counter
from subprocess32 import check_output
from multiprocessing import Pool
import ranking  # pip install ranking

def get_changed_bids(month):
    if month == "july":
        return [\
            'Simha_Sethumadhavan',
            'Arvind_Narayanan',
            'Tao_Xie',
            'Andreas_Haeberlen',
            'Asia_Slowinska',
            'Payman_Mohassel',
            'Stefano_Tessaro',
            'Herbert_Bos',
            'Gilles_Barthe',
            'Thorsten_Holz',
            'Cristiano_Giuffrida',
            'Ruby_Lee',
            'Nadia_Heninger',
            'Lujo_Bauer',
            'Manos_Antonakakis',
            'Gianluca_Stringhini',
            'Cynthia_Sturton',
            'Kurt_Thomas',
            'Jay_Lorch',
            'Michael_Hicks',
            'Andrei_Sabelfeld'
        ]
    elif month == "august":
        return [\
            "Marina_Blanton",
            "Stefano_Tessaro",
            "Matteo_Maffei",
            "George_Danezis",
            "Deian_Stefan",
            "Nadia_Heninger",
            "Arvind_Narayanan",
            "Yinqian_Zhang",
            "Lujo_Bauer",
            "Carmela_Troncoso",
            "Mariana_Raykova",
            "Michelle_Mazurek",
            "Gang_Tan",
            "Asia_Slowinska",
            "Ruby_Lee",
            "Davide_Balzarotti",
            "Manos_Antonakakis",
            "Herbert_Bos",
            "Andrei_Sabelfeld",
            "Gianluca_Stringhini",
            "Kurt_Thomas",
            "Jay_Lorch",
            "Thorsten_Holz",
            "Tudor_Dumitras",
            "Alex_Snoeren",
            "Michael_Hicks",
            "Manuel_Egele"
        ]
    elif month == "september":
        return [\
            "Cynthia_Sturton",
            "Stefano_Tessaro",
            "Matthew_Hicks",
            "Srini_Devadas",
            "Amir_Houmansadr",
            "Nadia_Heninger",
            "Deian_Stefan",
            "Kevin_Butler",
            "Manuel_Egele",
            "Asia_Slowinska",
            "Manos_Antonakakis",
            "Adam_Smith",
            "Adrian_Perrig",
            "Davide_Balzarotti",
            "Arvind_Narayanan",
            "Payman_Mohassel",
            "Andrei_Sabelfeld",
            "Gilles_Barthe",
            "Thorsten_Holz",
            "Hovav_Shacham",
            "Cristina_Nita-Rotaru",
            "Tao_Xie",
            "Kurt_Thomas",
            "Leyla_Bilge",
            "Lujo_Bauer",
            "Cristiano_Giuffrida",
            "Jay_Lorch"
        ]
    else:
        return []

class Bid:
    def __init__(self, score, submission):
        self.score = score
        self.submission = submission

    def __eq__(self, other):
        return isinstance(other, Bid) and \
               self.submission == other.submission

    def __str__(self):
        return "%d %02.f" % (int(self.submission), self.score)

    def __hash__(self):
        return hash(self.submission)

def is_digit(word):
    try:
        int(word)
        return True
    except ValueError:
        return False

def make_malformed(month):
    if month == "august":
        return set([26, 33])
    elif month == "2017":
        return set([\
                6,
                123,
                139,
                148,
                173,
                185,
                215,
                245,
                279,
                280,
                292,
                298,
                340,
                348,
                357,
                377,
                388,
                405,
                410,
                431,
                432,
                447,
                451,
                457,
                476,
                489,
                494,
                525,
                532,
                561,
                566,
                572,
                576,
                580,
                583,
                589,
                592,
                602])
    else:
        return set([])

def parse_bids(csv_file_name, month):
    bids = []
    conflicts = []
    malformed = make_malformed(month)
    with open(csv_file_name, 'rb') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            pref = row['preference']
            if pref == 'conflict' or (is_digit(pref) and int(pref) == -100):
                #pref = -100
                conflicts += [row['paper']]
                continue
            elif int(row['paper']) in malformed:
                continue    # Skip malformed submissions
            else:
                pref = float(pref)
            b = Bid(pref, row['paper'])
            bids.append(b)
    bids = sorted(bids, key=lambda b: b.score, reverse=True)
    return bids, conflicts


def analyze_bids_top_k(real, calc, top_k):
    real_k = real[:top_k]
    real_2k = real[:top_k*2]
    calc_k = calc[:top_k]

#    print "Real"
#    for b in real_k:
#        print "%s\t%s" % (b.submission, b.score)
#    
#    print "Calc"
#    for b in calc_k:
#        print "%s\t%s" % (b.submission, b.score)
    success = 0
    partial_success = 0
    for b in calc_k:
        if b in real_k:
            success += 1
        if b in real_2k:
            partial_success += 1

    #print "Of the top %d calculated bids, %d were in the top %d and %d were in the top %d" % (top_k, success, top_k, partial_success, 2*top_k)
    return success / float(top_k)

def fractional_ranking(bids):
    return ranking.Ranking(bids, strategy=ranking.FRACTIONAL, key=lambda b: b.score)

def average(x):
    sum = 0
    for i in x:
        sum += i
    mean = sum / float(len(x))
    return mean

def stddev(x):
    mean = average(x)

    delta_squared = 0
    for i in x:
        delta_squared += (i - mean)**2
    stdev = (1 / float(len(x) - 1) * delta_squared)**0.5

    return stdev

def covariance(x, y):
    mean_x = average(x)
    mean_y = average(y)

    sum = 0
    for x_i, y_i in zip(x, y):
        sum += (x_i - mean_x) * (y_i - mean_y)
    covariance = sum / float(len(x)-1)

    return covariance

def calculate_spearman(x, y):
    ranks_x = []
    ranks_y = []
    inverse_x = {}

    # Create a mapping from value -> ranking
    for index, val in fractional_ranking(x):
        inverse_x[val] = index

    # Accumulate the rankings for the same set of values
    for index, val in fractional_ranking(y):
        ranks_y.append(index)
        ranks_x.append(inverse_x[val])

    cov = covariance(ranks_x, ranks_y)
    std_x = stddev(ranks_x)
    std_y = stddev(ranks_y)
#    print "cov = %0.5f" % cov
#    print "std x = %0.5f" % std_x
#    print "std y = %0.5f" % std_y
    rank = cov / (std_x * std_y)

    return rank

# This only works with distinct rankings
def calculate_spearman_distinct(x, y):
    inverse_x = {}
    for index, val in fractional_ranking(x):
        #print "Submission %s got calculated index %s" % (bid.submission, index)
        inverse_x[val] = index

    diffs = 0
    for index, val in fractional_ranking(y):
        dist = index - inverse_x[val]
        diffs += dist**2

    n = len(x)
    rank = 1 - (6 * diffs) / float(n * (n**2 - 1))

    return rank


def analyze_bids_spearman(real, calc):
    if not(len(real) == len(calc)):
        #print "WARNING: Bids differ in length!  len(real) = %d, len(calc) = %d" % (len(real), len(calc))
        if len(real) < len(calc):
            new_bids = []
            for b in calc:
                if not(b in real):
                    new_bids.append(Bid(0, b.submission))
            #print "Adding %d more real bids..." % len(new_bids)
            real += new_bids
        else:
            print "WARNING: How do we have more real than calculated for real=%s, calc=%s?!" % (real, calc)

    # Make sure everything is properly sorted
    calc = sorted(calc, key=lambda b: b.score, reverse=True)
    real = sorted(real, key=lambda b: b.score, reverse=True)

#    inverse_calc = {}
#    for index, bid in fractional_ranking(calc):
#        #print "Submission %s got calculated index %s" % (bid.submission, index)
#        inverse_calc[bid.submission] = index
#
#    diffs = 0
#    for index, bid in fractional_ranking(real):
#        dist = index - inverse_calc[bid.submission]
#        diffs += dist**2
#
#    n = len(real)
#    rank = 1 - (6 * diffs) / float(n * (n**2 - 1))

    rank = calculate_spearman(calc, real)
    #print "Spearman rank is %0.1f (1 is perfect agreement, -1 is perfect disagreement)" % rank
    #print "Spearman rank is %0.1f" % rank
    return rank

def analyze_bids(real, calc, top_k, spear):
    if spear:
        return analyze_bids_spearman(real, calc)
    else:
        return analyze_bids_top_k(real, calc, top_k)

def compare_bids(real_file, calc_file, top_k, spear, month):
    if not os.path.exists(real_file):
        print "Failed to find %s.  Skipping it." % real_file
        return None
    if not os.path.exists(calc_file):
        print "Failed to find %s.  Skipping it." % calc_file
        return None

    #print "Comparing bids for %s" % real_file
    real,conflicts = parse_bids(real_file, month)
    calc,_ = parse_bids(calc_file, month)

    for conflict in conflicts:
        b = Bid(-100,conflict)
        if b in calc:
            calc.remove(b)

    return analyze_bids(real, calc, top_k, spear)

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def compare_all_bids(only_changed, month, spear, top_k, calc_bid_file="bid.csv"):
    dirs = get_changed_bids(only_changed) if not only_changed == None else get_immediate_subdirectories('./pc_data')
    ranks = []
    for d in dirs:
        if '_' in d:        # Skip directories that aren't for reviewers
            real = None
            if month == "2017":
                prefs_files = glob.glob('pc_data/%s/oakland17-revprefs*.csv' % d)
                if not(prefs_files == []):
                    real = prefs_files[0]
                else:
                    #print "Failed to find a preference file in directory %s!" % d 
                    continue
            else:
                real = os.path.join("pc_data", d, 'real_bid.%s.csv' % month)
            calc = os.path.join("pc_data", d, calc_bid_file)
            score = compare_bids(real, calc, top_k, spear=spear, month=month)
            if not score == None:
                ranks.append((d, score))
            else:
                print "Warning: Got a score of None for %s" % d
    
    sorted_ranks = sorted(ranks, key=lambda t : t[1], reverse=True)
    perfect = 0
    sum = 0
    min = 2
    max = -2
    for (d, score) in sorted_ranks:
        print "%0.2f\t%s" % (score, d)
        sum += score
        if score == 1.0:
            perfect += 1
        if score < min:
            min = score
        if score > max:
            max = score
    print "\n%d of %d scores were perfect" % (perfect, len(sorted_ranks))
    avg = sum / len(sorted_ranks)
    median = sorted_ranks[len(sorted_ranks) / 2][1]
    print "Average score: %0.2f\nMedian score %0.2f" % (avg, median)
    print "Scores range from %0.2f to %0.2f" % (min, max)

def main():
    parser = argparse.ArgumentParser(description= 'Compare bids')
    parser.add_argument('--all', action='store_true', default=False, help='Compare bids for all reviewers')
    parser.add_argument('--changed', action='store', default=None, help='Compare bids for reviewers who changed their bids in a given month')
    parser.add_argument('--month', action='store', default="august", help='Which month to compare')
    parser.add_argument('--real', action='store', help='CSV file containing real bids from HotCRP')
    parser.add_argument('--calc', action='store', help='CSV file containing calculated bids from HotCRP')
    parser.add_argument('--top_k', action='store', type=int, default=1, required=False, help='Top k bids to analyze')
    parser.add_argument('--spear', action='store_true', required=False, default=False,
            help='Calculate Spearman\'s coefficient to compare real with calculated bids')

    args = parser.parse_args()

    if args.all or (not args.changed == None):
        if args.calc is None:
            compare_all_bids(args.changed, args.month, args.spear, args.top_k)
        else:
            compare_all_bids(args.changed, args.month, args.spear, args.top_k, args.calc)
    else:
        if args.real == None or args.calc == None:
            print "Must provide both --real and --calc!"
        else:
            rank = compare_bids(args.real, args.calc, args.top_k, args.spear, args.month)
            if not rank == None:
                print "Rank is %0.5f" % rank

if (__name__=="__main__"):
  main()

