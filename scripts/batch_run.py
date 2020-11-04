import fnmatch
import argparse
import sys, traceback
import os
import sqlite3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../tools")))
from auxmetrics.auxmetrics import runAuxMetrics
from topometrics.topometrics import visitTopoMetrics
from topoauxmetrics.topoauxmetrics import visitTopoAuxMetrics
from validation.validation import validate
from lib.topoproject import TopoProject
import xml.etree.ElementTree as ET

def BatchRun(workbench, topoData, outputDir):

    dbCon = sqlite3.connect(workbench)
    dbCurs = dbCon.cursor()

    #watershedID = 6 # John Day
    watershedID = 30 # Yankee Fork
    jdTopo = [5174, 5167, 5214, 5215, 5203, 5216, 5204, 5217, 5205, 5206, 5219, 5207, 5168, 5221, 5211, 5222, 5209, 5210, 5212, 5213]
    #jdAux = [5169, 5170, 5171, 5260, 5172, 5261, 5173, 5174, 5167, 5214, 5215, 5203, 5216, 5204, 5217, 5205, 5206, 5219, 5207, 5168, 5221, 5211, 5222, 5209, 5210, 5212, 5213]

    #dbCurs.execute('SELECT VisitID, WatershedName, VisitYear, SiteName FROM vwMainVisitList WHERE (VisitYear = 2018) AND (WatershedID = ?)', [watershedID])
    dbCurs.execute('SELECT VisitID, WatershedName, VisitYear, SiteName FROM vwMainVisitList WHERE (VisitID IN ({0}))'.format(','.join(map(lambda x: str(x), jdTopo))))

    for row in dbCurs.fetchall():

        print 'Processing visit {0} at site {1}'.format(row[0], row[3])

        pathSlug = '{0}/{1}/{2}/VISIT_{3}'.format(row[2], row[1], row[3], row[0]).replace(' ', '')
        rootOutput = os.path.join(outputDir, pathSlug)

        if not os.path.isdir(rootOutput):
            os.makedirs(rootOutput)

        topoPath = os.path.join(topoData, pathSlug, 'Field Folders/Topo')
        projPath = getTopoPath(topoPath)

        if not projPath or not os.path.isdir(projPath):
            #raise Exception('No project found for project slug: ' + pathSlug)
            print 'No project found for project slug: ' + pathSlug
            continue

        # validate(projPath, os.path.join(rootOutput, 'validation.xml'), row[0])
        #visitTopoMetrics(row[0], os.path.join(rootOutput, 'topo_metrics.xml'), projPath, None, workbench, None)
        #runAuxMetrics(os.path.join(rootOutput, 'aux_metrics.xml'), None, row[0])
        visitTopoAuxMetrics(row[0], os.path.join(rootOutput, 'topoaux_metrics.xml'))

        print 'Completed visit {0} at site {1}'.format(row[0], row[3])


def getTopoPath(parentFolder):
    """ Sometimes the Topo data are nested in additional folders so use this
    function to dig into the expected folder looking for project.rs.xml
    """

    for root, dirnames, filenames in os.walk(parentFolder):
        for filename in fnmatch.filter(filenames, 'project.rs.xml'):
            return str(root)

    return None

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
