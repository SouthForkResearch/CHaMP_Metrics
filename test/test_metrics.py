import unittest
from lib.metrics import CHaMPMetric
from lib.exception import DataException

class MetricsTest(unittest.TestCase):

    def test_metrics(self):
        """
        test the exception return codes
        :return:
        """

        class TesterMetric(CHaMPMetric):

            TEMPLATE = {
                'a': None,
                'b': None,
                'c': None
            }

            def calc(self, a, b, c):

                self.metrics['a'] = a
                self.metrics['b'] = b
                self.metrics['c'] = c

                if a <= 0 or b <= 0 or c <= 0:
                    raise DataException("I AM AN EXCEPTION. LOOK AT ME AND DESPAIR")


        # And now we test -------------------------------------------------

        testerA = TesterMetric(1, 2, 3)
        testerB = TesterMetric(4, 5, 6)
        testerC = TesterMetric(-1, 2, 3)

        self.assertDictEqual(testerA.metrics, {'a': 1, 'b': 2, 'c': 3})
        self.assertDictEqual(testerB.metrics, {'a': 4, 'b': 5, 'c': 6})
        self.assertDictEqual(testerC.metrics, {'a': None, 'b': None, 'c': None})

        print "hi"