import argparse
import sys, traceback
import os
import sqlite3
from xml.etree import ElementTree as ET
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))
import time
import traceback
import json
from lib.env import setEnvFromFile 
from lib.sitkaAPI import APICall
from lib.loghelper import Logger
from tools.validation import validation
from tools.topometrics import topometrics
from tools.cad_export import export_cad_files
from tools.hydroprep import hydroPrep
from tools.hydrol_model_export import export_hydro_model
from tools.substrate_raster import generate_substrate_raster
from tools.bankfull_metrics import bankfull_metrics

__version__ = "0.1"


def main():
    """Run one or more models on local CHaMP/AEM visits. Make sure command prompt is open with the appropriate
    environment for the model(s) to be run."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('outputfolder', help='Path to output folder', type=str)
    parser.add_argument('-v', '--validation', help="Run Validation", action='store_true', default=False)
    parser.add_argument('-m', '--topometrics', help="Run Topo Metrics", action='store_true', default=False)
    parser.add_argument('-y', '--hydroprep', help="Run Hydro Prep", action='store_true', default=False)
    parser.add_argument('-e', '--hydroexport', help="Run Hydro Model GIS export", action='store_true', default=False)
    parser.add_argument('-p', '--siteprops', help="Run Topo Site Properties", action='store_true', default=False)
    parser.add_argument('-a', '--topoauxmetrics', help="Run Topo + Aux Metrics", action='store_true', default=False)
    parser.add_argument('-c', '--cadexport', help="Run Cad Export", action='store_true', default=False)
    parser.add_argument('-s', '--substrate', help="Run Substrate Raster at D84", action='store_true', default=False)
    parser.add_argument('-b', '--bankfull', help='Run Bankfull Metrics', action='store_true', default=False)
    parser.add_argument('--sourcefolder', help='(optional) Top level folder containing Topo Riverscapes projects', type=str)
    parser.add_argument('--years', help='(Optional) Years. One or comma delimited', type=str)
    parser.add_argument('--watersheds', help='(Optional) Watersheds. One or comma delimited', type=str)
    parser.add_argument('--sites', help='(Optional) Sites. One or comma delimited', type=str)
    parser.add_argument('--visits', help='(Optional) Visits. One or comma delimited', type=str)
    parser.add_argument('--di', help="(Optional) Di values for substrate (default=84). One or comma delimited", type=str)
    parser.add_argument('--hydrofolder', help='(Optional) source folder for hydro model resutls (hydroexport only)', type=str)
    parser.add_argument('--logfile', help='(Optional) output log db for batches', type=str)
    parser.add_argument('--verbose', help='Get more information in your logs.', action='store_true', default=False)

    args = parser.parse_args()

    yearsFilter = args.years.split(",") if args.years is not None else None
    sitesFilter = args.sites.split(",") if args.sites is not None else None
    watershedsFilter = args.watersheds.split(",") if args.watersheds is not None else None
    visitsFilter = args.visits.split(",") if args.visits is not None else None
    di_values = [int(d) for d in args.di.split(",")] if args.di is not None else [84]

    # Make sure the output folder exists
    if not os.path.isdir(args.outputfolder):
        os.makedirs(args.outputfolder)

    # Set up log table - could be same db, but different table.
    logdb = SqliteLog(os.path.join(args.outputfolder, "export_log.db") if args.logfile is None else args.logfile)
    if args.bankfull:
        logdb.add_bankfull_metrics_table()

    setEnvFromFile(r"D:\.env")
    
    # Walk through folders
    for dirname, dirs, filenames in os.walk(args.sourcefolder):
        for filename in [os.path.join(dirname, name) for name in filenames]:
            if os.path.basename(filename) == "project.rs.xml":
                print filename
                # Get project details
                tree = ET.parse(filename)
                root = tree.getroot()
                visitid = root.findtext("./MetaData/Meta[@name='Visit']") if root.findtext("./MetaData/Meta[@name='Visit']") is not None else root.findtext("./MetaData/Meta[@name='VisitID']")
                siteid = root.findtext("./MetaData/Meta[@name='Site']") if root.findtext("./MetaData/Meta[@name='Site']") is not None else root.findtext("./MetaData/Meta[@name='SiteName']")
                watershed = root.findtext("./MetaData/Meta[@name='Watershed']")
                year = root.findtext("./MetaData/Meta[@name='Year']") if root.findtext("./MetaData/Meta[@name='Year']") is not None else root.findtext("./MetaData/Meta[@name='FieldSeason']")
                if root.findtext("ProjectType") == "Topo":
                    if (yearsFilter is None or year in yearsFilter) and \
                       (watershedsFilter is None or watershed in watershedsFilter) and \
                       (sitesFilter is None or siteid in sitesFilter) and \
                       (visitsFilter is None or visitid in visitsFilter):
                        from lib.topoproject import TopoProject
                        topo_project = TopoProject(filename)
                        project_folder = dirname
                        # Make visit level output folder
                        resultsFolder = os.path.join(args.outputfolder, year, watershed, siteid, "VISIT_{}".format(str(visitid)))#, "models")
                        if not os.path.isdir(resultsFolder):
                            os.makedirs(resultsFolder)
                        if args.validation:
                            try:
                                validationfolder = os.path.join(resultsFolder, "validation")
                                if not os.path.isdir(validationfolder):
                                    os.makedirs(validationfolder)
                                logg = Logger("Program")
                                logfile = os.path.join(validationfolder, "validation.log")
                                xmlfile = os.path.join(validationfolder, "validation.xml")
                                logg.setup(logPath=logfile, verbose=args.verbose)
                                # Initiate the log file
                                log = Logger("Program")
                                log.setup(logPath=logfile, verbose=args.verbose)
                                v_result = validation.validate(project_folder, xmlfile, visitid)
                                logdb.write_log(year,watershed, siteid, visitid, "Validation", str(v_result), xmlfile)
                            except Exception as e:
                                logdb.write_log(year, watershed, siteid, visitid, "Validation", "Exception", traceback.format_exc())
                        if args.topometrics:
                            try:
                                topometricsfolder = os.path.join(resultsFolder, "topo_metrics")
                                if not os.path.isdir(topometricsfolder):
                                    os.makedirs(topometricsfolder)
                                logg = Logger("Program")
                                logfile = os.path.join(topometricsfolder, "topo_metrics.log")
                                xmlfile = os.path.join(topometricsfolder, "topo_metrics.xml")
                                logg.setup(logPath=logfile, verbose=args.verbose)
                                # Initiate the log file
                                log = Logger("Program")
                                log.setup(logPath=logfile, verbose=args.verbose)
                                #tm_result = topometrics.visitTopoMetrics(visitid, xmlfile, project_folder)
                                #logdb.write_log(year,watershed, siteid, visitid, "TopoMetrics", str(tm_result), xmlfile)
                            except:
                                logdb.write_log(year, watershed, siteid, visitid, "TopoMetrics", "Exception", traceback.format_exc())

                        if args.hydroprep:
                            try:
                                hydroprepfolder = os.path.join(resultsFolder, "Hydro", "HydroModelInputs", "artifacts")
                                if not os.path.isdir(hydroprepfolder):
                                    os.makedirs(hydroprepfolder)
                                logg = Logger("Program")
                                logfile = os.path.join(hydroprepfolder, "hydroprep.log")
                                xmlfile = os.path.join(hydroprepfolder, "hydroprep.xml")
                                logg.setup(logPath=logfile, verbose=args.verbose)
                                # Initiate the log file
                                log = Logger("Program")
                                log.setup(logPath=logfile, verbose=args.verbose)
                                dem = topo_project.getpath("DEM")
                                wsdem = topo_project.getpath("WaterSurfaceDEM")
                                thalweg = topo_project.getpath("Thalweg")

                                result = hydroPrep(dem, wsdem, thalweg, hydroprepfolder, True)
                                logdb.write_log(year, watershed, siteid, visitid, "HydroPrep", str(result), xmlfile)
                            except:
                                logdb.write_log(year, watershed, siteid, visitid, "HydroPrep", "Exception",
                                                traceback.format_exc())
                        if args.siteprops:
                            try:
                                pass
                            except:
                                pass
                        if args.topoauxmetrics:
                            try:
                                pass
                            except:
                                pass
                        if args.cadexport:
                            try:
                                cadexportfolder = os.path.join(resultsFolder, "CADExport")
                                if os.path.isdir(cadexportfolder):
                                    os.makedirs(cadexportfolder)
                                logg = Logger("Program")
                                logfile = os.path.join(cadexportfolder, "cad_export.log")
                                xmlfile = os.path.join(cadexportfolder, "cad_export.xml")
                                logg.setup(logPath=logfile, verbose=args.verbose)
                                # Initiate the log file
                                log = Logger("Program")
                                log.setup(logPath=logfile, verbose=args.verbose)
                                ce_result = export_cad_files(filename, cadexportfolder)
                                logdb.write_log(year, watershed, siteid, visitid, "CadExport", "Success", xmlfile)
                            except:
                                logdb.write_log(year, watershed, siteid, visitid, "CadExport", "Exception",
                                                traceback.format_exc())
                        if args.substrate:
                            channel_units_json = path.join(project_folder, "ChannelUnits.json")
                            if not os.path.isfile(channel_units_json):
                                url = r"/visits/{}/measurements/Substrate%20Cover".format(str(visitid))
                                dict_occular = APICall(url)#, channel_units_json)
                            else:
                                dict_occular = json.load(open(channel_units_json, 'rt'))
                            try:
                                substratefolder = os.path.join(resultsFolder, "substrateD")
                                if not os.path.isdir(substratefolder):
                                    os.makedirs(substratefolder)
                                logg = Logger("Program")
                                logfile = os.path.join(substratefolder, "substrate.log")
                                xmlfile = os.path.join(substratefolder, "substrate.xml")
                                logg.setup(logPath=logfile, verbose=args.verbose)
                                result = generate_substrate_raster(project_folder, substratefolder, di_values, dict_occular)
                                logdb.write_log(year, watershed, siteid, visitid, "SubstrateD".format(), str(result), xmlfile)
                            except:
                                logdb.write_log(year, watershed, siteid, visitid, "SubstrateD".format(),
                                                "Exception", traceback.format_exc())

                        if args.hydroexport:
                            hydrobasefolder = args.hydrofolder if args.hydrofolder else args.sourcefolder
                            hydrosearchfolder = os.path.join(hydrobasefolder, os.path.dirname(os.path.relpath(dirname, args.sourcefolder))) # todo: clunky but works. problem with spaces in folder names
                            for dirname2, dirs2, filenames2 in os.walk(hydrosearchfolder):
                                for filename2 in [os.path.join(dirname2, name) for name in filenames2]:
                                    if os.path.basename(filename2) == "project.rs.xml":
                                        tree2 = ET.parse(filename2)
                                        root2 = tree2.getroot()
                                        visitid2 = root2.findtext("./MetaData/Meta[@name='Visit']") if root2.findtext(
                                            "./MetaData/Meta[@name='Visit']") is not None else root2.findtext(
                                            "./MetaData/Meta[@name='VisitID']")
                                        if root2.findtext("ProjectType") == "Hydro" and visitid2 == visitid:
                                            try:
                                                flow = root2.findtext("./MetaData/Meta[@name='Flow']")
                                                hydroexportfolder = os.path.join(resultsFolder, "Hydro", "Results", flow, "GIS_Exports")
                                                if not os.path.isdir(hydroexportfolder):
                                                    os.makedirs(hydroexportfolder)
                                                logg = Logger("Program")
                                                logfile = os.path.join(hydroexportfolder, "hydrogisexport.log")
                                                xmlfile = os.path.join(hydroexportfolder, "hydrogisexport.xml")
                                                logg.setup(logPath=logfile, verbose=args.verbose)
                                                # Initiate the log file
                                                log = Logger("Program")
                                                log.setup(logPath=logfile, verbose=args.verbose)

                                                result = export_hydro_model(filename2, filename, hydroexportfolder)
                                                logdb.write_log(year, watershed, siteid, visitid, "HydroGISExport", 'Success for flow {}'.format(str(flow)), xmlfile)
                                            except:
                                                logdb.write_log(year, watershed, siteid, visitid, "HydroGISExport", "Exception",
                                                                traceback.format_exc())
                        if args.bankfull:
                            try:
                                outfolder = os.path.join(resultsFolder, "BankfullMetrics")
                                if os.path.isdir(outfolder):
                                    os.makedirs(outfolder)
                                logg = Logger("Program")
                                logfile = os.path.join(outfolder, "bankfull_metrics.log")
                                xmlfile = os.path.join(outfolder, "bankfull_metrics.xml")
                                logg.setup(logPath=logfile, verbose=args.verbose)
                                # Initiate the log file
                                log = Logger("Program")
                                log.setup(logPath=logfile, verbose=args.verbose)
                                results = bankfull_metrics(topo_project.getpath("DEM"),
                                                           topo_project.getpath("DetrendedDEM"),
                                                           topo_project.getpath("Topo_Points"))
                                # todo write xml?
                                logdb.write_bankfull_metrics(year, watershed, siteid, visitid, results)
                                logdb.write_log(year, watershed, siteid, visitid, "BankfullMetrics", "Success", xmlfile)
                            except:
                                logdb.write_log(year, watershed, siteid, visitid, "BankfullMetrics", "Exception",
                                                traceback.format_exc())
    sys.exit(0)


class SqliteLog(object):

    def __init__(self, logfile, batchname=None):
        self.conn_log = sqlite3.connect(logfile)
        self.cursor = self.conn_log.cursor()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        if not any("Batches" in tablename for tablename in self.cursor.fetchall()):
            self.conn_log.execute('''CREATE TABLE Batches (batchID integer,
                                                                 batchname text,
                                                                 timestamp text)''')
            self.conn_log.commit()

        self.new_batch(batchname)
        
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        if not any("ModelResults" in tablename for tablename in self.cursor.fetchall()):
            self.conn_log.execute('''CREATE TABLE ModelResults (batchID integer,
                                                                 timestamp text, 
                                                                 year text, 
                                                                 watershed text, 
                                                                 site text, 
                                                                 visit text, 
                                                                 model text,
                                                                 status text,
                                                                 message text)''')
            self.conn_log.commit()

    def add_bankfull_metrics_table(self):
        if not any("BankfullMetrics" in tablename for tablename in self.cursor.fetchall()):
            self.conn_log.execute('''CREATE TABLE BankfullMetricResults (batchID integer,
                                                                timestamp text, 
                                                                year text, 
                                                                watershed text, 
                                                                site text, 
                                                                visit text, 
                                                                BFVol double,
                                                                DepthBF_Max double,
                                                                DepthBF_Avg double,
                                                                BFMetricsVersion text)''')
            self.conn_log.commit()

    def new_batch(self, name):
        self.cursor.execute('''SELECT * FROM Batches''')
        self.batch_id = len(self.cursor.fetchall()) + 1
        name = name if name else "Batch{}".format(str(self.batch_id))
        self.cursor.execute("INSERT INTO Batches VALUES (?,?,?)",
                            (self.batch_id, name, str(time.asctime())))
        self.conn_log.commit()
        return

    def write_log(self, year, watershed, site, visitid, model, staus, message):
        self.cursor.execute("INSERT INTO ModelResults VALUES (?,?,?,?,?,?,?,?,?)",
                            (self.batch_id, str(time.asctime()), year, watershed, site, visitid, model, staus, message))
        self.conn_log.commit()

    def write_bankfull_metrics(self, year, watershed, site, visitid, dict_results):
        self.cursor.execute("INSERT INTO BankfullMetricResults VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (self.batch_id, str(time.asctime()), year, watershed, site, visitid,
                             dict_results["BFVol"],
                             dict_results["DepthBF_Max"],
                             dict_results["DepthBF_Avg"],
                             dict_results["BFVersion"]))
        self.conn_log.commit()

    def close(self):
        self.conn_log.commit()
        self.conn_log.close()


if __name__ == "__main__":
    main()
