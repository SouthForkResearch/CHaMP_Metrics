import unittest
from lib.raster import Raster

class RasterTest(unittest.TestCase):

    def test_min_nodata(self):
        testRaster = Raster('./data/bad_nodata/DEM.tif')
        self.assertAlmostEqual(testRaster.min, 911.59, places=3)
        self.assertAlmostEqual(testRaster.max, 917.924, places=3)

