import argparse
import sys, traceback
import os

from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))
import lib.env
from lib.sitkaAPI import downloadUnzipTopo
from lib.loghelper import Logger
from lib.exception import DataException, MissingException, NetworkException

__version__="0.1"

def myMainMethod(topoDataFolder, xmlfile, visitID):
    """
    :param jsonFilePath:
    :param outputFolder:
    :param bVerbose:
    :return:
    """
    log = Logger("myMainMethod")

    # dothingA()
    log.info("I did thing A")
    # dothingB()
    log.info("I did thing B")
    # Write XML()
    log.info("I wrote my XML file")
    # writelogs()
    log.info("I wrote my log files")


def main():
    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('visitID', help='Visit ID', type=int)
    parser.add_argument('outputfolder', help='Path to output folder', type=str)
    parser.add_argument('--datafolder', help='(optional) Top level folder containing TopoMetrics Riverscapes projects', type=str)
    parser.add_argument('--verbose', help='Get more information in your logs.', action='store_true', default=False )
    args = parser.parse_args()

    # Make sure the output folder exists
    resultsFolder = os.path.join(args.outputfolder, "outputs")

    # Initiate the log file
    logg = Logger("Program")
    logfile = os.path.join(resultsFolder, "validation.log")
    xmlfile = os.path.join(resultsFolder, "validation.xml")
    logg.setup(logPath=logfile, verbose=args.verbose)

    # Initiate the log file
    log = Logger("Program")
    log.setup(logPath=logfile, verbose=args.verbose)

    try:
        # Make some folders if we need to:
        if not os.path.isdir(args.outputfolder):
            os.makedirs(args.outputfolder)
        if not os.path.isdir(resultsFolder):
            os.makedirs(resultsFolder)

        # If we need to go get our own topodata.zip file and unzip it we do this
        if args.datafolder is None:
            topoDataFolder = os.path.join(args.outputfolder, "inputs")
            fileJSON, projectFolder = downloadUnzipTopo(args.visitID, topoDataFolder)
        # otherwise just pass in a path to existing data
        else:
            projectFolder = args.datafolder

        finalResult = myMainMethod(projectFolder, xmlfile, args.visitID)
        sys.exit(finalResult)

    except (DataException, MissingException, NetworkException) as e:
        # Exception class prints the relevant information
        traceback.print_exc(file=sys.stdout)
        sys.exit(e.returncode)
    except AssertionError as e:
        log.error(e.message)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
    except Exception as e:
        log.error(e.message)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
