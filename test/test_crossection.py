import unittest
import numpy as np

class crosssection_test(unittest.TestCase):

    def test_crosssection_getStatistics(self):
        from tools.topometrics.methods.crosssection import getStatistics

        lFeatures = []
        lFeatures.append( { 'WetWidth': 0  , 'W2MxDepth' : 0, 'W2AvDepth' : 0 } )
        lFeatures.append( { 'WetWidth': 2.0, 'W2MxDepth' : 2.0, 'W2AvDepth' : 2.0 } )
        dMetrics = getStatistics(lFeatures, 'WetWidth')

        self.assertEqual(dMetrics['Mean'], 1.0)
