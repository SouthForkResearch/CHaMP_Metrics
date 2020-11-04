import argparse
import sys, traceback
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from os import path
from lib.sitkaAPI import downloadUnzipTopo, APIGet
from lib.env import setEnvFromFile
from lib.loghelper import Logger
from lib.exception import DataException, MissingException, NetworkException
from scipy.spatial import Voronoi
from shapely.affinity import translate
from shapely.geometry import Point, MultiPoint, LineString, Polygon
from lib import topoproject, riverscapes
from lib.raster import get_data_polygon
import geopandas, pandas, logging
from math import pow, log10, isnan
from osgeo import gdal, ogr

__version__ = "0.0.7"


def generate_substrate_raster(topo_project_folder, out_path, di_values, dict_ocular_values, out_channel_value=4000.0):
    """Generate Substrate Raster from Channel units and ocular substrate estimates for each di value provided

    :param str topo_project_folder: folder source of the topo project
    :param str out_path: path for outputs
    :param list di_values: list of int percentile values for roughness calculation
    :param dict dict_ocular_values: dictionary of ocular estimates of grain size values
    :param float out_channel_value: roughness value to use for out of channel areas, default = 4000
    :return: 0 for success
    """

    # Load Topo Project
    log = Logger("SubstrateRaster")
    log.info("topo_project_folder: {}".format(str(topo_project_folder)))
    log.info("outputPath: {}".format(str(out_path)))
    log.info("D Values: {}".format(str(di_values)))
    project = topoproject.TopoProject(topo_project_folder)
    topo_rs_project = riverscapes.Project(os.path.join(topo_project_folder, "project.rs.xml"))
    log.info("Topo project loaded")

    # Initialize Riverscapes Project
    rsproject = riverscapes.Project()
    rsproject.create("Substrate", "Substrate", __version__)
    for tagname, tags in {"Site": ["Site", "SiteName"], "Visit": ["Visit", "VisitID"], "Year": ["Year", "FieldSeason"],
                          "Watershed": ["Watershed", "Watershed"]}.iteritems():
        if tags[0] in topo_rs_project.ProjectMetadata or tags[1] in topo_rs_project.ProjectMetadata:
            rsproject.addProjectMetadata(tagname, topo_rs_project.ProjectMetadata[tags[0]] if tags[0] in topo_rs_project.ProjectMetadata else topo_rs_project.ProjectMetadata[tags[1]])
        else:
            raise DataException("Missing project metadata")

    # 1. Do some math on the dictionary of substrate values for each di
    dict_di_roughness_values = {}
    list_keep_units = []
    for di in di_values:
        dict_units = dict_ocular_by_unit(dict_ocular_values)
        dict_roughness_values = {}
        for unitid, dict_unit in dict_units.iteritems():
            if all(dict_unit[key] is not None for key in ["Bedrock", "Boulders", "Cobbles", "CourseGravel",
                                                          "FineGravel", "Fines", "Sand"]):
                dict_roughness_values[int(unitid)] = calculate_grain_size(dict_unit, di)
                if unitid not in list_keep_units:
                    list_keep_units.append(unitid)
            else:
                log.warning("Missing Channel Unit Substrate Values for Unit {}.".format(str(unitid)))

        dict_roughness_values[0] = float(out_channel_value)  # Out of Channel "UnitNumber" == 0
        dict_di_roughness_values[di] = pandas.DataFrame(list(dict_roughness_values.iteritems()),
                                                        index=dict_roughness_values.keys(),
                                                        columns=["UnitNumber", "Roughness"])
        log.info("Calculated Roughness Values for D{}".format(str(di)))

    # 2. Spread the channel Unit areas
    gdf_expanded_channel_units = expand_polygons(project.getpath("ChannelUnits"), project.getpath("BankfullExtent"),
                                                 keep_units=list_keep_units)
    log.info("Channel Units expanded to Bankfull Area")

    # 3. Add DEM area
    gdf_demextent = geopandas.GeoDataFrame.from_features(geopandas.GeoSeries(get_data_polygon(project.getpath("DEM"))))
    if not all(gdf_demextent.geometry.is_valid):
        gdf_demextent.geometry = gdf_demextent.geometry.buffer(0)
        log.info("Fix invalid geoms for DEM Extent")
    gdf_demextent["UnitNumber"] = 0
    gdf_in_channel_union = geopandas.GeoDataFrame.from_features(geopandas.GeoSeries(gdf_expanded_channel_units.unary_union.buffer(0)))
    gdf_out_of_channel = geopandas.overlay(gdf_demextent, gdf_in_channel_union, "difference")
    gdf_full_polygons = gdf_expanded_channel_units.append(gdf_out_of_channel)
    log.info("Out of Channel Area generated")

    for di, df_roughness_values in dict_di_roughness_values.iteritems():
        # 4 Add dict to channel units
        gdf_full_polygons_merged = gdf_full_polygons.merge(df_roughness_values, on="UnitNumber")
        gdf_final_polys = gdf_full_polygons_merged.rename(columns={"Roughness_y":"Roughness"})
        gdf_final_polys.drop([col for col in gdf_final_polys.columns if col not in ["UnitNumber", "Roughness", 'geometry']], axis=1, inplace=True)
        log.info("Roughness Values added to Channel Units for D{}".format(str(di)))

        # 5. Rasterize Polygons
        raster_substrate = path.join(out_path, "substrate_D{}.tif".format(str(di)))
        shp_substrate = path.join(out_path, "substrate_D{}.shp".format(str(di)))
        gdf_final_polys.to_file(shp_substrate)
        log.info("Saved Substrate Shapefile: {}".format(shp_substrate))
        rasterize_polygons(shp_substrate, project.getpath("DEM"), raster_substrate, "Roughness")
        log.info("Created Substrate Raster: {}".format(raster_substrate))

        # Add Realization to Riverscapes
        realization = riverscapes.Realization("Substrate")
        realization.name = "Substrate_D{}".format(str(di))
        realization.productVersion = __version__
        ds_shapefile = riverscapes.Dataset().create("Substrate_Shapefile", "substrate_D{}.shp".format(str(di)))
        ds_raster = riverscapes.Dataset().create("Substrate_Raster", "substrate_D{}.tif".format(str(di)))
        ds_shapefile.metadata["D_Value"] = str(di)
        ds_raster.metadata["D_Value"] = str(di)
        ds_shapefile.id = "substrate_shapefile_d{}".format(str(di))
        ds_raster.id = "substrate_shapefile_d{}".format(str(di))
        realization.outputs[ds_shapefile.name] = ds_shapefile
        realization.outputs[ds_raster.name] = ds_raster
        rsproject.addRealization(realization)

    # Write Riverscapes Project.
    rsprojectxml = os.path.join(out_path, "project.rs.xml")
    rsproject.writeProjectXML(rsprojectxml)
    log.info("Riverscapes Project file saved: {}".format(rsprojectxml))

    return 0


def expand_polygons(shp_channel_units, shp_bankfull, shp_out=None, keep_units=None):
    """
    use voronoi polygons to expand the area of existing polygons to fill bounding polygon
    :param str shp_channel_units: shapefile of channel unit polygons to exand from
    :param str shp_bankfull: shapefile of bankfull polygon to expand to
    :param str shp_out: save expanded polygons to shapefile
    :param list keep_units: only use channel unit id's in this list
    :return GeoDataFrame: geodataframe of expanded polygons
    """
    # Generate GeoDataFrames
    gdf_channel_units = geopandas.GeoDataFrame.from_file(shp_channel_units)
    if keep_units:
        gdf_channel_units = gdf_channel_units.loc[gdf_channel_units['UnitNumber'].isin(keep_units)]
    gdf_bankfull = geopandas.GeoDataFrame.from_file(shp_bankfull)
    if not all(gdf_bankfull.geometry.is_valid):
        gdf_bankfull.geometry = gdf_bankfull.geometry.buffer(0)

    # Generate Voronoi Polygons    
    gs_vor_polys, points = generate_voronoi(gdf_channel_units.geometry)

    # Remove empty geometries
    for i, p in enumerate(gs_vor_polys):
        if p.type != "Polygon":
            del gs_vor_polys[i]

    # Generate buffered points to transfer Channel Unit Numbers to Voronoi
    gdf_points = geopandas.GeoDataFrame.from_features(geopandas.GeoSeries(points.geoms))
    gdf_points_buffer = geopandas.GeoDataFrame.from_features(gdf_points.buffer(.05))
    gdf_points_units = geopandas.sjoin(gdf_points_buffer, gdf_channel_units, how="left", op="intersects")
    gdf_points_units.drop(['index_right'], axis=1, inplace=True)

    # Transfer Channel Unit Numbers to Voronoi
    gdf_vor_polys = geopandas.GeoDataFrame.from_features(gs_vor_polys)
    gdf_vor_poly_units = geopandas.sjoin(gdf_vor_polys, gdf_points_units, how="left", op="intersects")
    gdf_vor_poly_units = gdf_vor_poly_units.rename(columns={"UnitNumber_right": "UnitNumber"})
    gdf_dissolve = gdf_vor_poly_units.dissolve(by="UnitNumber", as_index=False)

    # Clip Voronoi to Bankfull Extent
    gdf_intersection = geopandas.overlay(gdf_bankfull, gdf_dissolve, "intersection")

    # Add in missing pieces that did not form voronoi polygons.
    gdf_holes = geopandas.overlay(gdf_bankfull, gdf_dissolve, "symmetric_difference")
    gdf_iholes = geopandas.overlay(gdf_bankfull, gdf_holes, "intersection")
    gdf_clip_vor_bf = gdf_intersection.append(gdf_iholes, ignore_index=True)

    # Merge Channel Units and Voroinoi polygons
    gdf_clip_vor = geopandas.overlay(gdf_clip_vor_bf, gdf_channel_units, "difference")
    gdf_full = gdf_clip_vor.append(gdf_channel_units, ignore_index=True)

    # Assign UnitNumber from Nearest Polygon.
    for row in [r for r in gdf_full.iterrows() if isnan(r[1]["UnitNumber"])]:
        min_dist = 1000000.0
        for test_row in [t_row for t_row in gdf_full.iterrows() if t_row[0] != row[0]]:
            dist = row[1]['geometry'].centroid.distance(test_row[1]['geometry'].centroid)
            if dist < min_dist and not isnan(test_row[1]['UnitNumber']):
                gdf_full.set_value(row[0], "UnitNumber", test_row[1]['UnitNumber'])
                min_dist = dist

    if not all(gdf_full.geometry.is_valid):
        gdf_full.geometry = gdf_full.geometry.buffer(0)
    gdf_output = gdf_full.dissolve(by="UnitNumber", as_index=False)
    gdf_output.crs = gdf_channel_units.crs

    if shp_out:
        gdf_output.to_file(shp_out)

    return gdf_output


def generate_voronoi(geoseries_polygons):
    """Generate Voronoi polygons from polygon edges
    :param geoseries_polygons: GeoSeries of raw polygons
    :return:
    """
    edges = geoseries_polygons.unary_union.boundary
    pnts = points_along_boundaries(edges, 0.75)
    cent = pnts.centroid
    tpnts = translate(pnts, -cent.x, -cent.y)
    vor = Voronoi(tpnts)
    polys = []
    for region in vor.regions:
        if len(region) > 0 and all([i > 0 for i in region]):
            polys.append(Polygon([vor.vertices[i] for i in region]))
    gs_vor = geopandas.GeoSeries(polys)
    t_gs_vor = gs_vor.translate(cent.x, cent.y)
    t_gs_vor.crs = geoseries_polygons.crs
    return t_gs_vor, pnts


def points_along_boundaries(geoseries, distance=1.0):
    """
    Generate a shapely MultiPoint of point features along lines at a specified distance
    :param geoseries:
    :param distance:
    :return:
    """

    list_points = []
    for line3d in iter_line(geoseries):
        line = LineString([xy[0:2] for xy in list(line3d.coords)])
        current_dist = distance
        line_length = line.length
        list_points.append(Point(list(line.coords)[0]))
        while current_dist < line_length:
            list_points.append(line.interpolate(current_dist))
            current_dist += distance
            list_points.append(Point(list(line.coords)[-1]))
    return MultiPoint(list_points)


def iter_line(series):
    """
    recursively yield any linestrings within a data series
    :param series: geoseries
    :return: linestring
    """
    if series.type == "MultiLineString":
        for item in series:
            if item.type == "LineString":
                yield item
            else:
                iter_line(item)
    else:
        yield series


def rasterize_polygons(polygon_shp, template_raster, out_raster, field):
    """ generate a categorical raster based on polygons

    :rtype: None
    :param polygon_shp: input polygon shapefile
    :param template_raster: raster template for cellsize and extent
    :param out_raster: output raster file
    """

    # Source: https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html

    gdal.UseExceptions()
    # Get template raster specs
    src_ds = gdal.Open(template_raster)
    if src_ds is None:
        print 'Unable to open %s' % template_raster
        sys.exit(1)
    try:
        srcband = src_ds.GetRasterBand(1)
    except RuntimeError, e:
        print 'No band %i found' % 0
        print e
        sys.exit(1)

    # Open the data source and read in the extent
    source_ds = ogr.Open(polygon_shp)
    source_layer = source_ds.GetLayer()

    target_ds = gdal.GetDriverByName('GTiff').Create(out_raster, src_ds.RasterXSize, src_ds.RasterYSize, 1, gdal.GDT_Float32)
    target_ds.SetGeoTransform(src_ds.GetGeoTransform())
    target_ds.SetProjection(src_ds.GetProjection())
    band = target_ds.GetRasterBand(1)
    band.SetNoDataValue(srcband.GetNoDataValue())

    # Rasterize
    gdal.RasterizeLayer(target_ds, [1], source_layer, options=["ATTRIBUTE={}".format(field)])


def dict_ocular_by_unit(raw_dictionary):
    """
    Clean up raw ocular estimate dictionary.
    :param raw_dictionary:
    :return:
    """
    dict_units = {}
    for u in raw_dictionary['values']:
        dict_units[u['value']['ChannelUnitNumber']] = u['value']
    return dict_units


def calculate_grain_size(dict_values, di):
    """
    Calculate the grain size for a percentile (p) of a grain size distribution.

    :param dict_values: dictionary of named grain sizes and percent of total
    :param di: percentile to calculate grain size distribution.
    :return: estimated grain size for the percentile
    """

    grain_sizes = [{'size': 'Fines', "min": 0.001 , "max": 0.06},
                   {'size': 'Sand', "min": 0.06, "max": 2.0},
                   {'size': 'FineGravel', "min": 2.0, "max": 16.0},
                   {'size': 'CourseGravel', "min": 16.0, "max": 64.0},
                   {'size': 'Cobbles', "min": 64.0, "max": 256.0},
                   {'size': 'Boulders', "min": 256.0, "max": 4000.0}, # max obtained from original vb code
                   {'size': 'Bedrock', "min": 0.00001, "max": 0.01}]
    p_min = 0

    for gs in grain_sizes:
        p_max = p_min + dict_values[gs['size']]
        if gs['size'] == 'Bedrock':
            return 0.01
        if di == p_max:
            return gs['max']
        elif p_min < di < p_max:
            return pow(10, (log10(gs['max']) - log10(gs['min'])) * (float(di - p_min) / float(p_max - p_min)) + log10(gs['min']))
        else:
            p_min = p_max


def main():
    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('visitID', help='the visit id of the site to use (no spaces)', type=str)
    parser.add_argument('outputfolder', help='Output folder', type=str)
    parser.add_argument('substrate_values', nargs='+', help="one or more percentiles of grain size to calculate. 50 for D50, 84 for D84, etc", type=int)
    parser.add_argument('--out_channel_roughness_value', help="i.e. 4000.0", type=float, default=4000.0)
    parser.add_argument('--ocular_estimates', help="(optional) local json file of ocular estimates")
    parser.add_argument('--datafolder', help='(optional) local folder containing TopoMetrics Riverscapes projects',
                        type=str)
    parser.add_argument('--env', "-e", help="(optional) local env file", type=str)
    parser.add_argument('--verbose', help='Get more information in your logs.', action='store_true', default=False)

    args = parser.parse_args()

    if not all([args.visitID, args.outputfolder, args.substrate_values, args.out_channel_roughness_value]):
        print "ERROR: Missing arguments"
        parser.print_help()

    if args.env:
        setEnvFromFile(args.env)

    # Make sure the output folder exists
    resultsFolder = os.path.join(args.outputfolder, "outputs")

    # Initiate the log file
    logg = Logger("Program")
    logfile = os.path.join(resultsFolder, "substrate_raster.log")
    logg.setup(logPath=logfile, verbose=args.verbose)

    # Fiona debug-level loggers can cause problems
    logging.getLogger("Fiona").setLevel(logging.ERROR)
    logging.getLogger("fiona").setLevel(logging.ERROR)
    logging.getLogger("fiona.collection").setLevel(logging.ERROR)
    logging.getLogger("shapely.geos").setLevel(logging.ERROR)
    logging.getLogger("rasterio").setLevel(logging.ERROR)

    try:
        # Make some folders if we need to:
        if not os.path.isdir(args.outputfolder):
            os.makedirs(args.outputfolder)
        if not os.path.isdir(resultsFolder):
            os.makedirs(resultsFolder)

        # If we need to go get our own topodata.zip file and unzip it we do this
        if args.datafolder is None:
            topoDataFolder = os.path.join(args.outputfolder, "inputs")
            if not os.path.isdir(topoDataFolder):
                os.makedirs(topoDataFolder)
            fileJSON, projectFolder = downloadUnzipTopo(args.visitID, topoDataFolder)
        # otherwise just pass in a path to existing data
        else:
            projectFolder = args.datafolder

        if args.ocular_estimates is None:
            dict_ocular = APIGet("visits/{}/measurements/Substrate%20Cover".format(str(args.visitID)))
            dict_units = APIGet("visits/{}/measurements/Channel%20Unit".format(str(args.visitID)))
            dict_unitkey = {x['value']['ChannelUnitID']: x['value']['ChannelUnitNumber'] for x in dict_units['values']}
            for i in range(len(dict_ocular['values'])):
                dict_ocular['values'][i]['value']['ChannelUnitNumber'] = dict_unitkey[dict_ocular['values'][i]['value']['ChannelUnitID']]
        else:
            dict_ocular = json.load(open(args.ocular_estimates, 'rt'))
            dict_units = APIGet("visits/{}/measurements/Channel%20Unit".format(str(args.visitID)))
            dict_unitkey = {x['value']['ChannelUnitID']: x['value']['ChannelUnitNumber'] for x in dict_units['values']}
            for i in range(len(dict_ocular['values'])):
                dict_ocular['values'][i]['value']['ChannelUnitNumber'] = dict_unitkey[dict_ocular['values'][i]['value']['ChannelUnitID']]

        generate_substrate_raster(projectFolder,
                                  resultsFolder,
                                  args.substrate_values,
                                  dict_ocular,
                                  args.out_channel_roughness_value)

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
