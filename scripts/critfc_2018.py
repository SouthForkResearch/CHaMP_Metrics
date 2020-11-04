import fnmatch
import argparse
import sys, traceback
import os
import sqlite3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../tools")))
# from auxmetrics.auxmetrics import runAuxMetrics
from topometrics.topometrics import visitTopoMetrics
# from topoauxmetrics.topoauxmetrics import visitTopoAuxMetrics
# from validation.validation import validate
from lib.topoproject import TopoProject
import xml.etree.ElementTree as ET
from classes.TopoData import TopoData
from lib.channelunits import writeChannelUnitsToJSON
from lib.channelunits import dUnitDefs
from lib.shapefileloader import Shapefile
from lib.loghelper import Logger

# Channel Unit Definitions provided by Lauren 8 Jan 2019
# dUnitDefs = {
#     'Fast Water': ['FT', 'FNT'],
#     'Slow Water': ['PL', 'OC'],
#     'Special Case': ['DRY', 'Culv', 'MRSH']
# }

def BatchRun(workbench, topoData, outputDir):

    dbCon = sqlite3.connect(workbench)
    dbCurs = dbCon.cursor()

    # dbCurs.execute('SELECT VisitID, WatershedName, VisitYear, SiteName FROM vwMainVisitList WHERE (VisitID IN ({0}))'.format(','.join(map(lambda x: str(x), jdAux))))
    # for row in dbCurs.fetchall():

    log = Logger('Topo Metrics')
    log.setup(logPath=os.path.join(outputDir, "topo_metrics.log"), verbose=False)

    projects = getTopoProjects(topoData)
    print len(projects), 'topo projects found in', topoData
    rootOutput = os.path.join(outputDir, 'YankeeFork')
    print 'Outputing results to', rootOutput

    for project in projects:
        print(project)

        # if project[0] == 9028 or project[0] == 9027 or project[0] == 9023 or project[0] == 9022:
        #     continue

        outputFolder = project[3].replace(topoData, outputDir)

        if not os.path.isdir(outputFolder):
            os.makedirs(outputFolder)

        # Generate a Channel Units JSON file using the ShapeFile as the truth
        jsonFilePath = os.path.join(outputFolder, 'channel_units.json')
        createChannelUnitsJSON(project[3], project[0], jsonFilePath)

        # Calculate topo metrics
        visitTopoMetrics(project[0], os.path.join(outputFolder, 'topo_metrics.xml'), project[3], jsonFilePath, None, dUnitDefs)

    print(projects)

def createChannelUnitsJSON(topoDataFolder, visitID, jsonFilePath):

    topo = TopoData(topoDataFolder, visitID)
    topo.loadlayers()
    shpCU = Shapefile(topo.ChannelUnits)

    dUnits = {}
    feats = shpCU.featuresToShapely()
    for aFeat in feats:
        origTier1 = aFeat['fields']['Tier1']
        origTier2 = aFeat['fields']['Tier2']
        UtNum = aFeat['fields']['UnitNumber']

        finalTier1 = None
        for tier1 in dUnitDefs.keys():
            if tier1.lower() == origTier1.lower():
                finalTier1 = tier1
                break

        if not finalTier1:
            print('No Tier 1 channel unit type found')

        dUnits[UtNum] = (finalTier1, origTier2, 1)

    writeChannelUnitsToJSON(jsonFilePath, dUnits)


def getTopoProjects(parentFolder):
    """ Find all project.rs.xml in the top level folder
    """

    result = []

    for root, dirnames, filenames in os.walk(parentFolder):
        for filename in fnmatch.filter(filenames, 'project.rs.xml'):
            if 'VISIT_' not in root:
                continue
            parts = os.path.basename(root).split('_')
            tup = (int(parts[1]), parts[0].upper(), None, root)
            result.append(tup)

    return result

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('workbench', help='Path to CHaMP Workbench.', type=str)
    parser.add_argument('topoData', help='Top level folder containing unzipped topo data.', type=str)
    parser.add_argument('outputDir', help='OutputFolder.', type=str)
    args = parser.parse_args()

    try:
        BatchRun(args.workbench, args.topoData, args.outputDir)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)

if __name__ == "__main__":
    main()
