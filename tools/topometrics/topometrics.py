import argparse
import sys, traceback
import os

from classes.TopoData import TopoData
from methods.thalweg import ThalwegMetrics
from methods.centerline import CenterlineMetrics
from methods.channelunit import ChannelUnitMetrics
from methods.waterextent import WaterExtentMetrics
from methods.crosssection import CrossSectionMetrics
from methods.island import IslandMetrics
from methods.raster import RasterMetrics
from methods.bankfull import BankfullMetrics

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from lib import env
from lib.metricxmloutput import writeMetricsToXML, integrateMetricDictionary, integrateMetricList
from lib.loghelper import Logger
from lib.sitkaAPI import downloadUnzipTopo
from lib.channelunits import loadChannelUnitsFromAPI, loadChannelUnitsFromJSON, loadChannelUnitsFromSQLite
from lib.exception import DataException, MissingException, NetworkException

__version__ = "0.0.4"

def visitTopoMetrics(visitID, metricXMLPath, topoDataFolder, channelunitsfile, workbenchdb, channelUnitDefs):

    log = Logger('Metrics')
    log.info("Topo topometrics for visit {0}".format(visitID))

    # Load the topo data object that specifies the full paths to each data layer
    log.info("Loading topo data from {0}".format(topoDataFolder))

    topo = TopoData(topoDataFolder, visitID)
    topo.loadlayers()

    # Load the channel unit information from the argument XML file
    if channelunitsfile is not None:
        channelUnitInfo = loadChannelUnitsFromJSON(channelunitsfile)
    elif workbenchdb is not None:
        channelUnitInfo = loadChannelUnitsFromSQLite(visitID, workbenchdb)
    else:
        channelUnitInfo = loadChannelUnitsFromAPI(visitID)

    # This is the dictionary for all topometrics to this visit. This will get written to XML when done.
    visitMetrics = {}

    # Loop over all the channels defined in the topo data (wetted and bankfull)
    for channelName, channel in topo.Channels.iteritems():
        log.info("Processing topometrics for {0} channel".format(channelName.lower()))

        # Dictionary for the topometrics in this channel (wetted or bankfull)
        dChannelMetrics = {}

        metrics_cl = CenterlineMetrics(channel.Centerline)
        integrateMetricDictionary(dChannelMetrics, 'Centerline', metrics_cl.metrics)

        metrics_we = WaterExtentMetrics(channelName, channel.Extent, channel.Centerline, topo.Depth)
        integrateMetricDictionary(dChannelMetrics, 'WaterExtent', metrics_we.metrics)

        metrics_cs = CrossSectionMetrics(channel.CrossSections, topo.Channels[channelName].Extent, topo.DEM, 0.1)
        integrateMetricDictionary(dChannelMetrics, 'CrossSections', metrics_cs.metrics)

        metrics_i = IslandMetrics(channel.Islands)
        integrateMetricDictionary(dChannelMetrics, 'Islands', metrics_i.metrics)

        # Put topometrics for this channel into the visit metric dictionary keyed by the channel (wetted or bankfull)
        integrateMetricDictionary(visitMetrics, channelName, dChannelMetrics)

        log.info("{0} channel topometrics complete".format(channelName))

    metrics_thal = ThalwegMetrics(topo.Thalweg, topo.Depth, topo.WaterSurface, 0.1, visitMetrics)
    integrateMetricDictionary(visitMetrics, 'Thalweg', metrics_thal.metrics)

    # Channel units creates four groupings of topometrics that are returned as a Tuple
    cuResults = ChannelUnitMetrics(topo.ChannelUnits, topo.Thalweg, topo.Depth, visitMetrics, channelUnitInfo, channelUnitDefs)
    integrateMetricList(visitMetrics, 'ChannelUnits', 'Unit', cuResults.metrics['resultsCU'])
    integrateMetricDictionary(visitMetrics, 'ChannelUnitsTier1', cuResults.metrics['ResultsTier1'])
    integrateMetricDictionary(visitMetrics, 'ChannelUnitsTier2', cuResults.metrics['ResultsTier2'])
    integrateMetricDictionary(visitMetrics, 'ChannelUnitsSummary', cuResults.metrics['ResultsChannelSummary'])

    temp = RasterMetrics(topo.Depth)
    integrateMetricDictionary(visitMetrics, 'WaterDepth', temp)

    temp = RasterMetrics(topo.DEM)
    integrateMetricDictionary(visitMetrics, "DEM", temp)

    temp = RasterMetrics(topo.Detrended)
    integrateMetricDictionary(visitMetrics, "Detrended", temp)

    # special bankfull metrics appending to existing dictionary entry
    visitMetrics['Bankfull']['WaterExtent'].update(BankfullMetrics(topo.DEM, topo.Detrended, topo.TopoPoints))

    # Metric calculation complete. Write the topometrics to the XML file
    writeMetricsToXML(visitMetrics, visitID, topoDataFolder, metricXMLPath, "TopoMetrics", __version__)

    log.info("Metric calculation complete for visit {0}".format(visitID))
    return visitMetrics

def main():
    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('visitID', help='Visit ID', type=int)
    parser.add_argument('outputfolder', help='Path to output folder', type=str)
    parser.add_argument('--channelunitsjson', help='(optional) json file to load channel units from', type=str)
    parser.add_argument('--workbenchdb', help='(optional) sqlite db to load channel units from', type=str)
    parser.add_argument('--datafolder', help='(optional) Top level folder containing TopoMetrics Riverscapes projects', type=str)
    parser.add_argument('--verbose', help='Get more information in your logs.', action='store_true', default=False )
    args = parser.parse_args()

    # Make sure the output folder exists
    resultsFolder = os.path.join(args.outputfolder, "outputs")

    # Initiate the log file
    logg = Logger("Program")
    logfile = os.path.join(resultsFolder, "topo_metrics.log")
    xmlfile = os.path.join(resultsFolder, "topo_metrics.xml")
    logg.setup(logPath=logfile, verbose=args.verbose)

    try:
        # Make some folders if we need to:
        if not os.path.isdir(args.outputfolder):
            os.makedirs(args.outputfolder)
        if not os.path.isdir(resultsFolder):
            os.makedirs(resultsFolder)

        projectFolder = ""
        # If we need to go get our own topodata.zip file and unzip it we do this
        if args.datafolder is None:
            topoDataFolder = os.path.join(args.outputfolder, "inputs")
            fileJSON, projectFolder = downloadUnzipTopo(args.visitID, topoDataFolder)
        # otherwise just pass in a path to existing data
        else:
            projectFolder = args.datafolder

        dMetricsObj = visitTopoMetrics(args.visitID, xmlfile, projectFolder, args.channelunitsjson, args.workbenchdb)

    except (DataException, MissingException, NetworkException) as e:
        # Exception class prints the relevant information
        traceback.print_exc(file=sys.stdout)
        sys.exit(e.returncode)
    except AssertionError as e:
        logg.error(e.message)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
    except Exception as e:
        logg.error(e.message)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()