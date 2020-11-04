import argparse
import sys, traceback
import os

from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))
import csv, math
#import rasterio
import ogr, gdal, gdalconst, osr
#import fiona
import numpy
from lib.sitkaAPI import downloadUnzipTopo
from lib.loghelper import Logger
from lib.exception import DataException, MissingException, NetworkException
from lib.riverscapes import Project
from lib.topoproject import TopoProject

__version__="0.1.1"


def hydro_gis_export(hydro_project_xml, topo_project_xml, outfolder):
    """
    :param jsonFilePath:
    :param outputFolder:
    :param bVerbose:
    :return:
    """
    #gdal.UseExceptions()

    log = Logger("Hydro GIS Export")

    # 1 todo Read project.rs.xml
    rs_hydro = Project(hydro_project_xml)
    rs_topo = TopoProject(topo_project_xml)
    hydro_results_folder = os.path.dirname(hydro_project_xml)

    if not rs_hydro.ProjectMetadata.has_key("Visit"):
        raise MissingException("Cannot Find Visit ID")
    visit_id = rs_hydro.ProjectMetadata['Visit']

    dem = gdal.Open(rs_topo.getpath("DEM"))
    dem_srs = dem.GetProjection()
    dem_x_size = dem.RasterXSize
    dem_y_size = dem.RasterYSize
    dem_band = dem.GetRasterBand(1)
    dem_ndv = dem_band.GetNoDataValue()
    dem_geotransfrom = dem.GetGeoTransform()

    # 3 Get data columns in csv file
    csvfile = os.path.join(hydro_results_folder, "dem_grid_results.csv")
    csvfile_clean = os.path.join(hydro_results_folder, "dem_grid_results_clean_header.csv")
    if not os.path.isfile(csvfile):
        raise MissingException("Required file {} does not exist.".format(csvfile))
    with open(csvfile, "rb") as f_in, open(csvfile_clean, "wb") as f_out:
        reader = csv.reader(f_in)
    #     writer = csv.writer(f_out)
        cols = [col for col in reader.next() if col not in ["Y", "X"]]#[col.replace(".", "_") for col in reader.next() if col not in ["Y", "X"]]
        log.info("Loaded fields from csv file.")

        # writer.writerow(['X', 'Y'] + cols)
        # for row in reader:
        #     writer.writerow(row)
        # log.info("Saved csv file with sanitized headers.")

    # Write VRT file
    vrt = os.path.join(hydro_results_folder, '{}.vrt'.format("dem_grid_results"))
    with open(vrt, 'wt') as f:
        f.write('<OGRVRTDataSource>\n')
        f.write('\t<OGRVRTLayer name="{}">\n'.format("dem_grid_results"))
        f.write('\t\t<SrcDataSource>{}</SrcDataSource>\n'.format(csvfile))
        f.write('\t\t<SrcLayer>{}</SrcLayer>\n'.format("dem_grid_results"))
        f.write('\t\t<GeometryType>wkbPoint25D</GeometryType>\n')
        f.write('\t\t<LayerSRS>{}</LayerSRS>\n'.format(dem_srs))
        f.write('\t\t<GeometryField encoding="PointFromColumns" x="X" y="Y" />\n')
        for field in cols:
            f.write('\t\t<Field name="{}" type="Real" subtype="Float32" />\n'.format(field))
        f.write('\t</OGRVRTLayer>\n')
        f.write('</OGRVRTDataSource>\n')
        log.info("Generated vrt file {}".format(vrt))

    # Open csv as OGR
    ogr_vrt = ogr.Open(vrt, 1)
    if ogr_vrt is None:
        raise DataException("unable to open {}".format(vrt))
    layer = ogr_vrt.GetLayer()

    # 4 Generate geotiff for each column in the CSV file
    driver = gdal.GetDriverByName("GTiff")
    for col in cols:
        out_tif = os.path.join(outfolder, '{}.tif'.format(col))

        out_raster = driver.Create(out_tif, dem_x_size, dem_y_size, 1, gdalconst.GDT_Float32)
        out_raster.SetGeoTransform(dem_geotransfrom)
        out_raster.SetProjection(dem_srs)
        band = out_raster.GetRasterBand(1)
        band.SetNoDataValue(dem_ndv)
        band.FlushCache()

        gdal.RasterizeLayer(out_raster, [1], layer, options=["ATTRIBUTE={}".format(col)])
        band.GetStatistics(0, 1)
        band.FlushCache()
        out_raster.FlushCache()
        log.info("Generated {} for attribute {}".format(out_tif, col))

        if col == "Depth":
            raw = numpy.array(band.ReadAsArray())
            masked = numpy.ma.masked_array(raw, raw == dem_ndv)
            bool_raster = numpy.array(masked, "bool")
            numpy.greater(masked, 0, bool_raster)

            raster_mem = gdal.GetDriverByName("GTIFF").Create(os.path.join(outfolder, "Temp.tif"), dem_x_size, dem_y_size, 1, gdalconst.GDT_Int16)
            raster_mem.SetGeoTransform(dem_geotransfrom)
            raster_mem.SetProjection(dem_srs)
            band_mem = raster_mem.GetRasterBand(1)
            band_mem.WriteArray(bool_raster, 0, 0)
            band_mem.SetNoDataValue(dem_ndv)
            band_mem.FlushCache()

            temp = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(os.path.join(outfolder, "TempExtent.shp"))
            temp_layer = temp.CreateLayer("RawExtent", osr.SpatialReference(wkt=dem_srs), ogr.wkbPolygon)
            temp_layer.CreateField(ogr.FieldDefn("Value", ogr.OFTInteger))
            temp_layer.CreateField(ogr.FieldDefn("Area", ogr.OFTReal))

            gdal.Polygonize(band_mem, None, temp_layer, 0)

            del raster_mem
        #
        #     for feature in temp_layer:
        #         feature.SetField("Area", feature.GetGeometryRef().GetArea())
        #         temp_layer.SetFeature(feature)

            # Stage Extent
            # temp_layer.SetAttributeFilter("Value=1")
            # shp_extent = os.path.join(outfolder, "StageExtent.shp")
            # driver_extent = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(shp_extent)
            # driver_extent.CopyLayer(temp_layer, "StageExtent")
            # driver_extent = None
            # ogr_extent = ogr.Open(shp_extent, 1)
            # layer_extent = ogr_extent.GetLayer("StageExtent")
            # field_extent = ogr.FieldDefn("ExtentType", ogr.OFTString)
            # layer_extent.CreateField(field_extent)
            # area_current = 0.0
            # fid_current = None
            # for feature in layer_extent:
            #     area_feat = feature.GetGeometryRef().GetArea()
            #     if area_feat > area_current:
            #         area_current = area_feat
            #         fid_current = feature.GetFID()
            #
            # edit_feat = layer_extent.GetFeature(fid_current)
            # edit_feat.SetField("ExtentType", "Channel")
            # layer_extent.SetFeature(edit_feat)
            #
            # layer_extent.DeleteField(layer_extent.FindFieldIndex("Value", True))
            # #ogr_extent.Destroy()
            # log.info("Generated Stage Extent Shapefile {}".format(shp_extent))
            #
            # # Stage Islands
            # import time
            # time.sleep(5)
            # temp_layer.ResetReading()
            # temp_layer.SetAttributeFilter("Value=0")
            # shp_islands = os.path.join(outfolder, "StageIslands.shp")
            # driver_islands = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(shp_islands)
            # driver_islands.CopyLayer(temp_layer, "StageIslands")
            # driver_islands = None
            # ogr_islands = ogr.Open(shp_islands, 1)
            # layer_islands = ogr_islands.GetLayer("StageIslands")
            #
            # field_qual = ogr.FieldDefn("Qualifying", ogr.OFTInteger)
            # field_qual.SetDefault("0")
            # field_valid = ogr.FieldDefn("IsValid", ogr.OFTInteger)
            # field_valid.SetDefault("0")
            # layer_islands.CreateField(field_qual)
            # layer_islands.CreateField(field_valid)
            # layer_islands.SyncToDisk()
            #
            # area_current = 0.0
            # fid_current = None
            # for feature in layer_islands:
            #     if feature is not None:
            #         g = feature.GetGeometryRef()
            #         area_feat = g.GetArea()
            #         # todo identify qualifying islands here?
            #         if area_feat > area_current:
            #             area_current = area_feat
            #             fid_current = feature.GetFID()
            #
            # #feat_del = layer_islands.GetFeature(fid_current)
            # layer_islands.DeleteFeature(fid_current)
            #
            # layer_islands.DeleteField(layer_islands.FindFieldIndex("Value", True))
            # ogr_islands = None
            # ogr_extent = None
            # log.info("Generated Stage Islands Shapefile {}".format(shp_islands))
            temp = None
        del out_raster

    shp_hydroresults = os.path.join(outfolder, "HydroResults.shp")
    ogr.GetDriverByName("ESRI Shapefile").CopyDataSource(ogr_vrt, shp_hydroresults)
    #out_shp = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource()
    # ogr_shp = ogr.Open(shp_hydroresults, 1)
    # lyr = ogr_shp.GetLayer()
    # lyr_defn = lyr.GetLayerDefn()
    # for i in range(lyr_defn.GetFieldCount()):
    #     fielddefn = lyr_defn.GetFieldDefn(i)
    #     fielddefn.SetName(fielddefn.GetName().replace(".","_"))
    #     lyr.AlterFieldDefn(i, fielddefn, ogr.ALTER_NAME_FLAG)
    #
    # new_field = ogr.FieldDefn('V_Bearing', ogr.OFTReal)
    # lyr.CreateField(new_field)
    # # Calculate Velocity Bearing
    # for feat in lyr:
    #     vel_x = feat.GetField("X_Velocity")
    #     vel_y = feat.GetField("Y_Velocity")
    #     dir = 90 - math.degrees(math.atan2(float(vel_y), float(vel_x)))
    #     bearing = 360 + dir if dir < 0 else dir
    #     feat.SetField('V_Bearing', float(bearing))
    #     lyr.SetFeature(feat)

    log.info("Generated Hydro Results Shapefile {}".format(shp_hydroresults))
    ogr_vrt = None
    ogr_shp = None

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
    logg = Logger("Program")
    logfile = os.path.join(resultsFolder, "hydro_gis.log")
    xmlfile = os.path.join(resultsFolder, "hydro_gis.xml")
    logg.setup(logPath=logfile, verbose=args.verbose)

    # Initiate the log file
    log = Logger("Program")
    log.setup(logPath=logfile, verbose=args.verbose)

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
        result = hydro_gis_export(args.hydroprojectxml, args.topoprojectxml, resultsFolder)

        sys.exit(result)

    except (DataException, MissingException, NetworkException) as e:
        # Exception class prints the relevant information
        traceback.print_exc(file=sys.stdout)
        sys.exit(e.returncode)
    except AssertionError as e:
        log.error(e.message)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
    except Exception as e:
        log.error(e.message)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

    #sys.exit(0)


if __name__ == "__main__":
    main()