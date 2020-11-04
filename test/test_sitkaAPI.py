import unittest
from lib.sitkaAPI import *
from lib import env
import re
import mock
from lib.exception import *
# NOTE: WE'RE TESTING AGAINST PRODUCTION. DON'T DO ANY WRITE CALLS HERE

class SitkaAPITest(unittest.TestCase):

    def test_APIGet(self):
        """
        Make sure we handle data properly
        :return:
        """
        result = APIGet('programs')
        self.assertTrue(len(result) > 0)

    def test_APIGet404(self):
        """
        Make sure we handle 404 exceptions properly
        :return:
        """

        with self.assertRaises(MissingException) as e:
            result = APIGet('programsd')

        self.assertTrue(e.exception.message.index("404") == 0)

    def test_APIGet400(self):
        """
        Make sure we handle 404 exceptions properly
        :return:
        """
        with self.assertRaises(MissingException) as e:
            result = APIGet('visits/213/folders/floopydoop')

        # NOTE: This will only be correct for CHaMP (Not AEM)
        self.assertTrue(e.exception.message.index("400") == 0)

    def test_APIGet500(self):
        """
        Make sure we handle 500 exceptions properly
        We should see a bunch of retries
        :return:
        """
        import requests

        # MonkeyPatching to make a fake error!!!
        def fakefunc(*args, **kwargs):
            class fakeObj():
                status_code = 500
            return fakeObj()

        with mock.patch('requests.get', fakefunc), self.assertRaises(NetworkException) as e, mock.patch('lib.sitkaAPI.RETRY_DELAY', 0):
            result = APIGet('IAmaTeapot')

        self.assertTrue(e.exception.message.index("500") == 0)
        # Make sure the last error message has the pattern "5/5" (or whatever the max number of retries is)
        rere = re.search("(\d+)\/(\d+)", e.exception.message)
        self.assertEqual(int(rere.group(1)), RETRIES_ALLOWED)
        self.assertEqual(int(rere.group(2)), RETRIES_ALLOWED)

    def test_APIGetWeirdError(self):
        """
        Make sure we handle weird exceptions properly
        We should see a bunch of retries
        :return:
        """
        import requests

        # MonkeyPatching!!!
        def fakefunc(a, headers=False):
            raise Exception("I AM FAKE")
        requests.__dict__['get'] = fakefunc

        with self.assertRaises(NetworkException) as e:
            result = APIGet('IAmaTeapot')

        # Make sure we've freaked out appropriately
        self.assertTrue(e.exception.message.index("Connection Exception:") == 0)
        # Make sure we've done the requisite number of retries
        self.assertEqual(int(e.exception.message[-1]), RETRIES_ALLOWED)

    def test_latestMetricInstances(self):
        """
        Make sure we actually get the right metric instances.
        :return:
        """

        # Let's invent some fake data (alphabetical in ascending date order):
        a = {'values': [
                { 'type': 'String',  'name': 'GenerationDate', 'value': '2010-08-22T01:48:14.872'},
                { 'type': 'Numeric', 'name': 'numbermetric', 'value': '123'},
                { 'type': 'String',  'name': 'stringmetric', 'value': 'Alvin'} ]}
        b = {'values': [
                { 'type': 'String',  'name': 'GenerationDate', 'value': '2011-08-22T01:48:14.872'},
                { 'type': 'Numeric', 'name': 'numbermetric', 'value': '456'},
                { 'type': 'String',  'name': 'stringmetric', 'value': 'Bethany'} ]}
        c = {'values': [
                { 'type': 'String',  'name': 'GenerationDate', 'value': '2012-08-22T01:48:00.872'},
                { 'type': 'Numeric', 'name': 'numbermetric', 'value': '789'},
                { 'type': 'String',  'name': 'stringmetric', 'value': 'Corey'} ]}
        d = {'values': [
                { 'type': 'String',  'name': 'GenerationDate', 'value': '2012-08-22T01:48:14.875'},
                { 'type': 'Numeric', 'name': 'numbermetric', 'value': '346.45'},
                { 'type': 'String',  'name': 'stringmetric', 'value': 'Darius'} ]}
        e = {
            'values': [
                { 'type': 'String',  'name': 'GenerationDate', 'value': '2012-08-22T01:48:14.975'},
                { 'type': 'Numeric', 'name': 'numbermetric', 'value': '175'},
                { 'type': 'String',  'name': 'stringmetric', 'value': 'Evelyn'} ]}
        f = {
            'values': [
                { 'type': 'String',  'name': 'GenerationDate', 'value': '2015-08-22T01:48:14.875'},
                { 'type': 'Numeric', 'name': 'numbermetric', 'value': 'I am a teapot'},
                { 'type': 'String',  'name': 'stringmetric', 'value': 'Failsalot'} ]}

        # Here are the results we expect
        goodvals = {
            "Corey": 789.0,
            "Darius": 346.45,
            "Evelyn": 175.0
        }

        # Now lets test the multiple function
        # ----------------------------------------------------
        results = [
            latestMetricInstances( [a, b, c, d, e] ),
            latestMetricInstances( [c, e, b, a, d] ),
            latestMetricInstances( [b, a, c, d, e] ),
        ]
        # Now loop through all results and make sure each one is found in our result list
        for result in results:
            self.assertEqual(len(result), 3)
            for inst in result:
                self.assertIn(inst['stringmetric'], goodvals)
                self.assertAlmostEqual(inst['numbermetric'], goodvals[inst['stringmetric']], 3)

        # Now test the singular function
        # ----------------------------------------------------
        resultSingle = latestMetricInstance( [a, b, c, d, e] )
        self.assertEqual(resultSingle['stringmetric'], 'Evelyn')

        # Now let's try some failure cases
        self.assertIsNone(latestMetricInstances([]))
        self.assertIsNone(latestMetricInstance([]))

        # What happens when we try and parse a string as a number
        with self.assertRaises(ValueError) as e:
            resulta = latestMetricInstances([a, f])