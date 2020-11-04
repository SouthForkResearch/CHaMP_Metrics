import argparse
import os

import sys, traceback
import csv
import numpy as np
from datetime import datetime

import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))
from lib import env
import logging
import json
import tempfile
import shutil
import re

from datetime import datetime
from lib.exception import DataException, MissingException, NetworkException
from lib.topoproject import TopoProject
from lib.sitkaAPI import downloadUnzipTopo, APIGet
from lib.loghelper import Logger

__version__="0.1"

APIDATEFIELD = "lastUpdated"

def topomover(jsonfile):
    log = Logger("TopoMover")
    visitsraw = APIGet('visits')
    visitsreorg = { v['id']: v for v in visitsraw }
    visitids = [v['id'] for v in visitsraw]
    visitids.sort()

    # Load the inventory
    inventory = {}
    if os.path.isfile(jsonfile):
        try:
            with open(jsonfile, "r") as f:
                inventory = json.load(f)
        except Exception, e:
            pass

    counter = 0
    for vid in visitids:
        strvid = str(vid)
        APIVisit = visitsreorg[vid]

        if strvid not in inventory:
            inventory[strvid] = {}

        # Decide if there's anything to do:
        if APIDATEFIELD not in inventory[strvid] \
                or APIstrtodate(APIVisit[APIDATEFIELD]) > APIstrtodate(inventory[strvid][APIDATEFIELD]):
            processZipFile(inventory[strvid], APIVisit)
        else:
            log.info( "Nothing to do" )
        counter+=1
        log.info( "STATUS: {:d}%  {:d}/{:d}".format( (100 * counter / len(visitids)), counter, len(visitids) ) )

        with open(jsonfile, "w+") as f:
            json.dump(inventory, f, indent=4, sort_keys=True)

def processZipFile(invVisit, APIVisit):
    dirpath = tempfile.mkdtemp()
    try:
        doupload = False
        # Copy some useful things from the API:
        for k in ['status', 'lastMeasurementChange', 'lastUpdated', 'name']:
            invVisit[k] = APIVisit[k]

        file, projpath = downloadUnzipTopo(APIVisit['id'], dirpath)

        topo = TopoProject(projpath)
        invVisit["topozip"] = True
        latestRealizationdate = latestRealizationDate(topo)

        if "latestRealization" not in invVisit or APIstrtodate(invVisit["latestRealization"]) >= latestRealizationdate:
            invVisit["latestRealization"] = APIdatetostr(latestRealizationdate)
            invVisit["size"] = file['size']
            uploadProjectToRiverscapes(dirpath, invVisit)

    except MissingException, e:
        invVisit["topozip"] = False
        invVisit["error"] = e.message
    except Exception, e:
        invVisit["error"] = e.message

    # Clean up
    shutil.rmtree(dirpath)


def uploadProjectToRiverscapes(dirpath, invVisit):
    from riverscapestools.s3.operations import S3Operation
    from riverscapestools.s3.walkers import s3BuildOps
    from riverscapestools.program import Program
    from riverscapestools.program import Project
    from riverscapestools.settings import defaults

    direction = S3Operation.Direction.UP
    program = Program(defaults.ProgramXML)
    projectObj = Project(dirpath, program.ProjectFile)

    try:
        keyprefix = projectObj.getPath(program)
        conf = {
            "delete": True,
            "force": False,
            "direction": direction,
            "localroot": dirpath,
            "keyprefix": keyprefix,
            "bucket": program.Bucket
        }
        s3ops = s3BuildOps(conf)

        for key in s3ops:
            s3ops[key].execute()

        invVisit["uploaded"] = True


    except Exception, e:
        invVisit["uploaded"] = False
        invVisit["error"] = e.message

def APIstrtodate(datestr):
    datestringparsed = re.match("(\d{4}-\d{2}-\d{2}T\d{1,2}:\d{2}:\d{2})", datestr).group(0)
    return datetime.strptime(datestringparsed, "%Y-%m-%dT%H:%M:%S")

def APIdatetostr(dateobj):
    return datetime.strftime(dateobj, "%Y-%m-%dT%H:%M:%S.%f")

def latestRealizationDate(topo):
    realizations = topo.domroot.findall('.//Topography')
    return min([datetime.strptime(t.attrib['dateCreated'], "%Y-%m-%d %H:%M:%S.%f") for t in realizations])


def main():
    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('--jsonfile',
                        help='The sync file. Helps speed a process up to figure out which files to work with.',
                        default="topomover.json",
                        type=str)
    parser.add_argument('--verbose', help = 'Get more information in your logs.', action='store_true', default=False)


    logg = Logger("CADExport")
    logfile = os.path.join(os.path.dirname(__file__), "TopoMover.log")
    logg.setup(logPath=logfile, verbose=False)
    logging.getLogger("boto3").setLevel(logging.ERROR)
    args = parser.parse_args()

    try:
        topomover(args.jsonfile)

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