#!/usr/bin/python

from common import *
import analysis

import argparse
import glob
import csv


class Bid:
    def __init__(self, score, submission):
        self.score = score
        self.submission = submission

def load_2017_prefs(pc):
    print "Loading reviewers bids from 2017..."
    reviewers2017 = {}
    for reviewer in pc.reviewers():
        prefs_file = glob.glob('%s/oakland17-revprefs*.csv' % reviewer.dir())
        if not(prefs_file == []):
            prefs_file = prefs_file[0]
            prefs = []
            with open(prefs_file, 'rb') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    pref = -200
                    if row['preference'] == 'conflict':
                        pref = -100
                    elif analysis.is_digit(row['preference']):
                        pref = int(row['preference'])
                    else:
                        print "WARNING: Unknown preference %s for 2017 reviewer %s" % (row['preference'], reviewer)

                    b = Bid(score=pref, submission=row['paper'])
                    prefs.append(b)
            reviewers2017[reviewer] = prefs

    print "Loaded 2017 preferences for %d reviewers" % len(reviewers2017)
    print "Loading reviewers bids from 2017 complete!"
    return reviewers2017

def write_csv(prefs, csv_file):
    with open(csv_file, "w") as csv:
        csv.write("paperId\tcontactId\tpreference\n")
        for reviewer,bids in prefs.iteritems():
            if reviewer.sql_id is None:
                print "WARNING: Couldn't find an id for %s.  Skipping.  Consider using util.py with --pcids" % reviewer
                continue
            for bid in bids:
                csv.write("%s\t%s\t%s\t\n" % (bid.submission, reviewer.sql_id, bid.score))

def main():
    parser = argparse.ArgumentParser(description='Map bids from Oakland 2017 to new IDs')
    parser.add_argument('-c', '--cache', help="Use the specified file for caching reviewer data", required=True)
    parser.add_argument('--csv', help="Write out results to csv file", required=True)
    
    args = parser.parse_args()

    pc = PC()
    pc.load(args.cache)

    prefs = load_2017_prefs(pc)
    write_csv(prefs, args.csv)

if (__name__=="__main__"):
  main()

