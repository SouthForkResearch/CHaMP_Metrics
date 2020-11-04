import unittest
import mock
from lib.exception import MissingException

import os

msgs = []
def loglogger(self, msg):
    msgs.append(msg)

class UtilTest(unittest.TestCase):

    def test_getAbsInsensitivePath(self):
        from lib.util import getAbsInsensitivePath
        from lib.loghelper import Logger

        log = Logger("FakeLogger")

        base = os.path.dirname(__file__)
        testpaths = [
            {
                "in": os.path.join(base),
                "out": os.path.join(base),
            },
            {
                "in" : os.path.join(base, "../tools/topometrics"),
                "out": os.path.join(base, "../tools/topometrics"),
            },
            {
                "in": os.path.join(base, "../tools/topometrics/topometrics.py"),
                "out": os.path.join(base, "../tools/topometrics/topometrics.py"),
            },
            {
                "in": os.path.join(base, "../TOOLS/topoMetrics"),
                "out": os.path.join(base, "../tools/topometrics"),
            },
            {
                "in": os.path.join(base, "../tools\\topoMetrics"),
                "out": os.path.join(base, "../tools/topometrics"),
            },
        ]
        # Test the normal case (we're catching warnings too)
        for testpath in testpaths:
            with mock.patch('lib.loghelper.Logger.warning') as ctx:
                result = getAbsInsensitivePath(testpath['in'])
                # Make sure we get back the path we expect
                self.assertEqual(result, testpath['out'])

                # Make sure we get back the right number of warnings
                if testpath['in'] != testpath['out']:
                    self.assertEqual(ctx.call_count, 1)
                else:
                    self.assertEqual(ctx.call_count, 0)

        # Test the file not found case where it throws a MissingException
        brokenpath = os.path.join(base, "../tools/NOTTHERE/thing.dxf")
        with self.assertRaises(MissingException) as e:
            getAbsInsensitivePath(brokenpath)

        # Now test where we don't care
        br_result = getAbsInsensitivePath(brokenpath, ignoreAbsent=True)
        self.assertEqual(br_result, brokenpath)

        # Test the empty case
        broken2 = ''
        with self.assertRaises(IOError) as e:
            getAbsInsensitivePath(broken2)

