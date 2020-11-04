import fnmatch
import argparse
import sys, traceback
import os
import sqlite3
import xml.etree.ElementTree as ET
import csv

# The workbench database metric definitions use official CHaMP tier 1 and tier 2 types.
# However the CRITFC metric result files use their customized tier types. See critfc_2018.py
# for definitions.
#
# Use this list to specify substitutions. The first item in each tuple is the part of an
# CHaMP XPath and the second tuple item is the CRITFC alternate to use. Any metrics that
# contain these CHaMP XPath parts will be substituted. Use an empty CRITFC string to
# skip a metric altogether.
metricExceptions = [
    # ('ChannelUnitsTier1/SlowPool/', 'ChannelUnitsTier1/SlowWater/'),
    # ('ChannelUnitsTier1/FastTurbulent/', 'ChannelUnitsTier2/FT/'),
    # ('ChannelUnitsTier1/FastNonTurbulent/', 'ChannelUnitsTier2/FNT/'),
    # ('ChannelUnitsTier2/FNTGlide/', 'ChannelUnitsTier2/FNT/'),
    # ('ChannelUnitsTier1/FastNonTurbulentGlide/', 'ChannelUnitsTier2/FNT/'),
    # ('ChannelUnitsTier1/SmallSideChannel/', None)
]

# These are the schemas from the Workbench that we want to process
# Note that they are the topo metric QA schemas, not the final schemas
schemas = {'Visit': 1, 'ChannelUnit': 2, 'Tier1': 3, 'Tier2': 4}

def BatchRun(workbench, outputDir):

    # Open the CHaMP Workbench
    dbCon = sqlite3.connect(workbench)
    dbCurs = dbCon.cursor()

    # Load a list of topo metric result XML file tuples.
    resultXMLFiles = getMetricResultFilePaths(outputDir)

    # Loop over all schemas
    for schemaName, schemaID in schemas.iteritems():

        print 'Processing schema {0}...'.format(schemaName)

        # Get all the active metrics for this schema
        metricDefs = getMetricDefs(dbCurs, schemaID)

        # Create an ordered list of CSV column headings
        csvHeaders = ['Visit', 'Site']
        csvHeaders.extend(metric[1] for metric in metricDefs)

        # This will hold all the metric instances that will be written to CSV
        toCSV = []

        # Loop over all topo metric result XML files
        for resultFile in resultXMLFiles:

            # Get the root node for this schema. List will contain
            # single item for visit level. Multiple items for other dimensions.
            tree = ET.parse(resultFile[2])
            nodRoot = tree.findall(metricDefs[0][2])

            if len(nodRoot) == 1:
                # Visit level metrics
                instance = getVisitMetrics(metricDefs, resultFile[0], resultFile[1], nodRoot[0])
                if instance:
                    toCSV.append(instance)
            else:
                # Channel unit, tier 1, tier 2
                instanceList = getRepeatingMetrics(metricDefs, resultFile[0], resultFile[1], nodRoot)
                if instanceList:
                    toCSV.extend(instanceList)

        # Write a single CSV for this schema that contains all metric instances
        outputCSV = os.path.join(outputDir, '2019_yankee_fork_topo_{0}_metrics.csv'.format(schemaName))
        with open(outputCSV, 'wb') as f:  # Just use 'w' mode in 3.x
            w = csv.DictWriter(f, csvHeaders)
            w.writeheader()

            for instance in toCSV:
                w.writerow(instance)

    print "Process Completed successfully."

def getVisitMetrics(metrics, visit, site, nodRoot):
    """ Builds a single metric instance containing all metrics
        in the dictionary that occur under the nodRoot.

        This is used for visit level metrics and also
        individual instances of higher dimensional metrics
        such as tier 1, tier 2 and channel unit
    """

    # always put the visit and site on every instance
    instance = {'Visit': visit, 'Site': site}

    # Loop over all required metrics
    for metric in metrics:

        # Get the correct CRITFC XPath and skip metric if not needed
        xpath = getCRITFCXPath(metric[3])
        if not xpath:
            continue

        # Find the metric XML node
        nodMetric = nodRoot.find(xpath)
        if nodMetric is not None:
            instance[metric[1]] = nodMetric.text
        else:
            print('Missing metric ' + metric[1] + ': ' + xpath)

    return instance

def getRepeatingMetrics(metrics, visit, site, nodRoots):
    """ Gets a list of all instances of higher dimensional metrics
    such as tier 1, tier 2 and channel units.
    """

    instanceList = []

    # Loop over all root nodes. This will be all channel units or
    # all tier 1 or tier 2 types
    for nodRoot in nodRoots:
        instance = getVisitMetrics(metrics, visit, site, nodRoot)
        if instance:
            instanceList.append(instance)

    return instanceList


def getCRITFCXPath(xpath):
    """ See substitutions at top of file.
    This method takes a complete CHaMP XPath and replaces parts of it
    with the CRITFC alternative if the channel unit types are different.
    It returns None if CRITFC doesn't use the metric
    """

    # Loop over all CRITFC substitutions
    for sub in metricExceptions:

        if sub[0] in xpath:

            # Return None if CRITFC doesn't use the metric
            if not sub[1]:
                return None

            result = str(xpath).replace(sub[0], sub[1])
            return result

    return xpath


def getMetricResultFilePaths(parentFolder):
    """ Return a list of tuples defining all the top metric XML
    files that can be found recursively under the top level folder.
    """
    result = []

    for root, dirnames, filenames in os.walk(parentFolder):
        for filename in fnmatch.filter(filenames, 'topo_metrics.xml'):
            parts = os.path.basename(root).split('_')
            visit = int(parts[1])
            site = os.path.basename(os.path.dirname(root))
            tup = (visit, site, os.path.join(root, filename))

            result.append(tup)

    return result

def getMetricDefs(dbCurs, schema):
    """ Load all active metrics for the specified schema that have a valid XPath"""

    dbCurs.execute(
        'SELECT M.MetricID, DisplayNameShort, RootXPath, XPath' +
        ' FROM Metric_definitions M' +
        ' INNER JOIN Metric_Schema_Definitions MS ON M.MetricID = MS.MetricID' +
        ' INNER JOIN Metric_Schemas S ON MS.SchemaID = S.SchemaID' +
        ' WHERE (IsActive <> 0)' +
        ' AND (XPath IS NOT NULL) AND (S.SchemaID = {0})'.format(schema))

    metrics = []
    for row in dbCurs.fetchall():
        rootPath = './' + '/'.join(row[2].split('/')[2:])
        relativePath = row[3].replace(row[2], '')[1:]
        metrics.append((row[0], row[1], rootPath, relativePath))

    return metrics

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('workbench', help='Path to CHaMP Workbench.', type=str)
    parser.add_argument('outputDir', help='Top level folder containing topo metric XML files to process.', type=str)
    args = parser.parse_args()

    try:
        BatchRun(args.workbench, args.outputDir)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)

if __name__ == "__main__":
    main()
