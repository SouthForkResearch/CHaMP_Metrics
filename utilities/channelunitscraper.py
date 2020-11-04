import argparse
import shutil
import errno
import os
import sys, traceback
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))
from lib import env
import logging
import json
import tempfile
from lib.exception import DataException, MissingException, NetworkException
from lib.topoproject import TopoProject
from lib.sitkaAPI import downloadUnzipTopo, APIGet, latestMetricInstance
from lib.loghelper import Logger
import ogr
from shapely.geometry import *

from lib.shapefileloader import Shapefile

__version__="0.1"

APIDATEFIELD = "lastUpdated"

def channelUnitScraper(outputDir, watersheds):

    visitData = {}
    for watershed, apiName in watersheds.iteritems():
        visitData[watershed] = {}

        loadVisitData(watershed, apiName, visitData[watershed])

    for watershed, visits in visitData.iteritems():
        outPath = os.path.join(outputDir, watershed.replace(' ', '') + ".shp")
        outShape = None

        featureID = 0
        for visitID, visit in visits.iteritems():

            if  len(visit['ChannelUnits']) < 1:
                continue

            try:
                dirpath = tempfile.mkdtemp()

                # Open the visit channel unit shapefile.
                # Need the spatial reference from one of the visits to create the output watershed shapefile
                try:
                    fileJSON, projPath = downloadUnzipTopo(visitID, dirpath)
                    topo = TopoProject(projPath)
                    cuPath = topo.getpath('ChannelUnits')
                except (DataException, MissingException), e:
                    print "Error retrieving channel units ShapeFile for visit {0}".format(visitID)
                    continue

                try:
                    shpCU = Shapefile(cuPath)
                except Exception, e:
                    print "Error OGR opening channel unit ShapeFile for visit {0}".format(visitID)
                    continue

                if not outShape:
                    # Create new ShapeFile for this watershed
                    outShape = Shapefile()
                    outShape.create(outPath, shpCU.spatialRef, geoType=ogr.wkbPolygon)

                    outShape.createField("ID", ogr.OFTInteger)
                    outShape.createField("Watershed", ogr.OFTString)
                    outShape.createField("Site", ogr.OFTString)
                    outShape.createField("VisitID", ogr.OFTInteger)
                    outShape.createField("SampleYear", ogr.OFTInteger)
                    outShape.createField("Org", ogr.OFTString)
                    outShape.createField("UnitNumber", ogr.OFTInteger)
                    outShape.createField("UnitArea", ogr.OFTReal)
                    outShape.createField("Tier1", ogr.OFTString)
                    outShape.createField("Tier2", ogr.OFTString)
                    outShape.createField("AvgSiteWid", ogr.OFTReal)
                    outShape.createField("ReachLen", ogr.OFTReal)

                # Loop over all channel unit polygons for this visit

                feats = shpCU.featuresToShapely()
                for aFeat in feats:
                    featureID += 1
                    cuNumber = aFeat['fields']['UnitNumber']

                    featureDefn = outShape.layer.GetLayerDefn()
                    outFeature = ogr.Feature(featureDefn)
                    outFeature.SetField('ID', featureID)
                    outFeature.SetField('Watershed', visit['Watershed'])
                    outFeature.SetField('Site', visit['Site'])
                    outFeature.SetField('VisitID', visitID)
                    outFeature.SetField('SampleYear', visit['SampleYear'])
                    outFeature.SetField('Org', visit['Organization'])
                    outFeature.SetField('AvgSiteWid', visit['AverageSiteWidth'])
                    outFeature.SetField('ReachLen', visit['TotalReachLength'])
                    outFeature.SetField('UnitNumber', cuNumber)
                    outFeature.SetField('Tier1', visit['ChannelUnits'][cuNumber]['Tier1'])
                    outFeature.SetField('Tier2', visit['ChannelUnits'][cuNumber]['Tier2'])
                    outFeature.SetField('UnitArea', aFeat['geometry'].area)
                    outFeature.SetGeometry(ogr.CreateGeometryFromJson(json.dumps(mapping(aFeat['geometry']))))
                    outShape.layer.CreateFeature(outFeature)

            finally:
                try:
                    shutil.rmtree(dirpath)  # delete directory
                except OSError as exc:
                    if exc.errno != errno.ENOENT:  # ENOENT - no such file or directory
                        raise  # re-raise exception


def loadVisitData(watershedName, apiWatershedName, visitData):

    apiWatersheds = APIGet('watersheds/' + apiWatershedName.lower())
    for site in apiWatersheds['sites']:
        apiSites = APIGet(site['url'], True)

        for visit in apiSites['visits']:

            # if len(visitData) > 1:
            #     return

            apiVisit = APIGet(visit['url'], absolute=True)

            visitData[apiVisit['id']] = {}
            visitData[apiVisit['id']]['Watershed'] = watershedName
            visitData[apiVisit['id']]['Site'] = apiVisit['siteName']
            visitData[apiVisit['id']]['VisitID'] = apiVisit['id']
            visitData[apiVisit['id']]['Organization'] = apiVisit['organizationName']
            visitData[apiVisit['id']]['SampleYear'] = apiVisit['sampleYear']
            visitData[apiVisit['id']]['ChannelUnits'] = {}

            try:
                apiChannelUnits = APIGet('visits/{0}/measurements/Channel Unit'.format(visit['id']))
                for apiCU in apiChannelUnits['values']:
                    cu = apiCU['value']
                    visitData[apiVisit['id']]['ChannelUnits'][cu['ChannelUnitNumber']] = {}
                    visitData[apiVisit['id']]['ChannelUnits'][cu['ChannelUnitNumber']]['Tier1'] = cu['Tier1']
                    visitData[apiVisit['id']]['ChannelUnits'][cu['ChannelUnitNumber']]['Tier2'] = cu['Tier2']

            except MissingException, e:
                print "Skipping {0} visit {1} because no channel unit data".format(watershedName, visit['id'])

            try:
                # Get the average site width and total reach length from the visit topo metrics
                apiTopoMetrics = APIGet('visits/{0}/metricschemas/QA - Topo Visit Metrics/metrics'.format(visit['id']))
                visitData[apiVisit['id']]['AverageSiteWidth'] = getTopoMetricValue(apiTopoMetrics,
                                                                                              'WetWdth_Avg')
                visitData[apiVisit['id']]['TotalReachLength'] = getTopoMetricValue(apiTopoMetrics,
                                                                                              'Lgth_Wet')
            except MissingException, e:
                visitData[apiVisit['id']]['AverageSiteWidth'] = None
                visitData[apiVisit['id']]['TotalReachLength'] = None

def getTopoMetricValue(visitMetricList, metricName):

    if visitMetricList and len(visitMetricList) > 0:
        latestTopoMetrics = latestMetricInstance(visitMetricList)
        return latestTopoMetrics[metricName]

    return None

def main():
    # parse command line options
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--jsonfile',
    #                     help='The sync file. Helps speed a process up to figure out which files to work with.',
    #                     default="topomover.json",
    #                     type=str)
    # parser.add_argument('--verbose', help = 'Get more information in your logs.', action='store_true', default=False)
    #
    #
    # logg = Logger("CADExport")
    # logfile = os.path.join(os.path.dirname(__file__), "TopoMover.log")
    # logg.setup(logPath=logfile, verbose=False)
    # logging.getLogger("boto3").setLevel(logging.ERROR)
    # args = parser.parse_args()

    try:
        channelUnitScraper('D:\CHaMP\Temp', {'Minam' : 'minam', 'Upper Grande Ronde': 'ugr'})

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