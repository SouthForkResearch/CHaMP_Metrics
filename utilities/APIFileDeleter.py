import argparse
import os
import logging
import sys, traceback
import re
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))
from lib.sitkaAPI import APIDelete, APIGet
from lib.exception import *
from lib import env
from lib.userinput import query_yes_no

"""

# THIS SCRIPT is DANGEROUS and intentionally hard to use.

"""

def fileDeleter(args):

    log = Logger("APIFileDeleter")

    if args.dryrun == False:
        foldertext = ""
        if args.folder is not None:
            foldertext = "FROM FOLDER '{}' ".format(args.folder)
        print "\n\n\nTHIS WILL DELETE ALL VISIT FILES ON THE API {}THAT MATCH THE PATTERN: '{}'".format(foldertext, args.pattern)
        if not query_yes_no("Are you sure?") or not query_yes_no("\nNo, seriously! You're about to delete data on CM.org. Are you sure!?? (hint: BE SURE!!!)"):
            print "wise choice"
            return
    else:
        log.info("== DRYRUN DETECTED ==")

    # Get all the visits we know about
    visitsraw = APIGet('visits')
    visitids = [v['id'] for v in visitsraw]
    visitids.sort()

    total = 0
    for vid in visitids:
        total += visitProcess(vid, args.pattern, args.folder, args.dryrun)

    print "Total Found: {}".format(total)

def visitProcess(visit, pattern, folder, dryrun):
    """
    PRocess the deletion for each individual visit
    :param visit:
    :param pattern:
    :param folder:
    :param dryrun:
    :return:
    """
    log = Logger("DELETE")
    total = 0
    try:
        if folder is None:
            files = APIGet('visits/{}/files'.format(visit))
        else:
            files = APIGet('visits/{}/folders/{}/files'.format(visit, folder))

        for fileObj in files:
            name = fileObj['name']
            if re.match(pattern, name):
                total += 1
                dryruntext = ""
                if dryrun == False:
                    APIDelete(fileObj['url'], absolute=True)
                else:
                    dryruntext = "(dryrun)"

                log.info("{} DELETED: {}".format(dryruntext, fileObj['url']))

    except MissingException, e:
        log.debug("No files found for visit {}".format(visit))

    return total

def main():
    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('pattern',
                        help='the regex matching the file you want to delete')
    parser.add_argument('--folder',
                        help='The sync file. Helps speed a process up to figure out which files to work with.',
                        type=str)
    parser.add_argument('--dryrun', help='Do nothing but go through and simulate what "WOULD" have happened.', action='store_true', default=False)
    parser.add_argument('--verbose', help = 'Get more information in your logs.', action='store_true', default=False)


    logg = Logger("APIFileDeleter")
    logfile = os.path.join(os.path.dirname(__file__), "FileDeleter.log")
    logg.setup(logPath=logfile, verbose=False)
    args = parser.parse_args()

    try:
        fileDeleter(args)

    except (MissingException, NetworkException, DataException) as e:
        traceback.print_exc(file=sys.stdout)
        sys.exit(e.returncode)
    except AssertionError as e:
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()