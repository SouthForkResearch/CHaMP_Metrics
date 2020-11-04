import argparse
import sys, traceback
import os
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))
import lib.env
from lib.sitkaAPI import downloadUnzipTopo
from lib.loghelper import Logger
from lib.exception import DataException, MissingException, NetworkException

import fiona
import pandas
import rasterio
from rasterio import features
from shapely.geometry import asShape, Point, Polygon
import geopandas
import numpy

from lib.riverscapes import Project
from lib.topoproject import TopoProject

__version__="0.0.2"


def export_hydro_model(hydro_rs_xml, topo_rs_xml, out_path):

    log = Logger("Hydro GIS Export")

    # 1 todo Read project.rs.xml
    rs_hydro = Project(hydro_rs_xml)
    rs_topo = TopoProject(topo_rs_xml)
    hydro_results_folder = os.path.dirname(hydro_rs_xml)
    csvfile_hydro = os.path.join(hydro_results_folder, "dem_grid_results.csv") # todo get this from hydro project xml

    if not rs_hydro.ProjectMetadata.has_key("Visit"):
        raise MissingException("Cannot Find Visit ID")
    visit_id = rs_hydro.ProjectMetadata['Visit']

    df_csv = pandas.read_csv(csvfile_hydro)
    log.info("Read hydro results csv as data frame")

    # Get DEM Props
    with rasterio.open(rs_topo.getpath("DEM")) as rio_dem:
        dem_crs = rio_dem.crs
        dem_bounds = rio_dem.bounds
        dem_nodata = rio_dem.nodata
    out_transform = rasterio.transform.from_origin(dem_bounds.left, dem_bounds.top, 0.1, 0.1)

    pad_top = int((dem_bounds.top - max(df_csv['Y'])) / 0.1)
    pad_bottom = int((min(df_csv['Y']) - dem_bounds.bottom) / 0.1)
    pad_right = int((dem_bounds.right - max(df_csv['X'])) / 0.1)
    pad_left = int((min(df_csv['X']) - dem_bounds.left) / 0.1)
    log.info("Read DEM properties")

    # generate shp
    geom = [Point(xy) for xy in zip(df_csv.X, df_csv.Y)]
    df_output = df_csv.drop(["X", "Y", "Depth.Error", "WSE", "BedLevel"], axis="columns")#, inplace=True) # save a bit of space
    gdf_hydro = geopandas.GeoDataFrame(df_output, geometry=geom)
    gdf_hydro.crs = dem_crs
    gdf_hydro.columns = gdf_hydro.columns.str.replace(".", "_")
    gdf_hydro["VelDir"] = numpy.subtract(90, numpy.degrees(numpy.arctan2(gdf_hydro["Y_Velocity"], gdf_hydro["X_Velocity"])))
    gdf_hydro["VelBearing"] = numpy.where(gdf_hydro['VelDir'] < 0, 360 + gdf_hydro["VelDir"], gdf_hydro["VelDir"])
    gdf_hydro.drop("VelDir", axis="columns", inplace=True)
    #gdf_hydro.to_file(os.path.join(out_path, "HydroResults.shp"))
    del df_output, gdf_hydro
    log.info("Generated HydroResults.shp")

    for col in [col for col in df_csv.columns if col not in ["X", "Y", "X.Velocity", "Y.Velocity"]]:
        df_pivot = df_csv.pivot(index="Y", columns="X", values=col)
        np_raw = df_pivot.iloc[::-1].as_matrix()

        np_output = numpy.pad(np_raw, ((pad_top,pad_bottom),(pad_left,pad_right)), mode="constant", constant_values=numpy.nan)

        with rasterio.open(os.path.join(out_path, "{}.tif".format(col)), 'w', driver='GTiff',
                           height=np_output.shape[0],
                           width=np_output.shape[1],
                           count=1,
                           dtype=np_output.dtype,
                           crs=dem_crs,
                           transform=out_transform,
                           nodata=dem_nodata) as rio_output:
            rio_output.write(np_output, 1)
        log.info("Generated output Raster for {}".format(col))

        if col == "Depth":
            # Generate water extent polygon
            np_extent = numpy.greater(np_output, 0)
            mask = numpy.isfinite(np_output)
            shapes = features.shapes(np_extent.astype('float32'), mask, transform=out_transform)
            gdf_extent_raw = geopandas.GeoDataFrame.from_features(geopandas.GeoSeries([asShape(s) for s, v in shapes]))
            gdf_extent = geopandas.GeoDataFrame.from_features(gdf_extent_raw.geometry.simplify(0.5))
            gdf_extent.crs = dem_crs

            gdf_extent['Area'] = gdf_extent.geometry.area
            gdf_extent['Extent'] = ""
            gdf_extent.set_value(gdf_extent.index[gdf_extent['Area'].idxmax()], "Extent", "Channel" ) # Set largest Polygon as Main Channel
            gdf_extent.to_file(os.path.join(out_path, "StageExtent.shp"))
            log.info("Generated Water Extent Polygons")

            # Generate islands and spatial join existing islands attributes
            gdf_exterior = geopandas.GeoDataFrame.from_features(geopandas.GeoSeries([Polygon(shape) for shape in gdf_extent.geometry.exterior]))
            gs_diff = gdf_exterior.geometry.difference(gdf_extent.geometry)
            if not all(g.is_empty for g in gs_diff):
                gdf_islands_raw = geopandas.GeoDataFrame.from_features(geopandas.GeoSeries([shape for shape in gs_diff if not shape.is_empty]))
                gdf_islands_explode = geopandas.GeoDataFrame.from_features(gdf_islands_raw.geometry.explode())
                gdf_islands_clean = geopandas.GeoDataFrame.from_features(gdf_islands_explode.buffer(0))
                gdf_islands_clean.crs = dem_crs
                if fiona.open(rs_topo.getpath("WettedIslands")).__len__() > 0: # Exception when createing gdf if topo islands shapefile is empty feature class
                    gdf_topo_islands = geopandas.GeoDataFrame.from_file(rs_topo.getpath("WettedIslands"))
                    gdf_islands_sj = geopandas.sjoin(gdf_islands_clean, gdf_topo_islands, how="left", op="intersects")
                    gdf_islands_sj.drop(["index_right", "OBJECTID"], axis="columns", inplace=True)
                    gdf_islands_sj.crs = dem_crs
                    gdf_islands_sj.to_file(os.path.join(out_path, "StageIslands.shp"))

    #todo: Generate Lyr file and copy
    #todo: Generate readme

    return 0


def main():
    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('visitID', help='Visit ID', type=int)
    parser.add_argument('outputfolder', help='Path to output folder', type=str)
    parser.add_argument('--hydroprojectxml', '-p', help='(optional) hydro project xml file', type=str)
    parser.add_argument('--topoprojectxml', '-t', help='(optional) topo project xml file', type=str)
    parser.add_argument('--datafolder', help='(optional) Top level folder containing Hydro Model Riverscapes projects', type=str)
    parser.add_argument('--verbose', help='Get more information in your logs.', action='store_true', default=False )
    args = parser.parse_args()

    # Make sure the output folder exists
    resultsFolder = os.path.join(args.outputfolder, "outputs")

    # Initiate the log file
    #logg = Logger("Program")
    logfile = os.path.join(resultsFolder, "hydro_gis.log")
    xmlfile = os.path.join(resultsFolder, "hydro_gis.xml")
   # logg.setup(logPath=logfile, verbose=args.verbose)

    # Initiate the log file
    #log = Logger("Program")
   # log.setup(logPath=logfile, verbose=args.verbose)

    try:
        # Make some folders if we need to:
        if not os.path.isdir(args.outputfolder):
            os.makedirs(args.outputfolder)
        if not os.path.isdir(resultsFolder):
            os.makedirs(resultsFolder)

        # If we need to go get our own topodata.zip file and unzip it we do this
        # if args.datafolder is None:
        #     hydroDataFolder = os.path.join(args.outputfolder, "inputs")
        #     folderJSON, list_projectFolders = downloadUnzipTopo(args.visitID, hydroDataFolder)
        # # otherwise just pass in a path to existing data
        # else:
        #     list_projectFolders = args.datafolder
        # runResult = []
        # for fileJSON, projectFolder in list_projectFolders:
        result = export_hydro_model(args.hydroprojectxml, args.topoprojectxml, resultsFolder)

        sys.exit(result)

    except (DataException, MissingException, NetworkException) as e:
        # Exception class prints the relevant information
        traceback.print_exc(file=sys.stdout)
        sys.exit(e.returncode)
    except AssertionError as e:
        #log.error(e.message)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
    except Exception as e:
        #log.error(e.message)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

    #sys.exit(0)


if __name__ == "__main__":




    main()