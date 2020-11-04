import unittest
import numpy as np

class ThalwegTest(unittest.TestCase):

    def test_thalwegprofile(self):
        self.assertTrue(False)

    # def test_triangle(self):
    #     from topometrics.raster import Raster, PrintArr
    #     from shapely.geometry import Polygon, MultiPolygon, box
    #     from matplotlib import pyplot as plt
    #     from descartes import PolygonPatch
    #
    #     r = Raster('/Users/work/Downloads/Visit_2648_ChannelUnits_And_DEM/DEM.tif')
    #     s = Shapefile('/Users/work/Downloads/Visit_2648_ChannelUnits_And_DEM/Channel_Units.shp')
    #
    #     # Make a weird triangle
    #     poly = Polygon(
    #         [
    #             ((r.left + r.getWidth() / 4), (r.getBottom() + r.getHeight() / 4)),
    #             ((r.left + r.getWidth() / 2), (r.top - r.getHeight() / 4)),
    #             ((r.getRight() - r.getWidth() / 4), (r.getBottom() + r.getHeight() / 4)),
    #             ((r.left + r.getWidth() / 4), (r.getBottom() + r.getHeight() / 4))
    #         ]
    #     )
    #     theArr = r.rasterMaskLayer(MultiPolygon([poly]))
    #     PrintArr(theArr)
    #     # Graphing to make sure I'm still sane
    #     self.fig = plt.figure(1, figsize=(10, 10))
    #
    #     polybounds = box(*poly.bounds, ccw=True)
    #
    #
    #     self.ax = self.fig.gca()
    #     self.ax.add_patch(PolygonPatch(poly, fc='#FF0000', ec='#000000', zorder=2, label='polygon'))
    #     self.ax.add_patch(PolygonPatch(polybounds, fc='#00FF00', ec='#000000', zorder=1, label='polyboundary'))
    #     self.ax.add_patch(PolygonPatch(Polygon(r.getBoundaryShape()), fc='#0000FF', ec='#000000', zorder=0, label='rasterboundary'))
    #     plt.autoscale(enable=True)
    #     plt.legend(loc='best')
    #     plt.show()
    #     plt.clf()
    #     print "done"

    def test_real(self):
        from lib.raster import Raster, PrintArr
        from lib.shapefileloader import Shapefile

        r = Raster("D:/CHaMP/Harold/2014/Entiat/ENT00001-1BC1/VISIT_2447/Topo/GISLayers/DEM.tif")
        theArr = r.rasterMaskLayer("D:/CHaMP/Harold/2014/Entiat/ENT00001-1BC1/VISIT_2447/Topo/GISLayers/Channel_Units.shp", 'Unit_Numbe')
        PrintArr(theArr)