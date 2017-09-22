#!/usr/bin/python

from common import *

import argparse
import os
import glob
import re
import math
import random
from subprocess import Popen, PIPE
import subprocess
import slate
import cPickle as pickle
import sys
import traceback
from collections import Counter
from subprocess32 import check_output
from multiprocessing import Pool

#from stop_words import get_stop_words     # sudo pip install -U stop_words
from nltk.stem.porter import PorterStemmer # sudo pip install -U nltk
import gensim                              # sudo pip install -U --ignore-installed gensim
from gensim import corpora, models

######################################################
# 
#   Text analysis routines
#
######################################################

# List from: http://www.lextek.com/manuals/onix/stopwords1.html
def get_stop_words(): 
    return set([\
        "a", "about", "above", "across", "after", "again", "against",
        "all", "almost", "alone", "along", "already", "also", "although",
        "always", "among", "an", "and", "another", "any", "anybody",
        "anyone", "anything", "anywhere", "are", "area", "areas", "around",
        "as", "ask", "asked", "asking", "asks", "at", "away", "b", "back",
        "backed", "backing", "backs", "be", "became", "because", "become",
        "becomes", "been", "before", "began", "behind", "being", "beings",
        "best", "better", "between", "big", "both", "but", "by", "c",
        "came", "can", "cannot", "case", "cases", "certain", "certainly",
        "clear", "clearly", "come", "could", "d", "did", "differ",
        "different", "differently", "do", "does", "done", "down", "down",
        "downed", "downing", "downs", "during", "e", "each", "early",
        "either", "end", "ended", "ending", "ends", "enough", "even",
        "evenly", "ever", "every", "everybody", "everyone", "everything",
        "everywhere", "f", "face", "faces", "fact", "facts", "far", "felt",
        "few", "find", "finds", "first", "for", "four", "from", "full",
        "fully", "further", "furthered", "furthering", "furthers", "g",
        "gave", "general", "generally", "get", "gets", "give", "given",
        "gives", "go", "going", "good", "goods", "got", "great", "greater",
        "greatest", "group", "grouped", "grouping", "groups", "h", "had",
        "has", "have", "having", "he", "her", "here", "herself", "high",
        "high", "high", "higher", "highest", "him", "himself", "his",
        "how", "however", "i", "if", "important", "in", "interest",
        "interested", "interesting", "interests", "into", "is", "it",
        "its", "itself", "j", "just", "k", "keep", "keeps", "kind", "knew",
        "know", "known", "knows", "l", "large", "largely", "last", "later",
        "latest", "least", "less", "let", "lets", "like", "likely", "long",
        "longer", "longest", "m", "made", "make", "making", "man", "many",
        "may", "me", "member", "members", "men", "might", "more", "most",
        "mostly", "mr", "mrs", "much", "must", "my", "myself", "n",
        "necessary", "need", "needed", "needing", "needs", "never", "new",
        "new", "newer", "newest", "next", "no", "nobody", "non", "noone",
        "not", "nothing", "now", "nowhere", "number", "numbers", "o", "of",
        "off", "often", "old", "older", "oldest", "on", "once", "one",
        "only", "open", "opened", "opening", "opens", "or", "order",
        "ordered", "ordering", "orders", "other", "others", "our", "out",
        "over", "p", "part", "parted", "parting", "parts", "per",
        "perhaps", "place", "places", "point", "pointed", "pointing",
        "points", "possible", "present", "presented", "presenting",
        "presents", "problem", "problems", "put", "puts", "q", "quite",
        "r", "rather", "really", "right", "right", "room", "rooms", "s",
        "said", "same", "saw", "say", "says", "second", "seconds", "see",
        "seem", "seemed", "seeming", "seems", "sees", "several", "shall",
        "she", "should", "show", "showed", "showing", "shows", "side",
        "sides", "since", "small", "smaller", "smallest", "so", "some",
        "somebody", "someone", "something", "somewhere", "state", "states",
        "still", "still", "such", "sure", "t", "take", "taken", "than",
        "that", "the", "their", "them", "then", "there", "therefore",
        "these", "they", "thing", "things", "think", "thinks", "this",
        "those", "though", "thought", "thoughts", "three", "through",
        "thus", "to", "today", "together", "too", "took", "toward", "turn",
        "turned", "turning", "turns", "two", "u", "under", "until", "up",
        "upon", "us", "use", "used", "uses", "v", "very", "w", "want",
        "wanted", "wanting", "wants", "was", "way", "ways", "we", "well",
        "wells", "went", "were", "what", "when", "where", "whether", "which",
        "while", "who", "whole", "whose", "why", "will", "with", "within",
        "without", "work", "worked", "working", "works", "would", "x", "y",
        "year", "years", "yet", "you", "young", "younger", "youngest", "your",
        "yours", "z"
        ])


def is_digit(word):
    try:
        int(word)
        return True
    except ValueError:
        return False

def find_words(string):
    #words = page.lower().split()
    words = re.findall('\s(\w+)\s', string.lower())
    new_words = []
    for w in words:
        if not is_digit(w) and len(w) > 1:  # Reject numbers and single letters
            new_words.append(w)
    return new_words

# brew cask install pdftotext
def scrape_via_pdftotext(pdf_file):
    cmd = ['pdftotext', pdf_file, '-']
    text = check_output(cmd)
    return text

def scrape_via_pdfminer(pdf_file):
    text = ""
    with open(pdf_file) as pdf:
        pages = slate.PDF(pdf)
        for page in pages:
            text += page
    return text

def analyze_words(pdf_file):
    stops = get_stop_words()
    p_stemmer = PorterStemmer()

    try:
        text = scrape_via_pdftotext(pdf_file)
        words = find_words(text)
        return words        # Let StarSpace handle stemming and stop words
        stopped_words = [w for w in words if not w in stops]
        stemmed_words = [p_stemmer.stem(w) for w in stopped_words]
        return stemmed_words
    except:
        print "\nUnexpected error while opening pdf %s!\n%s" % (pdf_file, traceback.format_exc())
        return None

######################################################
# 
#   Analyzing reviewer papers
#
######################################################

def analyze_reviewer_papers(reviewer):
    count = reviewer.feature_vector  # Grab the existing count, if any
    old_words = reviewer.words
    weights = reviewer.make_pdf_weights()

    if reviewer.status == "PDFs":
        count = []  # Reset the count
        pdfs = glob.glob('%s/*pdf' % reviewer.dir())
        for pdf_file in pdfs:
            print "Analyzing %s" % pdf_file
            pdf_count = []
            try:
                words = analyze_words(pdf_file)
                if words == None:
                    print "WARNING: No words returned"
                    continue
                reviewer.num_words += len(words)
                old_words += words
                count += [words]
            except:
                print "\nUnexpected error while analyzing pdf %s!\n%s" % (pdf_file, traceback.format_exc())
                continue
    return (count, old_words)

def analyze_reviewers_papers(pc, j, train_file):
    print "Analyzing reviewers' papers..."
    reviewers = pc.reviewers()
    pool = None
    if not j == None:
        pool = Pool(int(j))
    else:
        pool = Pool()
    feature_vectors = pool.map(analyze_reviewer_papers, reviewers)

    for reviewer, (feature_vector, words) in zip(reviewers, feature_vectors):
        reviewer.feature_vector = feature_vector
        reviewer.words = words
        reviewer.status = "Features"

    with open(train_file, "w") as training:
        for reviewer in pc.reviewers():
            for words in reviewer.feature_vector:
                for word in words:
                    training.write(word)
                    training.write(" ")
                training.write("\t")
            training.write("\n")

    print "Analyzing reviewers' papers complete!"



######################################################
# 
#   Analyzing submissions
#
######################################################

def analyze_submission(pdf_file):
    num_words = 0
    print "Analyzing %s" % pdf_file
    words = analyze_words(pdf_file)
    feature_vector = words

    return (words, feature_vector)


def analyze_submissions(submission_dir, j):
    pdfs = glob.glob('%s/*pdf' % submission_dir)
    pool = None
    if not j == None:
        pool = Pool(int(j))
    else:
        pool = Pool()
    results = pool.map(analyze_submission, pdfs)

    submissions = {}
    for (pdf_file, result) in zip(pdfs, results):
        match = re.search("(.*)-paper(.*).pdf", pdf_file)
        if match == None:
            print "Malformed submission file name: %s" % pdf_file
            continue
        conf_name = match.group(1)
        paper_id = int(match.group(2))
        sub = Submission(conf_name, paper_id)
        words, feature_vector = result
        if not(words == None):
            sub.num_words = len(words)
            sub.feature_vector = feature_vector
            sub.words = words
            submissions[paper_id] = sub

    with open("%s/submissions.txt" % submission_dir, "w") as subtext:
        for sub in submissions.values():
            subtext.write("SubmissionID%s " % sub.id)
            for word in sub.feature_vector:
                subtext.write(word)
                subtext.write(" ")
            subtext.write("\n")

    return submissions


######################################################
# 
#   Build topic model from a corpus of PDFs
#
######################################################

def build_lda_model(corpus_dir, num_workers):
    model_file = "%s/lda.model" % corpus_dir
    if not os.path.isfile(model_file):
        print "Analyzing PDFs..."
        pdfs = glob.glob('%s/*pdf' % corpus_dir)
        pool = None
        if not num_workers == None:
            pool = Pool(int(num_workers))
        else:
            pool = Pool()
        results = pool.map(analyze_words, pdfs)
        print "Analyzing PDFs complete!"

        condensed_results = [r for r in results if not r == None]

        # turn our tokenized documents into an id <-> term dictionary
        dictionary = corpora.Dictionary(condensed_results)

        # convert tokenized documents into a document-term matrix
        corpus = [dictionary.doc2bow(text) for text in condensed_results]

        # generate LDA model
        print "Building topic model from PDFs..."
        ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=50, id2word = dictionary, passes=30)

        print ldamodel.show_topics(num_topics=50)

        ldamodel.save(model_file)
        print "Building topic model from PDFs complete!"
    else:
        print "LDA model already exists in file %s.  Delete or rename it to regenerate the model." % model_file


def main():
    parser = argparse.ArgumentParser(description='Analyze PC papers and/or submissions')
    parser.add_argument('-c', '--cache', help="Use the specified file for caching reviewer status and information", required=False)
    parser.add_argument('--submissions', action='store', help="Directory of submissions", required=False)
    parser.add_argument('--corpus', action='store', help="Directory of PDFs from which to build a topic (LDA) model", required=False)
    parser.add_argument('--train', action='store', help="Filename for training input", required=False)
    parser.add_argument('-j', action='store', help="Number of processes to use", required=False)
    
    args = parser.parse_args()

    pc = PC()

    if not (args.cache == None):
        pc.load(args.cache)
        analyze_reviewers_papers(pc, args.j, args.train)
        pc.save(args.cache)

    if not (args.submissions == None):
        pickle_file = "%s/submissions.dat" % args.submissions
        if not os.path.isfile(pickle_file):
            submissions = analyze_submissions(args.submissions, args.j)
            with open(pickle_file, "wb") as pickler:
                pickle.dump(submissions, pickler)

    if not (args.corpus == None):
        build_lda_model(args.corpus, args.j)


if (__name__=="__main__"):
  main()

