#!/usr/bin/python

from common import *

import argparse
import os
import glob
import re
import math
import random
from subprocess import Popen, PIPE
from urlparse import urljoin
from urlparse import urlparse
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

def wget_args():
    user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
    args = ['wget', '-t', '3', '-U', user_agent, '--no-check-certificate']
    return args

def fetch_url(url):
    cmd = wget_args() + ['-O', '-', url]

#    p = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
#    stdout, stderr = p.communicate()
#    html = stdout
#    print stderr

    html = check_output(cmd, timeout=10)
#    print "Downloaded HTML <<<<<<<<"
#    print html
#    print ">>>>>>>>>>>>>>>>>>>\n\n"
    return html

def fetch_pdf(url, dirname):
    cmd = wget_args() + ['--no-clobber', '--directory-prefix=%s' % dirname, url]
    subprocess.call(cmd)

# TODO: Replace this ad hoc version with Beautiful Soup: https://www.crummy.com/software/BeautifulSoup/
def find_pdf_links(base_url, html):
    # Remove whitespace, since sometimes the URL wraps
    html = re.sub('\s', '', html)

    href_links = re.findall('[hH][rR][eE][fF]\s*=\s*[\'"](.+?)[\'"]', html)

    # Keep track of the order of the links
    links = set()
    for i, link in enumerate(href_links):
        links.add(PDF(i, link))

    pdf_links = filter(lambda link: link.url.lower().endswith('pdf'), links)
    full_pdf_links = map(lambda link: link if link.url.lower().startswith('http') else PDF(link.index, urljoin(base_url, link.url)), pdf_links)
    
    print "Found %d pdfs out of %d links" % (len(pdf_links), len(links))
    for link in full_pdf_links:
        print "PDF link: %s" % link

    return full_pdf_links

def process_reviewers(pc, html_only):
    print "Processing reviewers..."
    count = 0
    for reviewer in pc.reviewers():
        count += 1
        did_work = False
        if reviewer.status == "Init":
            did_work = True
            print "Fetching publication page for %s" % reviewer.name()
            try:
                reviewer.html = fetch_url(reviewer.url)
            except:
                print "\nUnexpected error while fetching url %s!\n%s" % (reviewer.url, traceback.format_exc())
                print "\nSkipping reviewer %s\n" % reviewer
                continue
            reviewer.status = "HTML"

        if reviewer.status == "HTML":
            did_work = True
            print "Finding PDFs for %s (Reviewer %d of %d)" % (reviewer, count, pc.count())
            pdf_links = set(find_pdf_links(reviewer.url, reviewer.html))

            if len(pdf_links) > 500:
                print "ERROR: Found too many PDFs (%d) for %s.  Skipping them." % (len(pdf_links), reviewer)
                next

            if len(pdf_links) > 100:
                print "WARNING: Found many PDFs (%d) for %s" % (len(pdf_links), reviewer)

            if len(pdf_links) < 5:
                print "WARNING: Found too few PDFS (%d) for %s" % (len(pdf_links), reviewer)

            if not html_only:
                for link in pdf_links - reviewer.pdf_links:
                    try:
                        fetch_pdf(link.url, reviewer.dir())
                        reviewer.pdf_links.add(link)
                    except:
                        print "\nUnexpected error while fetching pdf %s!\n%s" % (link, traceback.format_exc())
                        continue

                    time.sleep(1)
                reviewer.status = "PDFs"
        if did_work:
            time.sleep(3)
        #raw_input('Press enter to continue...')
    print "Processing reviewers complete!"


def main():
    parser = argparse.ArgumentParser(description='Fetch PC member papers')
    parser.add_argument('--csv', action='store', required=False, help='CSV file containing PC member info from sign-up survey')
    parser.add_argument('-c', '--cache', help="Use the specified file for caching reviewer data", required=False)
    parser.add_argument('--html', action='store_true', default=False, help="Only fetch and analyze HTML pages", required=False)
    
    args = parser.parse_args()

    pc = PC()

    # Pull in previous data, if it exists
    if not (args.cache == None):
        pc.load(args.cache)
    
    if not args.csv == None:
        # Update based on csv file
        pc.parse_csv(args.csv)
        pc.save(args.cache)

    process_reviewers(pc, args.html)
    pc.save(args.cache)


if (__name__=="__main__"):
  main()

