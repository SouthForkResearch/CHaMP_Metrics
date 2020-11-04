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
from lib.shapefileloader import Shapefile
from lib.raster import Raster
from lib.exception import DataException, MissingException, NetworkException
from lib.topoproject import TopoProject
from lib.sitkaAPI import downloadUnzipTopo

__version__="0.0.4"

def hydroPrep(demPath, wsdemPath, thalwegPath, outputFolder, bVerbose):

    # Make sure the output folder exists
    if not os.path.isdir(outputFolder):
        os.mkdir(outputFolder)

    extents = {}
    extents['DEM'] = rasterToCSV(demPath, os.path.join(outputFolder, 'DEM.csv') )
    extents['WSEDEM'] = rasterToCSV(wsdemPath, os.path.join(outputFolder, 'WSEDEM.csv') )
    vectorToCSV(thalwegPath, os.path.join(outputFolder, 'Thalweg.csv') )

    # Write a metadata XML file that contains the extents
    writeXMLMetaData(extents, outputFolder)

def rasterToCSV(rasterPath, outputCSVPath):

    print "Writing raster {0} to {1}".format(os.path.basename(rasterPath), outputCSVPath)

    raster = Raster(rasterPath)
    npArr = raster.array

    # Retrieve and return the extent
    extent = {}
    extent['Top'] = raster.top
    extent['Left'] = raster.left
    extent['Right'] = raster.getRight()
    extent['Bottom'] = raster.getBottom()

    writer = csv.writer(open(outputCSVPath, 'wb'))
    header = ['x', 'y', 'value']
    writer.writerow(header)

    for i, iVal in enumerate(npArr):
        for j, jVal in enumerate(iVal):

            if not np.ma.is_masked(jVal):
                x = raster.left + (j * raster.cellWidth) + (raster.cellWidth / 2)
                y = raster.top  + (i * raster.cellHeight) + (raster.cellHeight / 2)
                writer.writerow([x, y, raster.array[i][j]])

    return extent

def vectorToCSV(shapefilePath, outputCSVPath):

    print "Writing vector {0} to {1}".format(os.path.basename(shapefilePath), outputCSVPath)

    clShp = Shapefile(shapefilePath)
    clList = clShp.featuresToShapely()

    with open(outputCSVPath, 'w') as csvfile:
        # write the header row
        csvfile.write('x,y\n')

        for aLine in clList:
            for aPoint in aLine['geometry'].coords:
                csvfile.write('{0},{1}\n'.format(aPoint[0],aPoint[1]))

def writeXMLMetaData(extents, outputFolder):

    projectTree = ET.ElementTree(ET.Element("HydroPrep"))
    project = projectTree.getroot()

    project.set('dateCreated', datetime.now().isoformat())

    #ET.SubElement(project, 'Site').text = inputs['Site']
    #ET.SubElement(project, 'Watershed').text = inputs['Watershed']

    for rasterName, extent in extents.iteritems():
        rasterNode = ET.SubElement(project, rasterName)
        ET.SubElement(rasterNode, 'Top').text = str(extent['Top'])
        ET.SubElement(rasterNode, 'Left').text = str(extent['Left'])
        ET.SubElement(rasterNode, 'Right').text = str(extent['Right'])
        ET.SubElement(rasterNode, 'Bottom').text = str(extent['Bottom'])

    rough_string = ET.tostring(project, encoding='utf8', method='xml')
    reparsed = minidom.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent="\t")
    xmlPath = os.path.join(outputFolder, "hydroprep.xml")
    print 'Hydro prep metadata XML written to {0}'.format(xmlPath)
    f = open(xmlPath, "w")
    f.write(pretty)
    f.close()


def main():
    # parse command line options
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest='mode', help='For help type `hydroprep.py manual -h`')

    # The manual subparser is for when we know explicit paths
    manual = subparsers.add_parser('manual', help='manual help')
    manual.add_argument('dem', help='DEM raster path', type=argparse.FileType('r'))
    manual.add_argument('wsdem', help='Water surface raster path', type=argparse.FileType('r'))
    manual.add_argument('thalweg', help='Thalweg ShapeFile path', type=argparse.FileType('r'))
    manual.add_argument('outputfolder', help='Output folder')
    manual.add_argument('--verbose', help='Get more information in your logs.', action='store_true', default=False)

    # The project subparser is when we want to pass in a project.rs.xml file
    project = subparsers.add_parser('project', help='project help')
    project.add_argument('visitID', help='Visit ID', type=int)
    project.add_argument('outputfolder', help='Path to output folder', type=str)
    project.add_argument('--datafolder', help='(optional) Top level folder containing TopoMetrics Riverscapes projects', type=str)
    project.add_argument('--verbose', help='Get more information in your logs.', action='store_true', default=False )

    args = parser.parse_args()

    try:
        if args.mode == "project":
            resultsFolder = os.path.join(args.outputfolder, "outputs")

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

            tp = TopoProject(projectFolder)
            funcargs = (tp.getpath("DEM"), tp.getpath("WaterSurfaceDEM"), tp.getpath("Thalweg"), resultsFolder, args.verbose)
        else:
            funcargs = (args.dem.name, args.wsdem.name, args.thalweg.name, args.outputfolder, args.verbose)

        hydroPrep(*funcargs)

    except (DataException, MissingException, NetworkException) as e:
        # Exception class prints the relevant information
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
