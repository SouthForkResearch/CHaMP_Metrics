import os
import sys
import argparse
import traceback
import csv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import lib.env
from lib.tin import TIN
from lib.sitkaAPI import downloadUnzipTopo
from lib import topoproject
from lib.shapefileloader import Shapefile
from lib.exception import DataException, MissingException, NetworkException
from lib.loghelper import Logger
from lib import riverscapes

__version__ = "0.0.2"

def export_cad_files(project_xml, out_path):
    """exports dxf files containing tin components of topo tin and Topographic Survey Points, Lines and Survey Extent"""

    log = Logger("CADExport")

    # Load Topo project
    log.info("Load Topo project")
    project = topoproject.TopoProject(project_xml)

    # TIN stuff
    log.info("Beginning TIN Work")
    tin = TIN(project.getpath("TopoTin"))
    dict_tinlayers = {}
    dict_tinlayers["tin_points"] = {"layer_type":"POINT", "Features":[feat for feat in tin.nodes.values()]}
    dict_tinlayers["tin_lines"] = {"layer_type":"POLYLINE", "Features":[feat['geometry'] for feat in tin.breaklines.values()]}#, "linetype_field":"LineType"}
    dict_tinlayers["tin_area"] = {"layer_type":"POLYGON", "Features":[feat for feat in tin.hull_polygons.values()]}

    out_tin_dxf = export_as_dxf(dict_tinlayers, os.path.join(out_path, "TopoTin.dxf"))

    # Topo Stuff
    log.info("Beginning Topo Work")
    shpTopo = Shapefile(project.getpath("Topo_Points"))
    shpEOW = Shapefile(project.getpath("EdgeofWater_Points"))
    shpCP = Shapefile(project.getpath("Control_Points"))
    shpBL = Shapefile(project.getpath("Breaklines")) if project.layer_exists("Breaklines") else None
    shpExtent = Shapefile(project.getpath("Survey_Extent"))
    dict_topolayers = {}
    dict_topolayers["Topo_Points"] = {"layer_type":"POINT", "Features":[feat['geometry'] for feat in shpTopo.featuresToShapely()]}
    dict_topolayers["EdgeofWater_Points"] = {"layer_type":"POINT", "Features":[feat['geometry'] for feat in shpEOW.featuresToShapely()]}
    dict_topolayers["Control_Points"] = {"layer_type":"POINT", "Features":[feat['geometry'] for feat in shpCP.featuresToShapely()]}
    dict_topolayers["Breaklines"] = {"layer_type":"POLYLINE", "Features":[feat['geometry'] for feat in shpBL.featuresToShapely()]} if shpBL else None
    dict_topolayers["Survey_Extent"] = {"layer_type":"POLYGON", "Features":[feat['geometry'] for feat in shpExtent.featuresToShapely()]}

    out_topo_dxf = export_as_dxf(dict_topolayers, os.path.join(out_path, "SurveyTopography.dxf"))

    out_topo_csv = exportAsCSV(shpTopo.featuresToShapely() + shpEOW.featuresToShapely(), os.path.join(out_path, "SurveyTopographyPoints.csv"))
    out_control_csv = exportAsCSV(shpCP.featuresToShapely(), os.path.join(out_path, "ControlNetworkPoints.csv"))

    topo_rs_project = riverscapes.Project(project_xml)

    out_project = riverscapes.Project()
    out_project.create("CHaMP_Survey_CAD_Export", "CAD_Export", __version__)
    out_project.addProjectMetadata("Watershed", topo_rs_project.ProjectMetadata["Watershed"])

    #  find previous meta tags
    for tagname, tags in {"Site": ["Site", "SiteName"], "Visit": ["Visit", "VisitID"], "Year": ["Year", "FieldSeason"], "Watershed": ["Watershed", "Watershed"]}.iteritems():
        if tags[0] in topo_rs_project.ProjectMetadata or tags[1] in topo_rs_project.ProjectMetadata:
            out_project.addProjectMetadata(tagname, topo_rs_project.ProjectMetadata[tags[0]] if tags[0] in topo_rs_project.ProjectMetadata else topo_rs_project.ProjectMetadata[tags[1]])
        else:
            raise DataException("Missing project metadata")

    out_realization = riverscapes.Realization("CAD_Export")
    out_realization.name = "CHaMP Survey CAD Export"
    out_realization.productVersion = out_project.projectVersion
    ds = []
    ds.append(out_project.addInputDataset("TopoTin", "tin", None, None, "TIN", project.get_guid("TopoTin")))
    ds.append(out_project.addInputDataset("Topo_Points", "topo_points", None, guid=project.get_guid("Topo_Points")))
    ds.append(out_project.addInputDataset("EdgeofWater_Points", "eow_points", None, guid=project.get_guid("EdgeofWater_Points")))
    ds.append(out_project.addInputDataset("Control_Points", "control_ponts", None, guid=project.get_guid("Control_Points")))
    if shpBL:
        ds.append(out_project.addInputDataset("Breaklines", "breaklines", None, guid=project.get_guid("Breaklines")))
    ds.append(out_project.addInputDataset("Survey_Extent", "survey_extent", None, guid=project.get_guid("Survey_Extent")))
    for inputds in ds:
        out_realization.inputs[inputds.name] = inputds.id

    ds_tin_dxf = riverscapes.Dataset()
    ds_tin_dxf.create("TIN_DXF", "TopoTin.dxf")
    ds_tin_dxf.id = 'tin_dxf'
    ds_topo_dxf = riverscapes.Dataset()
    ds_topo_dxf.create("Topo_DXF", "SurveyTopography.dxf")
    ds_topo_dxf.id = 'topo_dxf'
    ds_topo_csv = riverscapes.Dataset()
    ds_topo_csv.create("Topo_CSV", "SurveyTopographyPoints.csv", "CSV")
    ds_topo_csv.id = 'topo_csv'
    ds_con_csv = riverscapes.Dataset()
    ds_con_csv.create("Control_CSV", "ControlNetworkPoints.csv", "CSV")
    ds_con_csv.id = 'control_csv'
    out_realization.outputs.update({"TIN_DXF": ds_tin_dxf,
                                    "Topo_DXF": ds_topo_dxf,
                                    "Topo_CSV": ds_topo_csv,
                                    "Control_CSV": ds_con_csv})

    out_project.addRealization(out_realization)
    out_project.writeProjectXML(os.path.join(out_path, "project.rs.xml"))

    return 0


def export_as_dxf(dict_layers, out_dxf):
    log = Logger("DXFExport")

    header = "  0\nSECTION\n  2\nENTITIES\n"
    h = Handle()

    log.info("Beginning DXF Export")
    with open(out_dxf, "wt") as f:
        f.write(header)
        for name, layer in dict_layers.iteritems():
            log.info("Exporting Layer: {}".format(name))
            if layer:
                if layer["layer_type"] == "POINT":
                    for point in layer["Features"]:
                        f.write("  0\nPOINT\n  5\n{}\n100\nAcDBEntity\n  8\n{}\n".format(h.next(), name)) #  ,
                        f.write("100\nAcDbPoint\n 10\n{}\n 20\n{}\n 30\n{}\n".format(point.x, point.y, point.z))
                elif layer["layer_type"] == "POLYLINE":
                    for line in layer["Features"]: #['geometry'] if layer["Features"].has_key("geometry") else layer["Features"]['geometry']:
                        if line:
                            hline = h.next()
                            f.write("  0\nPOLYLINE\n  5\n{}\n100\nAcDBEntity\n  8\n{}\n".format(hline, name))
                            # if layer.has_key("linetype_field"):
                            #     f.write("  6\n{}\n".format("Linetypefield"))
                            f.write("100\nAcDb3dPolyline\n 10\n0.0\n 20\n0.0\n30\n0.0\n70\n      8\n")
                            for listcoords in [[line.coords] if line.geom_type == "LineString" else [linepart.coords for linepart in line]]:
                                for coords in listcoords:
                                    for vertex in coords:
                                        h.next()
                                        f.write("  0\nVERTEX\n  5\n{}\n330\n{}\n100\nAcDbEntitiy\n  8\n{}\n".format(h.next(),hline, name))
                                        # if layer.has_key("linetype_field"):
                                        #     f.write("  6\n{}\n".format("Linetypefield"))
                                        f.write("100\nAcDbVertex\n100\nAcDb3dPolylineVertex\n")
                                        f.write(" 10\n{}\n 20\n{}\n 30\n{}\n 70\n     32\n".format(vertex[0], vertex[1], vertex[2]))
                                    f.write("  0\nSEQEND\n  5\n{}\n330\n{}\n100\nAcDbEntity\n  8\n{}\n".format(h.next(), hline, name))
                                    # if layer['Features'].has_key("linetype_field"):
                                    #     f.write("  6\n{}\n".format(layer['Features']["linetype_field"]))
                elif layer["layer_type"] == "POLYGON":
                    for poly in layer["Features"]:
                        if poly :
                            hpoly = h.next()
                            f.write("  0\nPOLYLINE\n  5\n{}\n100\nAcDBEntity\n  8\n{}\n".format(hpoly, name))
                            if layer.has_key("linetype_field"):
                                f.write("  6\n{}\n".format("Linetypefield"))
                            f.write("100\nAcDb3dPolyline\n 10\n0.0\n 20\n0.0\n30\n0.0\n70\n      9\n")
                            for listcoords in [[poly.exterior.coords] if poly.geom_type == "Polygon" else [polypart.exterior.coords for polypart in poly]]:
                                for coord in listcoords:
                                    for vertex in coord:
                                        h.next()
                                        f.write("  0\nVERTEX\n  5\n{}\n330\n{}\n100\nAcDbEntitiy\n  8\n{}\n".format(h.next(),hpoly, name))
                                        if layer.has_key("linetype_field"):
                                            f.write("  6\n{}\n".format("Linetypefield"))
                                        f.write("100\nAcDbVertex\n100\nAcDb3dPolylineVertex\n")
                                        f.write(" 10\n{}\n 20\n{}\n 30\n{}\n 70\n     32\n".format(vertex[0], vertex[1], 0.0))
                                    f.write("  0\nSEQEND\n  5\n{}\n330\n{}\n100\nAcDbEntity\n  8\n{}\n".format(h.next(), hpoly, name))
                                    if layer.has_key("linetype_field"):
                                        f.write("  6\n{}\n".format("Linetypefield"))
        f.write("  0\nENDSEC\n")
        f.write("  0\nEOF")

    log.info("DXF Export Complete")
    return out_dxf


class Handle(object):
    def __init__(self):
        self.i = 1
    def next(self):
        self.i = self.i + 1
        return format(self.i, '02x').upper()
    def value(self):
        return format(self.i, '02x').upper()


def exportAsCSV(feats, outCSVfile):
    log = Logger("CSVExport")
    log.info("Beginning CSV Export")
    with open(outCSVfile, "wb") as csvfile:
        csvWriter = csv.writer(csvfile)
        #fieldsGIS = ("POINT_NUMBER", "SHAPE@Y", "SHAPE@X", "SHAPE@Z", "DESCRIPTION")
        csvWriter.writerow(("PNTNO", "Y", "X", "ELEV", "DESC"))
        for feat in feats:
            # Do some checking on mandatory fields first
            pnfield = getfield(feat, ["POINT_NUMB", "Point_Numb", "numb", "Number", "Point", "points", "p", "Point_Id", "PointId", "POINT_ID", "POINTID", "PointNumbe", "Point_id", "Name", "FID", "OBJECTID"])
            cfield = getfield(feat, ["Code","CODE"])
            row = (feat['fields'][pnfield], feat['geometry'].x, feat['geometry'].y, feat['geometry'].z, feat['fields'][cfield] )
            csvWriter.writerow(row)
    log.info("CSV Export complete")
    return outCSVfile

def getfield(feat, listfields):
    for field in listfields:
        if field in feat['fields']:
            return field
    raise DataException('Could not find field {} in shapefile'.format(str(listfields)))


def main():
    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('visitID', help='the id of the site to use (no spaces)',type=str)
    parser.add_argument('outputfolder', help='Output folder')
    parser.add_argument('--datafolder', help='(optional) Top level folder containing TopoMetrics Riverscapes projects', type=str)
    parser.add_argument('--logfile', help='output log file.', default="", type=str)
    parser.add_argument('--verbose', help = 'Get more information in your logs.', action='store_true', default=False)

    args = parser.parse_args()

    # Make sure the output folder exists
    resultsFolder = os.path.join(args.outputfolder, "outputs")

    # Initiate the log file
    if args.logfile == "":
        logfile = os.path.join(resultsFolder, "cad_export.log")
    else:
        logfile = args.logfile

    logg = Logger("CADExport")
    logg.setup(logPath=logfile, verbose=args.verbose)

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

        projectxml = os.path.join(projectFolder, "project.rs.xml")
        finalResult = export_cad_files(projectxml, resultsFolder)

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
