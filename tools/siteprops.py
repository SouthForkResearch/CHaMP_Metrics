import argparse
import json
import sys, traceback
import ogr
import os
import copy
from datetime import datetime
import re
from shapely.geometry import *

from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))
from lib.shapefileloader import Shapefile
from lib.raster import Raster
from lib.exception import *
from lib.loghelper import Logger
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from lib.sitkaAPI import APIGet, downloadUnzipTopo
from lib.topoproject import TopoProject
from lib import env

__version__="0.0.4"

def sitePropsGenerator(siteid, resultsFolder, topoDataFolder, bVerbose):

    visitObj = getAllVisits(siteid)
    vids = [int(v['name']) for v in visitObj]
    visits = downloadExtractParseVisits(vids, topoDataFolder)

    processSurveyExtent(visits, resultsFolder)
    concatenateControlPoints(visits, resultsFolder)
    dExtents = getDEMExtents(visits)

    writeXMLMetaData(visits, dExtents, resultsFolder)

def writeXMLMetaData(projects, dExtents, outputFolder):

    projectTree = ET.ElementTree(ET.Element("SiteProps"))
    project = projectTree.getroot()

    project.set('dateCreated', datetime.now().isoformat())

    # These values will be the same across visits so just pull the first one
    ET.SubElement(project, 'Site').text = projects[0]['project'].getMeta('Site')
    ET.SubElement(project, 'Watershed').text = projects[0]['project'].getMeta('Watershed')

    unionNode = ET.SubElement(project,'UnionExtent')
    ET.SubElement(unionNode, 'Top').text = str(dExtents['OuterExtent']['Top'])
    ET.SubElement(unionNode, 'Left').text = str(dExtents['OuterExtent']['Left'])
    ET.SubElement(unionNode, 'Right').text = str(dExtents['OuterExtent']['Right'])
    ET.SubElement(unionNode, 'Bottom').text = str(dExtents['OuterExtent']['Bottom'])

    visitsNode = ET.SubElement(project, 'Visits')
    for visitID, dExtent in dExtents.iteritems():
        visitNode = ET.SubElement(visitsNode, 'Visit')
        visitNode.set('id', str(visitID))

        ET.SubElement(visitNode, 'Top').text =str(dExtent['Top'])
        ET.SubElement(visitNode, 'Left').text =str(dExtent['Left'])
        ET.SubElement(visitNode, 'Right').text =str(dExtent['Right'])
        ET.SubElement(visitNode, 'Bottom').text =str(dExtent['Bottom'])

    rough_string = ET.tostring(project, encoding='utf-8', method='xml')
    reparsed = minidom.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent="\t")
    xmlPath = os.path.join(outputFolder, "siteprops.xml")
    print 'Site properties generator metadata XML written to {0}'.format(xmlPath)
    f = open(xmlPath, "w")
    f.write(pretty)
    f.close()

def processSurveyExtent(projects, outputFolder):

    spatialRef = None
    unionPoly = None
    intersectPoly = None

    for proj in projects:
        extentPath = proj['project'].getpath('SurveyExtent')
        vid = proj['visit']
        if not os.path.isfile(extentPath):
            print "Warning: Missing Survey Extent ShapeFile for Visit {0}".format(vid)
            continue

        seShp = Shapefile(extentPath)
        seList = seShp.featuresToShapely()
        spatialRef = seShp.spatialRef

        for sePolygon in seList:

            if unionPoly:
                unionPoly = unionPoly.union(sePolygon['geometry'])
            else:
                unionPoly = sePolygon['geometry']

            if intersectPoly:
                intersectPoly = intersectPoly.intersection(sePolygon['geometry'])
            else:
                intersectPoly = sePolygon['geometry']


    if not unionPoly:
        raise DataException("No survey extent union polygon derived from visits")

    if not intersectPoly:
        raise DataException("No survey extent intersect polygon derived from visits")

    unionPath = os.path.join(outputFolder, "SurveyExtentUnion.shp")
    print "Writing survey extent union to {0}".format(unionPath)
    writeShapeToShapeFile(unionPath, unionPoly, spatialRef)

    intersectPath = os.path.join(outputFolder, "SurveyExtentIntersect.shp")
    print "Writing survey extent intersection to {0}".format(intersectPath)
    writeShapeToShapeFile(intersectPath, intersectPoly, spatialRef)

def writeShapeToShapeFile(outputPath, aPolygon, spatialRef):

    # Write the polygon to ShapeFile (note: ShapeFile handles deleting existing file)
    outShape = Shapefile()
    outShape.create(outputPath, spatialRef, geoType=ogr.wkbPolygon)
    outShape.createField("ID", ogr.OFTInteger)

    # The main centerline gets written first
    featureDefn = outShape.layer.GetLayerDefn()
    outFeature = ogr.Feature(featureDefn)
    ogrPolygon = ogr.CreateGeometryFromJson(json.dumps(mapping(aPolygon)))
    outFeature.SetGeometry(ogrPolygon)
    outFeature.SetField('ID', 1)
    outShape.layer.CreateFeature(outFeature)

def concatenateControlPoints(projects, outputFolder):

    spatialRef = None
    cpList = []

    for proj in projects:
        controlPointsPath = proj['project'].getpath('Control_Points')
        vid = proj['visit']

        cpShp = Shapefile(controlPointsPath)
        visitCPList = cpShp.featuresToShapely()
        spatialRef = cpShp.spatialRef

        for aPoint in visitCPList:
            cpItems = {}
            cpItems['geometry'] = aPoint['geometry']
            cpItems['fields'] = {}

            cpItems['fields']['VisitID'] = int(vid)
            cpItems['fields']['PointNum'] = getFieldValue(aPoint['fields'], ['Point_Numb', 'POINT_NUMB', 'PointNumb', 'POINT_NUM', 'POINT'])
            cpItems['fields']['Code'] = getFieldValue(aPoint['fields'], ['DESCRIPTIO', 'Descriptio', 'Code'])
            cpItems['fields']['Type'] = getFieldValue(aPoint['fields'], ['Type', 'TYPE'])

            cpList.append(cpItems)

    outputPath = os.path.join(outputFolder, "AllVisitControlPoints.shp")
    print "Writing combined control points to {0}".format(outputPath)
    outShape = Shapefile()
    outShape.create(outputPath, spatialRef, geoType=ogr.wkbPointZM)

    outShape.createField("ID", ogr.OFTInteger)
    outShape.createField("VisitID", ogr.OFTInteger)
    outShape.createField("PointNum", ogr.OFTString)
    outShape.createField("Code", ogr.OFTString)
    outShape.createField("Type", ogr.OFTString)

    id = 1
    for aCP in cpList:

        featureDefn = outShape.layer.GetLayerDefn()
        outFeature = ogr.Feature(featureDefn)
        ogrPolygon = ogr.CreateGeometryFromJson(json.dumps(mapping(aCP['geometry'])))
        outFeature.SetGeometry(ogrPolygon)
        outFeature.SetField('ID', id)
        id += 1

        for fieldName, fieldValue in aCP['fields'].iteritems():
            outFeature.SetField(fieldName, fieldValue)

        outShape.layer.CreateFeature(outFeature)

def getDEMExtents(projects):

    outerExtent = {'Top' : None, 'Left' : None, 'Right' : None, 'Bottom' : None}
    extents = {}

    for proj in projects:
        dempath = proj['project'].getpath('DEM')
        vid = proj['visit']

        dem = Raster(dempath)

        extents[vid] = {
            'Top': dem.top,
            'Left': dem.left,
            'Right': dem.getRight(),
            'Bottom': dem.getBottom()
        }


        if outerExtent['Top']:
            outerExtent['Top'] = max(dem.top, outerExtent['Top'])
        else:
            outerExtent['Top'] = dem.top

        if outerExtent['Left']:
            outerExtent['Left'] = min(dem.left, outerExtent['Left'])
        else:
            outerExtent['Left'] = dem.left

        if outerExtent['Right']:
            outerExtent['Right'] = max(dem.getRight(), outerExtent['Right'])
        else:
            outerExtent['Right'] = dem.getRight()

        if outerExtent['Bottom']:
            outerExtent['Bottom'] = min(dem.getBottom(), outerExtent['Bottom'])
        else:
            outerExtent['Bottom'] = dem.getBottom()

    extents['OuterExtent'] = copy.deepcopy(outerExtent)
    return extents


def downloadExtractParseVisits(visits, outputFolder):
    log = Logger('Downloading')
    log.info("Downloading all visits from the API")

    projects = []
    for visit in visits:

        try:
            extractpath = os.path.join(outputFolder, 'VISIT_{}'.format(visit))
            projpath = os.path.join(extractpath, 'project.rs.xml')
            downloadUnzipTopo(visit, extractpath)

            proj = TopoProject(extractpath)

            if proj.isrsproject:
                projects.append({"project": proj, "visit": visit})
            else:
                log.error("File not found: {}".format(projpath))
                raise DataException("Missing Project File")

        # Just move on if something fails
        except Exception, e:
            pass

    # If we didn't get anything back then it's time to freak out a little
    if len(projects) == 0:
        raise DataException("No TopoData.zip files found for any visit")

    return projects

def getAllVisits(siteID):
    log = Logger('Visits')
    log.info("Getting all visits for site: {}".format(siteID))

    mangledSiteID = re.sub('[\s_-]', '', siteID)

    siteData = APIGet('sites/{}'.format(mangledSiteID))

    if 'visits' not in siteData or len(siteData['visits']) == 0:
        raise MissingException("No visits found for site `{}`.".format(siteID))

    return [visit for visit in siteData['visits'] if visit['sampleDate'] is not None]

def getFieldValue(dFields, lPossibleNames):

    for actualName in dFields:
        for possibleName in lPossibleNames:
            if actualName.lower() == possibleName.lower():
                return str(dFields[actualName])

    return ""


def main():
    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('siteid', help='the id of the site to use (no spaces)',type=str)
    parser.add_argument('outputfolder', help='Output folder')
    parser.add_argument('--logfile', help='Get more information in your logs.', default="", type=str)
    parser.add_argument('--verbose', help = 'Get more information in your logs.', action='store_true', default=False)

    args = parser.parse_args()

    # Make sure the output folder exists
    resultsFolder = os.path.join(args.outputfolder, "outputs")
    topoDataFolder = os.path.join(args.outputfolder, "inputs")

    if not os.path.isdir(args.outputfolder):
        os.makedirs(args.outputfolder)
    if not os.path.isdir(resultsFolder):
        os.makedirs(resultsFolder)
    if not os.path.isdir(topoDataFolder):
        os.makedirs(topoDataFolder)

    # Initiate the log file
    if args.logfile == "":
        logfile = os.path.join(resultsFolder, "siteproperties.log")
    else:
        logfile = args.logfile

    logg = Logger("SiteProperties")
    logg.setup(logPath=logfile, verbose=args.verbose)

    try:
        sitePropsGenerator(args.siteid, resultsFolder, topoDataFolder, args.verbose)

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
