import unittest
from lib.raster import Raster
from tools.validation.classes.validation_classes import *
from os import path
from lib import env

path_test_data = certFile = path.join(path.dirname(__file__),  'data')


# TODO export champ Test cases to GISLayers
class Dataset_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.dataset import Dataset
        testclass = Dataset("Dataset", path.join(path_test_data, "Dataset.gis"))
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")

    def test_validate_filenotexist(self):
        from tools.validation.classes.dataset import GIS_Dataset
        testclass = GIS_Dataset("dataset", "/path/does/not/exist/dataset.shp")
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Error")

    def test_optional_not_exist(self):
        from tools.validation.classes.dataset import GIS_Dataset
        testclass = GIS_Dataset("Dataset", "/path/does/not/exist/dataset.shp")
        testclass.required = False
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Warning")


class GIS_Dataset_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.dataset import GIS_Dataset
        testclass = GIS_Dataset("Topo_Points", path.join(path_test_data, "000_original", "GISLayers", "Topo_Points.shp"))
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")


class CHaMP_Raster_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.raster import CHaMP_Raster
        testclass = CHaMP_Raster("DEM", path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "SpatialReferenceExists"), "Pass")
        self.assertEqual(get_result_status(results, "TargetCellSize"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterHeight"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterWidth"), "Pass")
        self.assertEqual(get_result_status(results, "WholeMeterExtents"), "Pass")
        self.assertEqual(get_result_status(results, "ConcurrentWithDEM"), "NotTested")

    def test_concurrent_raster(self):
        from tools.validation.classes.raster import CHaMP_Raster
        testclass = CHaMP_Raster("DEM", path.join(path_test_data, "CHaMPRasterTests", "ConcurrentRasters", "DEM1.tif"))
        testRaster = Raster(path.join(path_test_data, "CHaMPRasterTests", "ConcurrentRasters", "DEM2.tif"))
        testclass.surveyDEM_Polygon = testRaster.getBoundaryShape()
        validation  = testclass.validate()
        self.assertEqual(get_result_status(validation, "ConcurrentWithDEM"), "Pass")

    def test_nonconcurrent_rasters(self):
        from tools.validation.classes.raster import CHaMP_Raster
        testclass = CHaMP_Raster("DEM", path.join(path_test_data, "CHaMPRasterTests", "NonConcurrentRasters", "DEM1.tif"))

        testRaster = Raster(path.join(path_test_data, "CHaMPRasterTests", "NonConcurrentRasters", "DifferentBottom.tif"))
        testclass.surveyDEM_Polygon = testRaster.getBoundaryShape()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "ConcurrentWithDEM"), "Warning")

        testRaster = Raster(path.join(path_test_data, "CHaMPRasterTests", "NonConcurrentRasters", "DifferentLeft.tif"))
        testclass.surveyDEM_Polygon = testRaster.getBoundaryShape()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "ConcurrentWithDEM"), "Warning")

        testRaster = Raster(path.join(path_test_data, "CHaMPRasterTests", "NonConcurrentRasters", "DifferentRight.tif"))
        testclass.surveyDEM_Polygon = testRaster.getBoundaryShape()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "ConcurrentWithDEM"), "Warning")

        testRaster = Raster(path.join(path_test_data, "CHaMPRasterTests", "NonConcurrentRasters", "DifferentTop.tif"))
        testclass.surveyDEM_Polygon = testRaster.getBoundaryShape()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "ConcurrentWithDEM"), "Warning")

    def test_spatial_ref_dem(self):
        from tools.validation.classes.raster import CHaMP_Raster
        testclass = CHaMP_Raster("DEM", path.join(path_test_data, "CHaMPRasterTests", "ConcurrentRasters", "DEM1.tif"))
        testDEM = CHaMP_Raster("DEM", path.join(path_test_data, "CHaMPRasterTests", "ConcurrentRasters", "DEM2.tif"))
        testclass.spatial_reference_dem_wkt = testDEM.get_crs_wkt()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "SpatialReferenceMatchesDEM"), "Pass")

    def test_wrong_spatial_ref_dem(self):
        from tools.validation.classes.raster import CHaMP_Raster
        testclass = CHaMP_Raster("DEM", path.join(path_test_data, "CHaMPRasterTests", "SpatialReference", "DEM1.tif"))
        testDEM = CHaMP_Raster("DEM", path.join(path_test_data, "CHaMPRasterTests", "SpatialReference", "DEM2.tif"))
        testclass.spatial_reference_dem_wkt = testDEM.get_crs_wkt()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "SpatialReferenceMatchesDEM"), "Error")


class CHaMP_Detrended_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.detrended import CHaMP_DetrendedDEM
        testclass = CHaMP_DetrendedDEM("DetrendedDEM", path.join(path_test_data, "000_original", "GISLayers", "Detrended.tif"))
        dem = Raster(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.surveyDEM_Polygon = dem.getBoundaryShape()
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "SpatialReferenceExists"), "Pass")
        self.assertEqual(get_result_status(results, "TargetCellSize"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterHeight"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterWidth"), "Pass")
        self.assertEqual(get_result_status(results, "WholeMeterExtents"), "Pass")
        self.assertEqual(get_result_status(results, "MinCellValue"), "Pass")
        self.assertEqual(get_result_status(results, "RangeCellValues"), "Pass")
        self.assertEqual(get_result_status(results, "ConcurrentWithDEM"), "Pass")


class CHaMP_DEM_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.dem import CHaMP_DEM
        testclass = CHaMP_DEM("DEM", path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "SpatialReferenceExists"), "Pass")
        self.assertEqual(get_result_status(results, "TargetCellSize"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterHeight"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterWidth"), "Pass")
        self.assertEqual(get_result_status(results, "WholeMeterExtents"), "Pass")
        self.assertEqual(get_result_status(results, "MinCellValue"), "Pass")
        self.assertEqual(get_result_status(results, "RangeCellValues"), "Pass")


class CHaMP_PointDensity_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.assoc_point_density import CHaMP_Associated_PointDensity
        testclass = CHaMP_Associated_PointDensity("PointDensity", path.join(path_test_data, "000_original", "GISLayers", "AssocPDensity.tif"))
        dem = Raster(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.surveyDEM_Polygon = dem.getBoundaryShape()
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "TargetCellSize"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterHeight"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterWidth"), "Pass")
        self.assertEqual(get_result_status(results, "WholeMeterExtents"), "Pass")
        self.assertEqual(get_result_status(results, "MinCellValue"), "Pass")
        self.assertEqual(get_result_status(results, "RangeCellValues"), "Pass")
        self.assertEqual(get_result_status(results, "ConcurrentWithDEM"), "Pass")


class CHaMP_PointQuality_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.assoc_3d_point_quality import CHaMP_Associated_3DPointQuality
        testclass = CHaMP_Associated_3DPointQuality("PointQuality", path.join(path_test_data, "000_original", "GISLayers", "Assoc3DPQ.tif"))
        dem = Raster(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.surveyDEM_Polygon = dem.getBoundaryShape()
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "TargetCellSize"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterHeight"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterWidth"), "Pass")
        self.assertEqual(get_result_status(results, "WholeMeterExtents"), "Pass")
        self.assertEqual(get_result_status(results, "ConcurrentWithDEM"), "Pass")


class CHaMP_Assoc_Slope_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.assoc_slope import CHaMP_Associated_Slope
        testclass = CHaMP_Associated_Slope("Slope", path.join(path_test_data, "000_original", "GISLayers", "AssocSlope.tif"))
        dem = Raster(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.surveyDEM_Polygon = dem.getBoundaryShape()
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "TargetCellSize"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterHeight"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterWidth"), "Pass")
        self.assertEqual(get_result_status(results, "WholeMeterExtents"), "Pass")
        self.assertEqual(get_result_status(results, "ConcurrentWithDEM"), "Pass")


class CHaMP_Assoc_Roughness_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.assoc_roughness import CHaMP_Associated_Roughness
        testclass = CHaMP_Associated_Roughness("Roughess", path.join(path_test_data, "000_original", "GISLayers", "AssocRough.tif"))
        dem = Raster(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.surveyDEM_Polygon = dem.getBoundaryShape()
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "TargetCellSize"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterHeight"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterWidth"), "Pass")
        self.assertEqual(get_result_status(results, "WholeMeterExtents"), "Pass")
        self.assertEqual(get_result_status(results, "ConcurrentWithDEM"), "Pass")


class CHaMP_Assoc_InterpolationError_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.assoc_interpolation_error import CHaMP_Associated_InterpolationError
        testclass = CHaMP_Associated_InterpolationError("Ierror", path.join(path_test_data, "000_original", "GISLayers", "AssocIErr.tif"))
        dem = Raster(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.surveyDEM_Polygon = dem.getBoundaryShape()
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "TargetCellSize"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterHeight"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterWidth"), "Pass")
        self.assertEqual(get_result_status(results, "WholeMeterExtents"), "Pass")
        self.assertEqual(get_result_status(results, "ConcurrentWithDEM"), "Pass")


class CHaMP_ErrorSurface_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.error_surface import CHaMP_ErrorSurface
        testclass = CHaMP_ErrorSurface("ErrorSurface", path.join(path_test_data, "000_original", "GISLayers", "ErrSurface.tif"))
        dem = Raster(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.surveyDEM_Polygon = dem.getBoundaryShape()
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "TargetCellSize"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterHeight"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterWidth"), "Pass")
        self.assertEqual(get_result_status(results, "WholeMeterExtents"), "Pass")
        self.assertEqual(get_result_status(results, "ConcurrentWithDEM"), "Pass")
        self.assertEqual(get_result_status(results, "MinCellValue"), "Pass")
        self.assertEqual(get_result_status(results, "RangeCellValues"), "Pass")


class CHaMP_WaterSurfaceDEM_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.water_surface_dem import CHaMP_WaterSurfaceDEM
        testclass = CHaMP_WaterSurfaceDEM("WaterSurface", path.join(path_test_data, "000_original", "GISLayers", "WSEDEM.tif"))
        dem = Raster(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.surveyDEM_Polygon = dem.getBoundaryShape()
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "TargetCellSize"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterHeight"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterWidth"), "Pass")
        self.assertEqual(get_result_status(results, "WholeMeterExtents"), "Pass")
        self.assertEqual(get_result_status(results, "ConcurrentWithDEM"), "Pass")
        self.assertEqual(get_result_status(results, "MinCellValue"), "Pass")


class CHaMP_WaterDepth_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.waterdepth import CHaMP_WaterDepth
        testclass = CHaMP_WaterDepth("WaterDepth", path.join(path_test_data, "000_original", "GISLayers", "Water_Depth.tif"))
        dem = Raster(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.surveyDEM_Polygon = dem.getBoundaryShape()
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "TargetCellSize"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterHeight"), "Pass")
        self.assertEqual(get_result_status(results, "MaxRasterWidth"), "Pass")
        self.assertEqual(get_result_status(results, "WholeMeterExtents"), "Pass")
        self.assertEqual(get_result_status(results, "ConcurrentWithDEM"), "Pass")
        self.assertEqual(get_result_status(results, "MinCellValue"), "Pass")
        self.assertEqual(get_result_status(results, "RangeCellValues"), "Pass")


class CHaMP_Vector_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.vector import CHaMP_Vector
        testclass = CHaMP_Vector("Topo_Points", path.join(path_test_data, "000_original", "GISLayers", "Topo_Points.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "SpatialReferenceExists"), "Pass")

    def test_no_features(self):
        from tools.validation.classes.vector import CHaMP_Vector
        testclass = CHaMP_Vector("Empty", path.join(path_test_data, "0001_emptyfeatureclass", "empty_feature_class.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Error")

    def test_validate_spatialreference(self):
        from tools.validation.classes.dataset import GIS_Dataset
        testclass = GIS_Dataset("Polyline", path.join(path_test_data, "0002_featureclass_nospatialreference", "polyline.shp"))
        results = testclass.validate()
        self.assertEqual(get_result_status(results, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(results, "Filename_Max_Length"), "Pass")
        self.assertEqual(get_result_status(results, "SpatialReferenceExists"), "Error")


class CHaMP_VectorPoint_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.vector import CHaMP_Vector_Point
        testclass = CHaMP_Vector_Point("Topo_Points", path.join(path_test_data, "000_original", "GISLayers", "Topo_Points.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")


class CHaMP_VectorPoint3D_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.vector import CHaMP_Vector_Point_3D
        testclass = CHaMP_Vector_Point_3D("Topo_Points", path.join(path_test_data, "000_original", "GISLayers", "Topo_Points.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "HasZ"), "Pass")


class CHaMP_TopoPoints_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.topo_points import CHaMP_TopoPoints
        from lib.raster import get_data_polygon
        testclass = CHaMP_TopoPoints("Topo_Points", path.join(path_test_data, "000_original", "GISLayers", "Topo_Points.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.dem = path.join(path_test_data, "000_original", "GISLayers", "DEM.tif")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "HasZ"), "Pass")
        self.assertEqual(get_result_status(validation, "CodeFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "CodeFieldNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "bfCount"), "Pass")
        self.assertEqual(get_result_status(validation, "tbCount"), "Pass")
        self.assertEqual(get_result_status(validation, "inCount"), "Pass")
        self.assertEqual(get_result_status(validation, "outCount"), "Pass")
        self.assertEqual(get_result_status(validation, "PointsOnDEM"), "Warning")
        self.assertEqual(get_result_status(validation, "tbPointsOnDEM"), "Pass")
        self.assertEqual(get_result_status(validation, "bfPointsOnDEM"), "Pass")
        self.assertEqual(get_result_status(validation, "InOutPointsOnDEMwithPosElev"), "Pass")

#     def test_nullcode(self):
#         from tools.validation.classes.topo_points import CHaMP_TopoPoints
#         testclass = CHaMP_TopoPoints(path.join(path_test_data, "000_original", "GISLayers")
#         validation = testclass.validate()
#
#         self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
#         self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
#         self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
#         self.assertEqual(get_result_status(validation, "HasZ"), "Pass")
#         self.assertEqual(get_result_status(validation, "CodeFieldExists"), "Pass")
#         self.assertEqual(get_result_status(validation, "CodeFieldNotNull"), "Error")
#         self.assertEqual(get_result_status(validation, "bfCount"), "NotTested")
#         self.assertEqual(get_result_status(validation, "tbCount"), "NotTested")
#         self.assertEqual(get_result_status(validation, "inCount"), "NotTested")
#         self.assertEqual(get_result_status(validation, "outCount"), "NotTested")
#
#     def test_bf_count(self):
#         from tools.validation.classes.topo_points import CHaMP_TopoPoints
#         testclass = CHaMP_TopoPoints(path.join(path_test_data, "000_original", "GISLayers")
#         #validation = testclass.validate()
#
#     def test_tb_count(self):
#         from tools.validation.classes.topo_points import CHaMP_TopoPoints
#         testclass = CHaMP_TopoPoints(path.join(path_test_data, "000_original", "GISLayers")
#         #validation = testclass.validate()
#
#
     # def test_in_out_points(self):
     #    from topo_points import CHaMP_TopoPoints
     #    testclass = CHaMP_TopoPoints(path.join(path_test_data, "000_original", "GISLayers")
     #    validation = testclass.validate()
     #
     #    self.assertEqual(get_result_status(validation, "InOutPointsOnDEMwithPosElev"), "Error")


    def test_within_dem_extent(self):
        from tools.validation.classes.topo_points import CHaMP_TopoPoints
        from lib.raster import get_data_polygon
        CHaMP_TopoPoints.fieldName_Description ="Code"
        testclass = CHaMP_TopoPoints("Topo_Points", path.join(path_test_data, "0037_TopoPointsBFNotOnDEM", "Topo_Points.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0037_TopoPointsBFNotOnDEM", "DEM.tif"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "HasZ"), "Pass")
        self.assertEqual(get_result_status(validation, "CodeFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "CodeFieldNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "bfCount"), "Pass")
        self.assertEqual(get_result_status(validation, "tbCount"), "Pass")
        self.assertEqual(get_result_status(validation, "inCount"), "Pass")
        self.assertEqual(get_result_status(validation, "outCount"), "Pass")
        self.assertEqual(get_result_status(validation, "PointsOnDEM"), "Warning")
        self.assertEqual(get_result_status(validation, "tbPointsOnDEM"), "Pass")
        self.assertEqual(get_result_status(validation, "bfPointsOnDEM"), "Warning")

    def test_in_higher_than_out(self):
        from tools.validation.classes.topo_points import CHaMP_TopoPoints
        from lib.raster import get_data_polygon
        CHaMP_TopoPoints.fieldName_Description = "Code"
        testclass = CHaMP_TopoPoints("Topo_Points", path.join(path_test_data, "0039_TopoPointsInLowerThanOut", "Topo_Points.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0039_TopoPointsInLowerThanOut", "DEM.tif"))
        testclass.dem = path.join(path_test_data, "0039_TopoPointsInLowerThanOut", "DEM.tif")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "InHigherThanOutPointDEM"), "Warning")


class CHaMP_EdgeofWaterPoints_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.edgeofwater_points import CHaMP_EdgeofWater_Points
        from lib.raster import get_data_polygon
        testclass = CHaMP_EdgeofWater_Points("EdgeofWater_Points", path.join(path_test_data, "000_original", "GISLayers", "EdgeofWater_Points.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.dem = path.join(path_test_data, "000_original", "GISLayers", "DEM.tif")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "HasZ"), "Pass")
        self.assertEqual(get_result_status(validation, "CodeFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "CodeFieldNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "RangeZValues"), "Pass")
        self.assertEqual(get_result_status(validation, "PointsOnDEM"), "Pass")
        self.assertEqual(get_result_status(validation, "RangeZValuesDEM"), "Pass")
        self.assertEqual(get_result_status(validation, "NegatveZValuesDEM"), "Pass")

    def test_within_dem_extent(self):
        from tools.validation.classes.edgeofwater_points import CHaMP_EdgeofWater_Points
        from lib.raster import get_data_polygon
        testclass = CHaMP_EdgeofWater_Points("EdgeofWater_Points", path.join(path_test_data, "0019_EoWOffDEM", "EdgeofWater_Points.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0019_EoWOffDEM", "DEM.tif"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "PointsOnDEM"), "Warning")

    def test_dem_elevation_range(self):
        from tools.validation.classes.edgeofwater_points import CHaMP_EdgeofWater_Points
        from lib.raster import get_data_polygon
        testclass = CHaMP_EdgeofWater_Points("EdgeofWater_Points", path.join(path_test_data, "0021_EoWElevationRange", "EdgeofWater_Points.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0021_EoWElevationRange", "DEM.tif"))
        testclass.dem = path.join(path_test_data, "0021_EoWElevationRange", "DEM.tif")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "RangeZValuesDEM"), "Error")

    def test_dem_elevation_negative(self):
        from tools.validation.classes.edgeofwater_points import CHaMP_EdgeofWater_Points
        from lib.raster import get_data_polygon
        testclass = CHaMP_EdgeofWater_Points("EdgeofWater_Points", path.join(path_test_data, "0020_EoWNegativeElev", "EdgeofWater_Points.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0020_EoWNegativeElev", "DEM.tif"))
        testclass.dem = path.join(path_test_data, "0020_EoWNegativeElev", "DEM.tif")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "NegatveZValuesDEM"), "Error")


class CHaMP_StreamFeatures_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.streamfeature_points import CHaMP_StreamFeature_Points
        testclass = CHaMP_StreamFeature_Points("StreamFeatures", path.join(path_test_data, "000_original", "GISLayers", "Stream_Features.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "NotTested")
        self.assertEqual(get_result_status(validation, "HasZ"), "NotTested")
        self.assertEqual(get_result_status(validation, "CodeFieldExists"), "NotTested")


class CHaMP_ControlPoints_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.control_points import CHaMP_ControlPoints
        testclass = CHaMP_ControlPoints("Control_Points", path.join(path_test_data, "000_original", "GISLayers", "Control_Points.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "HasZ"), "Pass")
        self.assertEqual(get_result_status(validation, "CodeFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "TypeFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "CodeFieldNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumZValue"), "Pass")
        self.assertEqual(get_result_status(validation, "RangeZValues"), "Pass")

    def test_missingfield(self):
        from tools.validation.classes.control_points import CHaMP_ControlPoints
        testclass = CHaMP_ControlPoints("Control_Points", path.join(path_test_data, "0011_ControlPointsMissingTypeField", "Control_Points.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "HasZ"), "Pass")
        self.assertEqual(get_result_status(validation, "CodeFieldExists"), "Error")
        self.assertEqual(get_result_status(validation, "TypeFieldExists"), "Warning")
        self.assertEqual(get_result_status(validation, "CodeFieldNotNull"), "NotTested")
        self.assertEqual(get_result_status(validation, "MinimumZValue"), "Pass")
        self.assertEqual(get_result_status(validation, "RangeZValues"), "Pass")


class CHaMP_Error_Points_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.error_points import CHaMP_Error_Points
        testclass = CHaMP_Error_Points("Error_Points", path.join(path_test_data, "000_original", "GISLayers", "Error_Points.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        # self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        # self.assertEqual(get_result_status(validation, "HasZ"), "Pass")
        # self.assertEqual(get_result_status(validation, "CodeFieldExists"), "Pass")


class CHaMP_Polyline_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.vector import CHaMP_Vector_Polyline
        testclass = CHaMP_Vector_Polyline("Breaklines", path.join(path_test_data, "000_original", "GISLayers", "Breaklines.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")


class CHaMP_Breaklines_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.breaklines import CHaMP_Breaklines
        from tools.validation.classes.vector import CHaMP_Vector_Point_3D
        testclass = CHaMP_Breaklines("Breaklines", path.join(path_test_data, "000_original", "GISLayers", "Breaklines.shp"))
        tp = CHaMP_Vector_Point_3D("Topo_Points", path.join(path_test_data, "000_original", "GISLayers", "Topo_Points.shp"))
        eow = CHaMP_Vector_Point_3D("EdgeofWater_Points", path.join(path_test_data, "000_original", "GISLayers", "EdgeofWater_Points"))
        testclass.survey_points = tp.get_list_geoms() + eow.get_list_geoms()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "HasZ"), "Pass")
        self.assertEqual(get_result_status(validation, "CodeFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "LineTypeFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "VertexOnPoints"), "Pass")

    def test_ogr_bug(self):
        from lib.exception import DataException
        from tools.validation.classes.breaklines import CHaMP_Breaklines
        CHaMP_Breaklines.fieldName_Description = "DESCRIPTIO" # Old Harold Name

        with self.assertRaises(DataException) as e:
            testclass = CHaMP_Breaklines("Breaklines", path.join(path_test_data, "0094_BL_StrangeOGR_Bug", "Breaklines.shp"))
        # validation = testclass.validate()
        # self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        # self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        # self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        # self.assertEqual(get_result_status(validation, "HasZ"), "Pass")
        # self.assertEqual(get_result_status(validation, "CodeFieldExists"), "Pass")
        # self.assertEqual(get_result_status(validation, "LineTypeFieldExists"), "Pass")
        # self.assertEqual(get_result_status(validation, "MinLength"), "Pass")

    def test_no_geom(self):
        from tools.validation.classes.breaklines import CHaMP_Breaklines
        testclass = CHaMP_Breaklines("Breaklines", path.join(path_test_data, "0095_BL_NoGeom", "Breaklines.shp"))
        CHaMP_Breaklines.fieldName_Description = "DESCRIPTIO" # Old Harold name
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "HasZ"), "Pass")
        self.assertEqual(get_result_status(validation, "CodeFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "LineTypeFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Error")


class CHaMP_Polyline_LongLines_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.vector import CHaMP_Vector_Polyline_LongLine
        from tools.validation.classes.water_extent import CHaMP_WaterExtent
        from tools.validation.classes.islands import CHaMP_Islands
        from lib.raster import get_data_polygon
        testclass = CHaMP_Vector_Polyline_LongLine("Thalweg", path.join(path_test_data, "000_original", "GISLayers", "Thalweg.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        we = CHaMP_WaterExtent("WaterExtent", path.join(path_test_data, "000_original", "GISLayers", "WaterExtent.shp"), "Wetted")
        isle = CHaMP_Islands("WISlands", path.join(path_test_data, "000_original", "GISLayers", "WIslands.shp"), "Wetted")
        testclass.extent_polygon = we.get_main_extent_polygon()
        testclass.island_polygons = isle.get_qualifying_island_polygons()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "SinglePartFeatures"), "Pass")
        self.assertEqual(get_result_status(validation, "ClosedLoopFeatures"), "Pass")
        self.assertEqual(get_result_status(validation, "FeaturesStartStopOnDEM"), "Pass")
        self.assertEqual(get_result_status(validation, "FeaturesWithinChannelExtent"), "Pass")
        self.assertEqual(get_result_status(validation, "FeaturesNotIntersectIslands"), "NotTested")

    def test_min_length_error(self):
        # todo write test
        pass

    def test_min_length_warning(self):
        # todo write test
        pass

    def test_multipart_feats(self):
        from tools.validation.classes.vector import CHaMP_Vector_Polyline_LongLine
        testclass = CHaMP_Vector_Polyline_LongLine("Thalweg", path.join(path_test_data, "0044_ThalwegMultiPartFeatures", "Thalweg.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Error")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "SinglePartFeatures"), "Error")
        self.assertEqual(get_result_status(validation, "ClosedLoopFeatures"), "NotTested")

    def test_closed_loop_feats(self):
        from tools.validation.classes.vector import CHaMP_Vector_Polyline_LongLine
        testclass = CHaMP_Vector_Polyline_LongLine("BankfullCL", path.join(path_test_data, "0091_LongLinesClosedLoop", "BankfullCL.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "SinglePartFeatures"), "Pass")
        self.assertEqual(get_result_status(validation, "ClosedLoopFeatures"), "Error")

    def test_start_stop_on_raster(self):
        from tools.validation.classes.vector import CHaMP_Vector_Polyline_LongLine
        from lib.raster import get_data_polygon
        testclass = CHaMP_Vector_Polyline_LongLine("Thalweg", path.join(path_test_data, "0045_ThalwegFromNotOnDEM", "Thalweg.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0045_ThalwegFromNotOnDEM", "DEM.tif"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "FeaturesStartStopOnDEM"), "Warning")

    def test_within_extent(self):
        from tools.validation.classes.vector import CHaMP_Vector_Polyline_LongLine
        from tools.validation.classes.water_extent import CHaMP_WaterExtent
        from lib.raster import get_data_polygon
        testclass = CHaMP_Vector_Polyline_LongLine("Thalweg", path.join(path_test_data, "0047_LongLineOutsideWaterExtent", "Thalweg.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0047_LongLineOutsideWaterExtent", "DEM.tif"))
        we = CHaMP_WaterExtent("WExtent", path.join(path_test_data, "0047_LongLineOutsideWaterExtent", "WaterExtent.shp"), "Wetted")
        testclass.extent_polygon = we.get_main_extent_polygon()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "SinglePartFeatures"), "Pass")
        self.assertEqual(get_result_status(validation, "ClosedLoopFeatures"), "Pass")
        self.assertEqual(get_result_status(validation, "FeaturesStartStopOnDEM"), "Pass")
        self.assertEqual(get_result_status(validation, "FeaturesWithinChannelExtent"), "Warning")

    def test_intersect_islands(self):
        from tools.validation.classes.vector import CHaMP_Vector_Polyline_LongLine
        from tools.validation.classes.water_extent import CHaMP_WaterExtent
        from tools.validation.classes.islands import CHaMP_Islands
        from lib.raster import get_data_polygon
        testclass = CHaMP_Vector_Polyline_LongLine("Thalweg", path.join(path_test_data, "0092_CenterlineComplexOverIsland", "Thalweg.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0092_CenterlineComplexOverIsland", "DEM.tif"))
        we = CHaMP_WaterExtent("WExtent", path.join(path_test_data, "0092_CenterlineComplexOverIsland", "WaterExtent.shp"), "Wetted")
        isle = CHaMP_Islands("WIslands", path.join(path_test_data, "0092_CenterlineComplexOverIsland", "WIslands.shp"),"Wetted")
        testclass.extent_polygon = we.get_main_extent_polygon()
        testclass.island_polygons = isle.get_qualifying_island_polygons()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "SinglePartFeatures"), "Pass")
        self.assertEqual(get_result_status(validation, "ClosedLoopFeatures"), "Pass")
        self.assertEqual(get_result_status(validation, "FeaturesStartStopOnDEM"), "Pass")
        self.assertEqual(get_result_status(validation, "FeaturesWithinChannelExtent"), "Warning")
        self.assertEqual(get_result_status(validation, "FeaturesNotIntersectIslands"), "Error")

class CHaMP_Thalweg_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.thalweg import CHaMP_Thalweg
        from tools.validation.classes.topo_points import CHaMP_TopoPoints
        from lib.raster import get_data_polygon
        testclass = CHaMP_Thalweg("Thalweg", path.join(path_test_data, "000_original", "GISLayers", "Thalweg.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "000_original", "GISLayers", "DEM.tif"))
        testclass.dem = path.join(path_test_data, "000_original", "GISLayers", "DEM.tif")
        testclass.wsedemExtent = get_data_polygon(path.join(path_test_data, "000_original", "GISLayers", "wsedem.tif"))
        tp = CHaMP_TopoPoints("Topo_Points", path.join(path_test_data, "000_original", "GISLayers", "Topo_Points.shp"))
        testclass.topo_in_point = tp.get_in_point()
        testclass.topo_out_point = tp.get_out_point()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "MaxFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "FeaturesStartStopOnDEM"), "Pass")
        self.assertEqual(get_result_status(validation, "WithinWSEDEMExtent"), "Pass")
        self.assertEqual(get_result_status(validation, "InPointNearEnd"), "Pass")
        self.assertEqual(get_result_status(validation, "OutPointNearStart"), "Pass")
        self.assertEqual(get_result_status(validation, "StartPointLowerEndPoint"), "Pass")

    def test_within_wsedem(self):
        from tools.validation.classes.thalweg import CHaMP_Thalweg
        from lib.raster import get_data_polygon
        testclass = CHaMP_Thalweg("Thalweg", path.join(path_test_data, "0046_ThalwegToNotOnDEM", "Thalweg.shp"))
        testclass.wsedemExtent = get_data_polygon(path.join(path_test_data, "0046_ThalwegToNotOnDEM", "wsedem.tif"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "WithinWSEDEMExtent"), "Error")

    def test_in_point_not_near(self):
        from tools.validation.classes.thalweg import CHaMP_Thalweg
        from tools.validation.classes.topo_points import CHaMP_TopoPoints
        from lib.raster import get_data_polygon
        CHaMP_TopoPoints.fieldName_Description = "Code"
        testclass = CHaMP_Thalweg("Thalweg", path.join(path_test_data, "0048_ThalwegStartTooFarInFlow", "Thalweg.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0048_ThalwegStartTooFarInFlow", "DEM.tif"))
        testclass.wsedemExtent = get_data_polygon(path.join(path_test_data, "0048_ThalwegStartTooFarInFlow", "wsedem.tif"))
        tp = CHaMP_TopoPoints("Topo_Points", path.join(path_test_data, "0048_ThalwegStartTooFarInFlow", "Topo_Points.shp"))
        testclass.topo_in_point = tp.get_in_point()
        testclass.topo_out_point = tp.get_out_point()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "MaxFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "FeaturesStartStopOnDEM"), "Pass")
        self.assertEqual(get_result_status(validation, "WithinWSEDEMExtent"), "Pass")
        self.assertEqual(get_result_status(validation, "InPointNearEnd"), "Warning")
        self.assertEqual(get_result_status(validation, "OutPointNearStart"), "Pass")

    def test_out_point_not_near(self):
        from tools.validation.classes.thalweg import CHaMP_Thalweg
        from tools.validation.classes.topo_points import CHaMP_TopoPoints
        from lib.raster import get_data_polygon
        testclass = CHaMP_Thalweg("Thalweg", path.join(path_test_data, "0049_ThalwegEndTooFarOutFlow", "Thalweg.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0049_ThalwegEndTooFarOutFlow", "DEM.tif"))
        testclass.wsedemExtent = get_data_polygon(path.join(path_test_data, "0049_ThalwegEndTooFarOutFlow", "wsedem.tif"))
        tp = CHaMP_TopoPoints("Topo_Points", path.join(path_test_data, "0049_ThalwegEndTooFarOutFlow", "Topo_Points.shp"))
        testclass.topo_in_point = tp.get_in_point()
        testclass.topo_out_point = tp.get_out_point()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "MaxFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "FeaturesStartStopOnDEM"), "Pass")
        self.assertEqual(get_result_status(validation, "WithinWSEDEMExtent"), "Pass")
        self.assertEqual(get_result_status(validation, "InPointNearEnd"), "Pass")
        self.assertEqual(get_result_status(validation, "OutPointNearStart"), "Warning")

    def test_start_stop_on_raster(self):
        from tools.validation.classes.thalweg import CHaMP_Thalweg
        from lib.raster import get_data_polygon
        testclass = CHaMP_Thalweg("Thalweg", path.join(path_test_data, "0045_ThalwegFromNotOnDEM", "Thalweg.shp"))
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0045_ThalwegFromNotOnDEM", "DEM.tif"))
        testclass.dem = path.join(path_test_data, "0045_ThalwegFromNotOnDEM", "DEM.tif")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "ThalwegStartStopOnDEM"), "Error")

            # def test_outflow_higherthan_inflow(self):
    #     from thalweg import CHaMP_Thalweg
    #     from topo_points import CHaMP_TopoPoints
    #     from topometrics.raster import get_data_polygon
    #     testclass = CHaMP_Thalweg(path.join(path_test_data, "0049_ThalwegEndTooFarOutFlow")
    #     testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0049_ThalwegEndTooFarOutFlow", "DEM.tif")
    #     testclass.wsedemExtent = get_data_polygon(path.join(path_test_data, "0049_ThalwegEndTooFarOutFlow", "wsedem.tif")
    #     tp = CHaMP_TopoPoints(path.join(path_test_data, "0049_ThalwegEndTooFarOutFlow")
    #     testclass.topo_in_point = tp.get_in_point()
    #     testclass.topo_out_point = tp.get_out_point()
    #     validation = testclass.validate()
    #     self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
    #     self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
    #     self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
    #     self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
    #     self.assertEqual(get_result_status(validation, "MaxFeatureCount"), "Pass")
    #     self.assertEqual(get_result_status(validation, "FeaturesStartStopOnDEM"), "Pass")
    #     self.assertEqual(get_result_status(validation, "WithinWSEDEMExtent"), "Pass")
    #     self.assertEqual(get_result_status(validation, "InPointNearEnd"), "Pass")
    #     self.assertEqual(get_result_status(validation, "OutPointNearStart"), "Pass")
    #     #self.assertEqual(get_result_status(validation, "StartPointLowerEndPoint"), "Error")

class CHaMP_Centerline_Class(unittest.TestCase):

    def test_validate_Wetted(self):
        from tools.validation.classes.centerline import CHaMP_Centerline
        from tools.validation.classes.thalweg import CHaMP_Thalweg
        from lib.raster import get_data_polygon
        testclass = CHaMP_Centerline("CenterLine", path.join(path_test_data, "000_original", "GISLayers", "CenterLine.shp"), "Wetted")
        testclass.thalweg = CHaMP_Thalweg("Thalweg", path.join(path_test_data, "000_original", "GISLayers", "Thalweg.shp")).get_thalweg()
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "000_original", "GISLayers", "dem.tif"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldMainCount"), "Pass")
        self.assertEqual(get_result_status(validation, "MainChannelLength"), "Pass")
        self.assertEqual(get_result_status(validation, "MainChannel10%Thalweg"), "Pass")

    def test_channel_field_exists(self):
        from tools.validation.classes.centerline import CHaMP_Centerline
        from lib.raster import get_data_polygon
        testclass = CHaMP_Centerline("CenterLine", path.join(path_test_data, "0068_CLComplexMissingField", "CenterLine.shp"), "Wetted")
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0068_CLComplexMissingField", "dem.tif"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldExists"), "Error")
        self.assertEqual(get_result_status(validation, "ChannelFieldNotNull"), "NotTested")
        self.assertEqual(get_result_status(validation, "ChannelFieldMainCount"), "NotTested")

    def test_channel_field_null_values(self):
        from tools.validation.classes.centerline import CHaMP_Centerline
        from lib.raster import get_data_polygon
        testclass = CHaMP_Centerline("CenterLine", path.join(path_test_data, "0067_CLComplesInvalidType", "CenterLine.shp"), "Wetted")
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0067_CLComplesInvalidType", "dem.tif"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldNotNull"), "Error")
        self.assertEqual(get_result_status(validation, "ChannelFieldMainCount"), "NotTested")

    def test_channel_field_main_count(self):
        from tools.validation.classes.centerline import CHaMP_Centerline
        from lib.raster import get_data_polygon
        testclass = CHaMP_Centerline("CenterLine", path.join(path_test_data, "0066_CLMissingMainstem", "CenterLine.shp"), "Wetted")
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0066_CLMissingMainstem", "dem.tif"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldMainCount"), "Error")

    def test_centerline_length_less_50m(self):
        from tools.validation.classes.centerline import CHaMP_Centerline
        from lib.raster import get_data_polygon
        testclass = CHaMP_Centerline("CenterLine", path.join(path_test_data, "0090_CentrelineMinDesiredLength", "CenterLine.shp"), "Wetted")
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0090_CentrelineMinDesiredLength", "dem.tif"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldMainCount"), "Pass")
        self.assertEqual(get_result_status(validation, "MainChannelLength"), "Warning")

    def test_10percent_thalweg_length(self):
        from tools.validation.classes.centerline import CHaMP_Centerline
        from tools.validation.classes.thalweg import CHaMP_Thalweg
        from lib.raster import get_data_polygon
        testclass = CHaMP_Centerline("CenterLine", path.join(path_test_data, "0061_CenterlineThalwegLength", "CenterLine.shp"), "Wetted")
        testclass.thalweg = CHaMP_Thalweg("Thalweg", path.join(path_test_data, "0061_CenterlineThalwegLength", "Thalweg.shp")).get_thalweg()
        testclass.demDataExtent = get_data_polygon(path.join(path_test_data, "0061_CenterlineThalwegLength", "dem.tif"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldMainCount"), "Pass")
        self.assertEqual(get_result_status(validation, "MainChannelLength"), "Pass")
        self.assertEqual(get_result_status(validation, "MainChannel10%Thalweg"), "Warning")

    def test_validate_Bankfull(self):
        from tools.validation.classes.centerline import CHaMP_Centerline
        testclass = CHaMP_Centerline("BankfullCL", path.join(path_test_data, "000_original", "GISLayers", "BankfullCL.shp"), "Bankfull")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldExists"), "Pass")


class CHaMP_CrossSection_Class(unittest.TestCase):
    def test_validate_Wetted(self):
        from tools.validation.classes.cross_sections import CHaMP_CrossSections
        testclass = CHaMP_CrossSections("WettedXS", path.join(path_test_data, "000_original", "GISLayers", "WettedXS.shp"), "Wetted")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "IsValidFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldValidValues"), "Pass")

    def test_null_channel_value(self):
        from tools.validation.classes.cross_sections import CHaMP_CrossSections
        testclass = CHaMP_CrossSections("WettedXS", path.join(path_test_data, "0093_ComplexXS_NullChannel", "GISLayers", "WettedXS.shp"), "Wetted")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "IsValidFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldValidValues"), "Error")

    def test_validate_Bankfull(self):
        from tools.validation.classes.cross_sections import CHaMP_CrossSections
        testclass = CHaMP_CrossSections("BankfullXS", path.join(path_test_data, "000_original", "GISLayers", "BankfullXS.shp"), "Bankfull")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        # self.assertEqual(get_result_status(validation, "MinLength"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelFieldExists"), "Pass")
        self.assertEqual(get_result_status(validation, "IsValidFieldExists"), "Pass")


class CHaMP_Polygon_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.vector import CHaMP_Polygon
        testclass = CHaMP_Polygon("WaterExtent", path.join(path_test_data, "000_original", "GISLayers", "WaterExtent.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")


class CHaMP_WaterExtent_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.water_extent import CHaMP_WaterExtent
        from tools.validation.classes.topo_points import CHaMP_TopoPoints
        testclass = CHaMP_WaterExtent("WaterExtent", path.join(path_test_data, "000_original", "GISLayers", "WaterExtent.shp"), "Wetted")
        tp = CHaMP_TopoPoints("Topo_Points", path.join(path_test_data, "000_original", "GISLayers", "Topo_Points.shp"))
        testclass.topo_in_point = tp.get_in_point()
        testclass.topo_out_point = tp.get_out_point()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldExtentTypeExists"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldExtentTypeChannel"), "Pass")
        self.assertEqual(get_result_status(validation, "SinglePartFeatures"), "Pass")
        self.assertEqual(get_result_status(validation, "InOutWithinExtent"), "Pass")

    def test_field_extenttype_exists(self):
        from tools.validation.classes.water_extent import CHaMP_WaterExtent
        testclass = CHaMP_WaterExtent("WaterExtent", path.join(path_test_data, "0056_WaterExtentFieldMissing", "WaterExtent.shp"), "Wetted")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "SinglePartFeatures"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldExtentTypeExists"), "Error")
        self.assertEqual(get_result_status(validation, "FieldExtentTypeChannel"), "NotTested")

    def test_field_extenttype_channel(self):
        from tools.validation.classes.water_extent import CHaMP_WaterExtent
        testclass = CHaMP_WaterExtent("WaterExtent", path.join(path_test_data, "0058_WaterExtentMissingMain", "WaterExtent.shp"), "Wetted")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "SinglePartFeatures"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldExtentTypeExists"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldExtentTypeChannel"), "Error")

        testclass2 = CHaMP_WaterExtent("WaterExtent", path.join(path_test_data, "0058_WaterExtentMissingMain", "WaterExtent.shp"), "Wetted")
        validation2 = testclass2.validate()
        self.assertEqual(get_result_status(validation2, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation2, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation2, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation2, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "SinglePartFeatures"), "Pass")
        self.assertEqual(get_result_status(validation2, "FieldExtentTypeExists"), "Pass")
        self.assertEqual(get_result_status(validation2, "FieldExtentTypeChannel"), "Error")


    def test_singlepart_features(self):
        from tools.validation.classes.water_extent import CHaMP_WaterExtent
        testclass = CHaMP_WaterExtent("WaterExtent", path.join(path_test_data, "0053_WaterExtentMultiPart", "WaterExtent.shp"), "Wetted")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "SinglePartFeatures"), "Error")
        self.assertEqual(get_result_status(validation, "FieldExtentTypeExists"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldExtentTypeChannel"), "Pass")

    def test_tp_in_out_extent(self):
        from tools.validation.classes.water_extent import CHaMP_WaterExtent
        from tools.validation.classes.topo_points import CHaMP_TopoPoints
        CHaMP_TopoPoints.fieldName_Description = "Code"
        testclass = CHaMP_WaterExtent("WaterExtent", path.join(path_test_data, "0054_WaterExtentInFlow", "WaterExtent.shp"), "Wetted")
        tp = CHaMP_TopoPoints("Topo_Points", path.join(path_test_data, "0054_WaterExtentInFlow", "Topo_Points.shp"))
        testclass.topo_in_point = tp.get_in_point()
        testclass.topo_out_point = tp.get_out_point()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldExtentTypeExists"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldExtentTypeChannel"), "Pass")
        self.assertEqual(get_result_status(validation, "SinglePartFeatures"), "Pass")
        self.assertEqual(get_result_status(validation, "InOutWithinExtent"), "Error")

class CHaMP_Islands_Class(unittest.TestCase):

    def test_validate_wetted(self):
        from tools.validation.classes.islands import CHaMP_Islands
        testclass = CHaMP_Islands("WIslands", path.join(path_test_data, "000_original", "GISLayers", "WIslands.shp"), "Wetted")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "NotTested")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "NotTested")
        self.assertEqual(get_result_status(validation, "FieldIsValidExists"), "NotTested")
        self.assertEqual(get_result_status(validation, "FieldQualifyingExists"), "NotTested")

    def test_validate_bankfull(self):
        from tools.validation.classes.islands import CHaMP_Islands
        testclass = CHaMP_Islands("WIslands", path.join(path_test_data, "000_original", "GISLayers", "BIslands.shp"), "Bankfull")
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "NotTested")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "NotTested")
        self.assertEqual(get_result_status(validation, "FieldIsValidExists"), "NotTested")
        self.assertEqual(get_result_status(validation, "FieldQualifyingExists"), "NotTested")


class CHaMP_ChannelUnits_Class(unittest.TestCase):

    def test_validate(self):
        from tools.validation.classes.channel_units import CHaMP_ChannelUnits
        from tools.validation.classes.water_extent import CHaMP_WaterExtent
        testclass = CHaMP_ChannelUnits("Channel_Units", path.join(path_test_data, "000_original", "GISLayers", "Channel_Units.shp"))
        testclass.load_attributes_db(3506, path.join(path_test_data, "workbench.db"))
        testclass.wetted_extent = CHaMP_WaterExtent("WaterExtent", path.join(path_test_data, "000_original", "GISLayers", "WaterExtent.shp"), "Wetted").get_main_extent_polygon()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberExists"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberPositive"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberUnique"), "Pass")
        self.assertEqual(get_result_status(validation, "UnitNumbersGISInAux"),"Pass")
        self.assertEqual(get_result_status(validation, "UnitNumbersAuxInGIS"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelUnitsWithinWettedExtent"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelUnitsOverlap"), "Pass")

    def test_missing_unitnumber_field(self):
        from tools.validation.classes.channel_units import CHaMP_ChannelUnits
        testclass = CHaMP_ChannelUnits("Channel_Units", path.join(path_test_data, "0079_CUMissingField", "Channel_Units.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberExists"), "Error")

    def test_unitnumber_field_notnull(self):
        from tools.validation.classes.channel_units import CHaMP_ChannelUnits
        testclass = CHaMP_ChannelUnits("Channel_Units", path.join(path_test_data, "0081_CUNullValue", "Channel_Units.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberExists"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberPositive"), "Error")

    def test_unitnumber_field_unique(self):
        from tools.validation.classes.channel_units import CHaMP_ChannelUnits
        testclass = CHaMP_ChannelUnits("Channel_Units", path.join(path_test_data, "0078_CUDplicate", "Channel_Units.shp"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberExists"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberPositive"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberUnique"), "Error")

    def test_unitnumber_gis_not_aux(self):
        from tools.validation.classes.channel_units import CHaMP_ChannelUnits
        testclass = CHaMP_ChannelUnits("Channel_Units", path.join(path_test_data, "0073_CUMissingFromAux", "Channel_Units.shp"))
        testclass.load_attributes_db(3506, path.join(path_test_data, "workbench.db"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberExists"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberPositive"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberUnique"), "Pass")
        self.assertEqual(get_result_status(validation, "UnitNumbersGISInAux"), "Error")
        self.assertEqual(get_result_status(validation, "UnitNumbersAuxInGIS"), "Pass")

    def test_unitnumber_aux_not_gis(self):
        from tools.validation.classes.channel_units import CHaMP_ChannelUnits
        testclass = CHaMP_ChannelUnits("Channel_Units", path.join(path_test_data, "0072_CUMissingFromGIS", "Channel_Units.shp"))
        testclass.load_attributes_db(3506, path.join(path_test_data, "workbench.db"))
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberExists"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberPositive"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberUnique"), "Pass")
        self.assertEqual(get_result_status(validation, "UnitNumbersAuxInGIS"), "Warning")
        self.assertEqual(get_result_status(validation, "UnitNumbersGISInAux"),"Pass")

    def test_channelunits_in_wettedextent(self):
        from tools.validation.classes.channel_units import CHaMP_ChannelUnits
        from tools.validation.classes.water_extent import CHaMP_WaterExtent
        testclass = CHaMP_ChannelUnits("Channel_Units", path.join(path_test_data, "0077_CUOutsideWetted", "Channel_Units.shp"))
        testclass.load_attributes_db(3506, path.join(path_test_data, "workbench.db"))
        testclass.wetted_extent = CHaMP_WaterExtent("WaterExtent", path.join(path_test_data, "0077_CUOutsideWetted", "WaterExtent.shp"),
                                                    "Wetted").get_main_extent_polygon()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberExists"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberPositive"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberUnique"), "Pass")
        self.assertEqual(get_result_status(validation, "UnitNumbersGISInAux"), "Pass")
        self.assertEqual(get_result_status(validation, "UnitNumbersAuxInGIS"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelUnitsWithinWettedExtent"), "Warning")

    def test_channelunits_overlap(self):
        from tools.validation.classes.channel_units import CHaMP_ChannelUnits
        from tools.validation.classes.water_extent import CHaMP_WaterExtent
        testclass = CHaMP_ChannelUnits("Channel_Units", path.join(path_test_data, "0076_CUOverlapping", "Channel_Units.shp"))
        testclass.load_attributes_db(3506, path.join(path_test_data, "workbench.db"))
        testclass.wetted_extent = CHaMP_WaterExtent("WaterExtent", path.join(path_test_data, "0076_CUOverlapping", "WaterExtent.shp"), "Wetted").get_main_extent_polygon()
        validation = testclass.validate()
        self.assertEqual(get_result_status(validation, "Dataset_Exists"), "Pass")
        self.assertEqual(get_result_status(validation, "MinFeatureCount"), "Pass")
        self.assertEqual(get_result_status(validation, "GeometryType"), "Pass")
        self.assertEqual(get_result_status(validation, "MinimumArea"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberExists"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberNotNull"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberPositive"), "Pass")
        self.assertEqual(get_result_status(validation, "FieldUnitNumberUnique"), "Pass")
        self.assertEqual(get_result_status(validation, "UnitNumbersGISInAux"),"Pass")
        self.assertEqual(get_result_status(validation, "UnitNumbersAuxInGIS"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelUnitsWithinWettedExtent"), "Pass")
        self.assertEqual(get_result_status(validation, "ChannelUnitsOverlap"), "Warning")


class CHaMP_Survey_Class(unittest.TestCase):
    """
    NOTE: These tests depend on the API. If they fail it could be that the API data no longer matches what we have
    locally.
    """
    def test_validate(self):
        from tools.validation.champ_survey import CHaMPSurvey
        survey = CHaMPSurvey()
        survey.load_topo_project(path.join(path_test_data, r"000_original", r"GISLayers"), 3506)
        survey.ChannelUnits.fieldName_UnitNumber = "UnitNumber"
        results = survey.validate()
        for results_dataset in results.itervalues():
            for result in results_dataset:
                # TODO: I've lost the plot and I don't really know what this is supposed to test
                self.assertIn(result['Status'], ["Error", "Warning", "NotTested"], " ".join([v for v in result.itervalues()]))

    def test_validate_0056_WaterExtentFieldMissing(self):
        from tools.validation.champ_survey import CHaMPSurvey
        survey = CHaMPSurvey()
        survey.load_topo_project(path.join(path_test_data, r"0056_WaterExtentFieldMissing", r"GISLayers"), 3506)
        results = survey.validate()
        self.assertEqual(get_result_status(results["WaterExtent"], "FieldExtentTypeExists"), "Error")

    def test_validate_0096_original_MissingTopoPointsFC(self):
        from tools.validation.champ_survey import CHaMPSurvey
        survey = CHaMPSurvey()
        survey.load_topo_project(path.join(path_test_data, r"0096_original_MissingTopoPointsFC", r"GISLayers"), 3506)
        results = survey.validate()
        self.assertEqual(get_result_status(results["Topo_Points"], "Dataset_Exists"), "Error")