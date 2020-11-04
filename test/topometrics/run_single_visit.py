import os
import argparse
import sys
from lib.channelunits import createChannelUnitJSONFile
from tools.topometrics.topometrics import visitTopoMetrics

def runSingleVisit(visitID, visitFolder, visitOutputFolder, workbenchDB, bVerbose):

    xmlFile = os.path.join(visitOutputFolder, "topometrics.xml")
    logFile = os.path.join(visitOutputFolder, "topometrics.log")
    chaFile = os.path.join(visitOutputFolder, "channelunits.json")

    createChannelUnitJSONFile(visitID, workbenchDB, chaFile)

    visitTopoMetrics(visitFolder, visitID, xmlFile, chaFile)

if __name__ == "__main__":

    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('visitID', help='Visit ID')
    parser.add_argument('visitFolder', help='Visit folder containing Harold results')
    parser.add_argument('outputfolder', help='OUTPUT folder where visit results will be written')
    parser.add_argument('workbench', help='Path to Workbench SQLite database', type=argparse.FileType('r'))
    parser.add_argument('--verbose', help = 'Get more information in your logs.', action='store_true', default=False)

    args = parser.parse_args()

    if not args.visitID or not args.visitFolder or not args.outputfolder or not args.workbench:
        print "ERROR: Missing arguments"
        parser.print_help()
        exit(0)

    try:
        dMetrics = runSingleVisit(args.visitID, args.visitFolder, args.outputfolder, args.workbench.name, args.verbose)

    except AssertionError as e:
        sys.exit(0)
    except Exception as e:
        raise
        sys.exit(0)
