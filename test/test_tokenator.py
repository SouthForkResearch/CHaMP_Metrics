import unittest
from lib import env
import re
from os import path, environ
import mock
from tempfile import NamedTemporaryFile
from lib.tokenator import TokenatorBorg, Tokenator
from lib.exception import *
import logging
# NOTE: WE'RE TESTING AGAINST PRODUCTION. DON'T DO ANY WRITE CALLS HERE

class SitkaAPITest(unittest.TestCase):

    def test_tokenator(self):
        """
        Make sure the tokenator is giving us a good pattern
        :return:
        """
        TokenatorBorg._kill()

        with mock.patch.dict('os.environ'):
            del environ['KEYSTONE_TOKENFILE']
            tokenator = Tokenator()

            self.assertTrue(tokenator.TOKEN.index("bearer ") == 0)
            self.assertTrue(len(tokenator.TOKEN) > 1000)

    def test_tokenator_retry(self):
        """
        Make sure the tokenator retrying if it fails
        :return:
        """
        TokenatorBorg._kill()

        # Make sure we eventually raise an exception
        with self.assertRaises(NetworkException) as e, \
             mock.patch.dict('os.environ', {'KEYSTONE_URL': 'https://keystone.sitkatech.com/core/connect/FAKEURL'}), \
             mock.patch('lib.loghelper.Logger.error') as ctx:
            Tokenator.RETRY_DELAY = 0
            # Make sure this doesn't get a chance to load from a file
            del environ['KEYSTONE_TOKENFILE']
            a = Tokenator()

        # Make sure we retried N times
        self.assertEqual(ctx.call_count, Tokenator.RETRIES_ALLOWED)

        # Make sure the last error message has the pattern "5/5" (or whatever the max number of retries is)
        rere = re.search("(\d+)\/(\d+)", e.exception.message)
        self.assertEqual(int(rere.group(1)), Tokenator.RETRIES_ALLOWED)
        self.assertEqual(int(rere.group(2)), Tokenator.RETRIES_ALLOWED)

    def test_tokenator_borg(self):
        """
        Test the tokenator re-use
        :return:
        """

        with NamedTemporaryFile() as f, mock.patch.dict('os.environ', {'KEYSTONE_TOKENFILE': f.name}):
            TokenatorBorg._kill()

            # Test tokenator loading from a file
            tokenatorA = Tokenator()
            tokenatorB = Tokenator()

            with open(f.name, "wb") as tokenfile:
                tokenfile.write("bearer IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN")

            tokenatorC = Tokenator()

            self.assertEqual(tokenatorA.TOKEN, tokenatorB.TOKEN)
            self.assertEqual(tokenatorA.TOKEN, tokenatorC.TOKEN)

            # Now test the kill order
            TokenatorBorg._kill()
            self.assertFalse(tokenatorA._initdone)
            self.assertFalse(tokenatorB._initdone)
            self.assertFalse(tokenatorC._initdone)

            self.assertEqual(len(tokenatorA._shared_state), 0)
            self.assertEqual(len(tokenatorB._shared_state), 0)
            self.assertEqual(len(tokenatorC._shared_state), 0)

    def test_tokenator_file(self):
        """
        Test that we're writing the file when appropriate but not if we don't specify the environment variable
        :return:
        """
        TokenatorBorg._kill()

        with NamedTemporaryFile() as f, mock.patch.dict('os.environ', {'KEYSTONE_TOKENFILE': f.name}):
            with open(f.name, "wb") as tokenfile:
                tokenfile.write("bearer IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN_IAMATESTTOKEN")

            # Test tokenator loading from a file
            tokenator = Tokenator()
            self.assertTrue(path.isfile(f.name))
            self.assertTrue(tokenator.TOKEN.index("bearer ") == 0)
            self.assertTrue("IAMATESTTOKEN" in tokenator.TOKEN)

            # Now make sure the reset is working.
            tokenator.reset()
            self.assertIsNone(tokenator.TOKEN)
            self.assertFalse(path.isfile(f.name))

            # Now test token renewal
            tokenator.getToken()
            self.assertTrue(tokenator.TOKEN.index("bearer ") == 0)
            self.assertTrue("IAMATESTTOKEN" not in tokenator.TOKEN)

            # Now test the token writing to file
            self.assertTrue(path.isfile(f.name))
            with open(f.name, "r") as tokenfile:
                testToken = tokenfile.read()
                self.assertEqual(tokenator.TOKEN, testToken)


    def test_tokenator_nofile(self):
        """
        Test that we're writing the file when appropriate but not if we don't specify the environment variable
        :return:
        """
        TokenatorBorg._kill()

        with mock.patch.dict('os.environ'):
            del environ['KEYSTONE_TOKENFILE']
            # Test tokenator loading from a file
            tokenator = Tokenator()
            self.assertTrue(tokenator.TOKEN.index("bearer ") == 0)
