#!/usr/bin/python

from common import *

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Manipulate PC state.  Valid PC status options include:"
                                               + "'Init', 'HTML', 'PDFs', 'Features'.  Each indicates which stage has been completed ")
    parser.add_argument('-c', '--cache', help="Use the specified file for caching reviewer data", required=True)
    parser.add_argument('--pc', action='store_true', help="Display PC status", required=False)
    parser.add_argument('--reviewer', action='store', help="Display status of one reviewer", required=False)
    parser.add_argument('--status', action='store', help="Update reviewer specified with --reviewer to the provided status", required=False)
    parser.add_argument('--remove', action='store', help="Remove the reviewer specified", required=False)
    parser.add_argument('--pcstatus', action='store', help="Set entire PC's status", required=False)
    parser.add_argument('--pcids', action='store', 
                        help="CSV file containing tab-delimited PC info: <first> <last> <ID>, where ID is the MySQL ID", required=False)
    
    args = parser.parse_args()

    pc = PC()
    pc.load(args.cache)

    if args.pc:
        pc.status()
        sys.exit(0)

    if not args.remove == None:
        if pc.remove_reviewer(args.remove):
            pc.save(args.cache)
            sys.exit(0)

    if not args.reviewer == None:
        if args.status == None:
            pc.reviewer(args.reviewer).display_status()
        else:
            pc.reviewer(args.reviewer).set_status(args.status)
            pc.save(args.cache)
        sys.exit(0)

    if not args.pcstatus == None:
        pc.set_status(args.pcstatus)
        pc.save(args.cache)
        sys.exit(0)

    if not args.pcids == None:
        pc.assign_sql_ids(args.pcids)
        pc.save(args.cache);
        sys.exit(0)


if (__name__=="__main__"):
  main()

